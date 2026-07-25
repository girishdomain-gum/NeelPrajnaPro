"""PlaceboBattery — the G-3 placebo run (ARCH-008 §1, A1.7).

A placebo asks the sharpest question you can ask a judge: *given this exact setup,
how often do you PASS a NULL-preserving twin of the data?* A healthy judge PASSes a
true null at most at its alpha rate; a judge that PASSes null twins often is
over-eager, and any real PASS it produced is suspect. This is the G-3 gate the
PROGRAM_RETRO demanded be BUILT, and ARCH-008 wires it beside every future verdict.

It runs the SAME pipeline as a real verdict — literally :meth:`EvidenceBattery.evaluate`,
which shares :meth:`EvidenceBattery._pipeline` with :meth:`EvidenceBattery.run` — over
``n_runs`` seeded null twins, and records a ``placebo_run`` with each run's tri-state.
Crucially it appends NO verdict and burns NO window: ``evaluate`` writes nothing, and
this module writes only the one ``placebo_run`` summary. That non-consumption is
type-audited here (verdict/burn counts unchanged across the run) and structurally
guaranteed by the ``placebo_run`` schema's closed key set.

Two seeded null constructions (DEVQ-018), each holding the bar/OHLC path and the cost
model FIXED and perturbing only the setup's claimed signal, so the judgement machinery
is unchanged and only the null draw differs:

* :data:`DIRECTION_PERMUTATION` — permute the events' ``direction`` column. The null:
  *the event's direction is uninformative* (for directional event claims, e.g. FVG
  follow-through). Preserves event count/timing/strength, bar path, cost.
* :data:`ENTRY_TIME_SHUFFLE` — relocate each entry to a uniformly-random distinct bar,
  keeping direction. The null: *the chosen entry TIMING carries no edge beyond the base
  drift* (for fixed-direction timing claims, e.g. a day-of-week drift). Preserves entry
  count/direction, bar path, cost.

Kernel module: it speaks ``events`` / ``direction`` / ``bars`` / ``cost_model`` and
never a trading word (firewall-clean); the simulator + cost model are injected opaque
objects, exactly as the battery receives them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qrf.kernel.battery.battery import EvidenceBattery
from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.record import Record, now_ns
from qrf.kernel.records.store import RecordStore

DIRECTION_PERMUTATION = "direction_permutation"
ENTRY_TIME_SHUFFLE = "entry_time_shuffle"
_METHODS = frozenset({DIRECTION_PERMUTATION, ENTRY_TIME_SHUFFLE})
# The DEVQ-018 ruled null set, public so the HypothesisRegistry can validate a
# sealed ``placebo_method`` against the SAME source of truth the judge dispatches
# on (ARCH-009 §2). A new method lands here (with its bias direction documented,
# DEVQ-018 clause 3) and both the seal-check and the run-dispatch see it at once.
PLACEBO_METHODS = _METHODS

# ARCH-008 §1 AC: at least 20 seeded repetitions.
DEFAULT_N_RUNS = 20


def _direction_permutation(events: pd.DataFrame, bars: pd.DataFrame, *, seed: int) -> pd.DataFrame:
    """Seeded permutation of the ``direction`` column; everything else untouched."""
    out = events.copy().reset_index(drop=True)
    if out.empty:
        return out
    rng = np.random.default_rng(int(seed))
    out["direction"] = rng.permutation(out["direction"].to_numpy())
    return out


def _entry_time_shuffle(events: pd.DataFrame, bars: pd.DataFrame, *, seed: int) -> pd.DataFrame:
    """Relocate each entry to a uniformly-random DISTINCT bar ts; direction preserved.

    Samples ``len(events)`` distinct bar timestamps without replacement and assigns them
    (sorted) to the events, keeping every other column. Destroys the entry-timing signal
    while preserving entry count, direction mix and the real bar path.
    """
    out = events.copy().reset_index(drop=True)
    n = len(out)
    if n == 0:
        return out
    bar_ts = np.asarray(bars["ts"], dtype=np.int64)
    if bar_ts.size == 0:
        return out
    rng = np.random.default_rng(int(seed))
    k = min(n, bar_ts.size)
    chosen = np.sort(rng.choice(bar_ts, size=k, replace=False))
    if k < n:  # fewer bars than events (degenerate); keep as many entries as bars
        out = out.iloc[:k].reset_index(drop=True)
    out["ts"] = chosen
    return out


_NULL_MAKERS = {
    DIRECTION_PERMUTATION: _direction_permutation,
    ENTRY_TIME_SHUFFLE: _entry_time_shuffle,
}


class PlaceboBattery:
    """Run ``n_runs`` null-twin dry-runs of a setup and record a ``placebo_run``."""

    def __init__(self, store: RecordStore, bulk: BulkStore) -> None:
        self._store = store
        self._battery = EvidenceBattery(store, bulk)

    def run(
        self,
        hypothesis_ref: str,
        *,
        simulator,
        cost_model,
        bars: pd.DataFrame,
        events: pd.DataFrame,
        method: str,
        base_seed: int,
        n_runs: int = DEFAULT_N_RUNS,
        producer: str = "placebo",
    ) -> Record:
        """Judge ``n_runs`` seeded null twins of ``events`` and append a ``placebo_run``.

        ``method`` selects the null construction (DEVQ-018); ``base_seed`` seeds run i as
        ``base_seed + i`` (so the whole run is reproducible and IVF-recomputable from the
        record alone). Appends exactly one ``placebo_run`` record; writes no verdict and
        burns no window (asserted here — the type-audit ARCH-008 §Acceptance requires).
        """
        if method not in _METHODS:
            raise SchemaViolation(
                f"placebo method {method!r} unknown; must be one of {sorted(_METHODS)}"
            )
        # ARCH-009 §2 (DEVQ-018 ADDENDUM, forward-binding): if the hypothesis sealed a
        # placebo_method in its content-hashed YAML, the requested method MUST agree
        # with it — the pre-registration governs, a mismatch is refused naming both.
        # A grandfathered record (Wave-1: no sealed field) proceeds with the caller's
        # method exactly as it did when its window was burned.
        sealed_method = self._store.get(hypothesis_ref).payload.get("placebo_method")
        if sealed_method is not None and sealed_method != method:
            raise SchemaViolation(
                f"placebo method mismatch for hypothesis {hypothesis_ref}: sealed "
                f"placebo_method={sealed_method!r} but run requested method={method!r} — "
                "the content-hash-sealed pre-registration governs (ARCH-009 §2, DEVQ-018)"
            )
        if not isinstance(n_runs, int) or isinstance(n_runs, bool) or n_runs < 1:
            raise SchemaViolation("placebo n_runs must be an int >= 1")
        if not isinstance(base_seed, int) or isinstance(base_seed, bool) or base_seed < 0:
            raise SchemaViolation("placebo base_seed must be an int >= 0")
        maker = _NULL_MAKERS[method]

        # Type-audit anchor: a placebo consumes nothing — these counts must not move.
        verdicts_before = sum(1 for _ in self._store.query(record_type="verdict"))
        burns_before = sum(1 for _ in self._store.query(record_type="window_burn"))

        outcomes: list[str] = []
        for i in range(n_runs):
            twin = maker(events, bars, seed=base_seed + i)
            result = self._battery.evaluate(
                hypothesis_ref,
                simulator=simulator,
                cost_model=cost_model,
                bars=bars,
                events=twin,
            )
            outcomes.append(result.verdict)

        verdicts_after = sum(1 for _ in self._store.query(record_type="verdict"))
        burns_after = sum(1 for _ in self._store.query(record_type="window_burn"))
        assert verdicts_after == verdicts_before, "placebo wrote a verdict — invariant broken"
        assert burns_after == burns_before, "placebo burned a window — invariant broken"

        n_pass = sum(1 for oc in outcomes if oc == "PASS")
        payload = {
            "hypothesis_ref": hypothesis_ref,
            "method": method,
            "seed": int(base_seed),
            "n_runs": int(n_runs),
            "outcomes": outcomes,
            "n_pass": int(n_pass),
        }
        return self._store.append(
            "placebo_run",
            payload,
            producer=producer,
            event_ts=now_ns(),
            parents=[hypothesis_ref],
            schema_version=1,
        )

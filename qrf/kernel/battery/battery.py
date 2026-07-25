"""EvidenceBattery — the full §4.7 verdict pipeline, in order, all enforced.

Implementation Blueprint v1.0 §4.7, ARCH-006 §3. This is the ONLY writer of
``verdict`` and ``window_burn`` records (Blueprint §5 arrow 9). Given a frozen
hypothesis and an injected audited simulator + cost model, it runs the walk-
forward evidence pipeline and returns the verdict record — burning the window in
the same code path, so a verdict without its burn is impossible by construction.

Pipeline (ARCH-006 §3, each step feeds the verdict payload):

1. ``require_audited_simulator`` — the screener class is rejected by TYPE, never
   by inspecting what it happens to do.
2. SELFTEST GATE — the injected engine must, TODAY, still call planted-edge PASS
   / noise FAIL / small-n INSUFFICIENT on synthetic data, else
   :class:`JudgeNotCalibratedError`. The verdict records the selftest seed.
3. WINDOW CHECKS — the hypothesis's window must exist, be TRAINING/EXPLORATION
   (VIRGIN → :class:`ContaminationError`), and not already be burned for this
   lineage (:class:`WindowBurnedError` — the re-run refusal).
4. SPLITS — anchored walk-forward from the hypothesis ``split_spec``; the
   embargo>=hold+1 boundary rule is re-checked (DEVQ-011).
5. ENGINE — per fold, over its TEST index range ONLY (a fold's trades may use no
   bar outside its own test block; trades that cannot open+close inside it are
   dropped and counted). Seed from ``seeds.for_run(hypothesis, window)``.
6. STATISTICS — pooled per-trade net outcomes across all fold TEST ranges; a
   one-sided t (H0: mean <= 0) plus a seeded percentile bootstrap CI; per-fold
   means recorded.
7. TRI-STATE — against the PRE-REGISTERED thresholds at the DEFLATED alpha:
   n < min_n → INSUFFICIENT; else PASS iff mean>0 AND p < effective_alpha;
   else FAIL.
8. APPEND — write the pooled fold trades to the BulkStore, append the ``verdict``
   (referencing hypothesis, window, both seeds, all stats, thresholds AS
   REGISTERED, and the correction fields), then append the ``window_burn`` in the
   same flow.

This module is kernel: the simulator and cost model are INJECTED opaque objects
(never imported); it speaks ``scope`` / ``lineage`` / ``net`` / ``gross`` and no
trading word (firewall-clean).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
import pyarrow as pa
from scipy import stats

from qrf.kernel.battery.selftest import run_selftest
from qrf.kernel.battery.simulator import require_audited_simulator
from qrf.kernel.corrections.deflation import deflate, deflate_family
from qrf.kernel.errors import ContaminationError, JudgeNotCalibratedError, SchemaViolation
from qrf.kernel.protocol import seeds
from qrf.kernel.protocol.splits import SplitSpec, walk_forward
from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.record import Record, now_ns
from qrf.kernel.records.store import RecordStore

PASS = "PASS"
FAIL = "FAIL"
INSUFFICIENT = "INSUFFICIENT"

_BOOTSTRAP_RESAMPLES = 2000
_JUDGEABLE_DESIGNATIONS = frozenset({"TRAINING", "EXPLORATION"})

# The selftest is a WIRING gate (DEVQ-013), not evidence: it must give the same
# verdict every run so it fails only when the engine/statistics are actually
# broken — never by seed luck. A fixed, validated seed does this. It is stable
# across cost models (cost only pushes the driftless noise suite MORE negative,
# so noise stays a FAIL) and is validated to classify all three suites correctly
# with the audited engine at both zero and real cost. It is recorded on every
# verdict as ``selftest_seed`` so the gate that licensed the run is auditable.
_SELFTEST_SEED = 20260725


def _finite_or_none(x: float | None) -> float | None:
    """Map a non-finite float to None so it can never enter canonical JSON."""
    if x is None:
        return None
    xf = float(x)
    return xf if math.isfinite(xf) else None


@dataclass(frozen=True)
class _FoldOutcome:
    index: int
    test_start: int
    test_end: int
    net: list[float]
    gross: list[float]
    n_dropped_tail: int
    trade_rows: list[dict]


class EvidenceBattery:
    """Run the §4.7 pipeline and emit a verdict + window_burn (Blueprint §4.7)."""

    def __init__(self, store: RecordStore, bulk: BulkStore) -> None:
        self._store = store
        self._bulk = bulk
        self._windows = WindowLedger(store)

    # -- helpers --------------------------------------------------------------
    def _hypothesis_window(self, hyp: Record) -> str:
        windows = [
            p for p in hyp.parents if self._store.get(p).record_type == "window"
        ]
        if len(windows) != 1:
            raise SchemaViolation(
                f"hypothesis {hyp.record_id} must have exactly one window parent, "
                f"found {len(windows)}"
            )
        return windows[0]

    def _window_bars(self, bars: pd.DataFrame, window: Record) -> pd.DataFrame:
        """The window's bars, in ts order — sliced from the caller's bar frame."""
        ts_start = window.payload["ts_start"]
        ts_end = window.payload["ts_end"]
        wb = bars[(bars["ts"] >= ts_start) & (bars["ts"] < ts_end)]
        return wb.sort_values("ts", kind="mergesort").reset_index(drop=True)

    def _selftest_gate(self, simulator, cost_model, *, seed: int) -> None:
        """Step 2: today's calibration gate; JudgeNotCalibratedError on failure."""

        def _runner(b, e, hold_bars):
            trades = simulator.simulate(
                b, e, cost_model, seed=seed, execution={"hold_bars": hold_bars, "size": 1.0}
            )
            return [t.net_pnl for t in trades.trades]

        report = run_selftest(_runner, seed=seed)
        if not report.passed:
            failed = [f"{r.name}: got {r.classification}, expected {r.expected}"
                      for r in report.results if not r.ok]
            raise JudgeNotCalibratedError(
                "battery selftest failed today — the engine no longer calls the "
                f"planted tri-state correctly ({'; '.join(failed)}); run aborted "
                f"(selftest seed {seed})"
            )

    def _run_folds(self, simulator, cost_model, exec_dict, spec, seed, wb, events):
        """Step 5: run the engine over each fold's TEST range only."""
        folds = walk_forward(len(wb), spec)
        ts_col = wb["ts"].tolist()
        outcomes: list[_FoldOutcome] = []
        for fold in folds:
            t0, t1 = fold.test.start, fold.test.end
            test_bars = wb.iloc[t0:t1].reset_index(drop=True)
            lo, hi = int(ts_col[t0]), int(ts_col[t1 - 1])
            fold_events = events[(events["ts"] >= lo) & (events["ts"] <= hi)]
            trades = simulator.simulate(
                test_bars, fold_events, cost_model, seed=seed, execution=exec_dict
            )
            net = [float(t.net_pnl) for t in trades.trades]
            gross = [float(t.gross_pnl) for t in trades.trades]
            rows = [{**t.as_dict(), "fold": fold.index} for t in trades.trades]
            outcomes.append(
                _FoldOutcome(
                    index=fold.index,
                    test_start=t0,
                    test_end=t1,
                    net=net,
                    gross=gross,
                    n_dropped_tail=int(trades.n_dropped_tail),
                    trade_rows=rows,
                )
            )
        return outcomes

    def _pooled_statistics(self, net: list[float], *, seed: int):
        """Step 6: one-sided t (H0: mean<=0) + seeded percentile bootstrap CI."""
        x = np.asarray(net, dtype=np.float64)
        n = int(x.size)
        if n == 0:
            return {"mean": None, "stat": None, "p": None, "ci_low": None, "ci_high": None}
        mean = float(x.mean())
        rng = np.random.default_rng(int(seed))
        ci_low = ci_high = None
        if n >= 2:
            idx = rng.integers(0, n, size=(_BOOTSTRAP_RESAMPLES, n))
            means = x[idx].mean(axis=1)
            lo, hi = np.percentile(means, [2.5, 97.5])
            ci_low, ci_high = _finite_or_none(lo), _finite_or_none(hi)
        sd = float(x.std(ddof=1)) if n >= 2 else 0.0
        scale = 1e-12 * (abs(mean) + 1.0)
        if n < 2 or sd <= scale:
            # Degenerate/zero-variance: decide on sign; the t is undefined.
            p = 0.0 if mean > 0 else 1.0
            return {"mean": mean, "stat": None, "p": p, "ci_low": ci_low, "ci_high": ci_high}
        t_stat, p_two = stats.ttest_1samp(x, 0.0)
        p_one = float(p_two / 2 if mean > 0 else 1.0 - p_two / 2)
        return {
            "mean": mean,
            "stat": _finite_or_none(t_stat),
            "p": _finite_or_none(p_one),
            "ci_low": ci_low,
            "ci_high": ci_high,
        }

    def _trades_manifest(self, hyp: Record, outcomes: list[_FoldOutcome]) -> str:
        """Step 8a: persist the pooled fold trades; return the manifest ref (or '')."""
        rows: list[dict] = []
        for oc in outcomes:
            for r in oc.trade_rows:
                d = dict(r)
                d["ts"] = int(d["signal_ts"])
                rows.append(d)
        if not rows:
            return ""  # no trades to anchor (a FAIL/INSUFFICIENT on an empty run)
        table = pa.Table.from_pylist(rows)
        ts_i64 = table.column("ts").cast(pa.int64())
        table = table.set_column(table.schema.get_field_index("ts"), "ts", ts_i64)
        manifest = self._bulk.write(
            f"verdict_trades.{hyp.payload['lineage']}",
            table,
            producer="battery",
            parents=[hyp.record_id],
        )
        return manifest.record_id

    # -- the pipeline ---------------------------------------------------------
    def run(
        self,
        hypothesis_ref: str,
        *,
        simulator,
        cost_model,
        bars: pd.DataFrame,
        events: pd.DataFrame,
        producer: str = "battery",
    ) -> Record:
        """Judge ``hypothesis_ref`` and return its verdict record (also burns window).

        ``simulator`` must be the audited engine (screener rejected by type);
        ``cost_model`` is the injected named model; ``bars`` and ``events`` are the
        window's numeric frames (bars carry ts/open/high/low/close; events carry
        ts/direction/strength). Any pipeline refusal raises before a verdict is
        written; on success the verdict and its window_burn are appended together.
        """
        # 1. type gate — screener rejected by type, not by inspection.
        require_audited_simulator(simulator)

        hyp = self._store.get(hypothesis_ref)
        if hyp.record_type != "hypothesis":
            raise SchemaViolation(
                f"record {hypothesis_ref} is a {hyp.record_type!r}, not a hypothesis"
            )
        lineage = hyp.payload["lineage"]
        scope = hyp.payload["scope"]
        thresholds = hyp.payload["thresholds"]
        window_ref = self._hypothesis_window(hyp)
        window = self._store.get(window_ref)

        engine_seed = seeds.for_run(hypothesis_ref, window_ref)
        selftest_seed = _SELFTEST_SEED

        # 2. selftest gate (records the seed; aborts on failure).
        self._selftest_gate(simulator, cost_model, seed=selftest_seed)

        # 3. window checks: designation + not burned for this lineage.
        designation = window.payload["designation"]
        if designation not in _JUDGEABLE_DESIGNATIONS:
            raise ContaminationError(
                f"window {window_ref} is {designation}-designated; the battery judges "
                "only TRAINING/EXPLORATION windows (VIRGIN is the untouched reserve)"
            )
        self._windows.check_available(window_ref, lineage)  # WindowBurnedError on re-run

        # 4. splits (embargo>=hold+1 re-checked via the config below).
        exec_dict = dict(hyp.payload["execution"])
        split_spec = hyp.payload["split_spec"]
        hold = exec_dict["hold_bars"]
        embargo = split_spec["embargo_bars"]
        if embargo < hold + 1:
            raise SchemaViolation(
                f"split_spec.embargo_bars ({embargo}) < hold_bars + 1 ({hold + 1}) — "
                "DEVQ-011 BINDING; run refused"
            )
        wb = self._window_bars(bars, window)

        # 5. engine per fold TEST range only.
        spec = SplitSpec(n_folds=split_spec["n_folds"], embargo_bars=embargo)
        outcomes = self._run_folds(simulator, cost_model, exec_dict, spec, engine_seed, wb, events)

        pooled_net = [v for oc in outcomes for v in oc.net]
        pooled_gross = [v for oc in outcomes for v in oc.gross]
        n_total = len(pooled_net)
        n_dropped = sum(oc.n_dropped_tail for oc in outcomes)

        # 6. statistics.
        st = self._pooled_statistics(pooled_net, seed=engine_seed)

        # 7. tri-state at the DEFLATED alpha. A v2 hypothesis deflates by its
        # CLAIM family (DEVQ-015 — the governing rule); a legacy v1 hypothesis by
        # the (scope, lineage) rule it was sealed under.
        family = hyp.payload.get("family")
        if family is not None:
            defl = deflate_family(thresholds["base_alpha"], family, self._store)
        else:
            defl = deflate(thresholds["base_alpha"], scope, lineage, self._store)
        mean_positive = st["mean"] is not None and st["mean"] > 0
        significant = st["p"] is not None and st["p"] < defl.effective_alpha
        if n_total < thresholds["min_n"]:
            verdict = INSUFFICIENT
        elif mean_positive and significant:
            verdict = PASS
        else:
            verdict = FAIL

        # 8. persist trades, append verdict, then burn — one code path.
        trades_manifest = self._trades_manifest(hyp, outcomes)
        payload = {
            "hypothesis_ref": hypothesis_ref,
            "window_ref": window_ref,
            "verdict": verdict,
            "n_trades": n_total,
            "n_dropped_tail": n_dropped,
            "gross": {
                "total": _finite_or_none(sum(pooled_gross)) if pooled_gross else 0.0,
                "mean": _finite_or_none(float(np.mean(pooled_gross))) if pooled_gross else None,
            },
            "net": {
                "total": _finite_or_none(sum(pooled_net)) if pooled_net else 0.0,
                "mean": st["mean"],
            },
            "statistics": {
                "t_one_sided": {
                    "stat": st["stat"],
                    "p": st["p"],
                    "ci_low": st["ci_low"],
                    "ci_high": st["ci_high"],
                }
            },
            "folds": [
                {
                    "index": oc.index,
                    "n_trades": len(oc.net),
                    "mean_net": _finite_or_none(float(np.mean(oc.net))) if oc.net else None,
                    "test_start": oc.test_start,
                    "test_end": oc.test_end,
                }
                for oc in outcomes
            ],
            "corrections": {
                "family_m": defl.n_trials,
                "method": defl.method,
                "base_alpha": defl.base_alpha,
                "effective_alpha": defl.effective_alpha,
            },
            "thresholds": thresholds,  # AS REGISTERED (byte-equal copy)
            "seed": engine_seed,
            "selftest_seed": selftest_seed,
            "engine_version": getattr(simulator, "engine_version", type(simulator).__name__),
            "trades_manifest": trades_manifest,
        }
        # v2 verdict records the family the deflation totalled over (audit trail).
        verdict_schema_version = 1
        if family is not None:
            payload["corrections"]["family"] = family
            verdict_schema_version = 2
        verdict_rec = self._store.append(
            "verdict",
            payload,
            producer=producer,
            event_ts=now_ns(),
            parents=[hypothesis_ref, window_ref],
            schema_version=verdict_schema_version,
        )
        # A verdict without its burn is impossible: the burn follows unconditionally.
        self._windows.burn(window_ref, lineage, verdict_rec.record_id)
        return verdict_rec

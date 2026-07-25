"""Screener — a vectorbt sweep over EventFrames that produces a shortlist.

Implementation Blueprint v1.0 §5 arrow (8), §7 Sprint 4; ARCH-004 §1/§2. The
screener is a **telescope, not a judge**: given price bars, a detector's
EventFrame, a parameter grid and a named cost model, it runs a vectorized
entry/exit sweep and emits a *shortlist* — a plain parquet artifact (via
BulkStore) plus a ``note`` record that references it and DECLARES the screening
metric and thresholds *before* ranking. It writes **no** ``verdict`` and **no**
``window_burn`` record — ever (a type-level audit test proves the module cannot),
and it runs only on TRAINING/EXPLORATION windows (a VIRGIN window raises
:class:`ContaminationError`).

**Single code path (arrow 8).** Every ``run`` that produces a shortlist also
appends exactly one ``trial_count`` record whose ``n_attempts`` equals the EXACT
grid size — every variant evaluated counts, with no netting and no dedup. The
bump and the shortlist are produced by the same method; a shortlist without its
trial_count bump is impossible by construction.

**Strategy under test.** Each grid variant is ``{hold_bars, strength_min,
side}``: enter on every event whose ``direction`` matches ``side``
(``long`` -> +1, ``short`` -> -1) and whose ``strength`` >= ``strength_min``;
exit ``hold_bars`` bars later. vectorbt runs the fill with zero fees/slippage so
its per-trade PnL is *gross*; the named :class:`CostModel` then charges the
honest frictions to yield *net*. Both gross and net metrics are recorded, so the
cost drag is visible in the artifact.

**Declared metric.** Primary ranking metric is per-trade net Sharpe
(``mean(net_pnl) / std(net_pnl)``). A variant is admitted to the shortlist iff
``n_trades >= min_trades`` and ``net_sharpe >= min_sharpe`` and
``net_total > 0``. The metric name and thresholds live in the note payload,
fixed before ranking (no post-hoc metric picking).
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import vectorbt as vbt

from qrf.kernel.corrections.trials import TrialCountLedger
from qrf.kernel.errors import SchemaViolation
from qrf.kernel.instruments.base import validate_event_frame
from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.record import Record, now_ns
from qrf.kernel.records.store import RecordStore

# The grid parameters the screener understands. A variant must supply all three.
_GRID_KEYS: tuple[str, ...] = ("hold_bars", "strength_min", "side")
_SIDES = frozenset({"long", "short"})

# The declared screening metric and its default admission thresholds.
RANKING_METRIC = "net_sharpe"

# Fields echoed into the note's compact "top" preview of the ranking.
_TOP_KEYS: tuple[str, ...] = (
    *_GRID_KEYS,
    "n_trades",
    "gross_sharpe",
    "net_sharpe",
    "net_total",
    "admitted",
)


@dataclass(frozen=True)
class ScreenThresholds:
    """Admission thresholds, declared in the shortlist note before ranking."""

    min_trades: int = 30
    min_sharpe: float = 0.10
    require_positive_net_total: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "min_trades": self.min_trades,
            "min_sharpe": self.min_sharpe,
            "require_positive_net_total": self.require_positive_net_total,
        }


@dataclass(frozen=True)
class ScreenResult:
    """The pure product of a sweep — the ranked table and its summary.

    Holds no journal records: ``compute_ranking`` returns this without writing,
    so the same computation drives both a real ``run`` (which persists) and a
    ``--rebuild-bulk`` (which re-derives the parquet and hash-verifies it).
    """

    table: pa.Table
    rows: list[dict[str, Any]]
    grid_size: int
    n_admitted: int
    designation: str
    thresholds: ScreenThresholds


def _derive_seed(
    dataset_manifest_refs: list[str],
    eventframe_manifest_ref: str,
    grid: dict[str, list],
    cost_model_name: str,
    window_ref: str,
    lineage: str,
    thresholds: ScreenThresholds,
) -> int:
    """A deterministic 63-bit seed derived from the run's full identity.

    The screener itself is deterministic (no RNG), so this seed is a
    reproducibility/provenance stamp: identical inputs → identical seed, and the
    shortlist note records a concrete integer rather than ``null`` (REV-S4 F-4).
    """
    identity = json.dumps(
        {
            "datasets": sorted(dataset_manifest_refs),
            "events": eventframe_manifest_ref,
            "grid": {k: sorted(map(str, grid[k])) for k in sorted(grid)},
            "cost_model": cost_model_name,
            "window": window_ref,
            "lineage": lineage,
            "thresholds": thresholds.as_dict(),
        },
        sort_keys=True,
    )
    digest = hashlib.sha256(identity.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") & 0x7FFF_FFFF_FFFF_FFFF


def grid_variants(grid: dict[str, list]) -> list[dict[str, Any]]:
    """Expand a parameter grid into the exact list of variants (Cartesian product).

    The product's length is the trial count — every combination is one variant.
    """
    if set(grid) != set(_GRID_KEYS):
        raise SchemaViolation(
            f"screener grid keys must be exactly {sorted(_GRID_KEYS)}, got {sorted(grid)}"
        )
    for k in _GRID_KEYS:
        if not isinstance(grid[k], list) or not grid[k]:
            raise SchemaViolation(f"screener grid[{k!r}] must be a non-empty list")
    keys = list(_GRID_KEYS)
    combos = itertools.product(*(grid[k] for k in keys))
    variants = [dict(zip(keys, combo, strict=True)) for combo in combos]
    for v in variants:
        if v["side"] not in _SIDES:
            raise SchemaViolation(f"screener side {v['side']!r} must be one of {sorted(_SIDES)}")
        hb = v["hold_bars"]
        if not isinstance(hb, int) or isinstance(hb, bool) or hb < 1:
            raise SchemaViolation("screener hold_bars must be an int >= 1")
    return variants


class Screener:
    """vectorbt sweep over an EventFrame → shortlist artifact + trial_count."""

    def __init__(self, store: RecordStore, bulk: BulkStore) -> None:
        self._store = store
        self._bulk = bulk
        self._windows = WindowLedger(store)
        self._trials = TrialCountLedger(store)

    # -- bar / event loading --------------------------------------------------
    def _load_bars(self, dataset_manifest_refs: list[str]) -> pd.DataFrame:
        frames = [self._bulk.read(ref).to_pandas() for ref in dataset_manifest_refs]
        bars = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
        if "ts" not in bars.columns or "close" not in bars.columns:
            raise SchemaViolation("screener bars require 'ts' and 'close' columns")
        bars = bars.sort_values("ts").reset_index(drop=True)
        return bars

    def _load_events(self, eventframe_manifest_ref: str) -> pd.DataFrame:
        table = self._bulk.read(eventframe_manifest_ref)
        validate_event_frame(table)
        return table.to_pandas()

    # -- one variant ----------------------------------------------------------
    def _evaluate(
        self,
        variant: dict[str, Any],
        close: pd.Series,
        ts_to_idx: dict[int, int],
        events: pd.DataFrame,
        cost_model,
    ) -> dict[str, Any]:
        n = len(close)
        want_dir = 1 if variant["side"] == "long" else -1
        smin = float(variant["strength_min"])
        hold = int(variant["hold_bars"])

        entries = np.zeros(n, dtype=bool)
        for ts, direction, strength in zip(
            events["ts"], events["direction"], events["strength"], strict=True
        ):
            if int(direction) != want_dir:
                continue
            if not (float(strength) >= smin):
                continue
            idx = ts_to_idx.get(int(ts))
            if idx is not None:
                entries[idx] = True

        exits = np.zeros(n, dtype=bool)
        if hold < n:
            src = np.flatnonzero(entries)
            dst = src + hold
            dst = dst[dst < n]
            exits[dst] = True

        result = {**variant, "n_trades": 0}
        for m in ("gross_total", "gross_sharpe", "net_total", "net_mean", "net_std", "net_sharpe"):
            result[m] = 0.0
        if not entries.any():
            return result

        direction = "longonly" if want_dir == 1 else "shortonly"
        pf = vbt.Portfolio.from_signals(
            close,
            pd.Series(entries, index=close.index),
            pd.Series(exits, index=close.index),
            direction=direction,
            fees=0.0,
            slippage=0.0,
            size=1,
            size_type="amount",
            init_cash=1_000_000,
            freq="1D",
        )
        trades = pf.trades.records_readable
        if len(trades) == 0:
            return result

        gross = pd.DataFrame(
            {"size": trades["Size"].to_numpy(), "gross_pnl": trades["PnL"].to_numpy()}
        )
        net = cost_model.apply(gross)
        net_pnl = net["net_pnl"].to_numpy()
        gross_pnl = net["gross_pnl"].to_numpy()

        result["n_trades"] = int(len(net_pnl))
        result["gross_total"] = float(gross_pnl.sum())
        result["gross_sharpe"] = _sharpe(gross_pnl)
        result["net_total"] = float(net_pnl.sum())
        result["net_mean"] = float(net_pnl.mean())
        result["net_std"] = float(net_pnl.std(ddof=1)) if len(net_pnl) >= 2 else 0.0
        result["net_sharpe"] = _sharpe(net_pnl)
        return result

    # -- pure sweep (no journal writes) ---------------------------------------
    def compute_ranking(
        self,
        *,
        dataset_manifest_refs: list[str],
        eventframe_manifest_ref: str,
        grid: dict[str, list],
        cost_model_name: str,
        window_ref: str,
        thresholds: ScreenThresholds | None = None,
        venues_path: str = "configs/venues.yaml",
    ) -> ScreenResult:
        """Run the sweep and build the ranked shortlist table — writing nothing.

        The single deterministic computation behind both :meth:`run` (which then
        persists) and ``--rebuild-bulk`` (which re-derives the parquet and
        hash-verifies it). Guards VIRGIN via :meth:`WindowLedger.check_screenable`.
        """
        from qrf.trading.utility.cost_models import load_cost_model

        # Guard: telescope only points at TRAINING/EXPLORATION (VIRGIN refused).
        designation = self._windows.check_screenable(window_ref)

        thresholds = thresholds or ScreenThresholds()
        variants = grid_variants(grid)
        grid_size = len(variants)

        cost_model = load_cost_model(cost_model_name, venues_path)
        bars = self._load_bars(dataset_manifest_refs)
        events = self._load_events(eventframe_manifest_ref)
        close = pd.Series(bars["close"].to_numpy(), index=pd.RangeIndex(len(bars)))
        ts_to_idx = {int(ts): i for i, ts in enumerate(bars["ts"].to_numpy())}

        rows = [self._evaluate(v, close, ts_to_idx, events, cost_model) for v in variants]

        # Admission + ranking under the DECLARED metric (fixed before this line).
        for r in rows:
            r["admitted"] = bool(
                r["n_trades"] >= thresholds.min_trades
                and r["net_sharpe"] >= thresholds.min_sharpe
                and (r["net_total"] > 0 or not thresholds.require_positive_net_total)
            )
        rows.sort(key=lambda r: (r["net_sharpe"], r["net_total"]), reverse=True)
        for rank, r in enumerate(rows):
            r["rank"] = rank
        n_admitted = sum(r["admitted"] for r in rows)

        scope_ts = int(self._store.get(window_ref).payload["ts_start"])
        table = _rank_table(rows, scope_ts)
        return ScreenResult(
            table=table,
            rows=rows,
            grid_size=grid_size,
            n_admitted=int(n_admitted),
            designation=designation,
            thresholds=thresholds,
        )

    # -- the single code path -------------------------------------------------
    def run(
        self,
        *,
        dataset_manifest_refs: list[str],
        eventframe_manifest_ref: str,
        grid: dict[str, list],
        cost_model_name: str,
        window_ref: str,
        lineage: str,
        family: str | None = None,
        thresholds: ScreenThresholds | None = None,
        shortlist_dataset: str = "screener_shortlist",
        seed: int | None = None,
        producer: str = "screener",
        venues_path: str = "configs/venues.yaml",
    ) -> Record:
        """Screen ``grid`` over the events, write the shortlist, bump trial_count.

        Returns the shortlist ``note`` record. Appends, in order: the shortlist
        ``bulk_manifest`` (the ranked parquet), one ``trial_count`` of exactly the
        grid size, and the ``note`` that references both and declares the metric.
        Raises :class:`ContaminationError` if ``window_ref`` is VIRGIN.

        ``seed`` is a provenance stamp recorded in the note: if omitted it is
        DERIVED deterministically from the run's identity, so the note never
        records ``null`` (REV-S4 F-4). The seed lives only in the note; the
        shortlist parquet does not depend on it.
        """
        result = self.compute_ranking(
            dataset_manifest_refs=dataset_manifest_refs,
            eventframe_manifest_ref=eventframe_manifest_ref,
            grid=grid,
            cost_model_name=cost_model_name,
            window_ref=window_ref,
            thresholds=thresholds,
            venues_path=venues_path,
        )
        thresholds = result.thresholds

        seed_source = "explicit" if seed is not None else "derived"
        effective_seed = seed if seed is not None else _derive_seed(
            dataset_manifest_refs,
            eventframe_manifest_ref,
            grid,
            cost_model_name,
            window_ref,
            lineage,
            thresholds,
        )

        # --- write the shortlist parquet via BulkStore (needs an int64 ts). ---
        manifest = self._bulk.write(
            shortlist_dataset,
            result.table,
            producer=producer,
            parents=[window_ref, eventframe_manifest_ref, *dataset_manifest_refs],
        )

        # --- auto-bump trial_count by the EXACT grid size (same run). ---------
        # ``family`` (DEVQ-015) makes this search's multiplicity burden accrue to
        # its {market}/{instrument_family}, so a later hypothesis in the same
        # family is deflated by it directly (not by a lineage prefix guess).
        trial = self._trials.bump(
            window_ref,
            lineage,
            result.grid_size,
            "screener",
            family=family,
            parents=[window_ref],
            producer=producer,
        )

        # --- the shortlist note: declares metric + thresholds, links artifact.-
        declaration = {
            "kind": "screener_shortlist",
            "ranking_metric": RANKING_METRIC,
            "thresholds": thresholds.as_dict(),
            "cost_model": cost_model_name,
            "window_ref": window_ref,
            "window_designation": result.designation,
            "lineage": lineage,
            "family": family,
            "grid_keys": list(_GRID_KEYS),
            "grid_size": result.grid_size,
            "trial_count_ref": trial.record_id,
            "trial_count_n": result.grid_size,
            "shortlist_manifest_ref": manifest.record_id,
            "n_admitted": result.n_admitted,
            "seed": effective_seed,
            "seed_source": seed_source,
            "top": [
                {k: r[k] for k in _TOP_KEYS}
                for r in result.rows[: min(10, len(result.rows))]
            ],
        }
        note = self._store.append(
            "note",
            {"text": json.dumps(declaration, sort_keys=True)},
            producer=producer,
            event_ts=now_ns(),
            parents=[manifest.record_id, trial.record_id, window_ref],
        )
        return note


def _sharpe(pnl: np.ndarray) -> float:
    """Per-trade Sharpe ``mean/std`` (ddof=1); 0.0 for <2 trades or ~zero variance.

    Degenerate zero-variance streaks (identical per-trade PnL — a synthetic
    artifact, never real market data) are treated as uninformative rather than
    infinitely sharp: a std at floating-point noise level yields Sharpe 0.0.
    """
    if len(pnl) < 2:
        return 0.0
    sd = float(pnl.std(ddof=1))
    scale = 1e-9 * (abs(float(pnl.mean())) + 1.0)
    if math.isnan(sd) or sd <= scale:
        return 0.0
    return float(pnl.mean()) / sd


def _rank_table(rows: list[dict[str, Any]], scope_ts: int) -> pa.Table:
    """Build the ranked shortlist parquet table (BulkStore needs an int64 ts)."""
    df = pd.DataFrame(rows)
    df.insert(0, "ts", np.int64(scope_ts))
    df["hold_bars"] = df["hold_bars"].astype("int64")
    df["strength_min"] = df["strength_min"].astype("float64")
    df["side"] = df["side"].astype("string")
    df["n_trades"] = df["n_trades"].astype("int64")
    df["rank"] = df["rank"].astype("int64")
    df["admitted"] = df["admitted"].astype("bool")
    for c in ("gross_total", "gross_sharpe", "net_total", "net_mean", "net_std", "net_sharpe"):
        df[c] = df[c].astype("float64")
    return pa.Table.from_pandas(df, preserve_index=False)

"""BlockNull — N2 block-resampling null construction (ECF, Scientific Model
§5.3; Gen-1 reference EXISTENCE_CLAIM_FRAMEWORK_ECF.md; sealed R1-v2, A-023).

Resamples whole, contiguous BLOCK_BARS-bar blocks of a real bar series (never
individual scalar returns) to preserve each block's own intact OHLC geometry
— local volatility clustering survives WITHIN a block — while the random
block order destroys any SPECIFIC cross-block event relationship a claim's
detector might report. The calendar-template draw is stratified by weekday: a
resampled trading-day slot's blocks are drawn only from real historical days
of the SAME weekday, so weekend/session structure is honest, not incidental
(Gen-1's own "session-aware... rotate by whole days within matched
weekday/session frames" language, applied here to N2's block DRAW).

BLOCK_BARS = 7 (= 2*PIVOT_K + 1, sealed R1-v2/A-023): the pivot-confirmation
neighborhood is the frozen liquidity-sweep detector's own minimal structural
geometry a block must keep intact. A real measurement (WO-15's own
pool-confirmation-to-sweep gap distribution, n=325, the real burned
xauusd_m5_vantage window) showed 55.7% of the actual pairs span more than 7
bars, so this block length structurally destroys the majority of the real
arrangement while preserving the detector's own local pivot/reclose
mechanics — derived from frozen detector constants + the sealed choice rule,
zero discretion.

NAMED LIMITATION (A-023, stated not hidden): volatility clustering is
preserved only WITHIN a 7-bar (35-minute) block; longer-range clustering is
NOT preserved — the standard block-bootstrap tradeoff, forced here by the
claim's own fine timescale.

This module is kernel: it never imports qrf.trading. The detector is an
INJECTED, duck-typed object (`.detect(bars_table: pa.Table) -> pa.Table`,
an EventFrame) — exactly placebo.py's own simulator/cost_model injection
pattern. The kernel never knows what a detector computes, only that
block-resampling its bar input and re-running it produces a null event set.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import pyarrow as pa

from qrf.kernel.errors import SchemaViolation

BLOCK_BARS = 7  # sealed, R1-v2 (A-023): 2*PIVOT_K + 1, zero discretion
_NS_PER_DAY = 86_400_000_000_000
_REQUIRED_BAR_COLUMNS = ("ts", "open", "high", "low", "close")


def _trading_day_groups(bars: pd.DataFrame) -> list[pd.DataFrame]:
    """Partition ``bars`` (already sorted by ts) into contiguous UTC-calendar-
    day groups, each a sub-DataFrame with the same columns and row order."""
    ts = bars["ts"].to_numpy(dtype="int64")
    days = ts // _NS_PER_DAY
    groups: list[pd.DataFrame] = []
    start = 0
    n = len(days)
    for i in range(1, n + 1):
        if i == n or days[i] != days[start]:
            groups.append(bars.iloc[start:i].reset_index(drop=True))
            start = i
    return groups


def _weekday_of_group(day_bars: pd.DataFrame) -> int:
    """0=Monday..6=Sunday, from the group's first bar's UTC calendar day.

    1970-01-01 (epoch day 0) was a Thursday (weekday index 3); weekday =
    (epoch_day + 3) mod 7 — no datetime construction needed.
    """
    ts0 = int(day_bars["ts"].iloc[0])
    epoch_day = ts0 // _NS_PER_DAY
    return int((epoch_day + 3) % 7)


def resample_bar_blocks(
    bars: pd.DataFrame, *, seed: int, block_bars: int = BLOCK_BARS
) -> pd.DataFrame:
    """One seeded N2 surrogate: a same-length synthetic OHLC series.

    ``bars`` needs columns ts/open/high/low/close (any others are dropped —
    callers needing them re-derive after resampling). Each real trading
    day's own ``ts`` values are kept EXACTLY (the calendar timeline is
    real); only the price content is resampled, in ``block_bars``-bar
    chunks drawn WITH REPLACEMENT from real blocks of the SAME weekday
    anywhere in ``bars``. Seams between chunks (and so between resampled
    trading days) are NOT smoothed — a pivot whose confirmation window
    would span a seam is honestly ineligible in the surrogate, exactly as
    a real calendar seam already is (Gen-1's "seams are data, never
    convention").
    """
    missing = [c for c in _REQUIRED_BAR_COLUMNS if c not in bars.columns]
    if missing:
        raise SchemaViolation(f"resample_bar_blocks: bars missing column(s) {missing}")
    if not isinstance(block_bars, int) or isinstance(block_bars, bool) or block_bars < 1:
        raise SchemaViolation("resample_bar_blocks: block_bars must be an int >= 1")

    b = bars.sort_values("ts", kind="mergesort").reset_index(drop=True)
    day_groups = _trading_day_groups(b)

    blocks_by_weekday: dict[int, list[pd.DataFrame]] = {w: [] for w in range(7)}
    for day in day_groups:
        w = _weekday_of_group(day)
        n = len(day)
        for start in range(0, n, block_bars):
            blocks_by_weekday[w].append(
                day.iloc[start : start + block_bars].reset_index(drop=True)
            )

    rng = np.random.default_rng(int(seed))
    out_parts: list[pd.DataFrame] = []
    for day in day_groups:
        w = _weekday_of_group(day)
        pool = blocks_by_weekday[w]
        n = len(day)
        day_ts = day["ts"].to_numpy()
        filled = 0
        while filled < n:
            draw = pool[int(rng.integers(0, len(pool)))]
            take = min(len(draw), n - filled)
            chunk = draw.iloc[:take][["ts", "open", "high", "low", "close"]].copy()
            chunk = chunk.reset_index(drop=True)
            chunk["ts"] = day_ts[filled : filled + take]  # real calendar timeline
            out_parts.append(chunk)
            filled += take
    return pd.concat(out_parts, ignore_index=True)


def _to_detector_table(surrogate: pd.DataFrame) -> pa.Table:
    """The exact ts/high/low/close shape LiquiditySweepDetector._ohlc reads."""
    return pa.table(
        {
            "ts": pa.array(surrogate["ts"].tolist(), type=pa.int64()),
            "high": pa.array(surrogate["high"].tolist(), type=pa.float64()),
            "low": pa.array(surrogate["low"].tolist(), type=pa.float64()),
            "close": pa.array(surrogate["close"].tolist(), type=pa.float64()),
        }
    )


@dataclass
class BlockNullResult:
    """``n_runs`` seeded N2 surrogates' event counts — a null CONSTRUCTION
    result, not a verdict. The caller (WO-16, not this module) builds
    whatever concentration/arrangement statistic the claim actually tests."""

    base_seed: int
    n_runs: int
    block_bars: int
    event_counts: list[int] = field(default_factory=list)


def run_block_null(
    bars: pd.DataFrame,
    detector,
    *,
    base_seed: int,
    n_runs: int = 200,  # sealed, R2 (A-022)
    block_bars: int = BLOCK_BARS,
) -> BlockNullResult:
    """Run ``n_runs`` seeded N2 surrogates through the injected ``detector``.

    ``detector`` is duck-typed (``.detect(bars_table) -> pa.Table``, the real
    LiquiditySweepDetector's own shape) — the kernel never imports it, only
    calls what it is handed, exactly placebo.py's injection pattern. Seed i
    is ``base_seed + i`` (the Placebo convention, A-022 R4/D-022 item 4), so
    the whole run is reproducible and IVF-recomputable from the record alone.
    """
    if not isinstance(n_runs, int) or isinstance(n_runs, bool) or n_runs < 1:
        raise SchemaViolation("run_block_null: n_runs must be an int >= 1")
    if not isinstance(base_seed, int) or isinstance(base_seed, bool) or base_seed < 0:
        raise SchemaViolation("run_block_null: base_seed must be an int >= 0")

    counts: list[int] = []
    for i in range(n_runs):
        surrogate = resample_bar_blocks(bars, seed=base_seed + i, block_bars=block_bars)
        events = detector.detect(_to_detector_table(surrogate))
        counts.append(events.num_rows)
    return BlockNullResult(
        base_seed=int(base_seed), n_runs=int(n_runs), block_bars=int(block_bars),
        event_counts=counts,
    )

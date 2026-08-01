"""WO-02 (S1, refs A-002) — the liquidity-sweep detector's real ``level`` output,
consumed as a per-trade stop through ``ExecutionSpec.event_stop_column`` (ARCH-
NP-004 §4.1/§4.2, engine.s5.2). No new semantics: A-002's one ruling is that the
per-trade stop source for this lineage is the EventFrame's own frozen ``level``
column, exactly as the detector already emits it — this file only proves the
existing capability (built under WO-P, already covered by
tests/simulator/test_engine.py::test_ac2_...) also works end to end when driven
by the REAL :class:`LiquiditySweepDetector`, not just hand-built event rows.

Scenario (mirrors the ``tests/simulator/_micro_scenario.py`` pattern: one shared,
hand-documented ``build()`` feeding every assertion in this file): two liquidity-
sweep pools, back to back on one 30-bar detection window, chosen so the detector
emits two SWEEP events with two DIFFERENT ``level`` values from ONE real run —

  * bars 0-14 reproduce ``fixtures._high_pool_single_bar_sweep_bars()`` (a HIGH
    pool at 100.35, direction -1) verbatim;
  * bars 15-29 reproduce ``fixtures._low_pool_single_bar_sweep_bars()`` verbatim,
    offset by +15 bars. The two segments cannot interfere: segment A's ``low`` is
    flat 99.50 throughout (fixtures' own "-> no LOW pivots possible" design) and
    segment B's ``high`` is flat 100.50 throughout ("-> no HIGH pivots"), so
    neither segment ever contributes a pivot on the side the other needs, and the
    boundary between them never spans a strict local max/min.

Confirmed against a real run (not assumed): the detector emits exactly
  ts=14  sweep  direction=-1  level=100.35
  ts=29  sweep  direction=+1  level= 99.65

Trade A enters at bar 15 (open 100.10, chosen so R = |100.10 - 100.35| = 0.25).
Trade B enters at bar 30 (open 100.00, so R = |100.00 - 99.65| = 0.35) — a
DIFFERENT R from the SAME simulate() call, which is the whole point (AT-4-i).
Bars 30-35 are fresh (beyond the detector's own window; the detector never sees
them) and hand-priced so the SAME shared price path decides trade B differently
under the real per-trade stop than under a legacy constant borrowed from trade
A's own R (AT-4-iii).
"""

from __future__ import annotations

import pandas as pd
import pyarrow as pa
import pytest

from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.neelprajna.detector import LiquiditySweepDetector
from qrf.trading.simulator.engine import EventEngine, ExecutionSpec
from qrf.trading.simulator.fills import resolve_exit
from qrf.trading.utility.cost_models import load_cost_model

COST = load_cost_model("xauusd_retail_median")
HOLD_BARS = 5
TARGET_R = 1.5
N_DETECT = 30  # bars actually shown to the detector
N_ENGINE = 36  # bars 30-35 exist only for trade B's post-entry price path


def _detection_bars() -> pa.Table:
    h = [100.00] * N_DETECT
    low = [99.50] * N_DETECT
    c = [100.00] * N_DETECT
    # Segment A (0-14): HIGH pool + single-bar sweep-and-reclose (fixtures case A).
    h[3], h[10], h[14] = 100.20, 100.35, 100.45
    c[14] = 100.30
    # Segment B (15-29): LOW pool + single-bar sweep-and-reclose (fixtures case B).
    for i in range(15, N_DETECT):
        h[i] = 100.50
        low[i] = 100.00
    low[15 + 3], low[15 + 10], low[15 + 14] = 99.80, 99.65, 99.55
    c[15 + 14] = 99.70
    return pa.table(
        {"ts": pa.array(list(range(N_DETECT)), type=pa.int64()), "high": h, "low": low, "close": c}
    )


def _engine_bars(detection: pa.Table) -> pd.DataFrame:
    opens = [100.00] * N_ENGINE
    highs = [100.00] * N_ENGINE
    lows = [100.00] * N_ENGINE
    closes = [100.00] * N_ENGINE
    for i, (h, low, c) in enumerate(
        zip(
            detection.column("high").to_pylist(),
            detection.column("low").to_pylist(),
            detection.column("close").to_pylist(),
            strict=True,
        )
    ):
        highs[i], lows[i], closes[i] = h, low, c

    # Trade A (entry bar 15): stop (100.35) is touched immediately at bar 16,
    # since segment B's own flat high plateau (100.50) already exceeds it — a
    # deterministic consequence of the shared bars, not a separate contrivance.
    opens[15] = 100.10
    opens[16] = 100.10  # <= the stop, so the pessimistic gap-fill is exact (=level)

    # Trade B (entry bar 30): a rising path. Under the real stop/target
    # (99.65 / 100.525) it never dips to the stop and reaches the target at bar
    # 33. Under a legacy CONSTANT offset borrowed from trade A's own R (0.25 ->
    # stop 99.75 / target 100.375), the SAME path clears the nearer legacy
    # target one bar earlier, at bar 32 — the fixed-size target that fits trade
    # A's smaller risk cuts trade B's larger, correctly-sized move short.
    opens[30] = 100.00
    highs[31], lows[31] = 100.20, 99.90
    highs[32], lows[32] = 100.40, 100.00
    highs[33], lows[33] = 100.60, 100.30
    highs[34], lows[34] = 100.60, 100.30
    highs[35], lows[35] = 100.60, 100.30

    return pd.DataFrame(
        {"ts": list(range(N_ENGINE)), "open": opens, "high": highs, "low": lows, "close": closes}
    )


def build():
    """Shared scenario: (sweep events from the real detector, bars for the engine)."""
    detection = _detection_bars()
    events_all = LiquiditySweepDetector().detect(detection).to_pandas()
    sweeps = events_all[events_all["event_type"].str.endswith(".sweep")].reset_index(drop=True)
    return sweeps, _engine_bars(detection)


# --- the detector really does emit two different levels from one run ---------
def test_real_detector_emits_two_sweeps_with_different_levels():
    sweeps, _ = build()
    assert len(sweeps) == 2
    by_ts = {int(r.ts): r for r in sweeps.itertuples()}
    assert by_ts[14].direction == -1 and by_ts[14].level == 100.35
    assert by_ts[29].direction == 1 and by_ts[29].level == 99.65


# --- AT-4(i): the effective per-trade stop varies, driven by real detector output
def test_at4_i_effective_stop_varies_across_trades(tmp_path):
    before = len(RecordStore(tmp_path / "journal.jsonl"))
    sweeps, bars = build()
    exe = ExecutionSpec(hold_bars=HOLD_BARS, event_stop_column="level", target_r_multiple=TARGET_R)
    trades = EventEngine().simulate(bars, sweeps, COST, seed=1, execution=exe).trades
    assert len(trades) == 2

    a = next(t for t in trades if t.direction == -1)
    b = next(t for t in trades if t.direction == 1)
    r_a = abs(a.entry_price - 100.35)  # trade A's stop source: the real level
    r_b = abs(b.entry_price - 99.65)  # trade B's stop source: the real level
    assert r_a == pytest.approx(0.25) and r_b == pytest.approx(0.35)
    assert r_a != pytest.approx(r_b)  # not a constant — the whole point of event_stop_column

    after = len(RecordStore(tmp_path / "journal.jsonl"))
    assert after == before == 0  # zero ledger writes, asserted not narrated


# --- AT-4(ii): exits flow through the UNMODIFIED fills.resolve_exit -----------
def test_at4_ii_exits_flow_through_unmodified_resolve_exit():
    sweeps, bars = build()
    exe = ExecutionSpec(hold_bars=HOLD_BARS, event_stop_column="level", target_r_multiple=TARGET_R)
    trades = EventEngine().simulate(bars, sweeps, COST, seed=1, execution=exe).trades
    a = next(t for t in trades if t.direction == -1)
    b = next(t for t in trades if t.direction == 1)

    opens = bars["open"].tolist()
    highs = bars["high"].tolist()
    lows = bars["low"].tolist()
    ts_sorted = bars["ts"].tolist()

    # Calling the SAME primitive directly, with the per-trade distances the
    # engine itself must have derived from `level`, reproduces its trades
    # exactly — proving simulate() delegates rather than re-implementing.
    direct_a = resolve_exit(
        entry_index=15, direction=-1, entry_price=a.entry_price, hold_bars=HOLD_BARS,
        opens=opens, highs=highs, lows=lows,
        stop_offset=abs(a.entry_price - 100.35),
        target_offset=TARGET_R * abs(a.entry_price - 100.35),
        ts_sorted=ts_sorted, exit_rule="time_stop",
    )
    assert (direct_a.exit_index, direct_a.exit_price, direct_a.reason) == (
        16, a.exit_price, a.exit_reason,
    )

    direct_b = resolve_exit(
        entry_index=30, direction=1, entry_price=b.entry_price, hold_bars=HOLD_BARS,
        opens=opens, highs=highs, lows=lows,
        stop_offset=abs(b.entry_price - 99.65),
        target_offset=TARGET_R * abs(b.entry_price - 99.65),
        ts_sorted=ts_sorted, exit_rule="time_stop",
    )
    assert (direct_b.exit_index, direct_b.exit_price, direct_b.reason) == (
        33, b.exit_price, b.exit_reason,
    )


# --- AT-4(iii): differs from the legacy fixed-offset path, expected direction -
def test_at4_iii_differs_from_legacy_fixed_offset_in_expected_direction():
    sweeps, bars = build()
    real_exe = ExecutionSpec(
        hold_bars=HOLD_BARS, event_stop_column="level", target_r_multiple=TARGET_R
    )
    real = EventEngine().simulate(bars, sweeps, COST, seed=1, execution=real_exe).trades

    # Legacy: ONE constant offset for every trade, borrowed from trade A's own
    # real R (0.25) — the only R the legacy scalar mechanism could ever supply.
    legacy_exe = ExecutionSpec(hold_bars=HOLD_BARS, stop_offset=0.25, target_r_multiple=TARGET_R)
    legacy = EventEngine().simulate(bars, sweeps, COST, seed=1, execution=legacy_exe).trades

    real_a = next(t for t in real if t.direction == -1)
    real_b = next(t for t in real if t.direction == 1)
    legacy_a = next(t for t in legacy if t.direction == -1)
    legacy_b = next(t for t in legacy if t.direction == 1)

    # Trade A: legacy CONST *is* trade A's own real R, so both paths agree —
    # isolating the divergence below to trade B alone, not a general mismatch.
    assert (real_a.exit_price, real_a.exit_reason) == (legacy_a.exit_price, legacy_a.exit_reason)

    # Trade B: the borrowed, too-small legacy stop/target both sit closer to
    # entry than trade B's real, correctly-sized ones. Same shared price path,
    # different outcome: the legacy target is reached a bar EARLIER (100.375 at
    # bar 32) than the real target (100.525 at bar 33) — the fixed size cuts
    # the larger, correctly-scaled trade short.
    assert real_b.exit_reason == "target" and legacy_b.exit_reason == "target"
    assert real_b.exit_ts == 33 and legacy_b.exit_ts == 32
    assert real_b.exit_price > legacy_b.exit_price
    # Expected direction, sharpened: net of costs, the correctly-sized real
    # stop lets trade B close PROFITABLE; the borrowed legacy size does not.
    assert real_b.net_pnl > 0
    assert legacy_b.net_pnl < 0

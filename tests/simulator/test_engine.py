"""Audited engine tests (ARCH-005 §1, Blueprint §4.7, §7 S5).

Covers the acceptance criteria: the hand-computed micro-scenario (gross + net to
the cent), the no-look-ahead property (incremental feed, fills never change
retroactively), seeded byte-identical determinism (twice in one run AND across a
process restart), gross-vs-net divergence, next-open entry, dropped trades, short
side, intrabar stop/target with the pessimistic tie, the strength filter, the
Simulator type distinction (screener rejected), and the VIRGIN-reachability guard.
"""

from __future__ import annotations

import hashlib
import inspect
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from qrf.kernel.battery.simulator import (
    is_audited_simulator,
    require_audited_simulator,
)
from qrf.kernel.errors import SchemaViolation
from qrf.trading.simulator import engine as engine_mod
from qrf.trading.simulator.engine import EventEngine, ExecutionSpec
from qrf.trading.simulator.fills import entry_bar_index, resolve_exit
from qrf.trading.utility.cost_models import load_cost_model
from tests.simulator import _micro_scenario

REPO_ROOT = Path(__file__).resolve().parents[2]
COST = load_cost_model("xauusd_retail_median")  # cost_per_unit = 0.47


def _bars(opens, highs=None, lows=None):
    n = len(opens)
    o = np.asarray(opens, dtype=float)
    return pd.DataFrame(
        {
            "ts": list(range(n)),
            "open": o,
            "high": o if highs is None else np.asarray(highs, dtype=float),
            "low": o if lows is None else np.asarray(lows, dtype=float),
            "close": o,
        }
    )


def _events(pairs):
    return pd.DataFrame(
        {
            "ts": [p[0] for p in pairs],
            "direction": [p[1] for p in pairs],
            "strength": [p[2] if len(p) > 2 else 1.0 for p in pairs],
        }
    )


def _events_with_level(rows):
    """Like ``_events`` but each row also carries a ``level`` (event-sourced stop)."""
    return pd.DataFrame(
        {
            "ts": [r[0] for r in rows],
            "direction": [r[1] for r in rows],
            "strength": [1.0 for _ in rows],
            "level": [r[2] for r in rows],
        }
    )


# --- fills primitives --------------------------------------------------------
def test_entry_is_next_bar_strictly_after_signal():
    ts = [0, 1, 2, 3]
    assert entry_bar_index(0, ts) == 1  # not the signal bar itself
    assert entry_bar_index(1, ts) == 2
    assert entry_bar_index(3, ts) is None  # nothing after the last bar


def test_resolve_exit_time_stop_at_open():
    opens = [100.0, 100.0, 100.0, 107.0]
    fill = resolve_exit(
        entry_index=1, direction=1, entry_price=100.0, hold_bars=2,
        opens=opens, highs=opens, lows=opens, stop_offset=None, target_offset=None,
    )
    assert fill.exit_index == 3 and fill.exit_price == 107.0 and fill.reason == "time_stop"


def test_resolve_exit_returns_none_beyond_data():
    opens = [100.0, 100.0]
    assert resolve_exit(
        entry_index=1, direction=1, entry_price=100.0, hold_bars=2,
        opens=opens, highs=opens, lows=opens, stop_offset=None, target_offset=None,
    ) is None


# --- the hand-computed micro-scenario ---------------------------------------
def test_micro_scenario_gross_and_net_to_the_cent():
    trades = _micro_scenario.build()
    assert len(trades) == 3
    assert round(trades.gross_total(), 2) == 4.00
    assert round(trades.net_total(), 2) == 2.59
    per = {
        (t.direction, t.entry_price): (round(t.gross_pnl, 2), round(t.net_pnl, 2))
        for t in trades.trades
    }
    assert per[(1, 100.0)] == (5.00, 4.53)
    assert per[(1, 200.0)] == (-3.00, -3.47)
    assert per[(-1, 50.0)] == (2.00, 1.53)


def test_every_trade_charges_the_cost_model():
    for t in _micro_scenario.build().trades:
        assert round(t.cost, 2) == 0.47
        assert t.net_pnl == pytest.approx(t.gross_pnl - t.cost)


# --- gross vs net differ -----------------------------------------------------
def test_gross_and_net_differ_by_costs():
    trades = _micro_scenario.build()
    assert trades.gross_total() != trades.net_total()
    assert trades.net_total() == pytest.approx(trades.gross_total() - 3 * 0.47)


# --- next-open entry, not signal close --------------------------------------
def _one_trade(bars, direction, execution):
    return EventEngine().simulate(
        bars, _events([(0, direction)]), COST, seed=1, execution=execution
    )


def test_entry_fills_next_open_not_signal_bar():
    # Signal bar (ts0) close would be 100; the NEXT bar's open is 200 — entry must be 200.
    trades = _one_trade(_bars([100.0, 200.0, 200.0, 210.0]), 1, ExecutionSpec(hold_bars=2))
    assert len(trades) == 1
    assert trades.trades[0].entry_price == 200.0
    assert trades.trades[0].exit_price == 210.0


# --- short side --------------------------------------------------------------
def test_short_trade_pnl_sign():
    bars = _bars([100.0, 100.0, 100.0, 90.0])  # price falls -> a short profits
    t = _one_trade(bars, -1, ExecutionSpec(hold_bars=2)).trades[0]
    assert t.direction == -1
    assert t.gross_pnl == pytest.approx(10.0)  # (100 - 90)


# --- dropped when it cannot close, and the drop is REPORTED ------------------
def test_trade_dropped_when_exit_beyond_data():
    bars = _bars([100.0, 100.0, 100.0])  # entry at idx1, exit would be idx3 (absent)
    trades = _one_trade(bars, 1, ExecutionSpec(hold_bars=2))
    assert len(trades) == 0
    assert trades.n_dropped_tail == 1  # counted, not silent


def test_n_dropped_tail_counts_no_exit_and_no_entry():
    # 10 bars; hold 3. Events late enough that their exit (or entry) runs off the end.
    bars = _bars([100.0] * 10)
    # signal ts 9 -> no next bar (no entry); ts 8 -> entry 9, exit 12 (beyond);
    # ts 7 -> entry 8, exit 11 (beyond); ts 0 -> entry 1, exit 4 (fine, closes).
    events = _events([(0, 1), (7, 1), (8, 1), (9, 1)])
    trades = EventEngine().simulate(
        bars, events, COST, seed=1, execution=ExecutionSpec(hold_bars=3)
    )
    assert len(trades) == 1  # only the ts0 event closes
    assert trades.n_dropped_tail == 3  # the three tail events, all reported


def test_n_dropped_tail_is_in_the_canonical_image():
    bars = _bars([100.0, 100.0, 100.0])
    trades = _one_trade(bars, 1, ExecutionSpec(hold_bars=2))
    assert trades.canonical_payload()["n_dropped_tail"] == 1


# --- pessimistic gap-through, both ways --------------------------------------
def test_long_stop_gaps_through_fills_worse_at_open():
    # Long stop = 98; the held bar GAPS DOWN, opening at 95 (below the stop).
    bars = _bars(
        opens=[100.0, 100.0, 95.0, 100.0],
        highs=[100.0, 100.0, 96.0, 100.0],
        lows=[100.0, 100.0, 94.0, 100.0],
    )
    t = _one_trade(bars, 1, ExecutionSpec(hold_bars=2, stop_offset=2.0)).trades[0]
    assert t.exit_reason == "stop"
    assert t.exit_price == 95.0  # filled at the gapped open, worse than the 98 stop


def test_short_stop_gaps_through_fills_worse_at_open():
    # Short stop = 102; the held bar GAPS UP, opening at 105 (above the stop).
    bars = _bars(
        opens=[100.0, 100.0, 105.0, 100.0],
        highs=[100.0, 100.0, 106.0, 100.0],
        lows=[100.0, 100.0, 104.0, 100.0],
    )
    t = _one_trade(bars, -1, ExecutionSpec(hold_bars=2, stop_offset=2.0)).trades[0]
    assert t.exit_reason == "stop"
    assert t.exit_price == 105.0  # filled at the gapped open, worse than the 102 stop


def test_long_target_favorable_gap_is_capped_not_credited():
    # Long target = 102; the held bar GAPS UP, opening at 110 (well past the target).
    bars = _bars(
        opens=[100.0, 100.0, 110.0, 100.0],
        highs=[100.0, 100.0, 111.0, 100.0],
        lows=[100.0, 100.0, 109.0, 100.0],
    )
    t = _one_trade(bars, 1, ExecutionSpec(hold_bars=2, target_offset=2.0)).trades[0]
    assert t.exit_reason == "target"
    assert t.exit_price == 102.0  # capped at the target — the favorable gap is NOT credited


def test_short_target_favorable_gap_is_capped_not_credited():
    # Short target = 98; the held bar GAPS DOWN, opening at 90 (well past the target).
    bars = _bars(
        opens=[100.0, 100.0, 90.0, 100.0],
        highs=[100.0, 100.0, 91.0, 100.0],
        lows=[100.0, 100.0, 89.0, 100.0],
    )
    t = _one_trade(bars, -1, ExecutionSpec(hold_bars=2, target_offset=2.0)).trades[0]
    assert t.exit_reason == "target"
    assert t.exit_price == 98.0  # capped at the target


def test_non_gapping_touch_still_fills_at_the_level():
    # No gap: bar opens on the safe side (100) and only dips to the stop intrabar.
    bars = _bars(
        opens=[100.0, 100.0, 100.0, 100.0],
        highs=[100.0, 100.0, 101.0, 100.0],
        lows=[100.0, 100.0, 97.0, 100.0],
    )
    t = _one_trade(bars, 1, ExecutionSpec(hold_bars=2, stop_offset=2.0)).trades[0]
    assert t.exit_price == 98.0  # exact stop, no gap adjustment


# --- intrabar stop / target + pessimistic tie -------------------------------
def test_stop_hits_intrabar():
    bars = _bars(
        opens=[100.0, 100.0, 100.0, 100.0],
        highs=[100.0, 100.0, 101.0, 100.0],
        lows=[100.0, 100.0, 97.0, 100.0],
    )
    t = _one_trade(bars, 1, ExecutionSpec(hold_bars=2, stop_offset=2.0)).trades[0]
    assert t.exit_reason == "stop" and t.exit_price == 98.0  # stop = 100 - 2


def test_target_hits_intrabar():
    bars = _bars(
        opens=[100.0, 100.0, 100.0, 100.0],
        highs=[100.0, 100.0, 103.0, 100.0],
        lows=[100.0, 100.0, 99.0, 100.0],
    )
    t = _one_trade(bars, 1, ExecutionSpec(hold_bars=2, target_offset=2.0)).trades[0]
    assert t.exit_reason == "target" and t.exit_price == 102.0


def test_pessimistic_tie_stop_before_target():
    # One bar spans BOTH the stop (98) and the target (102): the stop must win.
    bars = _bars(
        opens=[100.0, 100.0, 100.0, 100.0],
        highs=[100.0, 100.0, 103.0, 100.0],
        lows=[100.0, 100.0, 97.0, 100.0],
    )
    exe = ExecutionSpec(hold_bars=2, stop_offset=2.0, target_offset=2.0)
    assert _one_trade(bars, 1, exe).trades[0].exit_reason == "stop"


# --- ARCH-NP-004 §4.1/§4.2 — per-trade event-sourced stop + R-multiple target ------
# AC-2: a hand-computed fixture with per-trade VARYING stops and a 1.5R target
# round-trips exactly. Two events share one bars frame, each with its own
# event-sourced stop (the "level" column), so the same hypothesis prices two
# different risk distances — impossible under the legacy scalar stop_offset.
#
# Hand computation:
#   A  long  @ ts0 -> entry ts1 open 100.0, event stop (level) = 95.0
#             R = |100.0 - 95.0| = 5.0; target = 100.0 + 1.5*5.0 = 107.5
#             bar ts3 high touches 107.5 first (no earlier stop touch) -> target, 107.5
#   B  short @ ts10-> entry ts11 open 200.0, event stop (level) = 206.0
#             R = |200.0 - 206.0| = 6.0; target = 200.0 - 1.5*6.0 = 191.0
#             bar ts13 low touches 191.0 first (no earlier stop touch) -> target, 191.0
def test_ac2_hand_computed_per_trade_stop_and_r_multiple_target():
    n = 17
    opens = [100.0] * n
    highs = list(opens)
    lows = list(opens)
    for i in range(10, n):
        opens[i] = 200.0
        highs[i] = 200.0
        lows[i] = 200.0
    highs[3] = 107.5   # event A's target touched here
    lows[13] = 191.0   # event B's target touched here
    bars = _bars(opens, highs, lows)

    events = _events_with_level([(0, 1, 95.0), (10, -1, 206.0)])
    exe = ExecutionSpec(hold_bars=5, event_stop_column="level", target_r_multiple=1.5)
    trades = EventEngine().simulate(bars, events, COST, seed=1, execution=exe).trades
    assert len(trades) == 2
    by_signal = {t.signal_ts: t for t in trades}

    a = by_signal[0]
    assert a.direction == 1 and a.entry_price == 100.0
    assert a.exit_reason == "target" and a.exit_price == 107.5

    b = by_signal[10]
    assert b.direction == -1 and b.entry_price == 200.0
    assert b.exit_reason == "target" and b.exit_price == 191.0


# AC-3: the both-levels-in-one-bar fixture, for the NEW per-trade/R-multiple path,
# still fills the STOP (the pessimistic tie, §4.3) — not just the legacy constant-
# offset path already covered by test_pessimistic_tie_stop_before_target above.
def test_ac3_pessimistic_tie_stop_before_target_per_trade_path():
    # Long entry 100.0, event stop (level) = 98.0 -> R = 2.0, target = 100 + 1.5*2 = 103.0.
    # One bar spans BOTH: low 97 (below the 98 stop) and high 103 (at the target).
    bars = _bars(
        opens=[100.0, 100.0, 100.0, 100.0],
        highs=[100.0, 100.0, 103.0, 100.0],
        lows=[100.0, 100.0, 97.0, 100.0],
    )
    events = _events_with_level([(0, 1, 98.0)])
    exe = ExecutionSpec(hold_bars=2, event_stop_column="level", target_r_multiple=1.5)
    t = EventEngine().simulate(bars, events, COST, seed=1, execution=exe).trades[0]
    assert t.exit_reason == "stop"
    assert t.exit_price == 98.0  # non-gapping touch, exact stop


# --- strength filter ---------------------------------------------------------
def test_strength_min_filters_weak_events():
    bars = _bars([100.0, 100.0, 100.0, 105.0])
    trades = EventEngine().simulate(
        bars, _events([(0, 1, 0.2)]), COST, seed=1,
        execution=ExecutionSpec(hold_bars=2, strength_min=0.5),
    )
    assert len(trades) == 0


# --- no look-ahead: incremental feed, closed trades never change -------------
def test_no_look_ahead_incremental_feed():
    rng = np.random.default_rng(7)
    n = 200
    opens = 100.0 + np.cumsum(rng.normal(0, 1, n))
    bars = _bars(opens, highs=opens + 0.5, lows=opens - 0.5)
    ev = _events([(i, 1 if (i // 7) % 2 == 0 else -1) for i in range(0, n, 7)])
    engine = EventEngine()
    exe = ExecutionSpec(hold_bars=3)
    full = engine.simulate(bars, ev, COST, seed=1, execution=exe)
    full_by_sig = {t.signal_ts: t for t in full.trades}
    assert full_by_sig  # the scenario actually produces trades

    for k in range(10, n + 1, 13):
        prefix = engine.simulate(bars.iloc[:k], ev, COST, seed=1, execution=exe)
        for t in prefix.trades:
            # Every trade closed in the prefix is byte-for-byte the full-run trade.
            assert t == full_by_sig[t.signal_ts], f"trade at signal {t.signal_ts} changed"


# AC-4: the anti-hindsight property, WITH the per-trade paths exercised (an
# event-sourced stop + R-multiple target, not just the legacy scalar offsets).
# The event stop is fixed from data at-or-before its own signal_ts (the signal
# bar's own open — knowable the instant the event fires), so it never depends on
# what a data prefix does or doesn't include beyond that point.
def test_ac4_no_look_ahead_incremental_feed_per_trade_paths():
    rng = np.random.default_rng(11)
    n = 200
    opens = 100.0 + np.cumsum(rng.normal(0, 1, n))
    bars = _bars(opens, highs=opens + 1.5, lows=opens - 1.5)
    rows = []
    for i in range(0, n, 7):
        direction = 1 if (i // 7) % 2 == 0 else -1
        level = opens[i] - 2.0 * direction  # adverse side, known at signal time
        rows.append((i, direction, level))
    ev = _events_with_level(rows)
    engine = EventEngine()
    exe = ExecutionSpec(hold_bars=3, event_stop_column="level", target_r_multiple=1.5)
    full = engine.simulate(bars, ev, COST, seed=1, execution=exe)
    full_by_sig = {t.signal_ts: t for t in full.trades}
    assert full_by_sig  # the scenario actually produces trades

    for k in range(10, n + 1, 13):
        prefix = engine.simulate(bars.iloc[:k], ev, COST, seed=1, execution=exe)
        for t in prefix.trades:
            assert t == full_by_sig[t.signal_ts], f"trade at signal {t.signal_ts} changed"


# --- determinism: byte-identical, twice + across a process restart -----------
def test_same_seed_byte_identical_twice():
    a = _micro_scenario.build().canonical_bytes()
    b = _micro_scenario.build().canonical_bytes()
    assert a == b


def test_byte_identical_across_process_restart():
    in_process = hashlib.sha256(_micro_scenario.build().canonical_bytes()).hexdigest()
    out = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tests" / "simulator" / "_micro_scenario.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == in_process


# --- the Simulator type distinction (screener rejected) ----------------------
def test_engine_is_an_audited_simulator():
    e = EventEngine()
    assert is_audited_simulator(e)
    require_audited_simulator(e)  # does not raise


def test_screener_is_not_an_audited_simulator():
    from qrf.trading.simulator.screener_vbt import Screener

    screener = Screener.__new__(Screener)  # no marker, no simulate()
    assert not is_audited_simulator(screener)
    with pytest.raises(TypeError):
        require_audited_simulator(screener)


def test_bare_object_rejected_as_simulator():
    with pytest.raises(TypeError):
        require_audited_simulator(object())


# --- validation --------------------------------------------------------------
def test_bad_hold_bars_rejected():
    with pytest.raises(SchemaViolation):
        ExecutionSpec(hold_bars=0)


# --- ARCH-NP-004 §4.5 — ExecutionSpec-level mirror of the registry refusals -------
def test_execspec_target_r_multiple_without_stop_rejected():
    with pytest.raises(SchemaViolation, match="target_r_multiple requires a stop"):
        ExecutionSpec(hold_bars=2, target_r_multiple=1.5)


def test_execspec_event_stop_column_unknown_rejected():
    with pytest.raises(SchemaViolation, match="EventFrame cannot supply it"):
        ExecutionSpec(hold_bars=2, event_stop_column="close")


def test_execspec_stop_offset_and_event_stop_column_mutually_exclusive():
    with pytest.raises(SchemaViolation, match="mutually exclusive"):
        ExecutionSpec(hold_bars=2, stop_offset=1.0, event_stop_column="level")


def test_execspec_target_offset_and_target_r_multiple_mutually_exclusive():
    with pytest.raises(SchemaViolation, match="mutually exclusive"):
        ExecutionSpec(hold_bars=2, stop_offset=1.0, target_offset=1.0, target_r_multiple=1.5)


def test_execspec_non_finite_stop_offset_rejected():
    with pytest.raises(SchemaViolation, match="finite"):
        ExecutionSpec(hold_bars=2, stop_offset=float("inf"))


def test_execspec_event_stop_column_and_target_r_multiple_roundtrip_through_dict():
    exe = ExecutionSpec(hold_bars=2, event_stop_column="level", target_r_multiple=1.5)
    d = exe.as_dict()
    assert d["event_stop_column"] == "level" and d["target_r_multiple"] == 1.5
    assert ExecutionSpec.from_dict(d) == exe


def test_execspec_legacy_dict_without_new_keys_still_parses():
    # A dict shaped exactly like every sealed hypothesis's execution (AC-1): no
    # event_stop_column / target_r_multiple keys at all.
    d = {"hold_bars": 4, "size": 1.0, "strength_min": 0.0, "stop_offset": None, "target_offset": None}
    exe = ExecutionSpec.from_dict(d)
    assert exe.event_stop_column is None and exe.target_r_multiple is None


def test_missing_bar_columns_rejected():
    with pytest.raises(SchemaViolation):
        EventEngine().simulate(
            pd.DataFrame({"ts": [0]}), _events([(0, 1)]), COST, seed=1,
            execution=ExecutionSpec(hold_bars=1),
        )


# --- VIRGIN reachability guard (out-of-scope §: no VIRGIN in any S5 path) -----
def test_engine_structurally_cannot_read_a_window():
    params = set(inspect.signature(EventEngine.simulate).parameters)
    assert {"store", "window", "window_ref"}.isdisjoint(params)
    src = Path(engine_mod.__file__).read_text(encoding="utf-8")
    assert "VIRGIN" not in src
    assert "WindowLedger" not in src and "designate" not in src

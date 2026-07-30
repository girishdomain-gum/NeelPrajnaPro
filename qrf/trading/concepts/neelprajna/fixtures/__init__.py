"""Planted-truth / clean-control fixtures for LiquiditySweepDetector (v1.1).

Every bar array below is hand-authored with the frozen parameters in mind
(``pivot_k=3``, ``pool_tol=30 ticks=0.30``, ``min_pen=5 ticks=0.05``,
``reclose_window=2 bars``, ``tick_size=0.01``) so the expected event list can
be derived by hand from the ADR's rules, independent of running the detector
(AC-1: "all plants caught, silence on clean" is only a real test if the
expectation was not just copied from the code's own output).

``ts`` is close-time int64 ns (OBS-4 convention), 300s (M5) bars, bar ``i``'s
``ts = (i + 1) * 300s``.
"""

from __future__ import annotations

import pyarrow as pa

_TF_NS = 300 * 1_000_000_000


def _bars(high: list[float], low: list[float], close: list[float]) -> pa.Table:
    n = len(high)
    assert len(low) == n and len(close) == n
    ts = [(i + 1) * _TF_NS for i in range(n)]
    return pa.table(
        {
            "ts": pa.array(ts, type=pa.int64()),
            "high": pa.array(high, type=pa.float64()),
            "low": pa.array(low, type=pa.float64()),
            "close": pa.array(close, type=pa.float64()),
        }
    )


# -- Case 1: HIGH-side pool, same-bar reclose (reclose_bars=0) --------------
# Two pivot highs at 2000.00 (bar 5) and 2000.20 (bar 15) — within pool_tol
# (0.30) of each other — cluster into a pool at the second pivot's
# confirmation bar (15+3=18), level = max(2000.00, 2000.20) = 2000.20. Bar 21
# wicks to 2000.35 (breach: 2000.35 >= 2000.20+0.05) and closes at 1999.90,
# already back below the level -> SWEEP fires same-bar (reclose_bars=0).
_C1_HIGH = [
    1990.00, 1991.00, 1992.00, 1993.00, 1994.00, 2000.00, 1994.00, 1993.00,
    1992.00, 1991.00, 1990.00, 1991.00, 1992.00, 1993.00, 1994.00, 2000.20,
    1994.00, 1993.00, 1992.00, 1991.00, 1991.00, 2000.35,
]
_C1_LOW = [
    1989.50, 1990.50, 1991.50, 1992.50, 1993.50, 1993.00, 1993.50, 1992.50,
    1991.50, 1990.50, 1989.50, 1990.50, 1991.50, 1992.50, 1993.50, 1993.00,
    1993.50, 1992.50, 1991.50, 1990.50, 1990.50, 1999.50,
]
_C1_CLOSE = [
    1989.80, 1990.80, 1991.80, 1992.80, 1993.80, 1995.00, 1993.80, 1992.80,
    1991.80, 1990.80, 1989.80, 1990.80, 1991.80, 1992.80, 1993.80, 1995.00,
    1993.80, 1992.80, 1991.80, 1990.80, 1990.80, 1999.90,
]
CASE_1_POOL_AND_IMMEDIATE_SWEEP = _bars(_C1_HIGH, _C1_LOW, _C1_CLOSE)
CASE_1_EXPECTED = [
    {"ts": 19 * _TF_NS, "event_type": "neelprajna.liquidity_sweep.pool_formed", "direction": 1},
    {"ts": 22 * _TF_NS, "event_type": "neelprajna.liquidity_sweep.sweep", "direction": 1},
]

# -- Case 2: LOW-side pool, delayed reclose (reclose_bars=2) ----------------
# Pivot lows at 2000.00 (bar 5) and 1999.90 (bar 15) cluster at bar 18,
# level = min(2000.00, 1999.90) = 1999.90. Bar 21 wicks to 1999.80 (breach:
# 1999.80 <= 1999.90-0.05) but closes at 1999.80 (no reclose); bar 22 dips
# deeper to 1999.75, closes 1999.85 (still no reclose); bar 23 closes 1999.95
# (> 1999.90) -> SWEEP fires at bar 23, reclose_bars=2, deepest wick 1999.75.
# ``high`` is a strictly increasing ramp far above the low/close action so it
# never forms a pivot of its own (an interior point of a monotonic sequence
# can never be a local extreme).
_C2_N = 24
_C2_HIGH = [2100.00 + i * 0.01 for i in range(_C2_N)]
_C2_LOW = [
    2010.00, 2009.00, 2008.00, 2007.00, 2006.00, 2000.00, 2006.00, 2007.00,
    2008.00, 2009.00, 2010.00, 2009.00, 2008.00, 2007.00, 2006.00, 1999.90,
    2006.00, 2007.00, 2008.00, 2009.00, 2009.00, 1999.80, 1999.75, 1999.78,
]
_C2_CLOSE = [
    2011.00, 2010.00, 2009.00, 2008.00, 2007.00, 2001.00, 2007.00, 2008.00,
    2009.00, 2010.00, 2011.00, 2010.00, 2009.00, 2008.00, 2007.00, 2000.90,
    2007.00, 2008.00, 2009.00, 2010.00, 2010.00, 1999.80, 1999.85, 1999.95,
]
assert len(_C2_LOW) == _C2_N and len(_C2_CLOSE) == _C2_N
CASE_2_LOW_POOL_DELAYED_RECLOSE = _bars(_C2_HIGH, _C2_LOW, _C2_CLOSE)
CASE_2_EXPECTED = [
    {"ts": 19 * _TF_NS, "event_type": "neelprajna.liquidity_sweep.pool_formed", "direction": -1},
    {"ts": 24 * _TF_NS, "event_type": "neelprajna.liquidity_sweep.sweep", "direction": -1},
]

# -- Case 3: flat clean control (specificity) --------------------------------
# Every bar identical: ties disqualify a pivot candidate at every neighbor
# comparison (the detector requires STRICT extremes), so zero pivots, zero
# pools, zero sweeps ever fire — the detector must stay silent on structure-
# free data (V&V §4.2).
_C3_N = 60
CASE_3_FLAT_CLEAN_CONTROL = _bars(
    [2000.00] * _C3_N, [1999.50] * _C3_N, [1999.75] * _C3_N
)

# -- Case 4: too short to ever confirm a pivot (insufficient) ---------------
# With pivot_k=3, confirming even one pivot needs a bar index >= 2*pivot_k;
# 4 bars can never reach that, so the detector is silent by construction —
# distinct from Case 3 (silent because nothing qualifies) vs silent because
# there isn't enough data to ever decide.
CASE_4_TOO_SHORT = _bars([2000.0, 2001.0, 2000.5, 2000.2], [1999.0, 2000.0, 1999.5, 1999.8],
                          [1999.5, 2000.5, 1999.8, 2000.0])


def liquidity_sweep_cases() -> list:
    from qrf.kernel.instruments.base import CalibrationCase

    return [
        CalibrationCase(
            case_id="pool_and_immediate_sweep",
            kind="planted_truth",
            data=CASE_1_POOL_AND_IMMEDIATE_SWEEP,
            expected=CASE_1_EXPECTED,
        ),
        CalibrationCase(
            case_id="low_pool_delayed_reclose",
            kind="planted_truth",
            data=CASE_2_LOW_POOL_DELAYED_RECLOSE,
            expected=CASE_2_EXPECTED,
        ),
        CalibrationCase(
            case_id="flat_clean_control",
            kind="planted_noise",
            data=CASE_3_FLAT_CLEAN_CONTROL,
            expected=[],
        ),
        CalibrationCase(
            case_id="too_short_for_confirmation",
            kind="insufficient",
            data=CASE_4_TOO_SHORT,
            expected=[],
        ),
    ]

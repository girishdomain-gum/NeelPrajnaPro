"""Hand-planted calibration fixtures for the SMC detectors (ARCH-004 §4).

Each planted case is a small OHLC bar table whose true events are constructed by
hand, so calibration checks the detector against a known answer, not against the
library it wraps. ``ts`` on every bar is ``TS0 + i * STEP``; an expected event's
``ts`` is the timestamp of its **knowability bar** (see the detector docstring),
not the bar the pattern is centred on.

The comparison basis (CalibrationHarness) is the sorted
``{ts, event_type, direction}`` descriptor set, so these bars are tuned to emit
*exactly* the listed events and nothing else. The order-block series are built
for ``swing_length`` in {2, 3}.
"""

from __future__ import annotations

import numpy as np
import pyarrow as pa

from qrf.kernel.instruments.base import CalibrationCase

# One hour per bar; an arbitrary but fixed epoch anchor (2024-01-02T02:00Z-ish).
STEP: int = 3600 * 10**9
TS0: int = 1704160800000000000


def _ts(n: int) -> np.ndarray:
    return np.array([TS0 + i * STEP for i in range(n)], dtype=np.int64)


def bars(o: list, h: list, low: list, c: list) -> pa.Table:
    """A bar table (ts + OHLC) for a planted case, ts = TS0 + i*STEP."""
    n = len(o)
    return pa.table(
        {
            "ts": _ts(n),
            "open": [float(x) for x in o],
            "high": [float(x) for x in h],
            "low": [float(x) for x in low],
            "close": [float(x) for x in c],
        }
    )


def _ev(index: int, event_type: str, direction: int) -> dict:
    """An expected descriptor at knowability bar ``index``."""
    return {"ts": int(TS0 + index * STEP), "event_type": event_type, "direction": direction}


# --- FVG series --------------------------------------------------------------
def _fvg_bull_bars() -> pa.Table:
    # Bar 1 (bullish) prints a gap between high[0]=10 and low[2]=12.0; the fourth
    # bar is engineered NOT to open a second gap (low[3]=11.4 <= high[1]=11.5).
    return bars(
        [9, 10.5, 12.5, 12.8],
        [10, 11.5, 13.5, 13.5],
        [8, 10.2, 12.0, 11.4],
        [9.5, 11.2, 13.2, 12.6],
    )


def _fvg_bear_bars() -> pa.Table:
    # Bar 1 (bearish) prints a gap-down between low[0]=10.5 and high[2]=9.0; the
    # fourth bar recovers so no second gap forms.
    return bars(
        [11, 10.5, 8.5, 8.6],
        [11.5, 10.8, 9.0, 10.6],
        [10.5, 10.2, 8.0, 8.4],
        [11.2, 9.8, 8.2, 10.4],
    )


def fvg_cases() -> list[CalibrationCase]:
    """FVG planted-truth, structured-noise silence, and insufficient cases."""
    # Structured noise: a choppy, wide, fully-overlapping sideways range — no gaps.
    amp = [0, 1, -1, 1, -1, 0, 1, -1, 1, -1, 0, 1, -1, 1, -1, 0]
    base = [100 + a for a in amp]
    noise = bars(base, [b + 3 for b in base], [b - 3 for b in base], [b + 0.2 for b in base])
    return [
        CalibrationCase(
            "fvg_bull_truth", "planted_truth", _fvg_bull_bars(),
            [_ev(2, "smc.fvg.bull", 1)],
        ),
        CalibrationCase(
            "fvg_bear_truth", "planted_truth", _fvg_bear_bars(),
            [_ev(2, "smc.fvg.bear", -1)],
        ),
        CalibrationCase("fvg_noise_silence", "planted_noise", noise, []),
        CalibrationCase(
            "fvg_insufficient", "insufficient",
            bars([1, 2], [1.5, 2.5], [0.5, 1.5], [1.2, 2.2]), [],
        ),
    ]


# --- Order-block series ------------------------------------------------------
def _ob_bull_bars() -> pa.Table:
    # Rise to a swing high (bar 5), pull back to the block bar (bar 9, the lowest
    # low), then a bullish break above high[5] prints at bar 13 -> the block is
    # knowable at bar 13.
    return bars(
        [10, 11, 12, 13, 14, 15, 14, 13, 12, 11, 12, 13, 15, 17, 18, 19, 20, 21],
        [10.4, 11.4, 12.4, 13.4, 14.4, 15.5, 14.4, 13.4, 12.4, 11.4, 12.4, 13.4,
         15.4, 17.4, 18.4, 19.4, 20.4, 21.4],
        [9.6, 10.6, 11.6, 12.6, 13.6, 14.6, 13.6, 12.6, 11.6, 10.6, 11.6, 12.6,
         14.6, 16.6, 17.6, 18.6, 19.6, 20.6],
        [10.2, 11.2, 12.2, 13.2, 14.2, 15.2, 14.0, 13.0, 12.0, 11.0, 12.2, 13.2,
         15.2, 17.2, 18.2, 19.2, 20.2, 21.2],
    )


def _ob_bear_bars() -> pa.Table:
    # Mirror of the bull case: fall to a swing low (bar 5), bounce to the block
    # bar (bar 9, the highest high), then a bearish break below low[5] at bar 13.
    return bars(
        [21, 20, 19, 18, 17, 16, 17, 18, 19, 20, 19, 18, 16, 14, 13, 12, 11, 10],
        [21.4, 20.4, 19.4, 18.4, 17.4, 16.5, 17.4, 18.4, 19.4, 20.4, 19.4, 18.4,
         16.4, 14.4, 13.4, 12.4, 11.4, 10.4],
        [20.6, 19.6, 18.6, 17.6, 16.6, 15.5, 16.6, 17.6, 18.6, 19.6, 18.6, 17.6,
         15.6, 13.6, 12.6, 11.6, 10.6, 9.6],
        [20.8, 19.8, 18.8, 17.8, 16.8, 15.8, 17.0, 18.0, 19.0, 20.0, 18.8, 17.8,
         15.8, 13.8, 12.8, 11.8, 10.8, 9.8],
    )


def order_block_cases(*, swing_length: int = 3) -> list[CalibrationCase]:
    """Order-block planted-truth, structured-noise silence, and insufficient cases.

    Tuned for ``swing_length`` in {2, 3}: the planted swing is the extreme over
    its window and the break prints at bar 13 in both the bull and bear series.
    """
    # Structured noise: a wide, overlapping, drifting range with no pullback that
    # breaks structure -> no order block forms.
    n = 16
    base = [100 + i for i in range(n)]
    noise = bars(base, [b + 3 for b in base], [b - 3 for b in base], [b + 0.3 for b in base])
    return [
        CalibrationCase(
            "ob_bull_truth", "planted_truth", _ob_bull_bars(),
            [_ev(13, "smc.order_block.bull", 1)],
        ),
        CalibrationCase(
            "ob_bear_truth", "planted_truth", _ob_bear_bars(),
            [_ev(13, "smc.order_block.bear", -1)],
        ),
        CalibrationCase("ob_noise_silence", "planted_noise", noise, []),
        CalibrationCase(
            "ob_insufficient", "insufficient",
            bars([1, 2, 3], [1.5, 2.5, 3.5], [0.5, 1.5, 2.5], [1.2, 2.2, 3.2]), [],
        ),
    ]

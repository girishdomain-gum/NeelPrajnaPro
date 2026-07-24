"""Planted fixtures for the RSI detector — built in code, not downloaded.

ARCH-002 asks for hand-CONSTRUCTED bar series: a textbook truth case and a
structured-noise silence case. All series are deterministic; timestamps are
hourly UTC nanoseconds from a fixed anchor (the calendar value is irrelevant to
RSI — only monotonic order matters).

The planted crossings are author-determined from the deterministic construction
and pinned against ``pandas-ta==0.4.71b0`` (NOTE-004). They assume ``period=14``
(the detector default and the canonical calibration config); the test locks them,
so any dependency drift fails loudly rather than silently.
"""

from __future__ import annotations

import math

import pyarrow as pa

from qrf.kernel.instruments.base import CalibrationCase

_NS = 1_000_000_000
_HOUR = 3600 * _NS
_BASE = 1_704_067_200 * _NS  # 2024-01-01 00:00 UTC, hourly bars (order-only anchor)

# Truth-case crossing bar indices for period=14 (observed from the construction
# below; overbought on the rise at bar 21, oversold on the fall at bar 52).
_OVERBOUGHT_BAR = 21
_OVERSOLD_BAR = 52


def _bars(closes: list[float]) -> pa.Table:
    ts = [_BASE + i * _HOUR for i in range(len(closes))]
    return pa.table(
        {"ts": pa.array(ts, type=pa.int64()), "close": pa.array(closes, type=pa.float64())}
    )


def _truth_closes() -> list[float]:
    """A 'tent': zigzag warm-up (defines RSI ~50), a steady rise through 70, a
    steady fall through 30. Produces exactly one overbought and one oversold
    crossing, both well past the warm-up region."""
    closes = [100.0]
    for i in range(1, 20):  # zigzag warm-up -> RSI defined near 50
        closes.append(closes[-1] + (0.5 if i % 2 == 1 else -0.5))
    for _ in range(21):  # steady rise: RSI climbs up through 70
        closes.append(closes[-1] + 1.0)
    for _ in range(35):  # steady fall: RSI drops down through 30
        closes.append(closes[-1] - 1.5)
    return closes


def _noise_closes() -> list[float]:
    """Structured noise: a fast per-bar alternating carrier + slow sine envelope +
    gentle drift. Steady-state RSI sits in ~[43, 53]; the only near-band values are
    the RMA warm-up transient (indices < period), which the detector excludes — so
    this case also guards the warm-up boundary. Silent for period=14."""
    af, asl, ksl, drift, nb = 1.2, 0.35, 22.0, 0.02, 140
    return [100.0 + drift * i + af * ((-1) ** i) + asl * math.sin(i / ksl) for i in range(nb)]


def _desc(bar: int, event_type: str, direction: int) -> dict:
    return {"ts": int(_BASE + bar * _HOUR), "event_type": event_type, "direction": direction}


def rsi_cases(period: int = 14) -> list[CalibrationCase]:
    """The full planted suite for the RSI detector (truth pinned for period=14)."""
    if period != 14:
        raise ValueError(
            "rsi_cases planted crossings are pinned for period=14; "
            f"got period={period}. Recompute the truth case for other periods."
        )
    expected = [
        _desc(_OVERBOUGHT_BAR, "classical.rsi.overbought_cross", -1),
        _desc(_OVERSOLD_BAR, "classical.rsi.oversold_cross", +1),
    ]
    expected.sort(key=lambda r: (r["ts"], r["event_type"], r["direction"]))

    truth = CalibrationCase(
        case_id="tent_one_overbought_one_oversold", kind="planted_truth",
        data=_bars(_truth_closes()), expected=expected,
    )
    noise = CalibrationCase(
        case_id="alternating_carrier_in_band", kind="planted_noise",
        data=_bars(_noise_closes()), expected=[],
    )
    # Fewer than period+1 bars -> cannot warm up -> silent.
    insufficient = CalibrationCase(
        case_id="too_few_bars", kind="insufficient",
        data=_bars([100.0 + (i % 3) for i in range(period)]), expected=[],
    )
    return [truth, noise, insufficient]

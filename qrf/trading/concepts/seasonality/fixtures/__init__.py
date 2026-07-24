"""Planted fixtures for the seasonality detector — built in code, not downloaded.

ARCH-002 asks for hand-CONSTRUCTED bar series (textbook truth + a silence case)
rather than downloaded data. Everything here is deterministic integer arithmetic
on UTC nanosecond timestamps, so the expected events are exact.

Calibration configuration these cases target (``CANONICAL_PARAMS``): a single
UTC session ``london`` = 08:00–16:00, day-of-week markers on. Calibrate a
``SeasonalityDetector(params=CANONICAL_PARAMS)`` against :func:`seasonality_cases`.

Anchor day: 2024-01-01 00:00:00 UTC, which is a **Monday** — verified below by the
same weekday formula the detector uses, so the fixture cannot silently drift onto
the wrong weekday.
"""

from __future__ import annotations

import pyarrow as pa

from qrf.kernel.instruments.base import CalibrationCase

_NS = 1_000_000_000
_HOUR = 3600 * _NS
_DAY = 24 * _HOUR

# 2024-01-01 00:00:00 UTC in seconds -> ns. Epoch-day 19723; (19723+3)%7 == 0 == Mon.
_MON_2024_01_01 = 1_704_067_200 * _NS
# 2024-01-06 00:00:00 UTC — a Saturday (epoch-day 19728; (19728+3)%7 == 5 == Sat).
_SAT_2024_01_06 = _MON_2024_01_01 + 5 * _DAY

# London session as UTC seconds-of-day, [start, end).
CANONICAL_PARAMS: dict = {
    "sessions": {"london": [8 * 3600, 16 * 3600]},
    "emit_dow": True,
}

# Sanity: assert the anchor really is a Monday, using the detector's own rule.
_WEEKDAY_NAMES = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _weekday(ts_ns: int) -> str:
    return _WEEKDAY_NAMES[((ts_ns // _NS // 86_400) + 3) % 7]


assert _weekday(_MON_2024_01_01) == "mon", "anchor day is not a Monday — fixture drift"
assert _weekday(_SAT_2024_01_06) == "sat", "silence-case day is not a Saturday"


def _bars(ts_values: list[int]) -> pa.Table:
    """A minimal bar table — the seasonality detector needs only ``ts``."""
    return pa.table({"ts": pa.array(ts_values, type=pa.int64())})


def _desc(ts: int, event_type: str) -> dict:
    return {"ts": int(ts), "event_type": event_type, "direction": 0}


def _planted_truth_case() -> CalibrationCase:
    """Three UTC days of hourly bars (Mon–Wed); london 08:00–16:00, dow on.

    Per day: a dow marker at hour 0, a session open at hour 08, a session close
    at hour 16. Weekdays only (all three are Mon/Tue/Wed), so every dow fires.
    """
    ts_values = [_MON_2024_01_01 + h * _HOUR for h in range(72)]  # 3 days, hourly
    expected: list[dict] = []
    for day, name in enumerate(("mon", "tue", "wed")):
        day0 = _MON_2024_01_01 + day * _DAY
        expected.append(_desc(day0 + 0 * _HOUR, f"seasonality.dow.{name}"))
        expected.append(_desc(day0 + 8 * _HOUR, "seasonality.session.open"))
        expected.append(_desc(day0 + 16 * _HOUR, "seasonality.session.close"))
    expected.sort(key=lambda r: (r["ts"], r["event_type"], r["direction"]))
    return CalibrationCase(
        case_id="three_weekdays_london", kind="planted_truth",
        data=_bars(ts_values), expected=expected,
    )


def _planted_noise_case() -> CalibrationCase:
    """Saturday pre-session bars: weekend (no dow) + outside london -> silence."""
    ts_values = [_SAT_2024_01_06 + h * _HOUR for h in range(7)]  # hours 0..6 Sat
    return CalibrationCase(
        case_id="saturday_presession_silent", kind="planted_noise",
        data=_bars(ts_values), expected=[],
    )


def _insufficient_case() -> CalibrationCase:
    """A single weekend, out-of-session bar: too little to observe any transition."""
    ts_values = [_SAT_2024_01_06 + 3 * _HOUR]
    return CalibrationCase(
        case_id="single_bar_weekend", kind="insufficient",
        data=_bars(ts_values), expected=[],
    )


def seasonality_cases() -> list[CalibrationCase]:
    """The full planted suite for the seasonality detector."""
    return [_planted_truth_case(), _planted_noise_case(), _insufficient_case()]

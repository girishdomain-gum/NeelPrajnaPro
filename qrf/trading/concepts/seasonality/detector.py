"""Seasonality detector (DIY, detector #1) — session and day-of-week markers.

ARCH-002 §Trading plug-in. Deliberately simple: its job this sprint is to prove
the EventFrame + calibration contract, not to be clever. It emits, over a bar
series:

* ``seasonality.session.open`` / ``.close`` for each named session, at the bar
  where membership of that session's UTC window transitions in / out;
* ``seasonality.dow.<mon..fri>`` at the first bar of each UTC calendar weekday
  (weekends emit nothing).

**Timezone contract (DEVQ-002, proceeding on option A).** Input bars carry a
``ts`` column of ``int64`` nanoseconds since the UTC epoch — the same knowability
contract as the EventFrame ``ts``. Sessions are named UTC windows given in
seconds-of-day; day-of-week is computed in UTC. Broker-local-timezone
sessionization is a Sprint-3 adapter concern, out of scope here.

**Anti-hindsight.** Every emitted event depends only on the current bar and its
immediate predecessor (a membership transition, or a calendar-day change), so an
event's ``ts`` is the first bar at which the transition is observable and
previously emitted events never change as more bars arrive.

EventFrame semantics for this detector: ``direction = 0`` (calendar markers are
directionless), ``level``/``zone_hi``/``zone_lo`` are NaN (point events; a
``level_na`` flag is set in ``meta``), ``strength = 1.0`` (a marker either fires
or it does not). ``meta`` is a JSON object naming the session or weekday.
"""

from __future__ import annotations

import json
import math
from typing import Any

import pyarrow as pa

from qrf.kernel.instruments.base import CalibrationCase, build_event_frame

_NS_PER_SEC = 1_000_000_000
_SECS_PER_DAY = 86_400
# 1970-01-01 (UTC) was a Thursday; Monday=0 => offset 3 so epoch-day 0 -> Thu(3).
_EPOCH_WEEKDAY_OFFSET = 3
_WEEKDAY_NAMES = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
_WEEKDAYS = frozenset({"mon", "tue", "wed", "thu", "fri"})

# Default UTC sessions (seconds-of-day, [start, end)); overridable via params.
_DEFAULT_SESSIONS: dict[str, list[int]] = {
    "london": [8 * 3600, 16 * 3600],
    "newyork": [13 * 3600, 22 * 3600],
}


def _second_of_day(ts_ns: int) -> int:
    return (ts_ns // _NS_PER_SEC) % _SECS_PER_DAY


def _epoch_day(ts_ns: int) -> int:
    return (ts_ns // _NS_PER_SEC) // _SECS_PER_DAY


def _weekday_name(ts_ns: int) -> str:
    return _WEEKDAY_NAMES[(_epoch_day(ts_ns) + _EPOCH_WEEKDAY_OFFSET) % 7]


class SeasonalityDetector:
    """Session-open/close and day-of-week markers over UTC bar timestamps."""

    instrument_id = "seasonality.calendar"
    family = "seasonality"
    kind = "detector"
    code_ref = "qrf.trading.concepts.seasonality.detector:SeasonalityDetector"

    # Params validated against this schema when registered.
    params_schema = {
        "sessions": "dict[str, [start_sec:int, end_sec:int]]  # UTC seconds-of-day, [start,end)",
        "emit_dow": "bool  # emit seasonality.dow.<mon..fri> at each UTC day start",
    }

    def __init__(self, *, version: str = "0.1.0", params: dict[str, Any] | None = None) -> None:
        self.version = version
        params = dict(params or {})
        sessions = params.get("sessions", _DEFAULT_SESSIONS)
        # Normalize + validate session windows.
        norm: dict[str, tuple[int, int]] = {}
        for name, window in sessions.items():
            start, end = int(window[0]), int(window[1])
            if not (0 <= start < end <= _SECS_PER_DAY):
                raise ValueError(
                    f"session {name!r} window {window} must satisfy "
                    f"0 <= start < end <= {_SECS_PER_DAY}"
                )
            norm[name] = (start, end)
        self._sessions = norm
        self._emit_dow = bool(params.get("emit_dow", True))
        self.params = {
            "sessions": {k: [v[0], v[1]] for k, v in norm.items()},
            "emit_dow": self._emit_dow,
        }

    # -- detection ------------------------------------------------------------
    def detect(self, data: pa.Table) -> pa.Table:
        """Emit calendar markers for the bars in ``data`` (needs a ``ts`` column)."""
        if "ts" not in data.column_names:
            from qrf.kernel.errors import SchemaViolation

            raise SchemaViolation("seasonality detector requires a 'ts' column (int64 ns UTC)")
        ts_list = data.column("ts").to_pylist()

        rows: list[dict[str, Any]] = []
        prev_ts: int | None = None
        # Per-session membership of the previous bar (False before the first bar).
        prev_member = {name: False for name in self._sessions}

        for ts in ts_list:
            ts = int(ts)
            sod = _second_of_day(ts)

            # Day-of-week marker at the first bar of each new UTC calendar day.
            if self._emit_dow and (prev_ts is None or _epoch_day(ts) != _epoch_day(prev_ts)):
                name = _weekday_name(ts)
                if name in _WEEKDAYS:
                    rows.append(self._marker(ts, f"seasonality.dow.{name}", {"dow": name}))

            # Session open/close on membership transitions.
            for sname, (start, end) in self._sessions.items():
                member = start <= sod < end
                if member and not prev_member[sname]:
                    rows.append(
                        self._marker(ts, "seasonality.session.open", {"session": sname})
                    )
                elif not member and prev_member[sname]:
                    rows.append(
                        self._marker(ts, "seasonality.session.close", {"session": sname})
                    )
                prev_member[sname] = member

            prev_ts = ts

        return build_event_frame(rows)

    @staticmethod
    def _marker(ts: int, event_type: str, extra: dict[str, Any]) -> dict[str, Any]:
        meta = {"level_na": True, **extra}
        return {
            "ts": ts,
            "event_type": event_type,
            "direction": 0,
            "level": math.nan,
            "zone_hi": math.nan,
            "zone_lo": math.nan,
            "strength": 1.0,
            "meta": json.dumps(meta, sort_keys=True),
        }

    # -- calibration ----------------------------------------------------------
    def planted_cases(self) -> list[CalibrationCase]:
        """Planted truth / silence suite (built in fixture code, not downloaded)."""
        from qrf.trading.concepts.seasonality.fixtures import seasonality_cases

        return seasonality_cases()

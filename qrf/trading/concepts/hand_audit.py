"""Hand-audit hook — print sampled detector events with their source bars.

ARCH-002 AC: a tiny helper for the Owner's Sprint-2 human check (IVF §7 S2),
showing N events from a detector run alongside the bar that produced each, so a
human can eyeball that the events are real. Deterministic sampling (fixed step,
no RNG) keeps the output reproducible for sign-off.

Covered by tests. (The Sprint-2 CLI ``scripts/hand_audit_s2.py`` was renamed to
``scripts/calibration_audit_s2.py`` in ARCH-003, which now inspects the planted
calibration suite directly rather than via this hook.)
"""

from __future__ import annotations

import json
from typing import Any

import pyarrow as pa

_NS = 1_000_000_000
_HOUR = 3600 * _NS
_BASE = 1_704_067_200 * _NS  # 2024-01-01 00:00 UTC (a Monday), hourly bars


def seasonality_demo_bars(days: int = 10) -> pa.Table:
    """``days`` of hourly UTC bars — many session opens/closes + weekday markers."""
    ts = [_BASE + h * _HOUR for h in range(days * 24)]
    return pa.table({"ts": pa.array(ts, type=pa.int64())})


def rsi_demo_bars(cycles: int = 6) -> pa.Table:
    """Repeated rise/fall cycles -> several overbought/oversold crossings."""
    closes = [100.0]
    for _ in range(20):  # zigzag warm-up so RSI is defined near 50
        closes.append(closes[-1] + (0.5 if len(closes) % 2 else -0.5))
    for _ in range(cycles):
        for _ in range(20):
            closes.append(closes[-1] + 1.2)  # rise through overbought
        for _ in range(28):
            closes.append(closes[-1] - 1.2)  # fall through oversold
    ts = [_BASE + i * _HOUR for i in range(len(closes))]
    return pa.table(
        {
            "ts": pa.array(ts, type=pa.int64()),
            "close": pa.array(closes, type=pa.float64()),
        }
    )


def sample_events_with_bars(
    detector: Any, data: pa.Table, *, n: int = 10
) -> list[dict[str, Any]]:
    """Return up to ``n`` events from ``detector.detect(data)``, each joined to its
    source bar (the bar whose ``ts`` equals the event ``ts``).

    Sampling is a deterministic even stride across the emitted events, so a run
    with more than ``n`` events still yields a representative, reproducible slice.
    """
    events = detector.detect(data)
    total = events.num_rows
    if total == 0:
        return []

    bar_ts = data.column("ts").to_pylist()
    bar_index = {int(t): i for i, t in enumerate(bar_ts)}
    bar_cols = {name: data.column(name).to_pylist() for name in data.column_names}

    ev = {name: events.column(name).to_pylist() for name in events.column_names}
    step = max(1, total // n)
    picks = list(range(0, total, step))[:n]

    out: list[dict[str, Any]] = []
    for j in picks:
        ts = int(ev["ts"][j])
        src_i = bar_index.get(ts)
        source_bar = (
            {name: bar_cols[name][src_i] for name in bar_cols} if src_i is not None else None
        )
        out.append(
            {
                "event_type": ev["event_type"][j],
                "ts": ts,
                "direction": int(ev["direction"][j]),
                "level": ev["level"][j],
                "meta": json.loads(ev["meta"][j]),
                "source_bar": source_bar,
            }
        )
    return out


def format_audit(detector: Any, data: pa.Table, *, n: int = 10) -> str:
    """A human-readable block for ``n`` sampled events of one detector run."""
    ident = f"{detector.instrument_id}@{detector.version}"
    lines = [f"# hand-audit: {ident} - up to {n} events with source bars"]
    rows = sample_events_with_bars(detector, data, n=n)
    if not rows:
        lines.append("  (no events emitted)")
        return "\n".join(lines)
    for r in rows:
        lines.append(
            f"  ts={r['ts']} {r['event_type']} dir={r['direction']:+d} "
            f"level={r['level']} meta={r['meta']} src_bar={r['source_bar']}"
        )
    return "\n".join(lines)

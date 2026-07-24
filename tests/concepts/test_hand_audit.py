"""Hand-audit hook test (ARCH-002 AC: 10 events per detector with source bars)."""

from __future__ import annotations

from qrf.trading.concepts.classical import RSIDetector
from qrf.trading.concepts.hand_audit import (
    format_audit,
    rsi_demo_bars,
    sample_events_with_bars,
    seasonality_demo_bars,
)
from qrf.trading.concepts.seasonality import SeasonalityDetector


def test_seasonality_audit_yields_ten_events_with_source_bars():
    det = SeasonalityDetector(
        params={"sessions": {"london": [8 * 3600, 16 * 3600]}, "emit_dow": True}
    )
    rows = sample_events_with_bars(det, seasonality_demo_bars(days=10), n=10)
    assert len(rows) == 10
    for r in rows:
        assert r["source_bar"] is not None
        assert r["source_bar"]["ts"] == r["ts"]  # event joined to its own bar


def test_rsi_audit_yields_ten_events_with_source_bars():
    det = RSIDetector()
    rows = sample_events_with_bars(det, rsi_demo_bars(cycles=6), n=10)
    assert len(rows) == 10
    for r in rows:
        assert r["source_bar"] is not None
        assert r["level"] == r["source_bar"]["close"]  # RSI level == bar close


def test_empty_run_audits_cleanly():
    det = RSIDetector()
    # Too few bars -> no events -> empty audit, no crash.
    import pyarrow as pa

    data = pa.table({"ts": pa.array([1, 2], type=pa.int64()),
                     "close": pa.array([1.0, 2.0], type=pa.float64())})
    assert sample_events_with_bars(det, data, n=10) == []
    assert "no events" in format_audit(det, data)

"""RSI detector tests (Blueprint §4.3, ARCH-002 AC).

Planted-truth exact crossings/ts; structured-noise silence; the anti-hindsight
incremental-consistency property; params round-trip; knowability (event ts is the
completing bar's close time) and warm-up exclusion.
"""

from __future__ import annotations

import json

import pyarrow as pa
import pytest

from qrf.kernel.instruments.base import validate_event_frame
from qrf.kernel.instruments.calibration import descriptors
from qrf.trading.concepts.classical import RSIDetector


def test_planted_truth_exact_crossings():
    det = RSIDetector()
    truth = det.planted_cases()[0]
    got = descriptors(det.detect(truth.data))
    assert got == truth.expected
    # Exactly one overbought (dir -1) then one oversold (dir +1).
    assert [d["event_type"] for d in got] == [
        "classical.rsi.overbought_cross",
        "classical.rsi.oversold_cross",
    ]
    assert [d["direction"] for d in got] == [-1, 1]


def test_event_ts_is_completing_bar_close_and_level_is_price():
    det = RSIDetector()
    truth = det.planted_cases()[0]
    frame = det.detect(truth.data)
    validate_event_frame(frame)
    ts_bars = truth.data.column("ts").to_pylist()
    close_bars = truth.data.column("close").to_pylist()
    ev_ts = frame.column("ts").to_pylist()
    ev_level = frame.column("level").to_pylist()
    ev_meta = frame.column("meta").to_pylist()
    for t, lvl, meta in zip(ev_ts, ev_level, ev_meta, strict=True):
        # ts is an actual bar ts (a close/knowability time), never between bars.
        assert t in ts_bars
        idx = ts_bars.index(t)
        assert lvl == close_bars[idx]  # level == bar close (price level)
        assert "rsi" in json.loads(meta)  # RSI value carried in meta


def test_structured_noise_is_silent():
    det = RSIDetector()
    noise = det.planted_cases()[1]
    assert det.detect(noise.data).num_rows == 0


def test_insufficient_data_is_silent_not_error():
    det = RSIDetector(params={"period": 14})
    # Fewer than period+1 bars -> silent, no exception.
    data = pa.table({
        "ts": pa.array([i for i in range(10)], type=pa.int64()),
        "close": pa.array([100.0 + i for i in range(10)], type=pa.float64()),
    })
    assert det.detect(data).num_rows == 0


def test_no_repeat_event_while_beyond_threshold():
    """Crossings fire once, not on every bar RSI stays beyond the band."""
    det = RSIDetector()
    got = descriptors(det.detect(det.planted_cases()[0].data))
    # The tent stays overbought for many bars and oversold for many bars, yet
    # only one crossing of each is emitted.
    assert len(got) == 2


def test_incremental_consistency_property():
    """Prefixes never retroactively change emitted crossings (anti-hindsight)."""
    det = RSIDetector()
    data = det.planted_cases()[0].data
    ts_all = data.column("ts").to_pylist()
    full = descriptors(det.detect(data))
    for k in range(1, data.num_rows + 1):
        prefix = descriptors(det.detect(data.slice(0, k)))
        expected_prefix = [d for d in full if d["ts"] <= ts_all[k - 1]]
        assert prefix == expected_prefix


def test_params_roundtrip():
    det = RSIDetector(params={"period": 21, "overbought": 80, "oversold": 20})
    assert det.params == {"period": 21, "overbought": 80.0, "oversold": 20.0}
    assert det.instrument_id == "classical.rsi"
    assert det.family == "classical"


def test_invalid_params_rejected():
    with pytest.raises(ValueError):
        RSIDetector(params={"period": 0})
    with pytest.raises(ValueError):
        RSIDetector(params={"overbought": 20, "oversold": 80})  # inverted band

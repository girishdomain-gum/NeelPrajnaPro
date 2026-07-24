"""Seasonality detector tests (Blueprint §4.3, ARCH-002 AC).

Planted-truth exact events/ts; structured-noise silence; the anti-hindsight
incremental-consistency property; params round-trip.
"""

from __future__ import annotations

import json

import pyarrow as pa

from qrf.kernel.instruments.base import validate_event_frame
from qrf.kernel.instruments.calibration import descriptors
from qrf.trading.concepts.seasonality import SeasonalityDetector
from qrf.trading.concepts.seasonality import fixtures as SF


def _det():
    return SeasonalityDetector(params=SF.CANONICAL_PARAMS)


def test_planted_truth_exact_events_and_ts():
    det = _det()
    truth = det.planted_cases()[0]
    got = descriptors(det.detect(truth.data))
    assert got == truth.expected
    # Emits the expected 9 markers over three UTC weekdays (3 dow + 3 open + 3 close).
    assert len(got) == 9
    types = [d["event_type"] for d in got]
    assert types.count("seasonality.session.open") == 3
    assert types.count("seasonality.session.close") == 3
    assert sum(t.startswith("seasonality.dow.") for t in types) == 3


def test_output_is_valid_eventframe_with_meta_flags():
    det = _det()
    frame = det.detect(det.planted_cases()[0].data)
    validate_event_frame(frame)
    # Calendar markers are directionless point events with a level_na meta flag.
    for direction in frame.column("direction").to_pylist():
        assert direction == 0
    for meta in frame.column("meta").to_pylist():
        assert json.loads(meta)["level_na"] is True


def test_structured_noise_and_insufficient_are_silent():
    det = _det()
    # Select silence cases by kind (the suite now has two planted-truth cases).
    for case in det.planted_cases():
        if case.kind == "planted_truth":
            continue
        assert det.detect(case.data).num_rows == 0


def test_gapped_feed_dow_fires_at_first_bar_not_midnight():
    """DEVQ-005 contract: post-weekend dow marker lands at the day's first bar.

    On a feed whose first bar of each day is 01:00 (no 00:00 bar), the dow
    markers must fire at 01:00 — and the post-weekend Monday marker at Mon 01:00,
    never a back-stamped Mon 00:00.
    """
    det = _det()
    gapped = next(c for c in det.planted_cases() if c.case_id == "gapped_feed_first_bar_0100")
    got = descriptors(det.detect(gapped.data))
    assert got == gapped.expected  # exact match, ratified contract

    hour = 3600 * 1_000_000_000
    dow = {d["event_type"]: d["ts"] for d in got if d["event_type"].startswith("seasonality.dow.")}
    # Every dow marker sits at 01:00 of its day (offset 1h from midnight), never 00:00.
    for ts in dow.values():
        assert (ts // hour) % 24 == 1
    # The post-weekend Monday marker exists and is at Mon 01:00 (the DEVQ-005 case).
    assert dow["seasonality.dow.mon"] == SF._MON_2024_01_08 + hour


def test_weekend_emits_no_dow_marker():
    # A full Saturday of hourly bars: weekend -> no dow markers; and if fully
    # outside the london window, no session events either.
    det = SeasonalityDetector(params={"sessions": {"london": [8 * 3600, 16 * 3600]},
                                       "emit_dow": True})
    sat = SF._SAT_2024_01_06
    hour = 3600 * 1_000_000_000
    data = pa.table({"ts": pa.array([sat + h * hour for h in range(8)], type=pa.int64())})
    assert det.detect(data).num_rows == 0


def test_incremental_consistency_property():
    """Feeding prefixes never changes previously emitted events (anti-hindsight)."""
    det = _det()
    data = det.planted_cases()[0].data
    ts_all = data.column("ts").to_pylist()
    full = descriptors(det.detect(data))
    for k in range(1, data.num_rows + 1):
        prefix = descriptors(det.detect(data.slice(0, k)))
        expected_prefix = [d for d in full if d["ts"] <= ts_all[k - 1]]
        assert prefix == expected_prefix


def test_params_roundtrip():
    det = SeasonalityDetector(params={"sessions": {"tokyo": [0, 3600]}, "emit_dow": False})
    assert det.params == {"sessions": {"tokyo": [0, 3600]}, "emit_dow": False}
    assert det.instrument_id == "seasonality.calendar"
    assert det.family == "seasonality"
    # emit_dow off -> no dow markers even across day boundaries.
    hour = 3600 * 1_000_000_000
    data = pa.table({"ts": pa.array([SF._MON_2024_01_01 + h * hour for h in range(48)],
                                    type=pa.int64())})
    types = det.detect(data).column("event_type").to_pylist()
    assert not any(t.startswith("seasonality.dow.") for t in types)

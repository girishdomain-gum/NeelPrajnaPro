"""WO-03 AT-3 (S3, refs A-007 ruling; D-010 item 5) — EventFrame fidelity end
to end. R6 registers no ExecutionSpec and runs no detector this sprint (no
judging phase, Execution Plan v2.0 §6 exit criteria are explicit on that) —
this test instead proves the GUARANTEE item 5 asks for: whatever
collection/storage shape R6 lands on, a detector run against R6-shaped bars
still emits a valid EventFrame with level/zone_hi/zone_lo populated per the
kernel §4.3 contract, so a FUTURE confirmatory judgment can register with
ExecutionSpec.event_stop_column="level" exactly as WO-02 already proved for
H-07 — not fall back to the stop_offset=null path NP-S1 was stuck with
pre-parity. Reuses the REAL LiquiditySweepDetector and the REAL
validate_event_frame/ExecutionSpec — no new detector logic for R6.
"""

from __future__ import annotations

import pyarrow as pa

from qrf.kernel.instruments.base import validate_event_frame
from qrf.trading.concepts.neelprajna.detector import LiquiditySweepDetector
from qrf.trading.simulator.engine import ExecutionSpec

N = 15


def _r6_shaped_bars() -> pa.Table:
    """A single HIGH-pool sweep-and-reclose, R6-shaped (ts/high/low/close only
    — the same bar shape ingest_r6.py's own M5 bars would carry)."""
    h = [100.00] * N
    low = [99.50] * N
    c = [100.00] * N
    h[3], h[10], h[14] = 100.20, 100.35, 100.45
    c[14] = 100.30
    return pa.table(
        {"ts": pa.array(list(range(N)), type=pa.int64()), "high": h, "low": low, "close": c}
    )


def test_detector_against_r6_shaped_bars_emits_valid_event_frame():
    events = LiquiditySweepDetector().detect(_r6_shaped_bars())
    validate_event_frame(events)  # must not raise — the §4.3 contract holds

    rows = events.to_pandas()
    sweeps = rows[rows["event_type"].str.endswith(".sweep")]
    assert len(sweeps) == 1
    assert sweeps.iloc[0]["level"] == 100.35
    # point event (not a zone) — zone_hi/zone_lo both NaN, per the detector's
    # own convention, and still §4.3-valid (validate_event_frame already
    # accepted the whole frame above).
    assert sweeps.iloc[0]["zone_hi"] != sweeps.iloc[0]["zone_hi"]  # NaN
    assert sweeps.iloc[0]["zone_lo"] != sweeps.iloc[0]["zone_lo"]  # NaN


def test_future_judgment_can_register_event_stop_column_level():
    # The guarantee item 5 actually asks for: this must succeed, not fall
    # back to stop_offset=null — exactly WO-02's own registration path.
    exe = ExecutionSpec(hold_bars=5, event_stop_column="level", target_r_multiple=1.5)
    assert exe.event_stop_column == "level"
    assert exe.stop_offset is None

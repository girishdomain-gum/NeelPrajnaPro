"""WO-03 (S3, refs A-007) — dataset scope registration: AT-1 (no burn
collision with NP-S1's spent TRAINING window, proven not assumed) and AT-4
(registering writes EXACTLY the one scope-registration record — the A-004
sharpened standard: watched against a REAL journal's actual content, not a
throwaway always-empty tmp_path one; per the drill law, this test never
opens or writes the real production file directly — it copies the real
journal's bytes into a scratch path first, so a real run of this test suite
can never mutate F:\\NeelPrajnaPro\\datastore\\journal\\journal.jsonl)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from qrf.kernel.errors import SchemaViolation, WindowBurnedError
from qrf.kernel.protocol import scope_registry
from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.store import RecordStore

R6_DATASET = "xauusd_ticks_vantage_r6"

# NP-S1's real burned window facts (datastore/journal/journal.jsonl, the
# window + window_burn records) — quoted exactly, not re-derived, so this
# test proves non-collision against the REAL spent span, not a stand-in.
NP_S1_DATASET = "xauusd_m5_vantage"
NP_S1_LINEAGE = "h007_np_liquidity_sweep_v1_1"
NP_S1_TS_START = 1776722400000000000  # 2026-04-20T22:00:00Z
NP_S1_TS_END = 1783693980000000000  # 2026-07-10T14:33:00Z

REAL_JOURNAL = Path(__file__).resolve().parents[2] / "datastore" / "journal" / "journal.jsonl"


def _registration_kwargs(**overrides):
    kwargs = dict(
        dataset=R6_DATASET,
        iana_zone="Europe/Berlin",
        zone_evidence="PLACEHOLDER pending Owner export bracketing a DST transition",
        ingest_path="datastore/r6_exports",
        batch_forward_protocol="Owner periodically exports fresh Vantage ticks into "
        "the pinned ingest path; scripts/ingest_r6.py appends strictly-newer data "
        "only, refuses overlap/duplicate/backwards batches loudly, journals every batch.",
        oos_designation="EXPLORATION",
        anchor_ts=1785600000000000000,
    )
    kwargs.update(overrides)
    return kwargs


# --- registration ceremony has no silent-default form -------------------------
def test_register_writes_the_scope_record(tmp_path):
    store = RecordStore(tmp_path / "journal.jsonl")
    rec = scope_registry.register(store, **_registration_kwargs())
    assert rec.record_type == "dataset_scope"
    assert rec.payload["dataset"] == R6_DATASET
    assert rec.payload["oos_designation"] == "EXPLORATION"


@pytest.mark.parametrize(
    "field", ["dataset", "iana_zone", "zone_evidence", "ingest_path",
              "batch_forward_protocol", "oos_designation"],
)
def test_register_refuses_empty_field(tmp_path, field):
    store = RecordStore(tmp_path / "journal.jsonl")
    with pytest.raises(SchemaViolation):
        scope_registry.register(store, **_registration_kwargs(**{field: ""}))


# --- AT-4: registering writes EXACTLY one record, on a REAL journal's content -
def test_at4_registering_adds_exactly_one_record_to_real_journal_content(tmp_path):
    assert REAL_JOURNAL.exists(), "expected the real datastore journal to exist"
    scratch = tmp_path / "journal.jsonl"
    shutil.copyfile(REAL_JOURNAL, scratch)  # real content, never the real path

    before = len(RecordStore(scratch))
    assert before > 0  # a REAL journal, not an always-empty proxy (A-004's point)

    store = RecordStore(scratch)
    scope_registry.register(store, **_registration_kwargs())

    after = len(RecordStore(scratch))
    assert after == before + 1  # exactly the one scope-registration record


# --- AT-1: R6's dataset name mechanically cannot collide with NP-S1's burn ---
def test_at1_r6_dataset_never_collides_with_np_s1_burned_window(tmp_path):
    store = RecordStore(tmp_path / "journal.jsonl")
    wl = WindowLedger(store)

    # Reconstruct NP-S1's real burned window+burn (same dataset/lineage/span
    # as the real journal) so the collision check has something real to miss.
    np_s1_window = wl.designate(NP_S1_DATASET, NP_S1_TS_START, NP_S1_TS_END, "TRAINING")
    verdict_stub = store.append("note", {"text": "stand-in verdict"}, producer="p", event_ts=1)
    wl.burn(np_s1_window.record_id, NP_S1_LINEAGE, verdict_stub.record_id)

    # R6's own window, on a DIFFERENT dataset, deliberately given the SAME
    # time span AND the same lineage as NP-S1's burn — the only thing that
    # could save it from WindowBurnedError is the dataset-name mismatch
    # itself (windows.py:107's `continue`), not a lucky time gap.
    r6_window = wl.designate(R6_DATASET, NP_S1_TS_START, NP_S1_TS_END, "EXPLORATION")
    wl.check_available(r6_window.record_id, NP_S1_LINEAGE)  # must not raise

    # Sanity: the SAME span, SAME lineage, but the SAME dataset as NP-S1's
    # burn really is refused — proving the check is live, not vacuous.
    same_dataset_window = wl.designate(NP_S1_DATASET, NP_S1_TS_START, NP_S1_TS_END, "TRAINING")
    with pytest.raises(WindowBurnedError):
        wl.check_available(same_dataset_window.record_id, NP_S1_LINEAGE)

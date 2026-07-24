"""REV-S1 OBS-1: resolved views are loudly marked and can never be persisted.

A resolved view's content_hash is recomputed over the corrected payload (so it
differs from any stored record), and it carries meta={"resolved": true,
"amendments": [...]}. append() refuses any record whose meta contains that
marker, so a resolved view cannot be re-appended or chained.
"""

from __future__ import annotations

import pytest

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records.store import RecordStore


@pytest.fixture
def store(tmp_path):
    return RecordStore(tmp_path / "journal.jsonl")


def _amend(store, base, correction, ts):
    return store.append(
        "amendment",
        {"target_ref": base.record_id, "correction": correction},
        producer="human:fix",
        event_ts=ts,
        parents=[base.record_id],
    )


def test_resolved_view_is_marked(store):
    base = store.append("note", {"text": "orig"}, producer="p", event_ts=1)
    a1 = _amend(store, base, {"text": "fixed"}, 2)
    resolved = store.resolve(base.record_id)

    assert resolved.payload["text"] == "fixed"
    assert resolved.meta["resolved"] is True
    assert resolved.meta["amendments"] == [a1.record_id]
    # The view's content_hash differs from the stored base (recomputed over the
    # corrected payload) — it is NOT the journal record.
    assert resolved.content_hash != base.content_hash


def test_unamended_resolve_is_the_real_record_unmarked(store):
    base = store.append("note", {"text": "orig"}, producer="p", event_ts=1)
    resolved = store.resolve(base.record_id)
    assert resolved.record_id == base.record_id
    assert "resolved" not in resolved.meta  # genuine record, no marker


def test_append_refuses_resolved_meta_directly(store):
    with pytest.raises(SchemaViolation):
        store.append(
            "note", {"text": "x"}, producer="p", event_ts=1, meta={"resolved": True}
        )


def test_cannot_persist_a_resolved_view(store):
    base = store.append("note", {"text": "orig"}, producer="p", event_ts=1)
    _amend(store, base, {"text": "fixed"}, 2)
    resolved = store.resolve(base.record_id)
    n_before = len(store)
    # Attempting to chain/re-append the resolved view is refused by its marker.
    with pytest.raises(SchemaViolation):
        store.append(
            resolved.record_type,
            resolved.payload,
            producer=resolved.producer,
            event_ts=resolved.event_ts,
            meta=resolved.meta,
        )
    assert len(store) == n_before  # nothing written

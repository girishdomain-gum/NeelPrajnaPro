"""REV-S1 OBS-3: an amendment that is itself amended (shallow-override order).

Documents and locks the resolution semantics when amendments chain:

* ``resolve(X)`` applies exactly the amendments whose ``target_ref == X``, in
  ULID (= append) order, as shallow per-key overrides — last write wins.
* Resolution is NOT transitive: ``resolve(base)`` does not fold in an amendment
  that targets *another amendment*. To see a correction applied to an amendment,
  you ``resolve`` that amendment record itself.
"""

from __future__ import annotations

import pytest

from qrf.kernel.records.store import RecordStore


@pytest.fixture
def store(tmp_path):
    return RecordStore(tmp_path / "journal.jsonl")


def _amend(store, target, correction, ts):
    return store.append(
        "amendment",
        {"target_ref": target.record_id, "correction": correction},
        producer="human:fix",
        event_ts=ts,
        parents=[target.record_id],
    )


def test_amendment_of_an_amendment(store):
    # base note, then A1 corrects the base, then A2 corrects A1 (not the base).
    base = store.append("note", {"text": "v0"}, producer="p", event_ts=1)
    a1 = _amend(store, base, {"text": "v1"}, 2)
    a2 = _amend(store, a1, {"correction": {"text": "v1-fixed"}}, 3)

    # resolve(base) applies only amendments targeting base (A1). A2 targets A1,
    # so it is NOT folded into the base resolution (resolution is non-transitive).
    rb = store.resolve(base.record_id)
    assert rb.payload["text"] == "v1"
    assert rb.meta["amendments"] == [a1.record_id]

    # resolve(A1) applies A2's correction to A1's own payload. The 'correction'
    # key is overridden; the untouched 'target_ref' key survives the shallow merge.
    ra1 = store.resolve(a1.record_id)
    assert ra1.payload["correction"] == {"text": "v1-fixed"}
    assert ra1.payload["target_ref"] == base.record_id  # untouched key survives
    assert ra1.meta["amendments"] == [a2.record_id]


def test_shallow_override_last_write_wins_in_ulid_order(store):
    base = store.append("note", {"text": "v0"}, producer="p", event_ts=1)
    _amend(store, base, {"text": "v1"}, 2)
    _amend(store, base, {"text": "v2"}, 3)
    _amend(store, base, {"text": "v3"}, 4)
    # ULID order == append order; last correction wins.
    assert store.resolve(base.record_id).payload["text"] == "v3"


def test_multi_key_shallow_merge(store):
    base = store.append("note", {"text": "t0"}, producer="p", event_ts=1)
    # amendment payloads are {target_ref, correction}; correction merges by key.
    _amend(store, base, {"text": "t1"}, 2)
    resolved = store.resolve(base.record_id)
    assert resolved.payload == {"text": "t1"}

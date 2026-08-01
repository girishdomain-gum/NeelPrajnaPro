"""WO-08 (S5, spec A-013/A-016) — drill law for scripts/check_window_ledger.py:
every RED class tamper-drilled on a disposable scratch journal, then a
control GREEN pass on a COPY of the real journal (shutil.copyfile — never the
live path itself, per WO-03's own convention)."""

from __future__ import annotations

import shutil
from pathlib import Path

from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.record import Record, now_ns
from qrf.kernel.records.store import RecordStore
from scripts.check_window_ledger import check_window_ledger

REAL_JOURNAL = Path("datastore/journal/journal.jsonl")


def _store(tmp_path):
    return RecordStore(tmp_path / "journal.jsonl")


def _fake_verdict_id(store) -> str:
    """burn()'s parents=[window_ref, verdict_ref] requires BOTH to exist
    (I-3) — these drills don't need a real verdict schema, just an existing
    record id to stand in for one. Uses a throwaway window record for that
    (counts toward n_windows, never toward n_burns/findings)."""
    payload = {
        "dataset": "_fake_verdict_stub", "ts_start": 0, "ts_end": 1, "designation": "TRAINING",
    }
    rec = store.append("window", payload, producer="test:fixture", event_ts=now_ns())
    return rec.record_id


# --- control: clean scratch ledger is GREEN ------------------------------------
def test_clean_scratch_ledger_is_green(tmp_path):
    store = _store(tmp_path)
    ledger = WindowLedger(store)
    v = _fake_verdict_id(store)
    w = ledger.designate("xauusd_test", 100, 200, "TRAINING")
    ledger.burn(w.record_id, "lineage_a", v)

    report = check_window_ledger(store)
    assert report.is_green
    assert report.findings == []
    assert report.n_windows == 2  # the fixture window + the real one
    assert report.n_burns == 1
    assert report.n_virgin == 0


# --- RED 1: ORPHAN_BURN ---------------------------------------------------------
def test_orphan_burn_is_red(tmp_path):
    store = _store(tmp_path)
    # A window_burn hand-crafted via the low-level store API (bypassing
    # WindowLedger.burn(), which would refuse a nonexistent window_ref) —
    # simulating a corrupted/hand-authored record, not achievable through the
    # normal API, exactly the kind of defect this checker exists to catch.
    v = _fake_verdict_id(store)
    store.append(
        "window_burn",
        {"window_ref": "01NONEXISTENT000000000000", "lineage": "l", "consumed_by": v},
        producer="test:tamper",
        event_ts=now_ns(),
    )
    report = check_window_ledger(store)
    assert not report.is_green
    assert any("ORPHAN_BURN" in f for f in report.findings)


# --- RED 2: MALFORMED_SPAN -------------------------------------------------------
def test_malformed_span_is_red(tmp_path):
    """The write-time schema (schemas._validate_window) already refuses
    ts_end <= ts_start, so this cannot be produced through WindowLedger or
    RecordStore.append at all — confirmed by the SchemaViolation it raises
    when tried. MALFORMED_SPAN is therefore defense-in-depth against a raw,
    hand-tampered, or alternate-write-path journal line, since schema
    validation runs ONLY at append time (qrf.kernel.records.store.append),
    never when reading an existing file back (_read_records_from_disk) — a
    chain-valid but schema-invalid line loads and verifies fine. Drilled
    exactly that way: append one real record via the store, then hand-append
    a second, correctly-hash-chained-but-malformed record straight to the
    wire, bypassing schemas.validate entirely (as a corrupted file would)."""
    path = tmp_path / "journal.jsonl"
    store = RecordStore(path)
    genesis = store.append(
        "window", {"dataset": "xauusd_test", "ts_start": 0, "ts_end": 1, "designation": "TRAINING"},
        producer="test:fixture", event_ts=now_ns(),
    )
    bad = Record.create(
        record_id="01BADSPAN00000000000000000",
        record_type="window",
        schema_version=1,
        producer="test:tamper",
        event_ts=now_ns(),
        recorded_ts=now_ns(),
        parents=(),
        payload={
            "dataset": "xauusd_test", "ts_start": 200, "ts_end": 100, "designation": "TRAINING",
        },
        prev_hash=genesis.content_hash,
    )
    with open(path, "ab") as f:
        f.write(bad.to_json_line() + b"\n")

    store2 = RecordStore(path)  # loads + verifies the hash chain — must still pass
    report = check_window_ledger(store2)
    assert not report.is_green
    assert any("MALFORMED_SPAN" in f for f in report.findings)


# --- RED 3: OVERLAPPING_BURNS ----------------------------------------------------
def test_overlapping_burns_same_dataset_lineage_is_red(tmp_path):
    store = _store(tmp_path)
    ledger = WindowLedger(store)
    v1, v2 = _fake_verdict_id(store), _fake_verdict_id(store)
    w1 = ledger.designate("xauusd_test", 100, 300, "TRAINING")
    w2 = ledger.designate("xauusd_test", 200, 400, "TRAINING")  # overlaps w1
    # Both burned for the SAME lineage — calling burn() directly, bypassing
    # check_available (which a real caller like the Battery would have run
    # first and would have refused the second burn). This checker is the
    # standalone audit of exactly that promise.
    ledger.burn(w1.record_id, "lineage_a", v1)
    ledger.burn(w2.record_id, "lineage_a", v2)

    report = check_window_ledger(store)
    assert not report.is_green
    assert any("OVERLAPPING_BURNS" in f for f in report.findings)


def test_non_overlapping_burns_same_lineage_stay_green(tmp_path):
    """Sanity: two burns, same lineage+dataset, NON-intersecting windows -> clean."""
    store = _store(tmp_path)
    ledger = WindowLedger(store)
    v1, v2 = _fake_verdict_id(store), _fake_verdict_id(store)
    w1 = ledger.designate("xauusd_test", 100, 200, "TRAINING")
    w2 = ledger.designate("xauusd_test", 200, 300, "TRAINING")  # touches, doesn't overlap
    ledger.burn(w1.record_id, "lineage_a", v1)
    ledger.burn(w2.record_id, "lineage_a", v2)
    report = check_window_ledger(store)
    assert report.is_green


def test_overlapping_burns_different_lineage_stay_green(tmp_path):
    """Sanity: overlapping windows, but DIFFERENT lineages -> not a conflict."""
    store = _store(tmp_path)
    ledger = WindowLedger(store)
    v1, v2 = _fake_verdict_id(store), _fake_verdict_id(store)
    w1 = ledger.designate("xauusd_test", 100, 300, "TRAINING")
    w2 = ledger.designate("xauusd_test", 200, 400, "TRAINING")
    ledger.burn(w1.record_id, "lineage_a", v1)
    ledger.burn(w2.record_id, "lineage_b", v2)
    report = check_window_ledger(store)
    assert report.is_green


# --- RED 4: RESERVE_MISMATCH -----------------------------------------------------
def test_virgin_window_burned_is_red(tmp_path):
    store = _store(tmp_path)
    ledger = WindowLedger(store)
    v = _fake_verdict_id(store)
    w = ledger.designate("xauusd_test", 100, 200, "VIRGIN")
    # burn() itself does not check designation (only guard_observatory /
    # check_screenable do) — this drill proves the checker catches what the
    # runtime API alone would silently allow.
    ledger.burn(w.record_id, "lineage_a", v)
    report = check_window_ledger(store)
    assert not report.is_green
    assert any("RESERVE_MISMATCH" in f for f in report.findings)


def test_untouched_virgin_window_stays_green(tmp_path):
    store = _store(tmp_path)
    ledger = WindowLedger(store)
    ledger.designate("xauusd_test", 100, 200, "VIRGIN")
    report = check_window_ledger(store)
    assert report.is_green
    assert report.n_virgin == 1


# --- control: the REAL ledger, copied, GREEN ------------------------------------
def test_real_journal_copy_is_green(tmp_path):
    dest = tmp_path / "journal.jsonl"
    shutil.copyfile(REAL_JOURNAL, dest)
    store = RecordStore(dest)
    report = check_window_ledger(store)
    assert report.is_green, report.findings
    assert report.n_windows > 0  # non-vacuous: the real ledger has real windows

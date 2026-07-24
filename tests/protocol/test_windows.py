"""WindowLedger tests (Blueprint §4.6): overlap matrix, lineage isolation,
observatory guard, designation validation, burn round-trip."""

from __future__ import annotations

import pytest

from qrf.kernel.errors import ContaminationError, SchemaViolation, WindowBurnedError
from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.store import RecordStore

DS = "ds"


@pytest.fixture
def wl(tmp_path):
    return WindowLedger(RecordStore(tmp_path / "journal.jsonl"))


def _verdict(wl):
    """A stand-in verdict record to parent a burn (battery does not exist yet)."""
    return wl._store.append("note", {"text": "stand-in verdict"}, producer="p", event_ts=1)


def _burn_range(wl, start, end, lineage, *, dataset=DS):
    w = wl.designate(dataset, start, end, "TRAINING")
    wl.burn(w.record_id, lineage, _verdict(wl).record_id)
    return w


# --- designation validation --------------------------------------------------
def test_designate_validates_designation_and_interval(wl):
    w = wl.designate(DS, 0, 100, "EXPLORATION")
    assert w.payload["designation"] == "EXPLORATION"
    with pytest.raises(SchemaViolation):
        wl.designate(DS, 0, 100, "HOLDOUT")
    with pytest.raises(SchemaViolation):  # ts_end <= ts_start
        wl.designate(DS, 100, 100, "TRAINING")


# --- overlap matrix (half-open intervals) ------------------------------------
def test_disjoint_available(wl):
    _burn_range(wl, 0, 100, "fam")
    later = wl.designate(DS, 200, 300, "TRAINING")
    wl.check_available(later.record_id, "fam")  # no raise


def test_touching_is_available(wl):
    # [0,100) burned; [100,200) merely touches at the endpoint -> available.
    _burn_range(wl, 0, 100, "fam")
    touch = wl.designate(DS, 100, 200, "TRAINING")
    wl.check_available(touch.record_id, "fam")


def test_overlapping_refused(wl):
    _burn_range(wl, 0, 100, "fam")
    overlap = wl.designate(DS, 50, 150, "TRAINING")
    with pytest.raises(WindowBurnedError):
        wl.check_available(overlap.record_id, "fam")


def test_contained_refused(wl):
    _burn_range(wl, 0, 100, "fam")
    inner = wl.designate(DS, 40, 60, "TRAINING")
    with pytest.raises(WindowBurnedError):
        wl.check_available(inner.record_id, "fam")


def test_containing_refused(wl):
    _burn_range(wl, 40, 60, "fam")
    outer = wl.designate(DS, 0, 100, "TRAINING")
    with pytest.raises(WindowBurnedError) as ei:
        wl.check_available(outer.record_id, "fam")
    assert "out-of-sample reuse refused" in str(ei.value)


# --- lineage + dataset isolation ---------------------------------------------
def test_lineage_isolation(wl):
    _burn_range(wl, 0, 100, "famA")
    same = wl.designate(DS, 0, 100, "TRAINING")
    with pytest.raises(WindowBurnedError):
        wl.check_available(same.record_id, "famA")
    wl.check_available(same.record_id, "famB")  # a different lineage is unaffected


def test_dataset_isolation(wl):
    _burn_range(wl, 0, 100, "fam", dataset="ds1")
    other = wl.designate("ds2", 0, 100, "TRAINING")
    wl.check_available(other.record_id, "fam")  # same interval, other dataset -> ok


# --- observatory guard -------------------------------------------------------
def test_guard_refuses_virgin_allows_others(wl):
    virgin = wl.designate(DS, 0, 100, "VIRGIN")
    with pytest.raises(ContaminationError):
        wl.guard_observatory(virgin.record_id)
    for des in ("TRAINING", "EXPLORATION"):
        w = wl.designate(DS, 0, 100, des)
        wl.guard_observatory(w.record_id)  # no raise


# --- burn round-trip ---------------------------------------------------------
def test_burn_roundtrip_and_parents(wl):
    w = wl.designate(DS, 0, 100, "TRAINING")
    v = _verdict(wl)
    b = wl.burn(w.record_id, "fam", v.record_id)
    assert b.record_type == "window_burn"
    assert b.payload == {"window_ref": w.record_id, "lineage": "fam", "consumed_by": v.record_id}
    assert w.record_id in b.parents and v.record_id in b.parents
    with pytest.raises(WindowBurnedError):
        wl.check_available(w.record_id, "fam")
    assert wl._store.verify().ok


def test_non_window_ref_rejected(wl):
    note = wl._store.append("note", {"text": "x"}, producer="p", event_ts=1)
    with pytest.raises(SchemaViolation):
        wl.check_available(note.record_id, "fam")
    with pytest.raises(SchemaViolation):
        wl.guard_observatory(note.record_id)

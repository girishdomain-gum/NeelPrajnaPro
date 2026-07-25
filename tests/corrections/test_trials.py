"""TrialCountLedger tests (Blueprint §4.8): monotone accumulation, exact-n
bumps, source validation, generator inheritance, scope/lineage isolation."""

from __future__ import annotations

import pytest

from qrf.kernel.corrections.trials import TrialCountLedger
from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records.store import RecordStore

SCOPE = "win-ref"
LINEAGE = "fam.smc"


@pytest.fixture
def tl(tmp_path):
    return TrialCountLedger(RecordStore(tmp_path / "journal.jsonl"))


# --- basic append + total ----------------------------------------------------
def test_bump_appends_trial_count_record(tl):
    rec = tl.bump(SCOPE, LINEAGE, 7, "screener")
    assert rec.record_type == "trial_count"
    assert rec.payload == {
        "data_scope": SCOPE,
        "lineage": LINEAGE,
        "n_attempts": 7,
        "source": "screener",
    }
    assert tl.total(SCOPE, LINEAGE) == 7


# --- monotone accumulation ---------------------------------------------------
def test_total_accumulates_monotonically(tl):
    running = 0
    for n in (3, 500, 1, 42):
        tl.bump(SCOPE, LINEAGE, n, "screener")
        running += n
        assert tl.total(SCOPE, LINEAGE) == running
    # No decrement surface exists: appends only ever raise the total.
    assert tl.total(SCOPE, LINEAGE) == 546


# --- exact-n rule (no netting) -----------------------------------------------
def test_n_must_be_at_least_one(tl):
    with pytest.raises(SchemaViolation):
        tl.bump(SCOPE, LINEAGE, 0, "screener")
    with pytest.raises(SchemaViolation):
        tl.bump(SCOPE, LINEAGE, -5, "screener")


def test_n_must_be_int_not_bool(tl):
    with pytest.raises(SchemaViolation):
        tl.bump(SCOPE, LINEAGE, True, "screener")  # bool is not an int here


# --- source validation -------------------------------------------------------
def test_source_enum_enforced(tl):
    for src in ("human", "screener", "generator"):
        tl.bump(SCOPE, LINEAGE, 1, src, generator_ref="g" if src == "generator" else None)
    with pytest.raises(SchemaViolation):
        tl.bump(SCOPE, LINEAGE, 1, "robot")


# --- generator inheritance ---------------------------------------------------
def test_generator_ref_recorded_when_present(tl):
    rec = tl.bump(SCOPE, LINEAGE, 12, "generator", generator_ref="gen-01")
    assert rec.payload["generator_ref"] == "gen-01"
    # Absent generator_ref is simply omitted (optional field).
    rec2 = tl.bump(SCOPE, LINEAGE, 1, "human")
    assert "generator_ref" not in rec2.payload


# --- scope / lineage isolation ----------------------------------------------
def test_totals_are_isolated_by_scope_and_lineage(tl):
    tl.bump("A", "lin1", 10, "screener")
    tl.bump("A", "lin2", 5, "screener")
    tl.bump("B", "lin1", 3, "screener")
    assert tl.total("A", "lin1") == 10
    assert tl.total("A", "lin2") == 5
    assert tl.total("B", "lin1") == 3
    assert tl.total("A", "nope") == 0
    assert tl.total("nope", "lin1") == 0


# --- family key (DEVQ-015) ---------------------------------------------------
def test_family_written_as_v2_record(tl):
    rec = tl.bump(SCOPE, LINEAGE, 5, "screener", family="xauusd_h1/smc.fvg")
    assert rec.schema_version == 2
    assert rec.payload["family"] == "xauusd_h1/smc.fvg"
    # Without a family the record stays v1 (append-only back-compat).
    rec2 = tl.bump(SCOPE, LINEAGE, 1, "screener")
    assert rec2.schema_version == 1
    assert "family" not in rec2.payload


def test_empty_family_refused(tl):
    with pytest.raises(SchemaViolation):
        tl.bump(SCOPE, LINEAGE, 5, "screener", family="   ")


# --- observatory source / trial_count v3 (DEVQ-016) --------------------------
def test_observatory_source_written_as_v3(tl):
    rec = tl.bump(SCOPE, LINEAGE, 1, "observatory", family="xauusd_h1/smc.fvg")
    assert rec.schema_version == 3
    assert rec.payload["source"] == "observatory"
    assert rec.payload["family"] == "xauusd_h1/smc.fvg"


def test_observatory_source_requires_family(tl):
    with pytest.raises(SchemaViolation):
        tl.bump(SCOPE, LINEAGE, 1, "observatory")  # v3 requires a family


def test_observatory_source_rejected_by_v1_and_v2(tmp_path):
    from qrf.kernel.records import schemas

    base = {"data_scope": "s", "lineage": "l", "n_attempts": 1, "source": "observatory"}
    # v1/v2 are forward-only: they never accept the observatory source (NOTE-013).
    with pytest.raises(SchemaViolation):
        schemas.validate("trial_count", base, 1)
    with pytest.raises(SchemaViolation):
        schemas.validate("trial_count", base | {"family": "f"}, 2)
    # v3 accepts it.
    schemas.validate("trial_count", base | {"family": "f"}, 3)


# --- parents flow through ----------------------------------------------------
def test_parents_are_recorded(tl):
    w = tl._store.append("window", {
        "dataset": "d", "ts_start": 0, "ts_end": 10, "designation": "TRAINING",
    }, producer="p", event_ts=1)
    rec = tl.bump(SCOPE, LINEAGE, 1, "screener", parents=[w.record_id])
    assert rec.parents == (w.record_id,)

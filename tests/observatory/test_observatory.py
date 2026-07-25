"""Observatory — scan discipline, questions, and the no-VIRGIN guard (ARCH-007 §1-2).

Guarantees pinned here:
* a scan on a VIRGIN window is refused (ContaminationError) before any record;
* every scan bumps the trial ledger for its family (looking is a burden, DEVQ-015);
* a question is parented to its scan and carries no thresholds/verdict/burn;
* the findings summary is whatever the caller computed (kernel stays domain-blind).
"""

from __future__ import annotations

import pytest

from qrf.kernel.corrections.deflation import family_trials
from qrf.kernel.errors import ContaminationError, SchemaViolation
from qrf.kernel.observatory import Observatory
from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.store import RecordStore

FAMILY = "xauusd_h1/smc.fvg"


def _store(tmp_path) -> RecordStore:
    return RecordStore(tmp_path / "journal.jsonl")


def _manifest(store: RecordStore, dataset: str = "ds") -> str:
    return store.append(
        "bulk_manifest",
        {
            "path": f"{dataset}/part-00000.parquet",
            "dataset": dataset,
            "row_count": 10,
            "byte_size": 100,
            "file_sha256": "0" * 64,
            "columns": [{"name": "ts", "dtype": "int64"}],
            "ts_min": 1,
            "ts_max": 100,
        },
        producer="test",
        event_ts=100,
    ).record_id


def _window(store: RecordStore, designation: str) -> str:
    return WindowLedger(store).designate("ds", 1, 100, designation, producer="test").record_id


def test_scan_on_virgin_refused_before_any_write(tmp_path):
    store = _store(tmp_path)
    man = _manifest(store)
    virgin = _window(store, "VIRGIN")
    obs = Observatory(store)
    n_before = len(store)
    with pytest.raises(ContaminationError):
        obs.scan(
            family=FAMILY, window_ref=virgin, manifest_refs=[man],
            method="m", seed=1, findings={"x": 1},
        )
    # Guard fires first: no anomaly_scan, no trial bump written.
    assert len(store) == n_before
    assert not list(store.query(record_type="anomaly_scan"))
    assert not list(store.query(record_type="trial_count"))


def test_scan_bumps_family_trials(tmp_path):
    store = _store(tmp_path)
    man = _manifest(store)
    win = _window(store, "TRAINING")
    obs = Observatory(store)
    assert family_trials(FAMILY, store) == 0
    scan = obs.scan(
        family=FAMILY, window_ref=win, manifest_refs=[man],
        method="fvg.weekend@h4", seed=7, findings={"n_events": 3}, n_searched=2,
    )
    assert scan.record_type == "anomaly_scan"
    assert scan.parents == (win, man)
    assert scan.payload["findings"] == {"n_events": 3}
    # The scan bumped the family's trial ledger by n_searched (looking is a burden).
    assert family_trials(FAMILY, store) == 2
    tc = next(store.query(record_type="trial_count"))
    assert tc.payload["family"] == FAMILY
    assert scan.record_id in tc.parents


def test_training_and_exploration_are_scannable(tmp_path):
    store = _store(tmp_path)
    man = _manifest(store)
    obs = Observatory(store)
    for desig in ("TRAINING", "EXPLORATION"):
        win = _window(store, desig)
        scan = obs.scan(
            family=FAMILY, window_ref=win, manifest_refs=[man],
            method=f"m.{desig}", seed=1, findings={},
        )
        assert scan.payload["window_ref"] == win


def test_question_parented_to_scan_no_judgement(tmp_path):
    store = _store(tmp_path)
    man = _manifest(store)
    win = _window(store, "TRAINING")
    obs = Observatory(store)
    scan = obs.scan(
        family=FAMILY, window_ref=win, manifest_refs=[man], method="m", seed=1, findings={}
    )
    q = obs.pose_question(
        scan_ref=scan.record_id,
        observation="weekend FVGs look different",
        data_slice_refs=[man],
        candidate_hypothesis="restrict to intra-week",
        evidence_refs=["01VERDICT"],
    )
    assert q.record_type == "question"
    assert q.parents == (scan.record_id,)
    assert q.payload["origin"] == "observatory"
    # A question structurally cannot carry a threshold/verdict/burn.
    assert "thresholds" not in q.payload and "verdict" not in q.payload


def test_pose_question_refuses_non_scan_parent(tmp_path):
    store = _store(tmp_path)
    man = _manifest(store)
    obs = Observatory(store)
    with pytest.raises(SchemaViolation):
        obs.pose_question(
            scan_ref=man, observation="x", data_slice_refs=[man],
            candidate_hypothesis="y", evidence_refs=["z"],
        )


def test_scan_refuses_non_manifest_ref(tmp_path):
    store = _store(tmp_path)
    win = _window(store, "TRAINING")
    obs = Observatory(store)
    with pytest.raises(SchemaViolation):
        obs.scan(
            family=FAMILY, window_ref=win, manifest_refs=[win], method="m", seed=1, findings={}
        )


def test_same_seed_same_findings_are_recordable_twice_identically(tmp_path):
    # Determinism is the caller's (findings are a pure function of seed); the
    # observatory records byte-identical findings when handed identical input.
    store = _store(tmp_path)
    man = _manifest(store)
    win = _window(store, "TRAINING")
    obs = Observatory(store)
    findings = {"partition": {"mean": 1.5, "ci_low": 1.0, "ci_high": 2.0}}
    s1 = obs.scan(
        family=FAMILY, window_ref=win, manifest_refs=[man], method="m", seed=42, findings=findings
    )
    s2 = obs.scan(
        family=FAMILY, window_ref=win, manifest_refs=[man], method="m2", seed=42, findings=findings
    )
    assert s1.payload["findings"] == s2.payload["findings"]

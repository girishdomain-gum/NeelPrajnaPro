"""S07: runtime/types.py drills -- the consuming side of the Publication
Boundary independently re-verifies the sealed hash (A-029 §2.2).
"""

import pytest

from qrf.kernel.battery.battery import Verdict
from qrf.kernel.publication.release import publish
from runtime.errors import MalformedRelease
from runtime.types import ReleasedKnowledge
from tests.drills.harness import DrillLog, run_drill

SYNTHETIC_VERDICT = Verdict(
    hypothesis_id="SYNTHETIC-DEMO-H001",
    p_value=0.01,
    alpha=0.025,
    significant=True,
    n_resamples=5000,
    seed=1,
    null_name="block_resampling_v1",
    null_parameters={"block_length": 20},
    observed_statistic=0.0012,
    source_sha256="0" * 64,
)


def _clean_release():
    return publish(
        SYNTHETIC_VERDICT, measurement_id="LS-01-R001", direction="long",
        valid_from=1000, valid_until=2000,
    )


def test_valid_release_constructs():
    rk = ReleasedKnowledge.from_release_dict(_clean_release())
    assert rk.hypothesis_id == "SYNTHETIC-DEMO-H001"
    assert rk.significant is True


def test_tampered_sealed_hash_drill():
    """Control: the real, untouched release constructs cleanly. Tampered:
    a single field changed AFTER publish() sealed it -- the recomputed
    hash must disagree and the whole record is refused, not just the
    changed field.
    """
    log = DrillLog()
    clean = _clean_release()

    def checker(tamper: bool):
        release = dict(clean)
        if tamper:
            release["significant"] = not release["significant"]
        ReleasedKnowledge.from_release_dict(release)

    result = run_drill(
        name="released-knowledge-sealed-hash",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=MalformedRelease,
        log=log,
    )
    assert result.tampered_exception is MalformedRelease


def test_missing_field_refused():
    release = _clean_release()
    del release["direction"]
    with pytest.raises(MalformedRelease):
        ReleasedKnowledge.from_release_dict(release)


def test_extra_field_refused():
    release = _clean_release()
    release["p_value"] = 0.01
    with pytest.raises(MalformedRelease):
        ReleasedKnowledge.from_release_dict(release)


def test_not_a_dict_refused():
    with pytest.raises(MalformedRelease):
        ReleasedKnowledge.from_release_dict("not a dict")

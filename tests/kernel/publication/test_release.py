"""S07 W3/W4 drills: the Publication Boundary (A-029 §2.2/§2.3)."""

import pytest

from qrf.errors import PublicationLeak
from qrf.kernel.battery.battery import Verdict
from qrf.kernel.publication.release import publish, recompute_sealed_hash, verify_no_leak
from tests.drills.harness import DrillLog, run_drill

SYNTHETIC_VERDICT = Verdict(
    hypothesis_id="SYNTHETIC-DEMO-H001",
    p_value=0.01,
    alpha=0.025,
    significant=True,
    n_resamples=5000,
    seed=1,
    block_length=20,
    observed_statistic=0.0012,
    source_sha256="0" * 64,
)


def test_publish_only_carries_allowed_fields():
    release = publish(
        SYNTHETIC_VERDICT,
        measurement_id="LS-01-R001",
        direction="long",
        valid_from=1000,
        valid_until=2000,
    )
    assert set(release) == {
        "schema_version",
        "release_id",
        "hypothesis_id",
        "measurement_id",
        "significant",
        "direction",
        "valid_from",
        "valid_until",
        "sealed_hash",
    }
    # the derivation side never appears, even by field name
    for forbidden in ("p_value", "alpha", "n_resamples", "seed", "block_length",
                       "observed_statistic", "source_sha256"):
        assert forbidden not in release


def test_publish_rejects_non_verdict():
    with pytest.raises(TypeError):
        publish(
            {"hypothesis_id": "H1", "significant": True},  # a raw dict, not a Verdict
            measurement_id="LS-01-R001",
            direction="long",
            valid_from=1000,
            valid_until=2000,
        )


def test_byte_reproducibility():
    """A-029 §2.2: same inputs, same bytes, forever."""
    r1 = publish(SYNTHETIC_VERDICT, measurement_id="LS-01-R001", direction="long",
                 valid_from=1000, valid_until=2000)
    r2 = publish(SYNTHETIC_VERDICT, measurement_id="LS-01-R001", direction="long",
                 valid_from=1000, valid_until=2000)
    assert r1 == r2
    assert r1["release_id"] == r2["release_id"] == r1["sealed_hash"]


def test_sealed_hash_independently_recomputable():
    release = publish(SYNTHETIC_VERDICT, measurement_id="LS-01-R001", direction="long",
                       valid_from=1000, valid_until=2000)
    assert recompute_sealed_hash(release) == release["sealed_hash"]


# --- W3: the leak drill ----------------------------------------------------


def test_leak_drill(tmp_path):
    log = DrillLog()
    clean_release = publish(SYNTHETIC_VERDICT, measurement_id="LS-01-R001", direction="long",
                             valid_from=1000, valid_until=2000)

    def checker(inject_leak: bool):
        release = dict(clean_release)
        if inject_leak:
            release["p_value"] = 0.01  # a derivation detail, must never cross
        verify_no_leak(release)

    result = run_drill(
        name="publication-boundary-leak",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=PublicationLeak,
        log=log,
    )
    assert result.tampered_exception is PublicationLeak

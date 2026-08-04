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
    null_name="block_resampling_v1",
    null_parameters={"block_length": 20},
    observed_statistic=0.0012,
    source_sha256="0" * 64,
)

NOT_SIGNIFICANT_VERDICT = Verdict(
    hypothesis_id="SYNTHETIC-DEMO-H002",
    p_value=0.4,
    alpha=0.025,
    significant=False,
    n_resamples=5000,
    seed=1,
    null_name="block_resampling_v1",
    null_parameters={"block_length": 20},
    observed_statistic=0.0001,
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
    for forbidden in ("p_value", "alpha", "n_resamples", "seed", "null_name", "null_parameters",
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


# --- A-030 R1: direction is significant-conditional -------------------


def test_not_significant_release_has_no_direction_key():
    release = publish(
        NOT_SIGNIFICANT_VERDICT, measurement_id="LS-01-R001", direction=None,
        valid_from=1000, valid_until=2000,
    )
    assert "direction" not in release
    assert release["significant"] is False


def test_significant_requires_direction_drill():
    log = DrillLog()

    def checker(omit_direction: bool):
        publish(
            SYNTHETIC_VERDICT, measurement_id="LS-01-R001",
            direction=None if omit_direction else "long",
            valid_from=1000, valid_until=2000,
        )

    result = run_drill(
        name="publish-significant-requires-direction",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=ValueError,
        log=log,
    )
    assert result.tampered_exception is ValueError


def test_not_significant_forbids_direction_drill():
    log = DrillLog()

    def checker(supply_direction: bool):
        publish(
            NOT_SIGNIFICANT_VERDICT, measurement_id="LS-01-R001",
            direction="long" if supply_direction else None,
            valid_from=1000, valid_until=2000,
        )

    result = run_drill(
        name="publish-not-significant-forbids-direction",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=ValueError,
        log=log,
    )
    assert result.tampered_exception is ValueError


def test_verify_no_leak_catches_direction_on_not_significant_release():
    """Defense in depth: even a release that bypassed publish()'s own
    check (e.g. hand-built) is still caught by verify_no_leak().
    """
    hand_built = {
        "schema_version": 1,
        "hypothesis_id": "H1",
        "measurement_id": "LS-01-R001",
        "significant": False,
        "direction": "long",  # the leak: a direction on a null result
        "valid_from": 1000,
        "valid_until": 2000,
        "release_id": "x",
        "sealed_hash": "x",
    }
    with pytest.raises(PublicationLeak):
        verify_no_leak(hand_built)

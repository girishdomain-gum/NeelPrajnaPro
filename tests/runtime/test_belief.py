"""S07 W2: Belief.update() refuses a non-ReleasedKnowledge input, by name."""

from qrf.kernel.battery.battery import Verdict
from qrf.kernel.publication.release import publish
from runtime.belief import Belief
from runtime.errors import UntypedInput
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


def _released_knowledge():
    release = publish(
        SYNTHETIC_VERDICT, measurement_id="LS-01-R001", direction="long",
        valid_from=1000, valid_until=2000,
    )
    return ReleasedKnowledge.from_release_dict(release)


def test_update_and_latest_round_trip():
    belief = Belief()
    rk = _released_knowledge()
    belief.update(rk)
    assert belief.latest("SYNTHETIC-DEMO-H001") is rk
    assert belief.known_hypotheses() == ("SYNTHETIC-DEMO-H001",)


def test_unknown_hypothesis_returns_none():
    assert Belief().latest("NEVER-RELEASED") is None


def test_untyped_input_refused_drill():
    """A raw dict with every field correct is STILL refused -- passing the
    actual type is the point, not merely having the right shape.
    """
    log = DrillLog()
    belief = Belief()
    rk = _released_knowledge()

    def checker(pass_raw_dict: bool):
        if pass_raw_dict:
            belief.update(rk.__dict__)  # every field correct, wrong type
        else:
            belief.update(rk)

    result = run_drill(
        name="belief-untyped-input-refused",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=UntypedInput,
        log=log,
    )
    assert result.tampered_exception is UntypedInput

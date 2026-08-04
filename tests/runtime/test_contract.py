"""S07 W5 (Python side): an instruction's expiry, and that build_instruction
carries the release's own validity window rather than inventing one.
"""

import pytest

from qrf.kernel.battery.battery import Verdict
from qrf.kernel.publication.release import publish
from runtime.contract import build_instruction
from runtime.types import ReleasedKnowledge

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


def _released_knowledge(direction="long"):
    release = publish(
        SYNTHETIC_VERDICT, measurement_id="LS-01-R001", direction=direction,
        valid_from=1000, valid_until=2000,
    )
    return ReleasedKnowledge.from_release_dict(release)


def _not_significant_released_knowledge():
    release = publish(
        NOT_SIGNIFICANT_VERDICT, measurement_id="LS-01-R001", direction=None,
        valid_from=1000, valid_until=2000,
    )
    return ReleasedKnowledge.from_release_dict(release)


def test_instruction_carries_release_validity_window():
    instr = build_instruction(_released_knowledge(), trigger_price=4044.60)
    assert instr.valid_from == 1000
    assert instr.valid_until == 2000
    assert instr.direction == "long"
    assert instr.action == "open"


def test_expiry():
    instr = build_instruction(_released_knowledge(), trigger_price=4044.60)
    assert instr.is_expired(2001) is True
    assert instr.is_expired(2000) is False
    assert instr.is_expired(1500) is False


def test_not_significant_release_refused():
    """A-030 R1: a not-significant release has no direction to act on --
    build_instruction() must refuse it, not silently trade on absence.
    """
    with pytest.raises(ValueError):
        build_instruction(_not_significant_released_knowledge(), trigger_price=4044.60)

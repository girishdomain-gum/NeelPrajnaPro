"""S07 W8: end-to-end on a clearly-marked SYNTHETIC verdict --
published -> consumed -> feedback ingested as observations. Nothing
armed, nothing traded, at any point (no order-placement call exists
anywhere this path touches -- runtime/ has none, and RefusalEA.mq5's own
W9 drill proves the EA side has none either).

HOW THE SYNTHETIC ARTIFACT IS GUARANTEED NEVER TO BE MISTAKEN FOR A REAL
ONE (A-029 §2.6): this test constructs its `Verdict` BY HAND, directly as
a dataclass literal, never through `qrf.kernel.battery.battery.Battery`,
never against a `TrialLedger` registration, never against a real
`WindowLedger` window. A real verdict can only exist by passing through
`Battery.judge()`, which requires a REGISTERED hypothesis_id (refused
otherwise, HypothesisNotRegistered) and burns a real VIRGIN window
atomically. `hypothesis_id="SYNTHETIC-DEMO-H001"` was never registered
anywhere in this project's TrialLedger and never will be -- the
traceable guarantee is process separation (this artifact never touched
the real registration/battery pipeline), not a boolean flag that could
be forgotten or forged.
"""

from qrf.kernel.battery.battery import Verdict
from qrf.kernel.publication.release import publish
from runtime.belief import Belief
from runtime.consumption import consume, ingest_feedback
from runtime.contract import build_instruction
from runtime.dashboard import render_mirror
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


def test_end_to_end_publish_consume_feedback(tmp_path):
    # 1. PUBLISH -- crosses the Publication Boundary, WHAT only.
    release = publish(
        SYNTHETIC_VERDICT,
        measurement_id="LS-01-R001",
        direction="long",
        valid_from=1000,
        valid_until=2000,
    )
    assert "p_value" not in release  # the boundary held

    # 2. BELIEF -- accepts only a real ReleasedKnowledge.
    rk = ReleasedKnowledge.from_release_dict(release)
    belief = Belief()
    belief.update(rk)
    assert belief.latest("SYNTHETIC-DEMO-H001") is rk

    # 3. CONTRACT -- an expiring, conditional instruction.
    instruction = build_instruction(rk, trigger_price=4044.60)

    # 4. CONSUMPTION -- staged for the EA, well within its validity window.
    result = consume(instruction, now=1500, stage_path=tmp_path / "instruction.json")
    assert result.staged_path.exists()

    # 5. EXECUTION FEEDBACK -- what the real EA would report back (here,
    #    simulated: the real RefusalEA.mq5 places no order in S07 by
    #    design, so the only real feedback shape possible this sprint is
    #    a pass/refuse log line, never a fill).
    feedback = ingest_feedback(
        {"instruction_id": instruction.instruction_id, "result": "validated_no_order_placed"},
        tmp_path / "feedback.jsonl",
    )
    assert feedback["result"] == "validated_no_order_placed"

    # 6. MIRROR -- watches the whole chain, changes nothing.
    text = render_mirror(belief, [feedback])
    assert "SYNTHETIC-DEMO-H001" in text
    assert "validated_no_order_placed" in text

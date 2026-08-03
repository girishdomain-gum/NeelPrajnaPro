"""S07 W5: consume() refuses an expired instruction BEFORE staging it.
Also proves the feedback log round-trips and is append-only (seq order).
"""

import json

from qrf.kernel.battery.battery import Verdict
from qrf.kernel.publication.release import publish
from runtime.consumption import ConsumptionResult, consume, ingest_feedback
from runtime.contract import build_instruction
from runtime.errors import ExpiredInstruction
from runtime.types import ReleasedKnowledge
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


def _instruction():
    release = publish(
        SYNTHETIC_VERDICT, measurement_id="LS-01-R001", direction="long",
        valid_from=1000, valid_until=2000,
    )
    rk = ReleasedKnowledge.from_release_dict(release)
    return build_instruction(rk, trigger_price=4044.60)


def test_consume_stages_a_valid_instruction(tmp_path):
    instr = _instruction()
    result = consume(instr, now=1500, stage_path=tmp_path / "staged.json")
    assert isinstance(result, ConsumptionResult)
    assert result.staged_path.exists()
    staged = json.loads(result.staged_path.read_text())
    assert staged["instruction_id"] == instr.instruction_id


def test_expired_instruction_refused_before_staging_drill(tmp_path):
    log = DrillLog()
    instr = _instruction()
    tampered_stage_path = tmp_path / "tampered_staged.json"

    def checker(expired: bool):
        now = 2001 if expired else 1999
        stage_path = tampered_stage_path if expired else tmp_path / "clean_staged.json"
        consume(instr, now=now, stage_path=stage_path)

    result = run_drill(
        name="consumption-expiry-refused",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=ExpiredInstruction,
        log=log,
    )
    assert result.tampered_exception is ExpiredInstruction
    # the refusal must have happened BEFORE anything was staged
    assert not tampered_stage_path.exists()


def test_feedback_log_round_trip_and_seq(tmp_path):
    log_path = tmp_path / "feedback.jsonl"
    r1 = ingest_feedback({"instruction_id": "x:open", "result": "refused_expired"}, log_path)
    r2 = ingest_feedback({"instruction_id": "y:open", "result": "refused_malformed"}, log_path)
    assert r1["logged_seq"] == 0
    assert r2["logged_seq"] == 1
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["logged_seq"] == 0

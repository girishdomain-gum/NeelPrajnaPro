"""S07 W9: the refusal-only EA is token-scanned for order-placement calls
and pattern-logic vocabulary. This is a source-text check, not a
compile/run check -- CI has no MT5 terminal (S03's own launcher.py
docstring already established this limitation; unchanged here). The EA
is compiled and exercised by hand against the real terminal, and that
real run is the evidence, exactly like `run_export()`.
"""

from pathlib import Path

from runtime.errors import ActionCapableControl
from tests.drills.harness import DrillLog, run_drill

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EA_SOURCE = REPO_ROOT / "mql5" / "EA" / "QRF" / "RefusalEA.mq5"

# 3.3: "there is no order-sending call in the file" -- the literal check.
ORDER_PLACEMENT_TOKENS = (
    "ordersend(", "orderclose(", "positionopen(", "trade.buy(", "trade.sell(",
    "ctrade", "cpositioninfo",
)

# AM-02: no pattern-logic vocabulary. Deliberately SPECIFIC identifiers
# (Fable's actual gate module names, concept phrases) rather than bare
# English words like "gate" or "bias" -- this file's own header
# legitimately says "no bias, no trigger, no gate" in prose, and a naive
# substring match on those words would flag its own disclaimer.
PATTERN_LOGIC_TOKENS = (
    "b1_nexisgate", "b2_mtfcandle", "b3_keylevelgate", "b4_smcgate",
    "b6_regchannelgate", "t1_patterngate", "t2_autofibogate", "t3_sweepfvggate",
    "t4_trendlinesgate", "t5_topographygate", "t7_marketmetricsgate",
    "t8_cmhcandlegate", "t9_ccchiddengate", "entrygates.mqh", "advisorengine.mqh",
    "liquidity sweep", "fair value gap", "order block",
)


def scan_ea_source(source_text: str) -> None:
    lowered = source_text.lower()
    for token in ORDER_PLACEMENT_TOKENS + PATTERN_LOGIC_TOKENS:
        if token in lowered:
            raise ActionCapableControl(token)


def test_real_ea_source_is_clean():
    scan_ea_source(EA_SOURCE.read_text(encoding="utf-8"))


def test_order_placement_drill():
    log = DrillLog()
    clean_source = EA_SOURCE.read_text(encoding="utf-8")

    def checker(inject_order_call: bool):
        source = clean_source
        if inject_order_call:
            source += "\n// drill: OrderSend(request, result);\n"
        scan_ea_source(source)

    result = run_drill(
        name="ea-no-order-placement",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=ActionCapableControl,
        log=log,
    )
    assert result.tampered_exception is ActionCapableControl


def test_pattern_logic_drill():
    log = DrillLog()
    clean_source = EA_SOURCE.read_text(encoding="utf-8")

    def checker(inject_gate: bool):
        source = clean_source
        if inject_gate:
            source += "\n// drill: #include \"B4_SMCGate.mqh\"\n"
        scan_ea_source(source)

    result = run_drill(
        name="ea-no-pattern-logic",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=ActionCapableControl,
        log=log,
    )
    assert result.tampered_exception is ActionCapableControl


def test_staged_field_names_match_instruction_to_dict():
    """The EA's hand-written JSON reader names five fields
    (instruction_id, direction, action, trigger_price, valid_until) --
    proves those are exactly a subset of what
    runtime.contract.Instruction.to_dict() actually emits, so the two
    sides cannot silently drift apart.
    """
    from qrf.kernel.battery.battery import Verdict
    from qrf.kernel.publication.release import publish
    from runtime.contract import build_instruction
    from runtime.types import ReleasedKnowledge

    verdict = Verdict(
        hypothesis_id="SYNTHETIC-DEMO-H001", p_value=0.01, alpha=0.025, significant=True,
        n_resamples=5000, seed=1, null_name="block_resampling_v1",
        null_parameters={"block_length": 20}, observed_statistic=0.0012,
        source_sha256="0" * 64,
    )
    release = publish(verdict, measurement_id="LS-01-R001", direction="long",
                       valid_from=1000, valid_until=2000)
    rk = ReleasedKnowledge.from_release_dict(release)
    instr = build_instruction(rk, trigger_price=4044.60)
    payload_keys = set(instr.to_dict())

    ea_source = EA_SOURCE.read_text(encoding="utf-8")
    for field in ("instruction_id", "direction", "action", "trigger_price", "valid_until"):
        assert field in payload_keys, f"EA reads {field!r} but Instruction.to_dict() lacks it"
        assert f'"{field}"' in ea_source, f"EA source never references {field!r}"

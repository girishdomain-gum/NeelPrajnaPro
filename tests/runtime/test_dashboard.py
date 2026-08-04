"""S07 W7: the mirror dashboard contains no action-capable control --
drilled, not asserted. Scans SOURCE TEXT for a banned action-vocabulary
list, the same static-text approach the firewall test uses for imports
(ast there, plain substring here since MQL5-style "controls" don't parse
as Python AST nodes worth special-casing -- a banned identifier is a
banned identifier either way).
"""

from pathlib import Path

from runtime.errors import ActionCapableControl
from tests.drills.harness import DrillLog, run_drill

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DASHBOARD_SOURCE = REPO_ROOT / "runtime" / "dashboard.py"

# Case-insensitive substrings that would indicate a steering control.
# "significant"/"direction" etc. are fine to display; these are the verbs
# that would let the mirror ACT rather than merely report.
BANNED_TOKENS = (
    "def buy(", "def sell(", "def close(", "def enable(", "def disable(",
    "def arm(", "def execute(", "def place_order(", "ordersend", "order_send",
    "ctrade", "positionopen",
)


def scan_for_action_controls(source_text: str) -> None:
    lowered = source_text.lower()
    for token in BANNED_TOKENS:
        if token in lowered:
            raise ActionCapableControl(token)


def test_real_dashboard_source_is_clean():
    scan_for_action_controls(DASHBOARD_SOURCE.read_text(encoding="utf-8"))


def test_action_control_drill():
    log = DrillLog()
    clean_source = DASHBOARD_SOURCE.read_text(encoding="utf-8")

    def checker(inject_control: bool):
        source = clean_source
        if inject_control:
            source += "\n\ndef buy(symbol, lots):\n    pass\n"
        scan_for_action_controls(source)

    result = run_drill(
        name="dashboard-no-action-controls",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=ActionCapableControl,
        log=log,
    )
    assert result.tampered_exception is ActionCapableControl


def test_render_mirror_is_pure_text():
    from runtime.belief import Belief
    from runtime.dashboard import render_mirror

    text = render_mirror(Belief(), [])
    assert isinstance(text, str)
    assert "Known hypotheses: 0" in text

"""The mirror dashboard (A-029 §4): watches, never steers. This module
contains exactly one function, it takes data in and returns text out, and
it has no function whose name or effect could place, close, or toggle
anything. That is not just a design intent here -- it is drilled
mechanically in tests/runtime/test_dashboard.py by scanning THIS FILE'S
OWN SOURCE for any of a banned action-vocabulary list, the same
static-analysis-over-source-text approach the firewall test already uses
for imports. Fable's own Dashboard.mqh is the documented counter-example
(S07 import plan, A-028): live BUY/SELL/CLOSE buttons and per-gate
enable/disable checkboxes wired to CHARTEVENT_OBJECT_CLICK. Nothing here
resembles that by construction, not just by inspection.
"""

from __future__ import annotations

from runtime.belief import Belief


def render_mirror(belief: Belief, consumption_log: list[dict]) -> str:
    """Pure: reads `belief`'s known hypotheses and a list of already-
    logged consumption/feedback records, returns a plain-text summary.
    No parameter is mutated, nothing is written to disk, nothing is sent
    anywhere -- this function cannot act even if called with hostile
    input, because it has no side-effecting statement to hijack.
    """
    lines = ["=== QRF Runtime Mirror (read-only) ==="]
    hypotheses = belief.known_hypotheses()
    lines.append(f"Known hypotheses: {len(hypotheses)}")
    for hid in hypotheses:
        release = belief.latest(hid)
        lines.append(
            f"  {hid}: measurement={release.measurement_id} "
            f"significant={release.significant} direction={release.direction} "
            f"valid=[{release.valid_from},{release.valid_until})"
        )
    lines.append(f"Consumption/feedback records: {len(consumption_log)}")
    for record in consumption_log:
        lines.append(f"  {record}")
    return "\n".join(lines)

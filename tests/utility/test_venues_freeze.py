"""venues.yaml freeze test (DEVQ-008 ruling, REV-S4 micro-task 1).

Cost models are versioned CONFIG, not instruments. The binding rule from the
DEVQ-008 reply: the moment a cost-model name is cited by ANY ledger record, its
yaml definition is FROZEN — every change is a NEW name, and editing a cited entry
in ``configs/venues.yaml`` is forbidden. This test enforces that mechanically:

1. Each FROZEN name's parameters must match a pinned snapshot to the value — so
   an edit to a cited entry turns CI red and forces a new name instead.
2. Every cost-model name CITED in the real journal (screener shortlist notes)
   must appear in FROZEN — so a newly-cited name cannot escape the freeze
   unnoticed; adding it here is the deliberate act of freezing it.
"""

from __future__ import annotations

import json
from pathlib import Path

from qrf.trading.utility.cost_models import load_cost_model

REPO_ROOT = Path(__file__).resolve().parents[2]
JOURNAL = REPO_ROOT / "datastore" / "journal" / "journal.jsonl"

# Pinned snapshot of every cost-model name that has been cited by a ledger
# record. Editing any value here (or in venues.yaml) is a contract change: mint a
# NEW name (e.g. xauusd_retail_median_v2) instead of touching a frozen entry.
FROZEN: dict[str, dict] = {
    "xauusd_retail_median": {
        "spread": 0.30,
        "slippage_per_side": 0.05,
        "commission_per_side": 0.035,
        "version": "0.1.0",
    },
}


def _cited_cost_models() -> set[str]:
    """Every cost_model name cited by a screener_shortlist note in the real journal."""
    if not JOURNAL.exists():
        return set()
    cited: set[str] = set()
    for line in JOURNAL.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("record_type") != "note":
            continue
        try:
            body = json.loads(rec.get("payload", {}).get("text", ""))
        except (ValueError, TypeError):
            continue
        if isinstance(body, dict) and body.get("kind") == "screener_shortlist":
            cm = body.get("cost_model")
            if isinstance(cm, str):
                cited.add(cm)
    return cited


def test_frozen_cost_models_match_pinned_snapshot():
    for name, snap in FROZEN.items():
        m = load_cost_model(name)
        assert m.spread == snap["spread"], name
        assert m.slippage_per_side == snap["slippage_per_side"], name
        assert m.commission_per_side == snap["commission_per_side"], name
        assert m.version == snap["version"], name
        # The derived round-trip cost is part of the frozen contract too.
        assert m.cost_per_unit == snap["spread"] + 2 * (
            snap["slippage_per_side"] + snap["commission_per_side"]
        )


def test_every_cited_cost_model_is_frozen():
    cited = _cited_cost_models()
    unfrozen = cited - set(FROZEN)
    assert not unfrozen, (
        f"cost model(s) {sorted(unfrozen)} are cited by a ledger record but not in "
        "FROZEN — pin their parameters here to freeze them (DEVQ-008 ruling)"
    )


def test_the_reference_venue_is_actually_cited():
    # Guard the freeze test against silently passing on an empty journal: the
    # reference venue really is cited in the committed ledger.
    assert "xauusd_retail_median" in _cited_cost_models()

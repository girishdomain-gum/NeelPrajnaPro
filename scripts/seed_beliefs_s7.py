"""ARCH-007 §3 — seed the belief ledger from the real verdict set.

The belief ledger holds what the evidence has taught us, updated ONLY by verdicts.
H-001's FAIL must produce exactly one REJECTED belief for the naive FVG
follow-through claim, citing the verdict (01KYC7Y2KWYGXH73V1R9P57MYA). Idempotent:
if the belief already cites the verdict it is returned unchanged.

Run:  uv run python scripts/seed_beliefs_s7.py
"""

from __future__ import annotations

from qrf.kernel.belief import BeliefLayer
from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"

H001_VERDICT = "01KYC7Y2KWYGXH73V1R9P57MYA"
FAMILY = "xauusd_h1/smc.fvg"
CLAIM = "Naive FVG follow-through (smc.fvg, xauusd_h1) is profitable net of costs"


def main() -> None:
    store = RecordStore(JOURNAL)
    beliefs = BeliefLayer(store)

    rec = beliefs.update(H001_VERDICT, claim=CLAIM, family=FAMILY, producer="belief")
    p = rec.payload
    print(f"belief record = {rec.record_id}")
    print(f"  family   : {p['family']}")
    print(f"  claim    : {p['claim']}")
    print(f"  stance   : {p['stance']}   strength: {p['strength']}")
    print(f"  verdict_refs: {p['verdict_refs']}")
    if "prev_state" in p:
        print(f"  prev_state: {p['prev_state']}")
    report = store.verify()
    print(f"journal verify ok={report.ok} n_records={len(store)} head={report.head_hash[:12]}")


if __name__ == "__main__":
    main()

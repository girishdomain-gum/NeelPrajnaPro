"""ARCH-007 §3 (+ DEVQ-016) — seed the belief ledger from the real verdict set.

The belief ledger holds what the evidence has taught us, updated ONLY by verdicts.
H-001's FAIL produces a REJECTED belief for the naive FVG follow-through claim,
citing the verdict (01KYC7Y2KWYGXH73V1R9P57MYA).

Then re-derive under the DEVQ-016 decisiveness formula (strength = 2·|p−0.5|): the
first belief state was sealed under the retired p-as-strength rule (strength
0.9435); re-derivation appends a NEW state at strength 0.887 pointing at the prior
one — the old state REMAINS in the chain (append-only memory, the belief layer's
first demonstration that a formula change is recorded, not overwritten). Idempotent
on both steps.

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
    print(f"belief state (from verdict) = {rec.record_id}  "
          f"stance={rec.payload['stance']} strength={rec.payload['strength']}")

    # Re-derive under the current (DEVQ-016 decisiveness) formula. Appends a new
    # state iff the numbers moved; the prior state stays in the chain.
    head = beliefs.rederive(FAMILY, CLAIM, producer="belief")
    p = head.payload
    print(f"belief HEAD (current formula) = {head.record_id}")
    print(f"  family   : {p['family']}")
    print(f"  claim    : {p['claim']}")
    print(f"  stance   : {p['stance']}   strength: {p['strength']}")
    print(f"  verdict_refs: {p['verdict_refs']}")
    if "prev_state" in p:
        print(f"  prev_state: {p['prev_state']} (retired p-as-strength state, kept in chain)")
    report = store.verify()
    print(f"journal verify ok={report.ok} n_records={len(store)} head={report.head_hash[:12]}")


if __name__ == "__main__":
    main()

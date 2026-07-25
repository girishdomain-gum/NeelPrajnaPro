"""ARCH-008 T0 — chain Sprint 8 to the record.

Appends the GO-S7 ``note`` record (Owner decision GO, both verbatim Owner phrases,
the observatory question ids and the belief-chain ids ratified at GO-S7), parented
on the GO-S6 note that Sprint 7's own T0 laid down. This is the sprint's first
commit: every sprint begins by writing the previous sprint's close into the
append-only memory, so the ledger itself carries the sprint boundary.

Idempotent: if the GO-S7 note is already present it refuses to append a second.

    F:/QRF/.venv/Scripts/python.exe scripts/t0_s8.py
"""

from __future__ import annotations

import time

from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"

# The GO-S6 note laid down by Sprint 7's T0 — this sprint's chain parent.
GO_S6_NOTE = "01KYCEKQF2SPZ9T9XX705F8QE1"

GO_S7_NOTE_TEXT = (
    "Sprint 7 (Observatory + Beliefs) signed off by Owner: "
    "'Signed off — Sprint 7 closed'; HC sign-off 'HC-S7 PASS'. "
    "GO-S7: decision GO (AC 748 tests + ruff clean + firewall GREEN; "
    "VC check_s7_observatory rev3 GREEN zero amber — weekend partition "
    "twice-derived to 15 decimals (n=18 / -1.559444444444403 vs "
    "n=807 / -0.12840148698884718); drill CAUGHT x2 + clean control non-red; "
    "HC stratified PASS). Observatory questions "
    "01KYCFNE46BB7H2V300D1WZG1P (weekend-born FVGs behave differently, "
    "-1.56 vs -0.13) + 01KYCFNE69PEGMQHH85W8MT528 (H-001 deterioration "
    "~= costs/regime, not raw decay). Beliefs "
    "01KYCFNKCGSYFKWTRYKW54E9C8 -> 01KYCHPV8ZNT2F41F8JABD12K2 "
    "(REJECTED, strength 0.887, citing H-001 verdict "
    "01KYC7Y2KWYGXH73V1R9P57MYA; superseded state retained). "
    "Journal 41 records, chain GREEN; VIRGIN untouched. S8 T0."
)


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies the chain on open

    for n in store.query(record_type="note"):
        if n.payload["text"].startswith("Sprint 7 (Observatory + Beliefs) signed off"):
            print(f"GO-S7 note already present ({n.record_id}) — T0 is idempotent, nothing to do.")
            return

    if GO_S6_NOTE not in {r.record_id for r in store.query()}:
        raise SystemExit(
            f"chain parent {GO_S6_NOTE} (GO-S6 note) not found in the journal; "
            "refusing to append an unparented S8 T0"
        )

    rec = store.append(
        "note",
        {"text": GO_S7_NOTE_TEXT},
        producer="human:girish",
        event_ts=time.time_ns(),
        parents=[GO_S6_NOTE],
    )
    report = store.verify()
    print(f"S8 T0 appended GO-S7 note {rec.record_id}")
    print(f"  parents = {list(rec.parents)}")
    print(f"journal verify ok={report.ok} n_records={report.n_records} head={report.head_hash[:12]}")


if __name__ == "__main__":
    main()

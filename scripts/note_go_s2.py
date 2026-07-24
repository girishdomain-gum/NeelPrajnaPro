"""ARCH-003 T0 — append the GO-S2 sign-off note to the real journal.

One ``note`` record recording the Owner's Sprint-2 Go/No-Go, parented to the
GO-S1 note record (Blueprint §2 note; ARCH-003 T0). Idempotent: if a note with
this exact text already exists it reports the id and writes nothing.

Run:  uv run python scripts/note_go_s2.py
"""

from __future__ import annotations

from qrf.kernel.records.record import now_ns
from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"

# Parent = the GO-S1 note record (ARCH-003 T0).
GO_S1_NOTE = "01KYAJA3TMM03K1MYMCTRE9033"

NOTE_TEXT = (
    "Sprint 2 signed off by Owner: 'S2 VC GREEN, drill RED caught, HC done "
    "— sign off Sprint 2'. GO-S2: VC rev3 GREEN on real XAUUSD (red=0 amber=0), "
    "drill S2 caught (144), HC on real sampled events. DEVQ-005 DOW contract ratified."
)


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies chain on open

    for rec in store.query(record_type="note"):
        if rec.payload.get("text") == NOTE_TEXT:
            print(f"already present: GO-S2 note = {rec.record_id}")
            return

    if GO_S1_NOTE not in {r.record_id for r in store.query()}:
        raise SystemExit(f"GO-S1 parent {GO_S1_NOTE} not found in journal")

    rec = store.append(
        "note",
        {"text": NOTE_TEXT},
        producer="human:girish",
        event_ts=now_ns(),
        parents=[GO_S1_NOTE],
    )
    report = store.verify()
    print(f"appended GO-S2 note = {rec.record_id}")
    print(f"journal verify ok={report.ok} n_records={len(store)} head={report.head_hash[:12]}")


if __name__ == "__main__":
    main()

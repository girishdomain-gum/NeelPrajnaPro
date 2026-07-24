"""ARCH-004 T0 — append the GO-S3 sign-off note to the real journal.

One ``note`` record recording the Owner's Sprint-3 Go/No-Go, parented to the
GO-S2 note record (Blueprint §2 note; ARCH-004 T0). Everything in Sprint 4
descends from this record. Idempotent: if a note with this exact text already
exists it reports the id and writes nothing.

Run:  uv run python scripts/note_go_s3.py
"""

from __future__ import annotations

from qrf.kernel.records.record import now_ns
from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"

# Parent = the GO-S2 note record (ARCH-004 T0; found via query record_type=note).
GO_S2_NOTE = "01KYAVQFR4F94XPMT3C52TFFW0"

# Window ids declared at GO-S3 (xauusd_h1_full).
TRAINING_WINDOW = "01KYB4SSC96SSS8RA7D1NMTPEX"
VIRGIN_WINDOW = "01KYB4SSD9VVKB577KRGB1W1P0"

NOTE_TEXT = (
    "Sprint 3 (data plane) signed off by Owner: 'Signed off — Sprint 3 "
    "closed'; HC sign-off 'HC-S3 PASS'. GO-S3: decision GO (AC + VC GREEN "
    "504/504 exact + quarantine 6/6 anomaly classes AUDITED; drill CAUGHT x2; "
    "HC 5/5 MATCH, tool rev 4). Windows on xauusd_h1_full: "
    f"TRAINING {TRAINING_WINDOW} [1704160800000000000,1726128000000000000) "
    f"4157 bars; VIRGIN {VIRGIN_WINDOW} "
    "[1726128000000000000,1735689600000000001) 1781 bars, declared by the "
    "Owner's typed 'DECLARE VIRGIN' and untouchable until spent by the battery. "
    "Contracts ratified: DEVQ-006, DEVQ-007, ADR-009, PROTOCOL v1.2/v1.3. "
    "This note anchors Sprint 4 (screener + costs + SMC)."
)


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies chain on open

    for rec in store.query(record_type="note"):
        if rec.payload.get("text") == NOTE_TEXT:
            print(f"already present: GO-S3 note = {rec.record_id}")
            return

    if GO_S2_NOTE not in {r.record_id for r in store.query()}:
        raise SystemExit(f"GO-S2 parent {GO_S2_NOTE} not found in journal")

    rec = store.append(
        "note",
        {"text": NOTE_TEXT},
        producer="human:girish",
        event_ts=now_ns(),
        parents=[GO_S2_NOTE],
    )
    report = store.verify()
    print(f"appended GO-S3 note = {rec.record_id}")
    print(f"journal verify ok={report.ok} n_records={len(store)} head={report.head_hash[:12]}")


if __name__ == "__main__":
    main()

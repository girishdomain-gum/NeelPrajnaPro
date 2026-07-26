"""ARCH-010 T0 — chain Sprint 10 to the record.

Appends the GO-S9 ``note`` record (Owner decision GO on REV-S9's PASS
recommendation, the Sprint 9 close facts, and the Second-Lens / rebuild /
enforcement record ids ratified at GO-S9), parented on the GO-S8 note that
Sprint 9's own T0 laid down. This is the sprint's first commit: every sprint
begins by writing the previous sprint's close into the append-only memory, so
the ledger itself carries the sprint boundary. The note also refs this sprint's
instruction (ARCH-010) — sprint 10 open.

Idempotent: if the GO-S9 note is already present it refuses to append a second.

    F:/QRF/.venv/Scripts/python.exe scripts/t0_s10.py
"""

from __future__ import annotations

import time

from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"

# The GO-S8 note laid down by Sprint 9's T0 — this sprint's chain parent.
GO_S8_NOTE = "01KYDA4KXFBAA7461JJP6H1ZX9"

GO_S9_NOTE_TEXT = (
    "Sprint 9 (Second Lens + Rebuild + Enforcement) signed off by Owner: "
    "'go' (on REV-S9's PASS recommendation). GO-S9: decision GO. AC: "
    "§1 rebuild (4 lineages + overlap, sha assert-equal, byte-identity by "
    "shared construction); §2 placebo_method sealed (registry + judge "
    "refusals, Wave-1 grandfathered); §3 HC rev-2 shipped by the Architect; "
    "§4 second feed ingested (tier=BROKER declared), 2025 windows designated "
    "by the Owner's typed phrase (producer human:girish), first second_lens "
    "01KYE3WCKK40PNJ8JEATQ4XTNT (agreement_rate 0.9544 ≥ 0.95 — the feeds "
    "corroborate), overlap manifest 01KYE3WCJ7B954M3NRV2PGRZV9, H-004 judged "
    "placebo-first (FAIL, n=56, p=0.108). 843 tests · firewall 8/8 GREEN · "
    "journal 73 chain GREEN · both VIRGIN reserves untouched. VC check_s9 rev1 "
    "GREEN (every recorded number re-derived incl. CI replay and the full lens "
    "recomputation from the sealed note text) · Drill CAUGHT x5 (incl. the "
    "ordering fraud and the single-shift-across-DST lens) · HC 6/6 (rev-2 "
    "tool; MONX entry AND exit same-Monday). Record entries: H-004 hypothesis "
    "01KYDH7SGVXNTKDCZE2K84XGCD (schema v3, placebo_method sealed), placebo "
    "01KYDH7T3H2BT82FDNSJX80WSB (1/20), verdict 01KYDH7T6SH1D0AJMA70M2H0P8 "
    "(FAIL), burns x2 (both training windows), windows 01KYDE784029 "
    "(2025-TRAINING) / 01KYDE784NHY (2025-VIRGIN, reserve), sealed notes "
    "01KYDCNRM4 / 01KYDDMKQJ / 01KYE3BBE2 (the DEVQ-023 correction, sealed "
    "before the overlap run). Contracts ratified: DEVQ-022 (multi-window Option "
    "A, min_n 45, seam fix, reserve-by-market-time doctrine) / DEVQ-023 "
    "(agreement-rate discriminator, empirical US-DST segmentation, two-part + "
    "prediction guards; a loosened guard to admit a result is prohibited "
    "doctrine; Option C condemned). Tally: Architect 17, Developer 4 — every "
    "entry caught before harm. Journal 73 records, chain GREEN; both VIRGINs "
    "untouched. S10 open per ARCH-010 (Trial Accounting + Exploration Wave 2): "
    "count every attempt, then go looking again — and the formal conclusion "
    "of Generation 1. S10 T0."
)


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies the chain on open

    for n in store.query(record_type="note"):
        if n.payload["text"].startswith(
            "Sprint 9 (Second Lens + Rebuild + Enforcement) signed off"
        ):
            print(
                f"GO-S9 note already present ({n.record_id}) — T0 is idempotent, "
                "nothing to do."
            )
            return

    if GO_S8_NOTE not in {r.record_id for r in store.query()}:
        raise SystemExit(
            f"chain parent {GO_S8_NOTE} (GO-S8 note) not found in the journal; "
            "refusing to append an unparented S10 T0"
        )

    rec = store.append(
        "note",
        {"text": GO_S9_NOTE_TEXT},
        producer="human:girish",
        event_ts=time.time_ns(),
        parents=[GO_S8_NOTE],
    )
    report = store.verify()
    print(f"S10 T0 appended GO-S9 note {rec.record_id}")
    print(f"  parents = {list(rec.parents)}")
    print(
        f"journal verify ok={report.ok} n_records={report.n_records} "
        f"head={report.head_hash[:12]}"
    )


if __name__ == "__main__":
    main()

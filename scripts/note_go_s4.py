"""ARCH-005 T0 — append the GO-S4 sign-off note to the real journal.

One ``note`` record recording the Owner's Sprint-4 Go/No-Go, parented to the
GO-S3 note record (ARCH-005 T0). Everything in Sprint 5 descends from this
record. Idempotent: if a note with this exact text already exists it reports
the id and writes nothing.

Run:  uv run python scripts/note_go_s4.py
"""

from __future__ import annotations

from qrf.kernel.records.record import now_ns
from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"

# Parent = the GO-S3 note record (ARCH-005 T0).
GO_S3_NOTE = "01KYB5ARJPK3YK0AKCE9FP7DAH"

# Key Sprint-4 records (GO-S4 ledger state; existence verified before append).
SMC_FVG_REGISTERED = "01KYB7QQ7Y38PP5MKHEQ3X2G5Z"
SMC_FVG_CALIBRATED = "01KYB7QQA5W466QRPWCBC76K5S"
SMC_OB_REGISTERED = "01KYB7QQASN2429EKEQN0DKPT9"
SMC_OB_CALIBRATED = "01KYB7QQDQFCAQVV0BMPHDMK9R"
FVG_EVENTS_MANIFEST = "01KYB7WQFND907DMH550GPKMW0"
SHORTLIST_MANIFEST = "01KYB7X2YNXZKXR4E97HMQ1PFC"
TRIAL_COUNT = "01KYB7X308YS3KMV8C95MZ028E"
VIRGIN_WINDOW = "01KYB4SSD9VVKB577KRGB1W1P0"

NOTE_TEXT = (
    "Sprint 4 (screener + costs + SMC) signed off by Owner: 'Signed off "
    "— Sprint 4 closed'; HC sign-off 'HC-S4 PASS'. GO-S4: decision GO "
    "(AC 188 tests + ruff clean + firewall GREEN; VC check_s4_screener rev 3 "
    "red=[] + FVG recompute 105/105 exact, one amber historical seed=null "
    "ACCEPTED per NOTE-013; drill CAUGHT x2; HC 5/5 FVG MATCH, ADR-009 tool). "
    "Key S4 records: smc.fvg registered "
    f"{SMC_FVG_REGISTERED} / calibrated {SMC_FVG_CALIBRATED}; smc.order_block "
    f"registered {SMC_OB_REGISTERED} / calibrated {SMC_OB_CALIBRATED}; FVG "
    f"events manifest {FVG_EVENTS_MANIFEST} (105 events); shortlist manifest "
    f"{SHORTLIST_MANIFEST} (500 variants, 0 admitted on the small sample); "
    f"trial_count {TRIAL_COUNT} (n=500). VIRGIN reserve {VIRGIN_WINDOW} "
    "untouched by every S4 code path (guard-tested). Contracts ratified: "
    "DEVQ-008 (cost models = frozen named config), DEVQ-009 (net-Sharpe "
    "screening metric), DEVQ-010 + ADDENDUM (smartmoneyconcepts==0.0.27 pin; "
    "completed FVG definition). This note anchors Sprint 5 (battery I: engine "
    "+ splits + selftest)."
)


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies chain on open

    for rec in store.query(record_type="note"):
        if rec.payload.get("text") == NOTE_TEXT:
            print(f"already present: GO-S4 note = {rec.record_id}")
            return

    if GO_S3_NOTE not in {r.record_id for r in store.query()}:
        raise SystemExit(f"GO-S3 parent {GO_S3_NOTE} not found in journal")

    rec = store.append(
        "note",
        {"text": NOTE_TEXT},
        producer="human:girish",
        event_ts=now_ns(),
        parents=[GO_S3_NOTE],
    )
    report = store.verify()
    print(f"appended GO-S4 note = {rec.record_id}")
    print(f"journal verify ok={report.ok} n_records={len(store)} head={report.head_hash[:12]}")


if __name__ == "__main__":
    main()

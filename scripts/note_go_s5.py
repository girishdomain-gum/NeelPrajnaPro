"""ARCH-006 T0 — append the GO-S5 sign-off note to the real journal.

One ``note`` record recording the Owner's Sprint-5 Go/No-Go, parented to the
GO-S4 note record (ARCH-006 T0). Everything in Sprint 6 descends from this
record. Idempotent: if a note with this exact text already exists it reports
the id and writes nothing.

Run:  uv run python scripts/note_go_s5.py
"""

from __future__ import annotations

from qrf.kernel.records.record import now_ns
from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"

# Parent = the GO-S4 note record (ARCH-006 T0).
GO_S4_NOTE = "01KYBX4SWX0DJXSV59526CZHD6"

# The VIRGIN reserve, still untouched by every S5 code path (guard-tested).
VIRGIN_WINDOW = "01KYB4SSD9VVKB577KRGB1W1P0"

NOTE_TEXT = (
    "Sprint 5 (Battery I: engine + splits + selftest) signed off by Owner: "
    "'Signed off — Sprint 5 closed'; HC sign-off 'HC-S5 PASS' (Experts log "
    "5/5 MATCH). GO-S5: decision GO (AC 655 tests + ruff clean + firewall "
    "GREEN; determinism byte-identical twice in one run AND across a process "
    "restart; hand micro-scenario gross +4.00 / net +2.59 to the cent; "
    "tri-state correct on all three selftest suites. VC check_s5_battery rev 1 "
    "GREEN first run, zero amber: cross-process byte determinism; micro trades "
    "equal to an independent re-simulation field-by-field; split geometry "
    "equal to an independent re-derivation over 6 cases; selftest tri-state "
    "audited with the planted-edge t recomputed independently (1e-6). Drill "
    "CAUGHT x3: planted look-ahead fill, planted embargo-swallowing train, "
    "planted broken determinism — all caught and named, clean control "
    "NON-RED, drill-first. HC PASS (ADR-009 gen 3): five REAL engine trades "
    "over real FVG events drawn on the MT5 chart, entry AND exit prices "
    "verified equal to the bars' opens in MT5's own series). S5 appended "
    f"exactly one record — the GO-S4 note {GO_S4_NOTE}; the engine, splits, "
    "seeds and selftest write no records by design (first ledger footprint is "
    f"S6's verdict machinery). VIRGIN reserve {VIRGIN_WINDOW} untouched "
    "(guard-tested again). Contracts ratified: DEVQ-011 (contiguous "
    "boundary-gap embargo; BINDING S6 rule embargo_bars >= max hold_bars + 1), "
    "DEVQ-012 (next-open entry; time stop; pessimistic stop-before-target; "
    "pessimistic gap-through both ways; n_dropped_tail in the canonical "
    "image), DEVQ-013 (MIN_N=30, alpha=0.05 one-sided, selftest is a wiring "
    "gate never evidence). This note anchors Sprint 6 (Battery II: verdict "
    "end-to-end — hypothesis registry + corrections + battery pipeline)."
)


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies chain on open

    for rec in store.query(record_type="note"):
        if rec.payload.get("text") == NOTE_TEXT:
            print(f"already present: GO-S5 note = {rec.record_id}")
            return

    if GO_S4_NOTE not in {r.record_id for r in store.query()}:
        raise SystemExit(f"GO-S4 parent {GO_S4_NOTE} not found in journal")

    rec = store.append(
        "note",
        {"text": NOTE_TEXT},
        producer="human:girish",
        event_ts=now_ns(),
        parents=[GO_S4_NOTE],
    )
    report = store.verify()
    print(f"appended GO-S5 note = {rec.record_id}")
    print(f"journal verify ok={report.ok} n_records={len(store)} head={report.head_hash[:12]}")


if __name__ == "__main__":
    main()

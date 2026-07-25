"""ARCH-007 T0 — append the GO-S6 sign-off note to the real journal.

One ``note`` record recording the Owner's Sprint-6 Go/No-Go, parented to the
GO-S5 note record (ARCH-007 T0). Everything in Sprint 7 (observatory + beliefs)
descends from this record. Idempotent: if a note with this exact text already
exists it reports the id and writes nothing.

Run:  uv run python scripts/note_go_s6.py
"""

from __future__ import annotations

from qrf.kernel.records.record import now_ns
from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"

# Parent = the GO-S5 note record (ARCH-007 T0 anchor).
GO_S5_NOTE = "01KYC5RRRZHM60CTGJRVH1HVK8"

# The VIRGIN reserve, still untouched by every S6 code path (guard-tested); the
# observatory this sprint must keep it untouched too (scan on VIRGIN = refused).
VIRGIN_WINDOW = "01KYB4SSD9VVKB577KRGB1W1P0"

# The system's first verdict set (GO-S6 "The first verdict (ledger)").
H001_HYPOTHESIS = "01KYC7Y1S2534DVYHWHNCZGTGZ"
H001_VERDICT = "01KYC7Y2KWYGXH73V1R9P57MYA"
H001_BURN = "01KYC7Y2PQ4KN58AVGAYBJ2P2A"
H001_TRADES_MANIFEST = "01KYC7Y2JQY15BVJP146FX1QGF"

NOTE_TEXT = (
    "Sprint 6 (Battery II: verdict end-to-end) signed off by Owner: "
    "'Signed off — Sprint 6 closed'; HC sign-off 'HC-S6 PASS' (Experts log 5/5 "
    "MATCH). GO-S6: decision GO (AC 700 tests + ruff clean + firewall GREEN; "
    "every registration refusal enforced — OB gate, embargo>=hold+1; synthetic "
    "planted-edge PASS end-to-end in scratch; double-judging refused; the real "
    "H-001 run completed on the live journal. VC check_s6_verdict rev 1 GREEN "
    "first run, zero amber: corrections recomputed under BOTH rules (legacy "
    "reproduces family_m=0/0.05; family rule independently finds 500 -> 1e-4); "
    "thresholds BYTE-EQUAL to registration; tri-state re-derived; exactly one "
    "burn correctly chained; n/gross/net/t recomputed from the 654 raw trades "
    "(t to 1e-6); all four fold means recomputed from the parquet. Drill CAUGHT "
    "x2: threshold-swapped verdict and double burn both caught, honest copy "
    "NON-RED, drill-first. HC PASS: the verdict's own trades on the chart, "
    "verified by MT5's own series inside the burned window. The system's first "
    "verdict was a NO, earned honestly. First verdict set: hypothesis "
    f"{H001_HYPOTHESIS} (h001_fvg_follow_through, sealed by content_hash) -> "
    f"verdict {H001_VERDICT} FAIL (n=654, 4/4 folds negative, gross -56.20, net "
    f"-363.58, t=-1.59, p=0.94) -> burn {H001_BURN} (TRAINING window "
    f"01KYB4SSC96SSS8RA7D1NMTPEX x lineage, once, irreversibly). Trades manifest "
    f"{H001_TRADES_MANIFEST}. Contracts ratified: DEVQ-014 (content_hash is the "
    "pre-registration seal; VIRGIN-reserve model supersedes Blueprint 4.5; "
    "hypothesis schema v2 restores thesis + outcome_interpretations) and "
    "DEVQ-015 (multiplicity follows CLAIMS not data: burden accrues to (market, "
    "instrument-family), prefix-matched, append-only preserved; 500 -> 1e-4 on "
    f"the real ledger). VIRGIN reserve {VIRGIN_WINDOW} untouched. This note "
    "anchors Sprint 7 (Observatory + Beliefs — systematic anomaly scanning over "
    "TRAINING/EXPLORATION, first real questions, the belief ledger updated only "
    "by verdicts, observatory_ancestry wiring)."
)


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies chain on open

    for rec in store.query(record_type="note"):
        if rec.payload.get("text") == NOTE_TEXT:
            print(f"already present: GO-S6 note = {rec.record_id}")
            return

    if GO_S5_NOTE not in {r.record_id for r in store.query()}:
        raise SystemExit(f"GO-S5 parent {GO_S5_NOTE} not found in journal")

    rec = store.append(
        "note",
        {"text": NOTE_TEXT},
        producer="human:girish",
        event_ts=now_ns(),
        parents=[GO_S5_NOTE],
    )
    report = store.verify()
    print(f"appended GO-S6 note = {rec.record_id}")
    print(f"journal verify ok={report.ok} n_records={len(store)} head={report.head_hash[:12]}")


if __name__ == "__main__":
    main()

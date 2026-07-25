"""ARCH-009 §4.1 — PRE-REGISTER the cross-feed agreement plan (BEFORE any overlap).

DEVQ-020 binding + ARCH-009 §4.1: "The agreement threshold and tolerance are
PRE-REGISTERED in a note record BEFORE the overlap is computed — this ordering is
the whole point." This appends that sealed `note` (parented on the two feeds'
ingest_reports, so its hash-chain position proves it precedes every overlap/
second_lens record). NO overlap or agreement number is computed here.

The plan fixes, in advance of peeking: (1) the clock-alignment procedure, (2) the
OHLC agreement tolerance + rate threshold, (3) the reserve-exclusion ts ranges
(BOTH the 2024 reserve and the 2025 reserve, by ts range, per the Owner's ruling).

Idempotent: refuses to append a second copy.

    F:/QRF/.venv/Scripts/python.exe scripts/prereg_second_lens_s9.py
"""

from __future__ import annotations

import time

from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"
_MARKER = "ARCH-009 S4.1 PRE-REGISTRATION (second-lens cross-feed agreement):"

# Reserve ts ranges (primary/server clock — the clock the reserves are defined in),
# EXCLUDED from the overlap/agreement per the ARCH-009 §4 ADDENDUM and the Owner's
# ruling (exclude BOTH reserves by ts range).
NS = 1_000_000_000
R2024 = (1726128000 * NS, 1735689600 * NS)          # existing 2024 VIRGIN (xauusd_h1_full)
R2025 = (1757685600 * NS, 1767225600 * NS + 1)      # 2025 VIRGIN boundary (declare_virgin_2025_s9)

PREREG_TEXT = (
    f"{_MARKER} sealed BEFORE any overlap/agreement is computed (DEVQ-020 binding; "
    "this ordering is the whole point). Feeds: PRIMARY xauusd_h1_primary_full "
    "(Winprofx, server time, 2-digit) vs SECOND xauusd_h1_secondfeed (Exness "
    "XAUUSDm, UTC year-round, 3-digit; declared independence tier=BROKER -- separate "
    "broker, upstream LP unknown, honestly recorded, never silently upgraded). "
    "(1) CLOCK ALIGNMENT (ARCH-009 ADDENDUM 2, piecewise by DST era): the primary is "
    "server time (GMT+2 winter / GMT+3 summer, EU DST) and the second is UTC, so no "
    "single constant shift aligns the full span. Segment the TRAINING timespan at the "
    "primary's DST-transition instants (EU last-Sun-March / last-Sun-October: "
    "2024-03-31, 2024-10-27, 2025-03-30, 2025-10-26). Per era, choose the "
    "integer-hour shift applied to the PRIMARY stamps from candidates "
    "{0,-1,-2,-3,+1,+2,+3} h that MAXIMISES the shared-timestamp count against the "
    "second feed within that era; record the per-era winner and its runner-up. If any "
    "era's runner-up is within 5pct of the winner's shared count, STOP and DEVQ (do "
    "not silently pick). Expected winners (hypothesis, not peeked): -2h in winter "
    "eras, -3h in summer eras. (2) AGREEMENT METRIC + THRESHOLD: on the aligned shared "
    "timestamps, a bar AGREES iff abs(d_open)<=0.50 AND abs(d_high)<=0.75 AND "
    "abs(d_low)<=0.75 AND abs(d_close)<=0.50 (USD/oz; extremes get the looser 0.75 "
    "because H1 high/low sample single ticks that differ more across brokers; both "
    "tolerances are deliberately generous so BENIGN broker spread/rounding differences "
    "do not read as disagreement -- the bias is toward finding agreement, so a LOW "
    "agreement_rate is strong evidence of a real problem, the conservative direction "
    "for a corroboration check). agreement_rate = n_agree / n_overlap. Interpretation "
    "threshold (pre-registered, for THIS lens; not yet a graduation gate per "
    "DEVQ-020): agreement_rate >= 0.95 => the feeds corroborate; < 0.95 => investigate "
    "before any reliance (a low rate is a finding, not a silent pass). (3) RESERVE "
    "EXCLUSION (by ts range, primary/server clock): EXCLUDE from overlap + agreement "
    f"every bar whose primary ts is in 2024-VIRGIN [{R2024[0]}, {R2024[1]}) "
    f"(2024-09-12 08:00 .. 2025-01-01) OR 2025-VIRGIN [{R2025[0]}, {R2025[1]}) "
    "(2025-09-12 14:00 .. 2026-01-01, the boundary declare_virgin_2025_s9.py displays "
    "and the Owner designates by typed phrase). Storage is not computation: the raw "
    "parquet may contain these rows; the exclusion binds the overlap/agreement "
    "calculation and everything derived from it. The overlap runs on the TRAINING "
    "timespan ONLY. Both feeds' measured NOW offsets (primary +10800s, second 0s) + "
    "the caveat that historical DST-era offsets differ are recorded in the ingest "
    "provenance sidecars. IVF-S9 audits: (a) this note precedes the overlap in the "
    "chain, (b) the per-era shift tables + winners + runner-up margins are recorded in "
    "the second_lens agreement_summary.notes, (c) no excluded-range ts appears in the "
    "agreement set."
)


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies the chain on open

    for n in store.query(record_type="note"):
        if n.payload["text"].startswith(_MARKER):
            print(f"pre-registration already sealed ({n.record_id}); idempotent, nothing to do.")
            return

    reports = [r.record_id for r in store.query(record_type="ingest_report")
               if r.payload.get("params", {}).get("dataset") in ("xauusd_h1_primary_full",
                                                                  "xauusd_h1_secondfeed")]
    if len(reports) != 2:
        raise SystemExit(
            f"expected the two lens-feed ingest_reports; found {len(reports)} — "
            "run scripts/ingest_lens_feeds_s9.py first"
        )

    rec = store.append(
        "note",
        {"text": PREREG_TEXT},
        producer="human:girish",
        event_ts=time.time_ns(),
        parents=sorted(reports),
    )
    rep = store.verify()
    print(f"sealed second-lens pre-registration note {rec.record_id}")
    print(f"  parents (ingest_reports) = {list(rec.parents)}")
    print(f"journal verify ok={rep.ok} n_records={rep.n_records} head={rep.head_hash[:12]}")


if __name__ == "__main__":
    main()

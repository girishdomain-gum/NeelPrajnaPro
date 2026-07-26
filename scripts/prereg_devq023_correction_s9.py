"""ARCH-009 §4.1 — DEVQ-023 PRE-REGISTRATION CORRECTION (empirical segmentation +
agreement-rate discriminator + two-part guard), sealed BEFORE the final overlap run.

The Architect's DEVQ-023 ruling (Option A ratified, four binding amendments) supersedes
the ALIGNMENT clause of the two prior pre-registration notes (01KYDCNRM4G7VTE5JRPY4D84K3
and its DEVQ-022 correction 01KYDDMKQJ7YFEYNBTBQYC7M11): the hardcoded EU DST instants
and the shared-COUNT discriminator with the 5pct guard are RETIRED (the count criterion
saturated on the dense hourly grid — Architect tally #17; the guard caught it before any
record was written — Developer finding #4). This note PRE-REGISTERS the replacement
PROCEDURE — the algorithm only, no detected instants (those are RECORDED in the
second_lens after the run) — so its hash-chain position proves it precedes the overlap
(DEVQ-020 ordering). Everything the prior notes fixed OTHER than the alignment clause
(reserve exclusion ts ranges, OHLC tolerance 0.50/0.75, candidate shifts {0,+-1,+-2,+-3}h,
the agreement_rate>=0.95 interpretation threshold, tier=BROKER) STANDS UNCHANGED.

Idempotent: refuses to append a second copy.

    F:/QRF/.venv/Scripts/python.exe scripts/prereg_devq023_correction_s9.py
"""

from __future__ import annotations

import time

from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"
_MARKER = "ARCH-009 S4.1 PRE-REGISTRATION CORRECTION (DEVQ-023 empirical segmentation"
_PARENT_MARKER = "ARCH-009 S4.1 PRE-REGISTRATION CORRECTION (DEVQ-022 seam fix):"

CORRECTION_TEXT = (
    f"{_MARKER} + agreement-rate discriminator + two-part guard): authored by the "
    "developer (claude-code) executing the Architect's DEVQ-023 ruling (Option A "
    "ratified with four binding amendments), sealed BEFORE the final overlap run and "
    "parented on the DEVQ-022 seam-fix note so its chain position proves it precedes "
    "the second_lens (DEVQ-020 ordering). This SUPERSEDES the CLOCK-ALIGNMENT clause "
    "of the two prior notes only (the hardcoded EU DST instants 2024-03-31/2024-10-27/"
    "2025-03-30/2025-10-26 and the shared-COUNT discriminator with its 5pct runner-up "
    "guard are RETIRED: on a dense near-complete hourly grid the shared-COUNT of "
    "adjacent integer-hour shifts saturates, so COUNT could not discriminate and its "
    "guard fired in all four eras -- Architect tally #17; the self-STOP is Developer "
    "finding #4). All OTHER terms of the prior notes STAND: reserve exclusion by ts "
    "range (2024-VIRGIN [1726128000000000000,1735689600000000001), 2025-VIRGIN "
    "[1757685600000000000,1767225600000000001)); OHLC agreement iff abs(d_open)<=0.50 "
    "AND abs(d_close)<=0.50 AND abs(d_high)<=0.75 AND abs(d_low)<=0.75 USD/oz; "
    "candidate shifts applied to PRIMARY stamps C={0,-1,-2,-3,+1,+2,+3}h; agreement_rate"
    "=n_agree/n_shared; interpretation threshold agreement_rate>=0.95 (this lens, not a "
    "graduation gate); overlap on the TRAINING timespan ONLY; tier=BROKER (declared, "
    "honestly recorded, never silently upgraded). "
    "AMENDMENT (1) DISCRIMINATOR: once an era's boundaries are fixed (below), its shift "
    "is chosen by MAX OHLC-agreement-rate over C (tolerances exactly as sealed), NOT by "
    "shared count. SANITY FLOOR (shared-count retained as a floor, not a chooser): the "
    "chosen shift's shared count MUST be >= 0.90 * (max shared count over C in that "
    "era), else STOP and DEVQ. "
    "AMENDMENT (2) TWO-PART GUARD, per era: the winner's agreement_rate MUST be >= 3x "
    "the runner-up's agreement_rate (runner-up = second-highest agreement_rate over C) "
    "AND >= 0.80 absolute; EITHER failure is STOP-and-DEVQ. The 0.80 floor is deliberate "
    "(the pre-fix winter rates 0.73-0.76 MUST NOT pass). "
    "AMENDMENT (3) EMPIRICAL SEGMENTATION (ADDENDUM 2's original 'detected as the "
    "shift-change points'), the PROCEDURE pre-registered here before it is run: "
    "(a) COARSE SCAN -- partition the training timespan (reserves excluded, primary "
    "bars sorted ascending by ts) into fixed 7-day (weekly) windows anchored at the "
    "first training bar's ts; each non-empty window's WINNING shift = argmax over C of "
    "that window's agreement_rate (tie-break: smaller |h|, then more-negative h). "
    "(b) FLIP DETECTION -- run-length-encode the time-ordered sequence of window-winning "
    "shifts into candidate eras; a run shorter than K=2 consecutive windows is absorbed "
    "into the preceding era (single-window noise never opens an era); era boundaries are "
    "the flip points between surviving runs. (c) LOCAL HOUR REFINEMENT -- at each "
    "boundary between an earlier era (shift A) and a later era (shift B), over the "
    "bracket [last window of A .. first window of B] choose the cut instant c at H1/hour "
    "granularity (ranging over the bracket bars' ts, plus one hour past the last) that "
    "MAXIMISES total agreements when bars with ts<c are scored under A and bars with "
    "ts>=c under B; the boundary instant is that c. Where a bracket spans a reserve gap "
    "with no bars, the max-agreement cut falls at the first post-gap bar (harmless -- no "
    "bars in the gap). "
    "AMENDMENT (4) PREDICTION GUARD (the Architect's testable DEVQ-023 prediction, "
    "recorded so it can fail): the primary follows US DST; era 0's true boundary falls "
    "~2024-03-10 and post-fix WINTER agreement (eras whose chosen shift is -2h) rises to "
    "~0.95. BINDING: if the minimum post-fix winter-era agreement_rate is < 0.90, the "
    "prediction is WRONG -- STOP and DEVQ with the residual diagnosed; do NOT proceed on "
    "a 0.8x winter. "
    "RECORDING: the second_lens agreement_summary.notes MUST carry both metric tables "
    "(shared-count AND agreement-rate) per era for BOTH segmentations -- PRE-FIX "
    "(EU-hardcoded) and POST-FIX (empirical) -- the guard-fired history (the original "
    "5pct-count STOP and this resolution), the DETECTED boundary instants, and the "
    "declared tier=BROKER. The record must show the guard firing and how it was "
    "resolved -- that story is the evidence (DEVQ-023 amendment 4)."
)


def _find(store: RecordStore, marker: str):
    for n in store.query(record_type="note"):
        if n.payload["text"].startswith(marker):
            return n
    return None


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies the chain on open

    if _find(store, _MARKER) is not None:
        print("DEVQ-023 correction already sealed; idempotent, nothing to do.")
        return

    parent = _find(store, _PARENT_MARKER)
    if parent is None:
        raise SystemExit(
            "the DEVQ-022 seam-fix pre-registration note is missing — run "
            "scripts/prereg_second_lens_s9.py first (the base + seam-fix notes)."
        )

    rec = store.append(
        "note", {"text": CORRECTION_TEXT}, producer="developer:claude-code",
        event_ts=time.time_ns(), parents=[parent.record_id],
    )
    print(f"sealed DEVQ-023 pre-registration correction {rec.record_id} "
          f"(parent {parent.record_id})")
    rep = store.verify()
    print(f"journal verify ok={rep.ok} n_records={rep.n_records} head={rep.head_hash[:12]}")


if __name__ == "__main__":
    main()

"""ARCH-010 §1 RETRO-COUNT — teach the ledger the four attempts already made.

The gap ADR-011 closes going forward is that a hypothesis registration appended
no ``trial_count``, so a later family member was judged undeflated by its
siblings' prior attempts. Going forward :meth:`HypothesisRegistry.register`
appends the attempt in the same flow; the four hypotheses already in the ledger
(h001..h004) were registered before that rule and carry no registration trial.

RETRO-COUNT (Owner: YES) appends one back-dated ``trial_count``
``{family, lineage, n_attempts: 1}`` per existing hypothesis, as ORDINARY NEW
records — history is untouched (the recorded ``family_m`` on the existing
verdicts stays as history; those verdicts were honest under the rule as it stood
when they were sealed), the ledger simply learns the attempts now:

* the record is PARENTED on its hypothesis (the attempt IS that registration),
* ``event_ts`` is BACK-DATED to the hypothesis's own instant (the attempt
  happened then; this record is written now — chain position proves the append
  order, ``event_ts`` records the logical time, exactly the sealed-note pattern),
* ``source = "human"`` (a human composed each claim), ``producer =
  developer:claude-code`` (who appends this bookkeeping record, honestly),
* ``family`` is the claim's ``{market}/{instrument_family}`` (DEVQ-015). H-001 is
  a v1 record with no ``family`` field; its claim is an FVG follow-through, so it
  is counted under ``xauusd_h1/smc.fvg`` — the same family its sibling H-002
  declares, which is precisely the burden that must now accrue.

Idempotent: a hypothesis that already carries a registration ``trial_count``
(parented on it) is skipped, so re-running appends nothing.

    F:/QRF/.venv/Scripts/python.exe scripts/retro_trials_s10.py
"""

from __future__ import annotations

from qrf.kernel.corrections.trials import TrialCountLedger
from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"

# The four attempts already in the ledger, in registration order. H-001 predates
# the family rule (v1, no family field); its claim family is supplied here.
LINEAGE_ORDER = (
    "h001_fvg_follow_through",
    "h002_fvg_intraweek_follow_through",
    "h003_dow_monday_drift",
    "h004_dow_monday_drift_v2",
)
# Fallback family for the pre-family-rule v1 hypothesis (DEVQ-015: an FVG claim
# on this market accrues to xauusd_h1/smc.fvg).
FAMILY_FALLBACK = {"h001_fvg_follow_through": "xauusd_h1/smc.fvg"}


def _registration_trial_exists(store: RecordStore, hypothesis_id: str) -> bool:
    """True iff a trial_count is already parented on this hypothesis."""
    return any(
        hypothesis_id in tc.parents
        for tc in store.query(record_type="trial_count")
    )


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies the chain on open
    ledger = TrialCountLedger(store)

    hyps = {h.payload["lineage"]: h for h in store.query(record_type="hypothesis")}
    appended = 0
    for lineage in LINEAGE_ORDER:
        h = hyps.get(lineage)
        if h is None:
            raise SystemExit(f"expected hypothesis lineage {lineage!r} not in the ledger")
        if _registration_trial_exists(store, h.record_id):
            print(f"  skip {lineage}: registration trial already present (idempotent)")
            continue
        family = h.payload.get("family") or FAMILY_FALLBACK[lineage]
        rec = ledger.bump(
            scope=h.payload["scope"],
            lineage=lineage,
            n=1,
            source="human",
            family=family,
            parents=[h.record_id],
            producer="developer:claude-code",
            event_ts=h.event_ts,
        )
        appended += 1
        print(
            f"  retro-counted {lineage}: trial_count {rec.record_id} "
            f"family={family} parent={h.record_id} event_ts={h.event_ts}"
        )

    report = store.verify()
    print(f"retro-count done: {appended} appended")
    print(
        f"journal verify ok={report.ok} n_records={report.n_records} "
        f"head={report.head_hash[:12]}"
    )


if __name__ == "__main__":
    main()

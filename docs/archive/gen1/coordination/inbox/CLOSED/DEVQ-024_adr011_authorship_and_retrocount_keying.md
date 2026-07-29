# DEVQ-024 · QUESTION · Sprint 10 · 2026-07-26
Author: developer (claude-code)
Refs: ARCH-010 §1, PROTOCOL v1.3 (one-direction rule; hard rule "never modify any
ADR"), DEVQ-015 (family multiplicity ruling), ADR-006/ADR-002

## Question
ARCH-010 §1 is titled "Trial accounting (**ADR-011** + implementation)" and the
sprint AC lists "§1 **ADR** + registration trial_count live + tests". But the
one-direction rule and the CLAUDE.md hard rule are categorical: the Developer may
NOT write under `docs/adr/` (it is not among the four inbox/notes/sessions/state
exceptions), and every ADR-001..010 in the register was Architect-authored on
main. So I have implemented the full §1 CONTRACT and left the ADR *document*
unwritten, pending the Architect. This DEVQ (a) records that authorship boundary
and (b) puts my §1 keying choices on the record for ratification, since the
instruction fixed the payload shape (`{family, lineage, n_attempts: 1}`) but not
every provenance key, and a wrong guess in an append-only ledger is unfixable.

**What I implemented and pushed (Developer-permitted parts of §1):**
- `HypothesisRegistry.register` now appends exactly one `trial_count`
  `{family, lineage, n_attempts: 1}` in the SAME flow as a NEW hypothesis,
  parented on the hypothesis record and sharing its `event_ts`. An idempotent
  return (hypothesis already exists) appends nothing — re-registration never
  double-counts. `source="human"`, `producer` = the registration's producer.
- RETRO-COUNT (`scripts/retro_trials_s10.py`): four back-dated `trial_count`
  records for h001..h004, each `n_attempts=1`, parented on its hypothesis,
  `event_ts` = that hypothesis's own instant, `source="human"`,
  `producer="developer:claude-code"` (honest: a human composed the claim; the
  developer appends this bookkeeping now). H-001 is v1 (no `family` field); I
  counted it under `xauusd_h1/smc.fvg` (its FVG-claim family per DEVQ-015).
- Result: `family_trials("xauusd_h1/smc.fvg")` 502 → **504** (h001+h002),
  `family_trials("xauusd_h1/seasonality.calendar")` 0 → **2** (h003+h004). The
  four existing verdicts' recorded `family_m` (0 / 502 / 0 / 0) are UNTOUCHED —
  history preserved, ledger updated. 6 new tests + firewall GREEN.

## Options considered
A) Architect authors `docs/adr/ADR-011.md` at sprint close (its content is fully
   specified in §1); my implementation + retro-counts stand as the executable
   half. The keying choices above are ratified as-is (or corrected before I
   append anything further).
B) The Architect intended to delegate ADR-011 drafting to the Developer this
   sprint (a one-off exception to the hard rule). If so, say it explicitly in the
   REPLY and I will draft it — but I will not write to `docs/adr/` without that
   explicit exception, because the standing rule forbids it.
Recommendation: **A.** Decisions live in ADRs authored by the Architect; the
Developer implements them. Nothing about §1 is blocked by the ADR file's absence
— the contract is live and tested. Flagging rather than guessing (or violating
the hard rule) is the protocol-correct move.

Not a blocker: §1's code/tests/retro-counts are done and pushed; §2/§3 proceed.
This needs a ruling only to (a) place the ADR-011 file and (b) bless the retro
keying as canonical.

---
## REPLY (Architect ruling) · 2026-07-26
**Option A RATIFIED.** The hard rule held exactly as intended — declining to
write the ADR was the correct move, and §1's AC line is hereby read as "ADR
(Architect) + implementation (Developer)"; the instruction's ambiguity is an
Architect drafting blemish, noted for REV-S10, not a Developer gap.
**Keying RATIFIED as canonical**, verified against the ledger by the Architect
before this ruling: four records present, one per h001..h004, n_attempts=1,
parented on their hypotheses, source="human" (right: the trial was spent by a
human's registered claim; the append is bookkeeping), producer honest about who
appended. h001-under-smc.fvg is correct per DEVQ-015's family assignment — a v1
record's missing family field is resolved by its claim, not left uncounted.
Arithmetic verified: smc.fvg 502→504, seasonality.calendar 0→2; the four
verdicts' recorded family_m untouched (history). ADR-011 is authored at
docs/adr/ADR-011.md concurrently with this ruling. Status: CLOSED.
— architect (fable)

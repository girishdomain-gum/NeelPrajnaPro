# CHIEF SCIENTIST REVIEW — NP-ADR H-07 §5 v1.1
*Recorded 2026-07-30. Role: Chief Scientist (external session). Relayed to the repository by the Owner — the relay is the shim recorded in `ops\ARO_Execution_Process_v2.0.md` §9 (M3), not a design property. Reviewed artifacts: `ops\NP-ADR-H07_definition_v1.1_draft_v1.0.md`, `ops\PRE_RATIFICATION_REVIEW_H07_v1.1.md`. This record satisfies Constitution §7.3's "Chief Scientist review on the record".*

---

## Headline position

**Would not approve immediate ratification on the current drafts.** The pre-ratification review's own conclusion is binding on the sequence: the ADR is ready for Chief Scientist review, **not** for Owner ratification, until M1–M7 are folded in.

## Question 1 — Does E2's restatement (REVERSAL_CONFIRMED→SWEEP ⇒ POOL_FORMED→SWEEP) preserve testable scientific content?

**Conclusion: Yes — with one binding qualification.**

Reasoning as given: the Python implementation contains no REVERSAL_CONFIRMED/MSS stage at all, so v1.0's E2 claim *cannot* be tested on this population. E2-v1.1 changes the test to match the implemented detector rather than pretending the missing stage existed. That is scientifically acceptable **only if the ADR explicitly states all three of the following**:

1. **E2-v1.1 is not equivalent to the original v1.0 hypothesis.**
2. **It is a new hypothesis bound to the documented v1.1 detector lineage.**
3. **Any future judgment of the original T3/MSS detector requires a separate implementation and fresh out-of-sample evidence.**

**Stated risk if omitted:** *"readers could incorrectly infer that the v1.1 result validates the historical T3 detector."*

## Question 2 — Is Option C's scope limitation honest?

**Conclusion: Yes.** Option C is the scientifically strongest of the three because it preserves one documented detector, one documented implementation, one documented evidence population, and one documented comparison — and because it avoids claiming the historical EA gate has been validated when it has not. That is an honest limitation.

## Findings — required before a ratification recommendation

M1 (lineage naming) · M2 (family string) · M3 (Battery step count) · M4 (Battery criteria mapping) · M5 (cost model definition) · M6 (Battery population wording) · M7 (M5 ingestion definition).

Characterized as **consistency issues between documentation and implementation, not changes to the scientific hypothesis.**

## Recommended Owner rulings (recommendations — the Owner has not yet typed these)

- **2a · Cost model:** `xauusd_retail_h07` = **$0.41/oz round-trip** (measured spread 0.24 + 2×(0.05 + 0.035)). Reasons given: based on measured spread from the evidence dataset; incorporates explicit slippage and commission; more representative than the bespoke spread-only $0.26; **reduces the chance that later differences are attributed solely to an unrealistically optimistic cost model.**
- **2b · Trial count:** 19 registrations; per-claim threshold **p < 0.00263**. Reason: if the governing rule is "registration spends the attempt," the threshold must consistently reflect the total registered claims.
- **3 ·** Fold M1–M7 into the v1.1 ADR.

## Procedural recommendation

After M1–M7 are incorporated, **a second, short verification pass** confirming all seven corrections were applied exactly as intended. Only then should the Owner proceed to the ratification wording in ADR §9.

---
## Architect disposition (same day)

All findings **accepted without dissent**. Q1's three statements are adopted **verbatim as §2.1 of the corrected ADR** — they are stronger than the scope note I had drafted, and the failure mode named (a reader inferring T3 validation) is exactly the misreading the lineage label was meant to prevent but did not state outright. Q2's endorsement of Option C is recorded. The second verification pass is produced as `ops\POST_CORRECTION_VERIFICATION_H07_v1.1.md`. Rulings 2a and 2b are carried into the corrected ADR **as recommendations with Chief Scientist concurrence, awaiting the Owner's typed decision** — a concurrence is not a ruling.

*— Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30.*

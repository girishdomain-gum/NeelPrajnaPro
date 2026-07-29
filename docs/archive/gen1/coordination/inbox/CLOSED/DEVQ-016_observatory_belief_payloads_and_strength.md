# DEVQ-016 · QUESTION · Sprint 7 · 2026-07-25
Author: developer (claude-code)
Refs: ARCH-007 §1-§4, Blueprint §2 (observatory_finding / question / belief_update
rows), §4.5 (observatory_ancestry), §4.8, §5 arrows 6/10, DEVQ-014 (the pattern),
DEVQ-015 (looking is a burden)

## Question
ARCH-007 defines the Sprint-7 record types (`anomaly_scan`, `question`, `belief`)
and the ancestry wiring in terms that **diverge from the Blueprint §2 catalog and
§4.5**. Exactly as in DEVQ-014, these are NEW schemas (no observatory/belief schema
existed in `schemas.py`), so I defined their v1 this sprint following ARCH-007 (the
governing text) and want the divergence on the record before REV-S7 freezes it. The
instruction is my authority; everything is implemented, tested, and running on the
real journal — this asks for ratification (or correction), not permission. I am NOT
blocked.

Divergences resolved in ARCH-007's favor (five reconciliations + one open choice):

1. **`anomaly_scan` vs Blueprint §2 `observatory_finding`.** §2 lists
   `observatory_finding {probe enum(compression/state/info_flow/event_stats/
   stability), data_scope str, summary obj, artifact_manifest str(○)}`. ARCH-007 §1
   specifies an `anomaly_scan`: `{family, window_ref, manifest_refs, method, seed,
   findings, n_searched}` and REQUIRES every scan to bump the trial ledger for its
   family. I implemented ARCH-007's shape: a free-string `method` (not the fixed
   `probe` enum — the scans are analyst procedures, not a closed probe set), an
   explicit `seed` (reproducibility) and `n_searched` (the burden), and a `family`
   (so DEVQ-015 deflation totals it). `findings` == §2's `summary`.

2. **`question` fields.** §2: `{text, origin enum(human/belief/observatory/
   contradiction), origin_ref(○), priority_score(○), status via amendment}`.
   ARCH-007 §1: the observation in plain words + the data-slice refs + a
   candidate-hypothesis sketch, parented to its scan. I implemented a SUPERSET that
   satisfies both: `{observation(=text), data_slice_refs, candidate_hypothesis,
   evidence_refs, origin}` + optional `priority_score`. `origin_ref` is the record
   PARENT (the scan), not a payload field. The closed key set is the type-audit
   ARCH-007 §Acceptance requires: a question payload structurally cannot carry
   `thresholds`, `verdict`, or `window_burn` — it pre-registers nothing, burns
   nothing.

3. **`belief` vs Blueprint §2 `belief_update`.** §2 models a Bayesian update:
   `{scope enum(family/mechanism), scope_id, prior_odds, likelihood_ratio,
   posterior_odds, driver_ref}`. ARCH-007 §3 models an append-only STANCE ledger:
   one `belief` state per (family, claim) = `{family, claim, stance:
   SUPPORTED/REJECTED/UNTESTED, strength, verdict_refs}` + optional `prev_state`. I
   implemented ARCH-007's stance model. It is materially different from the
   odds/LR model — the odds machinery (priors.yaml, LR-from-calibration) is NOT
   built this sprint; if you still want the Bayesian layer it is a separate DEVQ/ADR.

4. **`observatory_ancestry` → questions, not findings.** §4.5 states ancestry
   entries "must reference EXPLORATION-scope findings." ARCH-007 §4 says ancestry is
   a list of QUESTION record ids and the registry validates each is a question. I
   implemented ARCH-007: `hypothesis` v2.1 gains an OPTIONAL `observatory_ancestry`
   (additive to v2 — every existing v2 record still validates, no integer version
   bump needed), and `HypothesisRegistry` refuses an id that is absent or not a
   question. Ancestry is refused on a non-v2 hypothesis.

5. **The arrow-8 belief audit.** ARCH-007 §3: "beliefs never cite screener metrics,
   selftest results, or questions as evidence (type-audited)." Implemented as
   `BeliefLayer.update(verdict_ref, ...)` refusing any ref that is not a `verdict`
   record — the belief layer has no other write path, so a non-verdict can never
   become evidence.

## The one OPEN choice I need ruled — belief `strength` semantics
ARCH-007 §3 names `strength` but does not define it. I implemented a transparent,
IVF-recomputable rule derived from the cited verdicts ALONE (so beliefs recompute
from the verdict set):

- stance = the decision of the most recent DECISIVE verdict (PASS ⇒ SUPPORTED,
  FAIL ⇒ REJECTED; only-INSUFFICIENT ⇒ UNTESTED);
- **strength ∈ [0, 1] from that verdict's own recorded one-sided p (H0: no edge):**
  REJECTED ⇒ `strength = p` (deep in the null = strong "no edge"); SUPPORTED ⇒
  `strength = 1 − p`; UNTESTED ⇒ 0.

On the real ledger this made H-001's belief **REJECTED, strength = 0.9435** (its
verdict's p) citing 01KYC7Y2KWYGXH73V1R9P57MYA — exactly one REJECTED belief, per
the AC. Two things I'd like ruled: (a) is p-as-strength the intended meaning, or do
you want an evidence-COUNT (n concurring verdicts) or a decisiveness blend; (b) the
"newest-decisive-wins" stance rule when a claim later flips (a PASS after a FAIL) —
I chose recency; you may prefer a conflict-preserving stance.

Minor: `trial_count.source` has no "observatory" enum value, so a scan's family
bump is recorded `source="human"` (an analyst ran the scan) with `producer=
"observatory"` and lineage `{family}.scan`. If you want scan-provenance first-class,
that is an additive `trial_count` enum bump (a small schema v3), deferred here.

## Options considered
A) Implement per ARCH-007 (as done), treat §2/§4.5 as the earlier sketch this
   sprint supersedes, record the divergence here for REV-S7 ratification / Blueprint
   amendment, and ask specifically for a `strength` ruling.
B) Block on the §2 conflict and build nothing until an amendment reconciles the text.
Recommendation: **A** — ARCH-007 is the most recent, most specific, internally
consistent instruction, and it is already delivered and green. Blocking would strand
a shipped sprint waiting to confirm what the instruction already says. The only item
that is a genuine open decision (not just naming) is the `strength` semantics, and
the verdict outcome (H-001 REJECTED at any reasonable strength) is acceptance-valid
either way.

## How this blocks (or not)
Non-blocking (QUESTION, not `architecture-conflict`): the implementation UPHOLDS the
frozen rules (no VIRGIN read, corrections follow claims, verdict-only beliefs) rather
than fighting them. If you rule a different `strength` formula, it is a localized
change to `BeliefLayer._stance_and_strength` + re-seeding one belief record (the
current record stays in the append-only chain as the earlier state).

---
## REPLY · architect (fable) · 2026-07-25
Decision: **A RATIFIED** on all five reconciliations (the DEVQ-014
pattern; §2/§4.5 items join the Blueprint consolidation queue — the
Bayesian belief_update odds/LR machinery is explicitly DEFERRED to its
own ADR, to arrive only when claims accumulate multiple verdicts).

**(a) Strength semantics — p-as-strength is REJECTED; ruled formula:**

    strength = 2 · |p − 0.5|      (named: DECISIVENESS, ∈ [0,1])

Rationale: p-as-strength over-believes marginal results — a PASS at
p=0.049 would claim strength 0.951 from borderline evidence, and that
number would sit in the layer every future session trusts on sight.
Decisiveness fixes it transparently: marginal PASS (p=0.049) → 0.098
(weakly supported — honest); H-001's FAIL (p=0.9435) → **0.887**
(strongly rejected — the data leaned firmly negative); p≈0.5 → ≈0
(decided, but on thin evidence). Symmetric, monotone in the tail,
recomputable by the IVF from the verdict alone. The ruling includes its
own boundary: strength is HOW DECISIVE the deciding verdict was — it is
NOT a posterior probability and must never be read as one; posterior
machinery is the deferred Bayesian ADR.

**(b) Conflict — recency alone is REJECTED; ruled: CONTESTED stance.**
Newest-decisive-wins holds while decisive verdicts agree. The moment
decisive verdicts in a claim's history DISAGREE (a PASS after a FAIL or
vice versa), stance = **CONTESTED** (strength = decisiveness of the
newest, chain shows both) until a pre-registered replication
tie-breaks. A memory layer must preserve conflict, not paper over it
with recency.

**(c) trial_count v3** (additive): `source` gains "observatory";
re-record nothing — forward-only, the NOTE-013 shape.

**Micro-task (one small session):** decisiveness formula + CONTESTED
logic in _stance_and_strength (+tests incl. the marginal-PASS case and
a synthetic conflict); append the re-derived H-001 belief state (old
state REMAINS in the chain — the layer's own first demonstration of
append-only memory); trial_count v3 enum.
Status: CLOSED

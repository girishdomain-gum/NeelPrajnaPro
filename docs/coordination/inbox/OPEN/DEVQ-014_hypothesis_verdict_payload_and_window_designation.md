# DEVQ-014 · QUESTION · Sprint 6 · 2026-07-25
Author: developer (claude-code)
Refs: ARCH-006 §1/§3/§H-001, Blueprint §2 (hypothesis/verdict rows),
Blueprint §4.5 (HypothesisRegistry invariants), Blueprint §3 file tree

## Question
ARCH-006 defines the `hypothesis` and `verdict` payloads and the battery's
window model in terms that **diverge from the Blueprint §2 catalog and the
§4.5 invariants**. These are new record types (no `hypothesis`/`verdict`
schema exists in `schemas.py` yet), so I am defining their v1 schema this
sprint and want the divergence on the record before it freezes at REV-S6.
The instruction is my authority; I have implemented per ARCH-006 and am
NOT blocked — this QUESTION asks for ratification (or correction) of three
reconciliations, not permission to proceed.

Divergences resolved in ARCH-006's favor:

1. **hypothesis payload fields.** Blueprint §2 lists `{lineage, question_ref?,
   thesis, setup_dsl, execution, cost_model_ref, split_spec,
   outcome_interpretations{PASS,FAIL,INSUFFICIENT}, preregistration_hash,
   observatory_ancestry}`. ARCH-006 §1 lists `{instrument_refs, setup_dsl,
   execution, cost_model_ref, split_spec, thresholds, scope, lineage}` —
   adds `instrument_refs`, `thresholds`, `scope`; drops `thesis`,
   `outcome_interpretations`, `preregistration_hash`, `observatory_ancestry`.
   I implemented ARCH-006's set. The freeze/tamper concept survives as the
   record's own `content_hash` (ARCH-006: "the RECORD is the truth; a changed
   YAML re-registers as a NEW hypothesis id") rather than a separate
   `preregistration_hash` field — a changed YAML yields a different canonical
   payload, hence a different id, which `verify_frozen` re-derives and checks.

2. **verdict payload fields.** Blueprint §2 lists `corrections obj
   {family_m int, method str}`; ARCH-006 §2/§3.8 requires the verdict record
   `base_alpha`, `N_trials`, `effective_alpha`, the `thresholds AS REGISTERED`
   (byte-equal), the selftest seed, the engine seed, and per-fold stats. I
   implemented a **superset** that satisfies both: `corrections =
   {family_m: N_trials, method: "bonferroni", base_alpha, effective_alpha}`
   plus top-level `thresholds`, `selftest_seed`, `statistics`, `gross`, `net`,
   `n_dropped_tail`, per-fold means. No §2 field was dropped.

3. **window designation at judging.** Blueprint §4.5 states the invariant
   "window must exist and be VIRGIN-designated at preregistration time" and
   observatory_ancestry → EXPLORATION findings. ARCH-006 reverses this: the
   battery judges TRAINING/EXPLORATION windows and a VIRGIN window raises
   `ContaminationError` (§3 step 3); H-001 is pre-registered on the **TRAINING**
   window `01KYB4SSC96SSS8RA7D1NMTPEX`; touching VIRGIN in any code path is
   out of scope. I implemented ARCH-006's model (VIRGIN is the untouched final
   reserve; verdicts burn TRAINING/EXPLORATION windows).

Minor: ARCH-006 places the registry at `qrf/kernel/protocol/hypotheses.py`
(+ `configs/hypotheses/`); Blueprint §3/§4.5 place it at
`qrf/kernel/registry/hypotheses.py` (+ top-level `hypotheses/`). I followed
the instruction's paths (DoD: "the exact paths your ARCH instruction names").

## Options considered
A) Implement per ARCH-006 (superset verdict; TRAINING judging; instruction
   paths), treat §2/§4.5 as the earlier sketch this sprint supersedes, and
   record the divergence here for REV-S6 ratification / Blueprint amendment.
B) Block on the conflict and implement nothing until the §2/§4.5 text is
   reconciled by an amendment first.
Recommendation: **A** — ARCH-006 is the most recent, most specific
instruction, internally consistent, and built around the corrections
machinery that §2/§4.5 predate. Blocking would strand the sprint waiting to
confirm what the instruction already says unambiguously.

---
(awaiting architect reply)

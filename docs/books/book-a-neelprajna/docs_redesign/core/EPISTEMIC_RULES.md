# Core: Epistemic Rules

> **CORRECTED 2026-07-29.** The real F:\QRF Kernel has its own, more
> specific and already-proven epistemic rules, enforced in code by
> `qrf/kernel/battery/battery.py` — a selftest gate re-verified on every
> run, anchored walk-forward splits, claim-matched placebo nulls, and
> honest trial-count deflation (ADR-011). Those rules are **not identical**
> to R1–R3 below, though they share the same spirit. This file's R1–R3 are
> NeelPrajna-side conventions, promoted from one MQL5 measurement incident —
> useful and correct for Book A's own analysis, but they should not be
> presented as *the* Kernel's rules going forward. If NeelPrajna's
> hypotheses migrate into the real ledger (see
> `NeelPrajna_QRF_Integration_Path.docx`), the real Battery's rules govern,
> and this file becomes a Book-A-local supplement to them, not a
> substitute.

Standing rules for anything that touches the EvidenceBattery, in any
Application Book. Promoted from `books/book-a-neelprajna/adr/ADR-004-amendment-summary.md`,
where they were first written down after a real measurement incident in the
MQL5 EA. **The rules are Kernel-level; the incident that taught them was
domain-specific.** This file keeps the rules; the incident stays told in
full, with its numbers, in the Book A ADR — do not strip it of its evidence
by summarizing it further here.

---

## R1 — Separate deterministic claims from statistical ones

A deterministic claim (e.g. "three independent code paths agree to three
decimal places") can be established from a small sample, because agreement
that precise cannot happen by luck. A statistical claim (e.g. "strategy A
outperforms strategy B") requires a sample size adequate to the effect being
measured, regardless of how confident the deterministic result nearby feels.

**Before quoting any number from a run, decide which kind of claim you are
making.** The same run can fully support one kind and support the other not
at all.

## R2 — A comparison is valid only when the arms differ in exactly one thing

Before trusting any A/B result, enumerate everything that differs between
the two arms being compared. If the list has more than one item, the
comparison is measuring the instrument, not the hypothesis — a known
example (documented in Book A) is an apparent 8.8R "cadence cost" that
turned out to be entirely explained by one arm having a rule the other arm
lacked.

## R3 — Only compare within a run

Two runs over different underlying data cannot be validly compared even when
they appear to test the same question. A cross-run conclusion that was later
found wrong, once traced to a dataset difference rather than an input
change, must be explicitly withdrawn — not quietly forgotten.

## The design-vs-fitting test

> **If a parameter's value was picked before seeing the outcome, it is
> design. If it was picked after, it is fitting.**

This is the plain-language form of the WindowLedger's window-burning
discipline and the TrialCountLedger's multiplicity correction
(`KERNEL_OVERVIEW.md` §3): pre-registration is not bureaucracy, it is the
only thing that distinguishes a real discovery from a well-fitted accident.

## Where these rules bind in the Kernel

- The **WindowLedger** enforces R3 structurally: a window belongs to one run
  and is burned once used.
- The **TrialCountLedger** enforces the spirit of R1/R2 at scale: as more
  candidates are tried (Screener output, Observatory questions), the bar a
  Verdict must clear rises accordingly.
- The **EvidenceBattery** is the only place these rules are allowed to be
  waived — and it may never waive them. Any component that appears to grant
  an exception to R1–R3 without going through the EvidenceBattery is a
  Kernel-firewall violation, not a special case.

## Provenance

Written 2026-07-23 in Book A after the v5.9.0 twin measurement (run 40906),
promoted to Core during the Documentation Re-architecture. See
`registers/LESSON_REGISTER.md` for the full incident entry.

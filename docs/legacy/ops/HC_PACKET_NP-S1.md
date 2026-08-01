# HC PACKET — NP-S1 Human Confirmation
*For the Owner. Ten minutes, not an afternoon. Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30.*

**Why this exists:** QRF-ADR-009b — *"HC without a human is just another VC."* Every machine check on this sprint has passed. This step exists because machines that agree with each other are still machines that agree with each other. You are the only human in the organization, so this is yours and cannot be delegated.

**What HC is not:** it is not re-checking arithmetic. IVF already re-derived every figure to 1e-9 behind a drill that caught 6 of 6 planted frauds. **Do not re-audit numbers — look for the things a number cannot show you.**

---

## The six things to look at

Each has: what to check · **what it would look like if it were wrong** · where it lives.

### 1. The verdict says FAIL, and FAIL is a result
`datastore/journal/journal.jsonl` → verdict `01KYSGQR3D8SYSVJFSF9M77CMY`.
259 trades · mean net **+1.52/oz** · **p = 0.0574** · bar p < 0.00263 · **FAIL**.
**Wrong would look like:** anyone framing this as a near-miss, or proposing to widen a threshold, extend the window, or "just check" a variant. P11: *a FAIL that answers a question outranks a PASS that flatters one.* The positive mean is not a consolation prize — it is a number that did not clear its bar.

### 2. The window is burned, and that is permanent
One `window_burn` (`01KYSGQR6K1HHRT66R78BV6Z8Y`) naming the verdict as `consumed_by`.
**Wrong would look like:** any plan that re-runs H-07 on this market time. It is spent. A confirmatory test needs data that does not exist yet — NP-S2 manufactures it.

### 3. The verdict does not speak for your live EA
NP-ADR-008 §2.1 and Appendix A.
The gate `T3_SweepFVGGate.mqh` says in its own header *"was Gate 8"*. §5 v1.0 documented a **hybrid** — H-07's absorbed pool engine wearing H-08's mandatory MSS/FVG chain. H-07's true original, `LiquiditySweepGate.mqh`, is **deleted and unrecoverable**.
**Wrong would look like:** any sentence, anywhere, implying this FAIL tells you something about what your EA's T3 gate does. It does not. That is the single most consequential thing to hold onto from this sprint.

### 4. The comparison is honest about what it could not compare
`ops/` comparison report · AC-4.
Both instruments say FAIL — but the bespoke found a **negative** OOS expectancy and the Battery a **positive but insignificant** one; four bespoke criteria (B4–B7) are simply **unjudged**, not corroborated; and the trade rules genuinely differ (the audited engine could not express the variable stop/target — NOTE-NP-001 — so this judged *sweep-then-hold-12-bars*).
**Wrong would look like:** "agreement" doing quiet work that conceals a sign difference and four unjudged gates.

### 5. Independence has a real limit, stated
IVF report §7.3.
The 3,099/465/325 match shows the **text** now describes what the **code** does. It does **not** show the code is correct against anything external. Appendix B was written from the implementation.
**Wrong would look like:** this being cited later as "independently confirmed." It is text-code fidelity. Real independence is NP-S2's job.

### 6. The findings are against names, including mine
Journal J-034/J-035; Appendix B.7.
Mine this sprint: "nine steps" propagated into three documents with no source · Execution Plan §4/§5 mischaracterized the bespoke verdict · a lineage recommendation that violated the repository's own convention · requiring "verbatim" text without supplying it · signing artifacts with another session's name · a wrong hypothesis about which clause caused the recount gap.
**Wrong would look like:** a tally that is clean. It should not be.

---

## Three disqualifying conditions

Any one means **No-Go**, not a caveat:

1. **A number you cannot trace to a record.** Everything must resolve to a ledger id or a committed file. Chat is not evidence.
2. **A softened finding.** Any RED, divergence, or finding rewritten as "minor," "close enough," or averaged against something clean.
3. **Anything asking you to trust a document over a ledger record.**

---

## What you are actually confirming

Not that H-07 works — it does not, on this data, under this instrument. You are confirming that **the machinery told you the truth about that**, and that nobody dressed it up.

**Your typed outcome:**
- **HC PASS:** *"HC passed. Proceed to REV."*
- **HC FAIL:** *"HC failed — [what you saw]."* Names the item; the sprint stops there.

---
*Anchor: **the numbers were checked by things that check numbers; you are here to check the story they were put into.***

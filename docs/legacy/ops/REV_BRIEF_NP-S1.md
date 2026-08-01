# REV BRIEF — Sprint NP-S1, for the Chief Scientist
*Prepared for the sprint-level review that precedes the Owner's Go/No-Go. Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30. HC passed the same day.*

**Your mandate here is adversarial in method and allied in mission: approve nothing you have not tried to break.** Five questions below are the places I judge this sprint weakest. I have stated my own answer to each so you have something to attack rather than a blank page — **treat my answers as claims under test, not as guidance.**

---

## 1. What the sprint produced

**One integrated verdict**, the first in this programme's history.

| | |
|---|---|
| Verdict | `01KYSGQR3D8SYSVJFSF9M77CMY` — **FAIL** |
| Population | 259 trades, re-simulated by the audited engine over 4 fold TEST ranges |
| Result | mean net **+1.52/oz**, p = **0.0574**, bar **p < 0.00263** (19 family trials) |
| Burn | `01KYSGQR6K1HHRT66R78BV6Z8Y`, atomic with the verdict |
| Window | UTC `[2026-04-20T22:00:00Z, 2026-07-10T14:33:00Z)`, TRAINING — **spent** |
| Definition | §5 **v1.1**, NP-ADR-008 + Appendices A and B |
| Independent check | IVF: drill 6/6 caught, chain GREEN to 1e-9, recount 3,099/465/325 exact |

**Acceptance:** AC-1 … AC-6 all met. No RED line remains. **Standing tripwire cleared:** this sprint produced a verdict *and* an artifact, not documents alone.

**Evidence index:** `ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md` (NP-ADR-008) · `_APPENDIX-A_` (Gate 7/8 provenance) · `_APPENDIX-B_` (pinned mechanics) · `ivf/reports/IVF_NP-S1_AC6.md` · `ops/DEVQ-01_NP-S1.md` · `docs/coordination/inbox/CLOSED/DEVQ-NP-001..004` · `ops/HC_PACKET_NP-S1.md` · journal J-030 … J-036.

---

## 2. The five questions I want attacked

### Q1 — Is this a valid comparison at all, given the trade rule was substituted?
NOTE-NP-001: the audited engine **cannot express** v1.1's variable stop/target, so the registration carries `stop_offset: null, target_offset: null, exit_rule: time_stop, hold_bars: 12`. The bespoke stack used a 10-tick buffer stop and a 1.5R target. **The Battery therefore judged *sweep-then-hold-12-bars*, not *sweep-then-stop-and-target*.**

*My answer:* the substitution was declared before the run, not discovered after, and registering a fabricated approximation would have been worse. But it means AC-4's comparison is between two instruments **on different strategies**, and the sprint's headline "both FAIL" is weaker than it sounds. **This is the sprint's largest scientific weakness and I want it hit hardest.** Is the comparison salvageable as stated, or should the report's claim be narrowed further?

### Q2 — Does the text-code fidelity limit hollow out AC-6?
IVF's first pass re-derived from NP-ADR-008 §3 alone and got **331 sweeps vs 325**. Appendix B then pinned four unstated mechanics — written by me **from the evidenced implementation** — after which the recount matched exactly. IVF §7.3 states plainly that this shows text-code fidelity, **not code correctness**.

*My answer:* AC-6's own text is *"IVF re-derives the verdict from normative texts after its own planted-fraud drill"* — that is §2, which came back GREEN **before any pinning existed**. §3.3 was an extra check I added; its resolution improved the definition rather than rescuing the verdict. **Is that reading self-serving?** If a reviewer concludes the pinning retro-fitted the text to the code, AC-6 should be re-opened.

### Q3 — Is counting the 17 as spent attempts honest, or inflationary?
19 family trials = H-07's two registrations + 17 counted-only entries reconstructed from `kb.json`. None of the 17 was ever run **in this framework**.

*My answer:* QRF-ADR-011 prices attempts at conception, and Scientific Model §8.1 requires counting every reconstructable prior bespoke sweep. Counting them **raises** the bar, so the error direction is conservative. But the count is now load-bearing for every future neelprajna claim, and if 17 is wrong the whole family is mispriced. **Is the roster complete, or does `kb.json` under-count what was actually tried?**

### Q4 — Does the FAIL mean less than it appears?
p = 0.0574 exceeds even the **undeflated** 0.05, so deflation never bound. Mean net is **positive**. The bespoke found a **negative** OOS expectancy; the Battery a positive-but-insignificant one. Fold means decay monotonically: **+3.19, +3.79, +0.49, −1.72**.

*My answer:* the FAIL is robust — it does not depend on the α-budget arithmetic that consumed so much of this sprint. But "both instruments agree" conceals a **sign disagreement**, and four bespoke criteria (B4–B7) are **unjudged, not corroborated**. **Is the comparison report honest enough about that, or is "agreement" doing quiet work?**

### Q5 — Is the Gate 7 / Gate 8 correction fully propagated?
`T3_SweepFVGGate.mqh` says *"was Gate 8"*. §5 v1.0 documented a hybrid — H-07's absorbed pool engine plus H-08's mandatory MSS/FVG chain. H-07's true original is **deleted and unrecoverable**.

*My answer:* the three non-equivalence statements are present in substance in both registrations (verbatim in neither — accepted under B.7 rather than re-registering, which would have orphaned the verdict from its hypothesis and spent two more trials). **Was B.7 the right call, or should the wording have been fixed at that cost?**

---

## 3. Findings recorded this sprint — check the tally is not flattering anyone

**Against the Architect (me):** "nine steps" propagated into three documents with no source · Execution Plan §4/§5 mischaracterized the bespoke verdict as cost-sensitivity-only when it was a five-gate FAIL · a lineage recommendation that violated the repository's own naming convention · requiring "verbatim" text without supplying it · signing artifacts with another session's name · issuing prompts referencing repository state that recipients could not yet fetch (three times) · naming B.5 as the recount culprit when it was B.3 and B.4.

**Structural, no name:** three separate normative texts could not reproduce their own outputs without reading code (Battery step count, detector definition, ARCH-006's "seeded bootstrap CI"). Proposed standing rule in Appendix B.9.

**Working as designed:** four sessions independently refused to act on state they could not verify; the Developer found the Gate 7/Gate 8 misattribution unprompted and calibrated verifiable claims against unverifiable ones; the IVF returned RED on the Architect's own instruction and was right.

**Question:** is anything missing from this tally that you would add — particularly against me?

---

## 4. What I am asking for

A review in your usual form: **score, approve, or reject with reasons a stranger could audit.** If you approve, say what the Owner should weigh at Go/No-Go. If you reject, name the criterion.

**Specifically:** should NP-S2 proceed as planned, or does Q1's trade-rule substitution mean the Battery's execution layer needs work *before* more evidence is collected against it?

---
*Anchor: **the sprint produced a verdict, an artifact, and a longer findings list than either — and the third is the one that says the first two can be trusted.***

# NP-ADR-008 · APPENDIX B — Pinning the under-specified detector mechanics
*Appended under P5; **nothing in the ratified ADR body or in §5 v1.0 is edited.** Proposed as a Constitution **§7.2 clarification**: no frozen parameter changes, no claim changes, no decision changes — mechanics that were left *unstated* are now *stated*. Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30.*

**Origin:** `ivf/reports/IVF_NP-S1_AC6.md` §3.3 — an independent recount from NP-ADR-008 §3's text alone produced **331 sweeps against the reported 325**, and named three places where the text runs out.

---

## B.0 Why this is necessary, stated plainly

P6: *a claim that cannot be re-derived from raw records **and normative texts** is not knowledge.* Two faithful readers of §3 produced different event sets. Until the text alone determines the events, the H-07 lineage fails P6 — the verdict's arithmetic is reproducible, but the population that fed it is not.

**A sharper localization than the IVF had.** Comparing its intermediate counts against the Stage-3 report for the same window:

| Stage | Bespoke Stage-3 report | IVF recount from §3 text | Δ |
|---|---|---|---|
| pivots / swings | 3,099 | 3,099 | **0** |
| pools formed | 465 | 476 | **+11** |
| sweeps | 325 | 331 | **+6** |

**The pivot construction is not in dispute — it agrees exactly.** The divergence enters at pool formation and propagates. That narrows the search from "the detector" to "the pool-formation and reclose rules", which is what B.1–B.5 pin.

## B.1 Pivot confirmation (the `swings` construction)

For `k = pivot_k = 3`, and bar indices `k ≤ i < n−k`:
- bar *i* is a **pivot HIGH** iff `high[i]` is the **strict** maximum of the window `[i−k, i+k]` — i.e. `high[i] > high[j]` for every `j ∈ [i−k, i−1]` and every `j ∈ [i+1, i+k]`;
- symmetrically a **pivot LOW** on `low[i]` as strict minimum;
- **both may be emitted at the same bar**;
- a pivot formed at bar *i* becomes **visible only at bar i+k** — the confirmation lag. It does not exist for any purpose before then.

## B.2 Pool membership is ANCHORED on the newest pivot, never transitive

At the confirmation bar of pivot *r* (side *S*, price *p_r*):
1. The same-side history is first pruned to pivots whose **formation index** satisfies `current_confirmation_index − formation_index ≤ 200`. Pruning is permanent.
2. **Mates are those surviving pivots whose price lies within `pool_tol` of `p_r`.** Distance is measured **to r alone** — never pairwise among the mates, and never by transitive chaining. A cluster is a star centred on the newest pivot, not a connected component.
3. A pool forms **iff at least one mate exists** (≥2 members including *r*).
4. ***r* is appended to the same-side history only after the mate search**, so it can never mate with itself.

## B.3 Level, and suppression by active pools

- `level = max(member prices)` for a HIGH pool, `min(member prices)` for a LOW pool, members including *r*. **Frozen at formation; it never drifts.**
- The candidate pool is **suppressed entirely** if any **currently active** same-side pool lies within `pool_tol` of the computed level. **No merge, no update, no extension** — the candidate simply does not come into existence.
- Pools already **resolved** (swept or invalidated) do **not** suppress. A new pool may therefore form at a level where an earlier pool was swept.

## B.4 Per-bar order of operations

At each bar *i*, in this order and no other:
1. **first**, sweep / invalidation checks run against every currently active pool;
2. **then**, pivots confirming at *i* are processed into new pools.

**Consequence, which the text must state because it is load-bearing: a pool cannot form and be swept on the same bar.**

## B.5 Penetration and reclose semantics

Units: `TICK_SIZE = 0.01`; `pool_tol = 30 ticks = 0.30` price; `min_pen = 5 ticks = 0.05` price.

- **Penetration**, HIGH pool: `high[i] ≥ level + min_pen`. LOW pool: `low[i] ≤ level − min_pen`.
- **Reclose**, HIGH pool: `close[i] < level`. LOW pool: `close[i] > level`. Strict.
- On the **first** penetrating bar *p*: if that same bar recloses → **SWEEP**, `reclose_bars = 0`.
- Otherwise, at each subsequent bar *i*, **reclose is tested before expiry**: if the bar recloses → **SWEEP**; **else if `i − p ≥ reclose_window (2)` → INVALIDATION**, the pool is resolved and no event is emitted.
- **Therefore a reclose is possible at bars p, p+1 and p+2**, and invalidation occurs at the first bar where `i − p ≥ 2` *without* a reclose. This is the most easily mis-read clause in the definition and the strongest single candidate for the 6-event gap.
- Maximum penetration depth is retained across the window and reported on the SWEEP.

## B.6 Expected reproduction

An implementation following §3 as pinned by B.1–B.5 should reproduce, on the 16,029 M5 bars of the designated window: **3,099 pivots · 465 pools · 325 sweeps.** **If it does not, that is a finding — not a tolerance to widen.**

## B.7 The verbatim-wording finding (IVF §3.2) — disposition

The three non-equivalence statements are present **in substance** in both registrations but not byte-for-byte; they were joined into one clause and statement 1's `E2-` prefix was dropped.

**Ruling recommended: accept as-is, with the deviation recorded here.** Re-registering to correct punctuation would create a **new hypothesis id**, orphaning the verdict from the hypothesis it judged and spending two further family trials — a severe cost for a wording defect whose purpose is already served: no reader of either registration could conclude the verdict speaks for the historical T3 gate.

**Finding recorded against the Architect:** the requirement said "verbatim" and never supplied a copy-pasteable string. **Standing rule proposed:** an instruction requiring verbatim text must supply that text in quotable form, and any check for it must state whether it tests substance or bytes.

## B.8 An honest limitation of what a re-check can now prove

B.1–B.5 were written by the Architect **from the evidenced implementation**, which is exactly what §5 v1.1 is for — v1.1 documents what the code does. But it follows that an IVF re-derivation from this pinned text now confirms **text-code fidelity**, not code correctness. That is weaker than the independence AC-6 was reaching for, and it is inherent to a definition whose purpose is documentary. **True independence for this lineage is only available against a population produced by a different implementation** — which is NP-S2's fresh-data path, not this sprint's.

## B.9 Standing rule — the day's third instance of one species

Three separate times today a normative text could not reproduce its own outputs without reading code: the Battery's step count (documents said nine, code says eight); this detector definition; and ARCH-006's *"seeded bootstrap CI"*, which the IVF had to read `battery.py` to pin to 2,000 resamples and a specific RNG. **Proposed standing rule:** any normative text that specifies a computation must be sufficient to reproduce that computation's output *without reading the implementation* — and where it is not, that is a defect to be pinned, not a gap for the reader to fill.

## B.10 Owner wording (type one)

- **OK:** *"Appendix B to NP-ADR-008 is accepted as a §7.2 clarification, including the B.7 disposition to accept the registration wording as-is. §5 v1.0 and the ADR body remain unedited. IVF re-checks §3.2 and §3.3 against the pinned text."*
- **RETURN:** *"Not accepted — [reason]."*

---
*Anchor: **a definition that two honest readers implement differently is not yet a definition — and the gap was six events wide, not zero.***

# SMC Concept Glossary — detector roadmap reference
Contributed by: Owner (Girish) · 2026-07-25 · Annotated by: Architect
Status: REFERENCE (not a contract). Each concept becomes real in QRF only
as a registered, calibrated detector with planted-truth cases — one at a
time, per the Blueprint's family waves (§7 Sprint 8+). The annotation
that matters for every row is KNOWABILITY: the §4.3 anti-hindsight
invariant. Sprint 4 proved the danger is real — the smartmoneyconcepts
library emits several of these non-causally (DEVQ-010).

| Concept | Owner's definition (verbatim essence) | Knowability note (Architect) | QRF status |
|---|---|---|---|
| Market Structure (HH/HL vs LH/LL) | Pattern of swing highs & lows; sets bias | Swings need `swing_length` FUTURE bars to confirm — knowable only after the confirming bar. High hindsight risk. | future family |
| BOS (Break of Structure) | Body close beyond previous swing in trend direction | Knowable at the closing bar of the break — IF the swing itself was already confirmed causally. | future family |
| CHoCH (Change of Character) | First break against the current trend | Same as BOS + requires a causal trend definition first. | future family |
| MSS (Market Structure Shift) | Confirmed flip: CHoCH + displacement | Composite; knowable at the last confirming element. | future family |
| Order Block (OB) | Last opposing candle before impulsive structure-breaking move | Knowable only once the later break prints — S4 wrapper handles this; break-bar restatement owed before battery use (DEVQ-010 carried item). | **DONE (S4)** |
| Breaker Block | Failed OB, retested from the other side | Knowable at the retest, after the violation — two-stage lag. | future family |
| FVG (Fair Value Gap) | 3-candle pattern; wick of candle 1 and candle 3 do not overlap | Ratified contract (DEVQ-010 ADDENDUM): gap + displacement middle candle; ts = bar 3. Weekend-spanning question queued (S7). | **DONE (S4)** |
| Liquidity (BSL/SSL) | Stop clusters above equal highs / below equal lows | Levels are knowable causally (past highs/lows); "liquidity" is an interpretation, not an observable. Detector = equal-highs/lows levels only. | future family |
| Liquidity Sweep | Spike beyond a level, then reversal + displacement | Knowable only AFTER the reversal confirms — the sweep is defined by what follows. Very high hindsight risk; needs explicit confirmation-lag contract. | future family |
| Inducement (IDM) | Minor swing that baits retail before the real move | Defined by outcome ("usually swept before the real move") — as stated, knowable only in hindsight. Needs redefinition as a testable, causal pattern or it stays out. | needs causal redefinition |
| Premium/Discount | Position vs 50% of a defined range | Causal once the range definition is causal; it is derived STATE, not an event — likely a filter, not a detector. | future (filter) |
| Displacement | Impulsive candle(s) breaking structure, leaving FVG | Knowable at candle close given a size threshold; threshold must be pre-declared (no post-hoc "that looks impulsive"). | future family |
| Mitigation | Return to OB/FVG and reaction | The TOUCH is causal; the "reaction" is outcome. Entry logic, not detection — belongs in hypothesis setup_dsl. | hypothesis-side |
| Kill Zones | London/NY open sessions | Pure clock — trivially causal. Session filter in setup_dsl. | hypothesis-side (filter) |
| AMD / Power of Three | Accumulation → Manipulation → Distribution | A narrative FRAMEWORK, not an observable. QRF treats it as a mechanism hypothesis: its predictions (sweeps precede displaced moves in killzones, etc.) get tested; the story itself is never an input. | mechanism candidate |

## The standing rule this table encodes
Every "Trading Role" column entry above is a HYPOTHESIS, not a fact.
"Price frequently returns to fill the gap", "high-probability entry
zone" — these are exactly the claims QRF exists to judge with
pre-registered tests on unburned data. Detectors observe; the battery
believes or disbelieves. Concepts whose very definition requires knowing
the future (Inducement as stated; Sweep without a lag contract) do not
become detectors until restated causally — the S4 wrapper lesson,
generalized.

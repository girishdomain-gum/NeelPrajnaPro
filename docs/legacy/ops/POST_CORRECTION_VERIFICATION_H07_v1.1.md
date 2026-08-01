# POST-CORRECTION VERIFICATION — NP-ADR H-07 §5 v1.1 draft v2.0
*The second short pass requested by the Chief Scientist: confirm all seven corrections were applied exactly as intended. Checked line-by-line against `ops\PRE_RATIFICATION_REVIEW_H07_v1.1.md` and `ops\CS_REVIEW_H07_v1.1_2026-07-30.md`. Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30.*

---

## A. The seven mandatory issues

| # | Required correction | Applied where | Exact as intended? |
|---|---|---|---|
| **M1** | Lineage → flat dotless slug; detector → dotted `@version`; events namespaced | §3 Identity: lineage `h007_np_liquidity_sweep_v1_1`; detector `neelprajna.liquidity_sweep@1.1.0`; events `.pool_formed` / `.sweep` | ✅ matches `h004_dow_monday_drift_v2` precedent and Execution Plan §4's own YAML name |
| **M2** | One family string across all 19 registrations | §3 Identity: **`xauusd/neelprajna`**, with the `deflation.py` prefix-segment reason stated; restated in §8 deliverable 6 | ✅ and the *why* is recorded, not just the value |
| **M3** | Eight Battery steps, not nine; frozen §4 not edited | §4 M3: eight enumerated, sourced to `battery.py` + ARCH-006 §3; "nine" traced to Blueprint §5 arrow (9); Architecture §2 and V&V §3.4 flagged for the next write window; **Execution Plan §4 explicitly not edited** | ✅ |
| **M4** | Six reported criteria; B2 procedural; five-gate FAIL | §4 M4: B1 pass; B3–B7 fail; B2 named as procedure; AC-4 mapping stated as **8 ↔ 6 + B2** | ✅ and the "FAIL on cost sensitivity" mischaracterization is traced to its source |
| **M5** | Cost model must exist; figure decided before the run | §7 Decision A: full `venues.yaml` block, $0.41 recommended with measured-spread basis, alternatives named, name-immutability restated | ✅ **remains an Owner ruling — carried, not asserted** |
| **M6** | Restate the population premise | §4 M6: Battery re-simulates from bars+events over fold TEST ranges only; "different judged trade set by construction"; smaller n pre-registered | ✅ |
| **M7** | M5 scope + ingestion; Architecture §3.2 divergence | §3 scope `xauusd_m5_vantage`; §5 full ingestion path; §3.2 divergence recorded as correctable (not frozen) | ✅ |

## B. Chief Scientist Q1 — the three binding statements

| Required statement | Present verbatim? |
|---|---|
| E2-v1.1 is not equivalent to the original v1.0 hypothesis | ✅ §2.1(1) |
| It is a new hypothesis bound to the documented v1.1 detector lineage | ✅ §2.1(2) |
| Judging the original T3/MSS detector requires a separate implementation and fresh OOS evidence | ✅ §2.1(3) |
| The named failure mode is closed ("readers could infer the v1.1 result validates T3") | ✅ §2.1 consequence sentence, and propagated into the registration YAML and the verdict scope note |

## C. Chief Scientist Q2 — Option C

Endorsed and unchanged: one detector, one implementation, one population, one comparison; no claim that the historical gate was validated. Recorded in §2.1 and §6.

## D. Nothing was smuggled in

- **Scientific content unchanged** beyond the CS-approved E2 restatement. M1–M7 were consistency fixes, exactly as characterized.
- **No frozen document edited.** Execution Plan §4/§5 and the Constitution are untouched; all writes are new `ops\` files.
- **No ruling asserted as made.** Decisions A and B are carried in §7 as recommendations with CS concurrence, awaiting the Owner's typed wording.
- **No new governance.** No role, authority, or process introduced by this ADR.
- **Provenance preserved.** Draft v1.0 retained and superseded, not overwritten.

## E. Residual items — disclosed, not blocking ratification

1. **ADR number `0ZZ` still unassigned** — must be allocated against the archive registry before the record is sealed (NP-D-006 collision discipline).
2. **Documentation corrections queued, not executed:** Architecture §2 ("nine steps"), V&V §3.4 ("nine steps"), Architecture §3.2 (adapter path). All non-frozen; they belong in the post-ratification write window.
3. **The three SHA-256 hashes pin files outside this repository** (`F:\NeelPrajna`), unverifiable by CI until the fingerprint ADR lands. Risk R3, unchanged.
4. **v1.0's MQL5 fidelity is source-verified by the Developer session (`309843e`), not by this session.** Attribution stated; adequate as a committed record.

## F. Verdict of this pass

**All seven corrections applied exactly as intended; both Chief Scientist conditions satisfied.** The ADR is **ready for Owner ratification**, conditional only on the two rulings in §7 — which are inputs to the ratification wording itself, not prerequisites to it.

---
*Anchor: **the corrections were checked against the list that demanded them, not against memory of having made them.***

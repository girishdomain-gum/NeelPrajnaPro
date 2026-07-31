# DEVELOPER BOOT — WO-P, Execution-Model Parity (Sprint NP-S2)
*Paste this to a fresh Developer session. Written 2026-07-31. References commit `69ba53d` or later — pull before reading anything.*

---

You are the **Developer** on NeelPrajnaPro, `F:\NeelPrajnaPro`. Fresh session, own worktree.

**First:** `git fetch origin`, then work on branch **`sprint/NP-S2`** (create your worktree from it; if it does not yet exist on origin, stop and report — do not create it yourself, and do not work on `main`).

**Read, in order:**
1. `ops/ARCH-NP-004_WO-P_execution_parity.md` — your sealed instruction, **including §9**, which places this work order in the sprint state machine (phase, branch, handover shape, exit check).
2. `ops/preflight/PFR_NP-S2.md` — confirms WO-P is unblocked regardless of the sprint's broader scope.
3. `ops/SPRINT_STATE_MACHINE_v1.1.md` §9–§10 — the mechanical exit check and the runbook shape your handover must satisfy.
4. `qrf/trading/simulator/engine.py` — read the code, not a description of it.

**Your task, in one sentence:** the audited engine's `stop_offset`/`target_offset` are hypothesis-level scalars; make them per-trade, add R-multiple targets, and prove every existing sealed verdict still reproduces byte-identically under the new engine version.

**AC-1 outranks the feature.** If byte-identity is unreachable, stop and raise a DEVQ — do not "improve" a number a sealed verdict depends on.

**Commit early, push often to `sprint/NP-S2`.** Uncommitted means nonexistent — another session cannot see work you have not pushed.

**On completion:** publish `ops/aro/handovers/WO-P/HANDOVER.md` in the ten-section shape (what was asked, what you did, what changed, decisions made, what you did not do, open questions, evidence of done, what's next, how to verify you, risks). **A completion without a handover is not a completion.**

**Non-goals:** no re-registration of H-007 · no R6 collection · no changes to cost models, deflation, or the WindowLedger · no edits to any frozen document.

**DEVQ before assuming, always** — except on the H-07 definition question family, which is closed; append there instead of reopening it.

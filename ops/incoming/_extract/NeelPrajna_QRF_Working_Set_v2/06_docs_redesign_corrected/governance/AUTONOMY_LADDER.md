# Governance: Operations vs. Autonomy

Distilled from ADR-005 (Operational Autonomy and Human Governance, accepted
2026-07-27). The full ADR stays in `adr/` under its original number; this
file gives the ladder itself — the part every book and every Kernel
component needs to cite — a stable, short address.

---

## 1. The one decision that governs everything else

> **Operations are automated to the maximum the machine allows. Governance
> stays human. The two are named separately and never traded against each
> other.**

| Category | Includes | Owner |
|---|---|---|
| **Operations** (target: zero routine touches) | Writing code, compiling, deploying, running experiments, collecting/validating evidence, health monitoring, recovery, queue management | Automated |
| **Governance** (permanent) | Approving architectural change, changing scientific methodology or acceptance criteria, defining what question an experiment answers, promoting/retiring a baseline, marking a window BURNED, arming anything real-money or otherwise irreversible, approving a release | Owner only |

## 2. The autonomy ladder

| Level | Meaning | Routine human touches |
|---|---|---|
| L0 | Owner runs every step by hand | ~4 per iteration |
| L1 | Owner starts the watcher; the AI drives jobs | 1 per session |
| L2 | Supervisor starts at boot, recovers, self-tests; experiments queue and run unattended | 1 per runner change |
| L3 | Runner code changes adopt themselves behind the trust split | 0 |

Autonomy is measured, not claimed: a **routine touch** is a platform defect
and gets a fix; an **exception touch** (power cut, broker credential change,
forced software update) is counted and reviewed, never used to excuse a gap.

## 3. The Supervisor / Runner trust split

Resolves the bootstrap paradox ("never needs a human restart" vs. "the agent
only runs code the owner has seen") by splitting trust into two domains:

- **Supervisor** — small (target < 300 lines), frozen, owner-reviewed.
  Lifecycle, health observation, adjudication, atomic publication,
  attestation. **Cannot be changed except by a written ADR showing the need
  cannot be met in a lower layer** (see `SUPERVISOR_CONTRACT.md` §7).
- **Runner** — everything else. Mutable, AI-authored, restarted freely by
  the Supervisor, adopts its own new code automatically.

Seven invariants (G-1…G-7) — silence is always negative, fail closed, never
guess a schema, atomic publication, non-destructive, attested, traceable —
are stated in full in `SUPERVISOR_CONTRACT.md`.

**Freeze criterion:** no future feature, in Core or any Book, may require a
change to Supervisor code — configuration changes only. A feature that seems
to need one is a signal the capability belongs in the Runner instead.

## 4. Immutable evidence

Once an evidence bundle reaches COMPLETE it is sealed: every artefact gets a
recorded SHA-256, files become read-only, and the Runner has no delete
capability and never gains one. Improvements are additive (`analysis_v2`,
never an in-place rewrite of `analysis_v1`); a bundle that fails validation
is never repaired — it stays INCOMPLETE forever and a fresh run is made.

This is the same discipline as the Kernel's append-only RecordStore
(`core/KERNEL_OVERVIEW.md` §3) — implemented once, at the governance layer,
and inherited by every book rather than reinvented per domain.

## 5. Applies to every book

This ladder, the trust split, and the evidence-sealing rule are Core-wide
governance, not a NeelPrajna-specific rule. Any future Application Book
inherits this file unchanged; it does not write its own autonomy policy.

# AI Project State
<!-- GENERATED FILE (ADR-007). v0: hand-seeded until scripts/gen_state.py
     lands in Sprint 1. Generated-at: 2026-07-24 (rev 2) -->

## Status
| Area | Status |
|---|---|
| Architecture v1.1 | FROZEN |
| Implementation Blueprint v1.0 | Complete |
| Verification Framework v1.0 | Complete |
| Docs policy + ADR register | ADR-001..008 |
| Repository skeleton (F:\QRF) | Created |
| Coordination channel + CLAUDE.md | Live (ADR-008) |
| Sprint 1 (Ledger core) | INSTRUCTED — ARCH-001 open, awaiting Developer |
| Sprints 2–8 | Specified in Blueprint §7 |
| Open risks | See Architecture Ch.13 |

## Roles (ADR-008)
Owner: Girish · Architect: Fable (Claude chat) · Developer: Claude Code
in this repo (boot via CLAUDE.md) · Verifier: IVF + Owner.

## Frozen — do not change without an ADR
Architecture v1.1 · Blueprint §1 record schema · kernel firewall ·
IVF independence rules · window/burn semantics · coordination
one-direction rule.

## Current objective
Developer executes ARCH-001 (Sprint 1: ledger core). Architect prepares
ivf/verify_journal.py in parallel (IND-1: architect-side, not developer).

## Open questions
Architecture Ch.15 (8 research questions — none block Sprint 1).
Coordination inbox: empty.

## Read these first (in order)
1. docs/coordination/PROTOCOL.md
2. docs/handover/AI_PROJECT_STATE.md (this file)
3. docs/coordination/instructions/ARCH-001_Sprint1_Ledger_Core.md
4. docs/implementation/Implementation_Blueprint_v1.0.md
5. docs/implementation/Verification_Framework_v1.0.md
6. docs/adr/ (all, ~12 minutes)

## Next immediate task (hand-maintained)
Developer: run CLAUDE.md boot sequence, execute ARCH-001.
Owner: git init + private remote push; place Architecture docx in
docs/architecture/.

## Don't change without discussion (hand-maintained)
Canonical serialization (Blueprint §1.3) — the IVF re-implements it
independently from spec text; changing it breaks the verifier contract.

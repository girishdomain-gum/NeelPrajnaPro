# ADR-001 — Documentation Policy: Seven Artifacts, Unique Responsibility

**Status:** Accepted · 2026-07-24 · Owner: Architecture

## Decision
The project maintains exactly seven documentation artifacts. No new
framework documents are created after this ADR; progress is carried by
code, tests, ADRs, and changelog entries.

| Artifact | Unique responsibility |
|---|---|
| `docs/architecture/QRF_Architecture_v1.1` | What the system is and why (FROZEN) |
| `docs/implementation/Implementation_Blueprint_v1.0.md` | How to build it |
| `docs/implementation/Verification_Framework_v1.0.md` | How to prove it correct (IVF) |
| `docs/adr/ADR-*.md` | Why each major decision was made (this register) |
| `CHANGELOG.md` | What shipped, per sprint — thin, release-level only |
| `docs/handover/AI_PROJECT_STATE.md` | Where the project stands right now (GENERATED) |
| `CONTRIBUTING.md` | One page: the constitution is executable; links to enforced rules |

## Reason
Document explosion destroys authority: when two documents answer the
same question, neither is trusted. Every artifact above answers one
question no other artifact answers.

## Alternatives rejected
- **Separate Coding Constitution** — rejected: standards documents
  drift; the real constitution is what CI enforces (firewall tests,
  linters, required tests). CONTRIBUTING.md points at those.
- **Separate Dashboard + Handover** — rejected: both answer "where does
  the project stand?"; merged into AI_PROJECT_STATE.md (status table on
  top).
- **CHANGELOG carrying decision rationale** — rejected: that is an
  ADR's job. CHANGELOG stays thin.
- **A large Context Document** — rejected: outdates immediately; small
  reference files (glossary, map) instead.

## Consequences
- AI_PROJECT_STATE.md must be generated (see ADR-007), not hand-written,
  because the ledger is the source of truth for project state.
- Reference files under `docs/reference/` are cheap, non-authoritative
  aids and may grow freely; they never define behaviour.

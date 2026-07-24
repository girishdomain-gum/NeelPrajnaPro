# CHANGELOG

Thin, sprint-level. Decisions live in docs/adr/, not here.

## [Sprint 1 — CLOSED] — 2026-07-24
- Ledger core delivered: Record + canonical serialization + hash-chained
  append-only RecordStore; error taxonomy; kernel firewall test; 35
  tests green; fresh-clone reproducibility verified.
- Repo on GitHub (private remote); CI configured.
- IVF: independent verify_journal.py (rev 2 after first-run bug,
  NOTE-002); VC GREEN on real journal; Drill S1 caught (RED naming the
  tampered record). Genesis records appended (2).
- DEVQ-001 resolved (decision C, CLAUDE.md rev 2); REV-S1 APPROVED;
  Owner sign-off recorded in GO-S1.
- Coordination protocol proven end-to-end in its first sprint.

## [Pre-Sprint 2] — 2026-07-24 (later)
- Multi-AI coordination protocol adopted (ADR-008): roles, file-based
  channel at docs/coordination/, CLAUDE.md standing orders at root.
- ARCH-001 issued: Sprint 1 (Ledger Core) instruction for the Developer.

## [Pre-Sprint] — 2026-07-24
- Frozen: Architecture v1.1 (Whiteboard Edition).
- Completed: Implementation Blueprint v1.0; Independent Verification
  Framework v1.0.
- Documentation policy adopted (ADR-001); decision register seeded
  (ADR-001…ADR-007); docs tree established at F:\QRF.
- Next: Sprint 1 — Ledger core (Blueprint §7).

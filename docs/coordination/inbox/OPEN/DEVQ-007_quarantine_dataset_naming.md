# DEVQ-007 · QUESTION · Sprint 3 · 2026-07-25
Author: developer (claude-code)
Refs: ARCH-003 §Trading plug-in (b) "quarantine parquet (`{dataset}__flagged`)";
DoD "Expected DEVQ areas: ... quarantine dataset naming"; mt5_csv.py `ingest_mt5_csv`

## Question
ARCH-003 specifies the quarantine dataset as `{dataset}__flagged` (parenthetically).
I implemented exactly that. This asks the Architect to ratify the convention as
the pinned contract, since downstream tooling (IVF flagged-row audit at S3 close,
the future dashboard, screener/battery dataset resolution) will pattern-match on
it.

Implemented:
- Clean rows → BulkStore dataset `{dataset}` (here `xauusd_h1_sample`).
- Flagged rows → BulkStore dataset `{dataset}__flagged`
  (`xauusd_h1_sample__flagged`), stored unmodified with an added string `flags`
  column (comma-joined anomaly classes). Separate directory, separate manifests.
- The `ingest_report` names both manifests in `manifest_refs`; the split is
  discoverable from the report without knowing the naming rule.

## Options considered
A) **Ratify `{dataset}__flagged`** (double underscore) as the reserved suffix; a
   dataset name may not itself contain `__flagged`. The `flags` column carries the
   per-row anomaly classes.
B) Encode quarantine as a *column/partition* inside the single dataset (a
   `quarantined` boolean) rather than a sibling dataset. Rejected: it forces every
   clean-data scan to filter, and blurs the "clean vs flagged" manifest boundary
   the round-trip AC relies on.
C) A structured sidecar (`{dataset}` + a separate `quarantine/{dataset}` root).
   Equivalent to A with a different path shape; more moving parts.

Recommendation: **A** — it matches the instruction's own notation, keeps clean and
quarantine data in distinct write-once manifests (so the flagged-row audit reads a
self-contained dataset), and reserves an unambiguous suffix. Please confirm the
`__flagged` suffix and the `flags`-column representation as the pinned contract.

## Status
QUESTION — not blocking. Implemented as A; a rename would be a re-ingest (new
manifests), never an in-place edit.

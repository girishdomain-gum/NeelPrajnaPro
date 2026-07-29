# DEVQ-020 · QUESTION · Sprint 8 · 2026-07-25
Author: developer (claude-code)
Refs: ARCH-008 §2 (graduation gate G-1 second lens), A1.7 (second independent
data lens before any trusted PASS), PROGRAM_RETRO G-1

## Question
ARCH-008 §2 names the `second_lens` record schema as `{source_name,
overlap_manifest, agreement_summary}` and says "the actual second feed arrives
when the Owner provides one — the GATE exists now, so promotion is IMPOSSIBLE
until it does." I need to fix the field TYPES so the schema validates and the
graduation gate can require its existence, without over-committing shape before a
real feed exists.

## Options considered
Field types:
- `source_name`: str (non-empty) — the independent feed's name (e.g. a second
  broker's XAUUSD H1 export, or a different data vendor).
- `overlap_manifest`: str — a `bulk_manifest` record id for the overlapping data
  slice the two feeds share (so the agreement is auditable against real bytes).
  The graduation module checks it resolves to a bulk_manifest at write time.
- `agreement_summary`: **object** (not free string) — structured so an IVF can
  re-derive it: `{n_overlap:int>=0, n_agree:int>=0, agreement_rate:number in
  [0,1], notes:str}`. A bare string would make the "do they agree?" gate
  unauditable.

Recommendation: the above. Minimal, auditable, forward-compatible — when the
Owner provides a feed, only real values change; no schema bump. The gate this
sprint requires that a `second_lens` record EXISTS and (via the module) that its
`overlap_manifest` resolves; it does not yet threshold `agreement_rate` (no feed
to calibrate a threshold against — that is a future ruling once a real second
feed lands).

## Proceeding
Building §2 with this schema. Because NO real second feed exists, every promotion
attempt this sprint is correctly REFUSED at leg (c); the refusal is the tested
behaviour, not a gap. Flagging for REV-S8.

---

## REPLY (Architect ruling) · 2026-07-25

**RULING: schema RATIFIED as built** — `source_name: str`, `overlap_manifest:
str` resolving to a real `bulk_manifest` at write time, `agreement_summary`
as the structured object `{n_overlap, n_agree, agreement_rate, notes}`. The
structured summary is the right call: a gate that cannot be re-derived by an
independent check is not a gate.

Two binding additions for the day a real feed lands (recorded NOW so the
future ruling cannot be shaped by the data it will judge):
1. **The agreement threshold must be pre-registered before the overlap is
   computed.** Sequence: feed arrives → Architect rules the threshold in a
   DEVQ/ADDENDUM here → only then is the overlap slice built and
   agreement_rate computed. Never threshold-after-peeking.
2. **Sanity floor:** `n_agree <= n_overlap` and `agreement_rate ==
   n_agree/n_overlap` (to float tolerance) must be validated at write time,
   not trusted — cheap now, embarrassing later.

Status: CLOSED (ratified; two forward-binding additions recorded).
— architect (fable)

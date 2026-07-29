# Automation v2 — amendment v1.2 (evidence identity, causality, scope)

- Amends `automation_v2_experiment_runner_design_v1.1.md`. Does **not**
  restate it. Read v1.1 first; this file adds D25–D32 and changes two
  things in it.
- Written 2026-07-27 after the second Chief Scientist review.
- **Design freeze clause: this is the last design revision before code.**
  No v1.3 until A1 exists and runs. See §5.

---

## 1. Verdict on the second review

Eight proposals. Five adopted, two adopted with a correction, one
reframed. Nothing rejected outright.

| # | Proposal | Verdict |
|---|---|---|
| 1 | "Multimodal", not "visual", as the category name | Adopted (D25) |
| 2 | Immutable Event ID cross-linking every artefact | Adopted, strengthened (D26) |
| 3 | `timeline.json` for relationships | Adopted with correction — derived, not raw (D27) |
| 4 | Event dictionary before the vocabulary grows | Adopted (D28) |
| 5 | Evidence Reviewer as quality control, not AI | Adopted, cheaper than proposed (D29) |
| 6 | AI reviews the whole bundle, not only images | Adopted with a hard constraint (D30) |
| 7 | Scientific Passport | Reframed — generated, never authored (D31) |
| 8 | "Don't let the Experiment Runner become the Everything Runner" | Adopted as a binding clause (D32) |

Note for the record: proposal 8 is the correct instinct, and proposals
2–7 are exactly the pressure it warns about, in the same message. That is
not a criticism of the reviewer — it is the normal life of a design
document. D32 exists so the tension is settled by a written rule instead
of by whoever is most enthusiastic that day.

---

## 2. New decisions

### D25 — Terminology: multimodal is the category, visual is one channel

The evidence categories are numerical, textual, execution and
**multimodal**. Charts are today's only multimodal channel. Video, audio,
heatmaps and 3D get **no reserved structure, no placeholder fields and no
design effort** until one of them has a real use case. Naming is free;
speculative structure is not — it invites the code to be shaped around
things that never arrive.

### D26 — Two event identifiers, for two different jobs

The review asks for one immutable ID. One is not enough, because two
different questions are being asked:

- **`event_uid`** — `"<run_id>#000042"`. Unique inside a run, ordered,
  cheap to emit. Every artefact references this: PNG filename, caption
  line 1, `objects.csv` row, `events.csv` row, log line, `timeline.json`
  node. This is the cross-link the review asks for.
- **`event_key`** — a deterministic hash over (event type, universe,
  bar open time, direction, the event's defining levels rounded to point
  precision). Same configuration, same data → **same key in a different
  run**.

Why the second one matters: a run-scoped counter cannot survive a re-run.
If a candidate build produces one extra pulse, every later event's number
shifts and a naive comparison reports a hundred differences where there is
one. `event_key` lets `visual_compare` align two runs event-by-event, and
report *"one event present in candidate, absent in baseline"* instead of
noise. Alignment by key, ordering by uid.

Hash: FNV-1a-32, same as `SQX_Normalise()`, so the project has one hashing
convention and not two.

### D27 — Causality is emitted, not inferred; `timeline.json` is derived

Adopted, with one correction that matters.

Only the EA knows that pulse #41 caused sequence step #43. Python cannot
reconstruct that from a flat CSV without guessing, and a guessed causal
graph is worse than none. So:

- `events.csv` gains three columns: `parent_uid`, `producer`
  (which subsystem emitted it — EntryGates, SequenceEngine, TradeManager,
  VirtualBook), `consumer` (which subsystem acted on it, when known).
- `timeline.json` is **built by `npexp` at bundle close** from
  `events.csv`. It is a view: parent/children, trade id, subsystem chain.
- **`events.csv` is the source of truth.** If the two ever disagree,
  `timeline.json` is wrong and is regenerated. It is never hand-edited,
  and nothing is stored in it that cannot be rebuilt.

Cost control: the EA emits one parent id per event. It does **not** build
or hold a graph at runtime. Graph work happens offline, where it is free.

### D28 — Event dictionary, starting now

`tests/events/dictionary.json`. One entry per event type:

```json
{
  "id": "PULSE_BIRTH",
  "version": 1,
  "since_ea": "5.10.0",
  "category": "gate",
  "severity": "info",
  "description": "A B1-B6 / T1-T9 gate turned true on a closed bar.",
  "fields": ["gate", "universe", "trigger_level", "bar_time"],
  "produced_by": "EntryGates",
  "typical_consumer": "SequenceEngine"
}
```

Rules:

- An event type not in the dictionary appearing in a stream flags the
  bundle `UNKNOWN_EVENT` and the validator refuses `COMPLETE`.
- Adding or changing an event requires a dictionary edit **in the same
  commit** as the EA change. This mirrors the rule already used for the
  sanctioned-residual `EG_` reader list in the phase ledger, so the
  project has one habit, not two.
- Changing an event's fields bumps its `version`. Bundles record the
  dictionary version they were captured against.

The file is created empty at A1 and filled as events are implemented. It
costs nothing now and prevents an inconsistent vocabulary later, which is
precisely the reviewer's point.

### D29 — Bundle validator (quality control, no AI)

Runs automatically when a bundle is closed, before anything is reported:

- every artefact named in `manifest.json` exists and is non-zero
- every artefact present is named somewhere (no orphans)
- SHA-256 recorded for each file; recomputed on validation
- `visual/index.json` agrees with the PNGs on disk
- every `event_uid` referenced by an image or object row exists in
  `events.csv`
- unknown event types → `UNKNOWN_EVENT`
- NAVFAIL ratio; if no valid images exist, `VISUAL: NO VALID EVIDENCE`

Stamps `bundle_status`: `COMPLETE` / `INCOMPLETE` / `CORRUPT`. An
`INCOMPLETE` bundle may not be promoted to golden and may not be used as a
regression baseline.

This is ~150 lines of Python and belongs in **A2**, not in a later stage.
It is the cheapest guard in the whole design.

### D30 — The AI explains a located difference; it never searches for one

Adopted, with a constraint that is not optional.

Giving a model a whole bundle and asking *"why did this regression fail?"*
produces a confident, fluent story. On 15–18 trades, most such stories are
explanations of noise — the exact failure ADR-004 was written to stop.

So the contract is fixed:

- The deterministic layers run **first**: deal-list diff, `objects.csv`
  diff, metric tolerances, event alignment by `event_key`.
- Their verdicts are **inputs** to the AI, not questions for it.
- The prompt is *"the deal list diverges at deal #12, 2026-03-11 09:31,
  universe TrendPullback_Fibo; the objects diff shows trigger_level moved
  0.35; here is the surrounding evidence — explain this divergence"*.
- The prompt is never *"find what is wrong with this run"*.
- If the deterministic layers found nothing, the AI is not asked to find
  something. "No difference" is a complete answer.
- Model name, model version and prompt hash go in the manifest, or the
  output is discarded (D22 unchanged).

The AI's value here is real: it reads a large bundle quickly and writes
`analysis.md` in prose the owner can check. That is assistance. Judgement
stays deterministic.

### D31 — The Scientific Passport is generated, not authored

The idea is good. The usual implementation is a form, and forms rot — six
months in, "what question was this answering?" reads "testing changes" on
every one of them.

Nearly all of it already exists as structured data:

| Passport question | Source |
|---|---|
| What question? | `spec.purpose` (**human, required**) |
| What hypothesis? | `spec.predictions` → PREDICTIONS.md |
| What changed from last time? | computed: diff of spec + manifest vs `parent_run` |
| What evidence? | bundle inventory + `bundle_status` |
| What guardrails applied? | guardrail stamps already in the manifest |
| Outcome? | `summary.json` + regression verdicts |
| What remains unresolved? | **human, required** — plus auto-added `STILL OPEN (n<30)` items |

So `passport.md` is assembled at bundle close from things that already
exist, with exactly **two** free-text fields. New spec field `parent_run`
gives experiments a lineage chain, which also makes "what changed" a
computation instead of a memory.

Lands in **A3**, once spec + manifest exist. Not a new stage.

### D32 — Responsibility boundary (binding)

The Experiment Runner **executes experiments and preserves evidence.**

It does **not**: rank strategies, decide what to promote, hold project
knowledge, tune parameters, or run search. Those belong to the owner, to
the analysis layer, and to Phase 7's replay engine.

Any future capability must state which side of this line it sits on. If
it is on the far side, it does not go in the runner — no matter how
convenient it would be to put it there.

---

## 3. Changes to v1.1

1. §12 evidence model: the fourth category is renamed **Multimodal**
   (channel: visual). Bundle gains `timeline.json` and `passport.md`.
2. §13.2 event table: each row also carries `event_uid`, `event_key`,
   `parent_uid`, `producer`. The table itself becomes the seed of
   `tests/events/dictionary.json`.

Everything else in v1.1 stands.

---

## 4. Where the new work lands (no new stages)

- **A1** — create `tests/events/dictionary.json` (empty, with schema).
  Nothing else changes.
- **A2** — bundle validator (D29), SHA-256 per artefact, `bundle_status`.
- **A3** — `passport.md` generation, `parent_run` lineage in the spec.
- **A4.1** — `event_uid` + `event_key` + `parent_uid` + `producer` in
  `events.csv`; dictionary filled as events are implemented.
- **A4.3** — `timeline.json` derivation; the D30 prompt contract.
- **A5** — unchanged.

Stage count stays at five. That is deliberate.

---

## 5. Design freeze, and one honest observation

Three documents now exist for this system. Zero lines of it have been
written. The watcher itself is still not running on the machine — there is
no `C:\NeelPrajna\bridge\` folder as of today.

Two rounds of review have produced no disagreement with any substantive
claim in the design. That is pleasant and it is also low information. A
design's real score is unknown until it survives contact with the tester,
and the single highest-risk assumption in v1.1 — whether MT5 can draw and
screenshot in the tester at all — is still unanswered (spike A4.0, thirty
minutes).

Therefore:

- **No v1.3 before A1 ships.** New ideas go into a `PARKED.md` list, not
  into the design.
- The next artefact produced for this system should be **code**: A1, then
  the A4.0 spike.
- If a future review is wanted, the useful question is not "rate this
  document" but **"what breaks first, and what would you cut?"**

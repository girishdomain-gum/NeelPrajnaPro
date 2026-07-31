# WO-Q — ARO IMPLEMENTATION LADDER
*A backlog, not a design document. Seven milestones. Each adds **one permission**, has **one exit test**, has **one drill**, and can be switched off. Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30.*

> ## If ARO ever needs intelligence, the specification is wrong.
> Every time the orchestrator seems to need judgment, the fix is upstream in the spec — never a smarter orchestrator.

**No calendar.** The unit is *one permission per passed drill*, not per week. A milestone is not "due"; it is either drilled or not granted.

---

## The ladder

| | Permission granted | Done when | Off switch |
|---|---|---|---|
| **v0.0** | *(none — no code)* | preflight checklist run before G1 | don't run it |
| **v0.1** | READ the repo | `status.json` is correct on a dirty tree | delete the file |
| **v0.2** | RENDER | `STATUS.md` readable in one screen | stop rendering |
| **v0.3** | MOVE work orders | `waiting/ → inbox/` only when inputs exist | revert the moves |
| **v0.4** | ASSEMBLE packets | one file per Owner decision | delete the packet |
| **v0.5** | CREATE work orders | next WO from completion event | delete the WO |
| **v0.6** | RECOVER leases | expired lease returns to inbox, once | disable the reaper |

**Nothing on this ladder ever writes to `datastore/**`, `docs/**`, `configs/hypotheses/**`, `qrf/**`, `ivf/**`, or `.github/**`.** That is a hard write-scope refusal at every level, not a convention.

---

## v0.0 — PREFLIGHT CHECKLIST *(no code; do this first, it is the highest-value item here)*

Run before G1. Every line is a yes/no with a path. A NO is a blocker, not a note.

**Data**
- [ ] the scope name exists and is registered
- [ ] the dataset is ingested, with a manifest, and its row count is recorded
- [ ] timestamps are int64 ns UTC, and the source timezone is stated

**Registration constants**
- [ ] cost model exists in `configs/venues.yaml`, by exact name
- [ ] lineage slug matches the convention in existing `configs/hypotheses/*.yaml`
- [ ] family string is identical across every registration this sprint
- [ ] expected trial count is written down, and the deflated bar computed from it

**Capability**
- [ ] the engine can express the trade rule the hypothesis needs
- [ ] every specification needed this sprint is complete enough to reimplement (NP-D-012)

**Boundaries**
- [ ] the list of frozen documents is written down
- [ ] open findings carried in are listed

**Output:** `ops/preflight/PFR_<sprint>.md`, ending with `RESULT: GREEN` or a numbered blocker list.

---

## v0.1 — STATUS (read only)

**Build:** one script that walks the repo and writes `ops/aro/status.json`.

```json
{ "sprint": "NP-S2", "phase": "P2", "generated_at": "...", "head": "<sha>",
  "work_orders": { "running": [], "blocked": [], "waiting": [] },
  "owner_decisions_pending": [], "leases": [], "stop": false }
```

**Done when:** run it on a deliberately messy tree and every field is right.
**Drill (must pass before v0.2):** plant three faults separately — an expired lease · a completed WO with no handover · a WO whose declared input file does not exist. **All three must appear in `status.json`.** If it reports a clean sprint on a dirty tree, no permission is granted.
**Off switch:** delete the file. Nothing depends on it.

## v0.2 — DASHBOARD (render only)

**Build:** `ops/aro/STATUS.md` generated from `status.json`. One screen. What phase · what's running · what's blocked · what's waiting on the Owner · stop state.
**Done when:** you can answer "where is the sprint" without opening a log.
**Drill:** kill the generator mid-write; the next run must produce a correct file, not a torn one.
**Off switch:** stop rendering; `status.json` still works.

## v0.3 — MOVE (first write permission)

**Build:** promote `waiting/ → inbox/` when **every declared input path exists**. Existence only.
**Done when:** a WO with a missing input stays in `waiting/`, and one with all inputs present moves.
**Drill:** point a WO at a non-existent input. **It must refuse to promote.** A promotion on a missing input is a failed drill.
**Off switch:** `git revert` the moves — they are ordinary commits.

## v0.4 — PACKET

**Build:** render one file per Owner decision into `ops/aro/queue/owner/decisions/pending/`.
**Done when:** each file is self-contained — decide, why you, evidence links, what happens either way, typed wordings.
**Drill:** feed it two decisions. **It must produce two files, never one bundled file.**
**Off switch:** delete the packet; the underlying escalation record remains.

## v0.5 — CREATE

**Build:** on a completion event, create the next WO from the declared template.
**Done when:** a completed WO produces exactly one successor in the right role's inbox.
**Drill:** present a completion with **no handover file**. **It must refuse and mark the WO blocked.** A completion without a handover is not a completion.
**Off switch:** delete the created WO.

## v0.6 — RECOVER

**Build:** expired lease → return WO to `inbox/`, log a timeout, decrement the retry budget.
**Done when:** a killed session's WO becomes claimable again without a human touching it.
**Drill:** replay the same expiry event twenty times. **Exactly one action must result.** Idempotency is the whole test.
**Off switch:** disable the reaper; leases simply persist.

---

## Rules that apply at every rung

1. **One permission per milestone.** If a milestone needs two, it is two milestones.
2. **Drill before grant.** A permission is earned by catching planted faults, never by working once.
3. **Reversible.** Every rung is switchable off, leaving the system usable at the rung below.
4. **Refusals over cleverness.** When in doubt, ARO refuses and escalates. A refusal is cheap; a wrong action is a finding.
5. **Silence is negative.** No heartbeat means stale, not fine.

## Accountability (unchanged by this ladder)

Sprint design → Architect · scientific validity → Chief Scientist · code correctness → Developer · verification → Validator · ratification and priorities → Owner. **Operational execution stays with the Architect, with ARO as the instrument** — findings attach to whoever built, invoked or trusted the machinery, never to a script.

## What this ladder is not

It does not reduce the Owner's judgment load. That floor — human confirmation, ratifications, designations, Go/No-Go, arming — is roughly four to six touches per sprint, and it is the system working. **The lever for judgment load is the rulebook, not the plumbing:** after each Owner decision, ask whether a rule could have made it mechanical.

---
*Anchor: **each rung buys one permission with one drill, and every rung can be switched off without stopping the sprint.***

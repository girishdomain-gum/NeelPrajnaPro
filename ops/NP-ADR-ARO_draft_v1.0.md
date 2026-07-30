# NP-ADR-0XX — The Research Orchestrator (ARO): Realization of QRF-ADR-010b Phase C
*WORKING RECORD — DRAFT v1.0 for Chief Scientist review and Owner ratification (Constitution §7.3 path: amends the ratified Roles document; adds architecture row 13). Number **0XX deliberately unassigned** pending a registry check against docs\archive\gen1\adr\ — collision discipline per NP-D-006 (the ARCH-011 lesson). Author: Fable (Architect), 2026-07-30. Evidence base: ops\ARO_Architecture_Review_NP.md (accepted working input per Owner mandate). Companion: ops\OWNER_PACKET_ARO_ratification.md.*

---

## §1 · The ADR proper

**Purpose.** Introduce the ARO — a coordination plane that machine-carries every arrow of the ratified sprint rhythm (dispatch, routing, queueing, mechanical-invariant watching) so that the Owner's remaining touches are judgments only.

**Rationale (condensed from the review; full evidence there).** Execution is automated; orchestration is not — the Owner is the message bus (five relay touches in one day of NP-S1, none of them judgment). The capability was ratified in Gen-1 as QRF-ADR-010b Phase C ("orchestrated cycle + Owner packet") and never scheduled — the F-24 species. The Automation Plan's own success metric (judgment fraction of Owner touches → 100%) demands exactly this layer.

**Architectural consequences.** One new §A.1 row (13, coordination plane — infrastructure, not an organ); no change to the two-organ diagram, the wall, the §2.1 write-authority closed list, Contract v2, or row 8's scope; the ratified Roles document gains one non-voice machinery definition; the Automation Plan gains an orchestration layer distinct from its execution layer plus one honesty correction to §3.

**Alternatives considered and rejected.**
1. *Widen row 8 (Continuous Communication) to cover the SDLC.* Rejected: row 8 is a ratified runtime-platform box scheduled for NP-S5; widening a sealed box's meaning mid-flight makes one term mean two things — definition rot.
2. *Ad-hoc scripts per sprint (status quo plus).* Rejected: leaves the arrows unowned; every sprint re-invents routing; no certification, no heartbeat, no packet; the Owner remains the courier of last resort.
3. *Give the Developer a standing orchestration session.* Rejected: violates fresh-session-per-task (Constitution §5.3), concentrates state in a session instead of the repository (ADR-008), and mixes a voice's mandate with transport.
4. *A third-party workflow engine as authority.* Rejected: external state store competes with the repository as source of truth (ADR-007/008); tooling *may* be used internally, but repo files remain the only authoritative state.
5. *Full autonomy without phases.* Rejected by rule: ADR-010b's phases and Owner gates are binding; an ungated autopilot is the failure mode the estate wrote R-1..R-7 against.

**Compatibility, verified line by line.** *ADR-010b:* the ARO is its Phase C, inheriting phases, reversibility, Owner drills, budget caps, heartbeat-or-STALE, write-refusals verbatim. *Constitution:* §6 untouched — every permanently-human power appears in §6 of this ADR as an unconditional escalation; §5 amended only by adding non-voice machinery; the Twelve Principles constrain the policy table (P2, P11 explicitly). *Architecture:* §2.1's closed write list unchanged — the ARO holds **zero** write authority to ledger, verdicts, windows, trials, beliefs; it writes only its own operational files (§7).

**Migration strategy.** §10 (O0→O3), each stage independently useful, each Owner-gated.

---

## §2 · Architecture Row 13 — full definition (replaces "merely add a row")

**Row 13 · Automation — Research Orchestrator (ARO, coordination plane) · Status TARGET · Delivered by O-track (§9).**

- **Purpose:** carry the arrows of the ratified rhythm; assemble the Owner Packet; watch mechanical invariants.
- **Responsibilities:** event watching · lane sequencing per the sealed rhythm (order fixed, no skip/reorder) · role-session dispatch with correct boot artifacts · question/review routing with verbatim attribution · Owner Packet assembly · fingerprint and register preflights (hard stop on mismatch) · heartbeat publication · append-only operational logging.
- **Inputs (repo files only):** sealed ARCHs · DEVQ files · IVF/HC/REV outputs · CI results · bridge job status/manifests · journal · detector manifests/fingerprints (per the companion detector-identity ADR).
- **Outputs (operational files only, §7):** dispatch records · routing notices · OWNER_PACKET.md · heartbeat/state · auto-findings for mechanical violations only.
- **Interfaces:** filesystem events (ADR-008 lanes, extended per §4) · bridge mailbox (job submission/harvest, typed jobs only — D1) · session launcher (boot-artifact dispatch) · CI status reader. No network beyond least-privilege local (ADR-010b no-web constraint).
- **Events:** catalogue §4. **Dependencies:** repository as sole state (ADR-007/008) · Supervisor pairing (G-1..G-7) · detector-identity ADR artifacts for the fingerprint preflight.
- **Failure behaviour:** silence is negative; unrecognized state/schema → lane STALE + escalate, never guess (G-2); dead ARO → heartbeat STALE loudly within budget; event storm → idempotency keys, single-flight per lane; conflicting repo state → repo wins, lane halts, finding.
- **Recovery behaviour:** rebuild entire state from repository scan (state files are cache, never truth); interrupted dispatch re-verified against manifests before any retry; at-most-once side effects proven by dispatch manifests (D4: no manifest, no dispatch).
- **Interaction with every existing box:** rows 1 (Battery/WindowLedger) — submits nothing, overrides nothing; reads verdict/burn records as events; surfaces WindowLedger refusals in the packet. Row 2 (Scientific Memory) — read-only. Row 3 (Observation Engine) — none at runtime; dispatches the sessions that build it. Row 4 — read-only. Row 5 — reads Performance-Store landing events (NP-S2+) for sequencing only. Row 6 — dispatches certification-drill sessions; never interprets results. Rows 7–8 (Contract v2) — **no interaction, permanently**: the coordination plane and the organs' nervous system never touch. Row 9 (Knowledge Graph) — read-only; may open a routed task when contradiction records appear (a human weighs them, per NP-S6's own rule). Row 10 — none until Gate A, then still transport-only. Rows 11–12 (surfaces) — the Research Console GOVERNANCE lens may *display* ARO state (read-only view onto operational files); dashboards never consume ARO data as knowledge.

---

## §3 · Responsibility Matrix

**Per-party (SHALL / SHALL NOT / MAY — existing voices unchanged; column states only what this ADR adds or re-affirms):**

| Party | SHALL (under ARO) | SHALL NOT | MAY |
|---|---|---|---|
| **ARO** | watch, sequence, dispatch, route verbatim, assemble packet, hard-stop on mechanical violations, log append-only, go STALE on ambiguity | answer/author/judge anything; skip or reorder rhythm; soften or summarize in transit; write scientific records; touch ivf/**, CI, normative docs; escalate non-judgments to Owner | batch notifications; retry within budget; open routed look-at-this tasks (authored by no one) |
| **Owner** | judge packet items; run ADR-010b drills; gate each O-phase | be asked to relay, run, or route (each such ask = ARO defect + finding) | pause/kill the ARO at any moment, no cause needed |
| **Architect** | answer routed DEVQs; seal ARCHs (the dispatch triggers); own IVF as today | delegate any authorship to the ARO | annotate packet items with recommendations (marked as such) |
| **Developer** | verify own preconditions from repo at boot (defense in depth against wrong dispatch); DEVQ on any oddity incl. suspected mis-dispatch | treat an ARO dispatch as overriding its sealed instruction — the ARCH text always wins | — |
| **Chief Scientist / Independent Reviewer / Research Analyst** | receive bundles via routing; return reviews as files | — (relay-only status unchanged) | flag ARO behavior itself for findings |
| **IVF** | run when dispatched, drill-first as always; RED freezes the lane (now machine-enforced) | accept ARO state as evidence of anything | — |
| **HC** | receive assembled bundles; human eyes mandatory (ADR-009b) | be replaced by ARO assembly | — |
| **REV** | file to its lane; filing is the packet trigger | — | — |
| **Bridge** | execute typed jobs the ARO submits, exactly as for humans | accept any new job type from the ARO (D1: typed jobs only, unchanged) | — |
| **Battery / WindowLedger / BeliefLayer / Knowledge Graph** | behave identically whether a human or the ARO sequenced the surrounding steps | expose any override path to the ARO | — |
| **Repository** | remain sole source of truth; ARO state rebuildable from it | — | — |
| **CI** | publish status the ARO reads | grant the ARO write access to workflows | — |

**Per-interaction (owner / trigger / consumer / override):**

| Interaction | Owns it | Triggers it | Consumes it | May override |
|---|---|---|---|---|
| ARCH sealing | Architect | Architect | ARO (dispatch), Developer | Owner (withdraw before Go) |
| Developer dispatch | ARO | ARCH_SEALED | Developer session | Owner/Architect (cancel lane) |
| DEVQ routing | ARO | DEVQ_OPEN | Architect (or Owner if §6-class) | no one — routing is mandatory |
| DEVQ answer | Architect (Owner for §6) | human | Developer via ARO | Owner |
| IVF dispatch | ARO | BUILD_COMPLETE | IVF | Architect (hold for cause, recorded) |
| Verdict + burn | Battery | Battery's own run | ledger; ARO reads as event | **no one, ever** |
| HC bundle | ARO assembles; HC owns judgment | VALIDATION_COMPLETE | human reviewer | — |
| Owner Packet entry | ARO | REVIEW_COMPLETE / any DECISION_REQUIRED | Owner | Owner (dismiss with reason, logged) |
| Go/No-Go | **Owner** | Owner reads packet | ARO (records event, dispatches retro) | no one |
| Auto-finding (mechanical) | ARO raises; tally is Owner's | FINGERPRINT_MISMATCH / REGISTER_DIVERGENCE | journal via routed task to Architect for recording | Owner (may reclassify, never delete — P5) |
| O-phase advancement | Owner | Owner typed decision | ARO config | Owner |

---

## §4 · Event Catalogue

Transport: files in ADR-008 lanes; an event is a file appearing/changing at a named path with a canonical JSON payload; `event_uid` (unique) + `event_key` (semantic, for idempotency) per D26. Common payload: `{event, uid, key, ts, actor, refs[], sha}`. Defaults unless overridden below: timeout → lane BLOCKED + packet entry; retry: transient I/O only, 3 attempts, exponential, budget-capped; escalation: anything unresolvable → OWNER_PACKET; **no event is ever auto-answered.**

| Event | Publisher | Subscribers | Payload extras | Required ARO action | Timeout | Retry | Escalation |
|---|---|---|---|---|---|---|---|
| ARCH_SEALED | Architect | ARO, Developer | arch_id, boot_artifact | dispatch Developer lane | — | — | — |
| DEVQ_OPEN | Developer | ARO, Architect | devq_id, blocking_lane | halt lane; route; start answer-clock | answer-clock (config) → packet nudge | — | §6-class content → Owner queue directly |
| DEVQ_RESOLVED | Architect/Owner | ARO, Developer | devq_id, answer_ref | resume lane; deliver verbatim | — | — | — |
| BUILD_COMPLETE | CI (green on lane branch) | ARO | commit, test_report | dispatch IVF (drill-first flag set) | — | — | red CI ≠ event; see FAILED state |
| VALIDATION_COMPLETE | IVF | ARO, HC | ivf_report, GREEN/RED | GREEN → assemble HC bundle; RED → freeze lane + packet | — | — | RED twice → forward-work freeze (ADR-006), packet CRITICAL |
| BATTERY_COMPLETE | Battery (ledger record observed) | ARO | verdict_ref, window_burn_ref | refresh generated state; sequence next step; packet info-entry | — | — | never interpreted |
| REVIEW_COMPLETE | REV filer | ARO | rev_ref | assemble packet decision-entry | — | — | — |
| OWNER_DECISION | Owner | ARO, all | decision, wording_ref | record; dispatch consequent lane (GO→retro; NO-GO→halt+retro) | — | — | — |
| GO_GRANTED / GO_REJECTED | Owner | ARO | sprint_id | as above | — | — | — |
| WINDOW_BURNED | WindowLedger record | ARO | window_ref | surface in packet; verify expected lane caused it — unexpected burn = CRITICAL escalation + auto-finding | — | — | immediate |
| REGISTRATION_CREATED | registration flow (ledger) | ARO | yaml_ref, fingerprint | preflight check: fingerprint & cost-model name known; mismatch → FINGERPRINT_MISMATCH | — | — | — |
| FINGERPRINT_MISMATCH | ARO preflight | Owner, Architect | expected/actual | **hard stop lane** + auto-finding + packet CRITICAL | — | none | immediate |
| REGISTER_DIVERGENCE | WO-D check | Owner, Architect | diff | auto-finding + packet | — | — | immediate |
| JOB_DONE / JOB_FAILED | Bridge | ARO | run_id, manifest | harvest by run id; sequence or FAILED-path | watchdog-inherited | bridge-native | repeated fail → packet |
| SPRINT_CLOSED | Owner GO + retro filed | ARO | outputs_ref | dispatch handover-rewrite task to Architect; archive lane | — | — | — |
| RETRO_COMPLETE | Architect | ARO | retro_ref | emit SPRINT_CLOSED prerequisites check | — | — | — |
| ARO_STALE | Supervisor/heartbeat | Owner, all | last_beat | none (it is the escalation) | — | — | by definition |

---

## §5 · State Machine (per lane / work item)

States: **WAITING** (preconditions unmet) · **READY** · **DISPATCHED** (manifest written, session/job launched) · **RUNNING** · **BLOCKED** (DEVQ or dependency) · **ESCALATED** (needs a voice, not the Owner) · **OWNER_REVIEW** (in the packet) · **RETRY** · **TIMEOUT** · **FAILED** · **RECOVERY** · **CANCELLED** · **COMPLETED**.

Transitions (complete; anything not listed is illegal and → ESCALATED with reason `illegal_transition`):
- WAITING→READY: all preconditions observed in repo. READY→DISPATCHED: single-flight lock acquired + dispatch manifest written (no manifest, no dispatch). DISPATCHED→RUNNING: session/job heartbeat or first output observed. DISPATCHED→TIMEOUT: no liveness within budget.
- RUNNING→BLOCKED: DEVQ_OPEN. BLOCKED→RUNNING: DEVQ_RESOLVED. BLOCKED→OWNER_REVIEW: answer-clock expiry (nudge, not answer).
- RUNNING→COMPLETED: lane's completion event with all required artifacts present. RUNNING→FAILED: completion event absent + failure signal (red CI, NAVFAIL-style self-invalidation, job FAILED). RUNNING→TIMEOUT: liveness lost.
- TIMEOUT→RETRY: transient class + budget remaining. TIMEOUT→ESCALATED: otherwise. RETRY→DISPATCHED: idempotency verified (event_key single-flight; prior manifest reconciled). RETRY→FAILED: budget exhausted.
- FAILED→ESCALATED: always (a failure is never silently retried into success without a record). ESCALATED→OWNER_REVIEW: only if the needed authority is §6-class; else routed to the accountable voice and →BLOCKED on their answer.
- OWNER_REVIEW→READY / →CANCELLED / →COMPLETED: per the Owner's recorded decision. CANCELLED: terminal; lock released; record kept (P5).
- Any state→RECOVERY: ARO restart; RECOVERY→(recomputed state): full repo rescan; in-doubt dispatches verified by manifest before any transition out. IVF RED-twice: lane→FAILED and **all forward lanes→WAITING(frozen)** per ADR-006.
- COMPLETED: terminal per item; emits its completion event.

---

## §6 · Escalation Policy

**Decides automatically (transport-class only):** sequencing per the sealed rhythm · dispatch/harvest · routing destinations (mechanical, by event type) · packet assembly · transient retry within budget · duplicate suppression · preflight hard stops (fingerprint, register divergence, unexpected burn) · generated-state refresh.

**Escalates to the accountable voice (not the Owner):** compile errors and red tests → Developer lane FAILED→Architect visibility (a red test is work, not a judgment) · missing/ambiguous documents → routed task to the owning voice · ADR conflicts detected mechanically (two docs claiming one thing) → Architect, as a candidate finding · scientific disputes of any kind → the voices; the ARO has no opinion to contribute.

**Escalates to the Owner, always and unconditionally (§6-class):** every Constitution §6 power (VIRGIN acts · verdict-adjacent anything · freezes/amendments · α-budgets · promotion/arming · the findings tally) · Go/No-Go · window designations · ratifications · DEVQs whose content touches values or §6 · constitutional questions · any O-phase change · any request to modify the ARO's own policy table · **any situation the ARO cannot classify** (the residual clause: unclassifiable = Owner packet, never a guess).

**Never escalated because never ARO business:** the *content* of answers, reviews, verdicts, and rulings — the ARO carries them verbatim and forms no view.

---

## §7 · Operational Metadata (owned by ARO; zero epistemic standing)

Location: `ops\aro\` — deliberately **outside** `datastore\` (the ledger's home) so no operational byte can be mistaken for a scientific record. Files: `state.json` (cache; rebuildable) · `queue.jsonl` · `dispatch.log.jsonl` (append-only, manifests inline) · `routing.log.jsonl` · `retry.log.jsonl` · `notify.log.jsonl` · `heartbeat.json` · `OWNER_PACKET.md` (the one human-facing file) · per-lane lock files. Rules: append-only where a log; never cited as evidence by anything (a citation of ops\aro\ in any scientific artifact is a finding); never a second journal (NP-D-009 — the journal remains the only log *of record*; these are machine artifacts); ARO write scope is **exactly this directory plus routed-task files in ADR-008 lanes**, enforced by the same refusal discipline as the Developer's ivf/** ban. The immutable list the mandate names — evidence, beliefs, verdicts, registrations, Constitution, Architecture, ADRs, WindowLedger, Battery outputs — is restated here as a hard write-deny, tested in certification (§8 tamper drill).

---

## §8 · Certification Plan (trust like an instrument)

- **Unit:** event parser (malformed payload → STALE, never guess) · state-machine transition table (every legal transition exercised; illegal transitions provably rejected) · idempotency (same event_key twice → one action) · write-scope guard (attempted write outside ops\aro\ → refusal + self-finding).
- **Simulation:** a full synthetic sprint (scripted voices emitting the §4 catalogue) run end-to-end; expected: every arrow carried, packet correct, zero human relays.
- **Fault injection:** corrupted event files · missing artifacts at dispatch time · repo lock contention · half-written manifests (torn-tail species) — each must land in ESCALATED/STALE, never in silent progress.
- **Drills:** *timeout* (kill a session mid-run → TIMEOUT path exact) · *lost message* (delete an event before processing → repo rescan finds truth) · *duplicate event* (replay storm → single-flight holds) · *replay* (full recovery from repo alone with state.json deleted → identical recomputed state, byte-compared) · *recovery* (kill ARO mid-dispatch → manifest reconciliation, no double work) · **planted-escalation drill** (synthetic §6-class items disguised as routine → 100% must reach the packet; one auto-action = certification FAIL) · **Owner drills** per ADR-010b (planted defects the Owner must catch; a miss pauses autopilot).
- **Certification criteria:** all above green in one unbroken campaign per phase (VV §1 nesting applies); certification is per-phase (O1 certifies watching; O2 adds dispatch drills; O3 adds full-cycle simulation).
- **Failure criteria (immediate de-certification):** any auto-answer of any question · any write outside scope · any softening/reordering detected in transit (byte-compare routing test) · silent progress past a fault injection.
- **Re-certification triggers:** any ARO code change · any rhythm change · any policy-table change (which itself requires Owner sign-off) · any new event type — VV §4.4 verbatim: certificates void, drills re-run clean.

---

## §9 · Sprint Planning (Execution Plan integration — NP-S1 untouched)

O-track runs **parallel** to the scientific ladder; it never sits on a scientific sprint's critical path until certified; NP-S1 proceeds exactly as sealed, ARO-free.

| Stage | Vehicle | When | Content |
|---|---|---|---|
| **O0** | No sprint — adopted by this ADR's ratification | immediately | conventions only: `ops\aro\OWNER_PACKET.md` + event-file naming; humans use them manually; zero code |
| **O1** | **WO-E** (new work order, Automation Plan §6) | alongside NP-S2 | watcher: routing, packet assembly, WO-D check, fingerprint preflight; **dispatches nothing**; O1 certification campaign |
| **O2** | **NP-O2** (small dedicated sprint) | at the NP-S2→NP-S3 boundary, gated on O1 observed across one full sprint + Owner gate | autonomous dispatch of Developer/IVF lanes; O2 certification |
| **O3** | **NP-O3** | after NP-S4 acceptance (the blinded campaign runs under human orchestration — answer-key custody stays clean) + Owner gate | full cycle + Owner drills armed; the two success numbers reported per sprint thereafter |

## §10 · Migration Strategy (each stage independently useful)

**Current** (Owner = bus) → **O0**: judgment queue unified in one file — useful even if everything else is rejected → **O1**: relays vanish (routing + packet automatic); dispatch still human — useful standalone forever → **O2**: dispatch automatic; Owner touches = designations + packet → **O3**: fully orchestrated cycle; Owner touches = pure judgment, drilled. Reversal at any stage = turn the watcher off; because all state is the repository, reversal loses nothing (ADR-008's "no AI is indispensable" applied to the ARO itself).

## §11 · Repository Changes (execute only after ratification, one write window)

| File | Section | Reason / change | New material |
|---|---|---|---|
| docs\architecture\…Architecture-v1.0.md (+docx twin, lockstep) | §A.1; new §10 "Coordination Plane"; Part C | add row 13 (full §2 definition by reference to this ADR); atlas caption | row-13 table row; §10 (~15 lines); caption |
| docs\vision\…Vision-v1.0.md | delivery table | +row 13, identical wording (spine rule) | one row |
| docs\execution_plan\…Execution_Plan-v2.0.md | §0 note; §6 (NP-S2 mention of WO-E); new §11 entries; O-track subsection | schedule O0..O3 per §9 | O-track table; WO-E line |
| docs\automation\…Automation-v1.0.md | §3 **honesty correction** ("every arrow… machine-executed" → accurate wording); new §8 Orchestration layer; §5 table gains relay-touch column; §6 +WO-E | required regardless of ARO verdict (F-17 species) | §8 (~20 lines) |
| docs\roles\…Roles…-v1.0.md | new §2.5 "ARO (non-voice machinery)"; §3 +machine-transport clause | the §7.3 trigger | §5-of-this-ADR content, condensed |
| docs\decisions\…Decisions-v1.0.md | Part 2 | append NP-D-0XX recording this ADR | one entry |
| docs\vv_plan\…VV_Plan-v1.0.md | new §6 "Orchestrator certification" | §8 content | drill tables |
| docs\journal\…Journal.md | append | ratification entry (Owner wording verbatim) | J-0XX |
| ops\aro\ (new) | — | O0 conventions: OWNER_PACKET.md, README of event naming | 2 files |
| CHANGELOG.md | — | via WO-A discipline | one line |
| Constitution | — | **no change** (verified) | — |

Diagrams: one new whiteboard-tier diagram (O-track ladder + coordination-plane placement) for the affected docx twins at their next rebuild — no organ diagram changes anywhere.

## §12 · Naming Evaluation (mandate's additional requirement)

Candidates: **ARO** (Owner's) · *Research Orchestrator (RO)* — drops "Autonomous," aligning with ADR-010b's "supervised" vocabulary · *Coordination Plane (CP)* — most architecturally literal, weakest as a component name · *Supervised Autopilot* — the lineage name, but names the governance envelope, not the component.

**Recommendation: keep ARO**, permanently, for three reasons: (1) it is already family-agnostic — nothing in "Autonomous Research Orchestrator" says NeelPrajna, so it serves every future concept family unchanged; (2) "autonomous" is *accurate at the layer it names* — the estate's own philosophy is autonomous operations inside a supervised envelope (Automation Plan §5), and the component is autonomous in transport while the envelope stays supervised; (3) renaming now churns an accepted review and mandate for a cosmetic gain. The one real risk — "autonomous" misread as "unsupervised" — is retired structurally, not lexically: the normative definition everywhere carries the subtitle **"Supervised Autopilot, Phase C (QRF-ADR-010b)"** and the one-sentence mission *"autonomous in transport, never in authority."* If the Owner prefers maximum conservatism, *RO* is the sanctioned fallback with zero other changes to this package.

---
*Anchor: **the ARO carries messages and dispatches work; it never has an opinion — autonomous in transport, never in authority.***

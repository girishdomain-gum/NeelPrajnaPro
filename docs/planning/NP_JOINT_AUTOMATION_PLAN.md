# NeelPrajna × QRF — Joint Automation Plan v1.0
*Complete operational automation for the integration work, on the ADR-005 line: operations automated to the maximum the machine allows; governance permanently human.*

Status: DRAFT — Architect proposal. Companion to NP_INTEGRATION_EXECUTION_ROADMAP.md and NP_INTEGRATION_VV_ACCEPTANCE_PLAN.md. Presentation copy: NP_JOINT_AUTOMATION_PLAN.docx.

---

## 1. Review verdict on the F:\NeelPrajna automation estate (live-verified 2026-07-29)

| Component | Documented | **Verified live state** |
|---|---|---|
| Automation bridge | AUTOMATION_BRIDGE.md (v1: 3 job types, `C:\NeelPrajna\bridge`) | **Agent v2.14.0, READY**, heartbeat 2 s fresh, mailbox at `F:\NeelPrajna\bridge`, 15 completed jobs incl. automated report screenshots, `preserve` job type and unpreserved-bundle tracking beyond the v1 doc |
| Supervisor/Runner trust split | SUPERVISOR_CONTRACT v1.1, owner-signed 2026-07-27 | **Supervisor 1.1.0 HEALTHY**, all 7 checks green with named value+threshold (G-7 honored), atomic publication, self+config SHA-256 attested (G-6), 310 GB free, 1 restart recorded — the contract is real in the artifact, not just on paper |
| Preflight & lab identity | Runner design v1.1 §10 (manifest identity) | **Preflight 1.5.0** publishing full lab identity: terminal/metaeditor hashed and versioned, data dir, deploy dir, deployed .ex5 hash and age — run identity is already being captured at the environment level |
| Experiment runner v2 | Design v1.1 + amendment v1.2 (design-frozen, D1–D32) | Partially built (agent far beyond v1); A-stage completion vs the staging plan to be confirmed; **A4.0 spike (can the tester screenshot at all?) remains the gating unknown for the full capture pass** |

**Verdict: adopt, don't redesign.** The v1.2 design-freeze clause stands — this plan schedules and applies the existing design; it does not amend it.

**Finding F-17 (docs lag reality — in the good direction):** AUTOMATION_BRIDGE.md still teaches `C:\NeelPrajna\bridge` and a 3-job v1 agent; the live system is at `F:\NeelPrajna\bridge` on v2.14.0. Design v1.1 §1's "honest reading" (bridge does not exist) is now false. A booting session following the doc would poll a dead path — precisely the dead-mailbox failure the doc itself warns about. Remedy: WO-A below. Same species as the QRF AI_PROJECT_STATE staleness; same class of fix.

## 2. The learnings adopted, by name

From the bridge and its design (verbatim into the joint work, no re-litigation):
- **Typed jobs only; no command escape hatch, ever** (D1). Executable paths in runner config, never in jobs.
- **Atomic hand-off, three-state lifecycle, watchdog, completion proven by multiple signals, harvest by run id** (D6–D9).
- **Every run produces a manifest or it is not a run; archive append-only** (D4, D5) — the automation-side sibling of the QRF ledger.
- **Guardrails travel with the automation** (§14): windows register with one-way BURNED, comparability refusal, n-floor honesty ("STILL OPEN — n=17 vs n=15", never a winner), predictions-file-older-than-run pre-registration check, fixed ranking order.
- **Multimodal evidence, correctly subordinated**: verdicts computed then drawn (D17); `objects.csv` text-diff as the deterministic regression instrument, images for humans and advisory AI (D20); no provenance, no capture (D14); NAVFAIL self-invalidation (D16); capture as a separate pass over `events.csv` (D19); event_uid + event_key dual identity (D26); causality emitted, never inferred (D27); **AI visual verdicts advisory only — PASS/REVIEW/SUSPECT, never a gate** (D22).
- **Supervisor constitution**: silence is negative, fail closed, never guess a schema, atomic publication, non-destructive, attested, traceable (G-1..G-7); firmware-style evolution; the freeze criterion.

## 3. The automation architecture of the joint work

Two execution surfaces, one philosophy:

| Surface | What runs there | Automation mechanism | Human touches (target) |
|---|---|---|---|
| **F:\QRF** (Python) | Detector build, registrations, Battery runs, IVF, drills, tests | Claude Code fresh sessions per ARCH-NP (ADR-008 rhythm) — already zero-touch for execution; Owner touches are git push/pull rhythm + rulings only | Rulings + Go/No-Go only |
| **MT5 lab** (MQL5/tester) | R6 collection runs, capture passes, any EA-side evidence | **The live bridge**: `experiment` / `capture` / `regress` / `preserve` typed jobs under the Supervisor | "Keep one window open" (and it starts at boot — 0 routine) |

The joint sprint loop, fully automated end-to-end:
`ARCH-NP sealed → Claude Code implements (QRF side) → bridge jobs execute (MT5 side) → evidence bundles assemble themselves → IVF re-derives → HC reviews the bundle → REV → Owner Go/No-Go.`
Every arrow except the last is machine-executed. The last is the point.

## 4. Sprint-by-sprint automation mapping

**NP-S1 (H-07 twice-judged).** Pure QRF-side; the bridge is not on the critical path. Claude Code runs detector, drills, registration, Battery, comparison unattended. **Cross-repo bridge use (new):** the historical `NP_Trades_*` exports feeding the mt5_csv adapter are produced/refreshed as bridge `backtest` jobs with run tags, so even the input data has a manifest. *Owner touches: the four sealed preconditions + Go/No-Go = 5.*

**NP-S2 (R6 long run).** The bridge's showcase. R6 executes as `experiment` jobs (spec-driven, windows named through the register, predictions-file age enforced), the watchdog guards the multi-hour runs, `preserve` archives bundles append-only, and the withheld OOS window enters both registers — `tests/windows.json` on the NP side and the QRF WindowLedger designation by the Owner's typed phrase — with an automated consistency check between the two (a divergence is a finding). *Owner touches: OOS designation (typed) + Go/No-Go = 2 across months of wall-clock.*

**NP-S3 (family migration).** Per-detector certification drills run as scripted QRF-side jobs; where a hypothesis needs fresh EA-side event evidence, the **capture pass** produces annotated, provenance-stamped, verdict-drawn PNGs from `events.csv` — the IVF_HC_Trades lineage coming home: QRF's HC layer receives multimodal bundles for NP detectors instead of raw CSV sampling alone. Gated on WO-B (the A4.0 spike). *Owner touches: the 17-hypothesis ruling + per-batch Go/No-Go.*

**NP-S4 (acceptance).** NB-1..NB-5 execute as queued jobs — synthetic dataset generation, blinded interleaving (the Owner holds answer keys), negative-control instrument runs, tamper drills on a sacrificial copy — and the stranger audit runs as a fresh session with repository read scope only. The Owner reviews assembled bundles and rules. *Owner touches: answer-key custody + acceptance ruling.*

## 5. The Owner touch budget (the honest definition of "minimal human involvement")

Per ADR-005, restated for the joint work: **routine operational touches target zero and every exception is logged and counted; governance touches are not minimized — they are the system.** The permanently-human list is unchanged and un-shrinkable: ratifications and freezes · VIRGIN designation/unlock and BURNED marking · α-budgets · verdict authority · promotion and golden-run status · arming anything real (live charts, InpSeq_LiveApply, Auto-Adopt, orders, deletion) · the findings tally · Go/No-Go. An automation proposal that would remove one of these is refused by rule, not debated per case.

| Sprint | Routine ops touches | Governance touches |
|---|---|---|
| NP-S1 | 0 | 5 (four preconditions + Go/No-Go) |
| NP-S2 | 0 (agent self-starts) | 2 (OOS designation, Go/No-Go) |
| NP-S3 | 0 | 2–4 (ruling + Go/No-Go per batch) |
| NP-S4 | 0 | 3 (answer keys, acceptance ruling, boundary rulings) |

## 6. Work orders (pre-sprint, small, sequenced)

- **WO-A — Documentation truth pass (½ session).** Rewrite AUTOMATION_BRIDGE.md against agent v2.14.0 reality (paths F:\, current job types, supervisor pairing); mark design v1.1 §1's stale reading corrected by appended note; fold the same refresh discipline into F:\QRF's AI_PROJECT_STATE hand rows and README/CHANGELOG (closes the Volume III §7 and F-17 species together). Exit: a cold session booting from docs alone reaches the live heartbeat first try.
- **WO-B — The A4.0 spike (30 min, decisive).** Answer the design's own single gating unknown: can `ChartScreenShot` + object drawing work under the tester at all, and if not, certify the decoupled post-run capture path as the only path. Everything visual in NP-S3/S4 sequences behind this answer.
- **WO-C — Cross-repo evidence linkage (1 session).** One field each way: bridge manifests gain the QRF record ids their data fed (`qrf_records: [...]`); QRF NP-family registrations gain the producing run's manifest path. A claim's chain of custody becomes walkable in both directions, machine-checked in IVF.
- **WO-D — Windows-register consistency check (small).** Automated comparison of `tests/windows.json` vs QRF WindowLedger designations for shared market time; divergence is a tallied finding, not a log line.

## 7. Standing boundaries (restated so automation never erodes them)

The bridge's human-only list, the D22 advisory ceiling on AI visual verdicts, the Supervisor freeze criterion, and Constitution v2.0 §6 apply jointly and permanently. Speed is an operations property; authority is not. The measure of this plan's success is two numbers moving in opposite directions: routine touches per sprint toward zero, and the fraction of Girish's remaining touches that are pure judgment toward one hundred percent.

---
*Anchor: **automation may build and measure everything; only the Owner arms, designates, and signs — and the day that line blurs is the day the automation has failed, however fast it runs.***

# PARKED — ideas held until the current milestone ships

Rule (design freeze, amendment v1.2 §5): after a design is frozen,
**implementation discoveries may change the design; speculative
improvements may not.** A speculative improvement goes here, with a date
and one line of reason, and waits.

Scope: the Automation v2 experiment runner only. Project-level parked work
lives in the phase ledger and the boot prompt.

Unpark rule: an item leaves this file when the stage it belongs to starts,
or when implementation evidence shows it is now the cheapest fix for a
real problem. Not because it is still a nice idea.

| Date | Item | Why parked |
|---|---|---|
| 2026-07-27 | Video / audio / heatmap / 3D evidence channels | D25 — named, but no use case exists. No structure built until one does. |
| 2026-07-27 | AI review of the whole evidence bundle beyond the D30 contract | Allowed only to explain a located difference. Wider use waits until deterministic layers are proven. |
| 2026-07-27 | Evidence Reviewer as an AI role | D29 ships as plain quality control first. If deterministic validation turns out to be insufficient, revisit with the evidence. |
| 2026-07-27 | Web dashboard for the runner | Results are read as text by Claude and by the owner. No evidence value yet. |
| 2026-07-27 | Broker / symbol matrix testing | XAUUSD on one broker is not yet understood. Also breaks regression baseline comparability. |
| 2026-07-27 | Parallel terminals | A5. Blocked on run tagging (shared `Common\Files` collision) and on per-terminal build differences. |
| 2026-07-27 | `optimise` job | A5, and gated behind Phase 7b acceptance. Mass search on 15–18 trades finds noise with certainty. |
| 2026-07-27 | `metatester64.exe` agent-based distributed testing | Present in the EXNESS install. Interesting for A5; irrelevant until one run is trustworthy. |

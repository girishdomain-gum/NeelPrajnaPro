# ADR-009 — Research Program Track (Generation 2+)

**Status:** Accepted · 2026-07-24 · Owner: Owner + Architecture

## Decision
QRF gains a fourth governing artifact: the **Future Research Program**
(docx, professional edition) with a living register at
`docs/research/RESEARCH_BACKLOG.md`. It captures scientifically
important questions that are intentionally OUTSIDE Generation-1 scope,
under a new ID class **RQ-NNN** and a fixed workflow:
Idea → RQ entry → discussion → prototype → experiment → evidence →
Architect review → ADR (if accepted) → generation roadmap.

## The one rule
Nothing in the research track changes Generation-1 architecture,
interfaces, or sprint scope unless supported by evidence AND an
approved ADR. Deep questions raised mid-sprint are triaged with a
single question: "Phase-1 implementation issue, or Generation-2
research question?" — and RQs go to the backlog, not into redesigns.

## Reason
Architecture churn is the classic failure mode of research software:
every idea becomes a redesign. The frozen architecture protects
delivery; the backlog protects curiosity. Freeze the interfaces, not
the thinking.

## Consequences
- ADR-001's artifact list gains the research program (unique
  responsibility: "what QRF may become and how that is investigated").
- The backlog is Architect-owned; the Developer may propose entries via
  NOTE (FYI) referencing a suggested RQ; the Architect registers them.
- Research prototypes live outside qrf/kernel and qrf/trading (e.g.
  experiments/) and never ship into sprints without the workflow above.
- Tone discipline: entries read like research proposals (question,
  motivation, experiment, evidence criteria) — never manifesto claims.

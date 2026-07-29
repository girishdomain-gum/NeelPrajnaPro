# NeelPrajna Programme — Documentation Index

**This file is the entry point.** Anyone — human or AI — opening this repository
cold should start here (the "no-dependency" / resurrection-test rule, carried
over from `HANDOVER.md`). If you read nothing else, read the "Read in this
order" table below and the one-paragraph map that follows it.

Written as part of the Documentation Re-architecture (see
`roadmap/MIGRATION_PLAN.md`, Phase 8). It reorganizes — and does not replace —
the existing body of ADRs, plans, and design docs, which keep their content
and simply move to a clearer home.

---

## The one-paragraph map

NeelPrajna is one programme with two halves. **Core** is the domain-blind
scientific Kernel (QRF): it knows how to judge a claim but not what the claim
is about. **Book A: NeelPrajna** is the first Application Book — the
domain-specific trading plug-in — a live, verified MQL5 Expert Advisor for
XAUUSD with its own gates, engine, dashboard, and shadow-universe research
subsystem (NPSU). **Governance** sits above both and is permanently human.
**Registers** hold the institutional memory (decisions and lessons) that
would otherwise evaporate. **Roadmap** is the one authoritative phase ladder.
Nothing here invents new philosophy — it gives an existing, hard-won practice
a permanent address.

---

## Read in this order

| You are... | Read | Skip on first pass |
|---|---|---|
| New to the programme | This file → `core/KERNEL_OVERVIEW.md` → `books/book-a-neelprajna/README.md` | Everything else |
| Designing a Core (Kernel) component | `core/KERNEL_OVERVIEW.md` + `core/COMMUNICATION_CONTRACT.md` + `core/EPISTEMIC_RULES.md` | `books/` until you need a concrete example |
| Designing or auditing a NeelPrajna (trading) component | `books/book-a-neelprajna/README.md` + `adr/ADR-001*.md` + `adr/ADR-003*.md` | Core internals |
| Implementing anything | The specific ADR or plan for your task + `governance/AUTONOMY_LADDER.md` §safety gates | Registers, until you need precedent |
| Reviewing the whole programme | Everything, in directory order below | Nothing |
| Resuming cold (no other context) | This file + `registers/DECISION_REGISTER.md` + `roadmap/PHASE_LEDGER.md` | — |

---

## Directory map

```
docs/
├── INDEX.md                         (this file)
├── DOCUMENTATION_ARCHITECTURE.md    the redesign itself: rationale + full old→new migration table
│
├── core/                            CORE — domain-blind QRF Kernel (never mentions XAUUSD)
│   ├── KERNEL_OVERVIEW.md              what the Kernel is, its components, the firewall
│   ├── COMMUNICATION_CONTRACT.md       the six objects + two prohibitions + Chief Scientist Principle
│   └── EPISTEMIC_RULES.md              R1–R3 and the evidence discipline, generalized from ADR-004
│
├── books/
│   └── book-a-neelprajna/           BOOK A — the trading plug-in (existing docs, relocated not rewritten)
│       └── README.md                   pointer map into the existing ADRs, plans, and design docs
│
├── governance/                      permanently human; never touched by an ADR alone
│   ├── SUPERVISOR_CONTRACT.md          (relocated from lab/, unchanged — frozen)
│   └── AUTONOMY_LADDER.md              L0–L3, operations/governance split (from ADR-005)
│
├── adr/                              one continuous numbering, Core and Books share it
│   ├── ADR-001 … ADR-007              (existing, unchanged)
│   └── ADR-008-kernel-trading-plugin-split.md   (new — ratifies the Core/Book split)
│
├── registers/                       institutional memory — new, filled from real history
│   ├── DECISION_REGISTER.md
│   └── LESSON_REGISTER.md
│
└── roadmap/
    ├── PHASE_LEDGER.md                (relocated, unchanged — the one ladder)
    └── MIGRATION_PLAN.md              how the reorganization itself is executed and gated
```

## What did NOT move

`tools/`, `Core/`, `Engine/`, `Apps/`, `Gates/`, `UI/`, `analyzer/`, `tests/`
keep their current locations exactly. This is a **documentation**
re-architecture only. No `.mqh`, `.mq5`, `.py`, `.set`, or `.ini` file changes
as a result of this plan.

## Standing rule

New documents are filed under exactly one of `core/`, `books/<book>/`,
`governance/`, `adr/`, `registers/`, or `roadmap/`. If a document does not
obviously belong in one of these six, that is a signal to fix the document's
scope, not to add a seventh folder.

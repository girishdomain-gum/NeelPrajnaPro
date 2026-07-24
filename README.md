# QRF — Quantitative Research Framework

A machine for finding out what is actually true about markets — built so
it cannot fool the person using it.

## Orientation (read in this order)
1. `docs/handover/AI_PROJECT_STATE.md` — where the project stands right now
2. `docs/implementation/Implementation_Blueprint_v1.0.md` — how to build it
3. `docs/implementation/Verification_Framework_v1.0.md` — how we prove it correct
4. `docs/architecture/` — what the system is and why (v1.1, FROZEN)
5. `docs/adr/` — every major decision, with reasons (10 minutes)
6. `CONTRIBUTING.md` — the executable constitution

## Layout
```
qrf/kernel/     domain-blind core: records, instruments, battery, belief...
qrf/trading/    the domain plug-in: adapters, simulator, costs, 17 concept families
ivf/            Independent Verification Framework (never imports qrf/)
tests/          mirrors qrf/; includes the kernel firewall test
configs/        venues, datasets, priors (YAML)
hypotheses/     pre-registered H-*.yaml (hashed into the ledger)
datastore/      journal/ (THE ledger) · bulk/ (parquet) · index/ (derived)
dashboard/      read-only Streamlit views
scripts/        gen_state.py, backup, utilities
docs/           architecture · implementation · adr · handover · reference
```

## Status
Documentation complete and frozen per ADR-001. Next: Sprint 1 (ledger core).

*Evidence before execution — concepts are temporary; knowledge is permanent.*

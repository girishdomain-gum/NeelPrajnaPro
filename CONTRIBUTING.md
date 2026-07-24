# Contributing to QRF

**The constitution of this codebase is executable.** Rules that matter
are enforced by tools, not prose. Before trusting anything written
here, trust what CI enforces:

| Rule | Enforced by |
|---|---|
| Kernel imports no trading code; no trading vocabulary in kernel identifiers | `tests/test_kernel_firewall.py` |
| IVF imports no qrf code | `ivf/tests/test_ivf_firewall.py` |
| Every payload validates against its schema before append | `kernel/records/schemas.py` + store tests |
| Every detector ships planted-pattern fixtures and passes calibration | calibration harness in CI |
| Environment is exact | `uv.lock` (commit it; `uv sync` reproduces) |
| Style/lint | `ruff` config in `pyproject.toml`; pre-commit hooks |

The few rules a tool cannot enforce:

1. **A module without its Blueprint-listed tests is not done.**
2. **Write an ADR** when a decision is hard to reverse, surprising, or
   rejects a plausible alternative. One file, `docs/adr/ADR-NNN-slug.md`,
   statuses: Proposed → Accepted → Superseded-by-NNN. Never delete.
3. **Notebooks are exploration only** — nothing a verdict depends on
   lives in one.
4. **When code and Blueprint disagree:** stop, write a `note` record,
   decide once, amend the Blueprint.
5. **Sprint close requires the IVF Go/No-Go** (IVF §8), including one
   planted-bug drill catch.

That's the whole document. If this page grows past one screen,
something that should be a tool has become prose.

# NOTE-007 · FYI · Sprint 2 close-out · 2026-07-24
Author: developer (claude-code)
Refs: ARCH-002A (IND-1: ivf/** is READ+RUN only, never edit); CI ci.yml
(`uv run ruff check .`); check_s2_detectors.py / drill_s2.py

## Discovery (no reply needed)
CI runs `ruff check .` over the whole repo. The Architect's IVF scripts
(`ivf/checks/check_s2_detectors.py`, `ivf/checks/drill_s2.py`) are written in a
deliberately terse, self-contained stdlib style — e.g. `import argparse, csv,
json, sys, time` on one line — which trips ruff's E401 (multiple imports) and
I001 (import sort). Four findings, all in `ivf/**`. They arrived on main with
the REV-S2 kit (be57423), so main's `ruff check .` was already red.

IND-1 forbids the Developer from editing anything under `ivf/**`, so I cannot
(and should not) reformat those files — the IVF's independence from the qrf
package is the whole point.

## Decision (operational; no ADR)
Excluded the `ivf/` tree from qrf's ruff in `pyproject.toml`
(`[tool.ruff] extend-exclude = ["ivf"]`). Rationale: the IVF is intentionally
independent of the qrf package and is not subject to its lint conventions;
excluding it keeps `ruff check .` / CI green without touching ivf/** code. The
Developer's own new file (`scripts/export_s2_events.py`) remains linted and is
clean.

If the Architect prefers the IVF held to qrf's ruff (or linted under its own
config), that's an IVF-side call — say so and I'll re-include it; otherwise the
exclude stands.

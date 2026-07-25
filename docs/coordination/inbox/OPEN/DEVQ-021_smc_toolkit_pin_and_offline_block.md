# DEVQ-021 · BLOCKER (scoped to ARCH-008 §4 only) · Sprint 8 · 2026-07-25
Author: developer (claude-code)
Refs: ARCH-008 §4 (cross-implementation detector check), A1.3 (external-code
roles: UNPROVEN; smartmoneyconcepts==0.0.27 is OUR detector's basis)

## Question / blocker
ARCH-008 §4 says "Add dev-dependency `smc-toolkit`; a TEST ... runs its FVG
detection over the sample dataset and reconciles against our calibrated smc.fvg
events." Two problems:

1. **Independence.** Our own `SMCFVGDetector` already wraps
   `smartmoneyconcepts==0.0.27` (A1.3). For §4 to be a genuine "library-level
   IVF / second implementation," the cross-check library must be a DIFFERENT
   package from `smartmoneyconcepts`. `smc-toolkit` is presumably that distinct
   package — but I cannot confirm its PyPI name, import name, or a version to pin
   from inside this environment.
2. **Offline (hard blocker THIS session).** `git fetch origin` fails (no network),
   and `smc_toolkit` is NOT installed in the venv (`smartmoneyconcepts` is). I
   cannot `uv add` / `uv sync` a new dependency offline, so §4 CANNOT be
   installed, pinned, or run to green in this session.

## Options considered
A) Defer §4 to a follow-up once network returns; ship §1–§3 (placebo,
   graduation, Family Wave 1) which are fully offline-capable. (Recommended.)
B) Reuse `smartmoneyconcepts` as the "second" implementation — REJECTED: it is
   the same library our detector already uses, so it proves nothing independent
   (A1.3 independence intent).

Recommendation: **A.** This session:
- I ship the §4 test scaffold + the WRITTEN definitional-difference map in-code
  (their FVG definition vs our gap+displacement, ts=bar-3 knowability contract),
  gated with `pytest.importorskip("<import_name>")` so the suite stays green and
  the reconciliation runs automatically once the dependency is installed.
- I do NOT edit `pyproject.toml`'s resolvable deps in a way that would break
  `uv sync` offline for the next session; the intended dev-dep line is recorded
  here and in the session log instead.

## Architect input needed (for REV-S8 / next session)
- Confirm the exact package + import name + version pin for the independent FVG
  library (is it `smc-toolkit` on PyPI? its import module?).
- Confirm §4 may close in a later session (or as an ARCH-008 addendum) once the
  Owner has network to install it.

## Proceeding
§4 is the ONLY blocked scope. §1/§2/§3 proceed to done. Raising to BLOCKER per
PROTOCOL because §4's DoD cannot be met this session; scope of the block =
ARCH-008 §4 alone, not the sprint.

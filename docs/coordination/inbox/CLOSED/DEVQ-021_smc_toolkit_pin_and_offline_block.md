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

---

## REPLY (Architect ruling) · 2026-07-25

### Finding first (machine-verified before this ruling shipped)
I probed PyPI and the upstream repo directly. **FINDING F-021-1: the PyPI
package `smc-toolkit==0.1.0` contains NO CODE.** I downloaded both published
artifacts: the wheel (`smc_toolkit-0.1.0-py3-none-any.whl`, 4532 bytes)
contains exactly five `dist-info` metadata files and zero `.py` files; the
sdist (`smc-toolkit-0.1.0.tar.gz`) likewise contains packaging metadata and
egg-info only. `pip install smc-toolkit` succeeds and installs NOTHING
importable — an `importorskip("smc_toolkit")` gate would skip forever. The
sole release (2025-07-14) appears to be a broken publish; the README's
advertised features exist only in the GitHub repository. The Developer's
refusal to install an unverified package unilaterally was correct twice over:
once on A1.3 principle, and once because the package is empty.

The REAL implementation: `github.com/Louisjzhao/smc-toolkit` (MIT license),
latest commit **812de852f0e0a6bf454720d0ea11ad5c7c64b4ef** (2025-07-15).
Genuinely independent of `smartmoneyconcepts`: its dependencies are numpy,
pandas, matplotlib only; two source files, `smc_toolkit/__init__.py` and
`smc_toolkit/core.py` (`extract_fvg` at core.py:128).

### RULING
1. **Do NOT add a PyPI dependency.** There is nothing to depend on.
2. **VENDOR the source as a test fixture** (SYNTHETIC-FIXTURE-adjacent
   UNPROVEN role per A1.3): copy `core.py` and `__init__.py` at commit
   `812de852f0e0a6bf454720d0ea11ad5c7c64b4ef` into
   `tests/third_party/smc_toolkit_vendored/`, with the upstream MIT LICENSE
   file alongside and a provenance header in each file recording: repo URL,
   commit SHA, retrieval date, and the source sha256s —
   `core.py` = 056a9fdbb20a8e4e26141f41c5b8d5540a2f40f9313e2bd2289c282f7b92288f,
   `__init__.py` = 82267473162398aef8e858a4f8fa20c7541ed3fea80d40c44f3dc7a2e8acf449.
   The §4 test drops `importorskip` and imports the vendored module plainly —
   deterministic, offline-proof, no supply-chain drift.
3. **Independence boundary:** the vendored module may be imported ONLY from
   `tests/`; never from `qrf/**`. Add this to the structural firewall's
   forbidden-import assertions.
4. **Difference-map facts to encode** (I read their `extract_fvg`; verify
   against the vendored copy, not this prose, per GO-S7 hygiene):
   - Their FVG adds TWO extra conditions beyond our 3-bar gap: middle-bar
     CLOSE beyond bar-1's extreme, and a displacement filter (middle-bar body
     move > 2× expanding mean of absolute body moves; note their
     `bar_delta_percent` carries a spurious /100 that cancels because the
     threshold is built from the same series — internally consistent, worth a
     comment).
   - Detection is indexed at bar 3 via shift(2) masks — compatible with our
     ts=bar-3 knowability contract; row-adjacency spans holes, same as ours.
   - **Their `mitigated` column scans the ENTIRE FUTURE of each event —
     lookahead by construction.** The reconciliation must use the detection
     mask ONLY and must never consume `mitigated`; state this in the
     difference map.
5. **§4 closes in a Developer micro-session as an ARCH-008 ADDENDUM** —
   approved. Scope: vendor per (2)+(3), flip the gate, run the
   reconciliation, append the addendum with the agreement/difference counts.

Status: CLOSED (blocker resolved by ruling; §4 completion delegated to a
micro-session). — architect (fable)

"""THE WALL: qrf/ never imports runtime/, runtime/ never imports qrf.kernel.

Enforced by STATIC ANALYSIS with `ast` — files are parsed, never imported, so
a broken or side-effecting module under either side cannot escape the check.

Design after reference/NeelPrajnaPro_v1 @ 67b1d69 (the two-sided firewall
concept), re-implemented from the plan doc, not the old code.

KNOWN LIMITATION: this scan catches STATIC `import` / `from ... import`
statements only. A dynamic import — `importlib.import_module("runtime.x")`
or `__import__("runtime.x")` — passes straight through undetected, because
neither produces an `ast.Import`/`ast.ImportFrom` node. No dynamic imports
exist in this codebase today, so this is acceptable for S01, but it is a
real, tested hole, not an assumed guarantee. Re-examine at S07 when
`runtime/` gains real code — see `test_dynamic_imports_are_not_caught`
below, which proves the hole exists rather than leaving it implicit.
"""

import ast
from pathlib import Path

from qrf.errors import IntegrityViolation
from tests.drills.harness import DrillLog, run_drill

REPO_ROOT = Path(__file__).resolve().parent.parent

# Module-level so a later sprint (S07) can add "runtime" with a one-line change.
SCANNED_ROOTS = {
    "qrf": REPO_ROOT / "qrf",
    "runtime": REPO_ROOT / "runtime",
}


def _imported_module_names(tree: ast.Module) -> list[tuple[str, int]]:
    """Return (dotted_module_name, lineno) for every import statement."""
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                found.append((node.module, node.lineno))
    return found


def find_violations(root: Path, forbidden_prefix: str) -> list[tuple[Path, int, str]]:
    """List every import under `root` naming `forbidden_prefix` or one of its
    submodules. An absent or empty root has no violations — it passes
    trivially, it is not skipped.
    """
    violations = []
    if not root.exists():
        return violations
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for module_name, lineno in _imported_module_names(tree):
            if module_name == forbidden_prefix or module_name.startswith(forbidden_prefix + "."):
                violations.append((path, lineno, module_name))
    return violations


def _format_violations(violations: list[tuple[Path, int, str]]) -> str:
    return "\n".join(f"  {path}:{lineno}: imports {name!r}" for path, lineno, name in violations)


# --- V1/V2: the two prohibitions ---------------------------------------


def test_qrf_never_imports_runtime():
    violations = find_violations(SCANNED_ROOTS["qrf"], "runtime")
    assert not violations, "qrf/ must never import runtime/, found:\n" + _format_violations(
        violations
    )


def test_runtime_never_imports_qrf_kernel():
    violations = find_violations(SCANNED_ROOTS["runtime"], "qrf.kernel")
    assert not violations, "runtime/ must never import qrf.kernel, found:\n" + _format_violations(
        violations
    )


# --- V4: precision --------------------------------------------------------


def test_comment_mentioning_forbidden_import_does_not_trip(tmp_path):
    (tmp_path / "mod.py").write_text(
        "# this module must never import runtime.something, see the wall\n"
        "x = 1\n"
    )
    assert find_violations(tmp_path, "runtime") == []


def test_unusually_written_real_imports_are_caught(tmp_path):
    (tmp_path / "mod.py").write_text(
        "from runtime import something as y\n"
        "import runtime.deep.sub.module\n"
    )
    found_names = {name for _, _, name in find_violations(tmp_path, "runtime")}
    assert "runtime" in found_names
    assert "runtime.deep.sub.module" in found_names


def test_dynamic_imports_are_not_caught(tmp_path):
    """Documents the known limitation (see module docstring): a dynamic
    import is real, static-analysis-invisible, and gets through today. This
    test exists so the hole is proven and tracked, not assumed away.
    """
    (tmp_path / "mod.py").write_text(
        "import importlib\n"
        "importlib.import_module('runtime.something')\n"
        "__import__('runtime.something_else')\n"
    )
    assert find_violations(tmp_path, "runtime") == []


# --- V3/V5: the drill — proven able to fail, on both sides of the wall ---


def test_firewall_drill_qrf_side():
    """Control: clean qrf/ tree, GREEN. Tampered: a planted file importing
    runtime.something under qrf/, RED.
    """
    log = DrillLog()
    tamper_file = SCANNED_ROOTS["qrf"] / "_drill_tamper_tmp.py"

    def checker(plant: bool):
        if plant:
            tamper_file.write_text("import runtime.something\n")
        else:
            tamper_file.unlink(missing_ok=True)
        violations = find_violations(SCANNED_ROOTS["qrf"], "runtime")
        if violations:
            raise IntegrityViolation("forbidden import found under qrf/", violations)

    try:
        result = run_drill(
            name="firewall-qrf-forbids-runtime",
            checker=checker,
            clean_input=False,
            tampered_input=True,
            expected_exception=IntegrityViolation,
            log=log,
        )
    finally:
        tamper_file.unlink(missing_ok=True)

    assert result.tampered_exception is IntegrityViolation


def test_firewall_drill_runtime_side():
    """Mirror of the qrf-side drill: a planted file under runtime/ importing
    qrf.kernel.x must turn the checker RED; a clean runtime/ stays GREEN.
    """
    log = DrillLog()
    runtime_root = SCANNED_ROOTS["runtime"]
    tamper_file = runtime_root / "_drill_tamper_tmp.py"

    def checker(plant: bool):
        if plant:
            runtime_root.mkdir(exist_ok=True)
            tamper_file.write_text("import qrf.kernel.x\n")
        else:
            tamper_file.unlink(missing_ok=True)
        violations = find_violations(runtime_root, "qrf.kernel")
        if violations:
            raise IntegrityViolation("forbidden import found under runtime/", violations)

    try:
        result = run_drill(
            name="firewall-runtime-forbids-qrf-kernel",
            checker=checker,
            clean_input=False,
            tampered_input=True,
            expected_exception=IntegrityViolation,
            log=log,
        )
    finally:
        tamper_file.unlink(missing_ok=True)
        if runtime_root.exists() and not any(runtime_root.iterdir()):
            runtime_root.rmdir()

    assert result.tampered_exception is IntegrityViolation

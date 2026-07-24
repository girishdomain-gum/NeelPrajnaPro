"""Kernel firewall (ADR-004, Blueprint §0.2).

Mechanically enforces that ``qrf/kernel/**``:

1. never imports ``qrf.trading`` (directly or as a submodule), and
2. contains none of the forbidden domain-vocabulary tokens
   (``price``, ``bid``, ``ask``, ``spread``, ``pip``, ``lot``, ``venue``)
   as whole words inside any identifier.

Matching is on *identifier words* — an identifier is split on underscores and
camelCase boundaries and each lowercase word compared for equality — so
``pipeline`` (word ``pipeline``) and ``task`` (word ``task``) are fine while
``bid_price`` (words ``bid``, ``price``) is not. String literals, comments and
docstrings are not scanned; only identifiers are.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
KERNEL_DIR = REPO_ROOT / "qrf" / "kernel"

FORBIDDEN_IMPORT_ROOT = "qrf.trading"
FORBIDDEN_TOKENS = frozenset({"price", "bid", "ask", "spread", "pip", "lot", "venue"})

_WORD_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")


def _identifier_words(name: str) -> set[str]:
    """Split an identifier into lowercase words (snake_case + camelCase)."""
    return {w.lower() for w in _WORD_RE.findall(name)}


def _import_targets(node: ast.AST) -> list[str]:
    """Dotted module names introduced by an import node."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom):
        # Absolute import only (level 0); relative imports cannot reach trading.
        return [node.module] if node.module and node.level == 0 else []
    return []


def _identifiers(node: ast.AST) -> list[str]:
    """Every identifier a node introduces or references."""
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        return [node.attr]
    if isinstance(node, ast.arg):
        return [node.arg]
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [node.name]
    if isinstance(node, ast.keyword) and node.arg is not None:
        return [node.arg]
    if isinstance(node, ast.Global | ast.Nonlocal):
        return list(node.names)
    return []


def scan_source(source: str, filename: str) -> list[str]:
    """Return a list of firewall-violation messages for one source string."""
    violations: list[str] = []
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        for target in _import_targets(node):
            if target == FORBIDDEN_IMPORT_ROOT or target.startswith(
                FORBIDDEN_IMPORT_ROOT + "."
            ):
                violations.append(
                    f"{filename}:{getattr(node, 'lineno', '?')}: kernel imports {target!r}"
                )
        for ident in _identifiers(node):
            bad = _identifier_words(ident) & FORBIDDEN_TOKENS
            if bad:
                violations.append(
                    f"{filename}:{getattr(node, 'lineno', '?')}: identifier "
                    f"{ident!r} contains forbidden token(s) {sorted(bad)}"
                )
    return violations


def _scan_kernel() -> list[str]:
    violations: list[str] = []
    for path in sorted(KERNEL_DIR.rglob("*.py")):
        violations.extend(scan_source(path.read_text(encoding="utf-8"), str(path)))
    return violations


# --- the gate ----------------------------------------------------------------
def test_kernel_has_python_files():
    # Guard against the scan silently passing because it found nothing.
    assert list(KERNEL_DIR.rglob("*.py")), "no kernel python files found to scan"


def test_kernel_is_clean():
    violations = _scan_kernel()
    assert not violations, "kernel firewall violations:\n" + "\n".join(violations)


# --- negative cases: the scanner must actually catch planted violations ------
def test_scanner_detects_trading_import(tmp_path):
    planted = tmp_path / "planted_import.py"
    planted.write_text("from qrf.trading import order_engine\n", encoding="utf-8")
    violations = scan_source(planted.read_text(encoding="utf-8"), str(planted))
    assert any("qrf.trading" in v for v in violations)


def test_scanner_detects_trading_submodule_import(tmp_path):
    planted = tmp_path / "planted_submodule.py"
    planted.write_text("import qrf.trading.simulator.engine\n", encoding="utf-8")
    violations = scan_source(planted.read_text(encoding="utf-8"), str(planted))
    assert any("qrf.trading" in v for v in violations)


def test_scanner_detects_forbidden_identifier():
    src = "def compute(bid_price):\n    spread = bid_price + 1\n    return spread\n"
    violations = scan_source(src, "<planted>")
    joined = "\n".join(violations)
    assert "bid" in joined and "price" in joined and "spread" in joined


def test_scanner_allows_lookalike_words():
    # 'pipeline', 'task', 'slot', 'allotment' must NOT trip the token scan.
    src = "def pipeline(task):\n    slot = task\n    return slot\n"
    assert scan_source(src, "<ok>") == []

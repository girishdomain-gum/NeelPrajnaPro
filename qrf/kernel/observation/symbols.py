"""Exact-symbol enforcement (A-007 §2.4, Owner order O-008).

Pure, terminal-independent: the exporter is the only module that talks to
a live MT5 terminal (qrf.kernel.observation.exporter). This check is
exercised directly in tests without needing one.
"""

from __future__ import annotations

from qrf.errors import SymbolRefused

PINNED_SYMBOL = "XAUUSD"


def require_exact_symbol(requested: str) -> str:
    """Refuse anything that is not a byte-exact match for PINNED_SYMBOL --
    `XAUUSD.crp`, `XAUUSDm`, differing case, anything else. Never "find
    the closest gold symbol". Returns the symbol on success, for chaining.
    """
    if requested != PINNED_SYMBOL:
        raise SymbolRefused(requested, PINNED_SYMBOL)
    return requested

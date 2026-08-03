"""E1: wrong symbol requested is refused, never fuzzy-matched (A-007 §2.4)."""

from qrf.errors import SymbolRefused
from qrf.kernel.observation.symbols import PINNED_SYMBOL, require_exact_symbol
from tests.drills.harness import DrillLog, run_drill


def test_e1_exact_symbol_only_drill():
    log = DrillLog()

    def checker(requested: str):
        require_exact_symbol(requested)

    result = run_drill(
        name="E1-exact-symbol-only",
        checker=checker,
        clean_input=PINNED_SYMBOL,
        tampered_input="XAUUSD.crp",
        expected_exception=SymbolRefused,
        log=log,
    )
    assert result.tampered_exception is SymbolRefused


def test_e1_variants_all_refused():
    for variant in ["XAUUSD.crp", "XAUUSDm", "xauusd", "XAUUSD ", " XAUUSD", "XAUUSD2"]:
        try:
            require_exact_symbol(variant)
        except SymbolRefused as exc:
            assert exc.requested == variant
            assert exc.pinned == PINNED_SYMBOL
        else:
            raise AssertionError(f"{variant!r} should have been refused")

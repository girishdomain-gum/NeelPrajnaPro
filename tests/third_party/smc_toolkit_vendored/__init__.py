# Vendored third-party source — DO NOT EDIT below the sentinel.
#
# Upstream:      github.com/Louisjzhao/smc-toolkit (MIT, LICENSE alongside)
# File:          smc_toolkit/__init__.py
# Commit:        812de852f0e0a6bf454720d0ea11ad5c7c64b4ef
# Retrieved:     2026-07-25 (DEVQ-021 micro-session; ARCH-008 §4 ruling)
# Upstream sha256: 82267473162398aef8e858a4f8fa20c7541ed3fea80d40c44f3dc7a2e8acf449
#   (covers every byte BELOW the sentinel line; verified by
#    tests/third_party/test_smc_toolkit_vendored_provenance.py)
#
# Why vendored, not pip-installed (ARCH-008 §4, DEVQ-021 CLOSED):
#   The PyPI package smc-toolkit==0.1.0 ships NO importable code (empty
#   publish, FINDING F-021-1). The real implementation lives only in the
#   GitHub repo. It is genuinely independent of smartmoneyconcepts (deps:
#   numpy/pandas/matplotlib only), so it is a valid second FVG implementation
#   for the library-level IVF. UNPROVEN role (A1.3): importable from tests/
#   ONLY, never from qrf/** (structural firewall enforces).
# === VENDORED UPSTREAM BEGINS (sha256 above covers all bytes below this line) ===
from .core import (
    calc_swing_structures,
    tag_fvg,
    plot_smc_structure,
    process_smc_with_internal,
    extract_ob_blocks,
    extract_fvg
)

__all__ = [
    "calc_swing_structures",
    "tag_fvg",
    "plot_smc_structure",
    "process_smc_with_internal",
    "extract_ob_blocks",
    "extract_fvg"
]

"""QRF — Quantitative Research Framework.

A machine for finding out what is actually true about markets, built so it
cannot fool the person using it. The kernel (``qrf.kernel``) is domain-blind;
the trading domain lives in ``qrf.trading`` and may import the kernel, never
the reverse (enforced by ``tests/test_kernel_firewall.py``).
"""

__version__ = "0.1.0"

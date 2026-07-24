"""Sprint-2 hand-audit CLI — print 10 sampled events per detector with source bars.

For the Owner's Sprint-2 human check (IVF §7 S2). Runs each Sprint-2 detector on a
deterministic demo bar series long enough to emit at least ten events, and prints
each sampled event beside the bar that produced it.

Run:  uv run python scripts/hand_audit_s2.py
"""

from __future__ import annotations

from qrf.trading.concepts.classical import RSIDetector
from qrf.trading.concepts.hand_audit import (
    format_audit,
    rsi_demo_bars,
    seasonality_demo_bars,
)
from qrf.trading.concepts.seasonality import SeasonalityDetector


def main() -> None:
    seas = SeasonalityDetector(
        params={
            "sessions": {"london": [8 * 3600, 16 * 3600], "newyork": [13 * 3600, 22 * 3600]},
            "emit_dow": True,
        }
    )
    rsi = RSIDetector()
    print(format_audit(seas, seasonality_demo_bars(), n=10))
    print()
    print(format_audit(rsi, rsi_demo_bars(), n=10))


if __name__ == "__main__":
    main()

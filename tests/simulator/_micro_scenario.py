"""Shared hand-computed micro-scenario for the engine determinism tests.

Not a test module (no ``test_`` functions, so pytest does not collect it). Both
the in-process determinism test and the across-process-restart subprocess build
their trades through :func:`build` here, so the two runs are byte-comparable by
construction. Run directly (``python tests/simulator/_micro_scenario.py`` from the
repo root) it prints the sha256 of the canonical trade image.

Hand computation (cost_per_unit = 0.30 + 2*(0.05 + 0.035) = 0.47, size 1):
    A  long  @ ts0 -> entry ts1 open 100, exit ts3 open 105  gross +5.00 net +4.53
    B  long  @ ts5 -> entry ts6 open 200, exit ts8 open 197  gross -3.00 net -3.47
    C  short @ ts10-> entry ts11 open 50, exit ts13 open 48  gross +2.00 net +1.53
    totals: gross +4.00, net +2.59
"""

from __future__ import annotations

import hashlib

import pandas as pd

from qrf.trading.simulator.engine import EventEngine, ExecutionSpec, Trades
from qrf.trading.utility.cost_models import load_cost_model

SEED = 12345
COST_MODEL_NAME = "xauusd_retail_median"


def build() -> Trades:
    """Build the fixed micro-scenario trades (deterministic, no RNG)."""
    n = 15
    opens = [100.0] * n
    opens[1] = 100.0   # entry A
    opens[3] = 105.0   # exit A
    opens[6] = 200.0   # entry B
    opens[8] = 197.0   # exit B
    opens[11] = 50.0   # entry C
    opens[13] = 48.0   # exit C
    bars = pd.DataFrame(
        {
            "ts": list(range(n)),
            "open": opens,
            "high": opens,
            "low": opens,
            "close": opens,
        }
    )
    events = pd.DataFrame(
        {
            "ts": [0, 5, 10],
            "direction": [1, 1, -1],
            "strength": [1.0, 1.0, 1.0],
        }
    )
    cost_model = load_cost_model(COST_MODEL_NAME)
    engine = EventEngine()
    return engine.simulate(
        bars, events, cost_model, seed=SEED, execution=ExecutionSpec(hold_bars=2)
    )


def main() -> None:
    print(hashlib.sha256(build().canonical_bytes()).hexdigest())


if __name__ == "__main__":
    main()

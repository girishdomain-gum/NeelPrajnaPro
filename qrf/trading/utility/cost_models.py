"""Named per-venue cost models (ARCH-004 §3, Blueprint §7 Sprint 4).

A cost model turns *gross* trade P&L into *net* by charging the honest, explicit
frictions of a venue — spread, slippage, commission — every number of which
lives in ``configs/venues.yaml`` (never hard-coded here, so a cost is auditable
and versioned like any other input). This is the trading plug-in, so price
vocabulary is allowed.

Cost formula (per unit of size, round trip)::

    cost_per_unit = spread + 2 * (slippage_per_side + commission_per_side)

    * spread            — full bid/ask spread crossed once over a round trip.
    * slippage_per_side — adverse fill per side, charged on entry AND exit.
    * commission_per_side — broker commission per side, per unit of size.

``apply`` charges ``cost_per_unit * |size|`` to each trade (costs are
direction-independent) and is a pure, deterministic function: same trades in,
byte-identical net out.

**Instrument ``kind`` is a DEVQ (DEVQ-008).** A cost model is neither a data
source, a detector, nor cleanly a judge; the catalog's kind enum
(``data``/``detector``/``judge``) has no obvious slot and the instruction forbids
extending it silently. Pending the Architect's ruling, the registration surface
(``instrument_id`` / ``kind`` / ``params_schema`` / ``code_ref``) exposes
``kind = "judge"`` (the closest fit: a cost model scores the economic
outcome of trades, and — like a judge — is trusted only against hand-computed
checks). No cost-model ``instrument_registered`` record is written to the real
journal this sprint; the screener references cost models by name. The screener's
functional use does not depend on the ruling.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from qrf.kernel.errors import SchemaViolation

DEFAULT_VENUES_PATH = "configs/venues.yaml"

# The columns apply() needs on a gross-trades frame, and the columns it adds.
_REQUIRED_TRADE_COLUMNS: tuple[str, ...] = ("size", "gross_pnl")
COST_COLUMN = "cost"
NET_COLUMN = "net_pnl"

_COST_FIELDS: tuple[str, ...] = ("spread", "slippage_per_side", "commission_per_side")


@dataclass(frozen=True)
class CostModel:
    """A named, deterministic gross→net cost model for one venue."""

    name: str
    spread: float
    slippage_per_side: float
    commission_per_side: float
    version: str = "0.1.0"
    instrument: str = ""
    unit: str = ""
    currency: str = ""

    kind = "judge"  # DEVQ-008 (pending) — see module docstring.
    family = "utility"
    code_ref = "qrf.trading.utility.cost_models:CostModel"

    def __post_init__(self) -> None:
        for f in _COST_FIELDS:
            v = getattr(self, f)
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                raise SchemaViolation(f"cost model {self.name!r}: {f} must be a number")
            if v < 0:
                raise SchemaViolation(f"cost model {self.name!r}: {f} must be >= 0 (got {v})")

    # -- cost arithmetic ------------------------------------------------------
    @property
    def cost_per_unit(self) -> float:
        """Round-trip cost charged per unit of size (price units)."""
        return self.spread + 2.0 * (self.slippage_per_side + self.commission_per_side)

    def cost_for_size(self, size: float) -> float:
        """The cost charged to a single trade of the given (signed) size."""
        return self.cost_per_unit * abs(float(size))

    def apply(self, gross_trades: pd.DataFrame) -> pd.DataFrame:
        """Return a copy of ``gross_trades`` with ``cost`` and ``net_pnl`` columns.

        ``gross_trades`` must carry ``size`` and ``gross_pnl`` columns. The result
        is a new frame (the input is never mutated); ``net_pnl = gross_pnl -
        cost`` where ``cost = cost_per_unit * |size|``. Deterministic.
        """
        if not isinstance(gross_trades, pd.DataFrame):
            raise SchemaViolation(
                f"CostModel.apply expects a pandas DataFrame, got {type(gross_trades).__name__}"
            )
        missing = [c for c in _REQUIRED_TRADE_COLUMNS if c not in gross_trades.columns]
        if missing:
            raise SchemaViolation(f"gross_trades missing column(s) {missing}")
        out = gross_trades.copy()
        out[COST_COLUMN] = out["size"].abs() * self.cost_per_unit
        out[NET_COLUMN] = out["gross_pnl"] - out[COST_COLUMN]
        return out

    # -- registration surface (DEVQ-008; not written to the real journal) -----
    @property
    def instrument_id(self) -> str:
        return f"cost.{self.name}"

    @property
    def params_schema(self) -> dict[str, str]:
        return {
            "spread": "float >= 0  # full round-trip bid/ask spread (price units)",
            "slippage_per_side": "float >= 0  # adverse fill per side",
            "commission_per_side": "float >= 0  # broker commission per side, per unit",
        }

    def params(self) -> dict[str, float]:
        return {f: float(getattr(self, f)) for f in _COST_FIELDS}


def _venues_doc(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise SchemaViolation(f"venues config {p} not found")
    doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or "venues" not in doc:
        raise SchemaViolation(f"venues config {p} must be a mapping with a 'venues' key")
    return doc


def available(path: str | Path = DEFAULT_VENUES_PATH) -> list[str]:
    """The names of every cost model defined in the venues config."""
    return sorted(_venues_doc(path)["venues"].keys())


def load_cost_model(name: str, path: str | Path = DEFAULT_VENUES_PATH) -> CostModel:
    """Load the named cost model from ``configs/venues.yaml``.

    Raises :class:`SchemaViolation` if the name is absent or a required cost
    field is missing.
    """
    venues = _venues_doc(path)["venues"]
    if name not in venues:
        raise SchemaViolation(
            f"cost model {name!r} not in {path} (available: {sorted(venues)})"
        )
    v = venues[name]
    missing = [f for f in _COST_FIELDS if f not in v]
    if missing:
        raise SchemaViolation(f"cost model {name!r} missing field(s) {missing}")
    return CostModel(
        name=name,
        spread=float(v["spread"]),
        slippage_per_side=float(v["slippage_per_side"]),
        commission_per_side=float(v["commission_per_side"]),
        version=str(v.get("version", "0.1.0")),
        instrument=str(v.get("instrument", "")),
        unit=str(v.get("unit", "")),
        currency=str(v.get("currency", "")),
    )

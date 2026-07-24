"""Pandera schema for MT5-format bar CSVs (Blueprint §5 arrow (2), §7 Sprint 3).

The *door* of the data plane: a structural contract on a bar frame after column
mapping. It checks that the canonical columns are present and numerically
coercible — nothing more. Value-level anomalies (non-positive prices, high < low,
gaps, duplicates, non-monotonic time, spread outliers) are **flagged** by the
adapter, never rejected here (arrow (2): "never repairs — flags"). Only a frame
that is structurally malformed — a missing required column, or a value that
cannot be coerced to a number — fails at this door.

Canonical columns
-----------------
Required : ``time`` (bar OPEN time, integer seconds UTC), ``open``, ``high``,
           ``low``, ``close``.
Optional : ``tick_volume``, ``spread``, ``real_volume``.

MT5 exports vary (some carry extra indicator columns; some omit volume). The
adapter maps source names onto these canonical names via a configurable
``column_map`` before validation, so this schema always sees canonical names.
"""

from __future__ import annotations

import pandas as pd
from pandera.pandas import Check, Column, DataFrameSchema

from qrf.kernel.errors import SchemaViolation

# Canonical column sets.
REQUIRED_COLUMNS: tuple[str, ...] = ("time", "open", "high", "low", "close")
OPTIONAL_COLUMNS: tuple[str, ...] = ("tick_volume", "spread", "real_volume")
CANONICAL_COLUMNS: tuple[str, ...] = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

# Standard MT5 bar CSV header, in order (time,open,high,low,close,tick_volume
# [,spread,real_volume]) — the identity mapping's source names.
DEFAULT_COLUMN_MAP: dict[str, str] = {c: c for c in CANONICAL_COLUMNS}

# The Sprint-2 IVF export (IVF_S2_XAUUSD_PERIOD_H1.csv) names the open time
# ``time_open_sec`` and carries no volume columns; OHLC names are identity.
IVF_S2_COLUMN_MAP: dict[str, str] = {"time": "time_open_sec"}

# The structural door. ``coerce`` turns coercible strings/ints into the target
# dtype; a value that cannot be coerced raises (a genuine structural fault).
BAR_SCHEMA = DataFrameSchema(
    columns={
        "time": Column("int64", Check.ge(0), coerce=True, nullable=False),
        "open": Column("float64", coerce=True, nullable=False),
        "high": Column("float64", coerce=True, nullable=False),
        "low": Column("float64", coerce=True, nullable=False),
        "close": Column("float64", coerce=True, nullable=False),
        "tick_volume": Column("float64", coerce=True, nullable=True, required=False),
        "spread": Column("float64", coerce=True, nullable=True, required=False),
        "real_volume": Column("float64", coerce=True, nullable=True, required=False),
    },
    strict=True,  # only canonical columns survive to the anomaly stage
    coerce=True,
)


def _effective_map(column_map: dict[str, str] | None) -> dict[str, str]:
    """Identity mapping for every canonical column, overridden by ``column_map``."""
    eff = dict(DEFAULT_COLUMN_MAP)
    if column_map:
        for canon, src in column_map.items():
            if canon not in CANONICAL_COLUMNS:
                raise SchemaViolation(
                    f"column_map key {canon!r} is not a canonical column "
                    f"{CANONICAL_COLUMNS}"
                )
            eff[canon] = src
    return eff


def to_canonical(df: pd.DataFrame, column_map: dict[str, str] | None = None) -> pd.DataFrame:
    """Map source columns to canonical names and validate against :data:`BAR_SCHEMA`.

    Extra source columns (e.g. an exported ``rsi14``/``dow``) are dropped. A
    missing required column, or a value uncoercible to its type, raises
    :class:`SchemaViolation` — the structural door. Returns the validated,
    canonical-columns-only frame.
    """
    eff = _effective_map(column_map)
    selected: dict[str, pd.Series] = {}
    for canon in CANONICAL_COLUMNS:
        src = eff[canon]
        if src in df.columns:
            selected[canon] = df[src].reset_index(drop=True)
        elif canon in REQUIRED_COLUMNS:
            raise SchemaViolation(
                f"required column {canon!r} (source {src!r}) missing from input; "
                f"available columns: {list(df.columns)}"
            )
    canonical = pd.DataFrame(selected)
    try:
        return BAR_SCHEMA.validate(canonical, lazy=True)
    except Exception as e:  # pandera SchemaError(s) -> our taxonomy at the door
        raise SchemaViolation(f"bar CSV failed structural schema at the door: {e}") from e

"""Cost model tests (ARCH-004 §3): hand-computed net matches to the cent,
determinism, per-unit formula, config loading, and input validation.

The reference venue ``xauusd_retail_median`` has
    spread = 0.30, slippage_per_side = 0.05, commission_per_side = 0.035
so its round-trip cost per ounce is
    0.30 + 2*(0.05 + 0.035) = 0.47 USD/oz.
"""

from __future__ import annotations

import pandas as pd
import pytest

from qrf.kernel.errors import SchemaViolation
from qrf.trading.utility.cost_models import (
    CostModel,
    available,
    load_cost_model,
)

VENUE = "xauusd_retail_median"


@pytest.fixture
def model() -> CostModel:
    return load_cost_model(VENUE)


# --- config loading ----------------------------------------------------------
def test_available_lists_the_reference_venue():
    assert VENUE in available()


def test_load_reads_explicit_numbers(model):
    assert model.spread == 0.30
    assert model.slippage_per_side == 0.05
    assert model.commission_per_side == 0.035
    assert model.instrument == "XAUUSD"
    assert model.unit == "troy_ounce"


def test_unknown_model_refused():
    with pytest.raises(SchemaViolation):
        load_cost_model("no_such_venue")


# --- per-unit cost formula (hand-computed) -----------------------------------
def test_cost_per_unit_matches_hand_computation(model):
    # 0.30 + 2*(0.05 + 0.035) = 0.47
    assert model.cost_per_unit == pytest.approx(0.47, abs=1e-12)


def test_cost_for_size_is_direction_independent(model):
    assert model.cost_for_size(100) == pytest.approx(47.0, abs=1e-9)
    assert model.cost_for_size(-100) == pytest.approx(47.0, abs=1e-9)  # |size|


# --- apply(): gross -> net to the cent ---------------------------------------
def test_apply_hand_computed_examples(model):
    gross = pd.DataFrame(
        {
            "direction": [1, -1, 1],
            "size": [100.0, 100.0, 50.0],
            "gross_pnl": [50.0, -20.0, 10.0],
        }
    )
    net = model.apply(gross)
    # cost = 0.47 * |size|
    assert list(net["cost"]) == pytest.approx([47.0, 47.0, 23.5], abs=1e-9)
    # net = gross - cost
    assert list(net["net_pnl"]) == pytest.approx([3.0, -67.0, -13.5], abs=1e-9)


def test_apply_does_not_mutate_input(model):
    gross = pd.DataFrame({"size": [100.0], "gross_pnl": [50.0]})
    _ = model.apply(gross)
    assert "cost" not in gross.columns
    assert "net_pnl" not in gross.columns


def test_apply_is_deterministic(model):
    gross = pd.DataFrame({"size": [100.0, 40.0], "gross_pnl": [50.0, -3.0]})
    a = model.apply(gross)
    b = model.apply(gross)
    pd.testing.assert_frame_equal(a, b)


def test_apply_empty_frame(model):
    gross = pd.DataFrame({"size": [], "gross_pnl": []})
    net = model.apply(gross)
    assert list(net.columns) == ["size", "gross_pnl", "cost", "net_pnl"]
    assert len(net) == 0


def test_apply_requires_columns(model):
    with pytest.raises(SchemaViolation):
        model.apply(pd.DataFrame({"size": [1.0]}))  # no gross_pnl
    with pytest.raises(SchemaViolation):
        model.apply(pd.DataFrame({"gross_pnl": [1.0]}))  # no size


# --- gross vs net visibly differ (AC) ----------------------------------------
def test_costs_make_gross_and_net_differ(model):
    gross = pd.DataFrame({"size": [100.0], "gross_pnl": [50.0]})
    net = model.apply(gross)
    assert net["net_pnl"].iloc[0] != net["gross_pnl"].iloc[0]
    assert net["net_pnl"].iloc[0] < net["gross_pnl"].iloc[0]  # costs are a drag


# --- validation --------------------------------------------------------------
def test_negative_cost_field_refused():
    with pytest.raises(SchemaViolation):
        CostModel(name="bad", spread=-0.1, slippage_per_side=0.0, commission_per_side=0.0)


def test_instrument_surface_for_devq_008(model):
    # The registration surface exists (kind pending DEVQ-008), but this sprint
    # writes no cost-model instrument_registered record to the real journal.
    assert model.kind == "judge"
    assert model.instrument_id == f"cost.{VENUE}"
    assert set(model.params().keys()) == {"spread", "slippage_per_side", "commission_per_side"}

"""ARCH-008 §4 — cross-implementation FVG check (the library-level IVF).

Goal (ARCH-008 §4): know EXACTLY where a second FVG implementation agrees or
disagrees with our calibrated ``smc.fvg`` detector, with a WRITTEN mapping of the
definitional differences. No registry entry; the second implementation is UNPROVEN
(A1.3) and never touches the belief layer.

STATUS (DEVQ-021): the external library ARCH-008 §4 named (``smc-toolkit``) is a
dev-dependency that is NOT installable in this offline session, and it must be a
DIFFERENT package from ``smartmoneyconcepts`` (which OUR detector already wraps —
using it again would prove nothing independent, A1.3). So this file ships:

  1. :data:`DIFFERENCE_MAP` — the written definitional-difference map (below).
  2. :func:`reconcile` — the reconciliation harness (tested here), which matches two
     FVG event sets by (knowability ts, direction) and compares their zones.
  3. :func:`plain_fvg` — a clean-room, INDEPENDENT re-implementation of the ICT
     3-candle FVG rule (NOT via smartmoneyconcepts), used as the offline stand-in so
     the harness is exercised and a genuinely independent definition is reconciled
     against ours NOW.
  4. :func:`test_cross_impl_external_library_over_sample` — the REAL second-library
     leg, gated by ``pytest.importorskip`` so it runs automatically once the Owner
     installs the dependency (network up). Skipped, not silently dropped.

Our FVG contract (A1.3, detector source): a 3-bar pattern with the gap centred on
bar ``i`` (forming bars ``i-1, i, i+1``); the event's knowability ts is bar ``i+1``
(the gap is only confirmed once the third bar exists); zone = [Bottom, Top] of the
gap band (``zone_hi >= zone_lo``); ``smartmoneyconcepts==0.0.27`` behind a
knowability wrapper.
"""

from __future__ import annotations

import json

import pyarrow as pa
import pytest

from qrf.trading.concepts.smc.detector import SMCFVGDetector

# --- the WRITTEN definitional-difference map (ARCH-008 §4 deliverable) --------
# Each axis: how OUR smc.fvg defines it vs how a generic external 3-candle FVG
# library (ICT-standard, e.g. the intended smc-toolkit) typically does. Where the
# reconciliation shows a disagreement, it should trace to exactly one of these.
DIFFERENCE_MAP = {
    "pattern": {
        "ours": "3-bar gap: bullish iff high[i-1] < low[i+1]; bearish iff low[i-1] > high[i+1]",
        "external_typical": "same ICT 3-candle imbalance rule",
        "expected_effect": "agreement on which triples are FVGs (same core rule)",
    },
    "timestamp_knowability": {
        "ours": "event ts = bar i+1 (the THIRD bar; gap unconfirmed until it exists)",
        "external_typical": "often the MIDDLE bar i, or the first bar i-1",
        "expected_effect": "a whole-event ts OFFSET of 1-2 bars if the lib differs — "
                           "reconciliation aligns on ts, so a convention gap shows as "
                           "ALL events unmatched (a loud, unambiguous signal)",
    },
    "zone_bounds": {
        "ours": "zone_hi/zone_lo = Top/Bottom of the gap band (smartmoneyconcepts)",
        "external_typical": "[high[i-1], low[i+1]] bull / [high[i+1], low[i-1]] bear",
        "expected_effect": "identical bounds for the plain gap; may differ if the lib "
                           "extends the zone to candle bodies vs wicks",
    },
    "displacement_filter": {
        "ours": "NONE — every gap qualifies; strength records gap/span but never filters",
        "external_typical": "some libs require a 'displacement'/imbalance size threshold",
        "expected_effect": "a filtering lib emits a SUBSET of ours (only-ours entries)",
    },
    "join_consecutive": {
        "ours": "default False — back-to-back gaps stay separate events",
        "external_typical": "some libs merge consecutive gaps into one",
        "expected_effect": "a merging lib emits FEWER, wider events",
    },
    "edge_bars": {
        "ours": "first bar and last-centre bar never fire (need i-1 and i+1)",
        "external_typical": "varies; some emit at the boundary",
        "expected_effect": "at most 1-2 boundary events differ",
    },
}


def _bars(rows: list[tuple[int, float, float, float, float]]) -> pa.Table:
    ts = [r[0] for r in rows]
    return pa.table({
        "ts": pa.array(ts, pa.int64()),
        "open": [r[1] for r in rows],
        "high": [r[2] for r in rows],
        "low": [r[3] for r in rows],
        "close": [r[4] for r in rows],
    })


def plain_fvg(bars: pa.Table) -> list[dict]:
    """Clean-room, independent ICT 3-candle FVG detector (NOT smartmoneyconcepts).

    Bullish iff high[i-1] < low[i+1] (gap [high[i-1], low[i+1]]); bearish iff
    low[i-1] > high[i+1] (gap [high[i+1], low[i-1]]). Event ts = bar i+1 (matching
    our knowability convention, so any disagreement is definitional, not a ts-offset
    artifact). Returns {ts, direction, zone_hi, zone_lo} rows.
    """
    ts = bars.column("ts").to_pylist()
    high = bars.column("high").to_pylist()
    low = bars.column("low").to_pylist()
    out: list[dict] = []
    for i in range(1, len(ts) - 1):
        if high[i - 1] < low[i + 1]:  # bullish gap
            out.append({"ts": int(ts[i + 1]), "direction": 1,
                        "zone_hi": float(low[i + 1]), "zone_lo": float(high[i - 1])})
        elif low[i - 1] > high[i + 1]:  # bearish gap
            out.append({"ts": int(ts[i + 1]), "direction": -1,
                        "zone_hi": float(low[i - 1]), "zone_lo": float(high[i + 1])})
    return out


def _ours(bars: pa.Table) -> list[dict]:
    """Our detector's FVG events as {ts, direction, zone_hi, zone_lo} rows."""
    df = SMCFVGDetector().detect(bars).to_pandas()
    return [
        {"ts": int(r.ts), "direction": int(r.direction),
         "zone_hi": float(r.zone_hi), "zone_lo": float(r.zone_lo)}
        for r in df.itertuples(index=False)
    ]


def reconcile(ours: list[dict], theirs: list[dict], *, price_tol: float = 1e-6) -> dict:
    """Match two FVG event sets by (ts, direction); compare zones within tol.

    Returns counts and the specific disagreements so a caller (or the IVF) can trace
    each one to an axis of :data:`DIFFERENCE_MAP`.
    """
    def key(e):
        return (e["ts"], e["direction"])

    ours_by = {key(e): e for e in ours}
    theirs_by = {key(e): e for e in theirs}
    matched, zone_mismatch = [], []
    for k, a in ours_by.items():
        b = theirs_by.get(k)
        if b is None:
            continue
        matched.append(k)
        if (abs(a["zone_hi"] - b["zone_hi"]) > price_tol
                or abs(a["zone_lo"] - b["zone_lo"]) > price_tol):
            zone_mismatch.append(k)
    only_ours = [k for k in ours_by if k not in theirs_by]
    only_theirs = [k for k in theirs_by if k not in ours_by]
    return {
        "n_ours": len(ours), "n_theirs": len(theirs), "n_matched": len(matched),
        "only_ours": only_ours, "only_theirs": only_theirs, "zone_mismatch": zone_mismatch,
    }


# A synthetic bar series with a planted bullish and bearish FVG plus flat bars.
_FVG_BARS = _bars([
    (1, 10.0, 10.0, 9.0, 10.0),     # 0
    (2, 10.0, 20.0, 10.0, 19.0),    # 1  centre of a bull gap (displacement up)
    (3, 19.0, 21.0, 15.0, 20.0),    # 2  low=15 > high[0]=10 -> BULL FVG (knowability bar i+1)
    (4, 20.0, 20.5, 19.5, 20.0),    # 3  flat
    (5, 20.0, 20.0, 8.0, 9.0),      # 4  centre of a bear gap (displacement down)
    (6, 9.0, 9.5, 7.0, 8.0),        # 5  high=9.5 < low[3]=19.5 -> BEAR FVG at centre 4, ts=bar i+1
    (7, 8.0, 8.2, 7.8, 8.0),        # 6  flat
])


def test_difference_map_is_documented():
    """The written map covers the axes the reconciliation can surface."""
    for axis in ("pattern", "timestamp_knowability", "zone_bounds",
                 "displacement_filter", "join_consecutive", "edge_bars"):
        assert axis in DIFFERENCE_MAP
        assert set(DIFFERENCE_MAP[axis]) == {"ours", "external_typical", "expected_effect"}


def test_reconcile_harness_counts_agreements_and_disagreements():
    ours = [{"ts": 10, "direction": 1, "zone_hi": 5.0, "zone_lo": 4.0},
            {"ts": 20, "direction": -1, "zone_hi": 9.0, "zone_lo": 8.0}]
    theirs = [{"ts": 10, "direction": 1, "zone_hi": 5.0, "zone_lo": 4.0},   # exact match
              {"ts": 30, "direction": 1, "zone_hi": 2.0, "zone_lo": 1.0}]   # only theirs
    r = reconcile(ours, theirs)
    assert r["n_matched"] == 1
    assert r["only_ours"] == [(20, -1)]
    assert r["only_theirs"] == [(30, 1)]
    # A zone-only disagreement is surfaced separately from a missing event.
    r2 = reconcile(ours, [{"ts": 20, "direction": -1, "zone_hi": 9.5, "zone_lo": 8.0}])
    assert r2["zone_mismatch"] == [(20, -1)]


def test_our_detector_agrees_with_independent_clean_room_impl():
    """Our smartmoneyconcepts-wrapped detector vs a clean-room ICT gap rule.

    Both are the plain 3-candle gap definition, so they must agree on the planted
    FVGs (same knowability ts convention). Any residual difference is REPORTED and
    traced to DIFFERENCE_MAP — the library-level IVF in miniature.
    """
    ours = _ours(_FVG_BARS)
    theirs = plain_fvg(_FVG_BARS)
    r = reconcile(ours, theirs)
    # Both find the same planted gaps with identical zones (the core rule agrees).
    assert r["n_ours"] >= 2 and r["n_theirs"] >= 2
    assert r["n_matched"] == r["n_ours"] == r["n_theirs"], (
        f"cross-impl divergence — trace to DIFFERENCE_MAP: {json.dumps(r, default=list)}"
    )
    assert not r["zone_mismatch"]


def test_cross_impl_external_library_over_sample():
    """The REAL second-library leg (ARCH-008 §4) — DEFERRED offline (DEVQ-021).

    Runs the external FVG library over the same bars and reconciles against ours.
    Skipped until the dependency is installed (it must be a package DISTINCT from
    smartmoneyconcepts — see DEVQ-021 for the pin/name the Architect must confirm).
    """
    smc_toolkit = pytest.importorskip(
        "smc_toolkit",
        reason="ARCH-008 §4 external FVG library not installed (DEVQ-021, offline)",
    )
    # Once available, adapt this call to the library's real API (DEVQ-021 open item),
    # produce {ts, direction, zone_hi, zone_lo} rows on our knowability convention,
    # then: r = reconcile(_ours(_FVG_BARS), their_events); assert on r vs DIFFERENCE_MAP.
    raise AssertionError(
        f"smc_toolkit is installed ({smc_toolkit}) — wire its FVG API per DEVQ-021 "
        "and reconcile against _ours(); this placeholder must then be implemented."
    )

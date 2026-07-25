"""ARCH-008 §4 — cross-implementation FVG check (the library-level IVF).

Goal (ARCH-008 §4): know EXACTLY where a second FVG implementation agrees or
disagrees with our calibrated ``smc.fvg`` detector, with a WRITTEN mapping of the
definitional differences. No registry entry; the second implementation is UNPROVEN
(A1.3) and never touches the belief layer.

STATUS (DEVQ-021 CLOSED — vendored, was offline-blocked):
The library ARCH-008 §4 named (``smc-toolkit``) ships NO importable code on PyPI
(``smc-toolkit==0.1.0`` is an empty publish — FINDING F-021-1). The real, genuinely
independent implementation (deps: numpy/pandas/matplotlib only — NOT
``smartmoneyconcepts``, which OUR detector wraps) lives only in the GitHub repo. Per
the Architect ruling it is **vendored** at a pinned commit into
``tests/third_party/smc_toolkit_vendored/`` (MIT LICENSE + per-file provenance
headers; sha256-verified by ``tests/third_party/test_smc_toolkit_vendored_provenance``).
So this file:

  1. :data:`DIFFERENCE_MAP` — the written definitional-difference map (below),
     describing OUR ``smc.fvg`` vs the VENDORED ``extract_fvg``, verified against the
     vendored source by :func:`test_difference_map_matches_vendored_source`.
  2. :func:`reconcile` — the reconciliation harness (tested here), matching two FVG
     event sets by (knowability ts, direction) and comparing their zones.
  3. :func:`plain_fvg` — a clean-room, INDEPENDENT ICT 3-candle FVG rule used to show
     our detector equals the plain gap definition, so the ONLY divergence against the
     vendored lib is its two extra filter conditions.
  4. :func:`test_cross_impl_vendored_library_over_sample` — the REAL second-library
     leg: runs the vendored ``extract_fvg`` over a sample dataset and reconciles it
     against our calibrated ``smc.fvg`` events (deterministic, offline-proof).

Our FVG contract (A1.3, detector source): a 3-bar pattern with the gap centred on
bar ``i`` (forming bars ``i-1, i, i+1``); the event's knowability ts is bar ``i+1``
(the gap is only confirmed once the third bar exists); zone = [Bottom, Top] of the
gap band (``zone_hi >= zone_lo``); ``smartmoneyconcepts==0.0.27`` behind a
knowability wrapper.

The vendored ``extract_fvg`` uses the SAME 3-bar gap (its window is ``i-2, i-1, i``,
stamping the third bar ``i`` via ``shift(2)`` masks — the same knowability moment as
ours), then adds TWO extra conditions (mid-bar close beyond bar-1's extreme + a
displacement filter). It is therefore a strict SUBSET of the plain gaps, with
IDENTICAL zone bounds on the intersection. Its ``mitigated`` column scans the entire
future of each event (lookahead by construction) and is NEVER consumed here.
"""

from __future__ import annotations

import inspect
import json

import pandas as pd
import pyarrow as pa

from qrf.trading.concepts.smc.detector import SMCFVGDetector

# The vendored, genuinely-independent second implementation (DEVQ-021 ruling).
from tests.third_party.smc_toolkit_vendored import core as smc_toolkit_core

# --- the WRITTEN definitional-difference map (ARCH-008 §4 deliverable) --------
# Each axis: how OUR smc.fvg defines it vs how the VENDORED smc_toolkit extract_fvg
# does. Every reconciliation disagreement must trace to exactly one of these axes.
# The `verify` field names the vendored-source token that proves the claim; it is
# checked mechanically by test_difference_map_matches_vendored_source (GO-S7 hygiene:
# verify against the vendored copy, not this prose).
DIFFERENCE_MAP = {
    "pattern_and_knowability": {
        "ours": "3-bar gap centred on bar i (bars i-1,i,i+1); bullish iff "
                "high[i-1] < low[i+1]; event ts = bar i+1 (the THIRD/confirming bar)",
        "vendored": "same gap, window i-2,i-1,i via shift(2); bullish iff "
                    "low[i] > high[i-2]; event end_time = bar i (also the THIRD bar)",
        "expected_effect": "SAME core rule and SAME knowability bar (third bar) — the "
                           "two impls align on ts, so any residual gap is definitional, "
                           "never a timestamp-convention artifact",
        "verify": ".shift(2)",
    },
    "zone_bounds": {
        "ours": "zone_hi/zone_lo = Top/Bottom of the gap band (smartmoneyconcepts)",
        "vendored": "bull: fvg_top=low[i], fvg_bottom=high[i-2]; bear mirrored — "
                    "the SAME band as ours on any shared triple",
        "expected_effect": "IDENTICAL bounds on every matched event (zone_mismatch == 0)",
        "verify": "fvg_top",
    },
    "mid_close_condition": {
        "ours": "NONE — a bare gap qualifies",
        "vendored": "requires the middle bar to CLOSE beyond bar-1's extreme "
                    "(close.shift(1) > high.shift(2) bull / < low.shift(2) bear)",
        "expected_effect": "removes gaps whose middle bar did not close through — a "
                           "source of only-ours events",
        "verify": "df['close'].shift(1) > df['high'].shift(2)",
    },
    "displacement_filter": {
        "ours": "NONE — every gap qualifies; strength records gap/span but never filters",
        "vendored": "requires a displacement: middle-bar body move > 2x the EXPANDING "
                    "mean of absolute body moves (bar_delta_percent > threshold). Note "
                    "the spurious /100 in bar_delta_percent CANCELS — threshold is built "
                    "from the same series, so it is internally consistent",
        "expected_effect": "the vendored lib emits a strict SUBSET of the plain gaps "
                           "(only-ours entries; never only-theirs)",
        "verify": "expanding().mean() * 2",
    },
    "mitigation_lookahead": {
        "ours": "detection carries no mitigation flag; knowability is bar i+1 only",
        "vendored": "a 'mitigated' column scans the ENTIRE FUTURE of each event "
                    "(future_df = bars strictly after end_time) — LOOKAHEAD by "
                    "construction",
        "expected_effect": "the reconciliation consumes the DETECTION MASK ONLY and "
                           "MUST NEVER read 'mitigated' (it would import hindsight)",
        "verify": "future_df",
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


def _theirs(bars: pa.Table) -> list[dict]:
    """The VENDORED smc_toolkit.extract_fvg events as {ts, direction, zone_hi, zone_lo}.

    Adapts the vendored library's MultiIndex (code, date) DataFrame API to our event
    shape, stamping ts at the library's ``end_time`` (bar i, the third/confirming bar —
    the same knowability moment as ours). The library's ``mitigated`` column is
    LOOKAHEAD by construction and is DELIBERATELY NOT READ here (see DIFFERENCE_MAP
    ``mitigation_lookahead``).
    """
    ts = bars.column("ts").to_pylist()
    index = pd.MultiIndex.from_arrays(
        [["XAUUSD"] * len(ts), ts], names=["code", "date"]
    )
    df = pd.DataFrame(
        {
            "open": bars.column("open").to_pylist(),
            "high": bars.column("high").to_pylist(),
            "low": bars.column("low").to_pylist(),
            "close": bars.column("close").to_pylist(),
        },
        index=index,
    )
    fvg = smc_toolkit_core.extract_fvg(df)
    out: list[dict] = []
    for _, r in fvg.iterrows():
        direction = 1 if r["fvg_type"] == "bullish" else -1
        out.append({
            "ts": int(r["end_time"]), "direction": direction,
            "zone_hi": float(r["fvg_top"]), "zone_lo": float(r["fvg_bottom"]),
        })
    return out


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


# The SAMPLE dataset for the vendored cross-impl leg (ARCH-008 §4): six genuine plain
# gaps of VARYING displacement, so the vendored lib's two extra conditions (mid-close +
# displacement) produce a proper, illustrative SUBSET. Two strong-displacement gaps
# (bull ts=4, bear ts=12) pass the vendored filter; four weaker gaps are only-ours.
_SAMPLE_BARS = _bars([
    (1,  100.0, 101.0,  99.0, 100.0),   # 0  filler
    (2,  100.0, 101.0,  99.0, 100.0),   # 1  filler
    (3,  100.0, 140.0, 100.0, 138.0),   # 2  strong up body (displacement)
    (4,  138.0, 150.0, 120.0, 145.0),   # 3  low=120 > high[1]=101 -> BULL gap, strong (matched)
    (5,  145.0, 146.0, 144.0, 145.0),   # 4  filler; forms a weak bull gap high[2]<low[4]
    (6,  145.0, 146.0, 144.0, 145.0),   # 5  filler
    (7,  145.0, 147.0, 144.0, 146.0),   # 6  tiny up body (weak displacement)
    (8,  146.0, 160.0, 148.0, 158.0),   # 7  low=148 > high[5]=146 -> BULL gap, weak (only-ours)
    (9,  158.0, 159.0, 157.0, 158.0),   # 8  filler; forms a weak bull gap high[6]<low[8]
    (10, 158.0, 159.0, 157.0, 158.0),   # 9  filler
    (11, 158.0, 158.0, 120.0, 122.0),   # 10 strong down body (displacement)
    (12, 122.0, 140.0, 110.0, 112.0),   # 11 high=140 < low[9]=157 -> BEAR gap, strong (matched)
    (13, 112.0, 113.0, 111.0, 112.0),   # 12 filler; forms a weak bear gap low[10]>high[12]
])

# The reconciliation the vendored leg must reproduce (deterministic, offline-proof).
# ours == plain gaps (6); vendored is a strict subset (2), zones identical on the
# intersection, nothing only-theirs.
_EXPECTED_SAMPLE_RECON = {
    "n_ours": 6, "n_theirs": 2, "n_matched": 2,
    "only_ours": [(5, 1), (8, 1), (9, 1), (13, -1)],
    "only_theirs": [],
    "zone_mismatch": [],
}


def test_difference_map_is_documented():
    """The written map covers the axes the reconciliation can surface."""
    for axis in ("pattern_and_knowability", "zone_bounds", "mid_close_condition",
                 "displacement_filter", "mitigation_lookahead"):
        assert axis in DIFFERENCE_MAP
        assert set(DIFFERENCE_MAP[axis]) == {"ours", "vendored", "expected_effect", "verify"}


def test_difference_map_matches_vendored_source():
    """Verify each difference-map claim against the VENDORED source, not this prose.

    GO-S7 hygiene (ruling item 4): the facts must be checked against the vendored
    ``extract_fvg`` copy. Each axis names a token that must appear in the source.
    """
    src = inspect.getsource(smc_toolkit_core.extract_fvg)
    for axis, spec in DIFFERENCE_MAP.items():
        assert spec["verify"] in src, (
            f"difference-map axis {axis!r} claims {spec['verify']!r} but it is not in "
            "the vendored extract_fvg source"
        )
    # The spurious /100 the map calls out (cancels, but must genuinely be present).
    assert "/ 100" in src or "/100" in src
    # mitigation is future-scanning lookahead: it reads bars strictly after end_time.
    assert "index.get_level_values(1) > end_time" in src


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


def test_our_detector_equals_plain_gaps_on_sample():
    """On the sample, our calibrated detector == the clean-room plain-gap rule.

    This isolates the vendored comparison: since ours == plain gaps, the ONLY
    divergence in the next test is attributable to the vendored lib's two extra
    filter conditions (mid-close + displacement), not to any ours-vs-plain quirk.
    """
    r = reconcile(_ours(_SAMPLE_BARS), plain_fvg(_SAMPLE_BARS))
    assert r["n_matched"] == r["n_ours"] == r["n_theirs"] == 6
    assert not r["only_ours"] and not r["only_theirs"] and not r["zone_mismatch"]


def test_cross_impl_vendored_library_over_sample():
    """ARCH-008 §4 — the REAL second-library leg, now vendored (DEVQ-021 CLOSED).

    Runs the vendored ``smc_toolkit.extract_fvg`` over the sample dataset and
    reconciles against our calibrated ``smc.fvg`` events. Deterministic and
    offline-proof (no importorskip, no PyPI, no supply-chain drift).

    The library-level IVF result, traced to DIFFERENCE_MAP:
      * The vendored lib is a strict SUBSET of the plain gaps — nothing only-theirs
        (``mid_close_condition`` + ``displacement_filter`` only ever REMOVE).
      * Zone bounds are IDENTICAL on every matched event (``zone_bounds``).
      * Matched events share our knowability ts (``pattern_and_knowability``).
    """
    ours = _ours(_SAMPLE_BARS)
    theirs = _theirs(_SAMPLE_BARS)
    r = reconcile(ours, theirs)

    # Structural invariants (the load-bearing difference-map claims):
    assert r["only_theirs"] == [], (
        "vendored emitted an event we did not — its extra conditions should only "
        f"REMOVE gaps: {json.dumps(r, default=list)}"
    )
    assert r["zone_mismatch"] == [], (
        f"zone bounds must be identical on the intersection: {json.dumps(r, default=list)}"
    )
    assert r["n_matched"] >= 1 and r["only_ours"], (
        "sample must exercise BOTH agreement and the displacement/mid-close filter"
    )

    # The exact, deterministic reconciliation (regression guard + the addendum's counts).
    r_sorted = {**r, "only_ours": sorted(r["only_ours"])}
    assert r_sorted == _EXPECTED_SAMPLE_RECON, json.dumps(r_sorted, default=list)


def test_vendored_reconciliation_never_consumes_mitigation():
    """The reconciliation is invariant to the vendored 'mitigated' lookahead column.

    Guards DIFFERENCE_MAP ``mitigation_lookahead``: our event shape carries only
    {ts, direction, zone_hi, zone_lo}, none of which is derived from 'mitigated'.
    """
    for e in _theirs(_SAMPLE_BARS):
        assert set(e) == {"ts", "direction", "zone_hi", "zone_lo"}

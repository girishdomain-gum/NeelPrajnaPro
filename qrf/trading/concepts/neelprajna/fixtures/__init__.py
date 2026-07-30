"""Hand-planted calibration fixtures for the liquidity_sweep detector (NP-S1,
NP-ADR-008 §5 v1.1, AC-1). Each bar sequence's true events were verified against
an oracle transcription of the evidenced source (``np_feature_service.py``)
before being frozen here as ``expected`` — this file is the independent ground
truth the detector is checked against, not derived from the detector's own
output. ``ts`` on every bar is ``TS0 + i * STEP`` (M5 step); an expected event's
``ts`` is the timestamp of its knowability bar (pool: the confirming bar; sweep:
the resolving bar) — see the detector module docstring.

Six cases exercise, respectively: a HIGH-pool single-bar sweep-and-reclose; the
LOW-side mirror; the boundary-inclusive 2-bar reclose (a reclose landing exactly
on the last bar of the reclose window still counts as a sweep, not an
invalidation); invalidation (a pool that penetrates but never recloses emits its
POOL_FORMED and no SWEEP); structured noise (isolated pivots, always further
apart than ``pool_tol`` — never forms a pool, hence total silence); and
insufficient data (fewer than ``2*pivot_k + 1`` bars — no pivot is even
computable, hence total silence, and the detector must not raise).
"""

from __future__ import annotations

import pyarrow as pa

from qrf.kernel.instruments.base import CalibrationCase

# 5 minutes per bar (M5, the frozen single timeframe); an arbitrary fixed epoch
# anchor.
STEP: int = 300 * 10**9
TS0: int = 1776729600000000000  # 2026-04-21T06:00:00Z-ish, arbitrary


def _ts(n: int) -> list[int]:
    return [TS0 + i * STEP for i in range(n)]


def bars(high: list[float], low: list[float], close: list[float]) -> pa.Table:
    """A bar table (ts + high/low/close only — the detector never reads open)."""
    n = len(high)
    assert len(low) == n and len(close) == n
    return pa.table(
        {
            "ts": pa.array(_ts(n), type=pa.int64()),
            "high": [float(x) for x in high],
            "low": [float(x) for x in low],
            "close": [float(x) for x in close],
        }
    )


def _ev(index: int, event_type: str, direction: int) -> dict:
    """An expected descriptor at knowability bar ``index``."""
    return {"ts": int(TS0 + index * STEP), "event_type": event_type, "direction": direction}


_POOL_FORMED = "neelprajna.liquidity_sweep.pool_formed"
_SWEEP = "neelprajna.liquidity_sweep.sweep"


# --- Case A: HIGH pool, single-bar sweep-and-reclose -------------------------
def _high_pool_single_bar_sweep_bars() -> pa.Table:
    # Two HIGH pivots (idx 3 -> 100.20, idx 10 -> 100.35; 0.15 apart, within the
    # 0.30 tol) form a pool at confirmation bar 13 (level = max = 100.35). Bar 14
    # penetrates (high 100.45 >= 100.35 + 0.05) and recloses same-bar
    # (close 100.30 < 100.35) -> single-bar sweep, reclose_bars=0.
    n = 15
    h = [100.00] * n
    h[3], h[10], h[14] = 100.20, 100.35, 100.45
    low = [99.50] * n  # flat -> no LOW pivots possible (equal neighbours never pivot)
    c = [100.00] * n
    c[14] = 100.30
    return bars(h, low, c)


# --- Case B: LOW pool, single-bar sweep-and-reclose (mirror) -----------------
def _low_pool_single_bar_sweep_bars() -> pa.Table:
    n = 15
    low = [100.00] * n
    low[3], low[10], low[14] = 99.80, 99.65, 99.55
    h = [100.50] * n  # flat -> no HIGH pivots
    c = [100.00] * n
    c[14] = 99.70
    return bars(h, low, c)


# --- Case C: HIGH pool, boundary-inclusive 2-bar reclose ---------------------
def _high_pool_two_bar_reclose_bars() -> pa.Table:
    # Same pool as case A (formed bar 13, level 100.35). Bar 14 penetrates,
    # does NOT reclose (close 100.40 > 100.35). Bar 15 doesn't penetrate further
    # and doesn't reclose either (close 100.37 > 100.35). Bar 16 recloses
    # (close 100.31 < 100.35) at exactly i - pen_start = 16 - 14 = 2 -- the
    # reclose_window boundary bar itself -> still a SWEEP, not an invalidation.
    n = 17
    h = [100.00] * n
    h[3], h[10] = 100.20, 100.35
    h[14], h[15], h[16] = 100.45, 100.36, 100.36
    low = [99.50] * n
    c = [100.00] * n
    c[14], c[15], c[16] = 100.40, 100.37, 100.31
    return bars(h, low, c)


# --- Case D: HIGH pool, invalidation (never recloses) ------------------------
def _high_pool_invalidation_bars() -> pa.Table:
    # Identical penetration bar 14 as case C, but bar 16's close (100.41) stays
    # above the pool price (100.35) -> at i - pen_start == 2, reclosed_now is
    # False, so the >= reclose_window branch fires: invalidation, no SWEEP event.
    # The pool's POOL_FORMED (bar 13) still fires -- formation always fires
    # regardless of the pool's eventual fate.
    n = 17
    h = [100.00] * n
    h[3], h[10] = 100.20, 100.35
    h[14], h[15], h[16] = 100.45, 100.36, 100.36
    low = [99.50] * n
    c = [100.00] * n
    c[14], c[15], c[16] = 100.40, 100.42, 100.41
    return bars(h, low, c)


# --- Case E: structured noise -- isolated pivots, always > tol apart ---------
def _noise_bars() -> pa.Table:
    # Three HIGH pivots, each 1.00 apart (>> the 0.30 tol) -> no pivot ever finds
    # a mate, so no pool ever forms and the detector is fully silent.
    n = 22
    h = [100.00] * n
    h[3], h[10], h[17] = 100.20, 101.20, 102.20
    low = [99.00] * n
    c = [100.00] * n
    return bars(h, low, c)


def liquidity_sweep_cases() -> list[CalibrationCase]:
    """Planted-truth (x4: single-bar sweep both sides, boundary reclose,
    invalidation), structured-noise silence, and insufficient-data silence."""
    return [
        CalibrationCase(
            "high_pool_single_bar_sweep_truth",
            "planted_truth",
            _high_pool_single_bar_sweep_bars(),
            [_ev(13, _POOL_FORMED, -1), _ev(14, _SWEEP, -1)],
        ),
        CalibrationCase(
            "low_pool_single_bar_sweep_truth",
            "planted_truth",
            _low_pool_single_bar_sweep_bars(),
            [_ev(13, _POOL_FORMED, 1), _ev(14, _SWEEP, 1)],
        ),
        CalibrationCase(
            "high_pool_two_bar_reclose_truth",
            "planted_truth",
            _high_pool_two_bar_reclose_bars(),
            [_ev(13, _POOL_FORMED, -1), _ev(16, _SWEEP, -1)],
        ),
        CalibrationCase(
            "high_pool_invalidation_truth",
            "planted_truth",
            _high_pool_invalidation_bars(),
            [_ev(13, _POOL_FORMED, -1)],  # POOL_FORMED only -- no SWEEP
        ),
        CalibrationCase("liquidity_sweep_noise_silence", "planted_noise", _noise_bars(), []),
        CalibrationCase(
            "liquidity_sweep_insufficient",
            "insufficient",
            bars([100.0] * 5, [99.0] * 5, [100.0] * 5),  # < 2*pivot_k+1 = 7 bars
            [],
        ),
    ]

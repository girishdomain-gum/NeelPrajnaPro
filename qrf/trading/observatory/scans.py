"""Trading-side observatory scans — descriptive FVG structure, no judgement.

ARCH-007 §2. The kernel :class:`qrf.kernel.observatory.Observatory` is
domain-blind: it records what it is handed. These functions are the domain half —
they turn real FVG events + bars into a DESCRIPTIVE ``findings`` summary the
observatory records. They compute price statistics (this is the trading plug-in,
so price vocabulary is allowed) but speak NO verdict language: no thresholds, no
PASS/FAIL, no significance claims. A scan describes; it never decides.

Two pre-declared scans (ARCH-007 §2):

* :func:`weekend_partition_scan` — do FVGs whose 3 forming bars span the weekend
  hole behave differently from intra-week ones? Partition the events by a
  weekend-spanning flag and compare their follow-through distributions.
* :func:`net_drift_scan` — does the FVG family's descriptive follow-through drift
  across 2024? Bucket the events by calendar quarter and compare.

Follow-through here is a DESCRIPTIVE forward move — ``direction * (close[k+H] -
close[k])`` over a fixed horizon H, with NO costs and NO trade simulation (that is
the battery's job, and it already ran: these scans cite H-001's verdict as
evidence, they do not re-litigate it). A seeded percentile bootstrap gives each
partition's mean a descriptive interval; the seed makes the summary reproducible.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd

# The descriptive follow-through horizon, in bars. Chosen equal to H-001's
# hold_bars (4) so the scan looks over the same forward span the verdict judged —
# but WITHOUT costs or the walk-forward engine (descriptive, not a re-run).
DEFAULT_HORIZON = 4
_BOOTSTRAP_RESAMPLES = 2000


def _finite(x: float | None) -> float | None:
    if x is None:
        return None
    xf = float(x)
    return xf if math.isfinite(xf) else None


def _spans_weekend(ts_a: int, ts_b: int, timeframe_seconds: int) -> bool:
    """True iff the gap between two adjacent forming bars crosses a weekend.

    A contiguous pair (gap == one timeframe) never spans anything. A larger gap
    spans a weekend iff any whole calendar day strictly inside the gap — or the
    endpoints' own days — is a Saturday or Sunday (UTC). This captures the Fri→Sun
    reopen hole that DEVQ-010's addendum flagged, while a mid-week holiday gap (no
    weekend day inside it) is NOT counted as weekend-spanning.
    """
    if ts_b - ts_a <= timeframe_seconds * 10**9:
        return False
    a = datetime.fromtimestamp(ts_a / 1e9, tz=UTC).date()
    b = datetime.fromtimestamp(ts_b / 1e9, tz=UTC).date()
    day = a
    while day <= b:
        if day.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            return True
        day += timedelta(days=1)
    return False


def follow_through(
    bars: pd.DataFrame, events: pd.DataFrame, *, horizon: int = DEFAULT_HORIZON
) -> pd.DataFrame:
    """Annotate each FVG event with a weekend-spanning flag + a follow-through move.

    Returns a frame with one row per event that has ``horizon`` bars of future room:
    ``ts, event_type, direction, zone_hi, zone_lo, weekend_spanning, follow_through``.
    ``follow_through = direction * (close[k+horizon] - close[k])`` where ``k`` is the
    event's knowability bar (its ts). Events without a matching bar or without
    ``horizon`` bars ahead are dropped (they have no descriptive future to measure).
    """
    bars = bars.sort_values("ts", kind="mergesort").reset_index(drop=True)
    ts_list = bars["ts"].astype("int64").tolist()
    close = bars["close"].astype(float).tolist()
    index_of = {int(t): i for i, t in enumerate(ts_list)}
    timeframe = _infer_timeframe_seconds(ts_list)

    rows = []
    for ev in events.itertuples(index=False):
        k = index_of.get(int(ev.ts))
        if k is None or k + horizon >= len(close) or k < 2:
            continue
        direction = int(ev.direction)
        move = direction * (close[k + horizon] - close[k])
        # The 3 forming bars are k-2, k-1, k (centre k-1, knowability k).
        weekend = _spans_weekend(ts_list[k - 2], ts_list[k - 1], timeframe) or _spans_weekend(
            ts_list[k - 1], ts_list[k], timeframe
        )
        rows.append(
            {
                "ts": int(ev.ts),
                "event_type": str(ev.event_type),
                "direction": direction,
                "zone_hi": float(ev.zone_hi),
                "zone_lo": float(ev.zone_lo),
                "weekend_spanning": bool(weekend),
                "follow_through": float(move),
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "ts",
            "event_type",
            "direction",
            "zone_hi",
            "zone_lo",
            "weekend_spanning",
            "follow_through",
        ],
    )


def _infer_timeframe_seconds(ts_list: list[int]) -> int:
    """The modal positive inter-bar gap, in seconds (robust to weekend holes)."""
    if len(ts_list) < 2:
        return 3600
    diffs = np.diff(np.asarray(ts_list, dtype=np.int64))
    diffs = diffs[diffs > 0]
    if diffs.size == 0:
        return 3600
    vals, counts = np.unique(diffs, return_counts=True)
    modal_ns = int(vals[int(counts.argmax())])
    return max(1, modal_ns // 10**9)


def _distribution(values: list[float], *, seed: int) -> dict:
    """Descriptive summary of a follow-through sample (count/mean/median/std + CI)."""
    x = np.asarray(values, dtype=np.float64)
    n = int(x.size)
    if n == 0:
        return {"n": 0, "mean": None, "median": None, "std": None, "ci_low": None, "ci_high": None,
                "n_positive": 0, "n_negative": 0}
    ci_low = ci_high = None
    if n >= 2:
        rng = np.random.default_rng(int(seed))
        idx = rng.integers(0, n, size=(_BOOTSTRAP_RESAMPLES, n))
        means = x[idx].mean(axis=1)
        lo, hi = np.percentile(means, [2.5, 97.5])
        ci_low, ci_high = _finite(lo), _finite(hi)
    return {
        "n": n,
        "mean": _finite(float(x.mean())),
        "median": _finite(float(np.median(x))),
        "std": _finite(float(x.std(ddof=1))) if n >= 2 else 0.0,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "n_positive": int((x > 0).sum()),
        "n_negative": int((x < 0).sum()),
    }


def weekend_partition_scan(
    bars: pd.DataFrame,
    events: pd.DataFrame,
    *,
    seed: int,
    horizon: int = DEFAULT_HORIZON,
) -> tuple[dict, pd.DataFrame]:
    """Scan (a): partition FVGs by weekend-spanning; compare follow-through.

    Returns ``(findings, annotated)`` where ``findings`` is the descriptive summary
    the observatory records and ``annotated`` is the per-event frame (for writing
    the data slices to bulk). PURELY descriptive — no threshold, no verdict word.
    """
    annotated = follow_through(bars, events, horizon=horizon)
    weekend = annotated[annotated["weekend_spanning"]]
    intra = annotated[~annotated["weekend_spanning"]]
    findings = {
        "horizon_bars": int(horizon),
        "n_events": int(len(annotated)),
        "partitions": {
            "weekend_spanning": _distribution(weekend["follow_through"].tolist(), seed=seed),
            "intra_week": _distribution(intra["follow_through"].tolist(), seed=seed),
        },
    }
    return findings, annotated


def net_drift_scan(
    bars: pd.DataFrame,
    events: pd.DataFrame,
    *,
    seed: int,
    horizon: int = DEFAULT_HORIZON,
) -> tuple[dict, pd.DataFrame]:
    """Scan (b): descriptive follow-through drift across 2024, by calendar quarter.

    Returns ``(findings, annotated)``. Buckets each event by the UTC calendar
    quarter of its knowability bar and summarises the follow-through per bucket, so
    a monotone-ish deterioration (the shape H-001's fold means showed) is visible as
    a drift in descriptive means. PURELY descriptive — cites, does not re-judge.
    """
    annotated = follow_through(bars, events, horizon=horizon)
    quarters: dict[str, list[float]] = {}
    for row in annotated.itertuples(index=False):
        dt = datetime.fromtimestamp(int(row.ts) / 1e9, tz=UTC)
        label = f"{dt.year}Q{(dt.month - 1) // 3 + 1}"
        quarters.setdefault(label, []).append(float(row.follow_through))
    buckets = {label: _distribution(vals, seed=seed) for label, vals in sorted(quarters.items())}
    means = [(label, b["mean"]) for label, b in buckets.items() if b["mean"] is not None]
    drift = None
    if len(means) >= 2:
        drift = _finite(means[-1][1] - means[0][1])
    findings = {
        "horizon_bars": int(horizon),
        "n_events": int(len(annotated)),
        "buckets_by_quarter": buckets,
        "drift_last_minus_first_mean": drift,
    }
    return findings, annotated

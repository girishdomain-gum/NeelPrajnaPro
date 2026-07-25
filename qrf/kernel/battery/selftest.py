"""Battery selftest generators + tri-state classifier (ARCH-005 §4, Blueprint §4.7 step 3).

Before the battery judges a real hypothesis it must prove — that day, on synthetic
data with a known answer — that the engine + statistics still call the three
outcomes correctly (else :class:`JudgeNotCalibratedError`, §4.7). This module
builds the three seeded suites and classifies a trade list into the tri-state:

* **PLANTED EDGE** — a real injected drift after each event; must classify PASS.
* **PURE NOISE**   — zero-mean moves; must classify FAIL (no edge).
* **SMALL-N**      — a real edge but too few trades; must classify INSUFFICIENT.

This sprint exercises ENGINE + basic statistics only (a one-sample t-test plus a
seeded bootstrap CI as groundwork). The full pre-registered verdict wiring is
Sprint 6; **no verdict record is written here** (an AST audit proves this module
cannot append one, mirroring the screener's no-verdict audit).

Firewall: this is kernel. It generates opaque numeric bar/event tables and
classifies numeric outcomes; it imports no trading code. The engine is injected as
a ``runner`` callable ``(bars, events, hold_bars) -> Sequence[float]`` returning
per-trade net outcomes — so the kernel selftest is blind to *which* simulator runs,
and the trading-side test wires the real :class:`EventEngine` in.

Calibration (recorded for ratification in DEVQ-013):
    MIN_N = 30 trades   · ALPHA = 0.05 (one-sided, H0: mean ≤ 0)
    planted edge: 60 trades, drift = 1.0, noise σ = 1.0  → t ≈ 7.7 (decisive PASS)
    pure noise:   60 trades, drift = 0.0, noise σ = 1.0  → not positive (FAIL)
    small-n:      8 trades,  drift = 1.0                 → below MIN_N (INSUFFICIENT)
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

# --- classifier calibration (DEVQ-013) --------------------------------------
MIN_N: int = 30
ALPHA: float = 0.05
_BOOTSTRAP_RESAMPLES: int = 2000

PASS = "PASS"
FAIL = "FAIL"
INSUFFICIENT = "INSUFFICIENT"

# A synthetic bar epoch and drift/size defaults for the generators.
_BASE_TS: int = 1_700_000_000_000_000_000
_BASE_LEVEL: float = 100.0

# The runner turns synthetic (bars, events, hold_bars) into per-trade net outcomes.
Runner = Callable[[pd.DataFrame, pd.DataFrame, int], Sequence[float]]


@dataclass(frozen=True)
class Suite:
    """One synthetic suite: its data, the hold it was built for, and its truth."""

    name: str
    expected: str  # PASS / FAIL / INSUFFICIENT
    bars: pd.DataFrame
    events: pd.DataFrame
    hold_bars: int


@dataclass(frozen=True)
class SuiteResult:
    """The classified outcome of running one suite through the engine."""

    name: str
    expected: str
    classification: str
    n_trades: int
    mean: float
    t_stat: float
    p_value: float  # one-sided (H0: mean <= 0)
    ci_low: float
    ci_high: float

    @property
    def ok(self) -> bool:
        return self.classification == self.expected


@dataclass(frozen=True)
class SelftestReport:
    """The plain report object — one :class:`SuiteResult` per suite plus the seed."""

    seed: int
    results: list[SuiteResult]

    @property
    def passed(self) -> bool:
        """True iff every suite classified to its expected tri-state value."""
        return all(r.ok for r in self.results)


# --- synthetic data generation ----------------------------------------------
def _episodic_bars_events(
    *,
    n_trades: int,
    hold_bars: int,
    drift: float,
    noise_sd: float,
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build independent episodes so each event yields exactly one non-overlapping trade.

    Each episode spans ``hold_bars + 2`` bars: a signal bar (carrying the event),
    an entry bar (next open, at ``_BASE_LEVEL``), then flat bars up to the exit bar
    ``hold_bars`` later, whose open is ``_BASE_LEVEL + move``. A long trade
    (size 1) therefore realises gross ``move = drift + N(0, noise_sd)`` — so the
    net-outcome mean is ``drift`` (minus whatever the injected cost model charges).
    """
    bars_per_episode = hold_bars + 2
    n_bars = n_trades * bars_per_episode
    ts = _BASE_TS + np.arange(n_bars, dtype=np.int64)
    opens = np.full(n_bars, _BASE_LEVEL, dtype=np.float64)

    moves = drift + rng.normal(0.0, noise_sd, size=n_trades)
    ev_ts: list[int] = []
    for m in range(n_trades):
        e0 = m * bars_per_episode            # signal bar
        entry_i = e0 + 1                      # entry (next open)
        exit_i = entry_i + hold_bars          # time-stop exit bar
        opens[exit_i] = _BASE_LEVEL + moves[m]
        ev_ts.append(int(ts[e0]))

    bars = pd.DataFrame(
        {
            "ts": ts,
            "open": opens,
            "high": opens,   # flat H/L: no stop/target in the selftest execution
            "low": opens,
            "close": opens,
        }
    )
    events = pd.DataFrame(
        {
            "ts": np.array(ev_ts, dtype=np.int64),
            "direction": np.ones(n_trades, dtype=np.int64),
            "strength": np.ones(n_trades, dtype=np.float64),
        }
    )
    return bars, events


def build_suites(seed: int, *, hold_bars: int = 3) -> list[Suite]:
    """Build the three seeded synthetic suites (deterministic in ``seed``)."""
    ss = np.random.SeedSequence(int(seed))
    rng_edge, rng_noise, rng_small = (np.random.default_rng(s) for s in ss.spawn(3))

    edge_bars, edge_events = _episodic_bars_events(
        n_trades=60, hold_bars=hold_bars, drift=1.0, noise_sd=1.0, rng=rng_edge
    )
    noise_bars, noise_events = _episodic_bars_events(
        n_trades=60, hold_bars=hold_bars, drift=0.0, noise_sd=1.0, rng=rng_noise
    )
    small_bars, small_events = _episodic_bars_events(
        n_trades=8, hold_bars=hold_bars, drift=1.0, noise_sd=1.0, rng=rng_small
    )
    return [
        Suite("planted_edge", PASS, edge_bars, edge_events, hold_bars),
        Suite("pure_noise", FAIL, noise_bars, noise_events, hold_bars),
        Suite("small_n", INSUFFICIENT, small_bars, small_events, hold_bars),
    ]


# --- statistics + tri-state classifier --------------------------------------
def _bootstrap_ci(x: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    """A seeded 95% percentile bootstrap CI for the mean (groundwork for §4.7 step 6)."""
    if len(x) < 2:
        return (float("nan"), float("nan"))
    idx = rng.integers(0, len(x), size=(_BOOTSTRAP_RESAMPLES, len(x)))
    means = x[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return (float(lo), float(hi))


def classify(net_outcomes: Sequence[float], *, seed: int) -> SuiteResult:
    """Classify per-trade net outcomes into PASS / FAIL / INSUFFICIENT.

    * fewer than ``MIN_N`` trades → INSUFFICIENT (the sample floor dominates);
    * else a one-sided one-sample t-test (H0: mean ≤ 0): a mean above zero that is
      significant at ``ALPHA`` → PASS; otherwise FAIL.

    ``seed`` seeds the bootstrap CI so the report is reproducible. The name field is
    filled by :func:`run_selftest`; here it is left blank.
    """
    x = np.asarray(list(net_outcomes), dtype=np.float64)
    n = int(x.size)
    rng = np.random.default_rng(int(seed))

    if n < MIN_N:
        mean = float(x.mean()) if n else 0.0
        lo, hi = _bootstrap_ci(x, rng) if n else (float("nan"), float("nan"))
        return SuiteResult("", "", INSUFFICIENT, n, mean, float("nan"), float("nan"), lo, hi)

    mean = float(x.mean())
    sd = float(x.std(ddof=1))
    lo, hi = _bootstrap_ci(x, rng)

    # Zero-variance degeneracy (identical outcomes — a synthetic artifact, never
    # real market data): the t-test is undefined, so decide on the sign alone.
    scale = 1e-12 * (abs(mean) + 1.0)
    if sd <= scale:
        positive = mean > 0
        classification = PASS if positive else FAIL
        t = float("inf") if positive else float("-inf")
        p = 0.0 if positive else 1.0
        return SuiteResult("", "", classification, n, mean, t, p, lo, hi)

    t_stat, p_two = stats.ttest_1samp(x, 0.0)
    # One-sided p for the alternative mean > 0.
    p_one = float(p_two / 2 if mean > 0 else 1.0 - p_two / 2)
    classification = PASS if (mean > 0 and p_one < ALPHA) else FAIL
    return SuiteResult("", "", classification, n, mean, float(t_stat), p_one, lo, hi)


def run_selftest(runner: Runner, *, seed: int, hold_bars: int = 3) -> SelftestReport:
    """Generate the three suites, run each through ``runner``, and classify.

    ``runner(bars, events, hold_bars) -> Sequence[float]`` is the injected audited
    engine (wired trading-side). Returns a :class:`SelftestReport`; ``report.passed``
    is the day's calibration gate (Blueprint §4.7 step 3). Writes no records.
    """
    results: list[SuiteResult] = []
    for suite in build_suites(seed, hold_bars=hold_bars):
        net_outcomes = runner(suite.bars, suite.events, suite.hold_bars)
        r = classify(net_outcomes, seed=seed)
        results.append(
            SuiteResult(
                name=suite.name,
                expected=suite.expected,
                classification=r.classification,
                n_trades=r.n_trades,
                mean=r.mean,
                t_stat=r.t_stat,
                p_value=r.p_value,
                ci_low=r.ci_low,
                ci_high=r.ci_high,
            )
        )
    return SelftestReport(seed=int(seed), results=results)

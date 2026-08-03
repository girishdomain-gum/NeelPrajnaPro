"""Order Block detector (M6, origin-candle method), implementing the
Detector SDK (AM-01) against docs/detectors/order_block.md (APPROVED
WITH CHANGES, A-019 R1/R3/R4) -- re-implemented from that document
alone, never from any previous-era code (AM-02), and never from "the
range" method (a different, unbuilt detector).

Rule: swings (SWING_K=3, confirmed at i+SWING_K, independently declared
-- see MSS's own note on why the same value is not a shared dependency).
A structure break at bar b is a close strictly beyond the most recently
confirmed, NOT-YET-CONSUMED swing high (bullish) or low (bearish). The
origin candle is the NEAREST opposite-colored candle in [s, b-1], where s
is the broken swing's own formation index (A-019 R1: the search is
bounded by the swing being broken, not an arbitrary lookback). The block
zone is that candle's own [low, high].

A-020 R1: a swing is CONSUMED by the break that breaks it -- once used,
it can never break again; the next break on that side requires a NEWLY
confirmed swing. Without this, a sustained trend re-breaks the SAME
already-broken swing on every subsequent bar (1,624 order blocks in
5,000 real bars was the evidence this was wrong -- one every three bars,
which cannot be a real impulsive move). Mirrors S02's window-burns-on-use
and the sweep detector's resolved-pool-cannot-be-swept-twice principle.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from qrf.kernel.detection.interface import Detector
from qrf.kernel.detection.types import Bar, DetectorConfig, Observation, ObservationSet

DETECTOR_NAME = "order_block"
DETECTOR_VERSION = "M6-v1-origin-candle"

SWING_K = 3  # same value as market_structure_shift's own SWING_K, by
# coincidence of reasoning, not a shared dependency (A-019 R3).

BULLISH = "BULLISH"
BEARISH = "BEARISH"


@dataclass(frozen=True)
class OrderBlockObservation(Observation):
    side: str = BULLISH
    origin_bar: int = 0
    break_bar: int = 0
    broken_swing_bar: int = 0
    zone_low: float = 0.0
    zone_high: float = 0.0


def _is_swing_high(highs: Sequence[float], i: int, k: int) -> bool:
    v = highs[i]
    return all(v > highs[j] for j in range(i - k, i)) and all(
        v > highs[j] for j in range(i + 1, i + k + 1)
    )


def _is_swing_low(lows: Sequence[float], i: int, k: int) -> bool:
    v = lows[i]
    return all(v < lows[j] for j in range(i - k, i)) and all(
        v < lows[j] for j in range(i + 1, i + k + 1)
    )


def _find_origin_candle(opens, closes, s: int, b: int, want_bearish: bool) -> int | None:
    """Nearest bar j in [s, b-1] whose color is opposite the break
    direction -- searched from b-1 DOWN TO s (nearest first). Dojis
    (open == close) are skipped, never matched, never stop the search.
    """
    for j in range(b - 1, s - 1, -1):
        if want_bearish and closes[j] < opens[j]:
            return j
        if not want_bearish and closes[j] > opens[j]:
            return j
    return None


def _run(bars: Sequence[Bar]) -> list[OrderBlockObservation]:
    n = len(bars)
    highs = [bar.high for bar in bars]
    lows = [bar.low for bar in bars]
    opens = [bar.open for bar in bars]
    closes = [bar.close for bar in bars]

    swing_high_confirm: dict[int, int] = {}
    swing_low_confirm: dict[int, int] = {}
    for i in range(SWING_K, n - SWING_K):
        c = i + SWING_K
        if _is_swing_high(highs, i, SWING_K):
            swing_high_confirm[c] = i
        if _is_swing_low(lows, i, SWING_K):
            swing_low_confirm[c] = i

    observations: list[OrderBlockObservation] = []
    last_swing_high: tuple[int, float] | None = None  # (formation_bar, price)
    last_swing_low: tuple[int, float] | None = None

    for b in range(n):
        if b in swing_high_confirm:
            last_swing_high = (swing_high_confirm[b], highs[swing_high_confirm[b]])
        if b in swing_low_confirm:
            last_swing_low = (swing_low_confirm[b], lows[swing_low_confirm[b]])

        if last_swing_high is not None and closes[b] > last_swing_high[1]:
            s = last_swing_high[0]
            origin = _find_origin_candle(opens, closes, s, b, want_bearish=True)
            if origin is not None:
                observations.append(
                    OrderBlockObservation(
                        kind="ORDER_BLOCK_FORMED",
                        side=BULLISH,
                        origin_bar=origin,
                        break_bar=b,
                        broken_swing_bar=s,
                        zone_low=lows[origin],
                        zone_high=highs[origin],
                    )
                )
            # A-020 R1: the swing is CONSUMED by this break, whether or not
            # an origin candle was found -- it can never break again until
            # a new swing high confirms.
            last_swing_high = None

        if last_swing_low is not None and closes[b] < last_swing_low[1]:
            s = last_swing_low[0]
            origin = _find_origin_candle(opens, closes, s, b, want_bearish=False)
            if origin is not None:
                observations.append(
                    OrderBlockObservation(
                        kind="ORDER_BLOCK_FORMED",
                        side=BEARISH,
                        origin_bar=origin,
                        break_bar=b,
                        broken_swing_bar=s,
                        zone_low=lows[origin],
                        zone_high=highs[origin],
                    )
                )
            last_swing_low = None  # A-020 R1: consumed, same as above.

    return observations


class OrderBlockDetector(Detector):
    def detect(self, data: Sequence[Bar], config: DetectorConfig) -> ObservationSet:
        observations = _run(data)
        return ObservationSet(
            detector_name=DETECTOR_NAME,
            detector_version=DETECTOR_VERSION,
            source_sha256=config.source_sha256,
            span_start_utc=config.span_start_utc,
            span_end_utc=config.span_end_utc,
            observations=tuple(observations),
        )

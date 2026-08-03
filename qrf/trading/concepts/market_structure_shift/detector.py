"""Market Structure Shift detector (M5), implementing the Detector SDK
(AM-01) against docs/detectors/market_structure_shift.md (APPROVED,
A-019 R2/R3/R4) -- re-implemented from that document alone, never from
any previous-era code (AM-02).

Prevailing structure (BULLISH/BEARISH/UNDEFINED) is derived from the two
most recently confirmed swings of each type (SWING_K=3, independently
declared -- same value as order_block's own SWING_K by coincidence of
reasoning, not a shared dependency, A-019 R3). A shift is a close
breaking the structure-defining swing in the opposing direction.
UNDEFINED structure can never shift (the mechanical proxy for LS-01
Sec1.6's choppy/directionless boundary).

A-019 R2 (confirmed by ruling): after a shift, prevailing resets to
UNDEFINED and stays there until BOTH the most recent confirmed swing
high AND the most recent confirmed swing low have confirmed AFTER the
reset bar -- i.e. genuinely new swings, not a re-read of the same pair
that just broke. This is what makes "two breaks in a row from
incoherent structure yield ONE event, not two" true: the second break
finds prevailing still UNDEFINED, since no new qualifying swing pair has
had a chance to confirm yet.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from qrf.kernel.detection.interface import Detector
from qrf.kernel.detection.types import Bar, DetectorConfig, Observation, ObservationSet

DETECTOR_NAME = "market_structure_shift"
DETECTOR_VERSION = "M5-v1-simplest"

SWING_K = 3  # same value as order_block's own SWING_K, by coincidence of
# reasoning, not a shared dependency (A-019 R3).

BULLISH = "BULLISH"
BEARISH = "BEARISH"
UNDEFINED = "UNDEFINED"


@dataclass(frozen=True)
class StructureShiftObservation(Observation):
    shift_direction: str = BULLISH
    prevailing_before: str = BULLISH
    broken_swing_bar: int = 0
    broken_swing_price: float = 0.0
    shift_bar: int = 0


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


def _run(bars: Sequence[Bar]) -> list[StructureShiftObservation]:
    n = len(bars)
    highs = [bar.high for bar in bars]
    lows = [bar.low for bar in bars]
    closes = [bar.close for bar in bars]

    swing_high_confirm: dict[int, int] = {}
    swing_low_confirm: dict[int, int] = {}
    for i in range(SWING_K, n - SWING_K):
        c = i + SWING_K
        if _is_swing_high(highs, i, SWING_K):
            swing_high_confirm[c] = i
        if _is_swing_low(lows, i, SWING_K):
            swing_low_confirm[c] = i

    observations: list[StructureShiftObservation] = []
    # each entry: (formation_bar, confirm_bar, price)
    highs_hist: list[tuple[int, int, float]] = []
    lows_hist: list[tuple[int, int, float]] = []
    prevailing = UNDEFINED
    reset_bar = -1

    for b in range(n):
        if b in swing_high_confirm:
            fb = swing_high_confirm[b]
            highs_hist.append((fb, b, highs[fb]))
        if b in swing_low_confirm:
            fb = swing_low_confirm[b]
            lows_hist.append((fb, b, lows[fb]))

        if prevailing == UNDEFINED and len(highs_hist) >= 2 and len(lows_hist) >= 2:
            newest_high, prev_high = highs_hist[-1], highs_hist[-2]
            newest_low, prev_low = lows_hist[-1], lows_hist[-2]
            if newest_high[1] > reset_bar and newest_low[1] > reset_bar:
                if newest_high[2] > prev_high[2] and newest_low[2] > prev_low[2]:
                    prevailing = BULLISH
                elif newest_high[2] < prev_high[2] and newest_low[2] < prev_low[2]:
                    prevailing = BEARISH

        if prevailing == BULLISH and lows_hist and closes[b] < lows_hist[-1][2]:
            broken = lows_hist[-1]
            observations.append(
                StructureShiftObservation(
                    kind="STRUCTURE_SHIFT",
                    shift_direction=BEARISH,
                    prevailing_before=BULLISH,
                    broken_swing_bar=broken[0],
                    broken_swing_price=broken[2],
                    shift_bar=b,
                )
            )
            prevailing = UNDEFINED
            reset_bar = b
        elif prevailing == BEARISH and highs_hist and closes[b] > highs_hist[-1][2]:
            broken = highs_hist[-1]
            observations.append(
                StructureShiftObservation(
                    kind="STRUCTURE_SHIFT",
                    shift_direction=BULLISH,
                    prevailing_before=BEARISH,
                    broken_swing_bar=broken[0],
                    broken_swing_price=broken[2],
                    shift_bar=b,
                )
            )
            prevailing = UNDEFINED
            reset_bar = b

    return observations


class MarketStructureShiftDetector(Detector):
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

"""Fair Value Gap detector (M7), implementing the Detector SDK (AM-01)
against docs/detectors/fair_value_gap.md (APPROVED, A-019) --
re-implemented from that document alone, never from any previous-era
code (AM-02).

Rule: bars (i, i+1, i+2) form a BULLISH gap iff high[i] < low[i+2]; a
BEARISH gap iff low[i] > high[i+2]. Middle bar has no shape requirement.
Strict inequality only -- touching bars are not a gap. See the
definition document for the full reasoning, exclusions, and the
low-vs-high mirror-comparison trap.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from qrf.kernel.detection.interface import Detector
from qrf.kernel.detection.types import Bar, DetectorConfig, Observation, ObservationSet

DETECTOR_NAME = "fair_value_gap"
DETECTOR_VERSION = "M7-v1-glossary"

BULLISH = "BULLISH"
BEARISH = "BEARISH"


@dataclass(frozen=True)
class FVGObservation(Observation):
    side: str = BULLISH
    first_bar: int = 0
    third_bar: int = 0
    gap_low: float = 0.0
    gap_high: float = 0.0
    gap_size: float = 0.0


def _run(bars: Sequence[Bar]) -> list[FVGObservation]:
    observations: list[FVGObservation] = []
    n = len(bars)
    for i in range(n - 2):
        b1, b3 = bars[i], bars[i + 2]
        if b1.high < b3.low:
            gap_low, gap_high = b1.high, b3.low
            observations.append(
                FVGObservation(
                    kind="FVG_FORMED",
                    side=BULLISH,
                    first_bar=i,
                    third_bar=i + 2,
                    gap_low=gap_low,
                    gap_high=gap_high,
                    gap_size=gap_high - gap_low,
                )
            )
        if b1.low > b3.high:
            gap_low, gap_high = b3.high, b1.low
            observations.append(
                FVGObservation(
                    kind="FVG_FORMED",
                    side=BEARISH,
                    first_bar=i,
                    third_bar=i + 2,
                    gap_low=gap_low,
                    gap_high=gap_high,
                    gap_size=gap_high - gap_low,
                )
            )
    return observations


class FairValueGapDetector(Detector):
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

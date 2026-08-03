"""The Detector interface (AM-01). One method, deliberately.

C2, PURE AND DETERMINISTIC: `detect()` must be a pure function of
(data, config) -- same inputs produce a byte-identical `ObservationSet`.
No clocks, no randomness, no hidden state, no I/O inside it. This is not
merely a convention: every conforming detector's test suite must include
a determinism drill (run twice, assert equal) -- see
tests/trading/concepts/liquidity_sweep/test_detector.py for the sweep
detector's.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from qrf.kernel.detection.types import Bar, DetectorConfig, ObservationSet


class Detector(ABC):
    @abstractmethod
    def detect(self, data: Sequence[Bar], config: DetectorConfig) -> ObservationSet:
        """Return this detector's ObservationSet for `data`, bound to
        `config`'s provenance. Must be pure (C2): no I/O, no randomness,
        no clock reads, no mutation of `data`.
        """

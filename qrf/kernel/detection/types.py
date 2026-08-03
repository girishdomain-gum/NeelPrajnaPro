"""Detector SDK types (AM-01). The JUDGE's vocabulary for what a detector
may report -- deliberately minimal (AM-01: "define ONLY what this
detector needs"), not a speculative model of ten future detectors.

C1, PROVENANCE-CARRYING: every ObservationSet carries the source
dataset's sha256 and the span it covers, so an observation can never
float free of the evidence that produced it.

C3, NO SELF-VOUCHING: `Observation` and `ObservationSet` have NO
significance/edge/hit-rate/win-rate/profitability field, anywhere, ever.
A detector reports WHAT IT SAW and WHERE -- nothing about whether it
mattered. Enforced structurally: these dataclasses are `frozen=True` with
a fixed, closed field set (`__slots__`-equivalent via dataclass fields),
so a caller cannot even monkey-patch an extra field onto an instance.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Bar:
    """One OHLC bar. `time` is the bar's own epoch second (server time, as
    recorded by S03's exporter) -- this SDK does not interpret or correct
    it; that is the caller's concern, not the detector's.
    """

    time: int
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class DetectorConfig:
    """Everything a detector needs to know about its input's PROVENANCE,
    supplied by the caller -- never derived inside `detect()`, which must
    stay a pure function with no I/O (C2).
    """

    source_sha256: str
    span_start_utc: int
    span_end_utc: int


@dataclass(frozen=True)
class Observation:
    """One thing a detector saw. Fields are detector-specific beyond the
    base identity (`kind`); see each detector's own module for what its
    observations carry. NEVER add a significance/edge/outcome field here
    or to any subtype -- that is C3's whole point.
    """

    kind: str


@dataclass(frozen=True)
class ObservationSet:
    """The complete, provenance-bound output of one `detect()` call."""

    detector_name: str
    detector_version: str
    source_sha256: str
    span_start_utc: int
    span_end_utc: int
    observations: tuple[Observation, ...]

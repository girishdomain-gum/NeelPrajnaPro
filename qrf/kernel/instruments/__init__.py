"""Instrument layer: detector contract, EventFrame, registry, calibration.

Implementation Blueprint v1.0 §4.3/§4.4. Kernel and domain-blind.
"""

from __future__ import annotations

from qrf.kernel.instruments.base import (
    CALIBRATION_CASE_KINDS,
    EVENTFRAME_COLUMNS,
    EVENTFRAME_SCHEMA,
    CalibrationCase,
    Detector,
    build_event_frame,
    empty_event_frame,
    validate_event_frame,
)
from qrf.kernel.instruments.calibration import CalibrationHarness, descriptors
from qrf.kernel.instruments.registry import InstrumentInfo, InstrumentRegistry

__all__ = [
    "CALIBRATION_CASE_KINDS",
    "EVENTFRAME_COLUMNS",
    "EVENTFRAME_SCHEMA",
    "CalibrationCase",
    "CalibrationHarness",
    "Detector",
    "InstrumentInfo",
    "InstrumentRegistry",
    "build_event_frame",
    "descriptors",
    "empty_event_frame",
    "validate_event_frame",
]

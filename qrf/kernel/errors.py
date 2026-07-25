"""QRF error taxonomy — Implementation Blueprint v1.0 §6.

Every kernel error derives from :class:`QRFError`. Policy (Blueprint §6):
integrity errors halt loudly; refusal errors (burned, unfrozen, uncalibrated)
are expected control flow whose messages name the exact record ids involved.

This module is stdlib-only so any layer may import it without pulling in the
rest of the kernel.
"""

from __future__ import annotations


class QRFError(Exception):
    """Root of the QRF error hierarchy."""


# --- Contract / schema -------------------------------------------------------
class SchemaViolation(QRFError):
    """A payload or EventFrame broke its registered schema contract."""


# --- Lookup ------------------------------------------------------------------
class UnknownRecordError(QRFError):
    """A referenced ``record_id`` does not exist in the store."""


class UnknownParentError(QRFError):
    """A record was appended naming a parent that does not exist (I-3)."""


class UnknownInstrumentError(QRFError):
    """A referenced instrument is not in the registry."""


# --- Integrity (fatal; halt) -------------------------------------------------
class LedgerIntegrityError(QRFError):
    """The journal hash chain is broken. Fatal — halt and investigate."""


class BulkIntegrityError(QRFError):
    """A parquet file's bytes do not match its manifest sha256. Fatal for that file."""


# --- Calibration / refusal (expected control flow) ---------------------------
class UncalibratedInstrumentError(QRFError):
    """An instrument's thermometer test is missing or stale."""


class JudgeNotCalibratedError(QRFError):
    """The battery selftest failed today; abort the run."""


class TamperedHypothesisError(QRFError):
    """A frozen hypothesis file no longer matches its ledger hash."""


class WindowBurnedError(QRFError):
    """Out-of-sample reuse refused: the window was already burned for this lineage."""


class ContaminationError(QRFError):
    """The observatory touched a VIRGIN-designated window."""


class AlreadyJudgedError(QRFError):
    """A verdict re-run was refused: this (hypothesis, window) already has a verdict."""


class GraduationRefused(QRFError):
    """A promotion was refused: one of its four graduation gates did not hold."""


# --- Firewall (CI-time) ------------------------------------------------------
class FirewallViolation(QRFError):
    """Kernel code imported domain code, or used forbidden domain vocabulary."""

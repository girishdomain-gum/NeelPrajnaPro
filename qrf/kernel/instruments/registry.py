"""InstrumentRegistry — register instruments and gate their use on calibration.

Implementation Blueprint v1.0 §4.4. Registering an instrument appends an
``instrument_registered`` record; the record's id is the instrument's
``instrument_ref`` used everywhere downstream. Because a version bump produces a
*new* registration record (a new ref), any prior ``calibration`` — which names
the old ref — no longer counts, so ``is_calibrated`` goes false until the new
version is calibrated (ARCH-002 AC).

The registry is also the gate: :meth:`require_calibrated` (and the convenience
:meth:`run_detector`) raise :class:`UncalibratedInstrumentError` when an
instrument has no passing, in-date calibration — a failed calibration is stored
but never counts (no soft-pass, §4.4).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pyarrow as pa

from qrf.kernel.errors import UncalibratedInstrumentError, UnknownInstrumentError
from qrf.kernel.records.record import Record, now_ns
from qrf.kernel.records.store import RecordStore

# One day in integer nanoseconds — for the max_age_days staleness check.
_NS_PER_DAY = 86_400 * 1_000_000_000


@dataclass(frozen=True)
class InstrumentInfo:
    """What the registry knows about one registered (instrument_id, version)."""

    instrument_id: str
    version: str
    kind: str
    params_schema: dict[str, Any]
    code_ref: str
    record_id: str  # == instrument_ref (the instrument_registered record id)
    detector: Any | None = None  # the live object, when registered from one


class InstrumentRegistry:
    """Registers instruments and answers calibration status (Blueprint §4.4)."""

    def __init__(self, store: RecordStore) -> None:
        self._store = store
        self._by_ref: dict[str, InstrumentInfo] = {}
        self._by_id_version: dict[tuple[str, str], InstrumentInfo] = {}
        self._latest_version: dict[str, str] = {}

    # -- registration ---------------------------------------------------------
    def register(
        self,
        inst: Any,
        *,
        producer: str = "human:bootstrap",
        event_ts: int | None = None,
    ) -> Record:
        """Append an ``instrument_registered`` record for ``inst`` and index it.

        ``inst`` supplies ``instrument_id``, ``version`` and (optionally)
        ``params_schema`` / ``kind`` / ``code_ref``; sensible kernel-blind
        defaults are used when absent. Returns the registration record whose id
        is the instrument_ref.
        """
        instrument_id = inst.instrument_id
        version = inst.version
        kind = getattr(inst, "kind", "detector")
        params_schema = dict(getattr(inst, "params_schema", {}))
        code_ref = getattr(inst, "code_ref", f"{type(inst).__module__}:{type(inst).__qualname__}")

        rec = self._store.append(
            "instrument_registered",
            {
                "instrument_id": instrument_id,
                "kind": kind,
                "version": version,
                "params_schema": params_schema,
                "code_ref": code_ref,
            },
            producer=producer,
            event_ts=event_ts if event_ts is not None else now_ns(),
        )
        info = InstrumentInfo(
            instrument_id=instrument_id,
            version=version,
            kind=kind,
            params_schema=params_schema,
            code_ref=code_ref,
            record_id=rec.record_id,
            detector=inst,
        )
        self._by_ref[rec.record_id] = info
        self._by_id_version[(instrument_id, version)] = info
        self._latest_version[instrument_id] = version
        return rec

    # -- lookup ---------------------------------------------------------------
    def get(self, instrument_id: str, version: str | None = None) -> InstrumentInfo:
        """Return the :class:`InstrumentInfo` for an instrument.

        ``version=None`` returns the most recently registered version. Raises
        :class:`UnknownInstrumentError` if the instrument (or version) is unknown.
        """
        if version is None:
            version = self._latest_version.get(instrument_id)
            if version is None:
                raise UnknownInstrumentError(
                    f"no instrument registered with id {instrument_id!r}"
                )
        try:
            return self._by_id_version[(instrument_id, version)]
        except KeyError as e:
            raise UnknownInstrumentError(
                f"instrument {instrument_id!r} has no registered version {version!r}"
            ) from e

    def info_for_ref(self, instrument_ref: str) -> InstrumentInfo:
        """Return the :class:`InstrumentInfo` for an instrument_ref (record id)."""
        try:
            return self._by_ref[instrument_ref]
        except KeyError as e:
            raise UnknownInstrumentError(
                f"no instrument registered under ref {instrument_ref!r}"
            ) from e

    # -- calibration status ---------------------------------------------------
    def is_calibrated(self, instrument_ref: str, max_age_days: int | None = None) -> bool:
        """True iff ``instrument_ref`` has a passing calibration within max age.

        Scans ``calibration`` records naming this ref; a record counts only when
        ``overall_pass`` is true (no soft-pass) and, if ``max_age_days`` is given,
        its ``event_ts`` is no older than that many days. A failed calibration
        never counts; a version bump (new ref) starts uncalibrated.
        """
        if instrument_ref not in self._by_ref:
            raise UnknownInstrumentError(
                f"no instrument registered under ref {instrument_ref!r}"
            )
        cutoff_ns: int | None = None
        if max_age_days is not None:
            cutoff_ns = now_ns() - max_age_days * _NS_PER_DAY
        for rec in self._store.query(record_type="calibration"):
            payload = rec.payload
            if payload.get("instrument_ref") != instrument_ref:
                continue
            if not payload.get("overall_pass"):
                continue
            if cutoff_ns is not None and rec.event_ts < cutoff_ns:
                continue
            return True
        return False

    def require_calibrated(self, instrument_ref: str, max_age_days: int | None = None) -> None:
        """Raise :class:`UncalibratedInstrumentError` unless calibrated (the gate)."""
        if not self.is_calibrated(instrument_ref, max_age_days):
            info = self._by_ref.get(instrument_ref)
            ident = f"{info.instrument_id}@{info.version}" if info else instrument_ref
            raise UncalibratedInstrumentError(
                f"instrument {ident} (ref {instrument_ref}) has no passing, in-date "
                "calibration; register + calibrate before use (no soft-pass)"
            )

    # -- gated use ------------------------------------------------------------
    def run_detector(
        self, instrument_ref: str, data: pa.Table, *, max_age_days: int | None = None
    ) -> pa.Table:
        """Calibration-gated ``detect``: refuse an uncalibrated instrument.

        This is the record-producing-call-path guard of §4.4 made concrete for
        Sprint 2 — any real use of a detector goes through the gate first.
        """
        self.require_calibrated(instrument_ref, max_age_days)
        info = self.info_for_ref(instrument_ref)
        if info.detector is None:
            raise UnknownInstrumentError(
                f"instrument ref {instrument_ref} has no live detector object to run"
            )
        return info.detector.detect(data)

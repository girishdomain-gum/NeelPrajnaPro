"""WindowLedger — designate data windows and refuse out-of-sample reuse.

Implementation Blueprint v1.0 §4.6. A ``window`` record marks a ``[ts_start,
ts_end)`` slice of a dataset with a designation (TRAINING / EXPLORATION /
VIRGIN). A ``window_burn`` record marks that a window was consumed by a verdict
for a given *lineage*; once burned, any window on the same dataset whose
interval intersects a burned interval *for that lineage* is refused
(:class:`WindowBurnedError`) — the mechanism that prevents silently reusing
out-of-sample data.

Interval convention: windows are half-open ``[ts_start, ts_end)``. Two
intervals intersect iff ``a_start < b_end and b_start < a_end`` — so windows
that merely *touch* at an endpoint (``a_end == b_start``) do not conflict.

Lineage is a plain string this sprint (Blueprint §4.6: "lineage = plain string
this sprint"); declared-ancestor expansion arrives with the battery in
Sprint 5/6. :meth:`burn` exists and is unit-tested here, but the only
production caller is the battery (§4.7 step 9) which does not exist yet.

This module is kernel: records layer + error taxonomy + stdlib only.
"""

from __future__ import annotations

from qrf.kernel.errors import (
    ContaminationError,
    SchemaViolation,
    WindowBurnedError,
)
from qrf.kernel.records.record import Record, now_ns
from qrf.kernel.records.store import RecordStore

_DESIGNATIONS = frozenset({"TRAINING", "EXPLORATION", "VIRGIN"})


def _intervals_intersect(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    """True iff the half-open intervals ``[a_start, a_end)`` and ``[b_start, b_end)`` overlap."""
    return a_start < b_end and b_start < a_end


class WindowLedger:
    """Designate windows and enforce burn/contamination rules (Blueprint §4.6)."""

    def __init__(self, store: RecordStore) -> None:
        self._store = store

    # -- designation ----------------------------------------------------------
    def designate(
        self,
        dataset: str,
        ts_start: int,
        ts_end: int,
        designation: str,
        *,
        producer: str = "human:protocol",
        parents: list[str] | tuple[str, ...] = (),
        event_ts: int | None = None,
    ) -> Record:
        """Append a ``window`` record for ``[ts_start, ts_end)`` of ``dataset``.

        ``parents`` are the ``bulk_manifest`` records the window covers
        (Blueprint §2 typical parents). ``designation`` must be one of
        TRAINING / EXPLORATION / VIRGIN.
        """
        if designation not in _DESIGNATIONS:
            raise SchemaViolation(
                f"designation {designation!r} must be one of {sorted(_DESIGNATIONS)}"
            )
        payload = {
            "dataset": dataset,
            "ts_start": int(ts_start),
            "ts_end": int(ts_end),
            "designation": designation,
        }
        return self._store.append(
            "window",
            payload,
            producer=producer,
            event_ts=event_ts if event_ts is not None else now_ns(),
            parents=list(parents),
        )

    # -- availability ---------------------------------------------------------
    def _window(self, window_ref: str) -> Record:
        rec = self._store.get(window_ref)
        if rec.record_type != "window":
            raise SchemaViolation(
                f"record {window_ref} is a {rec.record_type!r}, not a window"
            )
        return rec

    def check_available(self, window_ref: str, lineage: str) -> None:
        """Raise :class:`WindowBurnedError` if ``window_ref`` overlaps a prior burn.

        Only burns for the same ``lineage`` and the same ``dataset`` are
        considered; a burned interval that intersects this window's interval
        refuses reuse (out-of-sample protection).
        """
        w = self._window(window_ref)
        dataset = w.payload["dataset"]
        a_start, a_end = w.payload["ts_start"], w.payload["ts_end"]

        for burn in self._store.query(record_type="window_burn"):
            if burn.payload["lineage"] != lineage:
                continue
            burned = self._window(burn.payload["window_ref"])
            if burned.payload["dataset"] != dataset:
                continue
            b_start, b_end = burned.payload["ts_start"], burned.payload["ts_end"]
            if _intervals_intersect(a_start, a_end, b_start, b_end):
                raise WindowBurnedError(
                    f"window {window_ref} [{a_start},{a_end}) on dataset {dataset!r} "
                    f"overlaps a prior burn for lineage {lineage!r}: burn "
                    f"{burn.record_id} of window {burned.record_id} "
                    f"[{b_start},{b_end}) — out-of-sample reuse refused"
                )

    # -- burn (battery-only in production; unit-tested here) -------------------
    def burn(self, window_ref: str, lineage: str, verdict_ref: str) -> Record:
        """Append a ``window_burn`` marking ``window_ref`` consumed for ``lineage``.

        Parents are the window and the consuming verdict. Both must exist (I-3).
        In production this is called only by the battery (§4.7 step 9).
        """
        self._window(window_ref)  # existence + type check
        payload = {
            "window_ref": window_ref,
            "lineage": lineage,
            "consumed_by": verdict_ref,
        }
        return self._store.append(
            "window_burn",
            payload,
            producer="battery",
            event_ts=now_ns(),
            parents=[window_ref, verdict_ref],
        )

    # -- observatory guard ----------------------------------------------------
    def guard_observatory(self, window_ref: str) -> None:
        """Raise :class:`ContaminationError` if ``window_ref`` is VIRGIN-designated.

        The observatory may only probe TRAINING/EXPLORATION data (Blueprint §2,
        §4.8): touching a VIRGIN reserve would contaminate the out-of-sample set.
        """
        w = self._window(window_ref)
        if w.payload["designation"] == "VIRGIN":
            raise ContaminationError(
                f"window {window_ref} is VIRGIN-designated; the observatory must "
                "not read it (contamination of the out-of-sample reserve)"
            )

    def check_screenable(self, window_ref: str) -> str:
        """Return the designation of ``window_ref`` if it may be screened.

        The screener is a telescope, not a judge (Blueprint §5 arrow 8): it may
        sweep only TRAINING/EXPLORATION data. A VIRGIN window raises
        :class:`ContaminationError` — screening it would spend the out-of-sample
        reserve without a pre-registered hypothesis. Returns the designation
        (``"TRAINING"`` or ``"EXPLORATION"``) on success.
        """
        w = self._window(window_ref)
        designation = w.payload["designation"]
        if designation == "VIRGIN":
            raise ContaminationError(
                f"window {window_ref} is VIRGIN-designated; the screener must not "
                "read it (screening spends no window, but touching VIRGIN outside a "
                "pre-registered battery run contaminates the out-of-sample reserve)"
            )
        return designation

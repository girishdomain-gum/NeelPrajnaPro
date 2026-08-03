"""Window ledger: market time as a spendable, accounted resource.

A WINDOW is a span of market time with a label — TRAINING, EXPLORATION, or
VIRGIN. Only VIRGIN time may ever back a verdict, and using it BURNS the
window: it can never be virgin again, for any hypothesis, ever. This
module builds the mechanism only (A-004 §4.3) — no Owner ceremony, no
registration, no alpha; designation here is a plain function call.

Built entirely on qrf.kernel.records.store.RecordStore: every guarantee
the record store makes (hash-chained, single-writer, torn-tail detection)
applies to this ledger unmodified. This module only defines the payload
schema and interprets the resulting chain into a window state machine.

ATOMICITY ARGUMENT for burn-on-use (A-004 §4.2a): "consume" and "burn" are
not two steps — burning IS the act of using a window as evidence; there is
no separate prior "consumed" state. The only way a window becomes burned
is a single RecordStore.append() call, which is itself atomic at the file
level (one line, written then fsync'd before the writer lock is released).
A crash during that append therefore has exactly two possible outcomes,
never a third: the line lands completely (the window is burned, full
stop), or it does not land at all — RecordStore.verify() detects the
incomplete trailing bytes as a TornTail and refuses every further
operation until `RecordStore.recover_torn_tail()` truncates it away, after
which the window is exactly as if burn() had never been called. There is
no state in which a window is "used as evidence" yet not recorded as
burned, because those are the same event. See
tests/windows/test_ledger.py::test_burn_atomicity_drill for the drill
(D14) that exercises this by simulating the crash and the recovery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from qrf.errors import LedgerImbalance, SchemaViolation, WindowConflict
from qrf.kernel.records.store import RecordStore

LABELS = frozenset({"TRAINING", "EXPLORATION", "VIRGIN"})


def validate_window_payload(payload: dict) -> None:
    op = payload.get("op")
    if op == "reserve":
        required = {"op", "window_id", "start", "end", "label"}
        if not required.issubset(payload):
            raise SchemaViolation("reserve payload missing required fields", payload)
        if payload["label"] not in LABELS:
            raise SchemaViolation(
                "label must be TRAINING, EXPLORATION, or VIRGIN", payload["label"]
            )
        start, end = payload["start"], payload["end"]
        if isinstance(start, bool) or isinstance(end, bool) or not (
            isinstance(start, (int, float)) and isinstance(end, (int, float))
        ):
            raise SchemaViolation("start/end must be numeric market-time markers", payload)
        if not start < end:
            raise SchemaViolation("start must be strictly before end", (start, end))
    elif op == "burn":
        required = {"op", "window_id", "hypothesis_id"}
        if not required.issubset(payload):
            raise SchemaViolation("burn payload missing required fields", payload)
    else:
        raise SchemaViolation("unknown window ledger op", op)


@dataclass
class _WindowState:
    window_id: str
    start: float
    end: float
    label: str
    burned_by: str | None = field(default=None)


class WindowLedger:
    """A window ledger backed by one RecordStore. `reserve()` registers a
    new span with a label and refuses any overlap with an existing window,
    regardless of that window's label. `burn()` is the one and only
    evidence-consuming operation and only ever succeeds on a VIRGIN,
    not-yet-burned window. `balances()` recomputes and cross-checks the
    whole ledger's accounting from scratch every time — there is no
    separate index to fall out of sync with the ledger itself.
    """

    def __init__(self, path: Path):
        self._store = RecordStore(Path(path), validate_window_payload)

    def _rebuild(self) -> dict[str, _WindowState]:
        windows: dict[str, _WindowState] = {}
        for record in self._store.verify():
            payload = record.payload
            if payload["op"] == "reserve":
                windows[payload["window_id"]] = _WindowState(
                    window_id=payload["window_id"],
                    start=payload["start"],
                    end=payload["end"],
                    label=payload["label"],
                )
            else:  # "burn" -- validated at write time, nothing else reaches the chain
                wid = payload["window_id"]
                if wid not in windows:
                    raise LedgerImbalance(f"burn references unknown window_id {wid!r}")
                windows[wid].burned_by = payload["hypothesis_id"]
        return windows

    def reserve(self, window_id: str, start: float, end: float, label: str) -> None:
        windows = self._rebuild()
        for w in windows.values():
            if start < w.end and w.start < end:
                raise WindowConflict(
                    "overlap",
                    f"[{start},{end}) overlaps existing window {w.window_id!r} "
                    f"[{w.start},{w.end}) labelled {w.label}",
                )
        self._store.append(
            {"op": "reserve", "window_id": window_id, "start": start, "end": end, "label": label}
        )

    def burn(self, window_id: str, hypothesis_id: str) -> None:
        windows = self._rebuild()
        w = windows.get(window_id)
        if w is None:
            raise WindowConflict("unknown", f"no such window: {window_id!r}")
        if w.label != "VIRGIN":
            raise WindowConflict(
                "not-virgin", f"window {window_id!r} is {w.label}, never usable as evidence"
            )
        if w.burned_by is not None:
            raise WindowConflict(
                "already-burned", f"window {window_id!r} already burned by {w.burned_by!r}"
            )
        self._store.append({"op": "burn", "window_id": window_id, "hypothesis_id": hypothesis_id})

    def balances(self) -> dict:
        windows = self._rebuild()
        by_label = {"TRAINING": 0, "EXPLORATION": 0, "VIRGIN": 0}
        burned = 0
        for w in windows.values():
            by_label[w.label] += 1
            if w.burned_by is not None:
                burned += 1
        virgin_unburned = by_label["VIRGIN"] - burned
        if virgin_unburned < 0:
            raise LedgerImbalance(
                f"more burns ({burned}) than VIRGIN windows ({by_label['VIRGIN']})"
            )
        return {
            "total_windows": sum(by_label.values()),
            "training": by_label["TRAINING"],
            "exploration": by_label["EXPLORATION"],
            "virgin_unburned": virgin_unburned,
            "burned": burned,
        }

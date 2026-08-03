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
stop), or it does not land at all. In the second case RecordStore.verify()
detects the incomplete trailing bytes as a TornTail; because the crash
also leaves the writer lock held (see qrf.kernel.records.store's crash
recovery note, A-005 R1), recovery is a deliberate two-step operator
action — `break_lock()` then `recover_torn_tail()` — never automatic, so a
merely-slow writer is never mistaken for a dead one. Once recovered, the
window is exactly as if burn() had never been called. There is no state in
which a window is "used as evidence" yet not recorded as burned, because
those are the same event. See tests/windows/test_ledger.py's D14 drill,
which leaves BOTH the torn tail and the lock behind, as a real death does.

KNOWN LIMITATION (A-005 R3): this ledger can only enforce honesty over
spans it KNOWS about. Reserving overlap detection catches a VIRGIN
designation over any RECORDED window — but if a person looks at a span of
market time and never reserves it here, nothing in this module stops that
same span later being designated VIRGIN. This is not a software defect (no
program can observe a human reading a chart); it is the exact seam where
the whole guarantee rests on someone telling the truth about what they
have seen, and it is why the Owner ceremony at S05 exists — the typed
designation is the human key on a lock the machine cannot turn alone. See
tests/windows/test_ledger.py::test_r3_unrecorded_look_is_not_detected for
the test that proves this hole rather than leaving it implicit.
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
    elif op == "verdict":
        # S05: the Battery's atomic verdict+burn -- one append that both
        # consumes the window and records the judgment. See
        # WindowLedger.record_verdict() and qrf.kernel.battery.
        required = {"op", "window_id", "hypothesis_id", "verdict"}
        if not required.issubset(payload):
            raise SchemaViolation("verdict payload missing required fields", payload)
        if not isinstance(payload["verdict"], dict):
            raise SchemaViolation("verdict payload's 'verdict' field must be a dict", payload)
    else:
        raise SchemaViolation("unknown window ledger op", op)


@dataclass
class _WindowState:
    window_id: str
    start: float
    end: float
    label: str
    burned_by: str | None = field(default=None)
    verdict: dict | None = field(default=None)


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
            elif payload["op"] == "burn":
                wid = payload["window_id"]
                if wid not in windows:
                    raise LedgerImbalance(f"burn references unknown window_id {wid!r}")
                windows[wid].burned_by = payload["hypothesis_id"]
            else:  # "verdict" -- also burns, atomically, in the same record
                wid = payload["window_id"]
                if wid not in windows:
                    raise LedgerImbalance(f"verdict references unknown window_id {wid!r}")
                windows[wid].burned_by = payload["hypothesis_id"]
                windows[wid].verdict = payload["verdict"]
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

    def record_verdict(self, window_id: str, hypothesis_id: str, verdict: dict) -> None:
        """S05: the Battery's ONLY entry point for consuming a window with
        a judgment. Identical safety checks to `burn()` (VIRGIN,
        not-yet-burned), but the verdict and the burn are the SAME
        RecordStore.append() call -- one JSON line carries both, so the
        S02 atomicity argument (see module docstring) applies to the
        verdict exactly as it does to a bare burn: there is no state in
        which a verdict exists but the window is unburned, or the
        reverse, because they are not two events.
        """
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
        self._store.append(
            {
                "op": "verdict",
                "window_id": window_id,
                "hypothesis_id": hypothesis_id,
                "verdict": verdict,
            }
        )

    def get_verdict(self, window_id: str) -> dict | None:
        windows = self._rebuild()
        w = windows.get(window_id)
        return w.verdict if w is not None else None

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

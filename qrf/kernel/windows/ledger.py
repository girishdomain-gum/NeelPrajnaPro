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

CORRECTION MECHANISM — supersede() (A-024/A-025 R3, S07 F-07): the ledger
is append-only, and a RESERVATION MISTAKE (a span designated VIRGIN that
was, on investigation, already examined by something recorded elsewhere)
was otherwise permanent and uncorrectable. `supersede()` adds a new,
append-only op that retracts a reservation's occupancy of its span
without ever editing or deleting the original record.

THE GOVERNING PRINCIPLE, stated because it is binding and not obvious:
YOU MAY RETRACT A CLAIM THAT TIME IS UNTOUCHED; YOU MAY NEVER RETRACT A
CLAIM THAT TIME WAS TOUCHED. A VIRGIN reservation is a claim of
innocence, and claims of innocence can be wrong about our own records --
exactly what happened here. A TRAINING/EXPLORATION reservation is a claim
that time WAS looked at, which is a fact about the world; facts about the
world do not become untrue because they are inconvenient. Combined with
the burned-window guard below, `supersede()` can only ever make the
ledger MORE restrictive or correct a false claim of innocence -- it can
never manufacture innocence for a span already on record as examined.

RULES:
  1. Only a VIRGIN, UNBURNED window may be superseded. Superseding a
     TRAINING or EXPLORATION window is refused by name -- this is the
     rule that closes the laundering hole an earlier draft of this
     mechanism left open (contaminating a window, then "correcting" the
     EXPLORATION record that proved it, then re-reserving the same span
     as VIRGIN).
  2. Superseding a BURNED window is refused by name -- a verdict's window
     can never be retracted this way. This is the guard that stops
     `supersede()` from being "un-burn evidence" under a different name.
  3. A window may be superseded only ONCE -- superseding an
     already-superseded window is refused.
  4. `reason` is required and non-empty -- a correction with no stated
     reason is itself a small dishonesty. It is written into the
     append-only chain forever, for a reader years from now who has none
     of today's context.
  5. A superseded window's span becomes available again for a NEW
     reservation (`reserve()`'s overlap check skips superseded windows).
     `balances()` gains a `superseded` bucket so every window is counted
     in exactly one bucket, always.
Nothing is ever deleted or edited: the original `"reserve"` record and
the `"supersede"` record both remain in the chain forever, so the
ledger's history shows both the mistake and its correction, permanently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from qrf.errors import CapabilityRequired, LedgerImbalance, SchemaViolation, WindowConflict
from qrf.kernel.records.store import RecordStore

LABELS = frozenset({"TRAINING", "EXPLORATION", "VIRGIN"})


class VerdictCapability:
    """A-016 R1: `record_verdict()` requires an instance of exactly this
    type. This is not a hard security boundary -- Python has none across
    modules -- but it restricts writing a verdict in practice to code
    that deliberately imports THIS class and constructs it, rather than
    treating `record_verdict()` as a plain public method anyone can call
    with a hand-built dict. `qrf.kernel.battery.battery.Battery` is the
    only code in this project that does so.
    """


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
    elif op == "supersede":
        # S07 F-07 (A-024/A-025 R3): retracts a VIRGIN reservation's
        # occupancy of its span without editing or deleting the
        # original "reserve" record. See WindowLedger.supersede() and
        # the module docstring's CORRECTION MECHANISM section.
        required = {"op", "window_id", "reason"}
        if not required.issubset(payload):
            raise SchemaViolation("supersede payload missing required fields", payload)
        if not isinstance(payload["reason"], str) or not payload["reason"].strip():
            raise SchemaViolation("supersede 'reason' must be a non-empty string", payload)
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
    superseded_by_reason: str | None = field(default=None)


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
            elif payload["op"] == "verdict":  # also burns, atomically, in the same record
                wid = payload["window_id"]
                if wid not in windows:
                    raise LedgerImbalance(f"verdict references unknown window_id {wid!r}")
                windows[wid].burned_by = payload["hypothesis_id"]
                windows[wid].verdict = payload["verdict"]
            else:  # "supersede"
                wid = payload["window_id"]
                if wid not in windows:
                    raise LedgerImbalance(f"supersede references unknown window_id {wid!r}")
                windows[wid].superseded_by_reason = payload["reason"]
        return windows

    def reserve(self, window_id: str, start: float, end: float, label: str) -> None:
        windows = self._rebuild()
        for w in windows.values():
            if w.superseded_by_reason is not None:
                continue
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

    def record_verdict(
        self, window_id: str, hypothesis_id: str, verdict: dict, capability: VerdictCapability
    ) -> None:
        """S05: the Battery's ONLY entry point for consuming a window with
        a judgment. Identical safety checks to `burn()` (VIRGIN,
        not-yet-burned), but the verdict and the burn are the SAME
        RecordStore.append() call -- one JSON line carries both, so the
        S02 atomicity argument (see module docstring) applies to the
        verdict exactly as it does to a bare burn: there is no state in
        which a verdict exists but the window is unburned, or the
        reverse, because they are not two events.

        A-016 R1: `capability` must be a `VerdictCapability` instance —
        refused by name (CapabilityRequired) otherwise. See that class's
        docstring for exactly what this restricts and does not.
        """
        if not isinstance(capability, VerdictCapability):
            raise CapabilityRequired("WindowLedger.record_verdict")
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

    def supersede(self, window_id: str, reason: str) -> None:
        """S07 F-07 (A-024/A-025 R3): retract a mistaken VIRGIN reservation's
        occupancy of its span. See the module docstring's CORRECTION
        MECHANISM section for the full rationale; enforced here:

          1. Only a VIRGIN, unburned window may be superseded -- TRAINING
             and EXPLORATION are refused by name (closes the laundering
             hole: contaminate a window, "correct" the record that proved
             it, re-reserve as VIRGIN).
          2. A burned window is refused by name -- a verdict's window can
             never be retracted this way.
          3. An already-superseded window is refused.
          4. `reason` is required and non-empty.
        """
        if not isinstance(reason, str) or not reason.strip():
            raise SchemaViolation("supersede 'reason' must be a non-empty string", reason)
        windows = self._rebuild()
        w = windows.get(window_id)
        if w is None:
            raise WindowConflict("unknown", f"no such window: {window_id!r}")
        if w.label != "VIRGIN":
            raise WindowConflict(
                "not-virgin",
                f"window {window_id!r} is {w.label}, only VIRGIN windows may be superseded",
            )
        if w.burned_by is not None:
            raise WindowConflict(
                "already-burned", f"window {window_id!r} already burned by {w.burned_by!r}"
            )
        if w.superseded_by_reason is not None:
            raise WindowConflict("already-superseded", f"window {window_id!r} already superseded")
        self._store.append({"op": "supersede", "window_id": window_id, "reason": reason})

    def balances(self) -> dict:
        windows = self._rebuild()
        by_label = {"TRAINING": 0, "EXPLORATION": 0, "VIRGIN": 0}
        burned = 0
        superseded = 0
        for w in windows.values():
            by_label[w.label] += 1
            if w.burned_by is not None:
                burned += 1
            if w.superseded_by_reason is not None:
                superseded += 1
        virgin_unburned = by_label["VIRGIN"] - burned - superseded
        if virgin_unburned < 0:
            raise LedgerImbalance(
                f"more burns+supersedes ({burned + superseded}) than VIRGIN windows "
                f"({by_label['VIRGIN']})"
            )
        return {
            "total_windows": sum(by_label.values()),
            "training": by_label["TRAINING"],
            "exploration": by_label["EXPLORATION"],
            "virgin_unburned": virgin_unburned,
            "burned": burned,
            "superseded": superseded,
        }

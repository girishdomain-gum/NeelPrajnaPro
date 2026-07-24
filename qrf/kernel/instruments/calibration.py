"""CalibrationHarness — run a detector's planted suite, record the verdict.

Implementation Blueprint v1.0 §4.4. The harness runs each :class:`CalibrationCase`
through the detector, compares emitted events against the case's expectation, and
appends a ``calibration`` record (§2). It records the outcome whether it passes or
fails — both are ledger facts. The *block* lives in the registry: a calibration
with ``overall_pass = false`` never satisfies ``is_calibrated`` (no soft-pass), so
a failed detector's use raises ``UncalibratedInstrumentError``.

Comparison basis (deliberately robust for a contract-proving sprint): a
``planted_truth`` case passes iff the detector's emitted events — reduced to
``{ts, event_type, direction}`` descriptors, sorted — equal the case's
``expected`` exactly. ``planted_noise`` and ``insufficient`` pass iff the detector
is silent (emits zero events) and does not raise.
"""

from __future__ import annotations

from typing import Any

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.instruments.base import CalibrationCase, validate_event_frame
from qrf.kernel.instruments.registry import InstrumentRegistry
from qrf.kernel.records.record import Record, now_ns
from qrf.kernel.records.store import RecordStore


def descriptors(events: Any) -> list[dict[str, Any]]:
    """Reduce an EventFrame to sorted ``{ts, event_type, direction}`` dicts.

    This is the JSON-serializable, comparison-and-ledger form of a detector's
    output. Sorting by (ts, event_type, direction) makes the comparison and the
    recorded ``got`` order-independent and reproducible.
    """
    validate_event_frame(events)
    ts = events.column("ts").to_pylist()
    et = events.column("event_type").to_pylist()
    di = events.column("direction").to_pylist()
    out = [
        {"ts": int(t), "event_type": str(e), "direction": int(d)}
        for t, e, d in zip(ts, et, di, strict=True)
    ]
    out.sort(key=lambda r: (r["ts"], r["event_type"], r["direction"]))
    return out


class CalibrationHarness:
    """Runs a detector's planted suite and appends its ``calibration`` record."""

    def __init__(self, store: RecordStore, registry: InstrumentRegistry) -> None:
        self._store = store
        self._registry = registry

    def run(
        self,
        inst: Any,
        suite: list[CalibrationCase],
        *,
        suite_id: str = "default",
        producer: str | None = None,
        event_ts: int | None = None,
    ) -> Record:
        """Run ``suite`` against ``inst`` and append a ``calibration`` record.

        ``inst`` must already be registered (its ref is the registration record
        id). The record is parented to that registration. ``overall_pass`` is
        true only if every case passes.
        """
        info = self._registry.get(inst.instrument_id, inst.version)
        instrument_ref = info.record_id

        cases_payload: list[dict[str, Any]] = []
        truth_total = truth_pass = 0
        noise_total = noise_pass = 0

        for case in suite:
            got = descriptors(inst.detect(case.data))
            if case.kind == "planted_truth":
                expected = list(case.expected)
                passed = got == expected
                truth_total += 1
                truth_pass += int(passed)
            elif case.kind == "planted_noise":
                expected = []
                passed = got == []
                noise_total += 1
                noise_pass += int(passed)
            elif case.kind == "insufficient":
                expected = []
                passed = got == []
            else:  # defensive: CalibrationCase.__post_init__ already guards this
                raise SchemaViolation(f"unknown calibration case kind {case.kind!r}")

            cases_payload.append(
                {
                    "case_id": case.case_id,
                    "kind": case.kind,
                    "expected": expected,
                    "got": got,
                    "pass": passed,
                }
            )

        pass_rate_truth = truth_pass / truth_total if truth_total else 1.0
        silence_rate_noise = noise_pass / noise_total if noise_total else 1.0
        overall_pass = all(c["pass"] for c in cases_payload)

        payload = {
            "instrument_ref": instrument_ref,
            "suite_id": suite_id,
            "cases": cases_payload,
            "pass_rate_truth": pass_rate_truth,
            "silence_rate_noise": silence_rate_noise,
            "overall_pass": overall_pass,
        }
        return self._store.append(
            "calibration",
            payload,
            producer=producer or f"{inst.instrument_id}@{inst.version}",
            event_ts=event_ts if event_ts is not None else now_ns(),
            parents=[instrument_ref],
        )

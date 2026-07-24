"""Payload schemas for the v1 record types available through Sprint 2.

Implementation Blueprint v1.0 §2. Sprint 1 registered ``note``, ``amendment``
and ``instrument_registered``; Sprint 2 (ARCH-002) adds ``calibration``. Every
``RecordStore.append`` validates the payload against the schema registered for
``(record_type, schema_version)`` before writing (I-4); an unregistered pair is
itself a :class:`SchemaViolation`.

Validation here is deliberately hand-rolled and strict (unknown keys rejected)
rather than delegated to a DataFrame validator — payloads are small dicts and
crisp rejection makes the contract testable. Heavier schemas (EventFrames,
bulk manifests) arrive in later sprints.
"""

from __future__ import annotations

from collections.abc import Callable

from qrf.kernel.errors import SchemaViolation

# Enum from Blueprint §2, instrument_registered.kind.
_INSTRUMENT_KINDS = frozenset({"data", "detector", "judge"})

# Enum from Blueprint §2, calibration.cases[].kind.
_CALIBRATION_CASE_KINDS = frozenset({"planted_truth", "planted_noise", "insufficient"})


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise SchemaViolation(msg)


def _check_keys(payload: dict, required: set[str], optional: set[str], where: str) -> None:
    _require(isinstance(payload, dict), f"{where}: payload must be an object")
    keys = set(payload)
    missing = required - keys
    _require(not missing, f"{where}: missing required field(s) {sorted(missing)}")
    unknown = keys - required - optional
    _require(not unknown, f"{where}: unknown field(s) {sorted(unknown)}")


def _validate_note(payload: dict) -> None:
    _check_keys(payload, {"text"}, set(), "note")
    _require(isinstance(payload["text"], str), "note.text must be a string")


def _validate_amendment(payload: dict) -> None:
    _check_keys(payload, {"target_ref", "correction"}, set(), "amendment")
    _require(isinstance(payload["target_ref"], str), "amendment.target_ref must be a string")
    _require(isinstance(payload["correction"], dict), "amendment.correction must be an object")


def _validate_instrument_registered(payload: dict) -> None:
    _check_keys(
        payload,
        {"instrument_id", "kind", "version", "params_schema", "code_ref"},
        set(),
        "instrument_registered",
    )
    _require(
        isinstance(payload["instrument_id"], str),
        "instrument_registered.instrument_id must be a string",
    )
    _require(
        payload["kind"] in _INSTRUMENT_KINDS,
        f"instrument_registered.kind must be one of {sorted(_INSTRUMENT_KINDS)}",
    )
    _require(
        isinstance(payload["version"], str),
        "instrument_registered.version must be a string",
    )
    _require(
        isinstance(payload["params_schema"], dict),
        "instrument_registered.params_schema must be an object",
    )
    _require(
        isinstance(payload["code_ref"], str),
        "instrument_registered.code_ref must be a string",
    )


def _validate_calibration(payload: dict) -> None:
    _check_keys(
        payload,
        {
            "instrument_ref",
            "suite_id",
            "cases",
            "pass_rate_truth",
            "silence_rate_noise",
            "overall_pass",
        },
        set(),
        "calibration",
    )
    _require(
        isinstance(payload["instrument_ref"], str),
        "calibration.instrument_ref must be a string",
    )
    _require(isinstance(payload["suite_id"], str), "calibration.suite_id must be a string")
    _require(isinstance(payload["cases"], list), "calibration.cases must be a list")
    for i, case in enumerate(payload["cases"]):
        where = f"calibration.cases[{i}]"
        _check_keys(case, {"case_id", "kind", "expected", "got", "pass"}, set(), where)
        _require(isinstance(case["case_id"], str), f"{where}.case_id must be a string")
        _require(
            case["kind"] in _CALIBRATION_CASE_KINDS,
            f"{where}.kind must be one of {sorted(_CALIBRATION_CASE_KINDS)}",
        )
        # 'expected' and 'got' are free-form (per-detector) but must be present.
        _require(
            isinstance(case["pass"], bool),
            f"{where}.pass must be a bool",
        )
    for f64_field in ("pass_rate_truth", "silence_rate_noise"):
        val = payload[f64_field]
        _require(
            isinstance(val, (int, float)) and not isinstance(val, bool),
            f"calibration.{f64_field} must be a number",
        )
        _require(0.0 <= float(val) <= 1.0, f"calibration.{f64_field} must be in [0, 1]")
    _require(
        isinstance(payload["overall_pass"], bool),
        "calibration.overall_pass must be a bool",
    )


# Registry keyed by (record_type, schema_version). Additive schema evolution
# bumps the version (Blueprint §2); removals never happen.
SCHEMAS: dict[tuple[str, int], Callable[[dict], None]] = {
    ("note", 1): _validate_note,
    ("amendment", 1): _validate_amendment,
    ("instrument_registered", 1): _validate_instrument_registered,
    ("calibration", 1): _validate_calibration,
}


def validate(record_type: str, payload: dict, schema_version: int = 1) -> None:
    """Validate ``payload`` against the schema for ``(record_type, schema_version)``.

    Raises :class:`SchemaViolation` if the pair is unregistered or the payload
    fails its contract.
    """
    validator = SCHEMAS.get((record_type, schema_version))
    if validator is None:
        raise SchemaViolation(
            f"no schema registered for record_type={record_type!r} "
            f"schema_version={schema_version}"
        )
    validator(payload)

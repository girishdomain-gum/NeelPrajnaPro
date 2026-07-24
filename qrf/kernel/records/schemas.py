"""Payload schemas for the v1 record types available through Sprint 3.

Implementation Blueprint v1.0 §2. Sprint 1 registered ``note``, ``amendment``
and ``instrument_registered``; Sprint 2 (ARCH-002) added ``calibration``;
Sprint 3 (ARCH-003) adds the data-plane types ``bulk_manifest``,
``ingest_report``, ``window`` and ``window_burn``; the DEVQ-006 ruling adds
``ingest_report`` schema **version 2** (v1 plus a required ``params`` object) —
additively, so existing v1 records are never touched. Every
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

# Enum from Blueprint §2, ingest_report.verdict.
_INGEST_VERDICTS = frozenset({"PASS", "FAIL"})

# Enum from Blueprint §2, window.designation.
_WINDOW_DESIGNATIONS = frozenset({"TRAINING", "EXPLORATION", "VIRGIN"})


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


def _require_int(payload: dict, key: str, where: str, *, non_negative: bool = False) -> None:
    val = payload[key]
    _require(
        isinstance(val, int) and not isinstance(val, bool),
        f"{where}.{key} must be an int",
    )
    if non_negative:
        _require(val >= 0, f"{where}.{key} must be >= 0")


def _require_str(payload: dict, key: str, where: str) -> None:
    _require(isinstance(payload[key], str), f"{where}.{key} must be a string")


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


def _validate_bulk_manifest(payload: dict) -> None:
    _check_keys(
        payload,
        {
            "path",
            "dataset",
            "row_count",
            "byte_size",
            "file_sha256",
            "columns",
            "ts_min",
            "ts_max",
        },
        set(),
        "bulk_manifest",
    )
    _require_str(payload, "path", "bulk_manifest")
    _require_str(payload, "dataset", "bulk_manifest")
    _require_str(payload, "file_sha256", "bulk_manifest")
    _require_int(payload, "row_count", "bulk_manifest", non_negative=True)
    _require_int(payload, "byte_size", "bulk_manifest", non_negative=True)
    _require_int(payload, "ts_min", "bulk_manifest")
    _require_int(payload, "ts_max", "bulk_manifest")
    _require(payload["ts_max"] >= payload["ts_min"], "bulk_manifest.ts_max must be >= ts_min")
    _require(isinstance(payload["columns"], list), "bulk_manifest.columns must be a list")
    for i, col in enumerate(payload["columns"]):
        where = f"bulk_manifest.columns[{i}]"
        _check_keys(col, {"name", "dtype"}, set(), where)
        _require_str(col, "name", where)
        _require_str(col, "dtype", where)


# ingest_report.params fields (schema v2, DEVQ-006 ruling) — the parameters the
# adapter ran with, so a report's anomaly verdict (e.g. a holiday-excused gap) is
# reconstructable from the ledger alone.
_INGEST_PARAM_NUMBERS = ("gap_k", "spread_mad_k", "flagged_threshold")


def _check_ingest_report_common(payload: dict) -> None:
    """The v1 field checks, shared by every ingest_report schema version."""
    _require(
        isinstance(payload["manifest_refs"], list),
        "ingest_report.manifest_refs must be a list",
    )
    for i, ref in enumerate(payload["manifest_refs"]):
        _require(
            isinstance(ref, str),
            f"ingest_report.manifest_refs[{i}] must be a string",
        )
    _require_int(payload, "rows_clean", "ingest_report", non_negative=True)
    _require_int(payload, "rows_flagged", "ingest_report", non_negative=True)
    _require(
        isinstance(payload["anomaly_counts"], dict),
        "ingest_report.anomaly_counts must be an object",
    )
    for k, v in payload["anomaly_counts"].items():
        _require(
            isinstance(v, int) and not isinstance(v, bool),
            f"ingest_report.anomaly_counts[{k!r}] must be an int",
        )
    _require(
        payload["verdict"] in _INGEST_VERDICTS,
        f"ingest_report.verdict must be one of {sorted(_INGEST_VERDICTS)}",
    )


def _validate_ingest_report(payload: dict) -> None:
    _check_keys(
        payload,
        {"manifest_refs", "rows_clean", "rows_flagged", "anomaly_counts", "verdict"},
        set(),
        "ingest_report",
    )
    _check_ingest_report_common(payload)


def _validate_ingest_report_v2(payload: dict) -> None:
    """ingest_report v2 (DEVQ-006): v1 plus a required ``params`` object.

    Additive schema evolution (Blueprint §2): v1 records are never touched; new
    reports record the parameters the ingest ran under.
    """
    _check_keys(
        payload,
        {"manifest_refs", "rows_clean", "rows_flagged", "anomaly_counts", "verdict", "params"},
        set(),
        "ingest_report",
    )
    _check_ingest_report_common(payload)
    where = "ingest_report.params"
    _check_keys(
        payload["params"],
        {
            "timeframe_seconds",
            "gap_k",
            "weekend_allowance",
            "holidays",
            "spread_mad_k",
            "flagged_threshold",
            "dataset",
        },
        set(),
        where,
    )
    params = payload["params"]
    _require_int(params, "timeframe_seconds", where)
    _require(params["timeframe_seconds"] > 0, f"{where}.timeframe_seconds must be > 0")
    _require_str(params, "dataset", where)
    _require(
        isinstance(params["weekend_allowance"], bool),
        f"{where}.weekend_allowance must be a bool",
    )
    for num in _INGEST_PARAM_NUMBERS:
        _require(
            isinstance(params[num], (int, float)) and not isinstance(params[num], bool),
            f"{where}.{num} must be a number",
        )
    _require(isinstance(params["holidays"], list), f"{where}.holidays must be a list")
    for i, hol in enumerate(params["holidays"]):
        _require(isinstance(hol, str), f"{where}.holidays[{i}] must be a string")
    _require(
        params["holidays"] == sorted(params["holidays"]),
        f"{where}.holidays must be a sorted list",
    )


def _validate_window(payload: dict) -> None:
    _check_keys(
        payload,
        {"dataset", "ts_start", "ts_end", "designation"},
        set(),
        "window",
    )
    _require_str(payload, "dataset", "window")
    _require_int(payload, "ts_start", "window")
    _require_int(payload, "ts_end", "window")
    _require(payload["ts_end"] > payload["ts_start"], "window.ts_end must be > ts_start")
    _require(
        payload["designation"] in _WINDOW_DESIGNATIONS,
        f"window.designation must be one of {sorted(_WINDOW_DESIGNATIONS)}",
    )


def _validate_window_burn(payload: dict) -> None:
    _check_keys(payload, {"window_ref", "lineage", "consumed_by"}, set(), "window_burn")
    _require_str(payload, "window_ref", "window_burn")
    _require_str(payload, "lineage", "window_burn")
    _require_str(payload, "consumed_by", "window_burn")


# Registry keyed by (record_type, schema_version). Additive schema evolution
# bumps the version (Blueprint §2); removals never happen.
SCHEMAS: dict[tuple[str, int], Callable[[dict], None]] = {
    ("note", 1): _validate_note,
    ("amendment", 1): _validate_amendment,
    ("instrument_registered", 1): _validate_instrument_registered,
    ("calibration", 1): _validate_calibration,
    ("bulk_manifest", 1): _validate_bulk_manifest,
    ("ingest_report", 1): _validate_ingest_report,
    ("ingest_report", 2): _validate_ingest_report_v2,
    ("window", 1): _validate_window,
    ("window_burn", 1): _validate_window_burn,
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

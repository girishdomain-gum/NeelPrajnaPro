"""Payload schemas for the v1 record types available through Sprint 4.

Implementation Blueprint v1.0 §2. Sprint 1 registered ``note``, ``amendment``
and ``instrument_registered``; Sprint 2 (ARCH-002) added ``calibration``;
Sprint 3 (ARCH-003) adds the data-plane types ``bulk_manifest``,
``ingest_report``, ``window`` and ``window_burn``; the DEVQ-006 ruling adds
``ingest_report`` schema **version 2** (v1 plus a required ``params`` object) —
additively, so existing v1 records are never touched; Sprint 4 (ARCH-004) adds
``trial_count`` (the multiple-testing burden, §4.8). Every
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

# Enum from Blueprint §2, trial_count.source.
_TRIAL_SOURCES = frozenset({"human", "screener", "generator"})


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


def _require_number(payload: dict, key: str, where: str) -> None:
    val = payload[key]
    _require(
        isinstance(val, (int, float)) and not isinstance(val, bool),
        f"{where}.{key} must be a number",
    )


def _require_number_or_none(value: object, where: str) -> None:
    _require(
        value is None or (isinstance(value, (int, float)) and not isinstance(value, bool)),
        f"{where} must be a number or null",
    )


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


def _validate_trial_count_common(payload: dict, optional: set[str]) -> None:
    """The v1 field checks shared by every trial_count schema version."""
    _check_keys(
        payload,
        {"data_scope", "lineage", "n_attempts", "source"},
        optional,
        "trial_count",
    )
    _require_str(payload, "data_scope", "trial_count")
    _require_str(payload, "lineage", "trial_count")
    _require_int(payload, "n_attempts", "trial_count", non_negative=True)
    _require(payload["n_attempts"] >= 1, "trial_count.n_attempts must be >= 1")
    _require(
        payload["source"] in _TRIAL_SOURCES,
        f"trial_count.source must be one of {sorted(_TRIAL_SOURCES)}",
    )
    if "generator_ref" in payload:
        _require_str(payload, "generator_ref", "trial_count")


def _validate_trial_count(payload: dict) -> None:
    """trial_count v1 (Blueprint §2, §4.8) — a multiple-testing burden record.

    ``data_scope`` is a window_ref or a dataset name; ``n_attempts`` is the exact
    number of variants evaluated (>= 1 — a bump of nothing is meaningless);
    ``source`` is human/screener/generator; ``generator_ref`` is optional and
    carries the id of a generator instrument when ``source == generator``.
    """
    _validate_trial_count_common(payload, {"generator_ref"})


def _validate_trial_count_v2(payload: dict) -> None:
    """trial_count v2 (DEVQ-015 ruling): v1 plus a required ``family`` key.

    Additive (Blueprint §2): v1 records are never touched. ``family`` is the
    ``{market}/{instrument_family}`` a search's multiplicity burden accrues to
    (DEVQ-015: corrections follow CLAIMS, not the data slice searched), so the
    deflation can total a family's trials directly rather than by lineage prefix.
    """
    _validate_trial_count_common(payload, {"generator_ref", "family"})
    _require("family" in payload, "trial_count v2 requires a family")
    _require_str(payload, "family", "trial_count")


# Enum from Blueprint §2 / ARCH-006 §3, verdict.verdict (tri-state).
_VERDICT_VALUES = frozenset({"PASS", "FAIL", "INSUFFICIENT"})


def _validate_execution(payload: dict, where: str) -> None:
    """A hypothesis's ``execution`` sub-object (mirrors ExecutionSpec.as_dict)."""
    _check_keys(
        payload,
        {"hold_bars", "size"},
        {"strength_min", "stop_offset", "target_offset"},
        where,
    )
    _require_int(payload, "hold_bars", where)
    _require(payload["hold_bars"] >= 1, f"{where}.hold_bars must be >= 1")
    _require_number(payload, "size", where)
    _require(payload["size"] > 0, f"{where}.size must be > 0")
    if "strength_min" in payload:
        _require_number(payload, "strength_min", where)
    for name in ("stop_offset", "target_offset"):
        if name in payload:
            val = payload[name]
            _require_number_or_none(val, f"{where}.{name}")
            _require(val is None or val > 0, f"{where}.{name} must be > 0 or null")


def _validate_split_spec(payload: dict, where: str) -> None:
    _check_keys(payload, {"n_folds", "embargo_bars"}, set(), where)
    _require_int(payload, "n_folds", where)
    _require(payload["n_folds"] >= 1, f"{where}.n_folds must be >= 1")
    _require_int(payload, "embargo_bars", where, non_negative=True)


def _validate_thresholds(payload: dict, where: str) -> None:
    _check_keys(payload, {"min_n", "base_alpha", "correction"}, set(), where)
    _require_int(payload, "min_n", where)
    _require(payload["min_n"] >= 1, f"{where}.min_n must be >= 1")
    _require_number(payload, "base_alpha", where)
    _require(0.0 < float(payload["base_alpha"]) < 1.0, f"{where}.base_alpha must be in (0, 1)")
    _require(isinstance(payload["correction"], dict), f"{where}.correction must be an object")
    _check_keys(payload["correction"], {"method"}, set(), f"{where}.correction")
    _require_str(payload["correction"], "method", f"{where}.correction")


_HYPOTHESIS_V1_FIELDS = {
    "lineage",
    "scope",
    "instrument_refs",
    "setup_dsl",
    "execution",
    "cost_model_ref",
    "split_spec",
    "thresholds",
}
# v2 (DEVQ-014/015): the epistemic pre-commitments — plain-words claim, the
# conclusion to draw for each outcome (fixed BEFORE running), and the family the
# multiplicity burden accrues to.
_HYPOTHESIS_V2_FIELDS = {"thesis", "outcome_interpretations", "family"}


def _validate_hypothesis_core(payload: dict, extra_required: set[str]) -> None:
    """Shared hypothesis shape check (ARCH-006 §1) over v1 + any v2 fields.

    The record's own ``content_hash`` is the pre-registration seal: a changed
    YAML yields a different canonical payload, hence a new hypothesis id
    (ARCH-006 §1). Cross-record/semantic checks (embargo >= hold_bars + 1;
    cost_model_ref exists; instruments exist, are calibrated, and none is an
    order_block) are enforced by :class:`HypothesisRegistry` at registration,
    which alone has the store + allowlist to judge them; the schema fixes shape.
    """
    _check_keys(payload, _HYPOTHESIS_V1_FIELDS | extra_required, set(), "hypothesis")
    _require_str(payload, "lineage", "hypothesis")
    _require_str(payload, "scope", "hypothesis")
    _require_str(payload, "cost_model_ref", "hypothesis")
    _require(
        isinstance(payload["instrument_refs"], list) and payload["instrument_refs"],
        "hypothesis.instrument_refs must be a non-empty list",
    )
    for i, ref in enumerate(payload["instrument_refs"]):
        _require(isinstance(ref, str), f"hypothesis.instrument_refs[{i}] must be a string")
    _require(isinstance(payload["setup_dsl"], dict), "hypothesis.setup_dsl must be an object")
    _require(isinstance(payload["execution"], dict), "hypothesis.execution must be an object")
    _validate_execution(payload["execution"], "hypothesis.execution")
    _require(isinstance(payload["split_spec"], dict), "hypothesis.split_spec must be an object")
    _validate_split_spec(payload["split_spec"], "hypothesis.split_spec")
    _require(isinstance(payload["thresholds"], dict), "hypothesis.thresholds must be an object")
    _validate_thresholds(payload["thresholds"], "hypothesis.thresholds")


def _validate_hypothesis(payload: dict) -> None:
    """hypothesis v1 — the ARCH-006 §1 field set (H-001 stands on this schema)."""
    _validate_hypothesis_core(payload, set())


def _validate_hypothesis_v2(payload: dict) -> None:
    """hypothesis v2 (DEVQ-014/015): v1 plus ``thesis``, ``outcome_interpretations``,
    ``family`` — the pre-committed interpretation is as load-bearing as the
    pre-committed thresholds (the difference between "FAIL = the edge isn't there"
    and post-hoc "FAIL = wrong parameters"), and ``family`` fixes the
    multiplicity scope (DEVQ-015).
    """
    _validate_hypothesis_core(payload, _HYPOTHESIS_V2_FIELDS)
    _require(
        isinstance(payload["thesis"], str) and payload["thesis"].strip(),
        "hypothesis.thesis must be a non-empty string",
    )
    _require_str(payload, "family", "hypothesis")
    _require(payload["family"].strip(), "hypothesis.family must be non-empty")
    interp = payload["outcome_interpretations"]
    _require(
        isinstance(interp, dict),
        "hypothesis.outcome_interpretations must be an object",
    )
    where_i = "hypothesis.outcome_interpretations"
    _check_keys(interp, {"PASS", "FAIL", "INSUFFICIENT"}, set(), where_i)
    for k in ("PASS", "FAIL", "INSUFFICIENT"):
        _require(
            isinstance(interp[k], str) and interp[k].strip(),
            f"hypothesis.outcome_interpretations.{k} must be a non-empty string",
        )


def _validate_stat_block(block: object, where: str) -> None:
    """One statistics entry: ``{stat, p, ci_low, ci_high}`` (each number or null)."""
    _require(isinstance(block, dict), f"{where} must be an object")
    _check_keys(block, {"stat", "p", "ci_low", "ci_high"}, set(), where)
    for k in ("stat", "p", "ci_low", "ci_high"):
        _require_number_or_none(block[k], f"{where}.{k}")


def _validate_verdict_core(payload: dict, *, corrections_optional: set[str]) -> None:
    """Shared verdict shape check; ``corrections_optional`` widens corrections (v2)."""
    _check_keys(
        payload,
        {
            "hypothesis_ref",
            "window_ref",
            "verdict",
            "n_trades",
            "n_dropped_tail",
            "gross",
            "net",
            "statistics",
            "folds",
            "corrections",
            "thresholds",
            "seed",
            "selftest_seed",
            "engine_version",
            "trades_manifest",
        },
        set(),
        "verdict",
    )
    _require_str(payload, "hypothesis_ref", "verdict")
    _require_str(payload, "window_ref", "verdict")
    _require(
        payload["verdict"] in _VERDICT_VALUES,
        f"verdict.verdict must be one of {sorted(_VERDICT_VALUES)}",
    )
    _require_int(payload, "n_trades", "verdict", non_negative=True)
    _require_int(payload, "n_dropped_tail", "verdict", non_negative=True)
    _require_int(payload, "seed", "verdict", non_negative=True)
    _require_int(payload, "selftest_seed", "verdict", non_negative=True)
    _require_str(payload, "engine_version", "verdict")
    _require_str(payload, "trades_manifest", "verdict")
    for agg in ("gross", "net"):
        _require(isinstance(payload[agg], dict), f"verdict.{agg} must be an object")
        _check_keys(payload[agg], {"total", "mean"}, set(), f"verdict.{agg}")
        _require_number_or_none(payload[agg]["total"], f"verdict.{agg}.total")
        _require_number_or_none(payload[agg]["mean"], f"verdict.{agg}.mean")
    _require(isinstance(payload["statistics"], dict), "verdict.statistics must be an object")
    for name, block in payload["statistics"].items():
        _validate_stat_block(block, f"verdict.statistics[{name!r}]")
    _require(isinstance(payload["folds"], list), "verdict.folds must be a list")
    for i, fold in enumerate(payload["folds"]):
        where = f"verdict.folds[{i}]"
        _check_keys(
            fold, {"index", "n_trades", "mean_net", "test_start", "test_end"}, set(), where
        )
        _require_int(fold, "index", where)
        _require_int(fold, "n_trades", where, non_negative=True)
        _require_number_or_none(fold["mean_net"], f"{where}.mean_net")
        _require_int(fold, "test_start", where, non_negative=True)
        _require_int(fold, "test_end", where, non_negative=True)
    _require(isinstance(payload["corrections"], dict), "verdict.corrections must be an object")
    _check_keys(
        payload["corrections"],
        {"family_m", "method", "base_alpha", "effective_alpha"},
        corrections_optional,
        "verdict.corrections",
    )
    _require_int(payload["corrections"], "family_m", "verdict.corrections", non_negative=True)
    _require_str(payload["corrections"], "method", "verdict.corrections")
    _require_number(payload["corrections"], "base_alpha", "verdict.corrections")
    _require_number(payload["corrections"], "effective_alpha", "verdict.corrections")
    if "family" in payload["corrections"]:
        _require_str(payload["corrections"], "family", "verdict.corrections")
    _require(isinstance(payload["thresholds"], dict), "verdict.thresholds must be an object")
    _validate_thresholds(payload["thresholds"], "verdict.thresholds")


def _validate_verdict(payload: dict) -> None:
    """verdict v1 (Blueprint §2 + ARCH-006 §3.8) — the battery's sole judgement record.

    A superset of the §2 fields (``verdict, n_trades, gross, net, statistics,
    corrections, seed, engine_version, trades_manifest``) plus the ARCH-006
    additions the corrections machinery requires: ``thresholds`` AS REGISTERED
    (byte-equal), ``selftest_seed``, per-fold means, ``n_dropped_tail``, and the
    ``base_alpha``/``family_m``(=N_trials)/``effective_alpha`` correction fields.
    """
    _validate_verdict_core(payload, corrections_optional=set())


def _validate_verdict_v2(payload: dict) -> None:
    """verdict v2 (DEVQ-015): v1 plus an optional ``corrections.family`` — the
    ``{market}/{instrument_family}`` the deflation totalled trials over, so the
    correction is fully reconstructable from the verdict alone.
    """
    _validate_verdict_core(payload, corrections_optional={"family"})


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
    ("trial_count", 1): _validate_trial_count,
    ("trial_count", 2): _validate_trial_count_v2,
    ("hypothesis", 1): _validate_hypothesis,
    ("hypothesis", 2): _validate_hypothesis_v2,
    ("verdict", 1): _validate_verdict,
    ("verdict", 2): _validate_verdict_v2,
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

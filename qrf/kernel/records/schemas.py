"""Payload schemas for the v1 record types available through Sprint 4.

Implementation Blueprint v1.0 §2. Sprint 1 registered ``note``, ``amendment``
and ``instrument_registered``; Sprint 2 (ARCH-002) added ``calibration``;
Sprint 3 (ARCH-003) adds the data-plane types ``bulk_manifest``,
``ingest_report``, ``window`` and ``window_burn``; the DEVQ-006 ruling adds
``ingest_report`` schema **version 2** (v1 plus a required ``params`` object) —
additively, so existing v1 records are never touched; Sprint 4 (ARCH-004) adds
``trial_count`` (the multiple-testing burden, §4.8); WO-03 (S3, refs A-007)
adds ``dataset_scope`` (a data-collection scope's registration record — pinned
IANA zone + evidence, pinned ingest path, batch-forward protocol, OOS
designation, all in one place). Every
``RecordStore.append`` validates the payload against the schema registered for
``(record_type, schema_version)`` before writing (I-4); an unregistered pair is
itself a :class:`SchemaViolation`.

Validation here is deliberately hand-rolled and strict (unknown keys rejected)
rather than delegated to a DataFrame validator — payloads are small dicts and
crisp rejection makes the contract testable. Heavier schemas (EventFrames,
bulk manifests) arrive in later sprints.
"""

from __future__ import annotations

import math
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


def _validate_trial_count_common(
    payload: dict, optional: set[str], sources: frozenset[str] = _TRIAL_SOURCES
) -> None:
    """The v1 field checks shared by every trial_count schema version.

    ``sources`` is the accepted ``source`` enum for this version — v1/v2 use the
    original set; v3 widens it (forward-only, so v1/v2 records never accept a value
    they were sealed without).
    """
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
        payload["source"] in sources,
        f"trial_count.source must be one of {sorted(sources)}",
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


# trial_count v3 (DEVQ-016): the source enum gains "observatory" — an anomaly scan
# is a search, and its multiplicity burden is now recorded with first-class
# provenance. Forward-only (NOTE-013 shape): v1/v2 records are never re-recorded;
# only new observatory bumps use v3.
_TRIAL_SOURCES_V3 = _TRIAL_SOURCES | {"observatory"}


def _validate_trial_count_v3(payload: dict) -> None:
    """trial_count v3 (DEVQ-016): v2 plus ``source`` may be "observatory".

    Same fields as v2 (``family`` required) with the widened source enum. The
    observatory records its family bump here so a scan's search burden carries its
    own provenance rather than borrowing ``human``/``screener``.
    """
    _validate_trial_count_common(
        payload, {"generator_ref", "family"}, sources=_TRIAL_SOURCES_V3
    )
    _require("family" in payload, "trial_count v3 requires a family")
    _require_str(payload, "family", "trial_count")


# Enum from Blueprint §2 / ARCH-006 §3, verdict.verdict (tri-state).
_VERDICT_VALUES = frozenset({"PASS", "FAIL", "INSUFFICIENT"})


_EXIT_RULES = frozenset({"time_stop", "calendar_day"})

# ARCH-NP-004 §4.1: EventFrame columns (kernel §4.3) that may carry a per-trade
# stop PRICE. Duplicated in qrf/trading/simulator/engine.py's ExecutionSpec (the
# kernel/trading boundary already duplicates small closed sets this way, e.g.
# _EXIT_RULES above) — kernel may not import qrf.trading, so this is the kernel's
# own copy of the same closed set.
_EVENT_STOP_COLUMNS = frozenset({"level", "zone_hi", "zone_lo"})


def _validate_execution(payload: dict, where: str) -> None:
    """A hypothesis's ``execution`` sub-object (mirrors ExecutionSpec.as_dict)."""
    _check_keys(
        payload,
        {"hold_bars", "size"},
        {
            "strength_min",
            "stop_offset",
            "target_offset",
            "exit_rule",
            "event_stop_column",
            "target_r_multiple",
        },
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
            _require(
                val is None or (math.isfinite(val) and val > 0),
                f"{where}.{name} must be a positive finite number or null",
            )
    if "exit_rule" in payload:
        _require_str(payload, "exit_rule", where)
        _require(
            payload["exit_rule"] in _EXIT_RULES,
            f"{where}.exit_rule must be one of {sorted(_EXIT_RULES)} (ARCH-009 §4)",
        )

    has_stop_offset = payload.get("stop_offset") is not None
    has_event_stop = False
    if "event_stop_column" in payload:
        val = payload["event_stop_column"]
        _require(
            isinstance(val, str) and val != "" or val is None,
            f"{where}.event_stop_column must be a non-empty string or null",
        )
        if val is not None:
            has_event_stop = True
            _require(
                val in _EVENT_STOP_COLUMNS,
                f"{where}.event_stop_column {val!r} is not an EventFrame column that "
                f"can carry a stop (must be one of {sorted(_EVENT_STOP_COLUMNS)}) — "
                "the EventFrame cannot supply it; registration refused",
            )
            _require(
                not has_stop_offset,
                f"{where}.stop_offset and {where}.event_stop_column are mutually "
                "exclusive — declare exactly one stop mechanism; registration refused",
            )
    if "target_r_multiple" in payload and payload["target_r_multiple"] is not None:
        val = payload["target_r_multiple"]
        _require_number(payload, "target_r_multiple", where)
        _require(
            math.isfinite(val) and val > 0,
            f"{where}.target_r_multiple must be a positive finite number or null",
        )
        _require(
            has_stop_offset or has_event_stop,
            f"{where}.target_r_multiple requires a stop ({where}.stop_offset or "
            f"{where}.event_stop_column) — an R-multiple target without a stop is "
            "meaningless; registration refused",
        )
        _require(
            payload.get("target_offset") is None,
            f"{where}.target_offset and {where}.target_r_multiple are mutually "
            "exclusive — declare exactly one target mechanism; registration refused",
        )


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


def _validate_hypothesis_core(
    payload: dict, extra_required: set[str], extra_optional: set[str] = frozenset()
) -> None:
    """Shared hypothesis shape check (ARCH-006 §1) over v1 + any v2 fields.

    The record's own ``content_hash`` is the pre-registration seal: a changed
    YAML yields a different canonical payload, hence a new hypothesis id
    (ARCH-006 §1). Cross-record/semantic checks (embargo >= hold_bars + 1;
    cost_model_ref exists; instruments exist, are calibrated, and none is an
    order_block) are enforced by :class:`HypothesisRegistry` at registration,
    which alone has the store + allowlist to judge them; the schema fixes shape.
    """
    _check_keys(payload, _HYPOTHESIS_V1_FIELDS | extra_required, set(extra_optional), "hypothesis")
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


def _validate_hypothesis_v2_body(
    payload: dict, extra_required: set[str], extra_optional: set[str]
) -> None:
    """The v2 shape check (v1 core + the epistemic pre-commitments), reusable.

    ``extra_required``/``extra_optional`` widen the closed key set so a later
    schema version (v3 = multi-window) can add its own fields (``window_refs``)
    without re-implementing the v2 body. The v2 validator calls this with no
    extras; ``_validate_hypothesis_v3`` adds ``window_refs``.
    """
    _validate_hypothesis_core(
        payload,
        _HYPOTHESIS_V2_FIELDS | extra_required,
        {"observatory_ancestry", "placebo_method"} | extra_optional,
    )
    if "observatory_ancestry" in payload:
        anc = payload["observatory_ancestry"]
        _require(isinstance(anc, list), "hypothesis.observatory_ancestry must be a list")
        for i, qid in enumerate(anc):
            _require(
                isinstance(qid, str) and qid,
                f"hypothesis.observatory_ancestry[{i}] must be a non-empty string",
            )
    if "placebo_method" in payload:
        _require(
            isinstance(payload["placebo_method"], str) and payload["placebo_method"].strip(),
            "hypothesis.placebo_method must be a non-empty string",
        )
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


def _validate_hypothesis_v2(payload: dict) -> None:
    """hypothesis v2 (DEVQ-014/015): v1 plus ``thesis``, ``outcome_interpretations``,
    ``family`` — the pre-committed interpretation is as load-bearing as the
    pre-committed thresholds (the difference between "FAIL = the edge isn't there"
    and post-hoc "FAIL = wrong parameters"), and ``family`` fixes the
    multiplicity scope (DEVQ-015).

    v2.1 (ARCH-007 §4, DEVQ-014): an OPTIONAL ``observatory_ancestry`` — a list of
    ``question`` record ids the hypothesis descends from. Additive and optional,
    so every existing v2 record still validates; the registry (not the schema)
    checks each id exists and is a question record.

    v2.2 (ARCH-009 §2, DEVQ-018 ADDENDUM): an OPTIONAL ``placebo_method`` — the
    sealed null construction a placebo run of this claim must use. Additive and
    optional so the grandfathered Wave-1 records (H-002/H-003, which fixed their
    method in the ARCH-008 §3 instruction, not the YAML) still validate unchanged.
    The schema fixes SHAPE (a non-empty string); the registry enforces MEMBERSHIP
    in the DEVQ-018 ruled set (it owns the contract), and the placebo judge refuses
    to run a method that disagrees with this sealed field.
    """
    _validate_hypothesis_v2_body(payload, set(), set())


def _validate_hypothesis_v3(payload: dict) -> None:
    """hypothesis v3 (ARCH-009 §4, DEVQ-022 Option A) — the MULTI-WINDOW schema.

    The full v2 shape (thesis / outcome_interpretations / family, and the optional
    observatory_ancestry / placebo_method) PLUS a required ``window_refs`` — a
    non-empty ordered list of ``window`` record ids the hypothesis is judged over
    as a UNION. The list mirrors the record's window parents (the registry asserts
    ``parents == tuple(window_refs)``), so the multi-window binding is sealed twice
    over: in the content-hashed payload AND in the parent set (the same both-places
    pattern a verdict already uses for its single ``window_ref``).

    A single window still uses the v1/v2 ``window`` parent (single-window path,
    unchanged); v3 exists for the non-contiguous training span H-004 needs (2024 +
    2025 training with the 2024 VIRGIN reserve between them, which no single
    contiguous window may contain). The battery evaluates the union, pools folds
    per window with the seam as a hard fold boundary, and burns EACH window once.
    The schema fixes shape; the registry (which alone has the store) checks each id
    exists and is a window, and that the list matches the parents.
    """
    _validate_hypothesis_v2_body(payload, {"window_refs"}, set())
    wr = payload["window_refs"]
    _require(
        isinstance(wr, list) and wr,
        "hypothesis.window_refs must be a non-empty list of window ids",
    )
    for i, ref in enumerate(wr):
        _require(
            isinstance(ref, str) and ref,
            f"hypothesis.window_refs[{i}] must be a non-empty string",
        )


def _validate_stat_block(block: object, where: str) -> None:
    """One statistics entry: ``{stat, p, ci_low, ci_high}`` (each number or null)."""
    _require(isinstance(block, dict), f"{where} must be an object")
    _check_keys(block, {"stat", "p", "ci_low", "ci_high"}, set(), where)
    for k in ("stat", "p", "ci_low", "ci_high"):
        _require_number_or_none(block[k], f"{where}.{k}")


def _validate_verdict_core(
    payload: dict, *, corrections_optional: set[str], extra_optional: set[str] = frozenset()
) -> None:
    """Shared verdict shape check; ``corrections_optional`` widens corrections (v2);
    ``extra_optional`` widens the top-level key set (v3 multi-window)."""
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
        extra_optional,
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


def _validate_verdict_v3(payload: dict) -> None:
    """verdict v3 (ARCH-009 §4, DEVQ-022 Option A) — a MULTI-WINDOW verdict.

    The v2 verdict PLUS two required fields:
    * ``window_refs`` — the ordered list of every window this verdict was judged
      over (the union). ``window_ref`` (singular) is retained and set to the FIRST
      window so v1/v2 readers keep working; ``window_refs`` is the authoritative
      set the battery burned (one ``window_burn`` per entry).
    * ``n_dropped_hole`` — trades dropped because a same-day calendar exit would
      have to cross an inter-window hole (a training-span gap, e.g. the 2024 VIRGIN
      reserve between the 2024 and 2025 training windows). Counted, never silent
      (the seam is a hard boundary; no trade spans it).
    """
    _validate_verdict_core(
        payload, corrections_optional={"family"}, extra_optional={"window_refs", "n_dropped_hole"}
    )
    _require("window_refs" in payload, "verdict v3 requires window_refs")
    _require_str_list(payload, "window_refs", "verdict", non_empty=True)
    _require(
        payload["window_ref"] in payload["window_refs"],
        "verdict.window_ref must be one of window_refs (the primary window)",
    )
    _require("n_dropped_hole" in payload, "verdict v3 requires n_dropped_hole")
    _require_int(payload, "n_dropped_hole", "verdict", non_negative=True)


# ===========================================================================
# Sprint 7 (ARCH-007) — observatory + belief record types.
# These reconcile Blueprint §2's earlier sketch (observatory_finding /
# belief_update) with ARCH-007's governing shapes; the divergences are recorded
# in DEVQ-016 (the DEVQ-014 pattern) for REV-S7 ratification.
# ===========================================================================

# Enum from Blueprint §2 question.origin. ARCH-007 parents each question to its
# scan, so origin is "observatory" in practice; the full enum is kept for
# alignment with §2 (a human/belief/contradiction question is a future producer).
_QUESTION_ORIGINS = frozenset({"human", "belief", "observatory", "contradiction"})

# Belief stance (ARCH-007 §3 + DEVQ-016): a claim is SUPPORTED / REJECTED by
# verdict evidence, UNTESTED before any decisive verdict, or CONTESTED once
# decisive verdicts disagree (a PASS after a FAIL, or vice versa).
_BELIEF_STANCES = frozenset({"SUPPORTED", "REJECTED", "UNTESTED", "CONTESTED"})


def _require_str_list(payload: dict, key: str, where: str, *, non_empty: bool = False) -> None:
    _require(isinstance(payload[key], list), f"{where}.{key} must be a list")
    if non_empty:
        _require(payload[key], f"{where}.{key} must be non-empty")
    for i, item in enumerate(payload[key]):
        _require(isinstance(item, str) and item, f"{where}.{key}[{i}] must be a non-empty string")


def _validate_anomaly_scan(payload: dict) -> None:
    """anomaly_scan v1 (ARCH-007 §1) — one systematic search over a window.

    Records WHAT was scanned (``manifest_refs`` over ``window_ref``), WITH WHAT
    method (``method``), under WHICH declared ``family`` and ``seed``, and a
    ``findings`` summary. ``n_searched`` (>= 1) is how many things the scan looked
    at — the multiplicity burden a scan carries (DEVQ-015 applies to looking, not
    only screening; the observatory bumps the trial ledger for its family on every
    scan). A scan carries NO thresholds and burns NO window — it is a search, not
    a judgement. Divergence from Blueprint §2 ``observatory_finding`` (probe enum /
    summary / artifact_manifest) is recorded in DEVQ-016.
    """
    _check_keys(
        payload,
        {"family", "window_ref", "manifest_refs", "method", "seed", "findings", "n_searched"},
        set(),
        "anomaly_scan",
    )
    _require_str(payload, "family", "anomaly_scan")
    _require(payload["family"].strip(), "anomaly_scan.family must be non-empty")
    _require_str(payload, "window_ref", "anomaly_scan")
    _require_str_list(payload, "manifest_refs", "anomaly_scan", non_empty=True)
    _require_str(payload, "method", "anomaly_scan")
    _require(payload["method"].strip(), "anomaly_scan.method must be non-empty")
    _require_int(payload, "seed", "anomaly_scan", non_negative=True)
    _require(isinstance(payload["findings"], dict), "anomaly_scan.findings must be an object")
    _require_int(payload, "n_searched", "anomaly_scan")
    _require(payload["n_searched"] >= 1, "anomaly_scan.n_searched must be >= 1")


def _validate_question(payload: dict) -> None:
    """question v1 (ARCH-007 §1) — an observation worth a hypothesis, not one yet.

    Carries the ``observation`` in plain words, the ``data_slice_refs`` (bulk/record
    ids of the slices that provoked it), a ``candidate_hypothesis`` sketch (plain
    words — NOT a pre-registration), the ``evidence_refs`` it cites, and its
    ``origin`` (Blueprint §2 enum; "observatory" when parented to a scan). A
    question is deliberately SHAPELESS where a hypothesis is precise: the schema's
    closed key set means a question payload CANNOT carry ``thresholds``, a
    ``verdict``, or a ``window_burn`` — a question burns nothing and pre-registers
    nothing (the type-audit ARCH-007 §Acceptance requires). ``priority_score`` is
    an optional §2 field. Divergence from §2 recorded in DEVQ-016.
    """
    _check_keys(
        payload,
        {"observation", "data_slice_refs", "candidate_hypothesis", "evidence_refs", "origin"},
        {"priority_score"},
        "question",
    )
    _require_str(payload, "observation", "question")
    _require(payload["observation"].strip(), "question.observation must be non-empty")
    _require_str_list(payload, "data_slice_refs", "question")
    _require_str(payload, "candidate_hypothesis", "question")
    _require_str_list(payload, "evidence_refs", "question")
    _require(
        payload["origin"] in _QUESTION_ORIGINS,
        f"question.origin must be one of {sorted(_QUESTION_ORIGINS)}",
    )
    if "priority_score" in payload:
        _require_number(payload, "priority_score", "question")


def _validate_belief(payload: dict) -> None:
    """belief v1 (ARCH-007 §3) — one append-only state of a (family, claim) belief.

    A belief is updated ONLY by verdict events: ``verdict_refs`` is the evidence
    chain and every id MUST resolve to a ``verdict`` record — the belief module
    enforces the type at write time (the arrow-8 audit: beliefs never cite
    screener metrics, selftest results, or questions). ``stance`` is
    SUPPORTED / REJECTED / UNTESTED; ``strength`` is a [0, 1] evidence weight
    derived from the cited verdicts' recorded statistics; ``prev_state`` (optional)
    is the prior belief record id, so a future verdict UPDATES the chain rather
    than overwriting it. Divergence from Blueprint §2 ``belief_update`` (odds/LR
    model) recorded in DEVQ-016.
    """
    _check_keys(
        payload,
        {"family", "claim", "stance", "strength", "verdict_refs"},
        {"prev_state"},
        "belief",
    )
    _require_str(payload, "family", "belief")
    _require(payload["family"].strip(), "belief.family must be non-empty")
    _require_str(payload, "claim", "belief")
    _require(payload["claim"].strip(), "belief.claim must be non-empty")
    _require(
        payload["stance"] in _BELIEF_STANCES,
        f"belief.stance must be one of {sorted(_BELIEF_STANCES)}",
    )
    _require_number(payload, "strength", "belief")
    _require(0.0 <= float(payload["strength"]) <= 1.0, "belief.strength must be in [0, 1]")
    _require_str_list(payload, "verdict_refs", "belief")
    # A decided stance must cite at least one verdict; UNTESTED may have none.
    if payload["stance"] in {"SUPPORTED", "REJECTED", "CONTESTED"}:
        _require(
            payload["verdict_refs"],
            "belief.verdict_refs must be non-empty for a SUPPORTED/REJECTED/CONTESTED stance",
        )
    if "prev_state" in payload:
        _require_str(payload, "prev_state", "belief")


# ===========================================================================
# Sprint 8 (ARCH-008) — placebo battery (G-3) + graduation gate (G-1) records.
# placebo_run: a null-twin dry-run of the verdict pipeline (writes no verdict,
# burns no window). second_lens: the independent-feed evidence a promotion needs.
# promotion: a claim's lifecycle record, appendable only through all four gates.
# ===========================================================================

# The null-construction methods a placebo may use (DEVQ-018). direction_permutation
# for directional event claims; entry_time_shuffle for fixed-direction timing claims.
_PLACEBO_METHODS = frozenset({"direction_permutation", "entry_time_shuffle"})


def _validate_placebo_run(payload: dict) -> None:
    """placebo_run v1 (ARCH-008 §1, G-3) — N seeded null-twin runs of a setup.

    ``hypothesis_ref`` is the judged hypothesis whose exact setup was replayed;
    ``method`` is the null construction (DEVQ-018); ``seed`` is the base seed (run
    i uses seed+i); ``outcomes`` is one tri-state per run and ``n_runs`` == its
    length; ``n_pass`` == the number of PASS outcomes (a healthy judge yields at
    most ~alpha*n_runs). A placebo_run NEVER carries a window_burn or a verdict —
    the closed key set makes that structurally impossible (the type-audit ARCH-008
    §Acceptance requires).
    """
    _check_keys(
        payload,
        {"hypothesis_ref", "method", "seed", "n_runs", "outcomes", "n_pass"},
        set(),
        "placebo_run",
    )
    _require_str(payload, "hypothesis_ref", "placebo_run")
    _require(
        payload["method"] in _PLACEBO_METHODS,
        f"placebo_run.method must be one of {sorted(_PLACEBO_METHODS)}",
    )
    _require_int(payload, "seed", "placebo_run", non_negative=True)
    _require_int(payload, "n_runs", "placebo_run", non_negative=True)
    _require(payload["n_runs"] >= 1, "placebo_run.n_runs must be >= 1")
    _require(isinstance(payload["outcomes"], list), "placebo_run.outcomes must be a list")
    for i, oc in enumerate(payload["outcomes"]):
        _require(
            oc in _VERDICT_VALUES,
            f"placebo_run.outcomes[{i}] must be one of {sorted(_VERDICT_VALUES)}",
        )
    _require(
        len(payload["outcomes"]) == payload["n_runs"],
        "placebo_run.n_runs must equal len(outcomes)",
    )
    _require_int(payload, "n_pass", "placebo_run", non_negative=True)
    _require(
        payload["n_pass"] == sum(1 for oc in payload["outcomes"] if oc == "PASS"),
        "placebo_run.n_pass must equal the count of PASS outcomes (audit consistency)",
    )


def _validate_second_lens(payload: dict) -> None:
    """second_lens v1 (ARCH-008 §2, G-1, DEVQ-020) — independent-feed agreement.

    The evidence leg a promotion needs beyond a PASS verdict: a SECOND, independent
    data source agreeing on the overlapping slice. ``source_name`` names the feed;
    ``overlap_manifest`` is the bulk_manifest id of the shared slice (auditable
    against real bytes — the graduation module checks it resolves); ``agreement_summary``
    is structured so an IVF can re-derive the agreement. No real second feed exists
    yet (Owner-provided, future), so the GATE exists but no promotion can pass it.
    """
    _check_keys(
        payload,
        {"source_name", "overlap_manifest", "agreement_summary"},
        set(),
        "second_lens",
    )
    _require_str(payload, "source_name", "second_lens")
    _require(payload["source_name"].strip(), "second_lens.source_name must be non-empty")
    _require_str(payload, "overlap_manifest", "second_lens")
    summ = payload["agreement_summary"]
    _require(isinstance(summ, dict), "second_lens.agreement_summary must be an object")
    _check_keys(summ, {"n_overlap", "n_agree", "agreement_rate", "notes"}, set(),
                "second_lens.agreement_summary")
    _require_int(summ, "n_overlap", "second_lens.agreement_summary", non_negative=True)
    _require_int(summ, "n_agree", "second_lens.agreement_summary", non_negative=True)
    _require_number(summ, "agreement_rate", "second_lens.agreement_summary")
    _require(
        0.0 <= float(summ["agreement_rate"]) <= 1.0,
        "second_lens.agreement_summary.agreement_rate must be in [0, 1]",
    )
    _require_str(summ, "notes", "second_lens.agreement_summary")


def _validate_promotion(payload: dict) -> None:
    """promotion v1 (ARCH-008 §2, G-1) — a claim's lifecycle record.

    A promotion is appendable ONLY when all four gates hold (enforced by the
    graduation module, which alone has the store to check the referenced records):
    (a) ``verdict_ref`` is a PASS verdict; (b) ``placebo_ref`` is a placebo_run with
    no excess null passes; (c) ``second_lens_ref`` is a second_lens; (d) the belief
    at ``belief_ref`` is not CONTESTED. The schema fixes the shape; the module fixes
    the semantics (mirroring how the belief layer type-checks verdict_refs). A
    promotion is a lifecycle record — it does NOT add a belief stance (beliefs stay
    verdict-only); ``family``/``claim`` identify the belief chain it graduates.
    """
    _check_keys(
        payload,
        {"family", "claim", "hypothesis_ref", "verdict_ref", "placebo_ref",
         "second_lens_ref", "belief_ref"},
        set(),
        "promotion",
    )
    for k in ("family", "claim", "hypothesis_ref", "verdict_ref", "placebo_ref",
              "second_lens_ref", "belief_ref"):
        _require_str(payload, k, "promotion")
        _require(payload[k].strip(), f"promotion.{k} must be non-empty")


def _validate_dataset_scope(payload: dict) -> None:
    """dataset_scope v1 (WO-03, refs A-007 ruling (d)(1)) — a data-collection
    scope's registration record: the one place carrying a dataset's pinned
    IANA zone (+ the evidence it was determined from), its pinned ingest
    path, the batch-forward collection protocol in one paragraph, and its
    OOS designation. Every field is required and non-empty — the ceremony
    this record captures (typed at registration, per J-029/030) has no
    silent-default form; an incomplete registration is refused, not filled in.
    """
    _check_keys(
        payload,
        {
            "dataset",
            "iana_zone",
            "zone_evidence",
            "ingest_path",
            "batch_forward_protocol",
            "oos_designation",
            "anchor_ts",
        },
        set(),
        "dataset_scope",
    )
    for k in (
        "dataset", "iana_zone", "zone_evidence", "ingest_path",
        "batch_forward_protocol", "oos_designation",
    ):
        _require_str(payload, k, "dataset_scope")
        _require(payload[k].strip(), f"dataset_scope.{k} must be non-empty")
    _require_int(payload, "anchor_ts", "dataset_scope")


def _validate_r6_ingest_batch(payload: dict) -> None:
    """r6_ingest_batch v1 (WO-03, refs A-007 ruling (b)) — the mechanical
    record of one batch-forward ingest run: journals every ingest batch so
    the journal itself IS the collection record, and gives ``ingest_r6.py``
    something to query for its own idempotency guard (strictly-newer-only,
    no overlap/duplicate/backwards batches).
    """
    _check_keys(
        payload,
        {"dataset", "ts_start", "ts_end", "row_count", "source"},
        set(),
        "r6_ingest_batch",
    )
    _require_str(payload, "dataset", "r6_ingest_batch")
    _require(payload["dataset"].strip(), "r6_ingest_batch.dataset must be non-empty")
    _require_int(payload, "ts_start", "r6_ingest_batch")
    _require_int(payload, "ts_end", "r6_ingest_batch")
    _require(
        payload["ts_end"] > payload["ts_start"],
        "r6_ingest_batch.ts_end must be > ts_start",
    )
    _require_int(payload, "row_count", "r6_ingest_batch", non_negative=True)
    _require_str(payload, "source", "r6_ingest_batch")
    _require(payload["source"].strip(), "r6_ingest_batch.source must be non-empty")


def _validate_npsu_legacy_import(payload: dict, where: str) -> None:
    """npsu_legacy_import_trade / _shadow v1 (WO-07 stage B, refs A-020) — one
    record per SOURCE FILE BATCH (D-019 decision (b), ratified A-020): the
    journal records the migration EVENT, the actual rows live in BulkStore/
    Parquet (``bulk_manifest_ref``). ``epistemic_weight`` must be the exact
    literal ``"zero"`` — a structural marker (Architecture B.1), not free text
    — so ``qrf.kernel.records.epistemic.is_tainted`` can key on record TYPE
    alone; the field exists for human-readable audit, not as the gate itself.

    ``duplicate_source_paths`` (F-MIG-1, A-030): OTHER known source paths
    whose bytes are IDENTICAL (same sha256) to ``source`` — content migrates
    once, but every path it was ever known under stays reconstructable from
    the journal alone (never a silent drop). REQUIRED, always a list (empty
    when the file was unique in its migration batch) — explicit, not an
    optional field a caller could forget.
    """
    _check_keys(
        payload,
        {
            "source", "file_sha256", "row_count", "bulk_manifest_ref",
            "epistemic_weight", "duplicate_source_paths",
        },
        set(),
        where,
    )
    _require_str(payload, "source", where)
    _require(payload["source"].strip(), f"{where}.source must be non-empty")
    _require_str(payload, "file_sha256", where)
    _require(
        len(payload["file_sha256"]) == 64,
        f"{where}.file_sha256 must be a 64-char sha256 hex digest",
    )
    _require_int(payload, "row_count", where, non_negative=True)
    _require_str(payload, "bulk_manifest_ref", where)
    _require(payload["bulk_manifest_ref"].strip(), f"{where}.bulk_manifest_ref must be non-empty")
    _require_str(payload, "epistemic_weight", where)
    _require(
        payload["epistemic_weight"] == "zero",
        f'{where}.epistemic_weight must be exactly "zero" (Architecture B.1)',
    )
    _require(
        isinstance(payload["duplicate_source_paths"], list)
        and all(isinstance(p, str) and p.strip() for p in payload["duplicate_source_paths"]),
        f"{where}.duplicate_source_paths must be a list of non-empty strings",
    )


def _validate_npsu_legacy_import_trade(payload: dict) -> None:
    _validate_npsu_legacy_import(payload, "npsu_legacy_import_trade")


def _validate_npsu_legacy_import_shadow(payload: dict) -> None:
    _validate_npsu_legacy_import(payload, "npsu_legacy_import_shadow")


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
    ("trial_count", 3): _validate_trial_count_v3,
    ("hypothesis", 1): _validate_hypothesis,
    ("hypothesis", 2): _validate_hypothesis_v2,
    ("hypothesis", 3): _validate_hypothesis_v3,
    ("verdict", 1): _validate_verdict,
    ("verdict", 2): _validate_verdict_v2,
    ("verdict", 3): _validate_verdict_v3,
    ("anomaly_scan", 1): _validate_anomaly_scan,
    ("question", 1): _validate_question,
    ("belief", 1): _validate_belief,
    ("placebo_run", 1): _validate_placebo_run,
    ("second_lens", 1): _validate_second_lens,
    ("promotion", 1): _validate_promotion,
    ("dataset_scope", 1): _validate_dataset_scope,
    ("r6_ingest_batch", 1): _validate_r6_ingest_batch,
    ("npsu_legacy_import_trade", 1): _validate_npsu_legacy_import_trade,
    ("npsu_legacy_import_shadow", 1): _validate_npsu_legacy_import_shadow,
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

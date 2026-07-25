"""HypothesisRegistry — turn a human YAML into a frozen, validated hypothesis.

Implementation Blueprint v1.0 §4.5, ARCH-006 §1. A hypothesis lives twice: as a
human-editable YAML under ``configs/hypotheses/`` (the surface) and, once
registered, as a ``hypothesis`` record in the ledger (the truth). Registration
resolves the YAML's instrument specs (``smc.fvg@0.1.0``) to their registration
record ids, runs the pre-registration validations, and appends the record; the
record's own ``content_hash`` is the seal, so a changed YAML re-registers as a
NEW id and :meth:`verify_frozen` catches any drift between file and ledger.

Pre-registration validations (ARCH-006 §1), all enforced here — the only layer
with the store + the cost-model allowlist to judge them:

* ``embargo_bars >= execution.hold_bars + 1`` (DEVQ-011, BINDING) — the boundary
  gap must clear a full hold plus one so a trade opened at a train→test boundary
  cannot leak across it;
* ``cost_model_ref`` is a known cost model (DEVQ-008) — passed in as an
  allowlist so the kernel stays domain-blind (it never reads the venue config);
* every instrument exists AND has a passing calibration (no soft-pass);
* **any order-block instrument REFUSES registration** (DEVQ-010) — an order
  block's zone is only knowable after its break bar, a restatement gate that no
  hypothesis may cross until the detector encodes it.

Registration is idempotent: a YAML whose resolved payload + window already exist
returns the existing record and writes nothing (ARCH-006 §4 "registers
idempotently").

This module is kernel: it imports the records layer + trial/error taxonomy and
stdlib/yaml only; it speaks ``scope`` / ``lineage`` / ``cost_model_ref`` and
never a trading word (firewall-clean).
"""

from __future__ import annotations

from collections.abc import Collection
from pathlib import Path
from typing import Any

import yaml

from qrf.kernel.errors import (
    SchemaViolation,
    TamperedHypothesisError,
    UncalibratedInstrumentError,
    UnknownInstrumentError,
    UnknownRecordError,
)
from qrf.kernel.records.record import Record, now_ns
from qrf.kernel.records.store import RecordStore

# Instrument families whose events cross a restatement gate and may not be
# pre-registered until the detector encodes the break-bar knowability (DEVQ-010).
_RESTATEMENT_GATED_PREFIX = "smc.order_block"

# The execution keys the record carries, in ExecutionSpec.as_dict() shape.
_EXECUTION_KEYS = ("hold_bars", "strength_min", "stop_offset", "target_offset", "size")

# The v2 pre-commitments (DEVQ-014/015): the plain-words claim, the conclusion to
# draw for each outcome (fixed BEFORE running), and the family the multiplicity
# burden accrues to. All three or none.
_V2_KEYS = ("thesis", "outcome_interpretations", "family")
_OUTCOMES = ("PASS", "FAIL", "INSUFFICIENT")


class HypothesisRegistry:
    """Pre-register hypotheses from YAML into the ledger (Blueprint §4.5)."""

    def __init__(self, store: RecordStore) -> None:
        self._store = store

    # -- config loading -------------------------------------------------------
    @staticmethod
    def load_config(path: str | Path) -> dict[str, Any]:
        """Parse a hypothesis YAML into a plain dict (the human surface)."""
        p = Path(path)
        if not p.exists():
            raise SchemaViolation(f"hypothesis config {p} not found")
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            raise SchemaViolation(f"hypothesis config {p} must be a mapping")
        return doc

    # -- instrument resolution ------------------------------------------------
    def _resolve_instrument(self, spec: str) -> tuple[str, str]:
        """Resolve ``"id@version"`` (or ``"id"`` = latest) to ``(instrument_id, ref)``.

        Raises :class:`UnknownInstrumentError` when no matching registration
        exists. When several versions match ``id`` with no ``@version`` given,
        the most recently registered wins (journal order).
        """
        if "@" in spec:
            iid, _, version = spec.partition("@")
        else:
            iid, version = spec, None
        matches = [
            r
            for r in self._store.query(record_type="instrument_registered")
            if r.payload["instrument_id"] == iid
            and (version is None or r.payload["version"] == version)
        ]
        if not matches:
            raise UnknownInstrumentError(
                f"hypothesis references instrument {spec!r} with no matching "
                "instrument_registered record (register + calibrate it first)"
            )
        return iid, matches[-1].record_id

    def _passing_calibration(self, ref: str) -> bool:
        return any(
            c.payload.get("instrument_ref") == ref and c.payload.get("overall_pass")
            for c in self._store.query(record_type="calibration")
        )

    # -- payload assembly -----------------------------------------------------
    def _build_payload(self, config: dict[str, Any], cost_model_refs: Collection[str]) -> dict:
        """Validate the config and assemble the canonical hypothesis payload.

        Resolves instrument specs to refs and enforces every ARCH-006 §1
        pre-registration validation. Does not touch the store beyond read-only
        resolution/calibration lookups.
        """
        required = {
            "lineage",
            "scope",
            "instruments",
            "setup_dsl",
            "execution",
            "cost_model_ref",
            "split_spec",
            "thresholds",
        }
        missing = required - set(config)
        if missing:
            raise SchemaViolation(f"hypothesis config missing key(s) {sorted(missing)}")

        src_exec = config["execution"]
        execution = {k: src_exec.get(k) for k in _EXECUTION_KEYS if k in src_exec}
        if "hold_bars" not in execution or "size" not in execution:
            raise SchemaViolation("hypothesis execution must set hold_bars and size")

        split_spec = config["split_spec"]
        embargo = split_spec.get("embargo_bars")
        hold = execution["hold_bars"]
        # DEVQ-011 (BINDING): the boundary gap must clear a full hold plus one.
        if not isinstance(embargo, int) or isinstance(embargo, bool):
            raise SchemaViolation("split_spec.embargo_bars must be an int")
        if not isinstance(hold, int) or isinstance(hold, bool) or hold < 1:
            raise SchemaViolation("execution.hold_bars must be an int >= 1")
        if embargo < hold + 1:
            raise SchemaViolation(
                f"split_spec.embargo_bars ({embargo}) must be >= execution.hold_bars + 1 "
                f"({hold + 1}) — DEVQ-011 BINDING boundary-gap rule; registration refused"
            )

        # DEVQ-008: the cost model must be a known one (allowlist injected).
        cost_model_ref = config["cost_model_ref"]
        if cost_model_ref not in set(cost_model_refs):
            raise SchemaViolation(
                f"cost_model_ref {cost_model_ref!r} is not a known cost model "
                f"(available: {sorted(cost_model_refs)}) — DEVQ-008; registration refused"
            )

        # Resolve instruments; enforce existence, the order-block gate, calibration.
        instrument_refs: list[str] = []
        for spec in config["instruments"]:
            iid, ref = self._resolve_instrument(str(spec))
            if iid.startswith(_RESTATEMENT_GATED_PREFIX):
                raise SchemaViolation(
                    f"instrument {spec!r} is order-block family: its zone is only "
                    "knowable after the break bar, a restatement gate no hypothesis "
                    "may cross until the detector encodes it — DEVQ-010; "
                    "registration refused"
                )
            if not self._passing_calibration(ref):
                raise UncalibratedInstrumentError(
                    f"instrument {spec!r} (ref {ref}) has no passing calibration; "
                    "register + calibrate before pre-registering a hypothesis (no soft-pass)"
                )
            instrument_refs.append(ref)

        return {
            "lineage": str(config["lineage"]),
            "scope": str(config["scope"]),
            "instrument_refs": instrument_refs,
            "setup_dsl": dict(config["setup_dsl"]),
            "execution": execution,
            "cost_model_ref": str(cost_model_ref),
            "split_spec": {
                "n_folds": split_spec["n_folds"],
                "embargo_bars": embargo,
            },
            "thresholds": dict(config["thresholds"]),
        }

    def _window_ref(self, config: dict[str, Any]) -> str:
        """The window this hypothesis binds to (its record parent). Must exist."""
        window_ref = config.get("window")
        if not isinstance(window_ref, str) or not window_ref:
            raise SchemaViolation("hypothesis config must name a 'window' record id")
        rec = self._store.get(window_ref)  # UnknownRecordError if absent
        if rec.record_type != "window":
            raise SchemaViolation(
                f"hypothesis 'window' {window_ref} is a {rec.record_type!r}, not a window"
            )
        return window_ref

    def _v2_extra(self, config: dict[str, Any]) -> dict | None:
        """Assemble the v2 pre-commitments from ``config``, or None if absent.

        v2 (DEVQ-014/015) adds ``thesis``, ``outcome_interpretations`` and
        ``family`` — all three, or none (a partial set is refused). Shape is fully
        validated by the schema at append; this fixes the canonical payload.

        v2.1 (ARCH-007 §4, DEVQ-014): an optional ``observatory_ancestry`` — a list
        of ``question`` record ids the hypothesis descends from. Each id is checked
        to EXIST and be a ``question`` record (the composer cannot invent an
        ancestor or point at the wrong record type). Ancestry only makes sense on a
        v2 hypothesis, so it is refused when the v2 pre-commitments are absent.
        """
        present = [k for k in _V2_KEYS if k in config]
        has_ancestry = "observatory_ancestry" in config
        if not present:
            if has_ancestry:
                raise SchemaViolation(
                    "observatory_ancestry requires a v2 hypothesis (thesis, "
                    "outcome_interpretations, family must be present)"
                )
            return None
        if len(present) != len(_V2_KEYS):
            missing = [k for k in _V2_KEYS if k not in config]
            raise SchemaViolation(
                f"hypothesis v2 requires all of {list(_V2_KEYS)}; missing {missing} "
                "(thesis, outcome_interpretations and family go together)"
            )
        interp = config["outcome_interpretations"]
        if not isinstance(interp, dict) or set(interp) != set(_OUTCOMES):
            raise SchemaViolation(
                f"outcome_interpretations must have exactly the keys {list(_OUTCOMES)}"
            )
        extra: dict[str, Any] = {
            "thesis": config["thesis"],
            "outcome_interpretations": {k: interp[k] for k in _OUTCOMES},
            "family": config["family"],
        }
        if has_ancestry:
            extra["observatory_ancestry"] = self._resolve_ancestry(config["observatory_ancestry"])
        return extra

    def _resolve_ancestry(self, ancestry: Any) -> list[str]:
        """Validate ``observatory_ancestry``: a list of existing question ids."""
        if not isinstance(ancestry, list):
            raise SchemaViolation("observatory_ancestry must be a list of question ids")
        resolved: list[str] = []
        for qid in ancestry:
            if not isinstance(qid, str) or not qid:
                raise SchemaViolation("observatory_ancestry ids must be non-empty strings")
            try:
                rec = self._store.get(qid)
            except UnknownRecordError as e:
                raise SchemaViolation(
                    f"observatory_ancestry {qid!r} does not exist — a hypothesis may "
                    "only descend from a real question record"
                ) from e
            if rec.record_type != "question":
                raise SchemaViolation(
                    f"observatory_ancestry {qid} is a {rec.record_type!r}, not a question"
                )
            resolved.append(qid)
        return resolved

    def _resolved_payload(
        self, config: dict[str, Any], cost_model_refs: Collection[str]
    ) -> tuple[dict, int]:
        """The canonical hypothesis payload + its schema version (v1 or v2)."""
        payload = self._build_payload(config, cost_model_refs)
        v2 = self._v2_extra(config)
        if v2 is not None:
            payload = {**payload, **v2}
            return payload, 2
        return payload, 1

    # -- registration ---------------------------------------------------------
    def register(
        self,
        config: str | Path | dict[str, Any],
        *,
        cost_model_refs: Collection[str],
        producer: str = "human:composer",
        event_ts: int | None = None,
    ) -> Record:
        """Pre-register a hypothesis; return its (new or pre-existing) record.

        ``config`` is a YAML path or an already-parsed dict. ``cost_model_refs``
        is the allowlist of known cost model names (injected so the kernel never
        reads the venue config). Idempotent: an identical resolved payload +
        window already in the ledger is returned unchanged.

        A NEW hypothesis MUST carry the v2 pre-commitments (thesis,
        outcome_interpretations, family — DEVQ-014/015); only a record already in
        the ledger under the v1 schema (H-001) is exempt, and it is returned by
        the idempotency match rather than re-registered.
        """
        if isinstance(config, (str, Path)):
            config = self.load_config(config)
        window_ref = self._window_ref(config)
        payload, schema_version = self._resolved_payload(config, cost_model_refs)

        # Idempotency: same resolved payload + same window parent => same hypothesis.
        for rec in self._store.query(record_type="hypothesis"):
            if rec.payload == payload and rec.parents == (window_ref,):
                return rec

        if schema_version < 2:
            raise SchemaViolation(
                "a new hypothesis must declare thesis, outcome_interpretations and "
                "family (schema v2, DEVQ-014/015); the pre-committed interpretation is "
                "as load-bearing as the pre-committed thresholds"
            )
        return self._store.append(
            "hypothesis",
            payload,
            producer=producer,
            event_ts=event_ts if event_ts is not None else now_ns(),
            parents=[window_ref],
            schema_version=schema_version,
        )

    # -- freeze verification --------------------------------------------------
    def verify_frozen(
        self,
        hypothesis_ref: str,
        config: str | Path | dict[str, Any],
        *,
        cost_model_refs: Collection[str],
    ) -> None:
        """Raise :class:`TamperedHypothesisError` if the YAML no longer matches the record.

        Rebuilds the canonical payload from ``config`` and compares it to the
        stored record's payload (and window parent). A drifted YAML would produce
        a different payload — hence a different id — so a match confirms the file
        that produced this record is unchanged.
        """
        try:
            rec = self._store.get(hypothesis_ref)
        except UnknownRecordError as e:
            raise TamperedHypothesisError(
                f"no hypothesis record {hypothesis_ref!r} to verify against"
            ) from e
        if rec.record_type != "hypothesis":
            raise SchemaViolation(
                f"record {hypothesis_ref} is a {rec.record_type!r}, not a hypothesis"
            )
        if isinstance(config, (str, Path)):
            config = self.load_config(config)
        window_ref = self._window_ref(config)
        payload, _ = self._resolved_payload(config, cost_model_refs)
        if rec.payload != payload or rec.parents != (window_ref,):
            raise TamperedHypothesisError(
                f"hypothesis {hypothesis_ref} no longer matches its config: the YAML "
                "was edited after registration (a changed hypothesis must re-register "
                "as a new id, never mutate an existing verdict's basis)"
            )

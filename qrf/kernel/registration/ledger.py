"""The trial ledger: per-family registration, capacity 100, alpha spent
incrementally (AM-03).

Built on qrf.kernel.records.store.RecordStore, exactly like S02's window
ledger -- append-only, hash-chained, single-writer. Registration FREEZES,
before any test runs, everything A-015 §4.1 requires: the hypothesis
statement (as a hash), the statistic/detector identity, the data span,
the window, the decision thresholds (as a hash), and the alpha allocated.
A change to ANY of those fields for an existing hypothesis id is refused
(RegistrationMismatch) -- it MINTS A NEW HYPOTHESIS, it never edits one.

MIGRATION REQUIREMENT (AM-03, binding): every record also carries the
allocation rule BY NAME, the alpha this registration received, the
family's capacity, and the count spent at that moment -- so a future
policy change applies forward only, and every historical registration
remains interpretable under the rule it was actually judged by.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from qrf.errors import (
    BudgetExhausted,
    HypothesisNotRegistered,
    RegistrationMismatch,
    SchemaViolation,
)
from qrf.kernel.records.store import RecordStore
from qrf.kernel.registration.alpha import ALLOCATION_RULE_NAME, alpha_for_registration_index

DEFAULT_CAPACITY = 100

_FROZEN_FIELDS = (
    "family_id",
    "statement_hash",
    "detector_name",
    "detector_version",
    "data_span_start_utc",
    "data_span_end_utc",
    "window_id",
    "thresholds_hash",
)


def validate_registration_payload(payload: dict) -> None:
    required = {
        "hypothesis_id",
        "family_id",
        "statement_hash",
        "detector_name",
        "detector_version",
        "data_span_start_utc",
        "data_span_end_utc",
        "window_id",
        "thresholds_hash",
        "allocation_rule",
        "alpha",
        "capacity",
        "spent_count_at_registration",
        "phrase_hash",
    }
    if not required.issubset(payload):
        raise SchemaViolation(
            "registration payload missing required fields", sorted(required - payload.keys())
        )
    if not isinstance(payload["phrase_hash"], str) or len(payload["phrase_hash"]) != 64:
        raise SchemaViolation(
            "registration phrase_hash must be a 64-char hex string", payload["phrase_hash"]
        )
    if not isinstance(payload["alpha"], (int, float)) or not (0 < payload["alpha"] < 1):
        raise SchemaViolation("registration alpha must be in (0, 1)", payload["alpha"])


@dataclass(frozen=True)
class Registration:
    hypothesis_id: str
    family_id: str
    statement_hash: str
    detector_name: str
    detector_version: str
    data_span_start_utc: int
    data_span_end_utc: int
    window_id: str
    thresholds_hash: str
    allocation_rule: str
    alpha: float
    capacity: int
    spent_count_at_registration: int
    phrase_hash: str


class TrialLedger:
    def __init__(self, path: Path):
        self._store = RecordStore(Path(path), validate_registration_payload)

    def _rebuild(self) -> tuple[dict[str, Registration], dict[str, int]]:
        registrations: dict[str, Registration] = {}
        family_counts: dict[str, int] = {}
        for record in self._store.verify():
            reg = Registration(**record.payload)
            registrations[reg.hypothesis_id] = reg
            family_counts[reg.family_id] = family_counts.get(reg.family_id, 0) + 1
        return registrations, family_counts

    def register(
        self,
        *,
        hypothesis_id: str,
        family_id: str,
        statement_hash: str,
        detector_name: str,
        detector_version: str,
        data_span_start_utc: int,
        data_span_end_utc: int,
        window_id: str,
        thresholds_hash: str,
        phrase_hash: str,
        capacity: int = DEFAULT_CAPACITY,
    ) -> Registration:
        """Register a new hypothesis. Refuses (RegistrationMismatch) if
        `hypothesis_id` already exists -- re-registration under the same
        id is never an edit, even with identical fields; a genuinely new
        attempt must use a new id. Refuses (BudgetExhausted) if the
        family is already at capacity. Never call this directly to
        complete a real registration -- use
        qrf.kernel.registration.ceremony.complete_registration(), the
        Owner-gated entry point (A-015 §4.3).
        """
        registrations, family_counts = self._rebuild()
        if hypothesis_id in registrations:
            raise RegistrationMismatch(hypothesis_id, "hypothesis_id (already registered)")
        current_count = family_counts.get(family_id, 0)
        if current_count >= capacity:
            raise BudgetExhausted(family_id, capacity)
        index = current_count + 1
        alpha = alpha_for_registration_index(index)
        payload = {
            "hypothesis_id": hypothesis_id,
            "family_id": family_id,
            "statement_hash": statement_hash,
            "detector_name": detector_name,
            "detector_version": detector_version,
            "data_span_start_utc": data_span_start_utc,
            "data_span_end_utc": data_span_end_utc,
            "window_id": window_id,
            "thresholds_hash": thresholds_hash,
            "allocation_rule": ALLOCATION_RULE_NAME,
            "alpha": alpha,
            "capacity": capacity,
            "spent_count_at_registration": index,
            "phrase_hash": phrase_hash,
        }
        self._store.append(payload)
        return Registration(**payload)

    def lookup(self, hypothesis_id: str) -> Registration:
        registrations, _ = self._rebuild()
        if hypothesis_id not in registrations:
            raise HypothesisNotRegistered(hypothesis_id)
        return registrations[hypothesis_id]

    def family_count(self, family_id: str) -> int:
        _, family_counts = self._rebuild()
        return family_counts.get(family_id, 0)

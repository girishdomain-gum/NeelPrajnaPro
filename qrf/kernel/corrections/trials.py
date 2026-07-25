"""TrialCountLedger — the multiple-testing burden, recorded honestly.

Implementation Blueprint v1.0 §4.8 (and §2 ``trial_count`` schema). Every time a
family of variants is evaluated against a data scope, the number of attempts is
appended as a ``trial_count`` record. The battery reads the accumulated ``m`` at
correction time (§4.7 step 7) to size a Bonferroni/FDR family — so an honest
trial count is the difference between a real edge and a data-mined artifact.

Contract (normative):

* :meth:`bump` appends exactly one ``trial_count`` record; ``n`` is the exact
  number of variants evaluated (no netting, no dedup — every variant counts).
  ``n`` must be ``>= 1`` (a bump of zero is meaningless and is refused by the
  schema).
* :meth:`total` sums ``n_attempts`` across every ``trial_count`` record matching
  a ``(data_scope, lineage)`` pair — accumulation is monotone: appending only
  ever raises the total (there is no decrement surface, mirroring the ledger's
  no-update rule I-1).
* ``source`` is one of ``human`` / ``screener`` / ``generator``. When a
  generator produced the variants, its instrument ref rides along as
  ``generator_ref`` so the lineage of the count is auditable (generator
  inheritance).

This module is kernel: it imports only the records layer and stdlib, speaks the
domain-blind vocabulary of ``data_scope`` / ``lineage`` / ``n_attempts`` (no
trading words), and never judges anything.
"""

from __future__ import annotations

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records.record import Record, now_ns
from qrf.kernel.records.store import RecordStore

# DEVQ-016: "observatory" joins the source enum (trial_count v3). An observatory
# bump is written at v3 so its provenance is first-class; human/screener/generator
# keep writing v1/v2 (forward-only, NOTE-013).
_SOURCES = frozenset({"human", "screener", "generator", "observatory"})


class TrialCountLedger:
    """Append and total ``trial_count`` records (Blueprint §4.8)."""

    def __init__(self, store: RecordStore) -> None:
        self._store = store

    # -- write ----------------------------------------------------------------
    def bump(
        self,
        scope: str,
        lineage: str,
        n: int,
        source: str,
        *,
        family: str | None = None,
        generator_ref: str | None = None,
        parents: list[str] | tuple[str, ...] = (),
        producer: str | None = None,
        event_ts: int | None = None,
    ) -> Record:
        """Append one ``trial_count`` record of ``n`` attempts for ``(scope, lineage)``.

        ``scope`` is a window_ref or a dataset name (``data_scope`` in the
        schema). ``source`` must be one of ``human`` / ``screener`` /
        ``generator``; when ``source == "generator"`` a ``generator_ref`` should
        be supplied so the count inherits the generator's identity. ``family`` is
        the ``{market}/{instrument_family}`` this search's multiplicity burden
        accrues to (DEVQ-015); when supplied the record is written at schema
        version 2 so the deflation can total a family's trials directly. ``parents``
        typically names the window (Blueprint §2 typical parent). Returns the
        appended record.
        """
        if not isinstance(n, int) or isinstance(n, bool):
            raise SchemaViolation("trial_count n must be an int")
        if n < 1:
            raise SchemaViolation(f"trial_count n must be >= 1 (got {n})")
        if source not in _SOURCES:
            raise SchemaViolation(
                f"trial_count source {source!r} must be one of {sorted(_SOURCES)}"
            )
        payload: dict = {
            "data_scope": scope,
            "lineage": lineage,
            "n_attempts": n,
            "source": source,
        }
        if generator_ref is not None:
            payload["generator_ref"] = generator_ref
        schema_version = 1
        if family is not None:
            if not isinstance(family, str) or not family.strip():
                raise SchemaViolation("trial_count family must be a non-empty string")
            payload["family"] = family
            schema_version = 2
        # DEVQ-016: an observatory bump is written at v3 (its source enum value only
        # exists there); v3 requires a family, so refuse an observatory bump without.
        if source == "observatory":
            if family is None:
                raise SchemaViolation("an observatory trial_count requires a family")
            schema_version = 3
        return self._store.append(
            "trial_count",
            payload,
            producer=producer or source,
            event_ts=event_ts if event_ts is not None else now_ns(),
            parents=list(parents),
            schema_version=schema_version,
        )

    # -- read -----------------------------------------------------------------
    def total(self, scope: str, lineage: str) -> int:
        """Sum ``n_attempts`` across every record matching ``(scope, lineage)``.

        Monotone by construction: the store has no delete/update surface, so this
        total only ever rises as bumps are appended.
        """
        return sum(
            rec.payload["n_attempts"]
            for rec in self._store.query(record_type="trial_count")
            if rec.payload["data_scope"] == scope and rec.payload["lineage"] == lineage
        )

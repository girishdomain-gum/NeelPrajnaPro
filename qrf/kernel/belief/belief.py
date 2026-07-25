"""BeliefLayer — what the evidence has taught us, updated only by verdicts.

Implementation Blueprint v1.0 §4.8 / §5 arrow 10, ARCH-007 §3. The belief ledger
holds one append-only chain of states per ``(family, claim)``. A state records the
current ``stance`` (SUPPORTED / REJECTED / UNTESTED), a ``strength`` in [0, 1], and
the ``verdict_refs`` that are its ENTIRE evidence base.

The single load-bearing rule (the "arrow-8" type-audit, ARCH-007 §3): a belief is
updated ONLY by a ``verdict`` event. :meth:`update` refuses any evidence ref that
is not a verdict record — beliefs never cite screener metrics, selftest results,
questions, or notes. A screener shortlist is a search, a selftest is a wiring gate,
a question is a hunch; none of them is evidence about the world. Only a verdict —
a pre-registered claim judged on burned out-of-sample data — moves a belief.

Append-only, never overwrite: a new verdict appends a NEW belief state that points
at the prior one (``prev_state``) and carries the accumulated ``verdict_refs``. The
chain is the history of what a claim's evidence has said over time; :meth:`latest`
reads the head.

Stance / strength are DERIVED from the cited verdicts alone (so the IVF can
recompute a belief independently from the verdict set):

* stance = the decision of the most recent DECISIVE verdict — PASS ⇒ SUPPORTED,
  FAIL ⇒ REJECTED; a chain with only INSUFFICIENT verdicts is UNTESTED.
* strength = evidence weight of that decisive verdict from its own recorded
  one-sided p (H0: no edge): a FAIL is strong when the data sit deep in the null
  (strength = p); a PASS is strong when they sit far from it (strength = 1 - p);
  UNTESTED has strength 0. (Exact semantics posed for ratification in DEVQ-016.)

This module is kernel: records layer + error taxonomy + stdlib only. It has NO
import of the battery and the battery has NO import of it (the posterior is never
read back into a verdict — firewall-style, Blueprint §4.8).
"""

from __future__ import annotations

from qrf.kernel.errors import SchemaViolation, UnknownRecordError
from qrf.kernel.records.record import Record, now_ns
from qrf.kernel.records.store import RecordStore

SUPPORTED = "SUPPORTED"
REJECTED = "REJECTED"
UNTESTED = "UNTESTED"

# verdict.verdict value -> stance a decisive verdict drives.
_DECISION = {"PASS": SUPPORTED, "FAIL": REJECTED}


class BeliefLayer:
    """Update and read the per-(family, claim) belief chain (Blueprint §4.8)."""

    def __init__(self, store: RecordStore) -> None:
        self._store = store

    # -- read -----------------------------------------------------------------
    def latest(self, family: str, claim: str) -> Record | None:
        """The head belief state for ``(family, claim)``, or None if never formed.

        Journal order is chain order (append-only), so the last matching record is
        the current state.
        """
        head: Record | None = None
        for rec in self._store.query(record_type="belief"):
            if rec.payload["family"] == family and rec.payload["claim"] == claim:
                head = rec
        return head

    # -- update ---------------------------------------------------------------
    def _verdict(self, verdict_ref: str) -> Record:
        """Resolve ``verdict_ref``, enforcing it IS a verdict (the arrow-8 audit)."""
        try:
            rec = self._store.get(verdict_ref)
        except UnknownRecordError as e:
            raise SchemaViolation(
                f"belief evidence {verdict_ref!r} does not exist"
            ) from e
        if rec.record_type != "verdict":
            raise SchemaViolation(
                f"belief evidence {verdict_ref} is a {rec.record_type!r}, not a verdict — "
                "beliefs are updated ONLY by verdict events (never screener metrics, "
                "selftests, or questions)"
            )
        return rec

    @staticmethod
    def _stance_and_strength(verdicts: list[Record]) -> tuple[str, float]:
        """Derive (stance, strength) from a verdict chain (newest-decisive wins)."""
        decisive = [v for v in verdicts if v.payload["verdict"] in _DECISION]
        if not decisive:
            return UNTESTED, 0.0
        driver = decisive[-1]  # most recent decisive verdict
        stance = _DECISION[driver.payload["verdict"]]
        p = driver.payload.get("statistics", {}).get("t_one_sided", {}).get("p")
        if p is None:
            strength = 1.0  # a decisive verdict with a degenerate/undefined p
        elif stance == REJECTED:
            strength = float(p)
        else:  # SUPPORTED
            strength = 1.0 - float(p)
        return stance, max(0.0, min(1.0, strength))

    def update(
        self,
        verdict_ref: str,
        *,
        claim: str,
        family: str,
        producer: str = "belief",
        event_ts: int | None = None,
    ) -> Record:
        """Fold ``verdict_ref`` into the ``(family, claim)`` belief; append a new state.

        Refuses a non-verdict ``verdict_ref`` (the arrow-8 audit). Idempotent: if the
        current head already cites this verdict, it is returned unchanged (re-running
        the seeding never doubles a state). Otherwise the accumulated verdict_refs
        (prior chain + this verdict) drive a fresh stance + strength, and a new
        ``belief`` record is appended pointing back at the prior state.
        """
        self._verdict(verdict_ref)  # arrow-8 audit: refuse a non-verdict ref

        prior = self.latest(family, claim)
        prior_refs: list[str] = list(prior.payload["verdict_refs"]) if prior else []
        if verdict_ref in prior_refs:
            return prior  # already incorporated — idempotent

        verdict_refs = [*prior_refs, verdict_ref]
        verdicts = [self._store.get(r) for r in verdict_refs]
        stance, strength = self._stance_and_strength(verdicts)

        payload: dict = {
            "family": family,
            "claim": claim,
            "stance": stance,
            "strength": strength,
            "verdict_refs": verdict_refs,
        }
        parents = [verdict_ref]
        if prior is not None:
            payload["prev_state"] = prior.record_id
            parents.append(prior.record_id)
        return self._store.append(
            "belief",
            payload,
            producer=producer,
            event_ts=event_ts if event_ts is not None else now_ns(),
            parents=parents,
        )

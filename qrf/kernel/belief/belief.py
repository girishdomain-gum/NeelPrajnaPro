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
recompute a belief independently from the verdict set) — the DEVQ-016 ruling:

* stance = the decision of the most recent DECISIVE verdict — PASS ⇒ SUPPORTED,
  FAIL ⇒ REJECTED; a chain with only INSUFFICIENT verdicts is UNTESTED. BUT the
  moment decisive verdicts DISAGREE (a PASS after a FAIL, or vice versa) the
  stance is CONTESTED — recency must not paper over a genuine conflict; the claim
  stays contested until a pre-registered replication tie-breaks it.
* strength = DECISIVENESS of the deciding verdict = ``2 · |p − 0.5|`` ∈ [0, 1],
  where ``p`` is its one-sided p (H0: no edge): how far the evidence sits from a
  coin-flip. H-001's FAIL (p=0.9435) ⇒ 0.887 (the data leaned firmly negative);
  a result at p≈0.5 ⇒ ≈0 (decided, but on thin evidence). This is NOT a posterior
  probability and must never be read as one — the Bayesian odds/LR layer is a
  separate, deferred ADR (DEVQ-016). UNTESTED has strength 0.

This module is kernel: records layer + error taxonomy + stdlib only. It has NO
import of the battery and the battery has NO import of it (the posterior is never
read back into a verdict — firewall-style, Blueprint §4.8).
"""

from __future__ import annotations

from qrf.kernel.errors import SchemaViolation, UnknownRecordError
from qrf.kernel.records.epistemic import refuse_if_tainted
from qrf.kernel.records.record import Record, now_ns
from qrf.kernel.records.store import RecordStore

SUPPORTED = "SUPPORTED"
REJECTED = "REJECTED"
UNTESTED = "UNTESTED"
CONTESTED = "CONTESTED"

# verdict.verdict value -> stance a decisive verdict drives.
_DECISION = {"PASS": SUPPORTED, "FAIL": REJECTED}


def _decisiveness(p: float | None) -> float:
    """DECISIVENESS = ``2 · |p − 0.5|`` ∈ [0, 1] (DEVQ-016 ruling).

    How far the deciding verdict's evidence sits from a coin-flip. A degenerate /
    undefined p (a zero-variance decisive verdict) counts as maximally decisive.
    NOT a posterior probability — see the module docstring.
    """
    if p is None:
        return 1.0
    return max(0.0, min(1.0, 2.0 * abs(float(p) - 0.5)))


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
        """Derive (stance, strength) from a verdict chain (DEVQ-016 ruling).

        Newest-decisive-wins WHILE decisive verdicts agree; the moment they
        disagree (a PASS after a FAIL, or vice versa) the stance is CONTESTED —
        the conflict is preserved, not resolved by recency. Strength is always the
        DECISIVENESS (``2·|p−0.5|``) of the NEWEST decisive verdict.
        """
        decisive = [v for v in verdicts if v.payload["verdict"] in _DECISION]
        if not decisive:
            return UNTESTED, 0.0
        driver = decisive[-1]  # most recent decisive verdict
        p = driver.payload.get("statistics", {}).get("t_one_sided", {}).get("p")
        strength = _decisiveness(p)
        decisions = {_DECISION[v.payload["verdict"]] for v in decisive}
        if len(decisions) > 1:  # decisive verdicts disagree -> contested
            return CONTESTED, strength
        return _DECISION[driver.payload["verdict"]], strength

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
        # Closed-write-authority gate (Architecture B.1, WO-07): a belief must
        # never trace to zero-epistemic-weight NPSU-migrated data.
        refuse_if_tainted(self._store, verdict_ref, context="BeliefLayer.update")

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

    # -- re-derivation --------------------------------------------------------
    def rederive(
        self,
        family: str,
        claim: str,
        *,
        producer: str = "belief",
        event_ts: int | None = None,
    ) -> Record | None:
        """Recompute the head state under the CURRENT formula; append it if it moved.

        A belief's stance/strength are a pure function of its cited verdicts and the
        derivation rule. When the rule changes (e.g. the DEVQ-016 decisiveness
        ruling superseding p-as-strength), the head state is re-derived from its OWN
        verdict_refs and, if the recomputed (stance, strength) differs, a NEW belief
        state is appended pointing at the prior one — the prior state REMAINS in the
        chain (append-only memory: the ledger shows the belief moved and why).

        Idempotent: if the head already matches the current formula, it is returned
        unchanged. Returns None if the ``(family, claim)`` belief does not exist yet.
        """
        head = self.latest(family, claim)
        if head is None:
            return None
        verdict_refs = list(head.payload["verdict_refs"])
        verdicts = [self._store.get(r) for r in verdict_refs]
        stance, strength = self._stance_and_strength(verdicts)
        if stance == head.payload["stance"] and strength == head.payload["strength"]:
            return head  # already at the current formula — idempotent no-op
        payload = {
            "family": family,
            "claim": claim,
            "stance": stance,
            "strength": strength,
            "verdict_refs": verdict_refs,
            "prev_state": head.record_id,
        }
        return self._store.append(
            "belief",
            payload,
            producer=producer,
            event_ts=event_ts if event_ts is not None else now_ns(),
            parents=[verdict_refs[-1], head.record_id],
        )

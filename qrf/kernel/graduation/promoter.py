"""Promoter — the four-gate graduation of a claim (ARCH-008 §2, G-1).

A ``promotion`` is the strongest thing this system can say about a claim: not just
"a pre-registered test PASSed" but "and it survives the checks that catch a lucky
PASS." ARCH-008 §2 fixes the four gates, ALL of which must hold before a promotion
record may exist — the :class:`Promoter` is the sole writer and enforces them at
append time (mirroring how :class:`~qrf.kernel.belief.belief.BeliefLayer` type-checks
its verdict evidence):

(a) **A PASS verdict.** ``verdict_ref`` resolves to a ``verdict`` whose ``verdict``
    is PASS and whose ``hypothesis_ref`` is the claim being promoted.
(b) **A clean placebo.** ``placebo_ref`` is a ``placebo_run`` OF THE SAME hypothesis
    that shows no EXCESS null passes — its ``n_pass`` is within the band a true null
    predicts at the verdict's own deflated alpha (G-3 feeds G-1).
(c) **A second lens.** ``second_lens_ref`` is a ``second_lens`` whose
    ``overlap_manifest`` resolves to a real ``bulk_manifest`` (an independent feed
    agreeing on shared bytes). No real second feed exists yet (Owner-provided,
    future), so THIS gate makes every promotion impossible today — by design.
(d) **A non-contested belief.** ``belief_ref`` is the ``(family, claim)`` belief, it
    cites this verdict, and its stance is not CONTESTED (a claim with conflicting
    decisive verdicts is not ready to graduate).

A promotion is a LIFECYCLE record: it references the belief chain but does NOT
mutate it (no PROMOTED stance — beliefs stay verdict-only, ARCH-008 §2). Any gate
that fails raises :class:`GraduationRefused` BEFORE anything is written, so a
promotion in the journal is proof all four held.

Kernel module: records layer + error taxonomy + stdlib only; no battery, no belief,
no trading import; it speaks ``verdict`` / ``placebo_run`` / ``belief`` and no
trading word (firewall-clean).
"""

from __future__ import annotations

import math

from qrf.kernel.errors import GraduationRefused, UnknownRecordError
from qrf.kernel.records.record import Record, now_ns
from qrf.kernel.records.store import RecordStore


def _null_pass_ceiling(n_runs: int, effective_alpha: float) -> int:
    """The most null PASSes a TRUE null may plausibly show at ``effective_alpha``.

    Mean + 2 binomial sd of ``Binomial(n_runs, effective_alpha)``, floored at 1 (a
    single expected pass is never "excess"). A placebo with more PASSes than this is
    evidence the judge is over-eager, and the promotion is refused (G-3 → G-1).
    """
    expected = effective_alpha * n_runs
    sd = math.sqrt(max(0.0, expected * (1.0 - effective_alpha)))
    return max(1, math.ceil(expected + 2.0 * sd))


class Promoter:
    """Append a ``promotion`` iff all four graduation gates hold (ARCH-008 §2)."""

    def __init__(self, store: RecordStore) -> None:
        self._store = store

    def _require_type(self, ref: str, expected_type: str, *, leg: str) -> Record:
        """Resolve ``ref``, refusing a missing record or a wrong record type."""
        try:
            rec = self._store.get(ref)
        except UnknownRecordError as e:
            raise GraduationRefused(
                f"graduation gate {leg}: evidence {ref!r} does not exist"
            ) from e
        if rec.record_type != expected_type:
            raise GraduationRefused(
                f"graduation gate {leg}: {ref} is a {rec.record_type!r}, "
                f"not a {expected_type}"
            )
        return rec

    def promote(
        self,
        *,
        family: str,
        claim: str,
        hypothesis_ref: str,
        verdict_ref: str,
        placebo_ref: str,
        second_lens_ref: str,
        belief_ref: str,
        producer: str = "graduation",
        event_ts: int | None = None,
    ) -> Record:
        """Promote ``(family, claim)`` iff all four gates hold; else GraduationRefused."""
        # (a) a PASS verdict, of THIS hypothesis.
        verdict = self._require_type(verdict_ref, "verdict", leg="(a) verdict")
        if verdict.payload["verdict"] != "PASS":
            raise GraduationRefused(
                f"graduation gate (a): verdict {verdict_ref} is "
                f"{verdict.payload['verdict']}, not PASS — only a PASS may promote"
            )
        if verdict.payload["hypothesis_ref"] != hypothesis_ref:
            raise GraduationRefused(
                f"graduation gate (a): verdict {verdict_ref} is of hypothesis "
                f"{verdict.payload['hypothesis_ref']}, not {hypothesis_ref}"
            )

        # (b) a placebo of the SAME hypothesis with no excess null passes.
        placebo = self._require_type(placebo_ref, "placebo_run", leg="(b) placebo")
        if placebo.payload["hypothesis_ref"] != hypothesis_ref:
            raise GraduationRefused(
                f"graduation gate (b): placebo {placebo_ref} is of hypothesis "
                f"{placebo.payload['hypothesis_ref']}, not {hypothesis_ref}"
            )
        effective_alpha = verdict.payload["corrections"]["effective_alpha"]
        ceiling = _null_pass_ceiling(placebo.payload["n_runs"], effective_alpha)
        if placebo.payload["n_pass"] > ceiling:
            raise GraduationRefused(
                f"graduation gate (b): placebo {placebo_ref} shows "
                f"{placebo.payload['n_pass']} null passes > ceiling {ceiling} at "
                f"effective_alpha={effective_alpha} — the judge is over-eager"
            )

        # (c) a second lens whose overlap_manifest resolves to a real bulk_manifest.
        lens = self._require_type(second_lens_ref, "second_lens", leg="(c) second_lens")
        self._require_type(
            lens.payload["overlap_manifest"], "bulk_manifest",
            leg="(c) second_lens.overlap_manifest",
        )

        # (d) the (family, claim) belief cites this verdict and is not CONTESTED.
        belief = self._require_type(belief_ref, "belief", leg="(d) belief")
        if belief.payload["family"] != family or belief.payload["claim"] != claim:
            raise GraduationRefused(
                f"graduation gate (d): belief {belief_ref} is for "
                f"({belief.payload['family']}, {belief.payload['claim']}), "
                f"not ({family}, {claim})"
            )
        if verdict_ref not in belief.payload["verdict_refs"]:
            raise GraduationRefused(
                f"graduation gate (d): belief {belief_ref} does not cite verdict "
                f"{verdict_ref} — the promotion's evidence must be in the belief chain"
            )
        if belief.payload["stance"] == "CONTESTED":
            raise GraduationRefused(
                f"graduation gate (d): belief {belief_ref} stance is CONTESTED — "
                "a claim with conflicting decisive verdicts may not graduate"
            )

        # All four gates hold — append the lifecycle record (beliefs untouched).
        payload = {
            "family": family,
            "claim": claim,
            "hypothesis_ref": hypothesis_ref,
            "verdict_ref": verdict_ref,
            "placebo_ref": placebo_ref,
            "second_lens_ref": second_lens_ref,
            "belief_ref": belief_ref,
        }
        return self._store.append(
            "promotion",
            payload,
            producer=producer,
            event_ts=event_ts if event_ts is not None else now_ns(),
            parents=[verdict_ref, placebo_ref, second_lens_ref, belief_ref],
            schema_version=1,
        )

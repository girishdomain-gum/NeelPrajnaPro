"""The Battery: the SOLE verdict writer (A-015 §3).

It accepts only TYPED inputs -- a registered hypothesis, a
provenance-bound ObservationSet whose hash the caller has independently
verified, and a VIRGIN window -- and refuses BEFORE it reports on any of:
an unregistered hypothesis, unverified observations, a non-VIRGIN or
already-burned window, or an alpha the given resample count cannot
possibly achieve (S05's null model refuses that one itself).

ATOMICITY (S02's lesson, reused verbatim): "judge" and "burn" are not two
steps here either. `WindowLedger.record_verdict()` writes the verdict and
consumes the window in the SAME RecordStore.append() call -- see that
method's docstring for the full argument. The Battery never burns a
window and separately writes a verdict; it calls `record_verdict()`
exactly once, with the completed verdict already computed, and that one
call is the only thing that can fail or succeed atomically.

WHAT "SOLE VERDICT WRITER" MEANS IN PRACTICE (named honestly, not
overclaimed): `WindowLedger.record_verdict()` is a public method on a
shared object; nothing in Python prevents another piece of code from
importing `WindowLedger` and calling it directly with a hand-built verdict
dict that skips every check below. What IS true, and enforced
structurally: no OTHER function in this codebase computes a p-value,
checks registration/budget/provenance, or otherwise produces a verdict
that could be passed to `record_verdict()` without going through this
class. "Sole verdict writer" is a claim about where verdicts are
COMPUTED, not an access-control boundary around the storage call -- see
the sprint report's limitations section for the same point made plainly.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from qrf.errors import UnverifiedObservations
from qrf.kernel.detection.types import ObservationSet
from qrf.kernel.null.resampling import run_null_test
from qrf.kernel.registration.ledger import TrialLedger
from qrf.kernel.windows.ledger import WindowLedger


@dataclass(frozen=True)
class Verdict:
    hypothesis_id: str
    p_value: float
    alpha: float
    significant: bool
    n_resamples: int
    seed: int
    block_length: int
    observed_statistic: float
    source_sha256: str


class Battery:
    def __init__(self, trial_ledger: TrialLedger, window_ledger: WindowLedger):
        self._trials = trial_ledger
        self._windows = window_ledger

    def judge(
        self,
        *,
        hypothesis_id: str,
        observation_set: ObservationSet,
        verified_source_sha256: str,
        series: Sequence[float],
        statistic_fn,
        observed_statistic: float,
        block_length: int,
        n_resamples: int,
        seed: int,
    ) -> Verdict:
        """Refuses, in order: unregistered hypothesis (HypothesisNotRegistered,
        from `TrialLedger.lookup`), unverified observations
        (UnverifiedObservations), an alpha this many resamples cannot
        achieve (InsufficientResamples, from the null model), or a
        non-VIRGIN / already-burned window (WindowConflict, from
        `WindowLedger.record_verdict`). Only after all of those pass does
        it run the null test and write the one atomic verdict+burn record.
        """
        registration = self._trials.lookup(hypothesis_id)

        if observation_set.source_sha256 != verified_source_sha256:
            raise UnverifiedObservations(verified_source_sha256, observation_set.source_sha256)

        null_result = run_null_test(
            series=series,
            statistic_fn=statistic_fn,
            observed_statistic=observed_statistic,
            block_length=block_length,
            n_resamples=n_resamples,
            seed=seed,
            alpha=registration.alpha,
        )

        verdict = Verdict(
            hypothesis_id=hypothesis_id,
            p_value=null_result.p_value,
            alpha=registration.alpha,
            significant=null_result.p_value < registration.alpha,
            n_resamples=null_result.n_resamples,
            seed=null_result.seed,
            block_length=null_result.block_length,
            observed_statistic=observed_statistic,
            source_sha256=observation_set.source_sha256,
        )

        self._windows.record_verdict(
            registration.window_id, hypothesis_id, verdict.__dict__
        )
        return verdict

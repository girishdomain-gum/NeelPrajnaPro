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

A-016 R1: `record_verdict()` now REQUIRES a `VerdictCapability` token
(`qrf.kernel.windows.ledger.VerdictCapability`) -- the Battery is the
only code in this project that imports that class and constructs an
instance of it. This does not make "sole verdict writer" a hard security
boundary (Python has none across modules: anyone COULD import the token
class too), but it makes the claim structural rather than incidental --
calling `record_verdict()` now requires deliberately importing and
constructing a marker built for exactly this purpose, not just happening
to have a reference to a public method. A hand-built verdict dict passed
without that token is refused by name (CapabilityRequired), drilled in
tests/kernel/battery/test_battery.py.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from qrf.errors import UnverifiedObservations
from qrf.kernel.detection.types import ObservationSet
from qrf.kernel.null.resampling import run_null_test
from qrf.kernel.registration.ledger import TrialLedger
from qrf.kernel.windows.ledger import VerdictCapability, WindowLedger


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
        self._capability = VerdictCapability()

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
            registration.window_id, hypothesis_id, verdict.__dict__, self._capability
        )
        return verdict

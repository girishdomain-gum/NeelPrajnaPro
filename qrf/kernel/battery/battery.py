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

F-11 (A-044): PLUGGABLE NULL. `judge()` used to hardwire S05's
block-resampling null internally -- discovered, by AM-07 Stage A's P2
replay, to be the WRONG null for LS-01-R001 (F-09's circular-shift null
is what the spec actually requires), meaning the one component that
writes the real verdict could not execute the real measurement's
specification. Fixed by taking a `null_runner` -- a callable of exactly
`(observed_statistic, alpha) -> NullOutcome` (see
`qrf.kernel.null.outcome.NullOutcome`) -- instead of doing the null test
itself. `qrf.kernel.null.resampling.block_resampling_null_runner` and
`qrf.kernel.measurement.circular_shift_null.circular_shift_null_runner`
both build one; Battery does not need to know, or care, which null a
caller chose -- it only needs the result to be self-describing.
NO DEFAULT: `null_runner` is required and `None` is refused by name
(NullNotSpecified) BEFORE the hypothesis lookup even runs -- a verdict
computed under an unstated null is exactly the failure this fix exists
to close, so there is no fallback to "silently preserve today's
behaviour" the way an optional parameter with a default would invite.
SELF-DESCRIBING VERDICT: `Verdict.null_name`/`Verdict.null_parameters`
replace the old `block_length` field, which meant nothing for a null
that isn't block-resampling -- a verdict now always states which null
produced it and with what parameters, so no future reader has to infer
it from context or assume it was always the same one.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from qrf.errors import NullNotSpecified, UnverifiedObservations
from qrf.kernel.detection.types import ObservationSet
from qrf.kernel.null.outcome import NullOutcome
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
    null_name: str
    null_parameters: dict
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
        observed_statistic: float,
        null_runner: Callable[[float, float], NullOutcome],
    ) -> Verdict:
        """Refuses, in order: no null_runner supplied (NullNotSpecified --
        checked first, since it is a caller-usage error independent of any
        registration state); unregistered hypothesis
        (HypothesisNotRegistered, from `TrialLedger.lookup`); unverified
        observations (UnverifiedObservations); an alpha this many
        resamples cannot achieve (InsufficientResamples, raised inside
        `null_runner` itself -- see `block_resampling_null_runner`/
        `circular_shift_null_runner`); or a non-VIRGIN / already-burned
        window (WindowConflict, from `WindowLedger.record_verdict`). Only
        after all of those pass does it call `null_runner` and write the
        one atomic verdict+burn record.
        """
        if null_runner is None:
            raise NullNotSpecified(hypothesis_id)

        registration = self._trials.lookup(hypothesis_id)

        if observation_set.source_sha256 != verified_source_sha256:
            raise UnverifiedObservations(verified_source_sha256, observation_set.source_sha256)

        outcome = null_runner(observed_statistic, registration.alpha)

        verdict = Verdict(
            hypothesis_id=hypothesis_id,
            p_value=outcome.p_value,
            alpha=registration.alpha,
            significant=outcome.p_value < registration.alpha,
            n_resamples=outcome.n_resamples,
            seed=outcome.seed,
            null_name=outcome.null_name,
            null_parameters=outcome.parameters,
            observed_statistic=observed_statistic,
            source_sha256=observation_set.source_sha256,
        )

        self._windows.record_verdict(
            registration.window_id, hypothesis_id, verdict.__dict__, self._capability
        )
        return verdict

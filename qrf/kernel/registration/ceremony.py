"""The Owner's ceremony: the machine PREPARES a complete registration and
STOPS; only a correctly typed designation phrase completes it (A-015
§4.3).

BINDING (AM-03): the phrase is never stored, never logged, never written
to any fixture or artifact -- only its sha256 hash is ever compared or
recorded. `complete_registration()` is the ONLY function in this project
that touches a plaintext phrase, and it does not return, print, or persist
it anywhere; it exists in a local variable for the span of one hash
computation and then is gone.

`expected_phrase_hash` is supplied BY THE CALLER, out of band -- this
module has and wants no opinion about what the real phrase is. The Owner
has not chosen his real phrase as of S05; this ceremony is proven here
with throwaway strings obviously not his, exactly as instructed. Nothing
here needs, stores, or infers the real phrase, ever.
"""

from __future__ import annotations

import hashlib

from qrf.errors import CeremonyRefused
from qrf.kernel.registration.ledger import Registration, TrialLedger


def complete_registration(
    ledger: TrialLedger,
    *,
    typed_phrase: str,
    expected_phrase_hash: str,
    hypothesis_id: str,
    family_id: str,
    statement_hash: str,
    detector_name: str,
    detector_version: str,
    data_span_start_utc: int,
    data_span_end_utc: int,
    window_id: str,
    thresholds_hash: str,
    capacity: int | None = None,
) -> Registration:
    """Complete a registration. Refuses (CeremonyRefused) if `typed_phrase`
    is empty or its hash does not match `expected_phrase_hash` -- in
    either case NOTHING is registered; the ledger is never touched until
    the ceremony has already passed.
    """
    if not typed_phrase:
        raise CeremonyRefused("no phrase supplied")
    actual_hash = hashlib.sha256(typed_phrase.encode("utf-8")).hexdigest()
    if actual_hash != expected_phrase_hash:
        raise CeremonyRefused("typed phrase does not match the expected designation")
    kwargs = dict(
        hypothesis_id=hypothesis_id,
        family_id=family_id,
        statement_hash=statement_hash,
        detector_name=detector_name,
        detector_version=detector_version,
        data_span_start_utc=data_span_start_utc,
        data_span_end_utc=data_span_end_utc,
        window_id=window_id,
        thresholds_hash=thresholds_hash,
        phrase_hash=actual_hash,
    )
    if capacity is not None:
        kwargs["capacity"] = capacity
    return ledger.register(**kwargs)

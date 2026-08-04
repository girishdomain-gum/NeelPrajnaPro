"""The Publication Boundary (S07, A-029 §2.3): the ONLY place a `Verdict`
(qrf.kernel.battery.battery.Verdict) is allowed to turn into something
`runtime/` can read.

WHAT CROSSES, NEVER HOW: a release states the FINDING (which hypothesis,
which measurement, whether it was significant, which direction it
implies, and a validity window for any instruction built from it) and
never the DERIVATION (p_value, alpha, n_resamples, seed, block_length,
observed_statistic). AM-04 holds at the boundary too: a release names a
MEASUREMENT id, never the concept, and never phrases anything as "the
concept is true" -- it is silent on the concept entirely.

`direction` CROSSES ONLY WHEN `significant` IS TRUE (A-030 R1). When a
release is significant, direction is part of the finding itself -- an
instruction cannot act without it, and "which way the finding points" is
a result, not a method. When a release is NOT significant, a direction
would be the sign of an effect that was never established -- a stream of
not-significant releases each still carrying a direction would leak a
point estimate one bit at a time, the same class of problem as a rolling
statistic crossing the boundary. So `direction` is REQUIRED when
`significant` is true and structurally ABSENT (not null-but-present,
the KEY ITSELF is missing) when it is false: an allow-list boundary
should make an unpublishable value impossible to represent, not merely
conventionally empty.

NO SHARED TYPE CROSSES THE WALL. `runtime/` never imports qrf.kernel (the
firewall enforces this both ways -- see tests/test_firewall.py), so a
release is a plain, canonically-serialized dict, not a shared Python
class. `runtime/types.py` independently re-implements the same
canonicalization + sealed-hash check on the consuming side -- two
independent implementations that must agree byte-for-byte, exactly the
shape of every other proof-carrying record in this project (RecordStore's
hash chain, BulkStore's manifest).

BYTE-REPRODUCIBILITY (A-029 §2.2): `sealed_hash` is a sha256 over the
release's own fields (sorted-key, separator-compact JSON, excluding
`release_id`/`sealed_hash` themselves), and `release_id` IS that hash --
same inputs produce the same release_id and the same bytes, always. There
is no non-deterministic input (no wall-clock read, no random seed) inside
this module; `valid_from`/`valid_until` are supplied by the caller, not
generated here.
"""

from __future__ import annotations

import hashlib
import json

from qrf.errors import PublicationLeak
from qrf.kernel.battery.battery import Verdict

SCHEMA_VERSION = 1

# The allow-list IS the boundary: an unrecognised key is refused exactly
# like a known-forbidden one. Adding a new field to a release requires
# deliberately adding it here, never merely not-yet-forbidding it.
# "direction" is present in this list because it MAY appear -- whether it
# MUST or MUST NOT for a given release is significant-conditional, checked
# separately (see publish()/ReleasedKnowledge.from_release_dict()).
ALLOWED_FIELDS = frozenset(
    {
        "schema_version",
        "release_id",
        "hypothesis_id",
        "measurement_id",
        "significant",
        "direction",
        "valid_from",
        "valid_until",
        "sealed_hash",
    }
)

DIRECTIONS = frozenset({"long", "short"})


def _canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def publish(
    verdict: Verdict,
    *,
    measurement_id: str,
    direction: str | None,
    valid_from: int,
    valid_until: int,
) -> dict:
    """Build a knowledge release from a REAL `Verdict` -- `verdict` must be
    an actual `Verdict` instance, refused otherwise (TypeError; this
    module is qrf-side and may use qrf types directly, unlike the
    runtime-side check which cannot). Only `verdict.significant` crosses;
    `verdict.p_value` and everything else derivation-shaped never does.

    A-030 R1: `direction` is REQUIRED (one of DIRECTIONS) when
    `verdict.significant` is True, and MUST be `None` (omitted from the
    released dict entirely, not stored as null) when it is False. Both
    violations are refused BY NAME.
    """
    if not isinstance(verdict, Verdict):
        raise TypeError(f"publish() requires a real Verdict, got {type(verdict).__name__}")
    if verdict.significant:
        if direction not in DIRECTIONS:
            raise ValueError(
                f"direction must be one of {sorted(DIRECTIONS)} for a significant "
                f"release, got {direction!r}"
            )
    elif direction is not None:
        raise ValueError(
            f"direction must be None for a not-significant release, got {direction!r}"
        )
    if not valid_from < valid_until:
        raise ValueError(
            f"valid_from must be before valid_until, got ({valid_from}, {valid_until})"
        )

    unsealed = {
        "schema_version": SCHEMA_VERSION,
        "hypothesis_id": verdict.hypothesis_id,
        "measurement_id": measurement_id,
        "significant": verdict.significant,
        "valid_from": valid_from,
        "valid_until": valid_until,
    }
    if verdict.significant:
        unsealed["direction"] = direction
    sealed_hash = hashlib.sha256(_canonical_bytes(unsealed)).hexdigest()
    release = dict(unsealed)
    release["release_id"] = sealed_hash
    release["sealed_hash"] = sealed_hash
    verify_no_leak(release)
    return release


def verify_no_leak(release: dict) -> None:
    """Refuses any key outside ALLOWED_FIELDS, by name -- the leak drill's
    checker. Runs a second time inside `publish()` itself (defense in
    depth: even a future bug in `publish()` that added a forbidden field
    cannot ship a leaking release silently), and is also the function
    tests/kernel/publication/test_release.py drills directly.

    A-030 R1, enforced here too (defense in depth): `direction` present
    on a not-significant release is itself a leak -- the sign of an
    effect that was never established, crossing anyway.
    """
    leaked = set(release) - ALLOWED_FIELDS
    if leaked:
        raise PublicationLeak(sorted(leaked)[0])
    if "significant" in release and "direction" in release and not release["significant"]:
        raise PublicationLeak("direction")


def recompute_sealed_hash(release: dict) -> str:
    """Independently recompute the sealed hash from a release's own
    fields, for the consuming side (`runtime/types.py`) to verify against
    without importing anything qrf-side. Excludes `release_id`/
    `sealed_hash` themselves, mirroring `publish()`'s own construction.
    """
    unsealed = {k: v for k, v in release.items() if k not in ("release_id", "sealed_hash")}
    return hashlib.sha256(_canonical_bytes(unsealed)).hexdigest()

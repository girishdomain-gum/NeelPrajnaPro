"""`ReleasedKnowledge`: runtime/'s OWN typed representation of a knowledge
release. Independently re-implements the canonicalization + sealed-hash
check that `qrf/kernel/publication/release.py` performs on the other
side of the wall -- two independent implementations that must agree
byte-for-byte, because no shared Python type is allowed to cross (the
firewall bans `runtime/` from importing qrf.kernel, and this project
does not weaken that ban for convenience).

`from_release_dict()` is the ONLY way to construct a `ReleasedKnowledge`
outside a test -- it validates structure (required fields, types, a
recognised direction) AND recomputes the sealed hash independently,
refusing (`MalformedRelease`) if the recomputed hash disagrees with the
one the dict claims. This is what makes `Belief.update()` requiring a
`ReleasedKnowledge` instance more than a formality: you cannot build one
except by passing this check first.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from runtime.errors import MalformedRelease

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
DIRECTIONS = frozenset({"long", "short", "none"})


def _canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _recompute_sealed_hash(release: dict) -> str:
    unsealed = {k: v for k, v in release.items() if k not in ("release_id", "sealed_hash")}
    return hashlib.sha256(_canonical_bytes(unsealed)).hexdigest()


@dataclass(frozen=True)
class ReleasedKnowledge:
    schema_version: int
    release_id: str
    hypothesis_id: str
    measurement_id: str
    significant: bool
    direction: str
    valid_from: int
    valid_until: int
    sealed_hash: str

    @staticmethod
    def from_release_dict(release: dict) -> ReleasedKnowledge:
        if not isinstance(release, dict):
            raise MalformedRelease("not a dict", type(release).__name__)

        extra = set(release) - ALLOWED_FIELDS
        if extra:
            raise MalformedRelease("unrecognised field(s)", sorted(extra))
        missing = ALLOWED_FIELDS - set(release)
        if missing:
            raise MalformedRelease("missing required field(s)", sorted(missing))

        if release["direction"] not in DIRECTIONS:
            raise MalformedRelease("direction not recognised", release["direction"])
        if not isinstance(release["significant"], bool):
            raise MalformedRelease("significant must be bool", release["significant"])
        for field in ("valid_from", "valid_until"):
            value = release[field]
            if isinstance(value, bool) or not isinstance(value, int):
                raise MalformedRelease(f"{field} must be an int epoch second", value)
        if not release["valid_from"] < release["valid_until"]:
            raise MalformedRelease(
                "valid_from must precede valid_until",
                (release["valid_from"], release["valid_until"]),
            )

        expected_hash = _recompute_sealed_hash(release)
        if release["sealed_hash"] != expected_hash:
            raise MalformedRelease(
                "sealed_hash does not match recomputed hash",
                (release["sealed_hash"], expected_hash),
            )
        if release["release_id"] != release["sealed_hash"]:
            raise MalformedRelease(
                "release_id must equal sealed_hash",
                (release["release_id"], release["sealed_hash"]),
            )

        return ReleasedKnowledge(**release)

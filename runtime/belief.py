"""Belief: runtime/'s only entry point for updating what the runtime
organ knows (A-029 §2.1). `update()` requires an actual `ReleasedKnowledge`
instance -- a raw dict, a hand-built object with the right attributes, or
anything else duck-typed is refused BY NAME (`UntypedInput`), never
silently accepted because it "looks right". Since `ReleasedKnowledge` can
only be constructed via `from_release_dict()`'s validation + sealed-hash
check (see runtime/types.py), requiring the type is not just a formality
-- it is requiring the check to have already passed.

State is a simple per-hypothesis latest-known-release map. Belief never
interprets a release beyond storing it -- no aggregation across releases,
no "the concept is true" inference (AM-04 holds at every layer, not just
at publish time).
"""

from __future__ import annotations

from runtime.errors import UntypedInput
from runtime.types import ReleasedKnowledge


class Belief:
    def __init__(self) -> None:
        self._by_hypothesis: dict[str, ReleasedKnowledge] = {}

    def update(self, release: ReleasedKnowledge) -> None:
        if not isinstance(release, ReleasedKnowledge):
            raise UntypedInput("Belief.update", release)
        self._by_hypothesis[release.hypothesis_id] = release

    def latest(self, hypothesis_id: str) -> ReleasedKnowledge | None:
        return self._by_hypothesis.get(hypothesis_id)

    def known_hypotheses(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_hypothesis))

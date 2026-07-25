"""Deterministic run-seed derivation (Blueprint §4.7 step 4).

The battery derives a seed from a run's identity — ``seeds.for_run(hypothesis_ref,
window_ref)`` — records it in the verdict, and hands it to the simulator so a run
is reproducible from its two anchors alone. The engine itself carries no RNG this
sprint (its trades are a deterministic function of bars + events + execution +
cost model), so the seed is a provenance stamp and the anchor for any future
stochastic step (block bootstrap, §4.7 step 6); the recipe here is the single
source of that integer.

Recipe (normative — reproduce it exactly to audit a seed):

    body   = canonical_bytes({"hypothesis_ref": <str>, "window_ref": <str>})
    digest = sha256(body)                      # 32 bytes
    seed   = int.from_bytes(digest[:8], "big") & (2**63 - 1)

``canonical_bytes`` is the Blueprint §1.3 serialization (sorted keys, compact
separators, UTF-8) — the same function the ledger hashes records with — so the
seed is stable across machines and Python builds. Masking to 63 bits keeps the
value a non-negative signed 64-bit integer, safe for numpy / stdlib RNG seeding
and for canonical JSON (no unsigned-overflow surprises).

This module is kernel: it is domain-blind (both anchors are opaque record-id
strings) and depends only on the records layer + hashlib.
"""

from __future__ import annotations

import hashlib

from qrf.kernel.records.record import canonical_bytes

# Mask to a non-negative signed 63-bit integer (see module docstring).
_SEED_MASK = (1 << 63) - 1


def for_run(hypothesis_ref: str, window_ref: str) -> int:
    """Derive the deterministic run seed for ``(hypothesis_ref, window_ref)``.

    Both anchors are record-id strings. Identical anchors always yield the same
    seed; changing either anchor changes the seed. Raises :class:`TypeError`-free
    ``ValueError`` on a non-string / empty anchor so a caller cannot silently seed
    a run off a missing reference.
    """
    if not isinstance(hypothesis_ref, str) or not hypothesis_ref:
        raise ValueError("hypothesis_ref must be a non-empty string")
    if not isinstance(window_ref, str) or not window_ref:
        raise ValueError("window_ref must be a non-empty string")
    body = canonical_bytes({"hypothesis_ref": hypothesis_ref, "window_ref": window_ref})
    digest = hashlib.sha256(body).digest()
    return int.from_bytes(digest[:8], "big") & _SEED_MASK

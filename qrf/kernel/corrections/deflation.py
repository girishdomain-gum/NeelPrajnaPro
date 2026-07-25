"""Multiple-testing deflation — the penalty that makes trial counting BITE.

Implementation Blueprint v1.0 §4.8, ARCH-006 §2. A hypothesis is judged not at
its face alpha but at an alpha *deflated* by how many trials were spent reaching
it. The rule this sprint is deliberately the simplest conservative one — a
Bonferroni correction against the honest trial ledger:

    effective_alpha = base_alpha / max(1, N_trials)

where ``N_trials = TrialCountLedger.total(scope, lineage)`` read AT JUDGING TIME
(ARCH-006 §2). ``max(1, N)`` keeps a hypothesis with zero recorded trials at its
face alpha (never *inflating* it) and makes every recorded trial shrink the bar
the evidence must clear. Refinements (Benjamini-Hochberg FDR, deflated Sharpe)
arrive only via a future DEVQ/ADR — not silently.

The verdict records ``base_alpha``, ``N_trials`` and ``effective_alpha`` so the
correction is reconstructable from the ledger alone (IVF recomputes it).

This module is kernel: it reads the trial ledger through the records layer and
speaks only ``scope`` / ``lineage`` / ``base_alpha`` — no trading vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass

from qrf.kernel.corrections.trials import TrialCountLedger
from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records.store import RecordStore

METHOD = "bonferroni"


@dataclass(frozen=True, slots=True)
class Deflation:
    """The audit-complete result of a deflation: every input and the output."""

    base_alpha: float
    n_trials: int
    effective_alpha: float
    method: str = METHOD


def effective_alpha(base_alpha: float, scope: str, lineage: str, store: RecordStore) -> float:
    """Return ``base_alpha / max(1, N_trials)`` for ``(scope, lineage)`` (ARCH-006 §2).

    ``N_trials`` is ``TrialCountLedger.total(scope, lineage)`` at call time. The
    named contract of the module — the battery uses :func:`deflate` for the full
    audit record, the unit tests pin this exact number against hand arithmetic.
    """
    return deflate(base_alpha, scope, lineage, store).effective_alpha


def deflate(base_alpha: float, scope: str, lineage: str, store: RecordStore) -> Deflation:
    """The full deflation: read the ledger, apply Bonferroni, return every field.

    Raises :class:`SchemaViolation` on a non-positive / out-of-range base alpha so
    a caller cannot deflate against a nonsensical face rate.
    """
    if not isinstance(base_alpha, (int, float)) or isinstance(base_alpha, bool):
        raise SchemaViolation("base_alpha must be a number")
    if not 0.0 < float(base_alpha) < 1.0:
        raise SchemaViolation(f"base_alpha must be in (0, 1), got {base_alpha}")

    n_trials = TrialCountLedger(store).total(scope, lineage)
    eff = float(base_alpha) / max(1, n_trials)
    return Deflation(base_alpha=float(base_alpha), n_trials=int(n_trials), effective_alpha=eff)

"""Multiple-testing deflation — the penalty that makes trial counting BITE.

Implementation Blueprint v1.0 §4.8, ARCH-006 §2. A hypothesis is judged not at
its face alpha but at an alpha *deflated* by how many trials were spent reaching
it. The rule this sprint is deliberately the simplest conservative one — a
Bonferroni correction against the honest trial ledger:

    effective_alpha = base_alpha / max(1, N_trials)

``max(1, N)`` keeps a hypothesis with zero recorded trials at its face alpha
(never *inflating* it) and makes every recorded trial shrink the bar the evidence
must clear. Refinements (Benjamini-Hochberg FDR, deflated Sharpe) arrive only via
a future DEVQ/ADR — not silently.

The GOVERNING rule (DEVQ-015): the multiplicity burden accrues to the CLAIM's
``{market}/{instrument_family}`` — its ``family`` — not to a window or a single
lineage (which dataset slice a search touched is irrelevant to how many things
were tried). :func:`deflate_family` totals every ``trial_count`` that belongs to
the family, capturing legacy lineage-keyed records by prefix WITHOUT re-keying
them (the ledger is append-only). :func:`deflate` is the retired ``(scope,
lineage)`` rule, kept only for v1 hypotheses sealed under it (e.g. H-001).

The verdict records ``base_alpha``, ``N_trials`` (``family_m``), ``effective_alpha``
and the ``family`` so the correction is reconstructable from the ledger alone
(IVF recomputes it).

This module is kernel: it reads the trial ledger through the records layer and
speaks only ``scope`` / ``lineage`` / ``family`` / ``base_alpha`` — no trading
vocabulary.
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
    family: str | None = None  # the {market}/{instrument_family} totalled over (v2)


def _is_prefix_segment(prefix: str, full: str) -> bool:
    """True iff ``prefix`` is a leading dotted/slashed segment of ``full``.

    ``smc.fvg`` is a prefix segment of ``smc.fvg.screen.s4`` and of
    ``smc.fvg/anything`` but NOT of ``smc.fvghost`` — the boundary must fall on a
    ``.`` or ``/`` separator so ``smc.fvg`` never swallows an unrelated family.
    """
    return full == prefix or full.startswith(prefix + ".") or full.startswith(prefix + "/")


def _trial_belongs_to_family(family: str, tc_payload: dict) -> bool:
    """Whether a ``trial_count`` record counts toward ``family`` (DEVQ-015 ruling).

    A trial counts if EITHER its declared ``family`` matches (exact or one is a
    prefix segment of the other) OR the family's instrument-family segment is a
    prefix of the trial's ``lineage``. The second clause captures LEGACY records
    keyed only by lineage (e.g. ``smc.fvg.screen.s4``) without re-keying them —
    the ledger is append-only. Cross-market over-capture of a legacy record is a
    CONSERVATIVE error (it only lowers alpha); records written under the family
    convention isolate by market via the ``{market}/`` prefix.
    """
    declared = tc_payload.get("family")
    if declared is not None and (
        declared == family
        or _is_prefix_segment(declared, family)
        or _is_prefix_segment(family, declared)
    ):
        return True
    inst_family = family.rsplit("/", 1)[-1]
    return _is_prefix_segment(inst_family, tc_payload["lineage"])


def family_trials(family: str, store: RecordStore) -> int:
    """Sum ``n_attempts`` over every ``trial_count`` that belongs to ``family``.

    Monotone by construction (the store has no delete/update surface). This is the
    multiplicity burden a claim carries: how many things were tried in its
    (market, instrument-family), regardless of which data slice the search touched.
    """
    return sum(
        rec.payload["n_attempts"]
        for rec in store.query(record_type="trial_count")
        if _trial_belongs_to_family(family, rec.payload)
    )


def deflate_family(base_alpha: float, family: str, store: RecordStore) -> Deflation:
    """Deflate ``base_alpha`` by the trial burden of ``family`` (DEVQ-015 ruling).

    ``effective_alpha = base_alpha / max(1, family_trials(family))``. Corrections
    follow CLAIMS: the burden accrues to the ``{market}/{instrument_family}``, not
    to a window or a single lineage. Raises :class:`SchemaViolation` on a
    non-positive / out-of-range base alpha or an empty family.
    """
    _require_base_alpha(base_alpha)
    if not isinstance(family, str) or not family.strip():
        raise SchemaViolation("family must be a non-empty string")
    n_trials = family_trials(family, store)
    eff = float(base_alpha) / max(1, n_trials)
    return Deflation(
        base_alpha=float(base_alpha),
        n_trials=int(n_trials),
        effective_alpha=eff,
        family=family,
    )


def _require_base_alpha(base_alpha: float) -> None:
    if not isinstance(base_alpha, (int, float)) or isinstance(base_alpha, bool):
        raise SchemaViolation("base_alpha must be a number")
    if not 0.0 < float(base_alpha) < 1.0:
        raise SchemaViolation(f"base_alpha must be in (0, 1), got {base_alpha}")


def effective_alpha(base_alpha: float, scope: str, lineage: str, store: RecordStore) -> float:
    """Return ``base_alpha / max(1, N_trials)`` for a LEGACY ``(scope, lineage)`` key.

    Retained for v1 hypotheses (e.g. H-001, whose sealed verdict used this rule).
    The GOVERNING rule since DEVQ-015 is :func:`deflate_family` — multiplicity
    accrues to the claim's family, not to a window or a single lineage.
    """
    return deflate(base_alpha, scope, lineage, store).effective_alpha


def deflate(base_alpha: float, scope: str, lineage: str, store: RecordStore) -> Deflation:
    """LEGACY exact ``(scope, lineage)`` deflation (v1 hypotheses only).

    Superseded by :func:`deflate_family` (DEVQ-015). Kept so a v1 hypothesis
    record deflates by the rule it was registered under. Raises
    :class:`SchemaViolation` on a non-positive / out-of-range base alpha.
    """
    _require_base_alpha(base_alpha)
    n_trials = TrialCountLedger(store).total(scope, lineage)
    eff = float(base_alpha) / max(1, n_trials)
    return Deflation(base_alpha=float(base_alpha), n_trials=int(n_trials), effective_alpha=eff)

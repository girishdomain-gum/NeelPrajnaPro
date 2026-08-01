"""Epistemic lineage — the zero-epistemic-weight gate for retired NPSU data.

Architecture B.1 (binding): the bespoke NPSU stack's data may migrate as
records (WO-07) but carries ZERO epistemic weight, forever — no verdict,
burn, trial-count, or belief update may ever trace to it. This module makes
that MECHANICAL (a code-level type-gate every closed-write-authority
function calls), not procedural (a convention someone could forget).

``TAINTED_TYPES`` are the two record types WO-07's migration writes
(``npsu_legacy_import_trade`` / ``npsu_legacy_import_shadow``, schemas.py).
A record is "tainted" iff: it IS one of those types; OR it carries
``meta["epistemic_lineage"] == "tainted"`` (the append-time flag,
A-020/D-019(d)-ii — computed ONCE by the appending code via
:func:`append_with_lineage`, O(1) to check thereafter); OR any of its OWN
DIRECT parents is a tainted TYPE (a one-hop safety net catching a caller
that referenced tainted data directly without using
:func:`append_with_lineage` — the flag alone must never be the only guard).

This is NOT a blanket "missing flag = refuse": a record with NO tainted
ancestry and no flag at all (every record in this ledger before WO-07, and
any future record with genuinely no NPSU connection) is CLEAN, correctly —
the fail-safe applies to the NPSU boundary specifically, not to the whole
ledger's history, which would refuse every pre-existing verdict/burn/trial/
belief in the repo.

Kernel module: records layer + error taxonomy + stdlib only.
"""

from __future__ import annotations

from qrf.kernel.errors import EpistemicTaintError, UnknownRecordError
from qrf.kernel.records.record import Record, now_ns
from qrf.kernel.records.store import RecordStore

TAINTED_TYPES = frozenset({"npsu_legacy_import_trade", "npsu_legacy_import_shadow"})


def is_tainted(store: RecordStore, record_id: str) -> bool:
    """True iff ``record_id`` is, carries the flag for, or directly parents
    from, zero-epistemic-weight NPSU data (Architecture B.1)."""
    rec = store.get(record_id)
    if rec.record_type in TAINTED_TYPES:
        return True
    if rec.meta.get("epistemic_lineage") == "tainted":
        return True
    for pid in rec.parents:
        try:
            parent = store.get(pid)
        except UnknownRecordError:
            continue
        if parent.record_type in TAINTED_TYPES:
            return True
    return False


def compute_epistemic_lineage(store: RecordStore, parents: list[str] | tuple[str, ...]) -> str:
    """``"tainted"`` if any of ``parents`` is tainted (by :func:`is_tainted`),
    else ``"clean"`` — computed ONCE at append time; the caller's own record
    then carries this as its cached ``meta["epistemic_lineage"]``, so a LATER
    check of a record built from THIS one needs only the one-hop check in
    :func:`is_tainted`, never a full history walk (the O(1)-thereafter
    property, A-020(d)(ii))."""
    for pid in parents:
        if is_tainted(store, pid):
            return "tainted"
    return "clean"


def append_with_lineage(
    store: RecordStore,
    record_type: str,
    payload: dict,
    *,
    parents: list[str] | tuple[str, ...],
    producer: str,
    event_ts: int | None = None,
    meta: dict | None = None,
    **kwargs,
) -> Record:
    """``store.append`` with ``meta["epistemic_lineage"]`` computed from
    ``parents`` and stamped in. Any future code building a record from
    inputs that MIGHT trace to NPSU data should append through here, not
    ``store.append`` directly, so the flag stays accurate going forward."""
    m = dict(meta or {})
    m["epistemic_lineage"] = compute_epistemic_lineage(store, parents)
    return store.append(
        record_type,
        payload,
        parents=list(parents),
        producer=producer,
        event_ts=event_ts if event_ts is not None else now_ns(),
        meta=m,
        **kwargs,
    )


def refuse_if_tainted(store: RecordStore, record_id: str, *, context: str) -> None:
    """Raise :class:`EpistemicTaintError` if ``record_id`` is tainted.

    ``context`` names the calling gate (e.g. ``"WindowLedger.burn"``) so the
    refusal is traceable to which closed-write-authority function fired it.
    """
    if is_tainted(store, record_id):
        raise EpistemicTaintError(
            f"{context}: record {record_id} carries zero-epistemic-weight NPSU "
            "lineage (Architecture B.1) — refused, no verdict/burn/trial/belief "
            "may ever trace to retired NPSU data"
        )

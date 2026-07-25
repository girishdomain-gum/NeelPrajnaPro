"""Observatory — systematic anomaly scanning that asks questions, never judges.

Implementation Blueprint v1.0 §4.8 / §5 arrow 6, ARCH-007 §1-§2. The observatory
sweeps TRAINING / EXPLORATION data looking for structure worth a hypothesis. It
is a telescope, not a court: a scan records WHAT was looked at and WHAT was seen
(``anomaly_scan``) and may raise zero or more ``question`` records, but it carries
no thresholds, decides no verdict, and burns no window.

Two invariants make the observatory safe:

* **No VIRGIN read.** Every scan's first act is :meth:`WindowLedger.guard_observatory`
  on its window — a VIRGIN designation raises :class:`ContaminationError` before any
  data is touched. The out-of-sample reserve is spent only by a pre-registered
  battery run, never by looking.
* **Looking is a burden.** DEVQ-015 established that multiplicity accrues to a
  CLAIM's ``{market}/{instrument_family}`` — and it applies to *looking*, not only
  to screening. So every scan bumps the trial ledger for its declared ``family``:
  the searches an analyst runs before writing a hypothesis deflate that
  hypothesis's alpha exactly as a screener grid does.

The observatory is DOMAIN-BLIND. It never computes a follow-through, a gap, or any
price statistic — the caller (a trading-side scan) computes the descriptive
``findings`` summary and hands it in, exactly as the battery takes an injected
simulator. This module speaks ``family`` / ``window`` / ``scan`` / ``question`` and
no trading word (firewall-clean).

This module is kernel: it imports the records layer, the window/trial ledgers and
the error taxonomy only.
"""

from __future__ import annotations

from qrf.kernel.corrections.trials import TrialCountLedger
from qrf.kernel.errors import SchemaViolation
from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.record import Record, now_ns
from qrf.kernel.records.store import RecordStore


class Observatory:
    """Scan TRAINING/EXPLORATION windows and raise questions (Blueprint §4.8)."""

    def __init__(self, store: RecordStore) -> None:
        self._store = store
        self._windows = WindowLedger(store)
        self._trials = TrialCountLedger(store)

    # -- scan -----------------------------------------------------------------
    def scan(
        self,
        *,
        family: str,
        window_ref: str,
        manifest_refs: list[str] | tuple[str, ...],
        method: str,
        seed: int,
        findings: dict,
        n_searched: int = 1,
        source: str = "human",
        producer: str = "observatory",
        event_ts: int | None = None,
    ) -> Record:
        """Record one anomaly scan over ``window_ref`` and bump its family's trials.

        Refuses a VIRGIN window (:class:`ContaminationError`) before anything else.
        ``findings`` is the descriptive summary the caller computed (the kernel does
        not look at data); ``method`` names the scan procedure; ``seed`` is recorded
        so a re-run is reproducible; ``n_searched`` (>= 1) is how many things the
        scan examined — the count bumped into the trial ledger for ``family`` so the
        search burden deflates future hypotheses of that family (DEVQ-015).

        Appends the ``anomaly_scan`` record (parent = window + manifests), then a
        ``trial_count`` for the family (parent = window + this scan, so the burden
        points at its cause). Returns the scan record.
        """
        # No VIRGIN read — the very first act (ContaminationError on VIRGIN).
        self._windows.guard_observatory(window_ref)

        manifest_refs = list(manifest_refs)
        if not manifest_refs:
            raise SchemaViolation("anomaly_scan requires at least one manifest_ref")
        for ref in manifest_refs:
            rec = self._store.get(ref)  # UnknownRecordError if absent
            if rec.record_type != "bulk_manifest":
                raise SchemaViolation(
                    f"anomaly_scan manifest_ref {ref} is a {rec.record_type!r}, "
                    "not a bulk_manifest"
                )

        ts = event_ts if event_ts is not None else now_ns()
        payload = {
            "family": family,
            "window_ref": window_ref,
            "manifest_refs": manifest_refs,
            "method": method,
            "seed": int(seed),
            "findings": dict(findings),
            "n_searched": int(n_searched),
        }
        scan_rec = self._store.append(
            "anomaly_scan",
            payload,
            producer=producer,
            event_ts=ts,
            parents=[window_ref, *manifest_refs],
        )
        # Looking is a burden: bump the family's trial count (DEVQ-015 applies to
        # looking, not only screening). The bump points at the scan that incurred it.
        self._trials.bump(
            window_ref,
            f"{family}.scan",
            int(n_searched),
            source,
            family=family,
            parents=[window_ref, scan_rec.record_id],
            producer=producer,
            event_ts=ts,
        )
        return scan_rec

    # -- pose a question ------------------------------------------------------
    def pose_question(
        self,
        *,
        scan_ref: str,
        observation: str,
        data_slice_refs: list[str] | tuple[str, ...],
        candidate_hypothesis: str,
        evidence_refs: list[str] | tuple[str, ...],
        origin: str = "observatory",
        priority_score: float | None = None,
        producer: str = "observatory",
        event_ts: int | None = None,
    ) -> Record:
        """Raise a ``question`` from a scan — an observation, not a hypothesis.

        Parented to ``scan_ref`` (which must be an ``anomaly_scan``). The question
        carries the ``observation`` in plain words, the ``data_slice_refs`` and
        ``evidence_refs`` behind it, and a ``candidate_hypothesis`` SKETCH — never a
        threshold, a verdict, or a burn. The schema's closed key set is the
        type-audit: a question payload structurally cannot carry those fields, so a
        question can pre-register nothing and spend no window.
        """
        scan = self._store.get(scan_ref)  # UnknownRecordError if absent
        if scan.record_type != "anomaly_scan":
            raise SchemaViolation(
                f"question scan_ref {scan_ref} is a {scan.record_type!r}, not an anomaly_scan"
            )
        payload: dict = {
            "observation": observation,
            "data_slice_refs": list(data_slice_refs),
            "candidate_hypothesis": candidate_hypothesis,
            "evidence_refs": list(evidence_refs),
            "origin": origin,
        }
        if priority_score is not None:
            payload["priority_score"] = priority_score
        return self._store.append(
            "question",
            payload,
            producer=producer,
            event_ts=event_ts if event_ts is not None else now_ns(),
            parents=[scan_ref],
        )

"""WO-08 (S5, spec ratified A-013, rescoped A-016) — WindowLedger INTERNAL
consistency + burn-accounting checker.

The premise this replaces: WO-08 was originally scoped against a
``windows.json`` file that turned out never to exist (D-013 research,
confirmed again here) — the WindowLedger persists only into the journal
(record types ``window`` / ``window_burn``, ``qrf.kernel.protocol.windows``).
This checker verifies the ledger is internally honest on its own terms,
independent of and in addition to ``WindowLedger.check_available``'s
runtime refusal (this is the AUDIT of that guarantee, not a duplicate of
it): a standalone read of the real journal should never disagree with what
the guard would have refused, and a malformed record should never exist
undetected.

Four RED classes (A-016's rescoping, ROADMAP.md P2 VALIDATION, exact):
  1. ORPHAN_BURN       — a window_burn references a window_ref that does
                          not exist in the journal.
  2. MALFORMED_SPAN     — a window's [ts_start, ts_end) is not a well-formed
                          half-open interval (non-int, or ts_start >= ts_end).
  3. OVERLAPPING_BURNS  — two window_burn records share a (dataset, lineage)
                          pair whose windows' intervals intersect — the same
                          out-of-sample reuse WindowLedger.check_available
                          exists to refuse, found here as an auditor of that
                          promise, not a re-implementation of it.
  4. RESERVE_MISMATCH   — a VIRGIN-designated window has been burned. VIRGIN
                          is the reserve-by-market-time doctrine's protected
                          pool (Constitution §6, permanently-human unlock);
                          no code path burns one by ordinary judging.

GREEN prints the counts compared (windows, burns, VIRGIN windows) so a clean
result is visibly non-vacuous, never a silent "nothing to report."

Run:  .venv/Scripts/python.exe scripts/check_window_ledger.py [journal_path]
      (defaults to datastore/journal/journal.jsonl)
"""

from __future__ import annotations

import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"


def _intervals_intersect(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    """Same half-open convention as qrf.kernel.protocol.windows._intervals_intersect."""
    return a_start < b_end and b_start < a_end


@dataclass
class CheckReport:
    n_windows: int = 0
    n_burns: int = 0
    n_virgin: int = 0
    findings: list[str] = field(default_factory=list)

    @property
    def is_green(self) -> bool:
        return not self.findings


def check_window_ledger(store: RecordStore) -> CheckReport:
    """Read-only audit of every ``window``/``window_burn`` record in ``store``.

    Never writes anything. Findings are returned, never raised — the caller
    (main(), or a test) decides how loudly to fail.
    """
    windows = {r.record_id: r for r in store.query(record_type="window")}
    burns = list(store.query(record_type="window_burn"))
    report = CheckReport(n_windows=len(windows), n_burns=len(burns))
    report.n_virgin = sum(1 for w in windows.values() if w.payload.get("designation") == "VIRGIN")

    # 1. MALFORMED_SPAN — checked on every window regardless of whether it is
    #    ever referenced by a burn (a malformed window is a defect on its own).
    for wid, w in windows.items():
        ts_start = w.payload.get("ts_start")
        ts_end = w.payload.get("ts_end")
        malformed = (
            not isinstance(ts_start, int)
            or isinstance(ts_start, bool)
            or not isinstance(ts_end, int)
            or isinstance(ts_end, bool)
            or ts_start >= ts_end
        )
        if malformed:
            report.findings.append(
                f"MALFORMED_SPAN: window {wid} has ts_start={ts_start!r} ts_end={ts_end!r} "
                "(must be int, ts_start < ts_end)"
            )

    # 2. ORPHAN_BURN
    valid_burns: list = []  # burns whose window_ref resolves, for the checks below
    for b in burns:
        wref = b.payload.get("window_ref")
        if wref not in windows:
            report.findings.append(
                f"ORPHAN_BURN: window_burn {b.record_id} references window_ref "
                f"{wref!r}, which does not exist as a window record"
            )
            continue
        valid_burns.append(b)

    # 3. OVERLAPPING_BURNS — same (dataset, lineage), intersecting intervals.
    by_key: dict[tuple[str, str], list] = defaultdict(list)
    for b in valid_burns:
        w = windows[b.payload["window_ref"]]
        key = (w.payload["dataset"], b.payload["lineage"])
        by_key[key].append((b, w))
    for (dataset, lineage), items in by_key.items():
        for i in range(len(items)):
            b1, w1 = items[i]
            for j in range(i + 1, len(items)):
                b2, w2 = items[j]
                if _intervals_intersect(
                    w1.payload["ts_start"], w1.payload["ts_end"],
                    w2.payload["ts_start"], w2.payload["ts_end"],
                ):
                    r1, r2 = b1.payload["window_ref"], b2.payload["window_ref"]
                    span1 = f"[{w1.payload['ts_start']},{w1.payload['ts_end']})"
                    span2 = f"[{w2.payload['ts_start']},{w2.payload['ts_end']})"
                    report.findings.append(
                        f"OVERLAPPING_BURNS: {b1.record_id} and {b2.record_id} both burn "
                        f"dataset={dataset!r} lineage={lineage!r} with intersecting windows "
                        f"{r1} {span1} and {r2} {span2}"
                    )

    # 4. RESERVE_MISMATCH — a VIRGIN window burned.
    for b in valid_burns:
        w = windows[b.payload["window_ref"]]
        if w.payload.get("designation") == "VIRGIN":
            report.findings.append(
                f"RESERVE_MISMATCH: window_burn {b.record_id} burns VIRGIN window "
                f"{b.payload['window_ref']} — the reserve-by-market-time pool must "
                "never be consumed by ordinary judging"
            )

    return report


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(JOURNAL)
    store = RecordStore(path)  # verifies the hash chain on open
    report = check_window_ledger(store)
    print(
        f"windows={report.n_windows} burns={report.n_burns} "
        f"virgin_windows={report.n_virgin}"
    )
    if report.is_green:
        print("GREEN — no findings")
        return
    print(f"RED — {len(report.findings)} finding(s):")
    for f in report.findings:
        print(f"  {f}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()

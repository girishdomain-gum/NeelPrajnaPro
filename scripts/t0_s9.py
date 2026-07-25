"""ARCH-009 T0 — chain Sprint 9 to the record.

Appends the GO-S8 ``note`` record (Owner decision GO, the verbatim Owner phrase,
the Family Wave 1 hypothesis / placebo / verdict / burn / belief ids ratified at
GO-S8), parented on the GO-S7 note that Sprint 8's own T0 laid down. This is the
sprint's first commit: every sprint begins by writing the previous sprint's close
into the append-only memory, so the ledger itself carries the sprint boundary. The
note also refs this sprint's instruction (ARCH-009) — sprint 9 open.

Idempotent: if the GO-S8 note is already present it refuses to append a second.

    F:/QRF/.venv/Scripts/python.exe scripts/t0_s9.py
"""

from __future__ import annotations

import time

from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"

# The GO-S7 note laid down by Sprint 8's T0 — this sprint's chain parent.
GO_S7_NOTE = "01KYCNVX45TCMS16D22T2NEP3H"

GO_S8_NOTE_TEXT = (
    "Sprint 8 (Graduation + Placebo + Family Wave 1) signed off by Owner: "
    "'GO. I agree with closing Sprint 8.' GO-S8: decision GO (AC 786 tests + "
    "ruff clean + firewall GREEN + journal 54 chain GREEN; VC "
    "check_s8_graduation_placebo rev1 GREEN zero amber — both verdicts "
    "re-derived end to end from an independent event universe (1170 FVGs / "
    "25 weekend-born / 52 Monday markers) and independent judge, all 40 "
    "placebo nulls regenerated from recorded seeds and re-judged to exact "
    "sequence equality, 0 weekend leaks / 0 promotions / 0 second_lens "
    "[the designed state]; drill CAUGHT x3 [hidden pass, seed swap, "
    "fabricated promotion citing FAIL + nonexistent lens] + clean control "
    "non-red; HC 8/8 MATCH gen-4 label-driven tool). Family Wave 1: "
    "H-002 01KYCQBGW3C1M9ARZ1Y320WXW4 + H-003 01KYCQBHTPAFQX3DZHJE2BEK28; "
    "placebos 01KYCQBHMFK24B65JW4Y3BQJMR (direction_permutation 0/20) + "
    "01KYCQBJ3Z272XDF96BXGH0N41 (entry_time_shuffle 6/20, over the "
    "promotion ceiling of 3); verdicts 01KYCQBHRJHY1A1PY1PQ01TAT5 (FAIL "
    "n=637 @ alpha~1e-4) + 01KYCQBJ7N2D99N7CDKQ1V4J1K (INSUFFICIENT "
    "n=28<40), burns 01KYCQBHS6T92G5PHDVE6X01DS + 01KYCQBJ8APY08BQBZF8P2VDNQ; "
    "beliefs 01KYCQBHSWWW50DKGCHATQ4C67 (REJECTED 0.8624) + "
    "01KYCQBJ8Z7CAB2K26SRKK0KVH (UNTESTED 0.0). Contracts ratified: "
    "DEVQ-018 (+placebo_method-in-YAML addendum) / DEVQ-019 (+real-feed "
    "geometry standing rule) / DEVQ-020 (second_lens schema; threshold "
    "pre-registered BEFORE overlap) / DEVQ-021 (vendored smc-toolkit). "
    "Journal 54 records, chain GREEN; VIRGIN untouched. S9 open per "
    "ARCH-009 (second lens + rebuild + honesty enforcement): the second "
    "eye that gate (c) was built to demand. S9 T0."
)


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies the chain on open

    for n in store.query(record_type="note"):
        if n.payload["text"].startswith("Sprint 8 (Graduation + Placebo + Family Wave 1) signed off"):
            print(f"GO-S8 note already present ({n.record_id}) — T0 is idempotent, nothing to do.")
            return

    if GO_S7_NOTE not in {r.record_id for r in store.query()}:
        raise SystemExit(
            f"chain parent {GO_S7_NOTE} (GO-S7 note) not found in the journal; "
            "refusing to append an unparented S9 T0"
        )

    rec = store.append(
        "note",
        {"text": GO_S8_NOTE_TEXT},
        producer="human:girish",
        event_ts=time.time_ns(),
        parents=[GO_S7_NOTE],
    )
    report = store.verify()
    print(f"S9 T0 appended GO-S8 note {rec.record_id}")
    print(f"  parents = {list(rec.parents)}")
    print(
        f"journal verify ok={report.ok} n_records={report.n_records} "
        f"head={report.head_hash[:12]}"
    )


if __name__ == "__main__":
    main()

"""ARCH-009 §4.2 — declare the 2025-extension VIRGIN reserve (the OWNER runs this).

Sprint 3's declare_virgin carved the 2024 reserve; this carves the reserve from the
2025 extension of the primary feed, so "the reserve grows with the data" (ARCH-009
§4.2). The 2024 reserve is untouched and its boundary unmoved — this tool designates
ONLY the 2025 extension (ts >= 2025-01-01), splitting it 0.30-trailing VIRGIN /
0.70-leading TRAINING (the Owner's ruling: consistency with 2024 over marginal gain).

Per the Owner's binding instruction, the tool COMPUTES and DISPLAYS the exact boundary
timestamp (server-clock wall time AND epoch seconds), the resulting TRAINING/VIRGIN
bar counts and the fraction BEFORE prompting — the Owner types the phrase against
DISPLAYED NUMBERS, never against a description. NOTE: primary-feed timestamps are
BROKER SERVER TIME (clock doctrine, ARCH-009 ADDENDUM 2), so the wall-clock shown is
server time, not absolute UTC.

Reads the ALREADY-INGESTED `xauusd_h1_primary_full` dataset (run
scripts/ingest_lens_feeds_s9.py first); designates nothing else, appends only the two
window records on confirmation. Idempotent: refuses if a 2025 window already exists.

    F:/QRF/.venv/Scripts/python.exe scripts/declare_virgin_2025_s9.py

(Owner: you will be asked to type exactly 'DECLARE VIRGIN'. Anything else aborts and
writes nothing.)
"""

from __future__ import annotations

import importlib.util
from datetime import UTC, datetime
from pathlib import Path

from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.record import Record
from qrf.kernel.records.store import RecordStore

_spec = importlib.util.spec_from_file_location(
    "declare_virgin_s3", Path(__file__).resolve().parent / "declare_virgin_s3.py"
)
_dv3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dv3)
split_boundary = _dv3.split_boundary
is_confirmation = _dv3.is_confirmation
CONFIRM_PHRASE = _dv3.CONFIRM_PHRASE

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"
DATASET = "xauusd_h1_primary_full"
VIRGIN_FRACTION = 0.30  # Owner-ruled: match the 2024 split.
NS = 1_000_000_000


def _fmt_server(ts_ns: int) -> str:
    """Server-clock wall time of a stored ts (labelled UTC, but IS server time)."""
    return datetime.fromtimestamp(ts_ns // NS, tz=UTC).strftime("%Y-%m-%d %H:%M")


def _primary_manifest(store: RecordStore) -> Record:
    for m in store.query(record_type="bulk_manifest"):
        if m.payload["dataset"] == DATASET:
            return m
    raise SystemExit(
        f"{DATASET} not ingested — run scripts/ingest_lens_feeds_s9.py first"
    )


def _reserve_ranges(store: RecordStore) -> list[tuple[int, int]]:
    """Every VIRGIN window's [ts_start, ts_end) — RESERVE-BY-MARKET-TIME (DEVQ-022
    ruling ii): a reserve protects market hours regardless of which dataset/manifest
    the bars sit under, so reserves from ANY dataset bound the extension."""
    return [
        (int(w.payload["ts_start"]), int(w.payload["ts_end"]))
        for w in store.query(record_type="window")
        if w.payload["designation"] == "VIRGIN"
    ]


def _in_any_reserve(ts: int, reserves: list[tuple[int, int]]) -> bool:
    return any(lo <= ts < hi for lo, hi in reserves)


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies the chain on open

    reserves = _reserve_ranges(store)
    if not reserves:
        raise SystemExit("no VIRGIN reserve exists yet — the 2024 reserve must precede this")
    # DEVQ-022 SEAM FIX (ruling i): the extension begins STRICTLY AFTER the last
    # reserve's ts_end (the 2024 VIRGIN ts_end is 1735689600000000001, so the bar
    # with close-ts 1735689600e9 is the reserve's LAST bar, not the extension's
    # first). ext_start = the latest reserve boundary; the bar at 1735689600e9 stays
    # in the 2024 reserve where it belongs.
    ext_start = max(hi for _, hi in reserves)

    for w in store.query(record_type="window"):
        p = w.payload
        if p["dataset"] == DATASET and p["ts_end"] > ext_start:
            raise SystemExit(
                f"already declared: window {w.record_id} ({p['designation']}) "
                f"on {DATASET} in the 2025 extension; refusing to run twice"
            )

    bulk = BulkStore(store, BULK_ROOT)
    manifest = _primary_manifest(store)
    ts_all = sorted(int(x) for x in bulk.read(manifest.record_id).column("ts").to_pylist())
    ext = [t for t in ts_all if t >= ext_start]
    if len(ext) < 2:
        raise SystemExit(f"2025 extension has {len(ext)} bars (< 2); nothing to split")
    # RESERVE-BY-MARKET-TIME assertion (ruling ii): no extension bar may fall inside
    # any reserve range, whatever manifest it came from.
    leaked = [t for t in ext if _in_any_reserve(t, reserves)]
    if leaked:
        raise SystemExit(
            f"reserve leak: {len(leaked)} extension bar(s) fall inside a VIRGIN range "
            f"(first {leaked[0]}) — refusing to designate over reserved market hours"
        )

    split = split_boundary(ext, VIRGIN_FRACTION)
    train_start, boundary, last = ext[0], ext[split], ext[-1]
    n_train, n_virgin = split, len(ext) - split

    print("=" * 70)
    print(f"  2025 extension of {DATASET} (primary feed — SERVER TIME):")
    print(f"    bars           : {len(ext)}  ({_fmt_server(train_start)} .. {_fmt_server(last)})")
    print(f"    virgin_fraction: {VIRGIN_FRACTION}  ->  {n_train} TRAINING (leading) + "
          f"{n_virgin} VIRGIN (trailing)")
    print(f"    last  TRAINING : ts={ext[split - 1]}  server={_fmt_server(ext[split - 1])}  "
          f"epoch_sec={ext[split - 1] // NS}")
    print(f"    first VIRGIN   : ts={boundary}  server={_fmt_server(boundary)}  "
          f"epoch_sec={boundary // NS}")
    print(f"    TRAINING window: [{train_start}, {boundary})")
    print(f"    VIRGIN   window: [{boundary}, {last + 1})   <- untouchable reserve")
    print("=" * 70)

    entered = input(f"Type exactly '{CONFIRM_PHRASE}' to designate the 2025 VIRGIN reserve: ")
    if not is_confirmation(entered):
        raise SystemExit("not confirmed (phrase mismatch); no window designated")

    wl = WindowLedger(store)
    training = wl.designate(DATASET, train_start, boundary, "TRAINING",
                            producer="human:girish", parents=[manifest.record_id])
    virgin = wl.designate(DATASET, boundary, last + 1, "VIRGIN",
                          producer="human:girish", parents=[manifest.record_id])
    rep = store.verify()
    print(f"\ndesignated 2025-TRAINING {training.record_id} [{train_start}, {boundary})")
    print(f"designated 2025-VIRGIN   {virgin.record_id} [{boundary}, {last + 1})  (reserve)")
    print(f"journal verify ok={rep.ok} n_records={rep.n_records} head={rep.head_hash[:12]}")


if __name__ == "__main__":
    main()

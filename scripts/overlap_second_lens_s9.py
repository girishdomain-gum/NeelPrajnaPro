"""ARCH-009 §4.1 — clock-era cross-feed alignment + overlap engine (second lens).

Implements the SEALED pre-registration (journal notes 01KYDCNRM4G7VTE5JRPY4D84K3 +
its DEVQ-022 correction 01KYDDMKQJ7YFEYNBTBQYC7M11), computed AFTER those notes were
appended (DEVQ-020 ordering: the threshold precedes the overlap). The procedure,
verbatim from the seal:

  1. RESERVE EXCLUSION (primary/server clock): drop every primary bar whose ts is in
     2024-VIRGIN [1726128000000000000, 1735689600000000001) or 2025-VIRGIN
     [1757685600000000000, 1767225600000000001). Storage is not computation.
  2. CLOCK ALIGNMENT, PIECEWISE BY DST ERA (ADDENDUM 2): the primary is broker server
     time (GMT+2 winter / GMT+3 summer), the second feed is UTC year-round, so no
     single constant shift aligns the full span. Segment the training timespan at the
     EU DST-transition instants (2024-03-31, 2024-10-27, 2025-03-30, 2025-10-26) and,
     per era, choose the integer-hour shift applied to the PRIMARY stamps from
     {0, ±1, ±2, ±3} h that MAXIMISES the shared-timestamp count against the second
     feed within that era. Record the winner and runner-up. **If any era's runner-up
     is within 5% of the winner's shared count, STOP and DEVQ (do not silently pick).**
  3. AGREEMENT (only once the shifts are fixed): a shared bar AGREES iff
     |Δopen|,|Δclose| ≤ 0.50 and |Δhigh|,|Δlow| ≤ 0.75 USD/oz. agreement_rate =
     n_agree / n_overlap; interpretation threshold ≥ 0.95 (this lens, not yet a gate).

Then persist the aligned overlap slice (overlap_manifest) and append the first
``second_lens`` record ({source_name carries tier=BROKER, overlap_manifest,
agreement_summary with per-era shift tables}). Idempotent: an existing second_lens
is reported, never re-appended.

    F:/QRF/.venv/Scripts/python.exe scripts/overlap_second_lens_s9.py            # run
    F:/QRF/.venv/Scripts/python.exe scripts/overlap_second_lens_s9.py --dry      # no writes

STATUS (2026-07-26): the shared-count criterion trips its own 5% ambiguity guard in
ALL FOUR eras (a dense hourly grid makes adjacent integer-hour shifts nearly equally
populated by COUNT), so this script STOPS without appending and points at DEVQ-023.
The OHLC-agreement diagnostic it prints resolves the shift unambiguously and confirms
the pre-registered hypothesis (-2h winter / -3h summer) — the recommended tiebreak
the DEVQ asks the Architect to ratify. Rebuild the parquets first if absent:
    F:/QRF/.venv/Scripts/python.exe scripts/ingest_lens_feeds_s9.py --rebuild-bulk
"""

from __future__ import annotations

import argparse

from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"
PRIMARY = "xauusd_h1_primary_full"
SECOND = "xauusd_h1_secondfeed"

HR_NS = 3_600_000_000_000
SHIFT_CANDIDATES = (0, -1, -2, -3, 1, 2, 3)  # applied to PRIMARY stamps

# Reserve exclusion ranges (primary/server clock), half-open, per the DEVQ-022 seam fix.
RESERVE_RANGES = (
    (1726128000000000000, 1735689600000000001),  # 2024 VIRGIN
    (1757685600000000000, 1767225600000000001),  # 2025 VIRGIN
)
# EU DST-transition cut points (UTC-date epoch — the transition Sundays carry no
# bars, so the exact sub-day instant does not affect which bars land in each era).
DST_CUTS = (
    1711843200000000000,  # 2024-03-31
    1729987200000000000,  # 2024-10-27
    1743292800000000000,  # 2025-03-30
    1761436800000000000,  # 2025-10-26
)
# OHLC agreement tolerances (USD/oz), sealed.
TOL_OC = 0.50   # open, close
TOL_HL = 0.75   # high, low
AGREEMENT_THRESHOLD = 0.95
AMBIGUITY_MARGIN = 0.05  # runner-up within this fraction of the winner -> STOP + DEVQ

SOURCE_NAME = "exness_xauusdm_h1 (tier=BROKER)"


def _manifest_id(store: RecordStore, dataset: str) -> str:
    for m in store.query(record_type="bulk_manifest"):
        if m.payload["dataset"] == dataset:
            return m.record_id
    raise SystemExit(
        f"no bulk_manifest for {dataset!r}; rebuild:\n"
        "  F:/QRF/.venv/Scripts/python.exe scripts/ingest_lens_feeds_s9.py --rebuild-bulk"
    )


def _in_reserve(ts: int) -> bool:
    return any(lo <= ts < hi for lo, hi in RESERVE_RANGES)


def _era_index(ts: int) -> int:
    for i, cut in enumerate(DST_CUTS):
        if ts < cut:
            return i
    return len(DST_CUTS)


def _agrees(pr, sr) -> bool:
    return (
        abs(pr["open"] - sr["open"]) <= TOL_OC
        and abs(pr["close"] - sr["close"]) <= TOL_OC
        and abs(pr["high"] - sr["high"]) <= TOL_HL
        and abs(pr["low"] - sr["low"]) <= TOL_HL
    )


def _load(store: RecordStore):
    bulk = BulkStore(store, BULK_ROOT)
    prim = bulk.read(_manifest_id(store, PRIMARY)).to_pandas()
    sec = bulk.read(_manifest_id(store, SECOND)).to_pandas()
    return prim, sec


def _compute_eras(prim, sec):
    """Per-era shift tables (shared-count winner/runner-up + OHLC-agreement diagnostic).

    Returns a list of dicts, one per non-empty era, each carrying the full candidate
    table and the winner/runner-up-by-count with the ambiguity margin.
    """
    sec_by_ts = {int(r.ts): {"open": float(r.open), "high": float(r.high),
                             "low": float(r.low), "close": float(r.close)}
                 for r in sec.itertuples(index=False)}
    # primary training bars (reserves excluded), grouped by era.
    eras: dict[int, list] = {}
    for r in prim.itertuples(index=False):
        ts = int(r.ts)
        if _in_reserve(ts):
            continue
        eras.setdefault(_era_index(ts), []).append(
            {"ts": ts, "open": float(r.open), "high": float(r.high),
             "low": float(r.low), "close": float(r.close)}
        )

    out = []
    for era_idx in sorted(eras):
        bars = eras[era_idx]
        table = []
        for sh in SHIFT_CANDIDATES:
            shared = agree = 0
            for pr in bars:
                sr = sec_by_ts.get(pr["ts"] + sh * HR_NS)
                if sr is None:
                    continue
                shared += 1
                if _agrees(pr, sr):
                    agree += 1
            table.append({"shift_h": sh, "shared": shared, "agree": agree,
                          "agreement_rate": agree / shared if shared else 0.0})
        by_count = sorted(table, key=lambda t: -t["shared"])
        winner, runner = by_count[0], by_count[1]
        margin = 1.0 - (runner["shared"] / winner["shared"]) if winner["shared"] else 1.0
        by_agree = max(table, key=lambda t: t["agreement_rate"])
        out.append({
            "era_idx": era_idx, "n_bars": len(bars), "start_ts": bars[0]["ts"],
            "table": table, "winner_count": winner, "runner_count": runner,
            "margin": margin, "ambiguous": margin < AMBIGUITY_MARGIN,
            "winner_agreement": by_agree,
        })
    return out


def _print_report(eras) -> None:
    print("=" * 74)
    print("ARCH-009 §4.1 clock-era alignment — per-era shift tables")
    print("=" * 74)
    for e in eras:
        print(f"\nera {e['era_idx']}  bars={e['n_bars']}  first_ts={e['start_ts']}")
        print("  shift |  shared | agree | agreement_rate")
        for t in sorted(e["table"], key=lambda t: t["shift_h"]):
            mark = ""
            if t["shift_h"] == e["winner_count"]["shift_h"]:
                mark += " <-count-winner"
            if t["shift_h"] == e["winner_agreement"]["shift_h"]:
                mark += " <-agreement-winner"
            print(f"   {t['shift_h']:+d}h  | {t['shared']:6d}  | {t['agree']:5d} | "
                  f"{t['agreement_rate']:.3f}{mark}")
        verdict = "AMBIGUOUS (runner-up within 5%)" if e["ambiguous"] else "clear"
        print(f"  count winner {e['winner_count']['shift_h']:+d}h vs runner-up "
              f"{e['runner_count']['shift_h']:+d}h — margin {e['margin']:.2%} -> {verdict}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry", action="store_true", help="compute + print; append nothing")
    args = ap.parse_args()

    store = RecordStore(JOURNAL)  # verifies the chain on open

    existing = list(store.query(record_type="second_lens"))
    if existing:
        print(f"second_lens already exists ({existing[0].record_id}); nothing to do.")
        return

    prim, sec = _load(store)
    eras = _compute_eras(prim, sec)
    _print_report(eras)

    ambiguous = [e for e in eras if e["ambiguous"]]
    if ambiguous:
        raise SystemExit(
            "\n" + "!" * 74 + "\n"
            "STOP (sealed pre-registration): the shared-COUNT alignment criterion trips "
            f"its 5% ambiguity guard in {len(ambiguous)}/{len(eras)} era(s) — a dense "
            "hourly grid makes adjacent integer-hour shifts nearly equally populated by "
            "COUNT. The pre-registration binds: 'do not silently pick'. No second_lens "
            "appended. The OHLC-agreement diagnostic above resolves the shift cleanly "
            "and confirms the hypothesised shifts; see inbox/OPEN/DEVQ-023 for the "
            "proposed tiebreak the Architect must ratify before §4.1 can complete.\n"
            + "!" * 74
        )

    # (Unreached until the ordering guard is resolved — the append path lands with the
    # Architect's DEVQ-023 ruling on the discriminator. ``--dry`` will gate the append
    # once that path exists.)
    mode = "dry — no writes" if args.dry else "live"
    raise SystemExit(
        f"alignment clean ({mode}) but the append path awaits the DEVQ-023 "
        "discriminator ruling."
    )


if __name__ == "__main__":
    main()

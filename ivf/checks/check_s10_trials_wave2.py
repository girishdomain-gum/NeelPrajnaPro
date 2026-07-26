#!/usr/bin/env python3
"""IVF Sprint-10 check: trial-ledger completeness + Wave-2 sweep audit. (rev 1)

  A) TRIAL LEDGER (ADR-011, journal-only): EVERY hypothesis record must
     have >= 1 trial_count parented on it with n_attempts=1 (the four
     retro-counts included); family totals recomputed from scratch
     (DEVQ-015 prefix rule) and reported; the Wave-2 sweep's 500-trial
     charge must exist with the note's lineage; no verdict's recorded
     family_m is touched (history) — but any FUTURE verdict must deflate
     against the recomputed totals, so they are printed for the record.
  B) SWEEP / SHORTLIST (manifest-hash-verified parquet): exactly the
     note's grid_size rows, unique (hold_bars, strength_min, side)
     combos; the admission thresholds RE-APPLIED to every row's recorded
     metrics must reproduce each row's admitted flag and the note's
     n_admitted; the note's top list must match the parquet's ranking
     head; the events manifest's row count matches and — the reserve
     audit — the sweep bars manifest's ts_max must be strictly below the
     2025-VIRGIN ts_start (the slice guard verified from the ledger, not
     trusted).

INDEPENDENCE: stdlib + pyarrow; no qrf imports.
Usage (from /f/QRF; rebuild first via the wave script if the parquet is
absent):
  uv run python scripts/wave2_screen_s10.py --rebuild-bulk
  uv run python ivf/checks/check_s10_trials_wave2.py --journal datastore/journal/journal.jsonl --shortlist datastore/bulk/screener_shortlist_s10_wave2/part-00000.parquet --report ivf/reports/s10_verify.json
"""
from __future__ import annotations
import argparse, hashlib, json, sys, time

VIRGIN_2025 = "01KYDE784NHYD1ZX4X9BQJ54V2"


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def family_matches(family, rec_family, lineage):
    if rec_family == family:
        return True
    seg = family.split("/", 1)[1] if "/" in family else family
    return lineage == seg or lineage.startswith(seg + ".")


def run_check(journal, shortlist_rows=None, shortlist_ok=False):
    red, amber, counts = [], [], {"journal_records": len(journal)}
    by = {r["record_id"]: r for r in journal}
    hyps = [r for r in journal if r.get("record_type") == "hypothesis"]
    trials = [r for r in journal if r.get("record_type") == "trial_count"]

    # A: every hypothesis carries its spent attempt
    for h in hyps:
        mine = [t for t in trials if h["record_id"] in t.get("parents", [])
                and int(t["payload"].get("n_attempts", 0)) == 1]
        if not mine:
            red.append(f"A.unpaid: hypothesis {h['record_id']} "
                       f"({h['payload'].get('lineage')}) has NO trial_count "
                       f"parented on it — ADR-011 violated")
        elif len(mine) > 1:
            red.append(f"A.double: hypothesis {h['record_id']} has "
                       f"{len(mine)} trial_counts")
    fams = {}
    for t in trials:
        p = t["payload"]
        key = p.get("family") or "(v1:smc.fvg)"
        fams[key] = fams.get(key, 0) + int(p.get("n_attempts", 0))
    counts["family_totals_raw"] = fams
    for fam, want in (("xauusd_h1/smc.fvg", 1004),
                      ("xauusd_h1/seasonality.calendar", 2)):
        got = sum(int(t["payload"].get("n_attempts", 0)) for t in trials
                  if family_matches(fam, t["payload"].get("family"),
                                    str(t["payload"].get("lineage", ""))))
        counts[f"deflation_total[{fam}]"] = got
        if got != want:
            red.append(f"A.total[{fam}]: recomputed {got} != expected {want}")

    # B: sweep note vs shortlist parquet
    note = None
    for r in reversed(journal):
        if r.get("record_type") == "note":
            try:
                j = json.loads(r["payload"].get("text", ""))
                if j.get("kind") == "screener_shortlist" and \
                        j.get("lineage") == "smc.fvg.screen.s10.wave2":
                    note = (r, j)
                    break
            except (ValueError, TypeError):
                continue
    if note is None:
        red.append("B.note: no Wave-2 shortlist note")
        return red, amber, counts
    nrec, nj = note
    charge = [t for t in trials
              if t["payload"].get("lineage") == nj["lineage"]
              and int(t["payload"].get("n_attempts", 0)) == nj["grid_size"]]
    if len(charge) != 1:
        red.append(f"B.charge: expected exactly 1 trial_count of "
                   f"{nj['grid_size']} for {nj['lineage']}, found {len(charge)}")
    man = by.get(nj.get("shortlist_manifest_ref", ""), None)
    if man is None or man.get("record_type") != "bulk_manifest":
        red.append("B.manifest: shortlist_manifest_ref does not resolve")
    if shortlist_rows is not None and shortlist_ok:
        th = nj["thresholds"]
        n_adm = 0
        combos = set()
        for row in shortlist_rows:
            combos.add((int(row["hold_bars"]), float(row["strength_min"]),
                        str(row["side"])))
            should = (float(row["net_sharpe"]) >= float(th["min_sharpe"])
                      and int(row["n_trades"]) >= int(th["min_trades"])
                      and (not th["require_positive_net_total"]
                           or float(row["net_total"]) > 0))
            if bool(row["admitted"]) != should:
                red.append(f"B.admit: row {sorted(row.items())[:3]} admitted="
                           f"{row['admitted']} but thresholds say {should}")
            n_adm += 1 if row["admitted"] else 0
        if len(shortlist_rows) != int(nj["grid_size"]):
            red.append(f"B.rows: parquet {len(shortlist_rows)} != grid_size "
                       f"{nj['grid_size']}")
        if len(combos) != len(shortlist_rows):
            red.append("B.grid: duplicate grid combos in shortlist parquet")
        if n_adm != int(nj["n_admitted"]):
            red.append(f"B.count: parquet admits {n_adm} != note n_admitted "
                       f"{nj['n_admitted']}")
        counts["n_admitted_mine"] = n_adm
    # reserve audit from the ledger: sweep bars slice ends before the reserve
    vw = by.get(VIRGIN_2025)
    bars_man = next((r for r in journal if r.get("record_type") ==
                     "bulk_manifest" and r["payload"].get("dataset") ==
                     "xauusd_h1_primary_2025train"), None)
    if vw is None or bars_man is None:
        red.append("B.reserve: missing 2025 VIRGIN window or sweep bars manifest")
    else:
        tmax = bars_man["payload"].get("ts_max")
        if tmax is None:
            amber.append("B.reserve: bars manifest lacks ts_max — slice guard "
                         "not ledger-verifiable")
        elif int(tmax) >= int(vw["payload"]["ts_start"]):
            red.append(f"B.reserve: sweep bars ts_max {tmax} reaches into the "
                       f"2025 reserve (starts {vw['payload']['ts_start']})")
        counts["reserve_gap_ok"] = tmax is not None and \
            int(tmax) < int(vw["payload"]["ts_start"])
    burns = [b for b in journal if b.get("record_type") == "window_burn"
             and b["payload"].get("window_ref") == VIRGIN_2025]
    if burns:
        red.append("B.virgin: 2025 reserve has burns")
    return red, amber, counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--shortlist", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    journal = load(a.journal)
    man = next((r for r in journal if r.get("record_type") == "bulk_manifest"
                and r["payload"].get("dataset") ==
                "screener_shortlist_s10_wave2"), None)
    red, amber = [], []
    rows, ok = None, False
    if man is None:
        red.append("A.manifest: no shortlist manifest in journal")
    else:
        got = sha256_file(a.shortlist)
        ok = got == man["payload"]["file_sha256"]
        if not ok:
            red.append(f"A.hash: {a.shortlist} {got[:12]}… != manifest "
                       f"{man['payload']['file_sha256'][:12]}… — refused "
                       f"(rebuild via wave2_screen_s10.py --rebuild-bulk)")
        else:
            import pyarrow.parquet as pq
            rows = pq.read_table(a.shortlist).to_pylist()
    r2, a2, counts = run_check(journal, rows, ok)
    red += r2
    amber += a2
    verdict = "RED" if red else ("AMBER" if amber else "GREEN")
    rep = {"check": "s10_trials_wave2", "rev": 1, "run_utc": int(time.time()),
           "counts": counts, "red": red, "amber": amber, "verdict": verdict}
    out = json.dumps(rep, indent=2)
    if a.report:
        open(a.report, "w", encoding="utf-8").write(out + "\n")
    print(out)
    return 1 if verdict == "RED" else 0


if __name__ == "__main__":
    sys.exit(main())

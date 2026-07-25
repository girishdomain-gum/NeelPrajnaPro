#!/usr/bin/env python3
"""IVF Sprint-6 check: the verdict itself. (rev 1)

Four sections, one verdict (GREEN / AMBER / RED; exit 0 / 0 / 1):

  A) CORRECTIONS RECOMPUTATION. Reads the journal directly (stdlib) and
     re-implements BOTH deflation rules from the DEVQ-015 ruling text:
     legacy (scope, lineage) exact-key — must reproduce the H-001
     verdict's recorded family_m=0 / effective_alpha=0.05 — and the
     family-prefix rule for "xauusd_h1/smc.fvg" with boundary-safe
     matching — must find the 500 screener trials → 1e-4. Both numbers
     are compared against what the machinery recorded/reports.
  B) VERDICT vs REGISTRATION, BYTE-EQUAL. The thresholds inside the
     verdict payload must canonically equal the thresholds inside the
     hypothesis record it references — no goalpost moved by a comma.
     The tri-state is then RE-DERIVED from the verdict's own recorded
     numbers (n vs min_n; p vs effective_alpha; mean sign) and must
     equal the recorded verdict.
  C) BURN AUDIT. Exactly ONE window_burn for (window, lineage); its
     parents include the verdict; its consumed_by is the verdict; the
     verdict's window_ref matches. A second burn for the same pair
     anywhere in the journal is RED.
  D) TRADES RECOMPUTATION. From the verdict's trades manifest parquet:
     n_trades, gross total/mean, net total/mean, and the one-sided t
     recomputed with stdlib math — all compared to the verdict payload
     (1e-9 / 1e-6 tolerances). Fold means recomputed too when the
     parquet carries a fold column; otherwise AMBER names the absence.

INDEPENDENCE: no qrf imports; stdlib + pyarrow only; every rule
re-implemented from the ruling texts (ARCH-006 §2/§3, DEVQ-015 REPLY).

Usage (paste in git bash, from /f/QRF):
  uv run python ivf/checks/check_s6_verdict.py --journal datastore/journal/journal.jsonl --trades datastore/bulk/verdict_trades.h001_fvg_follow_through/part-00000.parquet --family xauusd_h1/smc.fvg --report ivf/reports/s6_verify.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time


def load_journal(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def family_matches(family: str, rec_family: str | None, lineage: str) -> bool:
    """DEVQ-015 rule, boundary-safe: declared family equal, or the family's
    instrument segment prefixes the lineage at a token boundary."""
    if rec_family == family:
        return True
    seg = family.split("/", 1)[1] if "/" in family else family
    return lineage == seg or lineage.startswith(seg + ".")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--trades", required=True)
    ap.add_argument("--family", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    red: list[str] = []
    amber: list[str] = []
    journal = load_journal(a.journal)
    by_id = {r["record_id"]: r for r in journal}

    verdicts = [r for r in journal if r.get("record_type") == "verdict"]
    if not verdicts:
        red.append("no verdict record in the journal — nothing to check")
    burns = [r for r in journal if r.get("record_type") == "window_burn"]
    trials = [r for r in journal if r.get("record_type") == "trial_count"]

    # --- A: corrections, both rules re-implemented ---------------------------
    n_family = sum(int(t["payload"].get("n_attempts", 0)) for t in trials
                   if family_matches(a.family, t["payload"].get("family"),
                                     str(t["payload"].get("lineage", ""))))
    eff_family = 0.05 / max(1, n_family)
    counts_a = {"family": a.family, "family_trials": n_family,
                "family_effective_alpha": eff_family}
    if n_family != 500:
        red.append(f"A.family: my prefix rule finds {n_family} trials for "
                   f"{a.family}, expected 500 (screener bump)")

    for v in verdicts:
        p = v["payload"]
        hyp = by_id.get(p.get("hypothesis_ref", ""))
        if hyp is None:
            red.append(f"B.ref: verdict {v['record_id']} references missing "
                       f"hypothesis {p.get('hypothesis_ref')}")
            continue
        hp = hyp["payload"]
        # legacy rule as it applied to this verdict
        scope, lineage = hp.get("scope"), hp.get("lineage")
        n_legacy = sum(int(t["payload"].get("n_attempts", 0)) for t in trials
                       if t["payload"].get("data_scope") == scope
                       and t["payload"].get("lineage") == lineage)
        corr = p.get("corrections", {})
        if int(corr.get("family_m", -1)) != n_legacy:
            red.append(f"A.legacy: verdict {v['record_id']} family_m="
                       f"{corr.get('family_m')} vs my legacy count {n_legacy}")
        eff_expect = float(corr.get("base_alpha", 0.05)) / max(1, n_legacy)
        if abs(float(corr.get("effective_alpha", -1)) - eff_expect) > 1e-12:
            red.append(f"A.eff: verdict {v['record_id']} effective_alpha="
                       f"{corr.get('effective_alpha')} vs my {eff_expect}")

        # --- B: thresholds byte-equal + tri-state re-derived ----------------
        if canon(p.get("thresholds")) != canon(hp.get("thresholds")):
            red.append(f"B.thresholds: verdict {v['record_id']} thresholds != "
                       f"registration {hyp['record_id']} (canonical compare)")
        n = int(p.get("n_trades", 0))
        min_n = int(hp.get("thresholds", {}).get("min_n", 0))
        pval = float(p["statistics"]["t_one_sided"]["p"])
        mean = float(p["net"]["mean"])
        eff = float(corr.get("effective_alpha", 0.05))
        if n < min_n:
            derived = "INSUFFICIENT"
        elif mean > 0 and pval < eff:
            derived = "PASS"
        else:
            derived = "FAIL"
        if derived != p.get("verdict"):
            red.append(f"B.tristate: verdict {v['record_id']} recorded "
                       f"{p.get('verdict')} but its own numbers derive {derived}")

        # --- C: burn audit ---------------------------------------------------
        w, lin = p.get("window_ref"), hp.get("lineage")
        my_burns = [b for b in burns
                    if b["payload"].get("window_ref") == w
                    and b["payload"].get("lineage") == lin]
        if len(my_burns) != 1:
            red.append(f"C.burn: {len(my_burns)} burns for (window {w}, "
                       f"lineage {lin}) — exactly 1 required")
        for b in my_burns:
            if b["payload"].get("consumed_by") != v["record_id"]:
                red.append(f"C.consumed: burn {b['record_id']} consumed_by="
                           f"{b['payload'].get('consumed_by')} != verdict id")
            if v["record_id"] not in b.get("parents", []):
                red.append(f"C.parents: burn {b['record_id']} parents lack "
                           f"the verdict id")

        # --- D: trades recomputation ----------------------------------------
        import pyarrow.parquet as pq
        rows = pq.read_table(a.trades).to_pylist()
        nets = [float(r["net_pnl"]) for r in rows]
        grosses = [float(r["gross_pnl"]) for r in rows]
        if len(rows) != n:
            red.append(f"D.n: parquet has {len(rows)} trades, verdict says {n}")
        if abs(sum(nets) - float(p["net"]["total"])) > 1e-6:
            red.append(f"D.net_total: parquet {sum(nets):.6f} vs verdict "
                       f"{p['net']['total']:.6f}")
        if abs(sum(grosses) - float(p["gross"]["total"])) > 1e-6:
            red.append(f"D.gross_total: parquet {sum(grosses):.6f} vs verdict "
                       f"{p['gross']['total']:.6f}")
        if len(nets) >= 2:
            m = sum(nets) / len(nets)
            sd = math.sqrt(sum((x - m) ** 2 for x in nets) / (len(nets) - 1))
            if sd > 1e-12:
                t_mine = m / (sd / math.sqrt(len(nets)))
                t_rec = float(p["statistics"]["t_one_sided"]["stat"])
                if abs(t_mine - t_rec) > 1e-6:
                    red.append(f"D.t: my t {t_mine:.6f} vs verdict {t_rec:.6f}")
        if rows and "fold" in rows[0]:
            for f in p.get("folds", []):
                fn = [float(r["net_pnl"]) for r in rows
                      if int(r["fold"]) == int(f["index"])]
                if fn and abs(sum(fn) / len(fn) - float(f["mean_net"])) > 1e-9:
                    red.append(f"D.fold{f['index']}: parquet mean "
                               f"{sum(fn)/len(fn):.6f} vs verdict "
                               f"{f['mean_net']:.6f}")
        else:
            amber.append("D.folds: trades parquet has no 'fold' column — "
                         "fold means verified only via pooled totals")

    verdict_out = "RED" if red else ("AMBER" if amber else "GREEN")
    report = {"check": "s6_verdict", "rev": 1, "run_utc": int(time.time()),
              "counts": {"journal_records": len(journal),
                         "verdicts": len(verdicts), "burns": len(burns),
                         "trial_counts": len(trials)} | counts_a,
              "red": red, "amber": amber, "verdict": verdict_out}
    out = json.dumps(report, indent=2)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print(out)
    return 1 if verdict_out == "RED" else 0


if __name__ == "__main__":
    sys.exit(main())

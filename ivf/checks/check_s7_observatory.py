#!/usr/bin/env python3
"""IVF Sprint-7 check: observatory discipline + belief recomputation. (rev 1)

Five sections, one verdict (GREEN / AMBER / RED; exit 0 / 0 / 1):

  A) BELIEF RECOMPUTATION. Every belief chain re-derived independently
     from the cited verdict records under the ruled contracts:
     evidence must be verdict-type only (arrow-8); stance =
     newest-decisive (PASS→SUPPORTED, FAIL→REJECTED, none→UNTESTED,
     disagreeing decisives→CONTESTED per DEVQ-016(b)); strength =
     2·|p−0.5| decisiveness per DEVQ-016/017 (H-001 anchor 0.887);
     prev_state links resolve.
  B) SCAN + QUESTION DISCIPLINE. Every anomaly_scan has a same-family
     trial_count bump (looking is a burden, DEVQ-015); every question
     is parented to a scan; question payloads carry no
     thresholds/verdict/window_burn keys; NO scan or question payload
     references the VIRGIN window id anywhere (deep scan of refs).
  C) ANCESTRY. Any hypothesis with observatory_ancestry: every id
     exists and is a question record.
  D) PARAMS-READING (owed since GO-S3). Every schema_version>=2
     ingest_report payload carries a params object with
     timeframe_seconds, gap_k, holidays, dataset.
  E) WEEKEND-QUESTION RECOMPUTATION (rev 3 — the scan's DECLARED spec).
     Population: events with a matching bar, k>=2, and horizon room.
     Metric: direction × (close[k+4] − close[k]) — close-based, from the
     knowability bar, NO costs. Weekend flag: for either adjacent
     forming-bar pair (k-2,k-1) or (k-1,k), the gap exceeds one
     timeframe AND any calendar day from the first endpoint's date
     through the second's (inclusive) is a Sat/Sun (UTC). Recomputed
     (n, mean) per partition must equal the scan record to 1e-6.
     Bug history: rev 1 used the wrong population+metric (#12); rev 2
     used an interval-probe weekend rule that over-flagged by 8 — both
     caught by the drill's clean-control requirement before any false
     judgement of the real ledger.

INDEPENDENCE: no qrf imports; stdlib + pyarrow.

Usage (paste in git bash, from /f/QRF):
  uv run python ivf/checks/check_s7_observatory.py --journal datastore/journal/journal.jsonl --bars datastore/bulk/xauusd_h1_full/part-00000.parquet --events "datastore/bulk/xauusd_h1_training_smc_fvg_scan/part-00000.parquet" --virgin 01KYB4SSD9VVKB577KRGB1W1P0 --report ivf/reports/s7_verify.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time

NS = 1_000_000_000
FORBIDDEN_Q_KEYS = {"thresholds", "verdict", "window_burn"}


def load_journal(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def deep_strings(obj) -> list[str]:
    out = []
    if isinstance(obj, dict):
        for v in obj.values():
            out += deep_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            out += deep_strings(v)
    elif isinstance(obj, str):
        out.append(obj)
    return out


def deep_numbers(obj) -> list[float]:
    out = []
    if isinstance(obj, dict):
        for v in obj.values():
            out += deep_numbers(v)
    elif isinstance(obj, list):
        for v in obj:
            out += deep_numbers(v)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out.append(float(obj))
    return out


def derive_belief(verdicts: list[dict]) -> tuple[str, float]:
    decisive = [v for v in verdicts
                if v["payload"].get("verdict") in ("PASS", "FAIL")]
    if not decisive:
        return "UNTESTED", 0.0
    decisions = {v["payload"]["verdict"] for v in decisive}
    newest = max(decisive, key=lambda v: v.get("recorded_ts", 0))
    p = float(newest["payload"]["statistics"]["t_one_sided"]["p"])
    strength = 2.0 * abs(p - 0.5)
    if len(decisions) > 1:
        return "CONTESTED", strength
    return ("SUPPORTED" if "PASS" in decisions else "REJECTED"), strength


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--bars", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--virgin", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    red: list[str] = []
    amber: list[str] = []
    journal = load_journal(a.journal)
    by_id = {r["record_id"]: r for r in journal}
    beliefs = [r for r in journal if r.get("record_type") == "belief"]
    scans = [r for r in journal if r.get("record_type") == "anomaly_scan"]
    questions = [r for r in journal if r.get("record_type") == "question"]
    trials = [r for r in journal if r.get("record_type") == "trial_count"]
    hyps = [r for r in journal if r.get("record_type") == "hypothesis"]

    # --- A: beliefs ----------------------------------------------------------
    # terminal state per (family, claim) = the one no other state points to
    prev_refs = {b["payload"].get("prev_state") for b in beliefs}
    for b in beliefs:
        for vr in b["payload"].get("verdict_refs", []):
            rec = by_id.get(vr)
            if rec is None or rec.get("record_type") != "verdict":
                red.append(f"A.evidence: belief {b['record_id']} cites {vr}, "
                           f"not a verdict record (arrow-8)")
        pv = b["payload"].get("prev_state")
        if pv and pv not in by_id:
            red.append(f"A.chain: belief {b['record_id']} prev_state {pv} "
                       f"missing")
    terminals = [b for b in beliefs if b["record_id"] not in prev_refs]
    for b in terminals:
        cited = [by_id[vr] for vr in b["payload"].get("verdict_refs", [])
                 if vr in by_id and by_id[vr].get("record_type") == "verdict"]
        stance, strength = derive_belief(cited)
        if b["payload"].get("stance") != stance:
            red.append(f"A.stance: belief {b['record_id']} says "
                       f"{b['payload'].get('stance')}, derivation says {stance}")
        if abs(float(b["payload"].get("strength", -1)) - strength) > 1e-9:
            red.append(f"A.strength: belief {b['record_id']} "
                       f"{b['payload'].get('strength')} vs derived "
                       f"{strength:.6f}")

    # --- B: scans + questions ------------------------------------------------
    for s in scans:
        fam = s["payload"].get("family", "")
        bumped = any(t["payload"].get("family") == fam
                     or str(t["payload"].get("lineage", "")) == f"{fam.split('/',1)[-1]}.scan"
                     or str(t["payload"].get("lineage", "")).endswith(".scan")
                     and fam.split("/", 1)[-1] in str(t["payload"].get("lineage", ""))
                     for t in trials)
        if not bumped:
            red.append(f"B.burden: scan {s['record_id']} (family {fam}) has "
                       f"no matching trial_count bump")
        if a.virgin in deep_strings(s["payload"]):
            red.append(f"B.virgin: scan {s['record_id']} references the "
                       f"VIRGIN window")
    scan_ids = {s["record_id"] for s in scans}
    for q in questions:
        if not (set(q.get("parents", [])) & scan_ids):
            red.append(f"B.parent: question {q['record_id']} not parented to "
                       f"any anomaly_scan")
        bad = FORBIDDEN_Q_KEYS & set(q["payload"].keys())
        if bad:
            red.append(f"B.keys: question {q['record_id']} carries forbidden "
                       f"key(s) {sorted(bad)}")
        if a.virgin in deep_strings(q["payload"]):
            red.append(f"B.virgin: question {q['record_id']} references the "
                       f"VIRGIN window")

    # --- C: ancestry ---------------------------------------------------------
    for h in hyps:
        for qid in h["payload"].get("observatory_ancestry", []) or []:
            rec = by_id.get(qid)
            if rec is None or rec.get("record_type") != "question":
                red.append(f"C.ancestry: hypothesis {h['record_id']} claims "
                           f"{qid}, not a question record")

    # --- D: ingest_report v2 params -----------------------------------------
    for r in journal:
        if r.get("record_type") == "ingest_report" and \
                int(r.get("schema_version", 1)) >= 2:
            params = r["payload"].get("params")
            if not isinstance(params, dict):
                red.append(f"D.params: v2 ingest_report {r['record_id']} "
                           f"lacks params object")
                continue
            for k in ("timeframe_seconds", "gap_k", "holidays", "dataset"):
                if k not in params:
                    red.append(f"D.params: report {r['record_id']} params "
                               f"missing {k!r}")

    # --- E: weekend-question recomputation (scan semantics, rev 2) ----------
    import pyarrow.parquet as pq
    from datetime import UTC, datetime, timedelta
    bars = sorted(pq.read_table(a.bars).to_pylist(), key=lambda r: int(r["ts"]))
    ts_index = {int(r["ts"]): i for i, r in enumerate(bars)}
    events = [e for e in pq.read_table(a.events).to_pylist()
              if str(e.get("event_type", "")).startswith("smc.fvg.")]

    def spans_weekend(a_ns: int, b_ns: int) -> bool:
        if b_ns - a_ns <= 3600 * NS:
            return False
        day = datetime.fromtimestamp(a_ns // NS, UTC).date()
        end = datetime.fromtimestamp(b_ns // NS, UTC).date()
        while day <= end:
            if day.weekday() >= 5:
                return True
            day += timedelta(days=1)
        return False

    wk, intra = [], []
    skipped = 0
    for e in events:
        k = ts_index.get(int(e["ts"]))
        if k is None or k < 2 or k + 4 >= len(bars):
            skipped += 1
            continue
        ft = int(e["direction"]) * (float(bars[k + 4]["close"])
                                    - float(bars[k]["close"]))
        weekend = (spans_weekend(int(bars[k - 2]["ts"]), int(bars[k - 1]["ts"]))
                   or spans_weekend(int(bars[k - 1]["ts"]), int(bars[k]["ts"])))
        (wk if weekend else intra).append(ft)
    counts_e = {"weekend_n": len(wk), "intra_n": len(intra),
                "events_skipped_tail": skipped,
                "weekend_mean": (sum(wk) / len(wk)) if wk else 0.0,
                "intra_mean": (sum(intra) / len(intra)) if intra else 0.0}
    scan_wk = next((s for s in scans if str(s["payload"].get("method", ""))
                    .startswith("fvg.weekend_partition")), None)
    if scan_wk is None:
        red.append("E.scan: no fvg.weekend_partition anomaly_scan found")
    else:
        parts = scan_wk["payload"]["findings"]["partitions"]
        for name, mine_n, mine_mean in (("weekend_spanning", len(wk),
                                         counts_e["weekend_mean"]),
                                        ("intra_week", len(intra),
                                         counts_e["intra_mean"])):
            rec = parts.get(name, {})
            if int(rec.get("n", -1)) != mine_n:
                red.append(f"E.n: {name} scan n={rec.get('n')} vs my {mine_n}")
            if abs(float(rec.get("mean", 9e9)) - mine_mean) > 1e-6:
                red.append(f"E.mean: {name} scan {rec.get('mean')} vs my "
                           f"{mine_mean:.9f}")

    verdict = "RED" if red else ("AMBER" if amber else "GREEN")
    report = {"check": "s7_observatory", "rev": 3, "run_utc": int(time.time()),
              "counts": {"journal_records": len(journal),
                         "beliefs": len(beliefs), "scans": len(scans),
                         "questions": len(questions),
                         "terminal_beliefs": len(terminals)} | counts_e,
              "red": red, "amber": amber, "verdict": verdict}
    out = json.dumps(report, indent=2)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print(out)
    return 1 if verdict == "RED" else 0


if __name__ == "__main__":
    sys.exit(main())

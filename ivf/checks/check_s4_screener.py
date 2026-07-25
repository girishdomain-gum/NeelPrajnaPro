#!/usr/bin/env python3
"""IVF Sprint-4 check: screener discipline + SMC causality. (rev 3)

rev 3: FVG rule completed per DEVQ-010 ADDENDUM — the 3-bar gap must have
a DIRECTIONAL middle (displacement) candle (close>open for bull,
close<open for bear). rev 2's pure-gap rule found 2 phantom events on
real data (both with bearish middles, both weekend-spanning); the
disagreement was caught by this check and ruled in the DEVQ-010 addendum.

Sections:
  A) NO-VERDICT AUDIT (arrow 8): AST scan of the screener sources for
     record_type "verdict"/"window_burn" literals.
  B) TRIAL-COUNT CROSS-COUNT: every screener_shortlist note must have a
     matching trial_count with n_attempts == grid_size, source=screener.
  C) SHORTLIST-NOTE CONTRACT (DEVQ-008/009): ranking_metric, thresholds,
     cost_model declared; cost_model present in venues.yaml.
  D) SMC FVG FULL RECOMPUTATION (DEVQ-010 / §4.3): from the bars parquet,
     bull FVG at pattern bar i when low[i+1] > high[i-1] (bear mirrored);
     event ts = bars ts of row i+1 (close basis); zone = [high[i-1],
     low[i+1]] (mirrored for bear). The recomputed set must equal the
     persisted events set exactly (join_consecutive=False default).
     Order blocks are NOT recomputed (operational knowability per
     DEVQ-010; Sprint-6 carried item) — stated, not hidden.

INDEPENDENCE: no qrf imports; pyarrow + yaml only.

Usage (bash-ready, from F:/QRF):
  uv run python ivf/checks/check_s4_screener.py --src qrf/trading/simulator --journal datastore/journal/journal.jsonl --venues configs/venues.yaml --bars datastore/bulk/xauusd_h1_sample/part-00000.parquet --events datastore/bulk/xauusd_h1_sample_smc_fvg_events/part-00000.parquet --report ivf/reports/s4_verify.json
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
import time

FORBIDDEN = {"verdict", "window_burn"}


def section_a(src_dir: str, red: list[str]) -> int:
    scanned = 0
    for root, _dirs, files in os.walk(src_dir):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(root, fn)
            scanned += 1
            with open(path, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and node.value in FORBIDDEN:
                    red.append(f"A.forbidden: {path}:{getattr(node,'lineno','?')} "
                               f"contains {node.value!r}")
    return scanned


def load_journal(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def parse_shortlists(journal: list[dict]) -> list[tuple[str, dict]]:
    out = []
    for r in journal:
        if r.get("record_type") != "note":
            continue
        text = (r.get("payload") or {}).get("text", "")
        try:
            body = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(body, dict) and body.get("kind") == "screener_shortlist":
            out.append((r["record_id"], body))
    return out


def section_bc(journal: list[dict], venues_path: str,
               red: list[str], amber: list[str]) -> dict:
    import yaml

    with open(venues_path, encoding="utf-8") as f:
        venues = yaml.safe_load(f) or {}
    venue_names = set()
    def collect(d):
        if isinstance(d, dict):
            for k, v in d.items():
                venue_names.add(k); collect(v)
    collect(venues)

    trial_counts = {r["record_id"]: r for r in journal
                    if r.get("record_type") == "trial_count"}
    shortlists = parse_shortlists(journal)
    if not shortlists:
        amber.append("B/C.vacuous: ZERO screener_shortlist notes found — "
                     "nothing audited (AMBER by rule; rev-1 lesson)")
    for nid, body in shortlists:
        for field in ("ranking_metric", "thresholds", "cost_model"):
            if field not in body:
                red.append(f"C.declare: shortlist {nid} missing {field!r}")
        cm = body.get("cost_model")
        if cm and cm not in venue_names:
            red.append(f"C.cost_model: {nid} cites {cm!r}, absent from venues.yaml")
        if body.get("seed") is None:
            amber.append(f"C.seed: shortlist {nid} recorded seed=null — real "
                         f"runs should record a seed (REV-S4 observation)")
        tref = body.get("trial_count_ref")
        if not tref:
            red.append(f"B.bump: shortlist {nid} has no trial_count_ref")
            continue
        tc = trial_counts.get(tref)
        if tc is None:
            red.append(f"B.bump: {nid} refs {tref}, not a trial_count record")
            continue
        n, g = tc["payload"].get("n_attempts"), body.get("grid_size")
        if n != g:
            red.append(f"B.count: {nid} grid_size={g} but trial_count {tref} "
                       f"n_attempts={n}")
        if tc["payload"].get("source") != "screener":
            amber.append(f"B.source: {tref} source="
                         f"{tc['payload'].get('source')!r} (expected 'screener')")
    return {"shortlists": len(shortlists), "trial_counts": len(trial_counts)}


def recompute_fvg(bars: list[dict]) -> set[tuple[int, str, float, float]]:
    """Ratified FVG rule (DEVQ-010 addendum): 3-bar gap AND directional
    middle (displacement) candle. rev 3."""
    out = set()
    for i in range(1, len(bars) - 1):
        hi_prev, lo_prev = float(bars[i-1]["high"]), float(bars[i-1]["low"])
        hi_next, lo_next = float(bars[i+1]["high"]), float(bars[i+1]["low"])
        o_mid, c_mid = float(bars[i]["open"]), float(bars[i]["close"])
        ts_next = int(bars[i+1]["ts"])
        if lo_next > hi_prev and c_mid > o_mid:
            out.add((ts_next, "smc.fvg.bull", round(lo_next, 10), round(hi_prev, 10)))
        if hi_next < lo_prev and c_mid < o_mid:
            out.add((ts_next, "smc.fvg.bear", round(lo_prev, 10), round(hi_next, 10)))
    return out


def section_d(bars_path: str, events_path: str,
              red: list[str], amber: list[str]) -> dict:
    import pyarrow.parquet as pq

    bars = sorted(pq.read_table(bars_path).to_pylist(),
                  key=lambda r: int(r["ts"]))
    events = [e for e in pq.read_table(events_path).to_pylist()
              if str(e.get("event_type", "")).startswith("smc.fvg.")]
    theirs = {(int(e["ts"]), str(e["event_type"]),
               round(float(e["zone_hi"]), 10), round(float(e["zone_lo"]), 10))
              for e in events}
    mine = recompute_fvg(bars)
    missing = mine - theirs      # I find it; detector didn't emit it
    invented = theirs - mine     # detector emitted; spec rule doesn't produce it
    for t in sorted(missing)[:5]:
        red.append(f"D.missing: spec finds FVG {t} but events lack it")
    if len(missing) > 5:
        red.append(f"D.missing: … and {len(missing)-5} more")
    for t in sorted(invented)[:5]:
        red.append(f"D.invented: events contain {t}, spec rule does not produce it")
    if len(invented) > 5:
        red.append(f"D.invented: … and {len(invented)-5} more")
    if not theirs:
        amber.append("D.vacuous: zero smc.fvg events in the events parquet")
    return {"bars": len(bars), "fvg_events_persisted": len(theirs),
            "fvg_events_recomputed": len(mine)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--journal", required=True)
    ap.add_argument("--venues", required=True)
    ap.add_argument("--bars", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    red: list[str] = []
    amber: list[str] = []
    scanned = section_a(a.src, red)
    journal = load_journal(a.journal)
    bc = section_bc(journal, a.venues, red, amber)
    d = section_d(a.bars, a.events, red, amber)

    verdict = "RED" if red else ("AMBER" if amber else "GREEN")
    report = {"check": "s4_screener", "rev": 3, "run_utc": int(time.time()),
              "inputs": {k: v for k, v in vars(a).items()},
              "counts": {"src_files_scanned": scanned,
                         "journal_records": len(journal)} | bc | d,
              "red": red, "amber": amber, "verdict": verdict}
    out = json.dumps(report, indent=2)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print(out)
    return 1 if verdict == "RED" else 0


if __name__ == "__main__":
    sys.exit(main())

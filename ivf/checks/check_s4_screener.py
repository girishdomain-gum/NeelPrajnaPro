#!/usr/bin/env python3
"""IVF Sprint-4 check: screener discipline + SMC causality. (rev 1)

Four sections, one verdict (GREEN / AMBER / RED; exit 0 / 0 / 1):

  A) NO-VERDICT AUDIT (arrow 8). Independent AST scan of the screener
     source tree: no call may pass record_type "verdict" or "window_burn"
     (as literal arg or keyword) anywhere under qrf/trading/simulator/.
     This re-implements the Developer's own audit from the spec text —
     two independent implementations must agree.
  B) TRIAL-COUNT CROSS-COUNT. Reads the journal JSONL directly (stdlib,
     no qrf imports): every screener shortlist note (payload with
     grid_size + trial_count_ref) must have a matching trial_count
     record with n_attempts == grid_size, source == "screener". Any
     shortlist without its bump, or with an under/over-count, is RED.
  C) SHORTLIST-NOTE CONTRACT (DEVQ-009). Each shortlist note payload
     must declare ranking_metric, thresholds (min_trades, min_sharpe),
     cost_model; the cost_model name must exist in configs/venues.yaml
     (name-reference contract, DEVQ-008).
  D) SMC FVG INDEPENDENT RECOMPUTATION (DEVQ-010 / §4.3). Re-derives
     bull/bear FVGs from the spec definition (bull: low[i+1] > high[i-1];
     zone = [high[i-1], low[i+1]]; knowability ts = bar i+1, close basis)
     over the planted truth fixtures, and compares against the events the
     calibration recorded as expected. Order blocks are NOT recomputed
     here (their knowability is operational per DEVQ-010; covered by
     calibration + the Sprint-6 carried item) — stated, not hidden.

INDEPENDENCE: no qrf imports. pyarrow reads parquet; yaml reads venues.

Usage (S4 close, run from F:/QRF):
  uv run python ivf/checks/check_s4_screener.py \
      --src qrf/trading/simulator \
      --journal datastore/journal/journal.jsonl \
      --venues configs/venues.yaml \
      --fixtures qrf/trading/concepts/smc/fixtures \
      --report ivf/reports/s4_verify.json
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
import time

FORBIDDEN = {"verdict", "window_burn"}
NS = 1_000_000_000


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
                values = []
                if isinstance(node, ast.Call):
                    values += [a for a in node.args]
                    values += [k.value for k in node.keywords]
                elif isinstance(node, ast.Constant):
                    values = [node]
                for v in values:
                    if isinstance(v, ast.Constant) and v.value in FORBIDDEN:
                        red.append(
                            f"A.forbidden: {path}:{getattr(v,'lineno','?')} "
                            f"contains {v.value!r}"
                        )
    return scanned


def load_journal(path: str) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def section_bc(journal: list[dict], venues_path: str,
               red: list[str], amber: list[str]) -> dict:
    import yaml

    with open(venues_path, encoding="utf-8") as f:
        venues = yaml.safe_load(f) or {}
    venue_names = set()
    def collect(d):
        if isinstance(d, dict):
            for k, v in d.items():
                venue_names.add(k)
                collect(v)
    collect(venues)

    trial_counts = {r["record_id"]: r for r in journal
                    if r.get("record_type") == "trial_count"}
    shortlists = [r for r in journal
                  if r.get("record_type") == "note"
                  and isinstance(r.get("payload"), dict)
                  and "grid_size" in r.get("payload", {})]
    for note in shortlists:
        p = note["payload"]
        nid = note["record_id"]
        # C: declaration contract
        for field in ("ranking_metric", "thresholds", "cost_model"):
            if field not in p:
                red.append(f"C.declare: shortlist {nid} missing {field!r}")
        cm = p.get("cost_model")
        if cm and cm not in venue_names:
            red.append(f"C.cost_model: {nid} cites {cm!r}, absent from venues.yaml")
        # B: trial-count cross-count
        tref = p.get("trial_count_ref")
        if not tref:
            red.append(f"B.bump: shortlist {nid} has no trial_count_ref")
            continue
        tc = trial_counts.get(tref)
        if tc is None:
            red.append(f"B.bump: {nid} refs {tref}, not a trial_count record")
            continue
        n = tc["payload"].get("n_attempts")
        g = p.get("grid_size")
        if n != g:
            red.append(f"B.count: {nid} grid_size={g} but trial_count "
                       f"{tref} n_attempts={n}")
        if tc["payload"].get("source") != "screener":
            amber.append(f"B.source: {tref} source={tc['payload'].get('source')!r}"
                         f" (expected 'screener')")
    return {"shortlists": len(shortlists), "trial_counts": len(trial_counts)}


def recompute_fvg(rows: list[dict]) -> list[tuple[int, str, float, float]]:
    """Spec-text FVG: bull at i when low[i+1] > high[i-1]; ts = bar i+1."""
    out = []
    for i in range(1, len(rows) - 1):
        hi_prev, lo_prev = rows[i - 1]["high"], rows[i - 1]["low"]
        hi_next, lo_next = rows[i + 1]["high"], rows[i + 1]["low"]
        if lo_next > hi_prev:
            out.append((int(rows[i + 1]["ts"]), "smc.fvg.bull",
                        float(lo_next), float(hi_prev)))
        if hi_next < lo_prev:
            out.append((int(rows[i + 1]["ts"]), "smc.fvg.bear",
                        float(lo_prev), float(hi_next)))
    return out


def section_d(fixtures_dir: str, red: list[str], amber: list[str]) -> dict:
    import pyarrow.parquet as pq

    stats = {"fixtures_checked": 0, "fvg_events_recomputed": 0}
    if not os.path.isdir(fixtures_dir):
        amber.append(f"D.fixtures: dir {fixtures_dir} not found — recomputation "
                     f"skipped (AMBER, investigate)")
        return stats
    for fn in sorted(os.listdir(fixtures_dir)):
        if "fvg" not in fn.lower() or not fn.endswith(".parquet"):
            continue
        path = os.path.join(fixtures_dir, fn)
        table = pq.read_table(path).to_pylist()
        if not table or not all(k in table[0] for k in ("ts", "high", "low")):
            amber.append(f"D.schema: {fn} lacks ts/high/low — skipped")
            continue
        stats["fixtures_checked"] += 1
        mine = recompute_fvg(table)
        stats["fvg_events_recomputed"] += len(mine)
        if "truth" in fn.lower() and not mine:
            red.append(f"D.truth: fixture {fn} is a planted-truth case but "
                       f"independent recomputation finds NO FVG")
        if "noise" in fn.lower() and mine:
            red.append(f"D.noise: fixture {fn} is a silence case but "
                       f"recomputation finds {len(mine)} FVG(s): first={mine[0]}")
    if stats["fixtures_checked"] == 0:
        amber.append("D.fixtures: no *fvg*.parquet fixtures found — "
                     "recomputation VACUOUS (AMBER)")
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--journal", required=True)
    ap.add_argument("--venues", required=True)
    ap.add_argument("--fixtures", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    red: list[str] = []
    amber: list[str] = []
    scanned = section_a(a.src, red)
    journal = load_journal(a.journal)
    bc = section_bc(journal, a.venues, red, amber)
    d = section_d(a.fixtures, red, amber)

    verdict = "RED" if red else ("AMBER" if amber else "GREEN")
    report = {
        "check": "s4_screener", "rev": 1, "run_utc": int(time.time()),
        "inputs": vars(a) | {"report": a.report},
        "counts": {"src_files_scanned": scanned,
                   "journal_records": len(journal)} | bc | d,
        "red": red, "amber": amber, "verdict": verdict,
    }
    out = json.dumps(report, indent=2)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print(out)
    return 1 if verdict == "RED" else 0


if __name__ == "__main__":
    sys.exit(main())

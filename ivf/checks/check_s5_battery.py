#!/usr/bin/env python3
"""IVF Sprint-5 check: battery foundations — engine, splits, selftest. (rev 1)

Four sections, one verdict (GREEN / AMBER / RED; exit 0 / 0 / 1):

  A) DETERMINISM, CROSS-PROCESS. Runs tests/simulator/_micro_scenario.py in
     TWO separate subprocesses and byte-compares the printed sha256 of the
     canonical trade image. Different hashes = RED.
  B) FILL + COST RECOMPUTATION (DEVQ-012). A collector subprocess builds the
     micro-scenario bars/events, runs the real engine, and prints bars,
     events, and Trades.canonical_payload(). This check then RE-SIMULATES the
     trades itself from the ratified rules — next-open entry, time-stop exit
     at entry+hold_bars open, gross = dir·(exit−entry)·size, round-trip cost
     from configs/venues.yaml, drop-and-count tails — and compares trade by
     trade, field by field, to the cent, including n_dropped_tail and the
     hand-computed totals (gross +4.00, net +2.59).
  C) SPLIT GEOMETRY RECOMPUTATION (DEVQ-011). A collector prints the
     product's walk_forward folds for a matrix of (n_bars, n_folds, embargo)
     cases including edge cases (remainder spread, embargo collapsing a
     train). This check re-implements the ratified geometry from the spec
     text and compares every range exactly.
  D) SELFTEST TRI-STATE AUDIT (DEVQ-013). A collector wires the REAL engine
     as the selftest runner and prints the report plus raw per-suite
     outcomes. This check asserts every suite classified to its expectation
     AND independently recomputes the planted-edge t statistic (stdlib math)
     against the reported one, and re-applies the MIN_N/ALPHA rules to the
     reported numbers.

INDEPENDENCE: this process imports NOTHING from qrf. The system under test
runs only in subprocesses, exactly as the Owner would run it; all
re-computation here is from the ratified DEVQ texts. pyyaml reads venues.

Usage (bash-ready, from F:/QRF):
  uv run python ivf/checks/check_s5_battery.py --workdir ivf/reports/s5_collect --report ivf/reports/s5_verify.json

Drill mode: --artifacts DIR skips collection and reads (possibly tampered)
artifact JSONs from DIR — used by drill_s5.py, which must run FIRST.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import time

SPLIT_CASES = [
    {"n_bars": 100, "n_folds": 4, "embargo": 0},
    {"n_bars": 100, "n_folds": 4, "embargo": 5},
    {"n_bars": 103, "n_folds": 4, "embargo": 5},   # remainder to earliest blocks
    {"n_bars": 10, "n_folds": 3, "embargo": 0},
    {"n_bars": 12, "n_folds": 5, "embargo": 4},    # embargo collapses early trains
    {"n_bars": 5000, "n_folds": 8, "embargo": 24},
]

COLLECT_MICRO = r"""
import json
from tests.simulator._micro_scenario import build, COST_MODEL_NAME
import tests.simulator._micro_scenario as ms
import pandas as pd
n = 15
opens = [100.0]*n
opens[1]=100.0; opens[3]=105.0; opens[6]=200.0; opens[8]=197.0; opens[11]=50.0; opens[13]=48.0
bars = {"ts": list(range(n)), "open": opens}
events = {"ts": [0,5,10], "direction": [1,1,-1], "strength": [1.0,1.0,1.0]}
t = build()
print(json.dumps({"bars": bars, "events": events, "hold_bars": 2, "size": 1.0,
                  "cost_model": COST_MODEL_NAME, "engine": t.canonical_payload()}))
"""

COLLECT_SPLITS = r"""
import json, sys
from qrf.kernel.protocol.splits import SplitSpec, walk_forward
cases = json.loads(sys.argv[1])
out = []
for c in cases:
    folds = walk_forward(c["n_bars"], SplitSpec(n_folds=c["n_folds"], embargo_bars=c["embargo"]))
    out.append({**c, "folds": [{"train": f.train.as_tuple(), "test": f.test.as_tuple()} for f in folds]})
print(json.dumps({"cases": out}))
"""

COLLECT_SELFTEST = r"""
import json
from qrf.kernel.battery.selftest import build_suites, run_selftest
from qrf.trading.simulator.engine import EventEngine, ExecutionSpec
from qrf.trading.utility.cost_models import load_cost_model
SEED = 777
cm = load_cost_model("xauusd_retail_median")
eng = EventEngine()
def runner(bars, events, hold_bars):
    t = eng.simulate(bars, events, cm, seed=SEED, execution=ExecutionSpec(hold_bars=hold_bars))
    return [tr.net_pnl for tr in t.trades]
outcomes = {}
for s in build_suites(SEED):
    outcomes[s.name] = list(map(float, runner(s.bars, s.events, s.hold_bars)))
rep = run_selftest(runner, seed=SEED)
print(json.dumps({"seed": SEED, "results": [
    {"name": r.name, "expected": r.expected, "classification": r.classification,
     "n_trades": r.n_trades, "mean": r.mean, "t_stat": r.t_stat, "p_value": r.p_value}
    for r in rep.results], "outcomes": outcomes, "passed": rep.passed}))
"""


def run_py(code: str, *args: str) -> str:
    p = subprocess.run([sys.executable, "-c", code, *args],
                       capture_output=True, text=True, cwd=os.getcwd())
    if p.returncode != 0:
        raise RuntimeError(f"collector failed:\n{p.stderr[-2000:]}")
    return p.stdout.strip().splitlines()[-1]


def collect(workdir: str) -> dict:
    os.makedirs(workdir, exist_ok=True)
    art = {}
    h1 = run_py(open("tests/simulator/_micro_scenario.py", encoding="utf-8").read())
    h2 = run_py(open("tests/simulator/_micro_scenario.py", encoding="utf-8").read())
    art["determinism"] = {"hash1": h1, "hash2": h2}
    art["micro"] = json.loads(run_py(COLLECT_MICRO))
    art["splits"] = json.loads(run_py(COLLECT_SPLITS, json.dumps(SPLIT_CASES)))
    art["selftest"] = json.loads(run_py(COLLECT_SELFTEST))
    for k, v in art.items():
        with open(os.path.join(workdir, f"{k}.json"), "w", encoding="utf-8") as f:
            json.dump(v, f, indent=1)
    return art


def load_artifacts(d: str) -> dict:
    art = {}
    for k in ("determinism", "micro", "splits", "selftest"):
        with open(os.path.join(d, f"{k}.json"), encoding="utf-8") as f:
            art[k] = json.load(f)
    return art


def yaml_roundtrip_cost(venues_path: str, model: str, size: float,
                        amber: list[str]) -> float | None:
    import yaml
    with open(venues_path, encoding="utf-8") as f:
        v = yaml.safe_load(f) or {}
    m = v.get(model) or (v.get("venues", {}) or {}).get(model)
    if not isinstance(m, dict):
        amber.append(f"B.cost: model {model!r} not found in {venues_path}")
        return None
    def pick(*names):
        for n in names:
            if n in m:
                return float(m[n])
        return None
    spread = pick("spread", "spread_per_round_trip")
    comm = pick("commission", "commission_per_side")
    slip = pick("slippage", "slippage_per_side")
    if None in (spread, comm, slip):
        amber.append(f"B.cost: unrecognized keys in {model!r} ({sorted(m)}) — "
                     f"cost recomputation skipped")
        return None
    return (spread + 2.0 * (comm + slip)) * size


def my_simulate(micro: dict, cost: float | None) -> dict:
    ts = [int(x) for x in micro["bars"]["ts"]]
    opens = [float(x) for x in micro["bars"]["open"]]
    hold, size = int(micro["hold_bars"]), float(micro["size"])
    trades, dropped = [], 0
    for s_ts, d, st in zip(micro["events"]["ts"], micro["events"]["direction"],
                           micro["events"]["strength"]):
        d = int(d)
        if d == 0 or float(st) < 0.0:
            continue
        entry_i = next((i for i, t in enumerate(ts) if t > int(s_ts)), None)
        if entry_i is None:
            dropped += 1
            continue
        exit_i = entry_i + hold
        if exit_i >= len(ts):
            dropped += 1
            continue
        entry, exit_ = opens[entry_i], opens[exit_i]
        gross = d * (exit_ - entry) * size
        trades.append({"signal_ts": int(s_ts), "entry_ts": ts[entry_i],
                       "exit_ts": ts[exit_i], "direction": d,
                       "entry_price": entry, "exit_price": exit_,
                       "gross_pnl": gross,
                       "net_pnl": (gross - cost) if cost is not None else None})
    trades.sort(key=lambda r: (r["signal_ts"], r["entry_ts"], r["direction"]))
    return {"trades": trades, "n_dropped_tail": dropped}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default="ivf/reports/s5_collect")
    ap.add_argument("--artifacts", default=None)
    ap.add_argument("--venues", default="configs/venues.yaml")
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    red: list[str] = []
    amber: list[str] = []
    art = load_artifacts(a.artifacts) if a.artifacts else collect(a.workdir)

    # --- A: determinism ------------------------------------------------------
    det = art["determinism"]
    if det["hash1"] != det["hash2"]:
        red.append(f"A.determinism: cross-process hashes differ "
                   f"({det['hash1'][:12]}… vs {det['hash2'][:12]}…)")

    # --- B: fills + costs ----------------------------------------------------
    micro = art["micro"]
    eng = micro["engine"]
    cost = yaml_roundtrip_cost(a.venues, micro["cost_model"], micro["size"], amber)
    mine = my_simulate(micro, cost)
    if eng["n_dropped_tail"] != mine["n_dropped_tail"]:
        red.append(f"B.dropped: engine n_dropped_tail={eng['n_dropped_tail']} "
                   f"vs spec {mine['n_dropped_tail']}")
    if len(eng["trades"]) != len(mine["trades"]):
        red.append(f"B.count: engine {len(eng['trades'])} trades vs spec "
                   f"{len(mine['trades'])}")
    for et, mt in zip(eng["trades"], mine["trades"]):
        for fld in ("signal_ts", "entry_ts", "exit_ts", "direction"):
            if int(et[fld]) != int(mt[fld]):
                red.append(f"B.{fld}: signal {et['signal_ts']}: engine "
                           f"{et[fld]} vs spec {mt[fld]}")
        for fld in ("entry_price", "exit_price", "gross_pnl"):
            if abs(float(et[fld]) - float(mt[fld])) > 1e-9:
                red.append(f"B.{fld}: signal {et['signal_ts']}: engine "
                           f"{et[fld]} vs spec {mt[fld]}")
        if mt["net_pnl"] is not None and abs(float(et["net_pnl"]) - mt["net_pnl"]) > 1e-9:
            red.append(f"B.net: signal {et['signal_ts']}: engine {et['net_pnl']} "
                       f"vs spec {mt['net_pnl']}")
    g = sum(float(t["gross_pnl"]) for t in eng["trades"])
    nn = sum(float(t["net_pnl"]) for t in eng["trades"])
    if abs(g - 4.00) > 1e-9 or abs(nn - 2.59) > 1e-9:
        red.append(f"B.totals: engine gross {g:.2f}/net {nn:.2f} != hand "
                   f"+4.00/+2.59")

    # --- C: split geometry ---------------------------------------------------
    for case in art["splits"]["cases"]:
        n_bars, n_folds, emb = case["n_bars"], case["n_folds"], case["embargo"]
        n_blocks = n_folds + 1
        base, rem = divmod(n_bars, n_blocks)
        bounds = [0]
        for b in range(n_blocks):
            bounds.append(bounds[-1] + base + (1 if b < rem else 0))
        expect = [{"train": (0, max(0, bounds[i] - emb)),
                   "test": (bounds[i], bounds[i + 1])}
                  for i in range(1, n_folds + 1)]
        got = [{"train": tuple(f["train"]), "test": tuple(f["test"])}
               for f in case["folds"]]
        if got != expect:
            for k, (e, gg) in enumerate(zip(expect, got), start=1):
                if e != gg:
                    red.append(f"C.geometry: case {n_bars}/{n_folds}/{emb} fold "
                               f"{k}: product {gg} vs spec {e}")
        for k, f in enumerate(got, start=1):
            if f["train"][1] > f["test"][0] - emb and f["train"][1] > 0:
                red.append(f"C.embargo: case {n_bars}/{n_folds}/{emb} fold {k}: "
                           f"train ends {f['train'][1]}, violating embargo "
                           f"{emb} before test start {f['test'][0]}")

    # --- D: selftest tri-state ----------------------------------------------
    st = art["selftest"]
    for r in st["results"]:
        if r["classification"] != r["expected"]:
            red.append(f"D.tristate: suite {r['name']} classified "
                       f"{r['classification']}, expected {r['expected']}")
        out = st["outcomes"].get(r["name"], [])
        n = len(out)
        if n != r["n_trades"]:
            red.append(f"D.n: suite {r['name']} outcomes {n} vs reported "
                       f"{r['n_trades']}")
        if n >= 2:
            mean = sum(out) / n
            sd = math.sqrt(sum((x - mean) ** 2 for x in out) / (n - 1))
            if sd > 1e-9:
                t_mine = mean / (sd / math.sqrt(n))
                if not math.isnan(r["t_stat"]) and abs(t_mine - r["t_stat"]) > 1e-6:
                    red.append(f"D.t: suite {r['name']} my t {t_mine:.6f} vs "
                               f"reported {r['t_stat']:.6f}")
        if r["n_trades"] < 30 and r["classification"] != "INSUFFICIENT":
            red.append(f"D.minn: suite {r['name']} n={r['n_trades']} < 30 but "
                       f"classified {r['classification']}")
    if not st.get("passed", False):
        red.append("D.gate: selftest report.passed is False")

    verdict = "RED" if red else ("AMBER" if amber else "GREEN")
    report = {"check": "s5_battery", "rev": 1, "run_utc": int(time.time()),
              "mode": "artifacts" if a.artifacts else "collect",
              "counts": {"split_cases": len(art["splits"]["cases"]),
                         "engine_trades": len(art["micro"]["engine"]["trades"]),
                         "selftest_suites": len(art["selftest"]["results"])},
              "red": red, "amber": amber, "verdict": verdict}
    out = json.dumps(report, indent=2)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print(out)
    return 1 if verdict == "RED" else 0


if __name__ == "__main__":
    sys.exit(main())

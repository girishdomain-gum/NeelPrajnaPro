#!/usr/bin/env python3
"""IVF Sprint-8 check: placebo recomputation + graduation-gate audit. (rev 1)

Five sections, one verdict (GREEN / AMBER / RED; exit 0 / 0 / 1):

  A) MANIFEST-VERIFIED INPUTS. Every parquet handed to this check is
     sha256-verified against its journal bulk_manifest BEFORE use. This
     makes file provenance irrelevant (a worktree path is fine): if the
     bytes hash to the ledger, the file IS the dataset. Any mismatch is
     RED and the file is not consumed.
  B) ANCHOR — the verdicts themselves, re-derived end to end. My OWN
     event construction (FVG per the DEVQ-010 ADDENDUM rule already
     proven in check_s4 rev 3, weekend filter per the GO-S7-ruled scan
     semantics; Monday markers per the DEVQ-005 rev-3 contract) + my
     OWN judge (splits per DEVQ-011 Option A, fills per DEVQ-012 incl.
     dropped tails, pooled one-sided t with a stdlib incomplete-beta
     CDF — verified to ~1e-15 against both recorded p-values before
     this check shipped, deflation per DEVQ-015 prefix rule counted at
     the verdict's journal position) must reproduce EACH verdict:
     n_trades, n_dropped_tail, net total/mean, t, p, per-fold geometry
     and means, effective_alpha, and the tri-state. The anchor is the
     licence for section D: a judge that reproduces the real verdicts
     may be trusted to re-judge the nulls.
  C) H-002 WEEKEND-FILTER AUDIT (ARCH-008 explicit deliverable). My
     weekend-born partition of the full-data FVG events, and the sharp
     end: NO weekend-born event ts may appear among the H-002 trades
     parquet's signal_ts values. The filter's claim is audited against
     the actual trades, not the setup's promise.
  D) PLACEBO RECOMPUTATION (ARCH-008: "recompute the placebo's null
     result independently"). For each placebo_run: regenerate all
     n_runs null twins from the RECORDED (method, seed+i) — the twin
     construction necessarily mirrors the DEVQ-018 ruled algorithms
     call-for-call (RNG-stream equality demands it) — then judge every
     twin with MY judge from section B. The recomputed per-run
     tri-state sequence must equal the recorded ``outcomes`` exactly;
     ``n_pass`` must equal both the recorded outcomes' PASS count and
     my recomputed count; method must be one of the two ruled nulls;
     the promoter's binomial ceiling is recomputed from its ruling
     formula and reported.
  E) GRADUATION / PROMOTION STRUCTURAL AUDIT (ARCH-008: "audit that no
     promotion exists without placebo + second-lens evidence"). All
     four gate legs re-implemented from the ARCH-008 §2 text and
     applied to EVERY promotion record in the journal (today: expected
     zero — reported as a counted fact, since zero promotions is the
     designed state while no second feed exists). Any promotion with a
     failing leg is RED. A second_lens record existing before the
     Owner provides a feed is AMBER (a lens with nothing behind it).
     Placebo non-consumption is re-audited ledger-wide: every verdict
     has exactly one burn, every burn's consumed_by is its verdict,
     and no verdict/burn producer is the placebo.

INDEPENDENCE: no qrf imports; stdlib + pyarrow + numpy (numpy is used
ONLY to reproduce the recorded RNG streams — default_rng(seed) — which
no stdlib generator can replay; every judgement rule is re-implemented
here from the ruling texts).

Usage (paste in git bash, from /f/QRF):
  uv run python ivf/checks/check_s8_graduation_placebo.py --journal datastore/journal/journal.jsonl --bars datastore/bulk/xauusd_h1_full/part-00000.parquet --trades-h002 .claude/worktrees/qrf-architect-handover-cf5806/datastore/bulk/verdict_trades.h002_fvg_intraweek_follow_through/part-00000.parquet --trades-h003 .claude/worktrees/qrf-architect-handover-cf5806/datastore/bulk/verdict_trades.h003_dow_monday_drift/part-00000.parquet --venues configs/venues.yaml --report ivf/reports/s8_verify.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time

NS = 1_000_000_000
DAY = 86_400
_WD_SAT = 5  # weekday() >= 5 is Sat/Sun; epoch day 0 (1970-01-01) = Thursday(3)

H002_LINEAGE = "h002_fvg_intraweek_follow_through"
H003_LINEAGE = "h003_dow_monday_drift"
RULED_METHODS = {"direction_permutation", "entry_time_shuffle"}


# --------------------------------------------------------------------------
# stdlib Student-t one-sided p (regularized incomplete beta, cont. fraction)
# --------------------------------------------------------------------------
def _betacf(a: float, b: float, x: float) -> float:
    MAXIT, EPS, FPMIN = 200, 3e-16, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h


def _betainc_reg(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
          + a * math.log(x) + b * math.log(1.0 - x))
    bt = math.exp(ln)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def one_sided_p(t: float, df: int, mean: float) -> float:
    """One-sided p for H0: mean<=0 from the t statistic (battery convention)."""
    p_two = _betainc_reg(df / 2.0, 0.5, df / (df + t * t))
    return p_two / 2.0 if mean > 0 else 1.0 - p_two / 2.0


# --------------------------------------------------------------------------
# my event constructions (from the ruled contracts, not from product code)
# --------------------------------------------------------------------------
def recompute_fvg(bars: list[dict]) -> list[dict]:
    """DEVQ-010 ADDENDUM rule (check_s4 rev 3): 3-bar gap AND directional
    middle candle; ts = bar 3 (row i+1), close-time basis; bull=+1, bear=-1.
    Returned ts-sorted (at most one event per ts — the two masks are mutually
    exclusive on any real bar triple)."""
    out: list[dict] = []
    for i in range(1, len(bars) - 1):
        hi_prev, lo_prev = float(bars[i - 1]["high"]), float(bars[i - 1]["low"])
        hi_next, lo_next = float(bars[i + 1]["high"]), float(bars[i + 1]["low"])
        o_mid, c_mid = float(bars[i]["open"]), float(bars[i]["close"])
        ts_next = int(bars[i + 1]["ts"])
        if lo_next > hi_prev and c_mid > o_mid:
            out.append({"ts": ts_next, "direction": 1})
        elif hi_next < lo_prev and c_mid < o_mid:
            out.append({"ts": ts_next, "direction": -1})
    out.sort(key=lambda e: e["ts"])
    return out


def infer_timeframe_seconds(ts_list: list[int]) -> int:
    diffs = [(b - a) // NS for a, b in zip(ts_list, ts_list[1:]) if b > a]
    return min(diffs) if diffs else 3600


def spans_weekend(a_ns: int, b_ns: int, tf_seconds: int) -> bool:
    """GO-S7-ruled scan rule (check_s7 §E rev 3, timeframe inferred): the gap
    exceeds one timeframe AND any calendar day from the first endpoint's UTC
    date through the second's (inclusive) is a Sat/Sun."""
    if b_ns - a_ns <= tf_seconds * NS:
        return False
    day = a_ns // NS // DAY
    end = b_ns // NS // DAY
    while day <= end:
        if ((day + 3) % 7) >= _WD_SAT:
            return True
        day += 1
    return False


def weekend_born_flags(bars_ts: list[int], events: list[dict]) -> list[bool]:
    """H-002 setup rule: an FVG (forming bars k-2, k-1, k; ts = bar k) is
    weekend-born iff either adjacent forming-bar gap crosses a weekend."""
    tf = infer_timeframe_seconds(bars_ts)
    index_of = {t: i for i, t in enumerate(bars_ts)}
    flags = []
    for e in events:
        k = index_of.get(int(e["ts"]))
        flags.append(bool(
            k is not None and k >= 2
            and (spans_weekend(bars_ts[k - 2], bars_ts[k - 1], tf)
                 or spans_weekend(bars_ts[k - 1], bars_ts[k], tf))
        ))
    return flags


def monday_markers(bars: list[dict]) -> list[dict]:
    """DEVQ-005 rev-3 contract, Monday lifted to LONG per DEVQ-019: the FIRST
    bar (close-time ts basis) of each new UTC epoch-day whose weekday is
    Monday, direction fixed +1."""
    out: list[dict] = []
    prev_day = None
    for b in bars:
        d0 = int(b["ts"]) // NS // DAY
        if prev_day is not None and d0 != prev_day and ((d0 + 3) % 7) == 0:
            out.append({"ts": int(b["ts"]), "direction": 1})
        prev_day = d0
    out.sort(key=lambda e: e["ts"])
    return out


# --------------------------------------------------------------------------
# my judge (DEVQ-011 Option A splits + DEVQ-012 fills + battery §4.7 stats)
# --------------------------------------------------------------------------
def walk_forward_ranges(n_bars: int, n_folds: int) -> list[tuple[int, int]]:
    """DEVQ-011 Option A: n_folds+1 contiguous near-equal blocks, remainder
    to the EARLIEST blocks; B1..B_{n_folds} are the test blocks."""
    blocks = n_folds + 1
    base, rem = divmod(n_bars, blocks)
    ranges, start = [], 0
    for i in range(blocks):
        size = base + (1 if i < rem else 0)
        ranges.append((start, start + size))
        start += size
    return ranges[1:]  # test blocks only


def run_fold(test_bars: list[dict], events: list[dict], hold: int,
             cost_rt: float) -> tuple[list[float], list[float], int]:
    """DEVQ-012 fills on a single fold's TEST bars: entry at the OPEN of the
    first test bar with ts strictly greater than signal_ts; exit at the OPEN
    of bar entry_index+hold; a trade that cannot open AND close inside the
    block is dropped and counted (never silently trimmed). No stop/target in
    any S8 setup, so the gap-through clauses are vacuous here. Net = gross
    minus the venues.yaml round-trip charge times size (size 1.0)."""
    ts_arr = [int(b["ts"]) for b in test_bars]
    net, gross, dropped = [], [], 0
    for e in events:
        sig = int(e["ts"])
        # first index with ts strictly greater than signal_ts (binary search)
        lo, hi = 0, len(ts_arr)
        while lo < hi:
            mid = (lo + hi) // 2
            if ts_arr[mid] <= sig:
                lo = mid + 1
            else:
                hi = mid
        entry_idx = lo
        if entry_idx >= len(ts_arr):
            dropped += 1
            continue
        exit_idx = entry_idx + hold
        if exit_idx >= len(ts_arr):
            dropped += 1
            continue
        entry = float(test_bars[entry_idx]["open"])
        exit_ = float(test_bars[exit_idx]["open"])
        g = int(e["direction"]) * (exit_ - entry) * 1.0
        gross.append(g)
        net.append(g - cost_rt * 1.0)
    return net, gross, dropped


def pooled_stats(net: list[float]) -> dict:
    """Battery step 6, re-implemented: one-sided t (H0: mean<=0), degenerate
    rule sd <= 1e-12*(|mean|+1) -> p decided on sign (bootstrap CI omitted —
    the tri-state never consumes it)."""
    n = len(net)
    if n == 0:
        return {"n": 0, "mean": None, "stat": None, "p": None}
    mean = sum(net) / n
    if n < 2:
        return {"n": n, "mean": mean, "stat": None,
                "p": 0.0 if mean > 0 else 1.0}
    var = sum((x - mean) ** 2 for x in net) / (n - 1)
    sd = math.sqrt(var)
    if sd <= 1e-12 * (abs(mean) + 1.0):
        return {"n": n, "mean": mean, "stat": None,
                "p": 0.0 if mean > 0 else 1.0}
    t = mean / (sd / math.sqrt(n))
    return {"n": n, "mean": mean, "stat": t, "p": one_sided_p(t, n - 1, mean)}


def tri_state(st: dict, min_n: int, effective_alpha: float) -> str:
    if st["n"] < min_n:
        return "INSUFFICIENT"
    if st["mean"] is not None and st["mean"] > 0 \
            and st["p"] is not None and st["p"] < effective_alpha:
        return "PASS"
    return "FAIL"


def judge(window_bars: list[dict], events: list[dict], *, n_folds: int,
          hold: int, cost_rt: float, min_n: int,
          effective_alpha: float) -> dict:
    """The full §4.7 pipeline steps 4-7, mine: splits -> per-fold TEST-range
    engine (fold events by ts in [first test bar ts, last test bar ts]) ->
    pooled stats -> tri-state at the deflated alpha."""
    ts_col = [int(b["ts"]) for b in window_bars]
    pooled_net: list[float] = []
    pooled_gross: list[float] = []
    folds_out = []
    dropped = 0
    for idx, (t0, t1) in enumerate(walk_forward_ranges(len(window_bars), n_folds)):
        lo, hi = ts_col[t0], ts_col[t1 - 1]
        fold_events = [e for e in events if lo <= int(e["ts"]) <= hi]
        net, gross, d = run_fold(window_bars[t0:t1], fold_events, hold, cost_rt)
        pooled_net += net
        pooled_gross += gross
        dropped += d
        folds_out.append({"index": idx, "n": len(net),
                          "mean": (sum(net) / len(net)) if net else None,
                          "test_start": t0, "test_end": t1})
    st = pooled_stats(pooled_net)
    return {"stats": st, "folds": folds_out, "n_dropped": dropped,
            "net_total": sum(pooled_net), "gross_total": sum(pooled_gross),
            "verdict": tri_state(st, min_n, effective_alpha)}


# --------------------------------------------------------------------------
# null twins from the RECORDED construction (DEVQ-018) — numpy RNG replay
# --------------------------------------------------------------------------
def twin(events: list[dict], window_bar_ts: list[int], method: str,
         seed: int) -> list[dict]:
    import numpy as np
    if method == "direction_permutation":
        rng = np.random.default_rng(int(seed))
        dirs = rng.permutation(
            np.asarray([e["direction"] for e in events]))
        return [{"ts": e["ts"], "direction": int(d)}
                for e, d in zip(events, dirs)]
    if method == "entry_time_shuffle":
        rng = np.random.default_rng(int(seed))
        bar_ts = np.asarray(window_bar_ts, dtype=np.int64)
        n = len(events)
        if n == 0 or bar_ts.size == 0:
            return list(events)
        k = min(n, int(bar_ts.size))
        chosen = np.sort(rng.choice(bar_ts, size=k, replace=False))
        return [{"ts": int(t), "direction": int(e["direction"])}
                for e, t in zip(events[:k], chosen)]
    raise ValueError(f"unruled placebo method {method!r}")


# --------------------------------------------------------------------------
# ledger helpers
# --------------------------------------------------------------------------
def load_journal(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cost_round_trip(venues_path: str, venue: str) -> float:
    """Parse venues.yaml with a deliberate mini-parser (no product yaml
    trust): cost = spread + 2*(slippage_per_side + commission_per_side)."""
    text = open(venues_path, encoding="utf-8").read()
    m = re.search(rf"^  {re.escape(venue)}:\n((?:    .*\n)+)", text, re.M)
    if not m:
        raise SystemExit(f"venue {venue!r} not found in {venues_path}")
    body = m.group(1)

    def num(key: str) -> float:
        mm = re.search(rf"^    {key}:\s*([0-9.]+)", body, re.M)
        if not mm:
            raise SystemExit(f"venue {venue!r} lacks numeric {key!r}")
        return float(mm.group(1))

    return num("spread") + 2.0 * (num("slippage_per_side")
                                  + num("commission_per_side"))


def family_matches(family: str, rec_family, lineage: str) -> bool:
    """DEVQ-015 prefix rule, boundary-safe (as in check_s6)."""
    if rec_family == family:
        return True
    seg = family.split("/", 1)[1] if "/" in family else family
    return lineage == seg or lineage.startswith(seg + ".")


def trials_before(journal: list[dict], family: str, upto_index: int) -> int:
    n = 0
    for r in journal[:upto_index]:
        if r.get("record_type") != "trial_count":
            continue
        p = r["payload"]
        if family_matches(family, p.get("family"), str(p.get("lineage", ""))):
            n += int(p.get("n_attempts", 0))
    return n


def null_pass_ceiling(n_runs: int, effective_alpha: float) -> int:
    """The promoter's ruled formula: mean + 2 binomial sd, floored at 1."""
    expected = effective_alpha * n_runs
    sd = math.sqrt(max(0.0, expected * (1.0 - effective_alpha)))
    return max(1, math.ceil(expected + 2.0 * sd))


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--bars", required=True)
    ap.add_argument("--trades-h002", required=True)
    ap.add_argument("--trades-h003", required=True)
    ap.add_argument("--venues", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    red: list[str] = []
    amber: list[str] = []
    journal = load_journal(a.journal)
    by_id = {r["record_id"]: r for r in journal}
    idx_of = {r["record_id"]: i for i, r in enumerate(journal)}
    manifests = {r["payload"]["dataset"]: r for r in journal
                 if r.get("record_type") == "bulk_manifest"}

    # --- A: manifest-verify every parquet input -----------------------------
    def verify(path: str, dataset: str) -> bool:
        man = manifests.get(dataset)
        if man is None:
            red.append(f"A.manifest: no bulk_manifest for dataset {dataset!r}")
            return False
        want = man["payload"]["file_sha256"]
        got = sha256_file(path)
        if got != want:
            red.append(f"A.hash: {path} sha256 {got[:12]}… != manifest "
                       f"{man['record_id']} {want[:12]}… — file refused")
            return False
        return True

    ok_bars = verify(a.bars, "xauusd_h1_full")
    ok_t2 = verify(a.trades_h002, f"verdict_trades.{H002_LINEAGE}")
    ok_t3 = verify(a.trades_h003, f"verdict_trades.{H003_LINEAGE}")
    if not ok_bars:
        _emit(a, red, amber, {}, hard_fail=True)
        return 1

    import pyarrow.parquet as pq
    bars_full = sorted(pq.read_table(a.bars).to_pylist(),
                       key=lambda r: int(r["ts"]))
    bars_ts_full = [int(b["ts"]) for b in bars_full]

    # --- B: anchors — reproduce each verdict end to end ---------------------
    verdicts = {}
    for v in journal:
        if v.get("record_type") == "verdict":
            hyp = by_id.get(v["payload"]["hypothesis_ref"], {})
            lin = hyp.get("payload", {}).get("lineage", "")
            verdicts[lin] = v
    counts: dict = {"journal_records": len(journal)}

    fvg_events = recompute_fvg(bars_full)
    wk_flags = weekend_born_flags(bars_ts_full, fvg_events)
    h002_events = [e for e, w in zip(fvg_events, wk_flags) if not w]
    h003_events = monday_markers(bars_full)
    counts |= {"fvg_events_recomputed": len(fvg_events),
               "fvg_weekend_born": sum(wk_flags),
               "h002_events_post_filter": len(h002_events),
               "h003_monday_markers": len(h003_events)}

    cost_rt = cost_round_trip(a.venues, "xauusd_retail_median")
    counts["cost_round_trip"] = cost_rt

    anchors = {}
    for lineage, events in ((H002_LINEAGE, h002_events),
                            (H003_LINEAGE, h003_events)):
        v = verdicts.get(lineage)
        if v is None:
            red.append(f"B.verdict: no verdict for lineage {lineage}")
            continue
        p = v["payload"]
        hyp = by_id[p["hypothesis_ref"]]
        hp = hyp["payload"]
        window = by_id[p["window_ref"]]["payload"]
        wb = [b for b in bars_full
              if window["ts_start"] <= int(b["ts"]) < window["ts_end"]]
        # deflation at the verdict's journal position, DEVQ-015 prefix rule
        fam = hp["family"]
        n_tr = trials_before(journal, fam, idx_of[v["record_id"]])
        eff_mine = float(hp["thresholds"]["base_alpha"]) / max(1, n_tr)
        corr = p["corrections"]
        if int(corr["family_m"]) != n_tr:
            red.append(f"B.deflate[{lineage}]: recorded family_m="
                       f"{corr['family_m']} vs my ledger count {n_tr}")
        if abs(float(corr["effective_alpha"]) - eff_mine) > 1e-15:
            red.append(f"B.eff[{lineage}]: recorded "
                       f"{corr['effective_alpha']} vs my {eff_mine}")
        mine = judge(wb, events,
                     n_folds=int(hp["split_spec"]["n_folds"]),
                     hold=int(hp["execution"]["hold_bars"]),
                     cost_rt=cost_rt,
                     min_n=int(hp["thresholds"]["min_n"]),
                     effective_alpha=eff_mine)
        anchors[lineage] = {"hyp": hp, "window_bars": wb, "events": events,
                            "eff": eff_mine, "verdict_rec": v}
        st, rec_st = mine["stats"], p["statistics"]["t_one_sided"]
        if st["n"] != int(p["n_trades"]):
            red.append(f"B.n[{lineage}]: my n={st['n']} vs verdict "
                       f"{p['n_trades']}")
        if mine["n_dropped"] != int(p["n_dropped_tail"]):
            red.append(f"B.dropped[{lineage}]: my {mine['n_dropped']} vs "
                       f"verdict {p['n_dropped_tail']}")
        if abs(mine["net_total"] - float(p["net"]["total"])) > 1e-6:
            red.append(f"B.net_total[{lineage}]: my {mine['net_total']:.6f} "
                       f"vs verdict {p['net']['total']:.6f}")
        if st["mean"] is not None and p["net"]["mean"] is not None \
                and abs(st["mean"] - float(p["net"]["mean"])) > 1e-9:
            red.append(f"B.mean[{lineage}]: my {st['mean']:.9f} vs verdict "
                       f"{p['net']['mean']:.9f}")
        if st["stat"] is not None and rec_st["stat"] is not None \
                and abs(st["stat"] - float(rec_st["stat"])) > 1e-6:
            red.append(f"B.t[{lineage}]: my {st['stat']:.6f} vs verdict "
                       f"{rec_st['stat']:.6f}")
        if st["p"] is not None and rec_st["p"] is not None \
                and abs(st["p"] - float(rec_st["p"])) > 1e-9:
            red.append(f"B.p[{lineage}]: my {st['p']:.9f} vs verdict "
                       f"{rec_st['p']:.9f}")
        if mine["verdict"] != p["verdict"]:
            red.append(f"B.tristate[{lineage}]: my {mine['verdict']} vs "
                       f"verdict {p['verdict']}")
        for mf, rf in zip(mine["folds"], p.get("folds", [])):
            if (mf["test_start"], mf["test_end"]) != \
                    (int(rf["test_start"]), int(rf["test_end"])):
                red.append(f"B.fold{mf['index']}[{lineage}]: my geometry "
                           f"({mf['test_start']},{mf['test_end']}) vs "
                           f"({rf['test_start']},{rf['test_end']})")
            if mf["n"] != int(rf["n_trades"]):
                red.append(f"B.fold{mf['index']}n[{lineage}]: my {mf['n']} "
                           f"vs {rf['n_trades']}")
            if mf["mean"] is not None and rf["mean_net"] is not None \
                    and abs(mf["mean"] - float(rf["mean_net"])) > 1e-9:
                red.append(f"B.fold{mf['index']}mean[{lineage}]: my "
                           f"{mf['mean']:.9f} vs {rf['mean_net']:.9f}")
        counts[f"anchor_{lineage}"] = {
            "n": st["n"], "verdict_mine": mine["verdict"],
            "verdict_recorded": p["verdict"], "effective_alpha": eff_mine}

    # --- C: weekend-filter audit against the actual H-002 trades ------------
    if ok_t2 and H002_LINEAGE in anchors:
        rows = pq.read_table(a.trades_h002).to_pylist()
        wk_ts = {e["ts"] for e, w in zip(fvg_events, wk_flags) if w}
        leaked = sorted({int(r["signal_ts"]) for r in rows} & wk_ts)
        counts["h002_trades_rows"] = len(rows)
        counts["h002_weekend_leaks"] = len(leaked)
        for t in leaked[:5]:
            red.append(f"C.leak: weekend-born event ts {t} produced an H-002 "
                       f"trade — the setup filter failed on it")
        if len(leaked) > 5:
            red.append(f"C.leak: … and {len(leaked) - 5} more")
        if not rows:
            amber.append("C.vacuous: H-002 trades parquet is empty — the "
                         "leak audit inspected nothing")

    # --- D: placebo recomputation from the recorded seeds -------------------
    placebos = [r for r in journal if r.get("record_type") == "placebo_run"]
    if not placebos:
        amber.append("D.vacuous: ZERO placebo_run records — nothing "
                     "recomputed (AMBER by rule)")
    for pr in placebos:
        pp = pr["payload"]
        pid = pr["record_id"]
        hyp = by_id.get(pp.get("hypothesis_ref", ""))
        lineage = (hyp or {}).get("payload", {}).get("lineage", "?")
        if pp.get("method") not in RULED_METHODS:
            red.append(f"D.method: placebo {pid} method {pp.get('method')!r} "
                       f"is not a DEVQ-018 ruled null")
            continue
        outcomes = pp.get("outcomes", [])
        if len(outcomes) != int(pp.get("n_runs", -1)):
            red.append(f"D.len: placebo {pid} has {len(outcomes)} outcomes "
                       f"but n_runs={pp.get('n_runs')}")
        if sum(1 for o in outcomes if o == "PASS") != int(pp.get("n_pass", -1)):
            red.append(f"D.count: placebo {pid} n_pass={pp.get('n_pass')} "
                       f"but outcomes contain "
                       f"{sum(1 for o in outcomes if o == 'PASS')} PASS")
        if lineage not in anchors:
            red.append(f"D.anchor: placebo {pid} lineage {lineage} has no "
                       f"validated anchor — cannot recompute")
            continue
        anc = anchors[lineage]
        wb_ts = [int(b["ts"]) for b in anc["window_bars"]]
        hp = anc["hyp"]
        mine_outcomes = []
        for i in range(int(pp["n_runs"])):
            tw = twin(anc["events"], wb_ts, pp["method"],
                      int(pp["seed"]) + i)
            res = judge(anc["window_bars"], tw,
                        n_folds=int(hp["split_spec"]["n_folds"]),
                        hold=int(hp["execution"]["hold_bars"]),
                        cost_rt=cost_rt,
                        min_n=int(hp["thresholds"]["min_n"]),
                        effective_alpha=anc["eff"])
            mine_outcomes.append(res["verdict"])
        if mine_outcomes != list(outcomes):
            diff = [i for i, (m, r) in enumerate(zip(mine_outcomes, outcomes))
                    if m != r]
            red.append(f"D.recompute: placebo {pid} ({lineage}) — my "
                       f"outcomes differ from recorded at runs {diff[:8]} "
                       f"(mine n_pass="
                       f"{sum(1 for o in mine_outcomes if o == 'PASS')}, "
                       f"recorded n_pass={pp.get('n_pass')})")
        ceiling = null_pass_ceiling(int(pp["n_runs"]), anc["eff"])
        counts[f"placebo_{lineage}"] = {
            "record": pid, "method": pp["method"],
            "n_pass_recorded": pp.get("n_pass"),
            "n_pass_mine": sum(1 for o in mine_outcomes if o == "PASS"),
            "promoter_ceiling": ceiling,
            "within_ceiling": int(pp.get("n_pass", 0)) <= ceiling}

    # --- E: graduation / promotion structural audit -------------------------
    promotions = [r for r in journal if r.get("record_type") == "promotion"]
    lenses = [r for r in journal if r.get("record_type") == "second_lens"]
    counts["promotions_found"] = len(promotions)
    counts["second_lens_found"] = len(lenses)
    if lenses:
        amber.append(f"E.lens: {len(lenses)} second_lens record(s) exist but "
                     f"no Owner-provided feed does — verify their provenance")
    for pm in promotions:
        pp = pm["payload"]
        pid = pm["record_id"]

        def _leg(ref_key: str, want_type: str) -> dict | None:
            rec = by_id.get(pp.get(ref_key, ""))
            if rec is None or rec.get("record_type") != want_type:
                red.append(f"E.{ref_key}: promotion {pid} {ref_key}="
                           f"{pp.get(ref_key)!r} does not resolve to a "
                           f"{want_type}")
                return None
            return rec

        v = _leg("verdict_ref", "verdict")
        if v is not None:
            if v["payload"].get("verdict") != "PASS":
                red.append(f"E.gate-a: promotion {pid} cites verdict "
                           f"{pp['verdict_ref']} with tri-state "
                           f"{v['payload'].get('verdict')} — only PASS "
                           f"promotes")
            if v["payload"].get("hypothesis_ref") != pp.get("hypothesis_ref"):
                red.append(f"E.gate-a: promotion {pid} verdict is of a "
                           f"different hypothesis")
        pb = _leg("placebo_ref", "placebo_run")
        if pb is not None and v is not None:
            if pb["payload"].get("hypothesis_ref") != pp.get("hypothesis_ref"):
                red.append(f"E.gate-b: promotion {pid} placebo is of a "
                           f"different hypothesis")
            eff = float(v["payload"]["corrections"]["effective_alpha"])
            ceil_ = null_pass_ceiling(int(pb["payload"]["n_runs"]), eff)
            if int(pb["payload"]["n_pass"]) > ceil_:
                red.append(f"E.gate-b: promotion {pid} placebo n_pass="
                           f"{pb['payload']['n_pass']} > ceiling {ceil_}")
        ln = _leg("second_lens_ref", "second_lens")
        if ln is not None:
            om = by_id.get(ln["payload"].get("overlap_manifest", ""))
            if om is None or om.get("record_type") != "bulk_manifest":
                red.append(f"E.gate-c: promotion {pid} second_lens overlap "
                           f"does not resolve to a bulk_manifest")
        bl = _leg("belief_ref", "belief")
        if bl is not None:
            bp = bl["payload"]
            if bp.get("family") != pp.get("family") \
                    or bp.get("claim") != pp.get("claim"):
                red.append(f"E.gate-d: promotion {pid} belief is for a "
                           f"different (family, claim)")
            if pp.get("verdict_ref") not in bp.get("verdict_refs", []):
                red.append(f"E.gate-d: promotion {pid} belief does not cite "
                           f"its verdict")
            if bp.get("stance") == "CONTESTED":
                red.append(f"E.gate-d: promotion {pid} belief is CONTESTED")

    # placebo non-consumption, ledger-wide
    all_verdicts = [r for r in journal if r.get("record_type") == "verdict"]
    all_burns = [r for r in journal if r.get("record_type") == "window_burn"]
    for r in all_verdicts + all_burns:
        if "placebo" in str(r.get("producer", "")).lower():
            red.append(f"E.producer: {r['record_type']} {r['record_id']} "
                       f"produced by {r['producer']!r} — the placebo may "
                       f"write neither")
    burn_by_verdict = {}
    for b in all_burns:
        burn_by_verdict.setdefault(b["payload"].get("consumed_by"), []).append(b)
    for v in all_verdicts:
        mine_b = burn_by_verdict.get(v["record_id"], [])
        if len(mine_b) != 1:
            red.append(f"E.burn: verdict {v['record_id']} has {len(mine_b)} "
                       f"burns consumed_by it — exactly 1 required")
    counts["verdicts_total"] = len(all_verdicts)
    counts["burns_total"] = len(all_burns)

    return _emit(a, red, amber, counts)


def _emit(a, red, amber, counts, hard_fail: bool = False) -> int:
    verdict = "RED" if red else ("AMBER" if amber else "GREEN")
    report = {"check": "s8_graduation_placebo", "rev": 1,
              "run_utc": int(time.time()), "counts": counts,
              "red": red, "amber": amber, "verdict": verdict}
    out = json.dumps(report, indent=2)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print(out)
    return 1 if verdict == "RED" else 0


if __name__ == "__main__":
    sys.exit(main())

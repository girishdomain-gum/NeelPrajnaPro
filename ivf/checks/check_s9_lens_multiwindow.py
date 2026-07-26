#!/usr/bin/env python3
"""IVF Sprint-9 check: multi-window anchor + lens recomputation + audits. (rev 1)

Six sections, one verdict (GREEN / AMBER / RED; exit 0 / 0 / 1):

  A) MANIFEST-VERIFIED INPUTS. Every parquet consumed is sha256-verified
     against its journal bulk_manifest first (rebuild them via the §1
     scripts if absent — that debt is paid; nothing is hand-copied).
  B) H-004 ANCHOR — the verdict re-derived end to end with MY machinery:
     Monday markers per the DEVQ-005 rev-3 contract computed on the
     CONTINUOUS primary series; window slices per the ledger's window
     records; DEVQ-011-A fold geometry PER WINDOW over the concatenation
     (the seam a hard boundary, per DEVQ-022); DEVQ-012 fills with the
     ARCH-009 CALENDAR-DAY exit re-implemented from the fills-module
     normative docstring (same epoch-day walk, hold cap, drop on
     truncation or unconfirmed day-end); pooled one-sided t via the
     stdlib incomplete-beta CDF (verified to ~1e-15 in S8); DEVQ-015
     family deflation counted at the verdict's journal position; and the
     bootstrap CI replayed from the recorded engine seed via numpy
     default_rng. Every recorded number must match: n, tail drops, HOLE
     drops (recomputed structurally per the DEVQ-022 seam rule), net
     totals/means, t, p, CI bounds, all 8 folds' geometry+n+means,
     effective alpha, tri-state.
  C) PLACEBO REPLAY — all 20 entry_time_shuffle twins regenerated from
     the recorded (seed+i) over the UNION bar timestamps (the exact bars
     the judge passed) and re-judged with MY judge; the tri-state
     sequence must equal the recorded outcomes exactly.
  D) SECOND-LENS RECOMPUTATION — the sealed DEVQ-023 correction-note
     procedure re-implemented from ITS text and re-run over the raw
     feeds: weekly coarse scan, run-length flip detection (K=2,
     absorb-into-preceding, same-shift coalescing), local hour
     refinement, agreement-rate discriminator with the count sanity
     floor and the two-part + prediction guards, reserves excluded by ts
     range. My chosen shifts, era tables, detected boundaries, and the
     POOLED n_overlap / n_agree / agreement_rate are compared against
     the recorded second_lens (pooled figures exactly; per-era figures
     and boundary instants against the record's own notes tables, with
     boundary ties inside bar-free gaps treated as compliant if the
     resulting bar partition is identical).
  E) ORDERING AUDIT (DEVQ-020, the sprint's soul): the sealed correction
     note must precede the overlap manifest, which must precede the
     second_lens, in JOURNAL CHAIN POSITION; the lens must parent both;
     the overlap parquet must contain zero reserve timestamps and
     exactly its manifest's rows.
  F) STRUCTURE + ENFORCEMENT — one window_burn per window_ref of every
     verdict (v3: one per union member); §2 audit: any hypothesis with a
     sealed placebo_method must have every placebo_run agree with it
     (Wave-1 grandfathered per ARCH-008 §3 claim-type assignment);
     promotions re-audited per the S8 four-leg rule (still expected 0).

INDEPENDENCE: no qrf imports; stdlib + pyarrow + numpy (numpy ONLY for
RNG replay of the recorded shuffle seeds and the bootstrap CI). Every
judgement and alignment rule is re-implemented from the ruling / sealed
note texts, never from product code.

Usage (paste in git bash, from /f/QRF, after rebuilding parquets):
  uv run python ivf/checks/check_s9_lens_multiwindow.py --journal datastore/journal/journal.jsonl --bars-primary datastore/bulk/xauusd_h1_primary_full/part-00000.parquet --bars-second datastore/bulk/xauusd_h1_secondfeed/part-00000.parquet --trades-h004 datastore/bulk/verdict_trades.h004_dow_monday_drift_v2/part-00000.parquet --overlap datastore/bulk/xauusd_h1_overlap_lens/part-00000.parquet --venues configs/venues.yaml --report ivf/reports/s9_verify.json
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
NS_DAY = 86_400_000_000_000
H004 = "h004_dow_monday_drift_v2"
RULED_METHODS = {"direction_permutation", "entry_time_shuffle"}
CANDIDATES_H = [0, -1, -2, -3, 1, 2, 3]  # sealed order irrelevant; tie-break rules below
TOL = {"open": 0.50, "close": 0.50, "high": 0.75, "low": 0.75}
WEEK_NS = 7 * NS_DAY
K_MIN_RUN = 2


# ---------------------------------------------------------------- stdlib t
def _betacf(a, b, x):
    MAXIT, EPS, FPMIN = 200, 3e-16, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = FPMIN if abs(d) < FPMIN else d
        c = 1.0 + aa / c
        c = FPMIN if abs(c) < FPMIN else c
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = FPMIN if abs(d) < FPMIN else d
        c = 1.0 + aa / c
        c = FPMIN if abs(c) < FPMIN else c
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h


def _betainc(a, b, x):
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


def one_sided_p(t, df, mean):
    p2 = _betainc(df / 2.0, 0.5, df / (df + t * t))
    return p2 / 2.0 if mean > 0 else 1.0 - p2 / 2.0


# ------------------------------------------------------- events + windows
def monday_markers(bars):
    """DEVQ-005 rev-3: first bar (close-ts basis) of each new UTC epoch-day
    that is a Monday, computed on the CONTINUOUS series; direction +1."""
    out, prev = [], None
    for b in bars:
        d = int(b["ts"]) // NS_DAY
        if prev is not None and d != prev and ((d + 3) % 7) == 0:
            out.append({"ts": int(b["ts"]), "direction": 1})
        prev = d
    return out


def window_slice(bars, w):
    lo, hi = int(w["ts_start"]), int(w["ts_end"])
    return [b for b in bars if lo <= int(b["ts"]) < hi]


# --------------------------------------------------- my multi-window judge
def walk_forward_ranges(n_bars, n_folds):
    blocks = n_folds + 1
    base, rem = divmod(n_bars, blocks)
    out, start = [], 0
    for i in range(blocks):
        size = base + (1 if i < rem else 0)
        out.append((start, start + size))
        start += size
    return out[1:]


def multi_ranges(window_lengths, n_folds):
    """DEVQ-022: per-window DEVQ-011-A folds over the concatenation; the seam
    a hard boundary; fold indices continuous across windows starting at 1."""
    folds, off, idx = [], 0, 1
    for ln in window_lengths:
        for (a, b) in walk_forward_ranges(ln, n_folds):
            folds.append({"index": idx, "t0": off + a, "t1": off + b})
            idx += 1
        off += ln
    return folds


def calendar_exit_index(entry_idx, ts, hold):
    """fills.py normative rule: last bar sharing the entry's epoch-day;
    None (drop) if the day exceeds the hold cap or ends unconfirmed."""
    n = len(ts)
    if entry_idx >= n:
        return None
    day = ts[entry_idx] // NS_DAY
    cap = entry_idx + hold
    j = entry_idx
    while j + 1 < n and (ts[j + 1] // NS_DAY) == day:
        if j + 1 > cap:
            return None
        j += 1
    if j + 1 >= n:
        return None
    return j


def run_fold_calendar(test_bars, events, hold, cost_rt):
    ts = [int(b["ts"]) for b in test_bars]
    net, gross, dropped, rows = [], [], 0, []
    for e in events:
        sig = int(e["ts"])
        lo, hi = 0, len(ts)
        while lo < hi:
            mid = (lo + hi) // 2
            if ts[mid] <= sig:
                lo = mid + 1
            else:
                hi = mid
        ei = lo
        if ei >= len(ts):
            dropped += 1
            continue
        xi = calendar_exit_index(ei, ts, hold)
        if xi is None:
            dropped += 1
            continue
        entry = float(test_bars[ei]["open"])
        exit_ = float(test_bars[xi]["open"])
        g = int(e["direction"]) * (exit_ - entry) * 1.0
        gross.append(g)
        net.append(g - cost_rt)
        rows.append({"signal_ts": sig, "entry_ts": ts[ei], "exit_ts": ts[xi]})
    return net, gross, dropped, rows


def pooled_stats(net):
    n = len(net)
    if n == 0:
        return {"n": 0, "mean": None, "stat": None, "p": None}
    mean = sum(net) / n
    if n < 2:
        return {"n": n, "mean": mean, "stat": None, "p": 0.0 if mean > 0 else 1.0}
    var = sum((x - mean) ** 2 for x in net) / (n - 1)
    sd = math.sqrt(var)
    if sd <= 1e-12 * (abs(mean) + 1.0):
        return {"n": n, "mean": mean, "stat": None, "p": 0.0 if mean > 0 else 1.0}
    t = mean / (sd / math.sqrt(n))
    return {"n": n, "mean": mean, "stat": t, "p": one_sided_p(t, n - 1, mean)}


def judge_multi(window_bar_lists, events, *, n_folds, hold, cost_rt, min_n, eff):
    union = [b for wb in window_bar_lists for b in wb]
    ts_col = [int(b["ts"]) for b in union]
    folds = multi_ranges([len(wb) for wb in window_bar_lists], n_folds)
    pooled_net, pooled_gross, dropped, fold_out, trade_rows = [], [], 0, [], []
    for f in folds:
        t0, t1 = f["t0"], f["t1"]
        lo, hi = ts_col[t0], ts_col[t1 - 1]
        fe = [e for e in events if lo <= int(e["ts"]) <= hi]
        net, gross, d, rows = run_fold_calendar(union[t0:t1], fe, hold, cost_rt)
        pooled_net += net
        pooled_gross += gross
        dropped += d
        trade_rows += rows
        fold_out.append({"index": f["index"], "n": len(net),
                         "mean": (sum(net) / len(net)) if net else None,
                         "test_start": t0, "test_end": t1})
    st = pooled_stats(pooled_net)
    if st["n"] < min_n:
        tri = "INSUFFICIENT"
    elif st["mean"] is not None and st["mean"] > 0 and st["p"] is not None \
            and st["p"] < eff:
        tri = "PASS"
    else:
        tri = "FAIL"
    return {"stats": st, "folds": fold_out, "dropped": dropped,
            "net_total": sum(pooled_net), "gross_total": sum(pooled_gross),
            "gross_mean": (sum(pooled_gross) / len(pooled_gross)) if pooled_gross else None,
            "pooled_net": pooled_net, "verdict": tri, "trade_rows": trade_rows}


def hole_drops(window_bar_lists, events_by_window, hold, cost_rt):
    """DEVQ-022 seam rule as recorded in the battery contract: for every
    window EXCEPT the last, run over that window's OWN bars with its own
    events; its tail drops are seam/hole drops."""
    total = 0
    for wb, ev in zip(window_bar_lists[:-1], events_by_window[:-1]):
        _, _, d, _ = run_fold_calendar(wb, ev, hold, cost_rt)
        total += d
    return total


# -------------------------------------------------------------- lens core
def agree(pb, sb):
    return (abs(pb["open"] - sb["open"]) <= TOL["open"]
            and abs(pb["close"] - sb["close"]) <= TOL["close"]
            and abs(pb["high"] - sb["high"]) <= TOL["high"]
            and abs(pb["low"] - sb["low"]) <= TOL["low"])


def shift_tables(train_bars, second_by_ts, lo_ts, hi_ts):
    """Per candidate shift over train bars with ts in [lo_ts, hi_ts):
    (n_shared, n_agree)."""
    out = {}
    for h in CANDIDATES_H:
        dh = h * 3600 * NS
        n = a = 0
        for pb in train_bars:
            t = int(pb["ts"])
            if not (lo_ts <= t < hi_ts):
                continue
            sb = second_by_ts.get(t + dh)
            if sb is None:
                continue
            n += 1
            if agree(pb, sb):
                a += 1
        out[h] = (n, a)
    return out


def window_winner(tbl):
    """Sealed tie-break: max agreement rate; ties → smaller |h|, then more
    negative h."""
    best = None
    for h, (n, a) in tbl.items():
        r = (a / n) if n else 0.0
        key = (-r, abs(h), h)  # more-negative h wins the final tie via h asc
        if best is None or key < best[0]:
            best = (key, h)
    return best[1]


def coarse_eras(train_bars, second_by_ts, anchor_ts, end_ts):
    """Sealed (a)+(b): weekly windows anchored at the first training bar;
    per-window winner; RLE with K=2 absorb-into-preceding + same-shift
    coalescing. Returns list of (start_ts, end_ts, shift) candidate eras."""
    winners = []  # (win_start, win_end, shift) for non-empty windows
    t = anchor_ts
    while t < end_ts:
        w_end = t + WEEK_NS
        tbl = shift_tables(train_bars, second_by_ts, t, min(w_end, end_ts))
        n_any = sum(n for (n, _a) in tbl.values())
        if n_any > 0:
            winners.append((t, min(w_end, end_ts), window_winner(tbl)))
        t = w_end
    # RLE
    runs = []
    for w in winners:
        if runs and runs[-1]["shift"] == w[2]:
            runs[-1]["end"] = w[1]
            runs[-1]["count"] += 1
        else:
            runs.append({"start": w[0], "end": w[1], "shift": w[2], "count": 1})
    # absorb sub-K runs into the PRECEDING era, then coalesce same-shift
    out = []
    for r in runs:
        if r["count"] < K_MIN_RUN and out:
            out[-1]["end"] = r["end"]
        elif out and out[-1]["shift"] == r["shift"]:
            out[-1]["end"] = r["end"]
        else:
            out.append(dict(r))
    return [(r["start"], r["end"], r["shift"]) for r in out]


def refine_boundary(train_bars, second_by_ts, a_shift, b_shift, lo_ts, hi_ts):
    """Sealed (c): choose the H1 cut c in the bracket (bar ts values, plus one
    hour past the last) maximizing total agreements with ts<c scored under
    a_shift and ts>=c under b_shift. Ties are possible when the true switch
    sits in a bar-free gap; ALL maximizing cuts are recorded (the caller
    treats any recorded instant inside the tie-set as compliant)."""
    bracket = [int(b["ts"]) for b in train_bars if lo_ts <= int(b["ts"]) < hi_ts]
    if not bracket:
        return [lo_ts]
    cands = bracket + [bracket[-1] + 3600 * NS]
    da, db = a_shift * 3600 * NS, b_shift * 3600 * NS

    def scored(t, dh):
        sb = second_by_ts.get(t + dh)
        pb = _bars_by_ts.get(t)
        return 1 if (sb is not None and pb is not None and agree(pb, sb)) else 0

    global _bars_by_ts
    _bars_by_ts = {int(b["ts"]): b for b in train_bars}
    # prefix sums under A, suffix under B
    a_sc = [scored(t, da) for t in bracket]
    b_sc = [scored(t, db) for t in bracket]
    best_total, ties = -1, []
    for ci, c in enumerate(cands):
        # bars < c under A: indices [0, ci); bars >= c under B: [ci, end)
        total = sum(a_sc[:ci]) + sum(b_sc[ci:])
        if total > best_total:
            best_total, ties = total, [c]
        elif total == best_total:
            ties.append(c)
    return ties


def run_lens(primary_bars, second_bars, windows_train, reserves):
    """The full sealed procedure. Returns eras with tables, boundaries
    (tie-sets), pooled figures, and guard results."""
    res_ranges = [(int(a), int(b)) for (a, b) in reserves]

    def in_reserve(t):
        return any(lo <= t < hi for (lo, hi) in res_ranges)

    train = [b for w in windows_train for b in window_slice(primary_bars, w)]
    train = [b for b in train if not in_reserve(int(b["ts"]))]
    train.sort(key=lambda b: int(b["ts"]))
    second_by_ts = {int(b["ts"]): b for b in second_bars}

    anchor = int(train[0]["ts"])
    end = int(train[-1]["ts"]) + 1
    eras = coarse_eras(train, second_by_ts, anchor, end)

    # refine boundaries between consecutive eras
    boundaries = []  # list of tie-set lists
    refined = []
    prev_cut = anchor
    for i, (s, e, h) in enumerate(eras):
        if i + 1 < len(eras):
            nxt = eras[i + 1]
            ties = refine_boundary(train, second_by_ts, h, nxt[2], s, nxt[1])
            boundaries.append(ties)
            cut = ties[0]
            refined.append((prev_cut, cut, h))
            prev_cut = cut
        else:
            refined.append((prev_cut, end, h))

    era_rows = []
    pooled_n = pooled_a = 0
    guard_fail = []
    for (s, e, h) in refined:
        tbl = shift_tables(train, second_by_ts, s, e)
        n, a = tbl[h]
        r = (a / n) if n else 0.0
        rates = sorted(((aa / nn) if nn else 0.0, hh)
                       for hh, (nn, aa) in tbl.items())
        runner = [x for x in rates if x[1] != h][-1][0]
        max_count = max(nn for (nn, _aa) in tbl.values())
        floor_ok = n >= 0.90 * max_count
        three_ok = (runner == 0 and r > 0) or (runner > 0 and r >= 3 * runner)
        abs_ok = r >= 0.80
        if not floor_ok:
            guard_fail.append(f"era[{s}] count floor")
        if not three_ok:
            guard_fail.append(f"era[{s}] 3x guard")
        if not abs_ok:
            guard_fail.append(f"era[{s}] 0.80 guard")
        pooled_n += n
        pooled_a += a
        era_rows.append({"start": s, "end": e, "shift": h, "n": n, "agree": a,
                         "rate": r, "table": {str(k): v for k, v in tbl.items()}})
    winter = [er["rate"] for er in era_rows if er["shift"] == -2]
    if winter and min(winter) < 0.90:
        guard_fail.append("prediction guard: min winter < 0.90")
    return {"eras": era_rows, "boundaries": boundaries,
            "n_overlap": pooled_n, "n_agree": pooled_a,
            "rate": (pooled_a / pooled_n) if pooled_n else 0.0,
            "guard_failures": guard_fail}


# ---------------------------------------------------------------- ledger
def load_journal(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cost_round_trip(venues_path, venue):
    text = open(venues_path, encoding="utf-8").read()
    m = re.search(rf"^  {re.escape(venue)}:\n((?:    .*\n)+)", text, re.M)
    if not m:
        raise SystemExit(f"venue {venue!r} not found")
    body = m.group(1)

    def num(key):
        mm = re.search(rf"^    {key}:\s*([0-9.]+)", body, re.M)
        if not mm:
            raise SystemExit(f"venue lacks {key!r}")
        return float(mm.group(1))

    return num("spread") + 2.0 * (num("slippage_per_side") + num("commission_per_side"))


def family_matches(family, rec_family, lineage):
    if rec_family == family:
        return True
    seg = family.split("/", 1)[1] if "/" in family else family
    return lineage == seg or lineage.startswith(seg + ".")


def trials_before(journal, family, upto):
    n = 0
    for r in journal[:upto]:
        if r.get("record_type") != "trial_count":
            continue
        p = r["payload"]
        if family_matches(family, p.get("family"), str(p.get("lineage", ""))):
            n += int(p.get("n_attempts", 0))
    return n


# ------------------------------------------------------------------ main
def run_check(journal, primary_bars, second_bars, *, cost_rt,
              trades_rows=None, overlap_rows=None, verified=None):
    """Sections B-F over already-loaded frames. ``verified`` maps input names
    to bool (section A results); pure so the drill and rehearsal can drive it."""
    red, amber = [], []
    counts = {"journal_records": len(journal)}
    by = {r["record_id"]: r for r in journal}
    idx = {r["record_id"]: i for i, r in enumerate(journal)}

    hyp = next((r for r in journal if r.get("record_type") == "hypothesis"
                and r["payload"].get("lineage") == H004), None)
    if hyp is None:
        red.append("B.hyp: no H-004 hypothesis record")
        return red, amber, counts
    hp = hyp["payload"]
    verdict = next((r for r in journal if r.get("record_type") == "verdict"
                    and r["payload"].get("hypothesis_ref") == hyp["record_id"]), None)
    placebo = next((r for r in journal if r.get("record_type") == "placebo_run"
                    and r["payload"].get("hypothesis_ref") == hyp["record_id"]), None)
    if verdict is None or placebo is None:
        red.append("B.records: H-004 verdict or placebo missing")
        return red, amber, counts
    vp = verdict["payload"]

    windows = [by[w]["payload"] for w in hp["window_refs"]]
    wbs = [window_slice(primary_bars, w) for w in windows]
    counts["window_bars"] = [len(wb) for wb in wbs]

    markers = monday_markers(primary_bars)
    ev = [e for e in markers
          if any(int(w["ts_start"]) <= e["ts"] < int(w["ts_end"]) for w in windows)]
    counts["monday_markers_full"] = len(markers)
    counts["monday_markers_union"] = len(ev)

    n_tr = trials_before(journal, hp["family"], idx[verdict["record_id"]])
    eff = float(hp["thresholds"]["base_alpha"]) / max(1, n_tr)
    corr = vp["corrections"]
    if int(corr["family_m"]) != n_tr:
        red.append(f"B.deflate: recorded family_m={corr['family_m']} vs mine {n_tr}")
    if abs(float(corr["effective_alpha"]) - eff) > 1e-15:
        red.append(f"B.eff: recorded {corr['effective_alpha']} vs mine {eff}")

    mine = judge_multi(wbs, ev, n_folds=int(hp["split_spec"]["n_folds"]),
                       hold=int(hp["execution"]["hold_bars"]), cost_rt=cost_rt,
                       min_n=int(hp["thresholds"]["min_n"]), eff=eff)
    st = mine["stats"]
    rec_st = vp["statistics"]["t_one_sided"]
    checks = [
        ("n", st["n"], int(vp["n_trades"]), 0),
        ("dropped_tail", mine["dropped"], int(vp["n_dropped_tail"]), 0),
        ("net_total", mine["net_total"], float(vp["net"]["total"]), 1e-6),
        ("net_mean", st["mean"], float(vp["net"]["mean"]), 1e-9),
        ("gross_total", mine["gross_total"], float(vp["gross"]["total"]), 1e-6),
        ("t", st["stat"], float(rec_st["stat"]), 1e-6),
        ("p", st["p"], float(rec_st["p"]), 1e-9),
    ]
    for name, a, b, tol in checks:
        bad = (a is None) != (b is None) or (
            a is not None and (abs(a - b) > tol if tol else a != b))
        if bad:
            red.append(f"B.{name}: mine {a} vs verdict {b}")
    if mine["verdict"] != vp["verdict"]:
        red.append(f"B.tristate: mine {mine['verdict']} vs verdict {vp['verdict']}")
    for mf, rf in zip(mine["folds"], vp.get("folds", [])):
        if (mf["index"], mf["test_start"], mf["test_end"], mf["n"]) != \
                (int(rf["index"]), int(rf["test_start"]), int(rf["test_end"]),
                 int(rf["n_trades"])):
            red.append(f"B.fold{mf['index']}: geometry/n mismatch "
                       f"mine=({mf['test_start']},{mf['test_end']},{mf['n']}) "
                       f"rec=({rf['test_start']},{rf['test_end']},{rf['n_trades']})")
        elif mf["mean"] is not None and rf["mean_net"] is not None and \
                abs(mf["mean"] - float(rf["mean_net"])) > 1e-9:
            red.append(f"B.fold{mf['index']}mean: {mf['mean']} vs {rf['mean_net']}")
    if len(mine["folds"]) != len(vp.get("folds", [])):
        red.append(f"B.folds: mine {len(mine['folds'])} vs {len(vp.get('folds', []))}")

    # hole drops per the seam rule
    ev_by_w = [[e for e in ev
                if int(w["ts_start"]) <= e["ts"] < int(w["ts_end"])]
               for w in windows]
    hole = hole_drops(wbs, ev_by_w, int(hp["execution"]["hold_bars"]), cost_rt)
    if hole != int(vp.get("n_dropped_hole", 0)):
        red.append(f"B.hole: mine {hole} vs verdict {vp.get('n_dropped_hole')}")
    counts["n_dropped_hole_mine"] = hole

    # bootstrap CI replay from the recorded engine seed
    try:
        import numpy as np
        x = np.asarray(mine["pooled_net"], dtype=np.float64)
        if x.size >= 2:
            rng = np.random.default_rng(int(vp["seed"]))
            idxs = rng.integers(0, x.size, size=(2000, x.size))
            means = x[idxs].mean(axis=1)
            lo, hi = np.percentile(means, [2.5, 97.5])
            if abs(lo - float(rec_st["ci_low"])) > 1e-9 or \
                    abs(hi - float(rec_st["ci_high"])) > 1e-9:
                red.append(f"B.ci: mine ({lo},{hi}) vs verdict "
                           f"({rec_st['ci_low']},{rec_st['ci_high']})")
    except Exception as e:  # pragma: no cover
        amber.append(f"B.ci: replay unavailable ({e})")

    # trades parquet cross-check (if provided + hash-verified)
    if trades_rows is not None and verified.get("trades_h004", False):
        mine_keys = sorted((r["signal_ts"], r["entry_ts"], r["exit_ts"])
                           for r in mine["trade_rows"])
        rec_keys = sorted((int(r["signal_ts"]), int(r["entry_ts"]), int(r["exit_ts"]))
                          for r in trades_rows)
        if mine_keys != rec_keys:
            red.append("B.trades: my (signal,entry,exit) set differs from the parquet")
        counts["h004_trades_rows"] = len(rec_keys)

    counts["anchor_h004"] = {"n": st["n"], "tri_mine": mine["verdict"],
                             "tri_recorded": vp["verdict"], "eff": eff}

    # --- C: placebo replay ---------------------------------------------------
    pp = placebo["payload"]
    if pp.get("method") not in RULED_METHODS:
        red.append(f"C.method: {pp.get('method')!r} not a ruled null")
    if len(pp.get("outcomes", [])) != int(pp.get("n_runs", -1)):
        red.append("C.len: outcomes length != n_runs")
    if sum(1 for o in pp.get("outcomes", []) if o == "PASS") != int(pp.get("n_pass", -1)):
        red.append("C.count: n_pass inconsistent with outcomes")
    sealed = hp.get("placebo_method")
    if sealed is not None and sealed != pp.get("method"):
        red.append(f"C.seal: sealed {sealed!r} != run method {pp.get('method')!r}")
    try:
        import numpy as np
        union_ts = np.asarray([int(b["ts"]) for wb in wbs for b in wb], dtype=np.int64)
        mine_out = []
        for i in range(int(pp["n_runs"])):
            rng = np.random.default_rng(int(pp["seed"]) + i)
            k = min(len(ev), int(union_ts.size))
            chosen = np.sort(rng.choice(union_ts, size=k, replace=False))
            twin = [{"ts": int(t), "direction": 1} for t in chosen]
            r = judge_multi(wbs, twin, n_folds=int(hp["split_spec"]["n_folds"]),
                            hold=int(hp["execution"]["hold_bars"]), cost_rt=cost_rt,
                            min_n=int(hp["thresholds"]["min_n"]), eff=eff)
            mine_out.append(r["verdict"])
        if mine_out != list(pp["outcomes"]):
            diff = [i for i, (m, r_) in enumerate(zip(mine_out, pp["outcomes"]))
                    if m != r_]
            red.append(f"C.replay: outcomes differ at runs {diff[:8]} "
                       f"(mine n_pass={sum(1 for o in mine_out if o == 'PASS')})")
        counts["placebo_h004"] = {"n_pass_recorded": pp.get("n_pass"),
                                  "n_pass_mine":
                                      sum(1 for o in mine_out if o == "PASS")}
    except ImportError:
        amber.append("C.replay: numpy unavailable")

    # --- D: second-lens recomputation ---------------------------------------
    lens = next((r for r in journal if r.get("record_type") == "second_lens"), None)
    if lens is None:
        red.append("D.lens: no second_lens record")
    else:
        lp = lens["payload"]
        reserves = []
        for r in journal:
            if r.get("record_type") == "window" and \
                    r["payload"].get("designation") == "VIRGIN":
                reserves.append((r["payload"]["ts_start"], r["payload"]["ts_end"]))
        mine_lens = run_lens(primary_bars, second_bars, windows, reserves)
        counts["lens_mine"] = {
            "n_overlap": mine_lens["n_overlap"], "n_agree": mine_lens["n_agree"],
            "rate": mine_lens["rate"],
            "eras": [{"shift": e["shift"], "n": e["n"], "agree": e["agree"],
                      "rate": round(e["rate"], 4)} for e in mine_lens["eras"]],
            "boundaries_tie_sets": [b[:4] for b in mine_lens["boundaries"]]}
        ag = lp["agreement_summary"]
        if mine_lens["n_overlap"] != int(ag["n_overlap"]):
            red.append(f"D.n_overlap: mine {mine_lens['n_overlap']} vs {ag['n_overlap']}")
        if mine_lens["n_agree"] != int(ag["n_agree"]):
            red.append(f"D.n_agree: mine {mine_lens['n_agree']} vs {ag['n_agree']}")
        if abs(mine_lens["rate"] - float(ag["agreement_rate"])) > 1e-12:
            red.append(f"D.rate: mine {mine_lens['rate']} vs {ag['agreement_rate']}")
        if mine_lens["guard_failures"]:
            red.append(f"D.guards: my recomputation fails guards "
                       f"{mine_lens['guard_failures']} yet a lens was recorded")
        # recorded boundary instants must lie inside my tie-sets (bar-partition
        # equivalence: any tie-set member yields the identical bar split)
        m = re.search(r"DETECTED boundary instants[^:]*:\s*([0-9 ,()\-:]+)",
                      ag.get("notes", ""))
        if m:
            rec_bounds = [int(x) for x in re.findall(r"(\d{16,})", m.group(1))]
            flat_ties = mine_lens["boundaries"]
            # recorded may include the reserve-gap edge between windows as a
            # boundary; every recorded instant must be a member of SOME tie-set
            for rb in rec_bounds:
                if not any(rb in ties for ties in flat_ties):
                    red.append(f"D.boundary: recorded instant {rb} not in any of "
                               f"my maximizing tie-sets")
        rec_shifts = re.findall(r"CHOSEN (-?\d)h", ag.get("notes", ""))
        if rec_shifts:
            mine_shifts = [str(e["shift"]) for e in mine_lens["eras"]]
            if [s for s in rec_shifts] != mine_shifts:
                red.append(f"D.shifts: recorded {rec_shifts} vs mine {mine_shifts}")
        if float(ag["agreement_rate"]) < 0.95:
            amber.append("D.threshold: recorded rate below the sealed 0.95 "
                         "interpretation threshold")
        # overlap parquet audit
        if overlap_rows is not None and verified.get("overlap", False):
            man = by.get(lp.get("overlap_manifest", ""), {})
            if man.get("record_type") != "bulk_manifest":
                red.append("D.manifest: lens overlap_manifest does not resolve")
            if len(overlap_rows) != mine_lens["n_overlap"]:
                red.append(f"D.overlap_rows: parquet {len(overlap_rows)} vs "
                           f"recomputed {mine_lens['n_overlap']}")
            res = reserves
            bad = [int(r_["ts"]) for r_ in overlap_rows
                   if any(int(a) <= int(r_["ts"]) < int(b) for (a, b) in res)]
            if bad:
                red.append(f"D.reserve: {len(bad)} overlap rows inside a reserve")
            counts["overlap_reserve_hits"] = len(bad) if bad else 0

    # --- E: ordering audit ----------------------------------------------------
    if lens is not None:
        note_ref = next((p for p in lens.get("parents", [])
                         if by.get(p, {}).get("record_type") == "note"), None)
        man_ref = lens["payload"].get("overlap_manifest")
        if note_ref is None:
            red.append("E.parent: second_lens does not parent a sealed note")
        else:
            i_note = idx.get(note_ref, 10**9)
            i_man = idx.get(man_ref, 10**9)
            i_lens = idx[lens["record_id"]]
            if not (i_note < i_man < i_lens):
                red.append(f"E.order: chain positions note={i_note} "
                           f"manifest={i_man} lens={i_lens} — the seal must "
                           f"precede the overlap which must precede the lens")
            counts["ordering"] = {"note": i_note, "manifest": i_man, "lens": i_lens}

    # --- F: structure + enforcement -------------------------------------------
    burns = [r for r in journal if r.get("record_type") == "window_burn"]
    for v in (r for r in journal if r.get("record_type") == "verdict"):
        wrefs = v["payload"].get("window_refs") or [v["payload"]["window_ref"]]
        mine_b = [b for b in burns
                  if b["payload"].get("consumed_by") == v["record_id"]]
        if len(mine_b) != len(wrefs):
            red.append(f"F.burn: verdict {v['record_id']} has {len(mine_b)} "
                       f"burns for {len(wrefs)} windows")
        elif sorted(b["payload"]["window_ref"] for b in mine_b) != sorted(wrefs):
            red.append(f"F.burn: verdict {v['record_id']} burn windows differ "
                       f"from its window_refs")
    for r in journal:
        if r.get("record_type") == "window" and \
                r["payload"].get("designation") == "VIRGIN":
            burned = [b for b in burns
                      if b["payload"].get("window_ref") == r["record_id"]]
            if burned:
                red.append(f"F.virgin: VIRGIN window {r['record_id']} has burns")
    for pr in (r for r in journal if r.get("record_type") == "placebo_run"):
        h = by.get(pr["payload"].get("hypothesis_ref", ""), {})
        sealed = h.get("payload", {}).get("placebo_method")
        if sealed is not None and sealed != pr["payload"].get("method"):
            red.append(f"F.seal: placebo {pr['record_id']} method "
                       f"{pr['payload'].get('method')!r} != sealed {sealed!r}")
    promos = [r for r in journal if r.get("record_type") == "promotion"]
    counts["promotions_found"] = len(promos)
    for pm in promos:
        v = by.get(pm["payload"].get("verdict_ref", ""), {})
        if v.get("payload", {}).get("verdict") != "PASS":
            red.append(f"F.gate-a: promotion {pm['record_id']} cites a "
                       f"non-PASS verdict")
        ln = by.get(pm["payload"].get("second_lens_ref", ""), {})
        if ln.get("record_type") != "second_lens":
            red.append(f"F.gate-c: promotion {pm['record_id']} second_lens_ref "
                       f"does not resolve")
    counts["verdicts_total"] = sum(
        1 for r in journal if r.get("record_type") == "verdict")
    counts["burns_total"] = len(burns)
    counts["second_lens_found"] = sum(
        1 for r in journal if r.get("record_type") == "second_lens")
    return red, amber, counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--bars-primary", required=True)
    ap.add_argument("--bars-second", required=True)
    ap.add_argument("--trades-h004", required=True)
    ap.add_argument("--overlap", required=True)
    ap.add_argument("--venues", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    journal = load_journal(a.journal)
    manifests = {r["payload"]["dataset"]: r for r in journal
                 if r.get("record_type") == "bulk_manifest"}
    red, amber = [], []
    verified = {}

    def verify(path, dataset, key):
        man = manifests.get(dataset)
        if man is None:
            red.append(f"A.manifest: no bulk_manifest for {dataset!r}")
            verified[key] = False
            return
        got = sha256_file(path)
        want = man["payload"]["file_sha256"]
        verified[key] = got == want
        if not verified[key]:
            red.append(f"A.hash: {path} {got[:12]}… != manifest {want[:12]}… "
                       f"— file refused (rebuild via the §1 scripts)")

    verify(a.bars_primary, "xauusd_h1_primary_full", "primary")
    verify(a.bars_second, "xauusd_h1_secondfeed", "second")
    verify(a.trades_h004, f"verdict_trades.{H004}", "trades_h004")
    verify(a.overlap, "xauusd_h1_overlap_lens", "overlap")
    if not (verified.get("primary") and verified.get("second")):
        _emit(a, red, amber, {})
        return 1

    import pyarrow.parquet as pq
    primary = sorted(pq.read_table(a.bars_primary).to_pylist(),
                     key=lambda r: int(r["ts"]))
    second = sorted(pq.read_table(a.bars_second).to_pylist(),
                    key=lambda r: int(r["ts"]))
    trades = pq.read_table(a.trades_h004).to_pylist() \
        if verified.get("trades_h004") else None
    overlap = pq.read_table(a.overlap).to_pylist() \
        if verified.get("overlap") else None

    cost_rt = cost_round_trip(a.venues, "xauusd_retail_median")
    r2, a2, counts = run_check(journal, primary, second, cost_rt=cost_rt,
                               trades_rows=trades, overlap_rows=overlap,
                               verified=verified)
    red += r2
    amber += a2
    counts["cost_round_trip"] = cost_rt
    return _emit(a, red, amber, counts)


def _emit(a, red, amber, counts):
    verdict = "RED" if red else ("AMBER" if amber else "GREEN")
    report = {"check": "s9_lens_multiwindow", "rev": 1,
              "run_utc": int(time.time()), "counts": counts,
              "red": red, "amber": amber, "verdict": verdict}
    out = json.dumps(report, indent=2)
    if getattr(a, "report", None):
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print(out)
    return 1 if verdict == "RED" else 0


if __name__ == "__main__":
    sys.exit(main())

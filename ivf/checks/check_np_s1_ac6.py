#!/usr/bin/env python3
"""IVF NP-S1 AC-6 check: independent re-derivation of the H-07 prediction
verdict. (rev 1)

Re-implements every rule from the ruling texts alone (NP-ADR-008, its
Appendix A, ARCH-006 SS2/SS3, DEVQ-015, seeds.py's own "normative --
reproduce exactly" recipe, and record.py's canonical_bytes docstring,
itself "normative, copy exactly"). No qrf import anywhere in this file.

Sections (each an independent pass/fail; RED on any mismatch):
  A) FAMILY TRIAL RECOUNT -- reimplements deflation.py's stated
     prefix-segment rule (read as text, not imported) and sums
     trial_count.n_attempts for family "xauusd/neelprajna"; compares
     to the verdict's corrections.family_m / effective_alpha.
  B) THRESHOLDS BYTE-EQUAL -- verdict.thresholds vs hypothesis.thresholds,
     canonical-JSON compared.
  C) BURN ATOMICITY -- exactly one window_burn for (window_ref, lineage);
     its consumed_by is the verdict id; the verdict id is among its
     parents; its window_ref matches the verdict's.
  D) TRADES RECOMPUTATION -- n_trades, gross/net mean+total, one-sided
     t-stat + p (scipy ttest_1samp, H0: mean<=0), seeded percentile
     bootstrap CI (numpy default_rng(seed), 2000 resamples, [2.5,97.5]
     percentile -- battery.py's own stated _BOOTSTRAP_RESAMPLES/recipe,
     read as a mechanical, domain-blind procedure, not detector logic),
     fold n + fold means from the trades parquet's own "fold" column.
  E) TRI-STATE RE-DERIVATION -- n vs min_n, mean sign, p vs
     effective_alpha => PASS/FAIL/INSUFFICIENT, compared to recorded.
  F) COST MODEL -- gross_pnl - net_pnl == 0.41 for every trade; venues.yaml
     xauusd_retail_h07 recomputes 0.24 + 2*(0.05+0.035) = 0.41.
  G) WINDOW -- designation TRAINING; ts bounds equal the ratified UTC
     half-open interval [2026-04-20T22:00:00Z, 2026-07-10T14:33:00Z).
  H) EMBARGO -- embargo_bars >= hold_bars + 1.
  I) SEED -- selftest_seed == 20260725 recorded on the verdict; the run
     seed reproduces via seeds.for_run's stated recipe:
     int.from_bytes(sha256(canonical_bytes({hypothesis_ref, window_ref}))[:8],
     "big") & (2**63-1).
  J) HASH CHAIN -- record.py's own "IVF re-implements canonical
     serialization independently from the spec text" docstring: recompute
     content_hash = sha256(canonical_bytes({record_type, schema_version,
     producer, event_ts, parents, payload})) for every record; prev_hash
     of record i must equal content_hash of record i-1 (genesis = 64
     zeros); no torn tail.
  K) BULK MANIFEST -- the verdict's trades_manifest bulk_manifest record's
     file_sha256/row_count match the actual parquet on disk.

Usage:
  python ivf/checks/check_np_s1_ac6.py --journal <path> --trades <path>
    --venues <path> --verdict-id 01KYSGQR3D8SYSVJFSF9M77CMY
    --report ivf/reports/ac6_verify.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time

import datetime

FAMILY = "xauusd/neelprajna"
WINDOW_START_UTC_NS = int(
    datetime.datetime(2026, 4, 20, 22, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1e9
)
WINDOW_END_UTC_NS = int(
    datetime.datetime(2026, 7, 10, 14, 33, 0, tzinfo=datetime.timezone.utc).timestamp() * 1e9
)
BASE_ALPHA = 0.05
COST_EXPECT = 0.41
BOOTSTRAP_RESAMPLES = 2000
SELFTEST_SEED_EXPECT = 20260725


def load_journal(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def canonical_bytes(d: dict) -> bytes:
    """record.py canonical_bytes, "normative -- copy exactly" (own docstring)."""
    return json.dumps(
        d, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def is_prefix_segment(prefix: str, full: str) -> bool:
    """deflation.py::_is_prefix_segment, reimplemented from its docstring."""
    return full == prefix or full.startswith(prefix + ".") or full.startswith(prefix + "/")


def trial_belongs_to_family(family: str, tc_payload: dict) -> bool:
    """deflation.py::_trial_belongs_to_family, reimplemented from its docstring."""
    declared = tc_payload.get("family")
    if declared is not None and (
        declared == family
        or is_prefix_segment(declared, family)
        or is_prefix_segment(family, declared)
    ):
        return True
    inst_family = family.rsplit("/", 1)[-1]
    return is_prefix_segment(inst_family, tc_payload["lineage"])


HASHED_FIELDS = ("record_type", "schema_version", "producer", "event_ts", "parents", "payload")


def compute_content_hash(rec: dict) -> str:
    """record.py::compute_content_hash, reimplemented from its docstring."""
    body = {k: rec[k] for k in HASHED_FIELDS}
    return hashlib.sha256(canonical_bytes(body)).hexdigest()


def for_run_seed(hypothesis_ref: str, window_ref: str) -> int:
    """seeds.py::for_run, reimplemented from its "normative -- reproduce
    exactly" docstring recipe."""
    body = canonical_bytes({"hypothesis_ref": hypothesis_ref, "window_ref": window_ref})
    digest = hashlib.sha256(body).digest()
    return int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)


def ns_to_iso(ns: int) -> str:
    return datetime.datetime.fromtimestamp(ns / 1e9, tz=datetime.timezone.utc).isoformat()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--trades", required=True)
    ap.add_argument("--venues", required=True)
    ap.add_argument("--verdict-id", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    red: list[str] = []
    amber: list[str] = []
    pass_lines: list[str] = []

    journal = load_journal(a.journal)
    by_id = {r["record_id"]: r for r in journal}

    verdict = by_id.get(a.verdict_id)
    if verdict is None or verdict.get("record_type") != "verdict":
        red.append(f"TARGET: no verdict record {a.verdict_id} in journal")
        _emit(a, red, amber, pass_lines)
        return 1

    vp = verdict["payload"]
    hyp = by_id.get(vp.get("hypothesis_ref", ""))
    win = by_id.get(vp.get("window_ref", ""))
    if hyp is None:
        red.append(f"REF: verdict references missing hypothesis {vp.get('hypothesis_ref')}")
    if win is None:
        red.append(f"REF: verdict references missing window {vp.get('window_ref')}")
    if red:
        _emit(a, red, amber, pass_lines)
        return 1
    hp = hyp["payload"]
    wp = win["payload"]

    trials = [r for r in journal if r.get("record_type") == "trial_count"]
    burns = [r for r in journal if r.get("record_type") == "window_burn"]

    # --- J: hash chain integrity, whole journal -----------------------------
    GENESIS = "0" * 64
    prev = GENESIS
    chain_broken_at = None
    for i, rec in enumerate(journal):
        recomputed = compute_content_hash(rec)
        if recomputed != rec.get("content_hash"):
            chain_broken_at = (i, "content_hash mismatch", rec.get("record_id"))
            break
        if rec.get("prev_hash") != prev:
            chain_broken_at = (i, "prev_hash does not chain", rec.get("record_id"))
            break
        prev = recomputed
    if chain_broken_at is not None:
        red.append(f"J.hash_chain: broken at line {chain_broken_at[0]} ({chain_broken_at[1]}, record {chain_broken_at[2]})")
    else:
        pass_lines.append(f"J.hash_chain: PASS (all {len(journal)} records chain intact, genesis-to-tail)")

    # --- A: family trial recount ------------------------------------------
    n_family = sum(
        int(t["payload"].get("n_attempts", 0))
        for t in trials
        if trial_belongs_to_family(FAMILY, t["payload"])
    )
    eff_expect = BASE_ALPHA / max(1, n_family)
    corr = vp.get("corrections", {})
    if int(corr.get("family_m", -1)) != n_family:
        red.append(
            f"A.family_m: my recount={n_family} (family={FAMILY}) vs verdict "
            f"family_m={corr.get('family_m')}"
        )
    else:
        pass_lines.append(f"A.family_m: PASS ({n_family} == recorded {corr.get('family_m')})")
    if abs(float(corr.get("effective_alpha", -1)) - eff_expect) > 1e-12:
        red.append(
            f"A.effective_alpha: my {eff_expect} vs verdict {corr.get('effective_alpha')}"
        )
    else:
        pass_lines.append(
            f"A.effective_alpha: PASS ({eff_expect:.10f} == recorded "
            f"{corr.get('effective_alpha'):.10f})"
        )

    # --- B: thresholds byte-equal -------------------------------------------
    if canon(vp.get("thresholds")) != canon(hp.get("thresholds")):
        red.append("B.thresholds: verdict.thresholds != hypothesis.thresholds (canonical)")
    else:
        pass_lines.append("B.thresholds: PASS (byte-equal, canonical JSON)")

    # --- C: burn atomicity ---------------------------------------------------
    lineage = hp.get("lineage")
    my_burns = [
        b
        for b in burns
        if b["payload"].get("window_ref") == vp.get("window_ref")
        and b["payload"].get("lineage") == lineage
    ]
    if len(my_burns) != 1:
        red.append(f"C.burn: {len(my_burns)} burns for (window, lineage={lineage}); expected 1")
    else:
        b = my_burns[0]
        if b["payload"].get("consumed_by") != verdict["record_id"]:
            red.append(f"C.consumed_by: {b['payload'].get('consumed_by')} != verdict id")
        elif verdict["record_id"] not in b.get("parents", []):
            red.append("C.parents: burn's parents do not include the verdict id")
        elif b["payload"].get("window_ref") != vp.get("window_ref"):
            red.append("C.window_ref: burn window_ref != verdict window_ref")
        else:
            pass_lines.append(
                f"C.burn: PASS (exactly 1 burn {b['record_id']}, consumed_by/parents/window_ref atomic)"
            )

    # --- D: trades recomputation ---------------------------------------------
    import pyarrow.parquet as pq

    table = pq.read_table(a.trades)
    file_sha256 = hashlib.sha256(open(a.trades, "rb").read()).hexdigest()
    rows = table.to_pylist()
    n = len(rows)
    nets = [float(r["net_pnl"]) for r in rows]
    grosses = [float(r["gross_pnl"]) for r in rows]

    manifest = by_id.get(vp.get("trades_manifest", ""))
    if manifest is None or manifest.get("record_type") != "bulk_manifest":
        red.append(f"K.manifest: no bulk_manifest record {vp.get('trades_manifest')}")
    else:
        mp = manifest["payload"]
        if mp.get("file_sha256") != file_sha256:
            red.append(f"K.file_sha256: parquet on disk={file_sha256} vs manifest={mp.get('file_sha256')}")
        else:
            pass_lines.append(f"K.file_sha256: PASS ({file_sha256})")
        if int(mp.get("row_count", -1)) != n:
            red.append(f"K.row_count: parquet has {n} rows vs manifest row_count={mp.get('row_count')}")
        else:
            pass_lines.append(f"K.row_count: PASS ({n})")

    if n != int(vp.get("n_trades", -1)):
        red.append(f"D.n_trades: parquet {n} vs verdict {vp.get('n_trades')}")
    else:
        pass_lines.append(f"D.n_trades: PASS ({n})")

    net_mean = sum(nets) / n if n else None
    gross_mean = sum(grosses) / n if n else None
    if abs(net_mean - float(vp["net"]["mean"])) > 1e-9:
        red.append(f"D.net_mean: mine={net_mean!r} vs verdict={vp['net']['mean']!r}")
    else:
        pass_lines.append(f"D.net_mean: PASS ({net_mean!r})")
    if abs(gross_mean - float(vp["gross"]["mean"])) > 1e-9:
        red.append(f"D.gross_mean: mine={gross_mean!r} vs verdict={vp['gross']['mean']!r}")
    else:
        pass_lines.append(f"D.gross_mean: PASS ({gross_mean!r})")
    if abs(sum(nets) - float(vp["net"]["total"])) > 1e-6:
        red.append(f"D.net_total: mine={sum(nets)!r} vs verdict={vp['net']['total']!r}")
    if abs(sum(grosses) - float(vp["gross"]["total"])) > 1e-6:
        red.append(f"D.gross_total: mine={sum(grosses)!r} vs verdict={vp['gross']['total']!r}")

    # one-sided t-test, H0: mean <= 0 (ARCH-006 SS2 line 50; battery.py step 6)
    from scipy import stats
    import numpy as np

    x = np.asarray(nets, dtype=np.float64)
    mean = float(x.mean())
    sd = float(x.std(ddof=1)) if n >= 2 else 0.0
    t_mine, p_two = stats.ttest_1samp(x, 0.0)
    p_one = float(p_two / 2 if mean > 0 else 1.0 - p_two / 2)
    rec_stat = vp["statistics"]["t_one_sided"]["stat"]
    rec_p = vp["statistics"]["t_one_sided"]["p"]
    if abs(float(t_mine) - float(rec_stat)) > 1e-9:
        red.append(f"D.t_stat: mine={float(t_mine)!r} vs verdict={rec_stat!r}")
    else:
        pass_lines.append(f"D.t_stat: PASS ({float(t_mine)!r})")
    if abs(p_one - float(rec_p)) > 1e-9:
        red.append(f"D.p_one_sided: mine={p_one!r} vs verdict={rec_p!r}")
    else:
        pass_lines.append(f"D.p_one_sided: PASS ({p_one!r})")

    # seeded percentile bootstrap CI (battery.py: default_rng(seed),
    # 2000 x n integers draw, percentile [2.5, 97.5])
    seed = int(vp["seed"])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(BOOTSTRAP_RESAMPLES, n))
    means = x[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    rec_lo = vp["statistics"]["t_one_sided"]["ci_low"]
    rec_hi = vp["statistics"]["t_one_sided"]["ci_high"]
    if abs(float(lo) - float(rec_lo)) > 1e-9:
        red.append(f"D.ci_low: mine={float(lo)!r} vs verdict={rec_lo!r}")
    else:
        pass_lines.append(f"D.ci_low: PASS ({float(lo)!r})")
    if abs(float(hi) - float(rec_hi)) > 1e-9:
        red.append(f"D.ci_high: mine={float(hi)!r} vs verdict={rec_hi!r}")
    else:
        pass_lines.append(f"D.ci_high: PASS ({float(hi)!r})")

    # fold n + fold means
    if rows and "fold" in rows[0]:
        fold_counts = {}
        fold_means = {}
        for f_idx in sorted({int(r["fold"]) for r in rows}):
            fn = [float(r["net_pnl"]) for r in rows if int(r["fold"]) == f_idx]
            fold_counts[f_idx] = len(fn)
            fold_means[f_idx] = sum(fn) / len(fn) if fn else None
        for f in vp.get("folds", []):
            idx_ = int(f["index"])
            if fold_counts.get(idx_) != int(f["n_trades"]):
                red.append(
                    f"D.fold{idx_}.n: mine={fold_counts.get(idx_)} vs verdict={f['n_trades']}"
                )
            else:
                pass_lines.append(f"D.fold{idx_}.n: PASS ({fold_counts.get(idx_)})")
            if abs(fold_means.get(idx_, math.nan) - float(f["mean_net"])) > 1e-9:
                red.append(
                    f"D.fold{idx_}.mean: mine={fold_means.get(idx_)!r} vs verdict={f['mean_net']!r}"
                )
            else:
                pass_lines.append(f"D.fold{idx_}.mean: PASS ({fold_means.get(idx_)!r})")
    else:
        amber.append("D.folds: trades parquet has no 'fold' column")

    # --- E: tri-state re-derivation -------------------------------------------
    min_n = int(hp.get("thresholds", {}).get("min_n", 0))
    eff = float(corr.get("effective_alpha", BASE_ALPHA))
    if n < min_n:
        derived = "INSUFFICIENT"
    elif mean > 0 and p_one < eff:
        derived = "PASS"
    else:
        derived = "FAIL"
    if derived != vp.get("verdict"):
        red.append(f"E.tristate: my derivation={derived} vs recorded={vp.get('verdict')}")
    else:
        pass_lines.append(f"E.tristate: PASS (derived {derived})")

    # --- F: cost model ---------------------------------------------------------
    diffs = {round(g - ne, 6) for g, ne in zip(grosses, nets)}
    if diffs != {COST_EXPECT}:
        red.append(f"F.per_trade_cost: gross-net values found = {sorted(diffs)}, expected {{{COST_EXPECT}}}")
    else:
        pass_lines.append(f"F.per_trade_cost: PASS (every trade gross-net == {COST_EXPECT})")

    import yaml

    with open(a.venues, encoding="utf-8") as f:
        venues = yaml.safe_load(f)
    v = venues.get("venues", {}).get("xauusd_retail_h07", {})
    recomputed = round(v.get("spread", 0) + 2 * (v.get("slippage_per_side", 0) + v.get("commission_per_side", 0)), 6)
    if abs(recomputed - COST_EXPECT) > 1e-9:
        red.append(f"F.venues_formula: {v.get('spread')} + 2*({v.get('slippage_per_side')}+{v.get('commission_per_side')}) = {recomputed} != {COST_EXPECT}")
    else:
        pass_lines.append(f"F.venues_formula: PASS (0.24 + 2*(0.05+0.035) = {recomputed})")

    # --- G: window designation + bounds -----------------------------------------
    if wp.get("designation") != "TRAINING":
        red.append(f"G.designation: {wp.get('designation')} != TRAINING")
    else:
        pass_lines.append("G.designation: PASS (TRAINING)")
    ts_start, ts_end = int(wp.get("ts_start", -1)), int(wp.get("ts_end", -1))
    if ts_start != WINDOW_START_UTC_NS or ts_end != WINDOW_END_UTC_NS:
        red.append(
            f"G.bounds: window=[{ns_to_iso(ts_start)}, {ns_to_iso(ts_end)}) vs "
            f"ratified [2026-04-20T22:00:00Z, 2026-07-10T14:33:00Z)"
        )
    else:
        pass_lines.append(
            f"G.bounds: PASS ([{ns_to_iso(ts_start)}, {ns_to_iso(ts_end)}) matches ratified interval)"
        )

    # --- H: embargo >= hold_bars + 1 ---------------------------------------------
    hold_bars = int(hp.get("execution", {}).get("hold_bars", -1))
    embargo_bars = int(hp.get("split_spec", {}).get("embargo_bars", -1))
    if embargo_bars < hold_bars + 1:
        red.append(f"H.embargo: embargo_bars={embargo_bars} < hold_bars+1={hold_bars + 1}")
    else:
        pass_lines.append(f"H.embargo: PASS ({embargo_bars} >= {hold_bars + 1})")

    # --- I: selftest seed + run seed reproducibility ------------------------------
    if int(vp.get("selftest_seed", -1)) != SELFTEST_SEED_EXPECT:
        red.append(f"I.selftest_seed: {vp.get('selftest_seed')} != {SELFTEST_SEED_EXPECT}")
    else:
        pass_lines.append(f"I.selftest_seed: PASS ({SELFTEST_SEED_EXPECT})")
    seed_mine = for_run_seed(hyp["record_id"], win["record_id"])
    if seed_mine != seed:
        red.append(f"I.seed_reproducible: my seeds.for_run={seed_mine} vs recorded seed={seed}")
    else:
        pass_lines.append(f"I.seed_reproducible: PASS (seeds.for_run({hyp['record_id']},{win['record_id']})={seed_mine})")

    # NOTE ON SCOPE: sections A-K above are the mechanical CHAIN CHECKS
    # (NP-ADR-002 SS2) -- these are what the drill (SS1) plants frauds
    # against, and "verdict"/exit-code below gate ONLY on them. Sections
    # L/M below are SS3's "four things nobody has checked" -- substantive
    # findings that may honestly fail on the REAL, untampered ledger
    # without that being a drill false-alarm. They are reported in a
    # SEPARATE list (section3) and never affect the chain-check verdict,
    # so a real (non-drill) finding here cannot masquerade as -- or be
    # confused with -- a control false-positive.
    section3_pass: list[str] = []
    section3_red: list[str] = []

    # --- L (SS3.1): FAIL survives at the UNDEFLATED base alpha --------------------
    # p=0.0574 > 0.05: the 19-vs-18 family-count ruling could not have changed
    # the outcome (deflation only ever LOWERS the bar the evidence must clear).
    if p_one <= BASE_ALPHA:
        section3_red.append(
            f"L.undeflated_alpha: p={p_one!r} <= base_alpha={BASE_ALPHA} -- the FAIL "
            f"does NOT survive at undeflated alpha; the 19-vs-18 ruling WOULD have mattered"
        )
    else:
        section3_pass.append(
            f"L.undeflated_alpha: PASS (p={p_one!r} > base_alpha={BASE_ALPHA}; FAIL survives "
            f"even without deflation -- the 19-vs-18 ruling could not have changed the outcome)"
        )

    # --- M (SS3.2): three non-equivalence statements, VERBATIM --------------------
    # NP-ADR-008 SS2.1, exact text:
    ADR_STATEMENTS = [
        "E2-v1.1 is not equivalent to the original v1.0 hypothesis.",
        "It is a new hypothesis bound to the documented v1.1 detector lineage.",
        "Any future judgment of the original T3/MSS detector requires a separate "
        "implementation and fresh out-of-sample evidence.",
    ]
    lineage_hyps = [
        r for r in journal
        if r.get("record_type") == "hypothesis" and r["payload"].get("lineage") == hp.get("lineage")
    ]
    for hrec in lineage_hyps:
        hrp = hrec["payload"]
        claim_form = hrp.get("setup_dsl", {}).get("claim_form", "?")
        hay = json.dumps(hrp.get("outcome_interpretations", {})) + " " + hrp.get("thesis", "")
        for i, stmt in enumerate(ADR_STATEMENTS, start=1):
            tag = f"M.{claim_form}.statement{i}"
            if stmt in hay:
                section3_pass.append(f"{tag}: PASS (byte-exact substring found, {hrec['record_id']})")
            else:
                section3_red.append(
                    f"{tag}: NOT byte-verbatim in {hrec['record_id']}'s "
                    f"outcome_interpretations/thesis -- ADR text: {stmt!r}"
                )

    verdict_out = "RED" if red else ("AMBER" if amber else "GREEN")
    report = {
        "check": "np_s1_ac6",
        "rev": 1,
        "run_utc": int(time.time()),
        "verdict_id": a.verdict_id,
        "trades_file_sha256": file_sha256,
        "counts": {
            "journal_records": len(journal),
            "trial_counts": len(trials),
            "family_recount": n_family,
        },
        "pass": pass_lines,
        "amber": amber,
        "red": red,
        "verdict": verdict_out,
        "section3_pass": section3_pass,
        "section3_red": section3_red,
    }
    _write(a, report)
    return 1 if verdict_out == "RED" else 0


def _emit(a, red, amber, pass_lines):
    report = {
        "check": "np_s1_ac6",
        "rev": 1,
        "run_utc": int(time.time()),
        "pass": pass_lines,
        "amber": amber,
        "red": red,
        "verdict": "RED" if red else "GREEN",
    }
    _write(a, report)


def _write(a, report):
    out = json.dumps(report, indent=2)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print(out)


if __name__ == "__main__":
    sys.exit(main())

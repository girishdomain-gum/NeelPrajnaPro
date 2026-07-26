"""ARCH-009 S4.1 -- clock-era cross-feed alignment + overlap engine (independent lens).

Implements the SEALED pre-registration as amended by the Architect's DEVQ-023 ruling
(Option A + four binding amendments), sealed in the correction note
``01KYE3BBE2PK0EP87D62S57CE6`` (procedure only) BEFORE this overlap runs -- its
hash-chain position proves the ordering (DEVQ-020). The three prior notes bind the
tolerances, candidate shifts, reserve exclusion, and the 0.95 interpretation threshold;
DEVQ-023 supersedes ONLY the alignment clause. The amended procedure, verbatim from the
seal:

  1. RESERVE EXCLUSION (primary/server clock): drop every primary bar whose ts is in a
     VIRGIN range. Storage is not computation.
  2. EMPIRICAL CLOCK-ERA SEGMENTATION (DEVQ-023 amendment 3): coarse weekly scan of the
     training bars -> each window's agreement-rate-winning shift -> run-length flip
     detection (a run < K=2 windows is absorbed) -> local hour refinement by the
     max-agreement cut. The EU-hardcoded DST instants are RETIRED (recorded pre-fix for
     the audit trail).
  3. DISCRIMINATOR (amendment 1): per era, the shift is chosen by MAX OHLC-agreement-rate
     over the candidates; the shared count is retained ONLY as a sanity floor (chosen
     shift's count >= 0.90 x max candidate count).
  4. TWO-PART GUARD (amendment 2): winner agreement_rate >= 3x runner-up AND >= 0.80
     absolute; either failure STOPs and DEVQs. PREDICTION GUARD (amendment 4): minimum
     post-fix WINTER-era agreement < 0.90 STOPs and DEVQs (the Architect's testable
     prediction: US DST, era-0 boundary ~2024-03-10, winter -> ~0.95).
  5. AGREEMENT: a shared bar AGREES iff |dopen|,|dclose| <= 0.50 and |dhigh|,|dlow| <= 0.75.

On success: persist the aligned overlap slice (a bulk_manifest = ``overlap_manifest``)
and append the first ``second_lens`` -- source_name tier=BROKER, overlap_manifest, and an
``agreement_summary`` whose ``notes`` carry BOTH metric tables (count AND agreement) per
era for the PRE-FIX and POST-FIX segmentations, the guard-fired history, the detected
boundary instants, and the declared tier (DEVQ-023 amendment 4). Idempotent.

    F:/QRF/.venv/Scripts/python.exe scripts/overlap_second_lens_s9.py            # run
    F:/QRF/.venv/Scripts/python.exe scripts/overlap_second_lens_s9.py --dry      # no writes

Rebuild the gitignored parquets first if absent:
    F:/QRF/.venv/Scripts/python.exe scripts/ingest_lens_feeds_s9.py --rebuild-bulk
"""

from __future__ import annotations

import argparse
import importlib.util
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from qrf.kernel.errors import BulkIntegrityError
from qrf.kernel.records.bulk import BulkStore, _sha256_file
from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"
PRIMARY = "xauusd_h1_primary_full"
SECOND = "xauusd_h1_secondfeed"
OVERLAP_DATASET = "xauusd_h1_overlap_lens"
PRODUCER = "lens.overlap@0.1.0"

HR_NS = 3_600_000_000_000
WEEK_NS = 7 * 86_400 * 1_000_000_000
SHIFT_CANDIDATES = (0, -1, -2, -3, 1, 2, 3)  # applied to PRIMARY stamps

# Reserve exclusion ranges (primary/server clock), half-open -- DEVQ-022 seam fix.
RESERVE_RANGES = (
    (1726128000000000000, 1735689600000000001),  # 2024 VIRGIN
    (1757685600000000000, 1767225600000000001),  # 2025 VIRGIN
)
# PRE-FIX EU DST cut points -- RETIRED by DEVQ-023, kept only to recompute the pre-fix
# tables recorded in the audit trail (the "before" story the record must show).
EU_DST_CUTS = (
    1711843200000000000,  # 2024-03-31
    1729987200000000000,  # 2024-10-27
    1743292800000000000,  # 2025-03-30
    1761436800000000000,  # 2025-10-26
)

# OHLC agreement tolerances (USD/oz), sealed.
TOL_OC = 0.50   # open, close
TOL_HL = 0.75   # high, low
AGREEMENT_THRESHOLD = 0.95   # interpretation threshold (this lens; not a gate)

# DEVQ-023 discriminator + guards.
FLOOR_FRAC = 0.90        # sanity floor: winner shared count >= this x max candidate count
GUARD_RATIO = 3.0        # winner agreement_rate >= GUARD_RATIO x runner-up's
GUARD_ABS = 0.80         # winner agreement_rate >= this absolute
WINTER_SHIFT = -2        # eras whose chosen shift is -2h are "winter"
WINTER_PREDICTION_MIN = 0.90  # min winter agreement below this => prediction wrong => STOP
K_PERSIST = 2            # a coarse run shorter than this is absorbed (noise)

SOURCE_NAME = "exness_xauusdm_h1 (tier=BROKER)"


# --------------------------------------------------------------------------- helpers
def _iso(ts: int) -> str:
    return datetime.fromtimestamp(ts / 1e9, tz=UTC).strftime("%Y-%m-%d %H:%M")


def _in_reserve(ts: int) -> bool:
    return any(lo <= ts < hi for lo, hi in RESERVE_RANGES)


def _agrees(pr: dict, sr: dict) -> bool:
    return (
        abs(pr["open"] - sr["open"]) <= TOL_OC
        and abs(pr["close"] - sr["close"]) <= TOL_OC
        and abs(pr["high"] - sr["high"]) <= TOL_HL
        and abs(pr["low"] - sr["low"]) <= TOL_HL
    )


def _matched(bar: dict, sec_by_ts: dict, sh: int) -> dict | None:
    return sec_by_ts.get(bar["ts"] + sh * HR_NS)


def _shift_table(bars: list[dict], sec_by_ts: dict) -> list[dict]:
    """Per-candidate {shift_h, shared, agree, agreement_rate} over ``bars``."""
    table = []
    for sh in SHIFT_CANDIDATES:
        shared = agree = 0
        for b in bars:
            sr = _matched(b, sec_by_ts, sh)
            if sr is None:
                continue
            shared += 1
            if _agrees(b, sr):
                agree += 1
        table.append({"shift_h": sh, "shared": shared, "agree": agree,
                      "agreement_rate": agree / shared if shared else 0.0})
    return table


def _rate_key(t: dict) -> tuple:
    # rank by agreement_rate desc, tie-break smaller |shift|, then more-negative shift
    return (t["agreement_rate"], -abs(t["shift_h"]), -t["shift_h"])


def _window_winner(bars: list[dict], sec_by_ts: dict) -> int | None:
    """The agreement-rate-winning shift for one coarse window (or None if no overlap)."""
    table = [t for t in _shift_table(bars, sec_by_ts) if t["shared"] > 0]
    if not table:
        return None
    return max(table, key=_rate_key)["shift_h"]


def weekly_winners(bars: list[dict], sec_by_ts: dict) -> list[tuple[int, int]]:
    """(window_index, winning_shift) for each non-empty 7-day window, time-ordered.

    Windows are anchored at the first training bar's ts (DEVQ-023 amendment 3a).
    """
    anchor = bars[0]["ts"]
    groups: dict[int, list] = {}
    for b in bars:
        groups.setdefault((b["ts"] - anchor) // WEEK_NS, []).append(b)
    out = []
    for wk in sorted(groups):
        sh = _window_winner(groups[wk], sec_by_ts)
        if sh is not None:
            out.append((wk, sh))
    return out


def _coarse_runs(winners: list[tuple[int, int]]) -> list[dict]:
    """Run-length-encode window winners; absorb runs shorter than K_PERSIST (3b)."""
    runs: list[dict] = []
    for wk, sh in winners:
        if runs and runs[-1]["shift"] == sh:
            runs[-1]["weeks"].append(wk)
        else:
            runs.append({"shift": sh, "weeks": [wk]})
    merged: list[dict] = []
    for run in runs:
        if merged and len(run["weeks"]) < K_PERSIST:
            merged[-1]["weeks"].extend(run["weeks"])         # noise -> the preceding era
        elif merged and merged[-1]["shift"] == run["shift"]:
            merged[-1]["weeks"].extend(run["weeks"])         # coalesce (absorption left a seam)
        else:
            merged.append(run)
    return merged


def _refine_boundary(bars: list[dict], sec_by_ts: dict, sh_a: int, sh_b: int,
                     lo_ts: int, hi_ts: int) -> int:
    """Local hour refinement (3c): the cut c maximising agreements when bars < c score
    under ``sh_a`` and bars >= c under ``sh_b`` over the bracket [lo_ts, hi_ts]."""
    region = [b for b in bars if lo_ts <= b["ts"] <= hi_ts]
    if not region:
        return lo_ts
    cuts = sorted({b["ts"] for b in region}) + [region[-1]["ts"] + HR_NS]
    best_cut, best_agr = cuts[0], -1
    for c in cuts:
        agr = 0
        for b in region:
            sh = sh_a if b["ts"] < c else sh_b
            sr = _matched(b, sec_by_ts, sh)
            if sr is not None and _agrees(b, sr):
                agr += 1
        if agr > best_agr:
            best_cut, best_agr = c, agr
    return best_cut


def detect_eras(bars: list[dict], sec_by_ts: dict) -> tuple[list[dict], list[int]]:
    """Empirical segmentation -> (eras, boundary_instants).

    ``bars`` must be the reserve-excluded primary training bars sorted ascending by ts.
    Each era dict: {shift_coarse, start_ts, end_ts} (end_ts half-open). The coarse shift
    is the window-scan winner; the FINAL per-era shift is re-chosen by the discriminator.
    """
    runs = _coarse_runs(weekly_winners(bars, sec_by_ts))
    anchor = bars[0]["ts"]
    boundaries: list[int] = []
    eras: list[dict] = []
    for i, run in enumerate(runs):
        start = anchor + run["weeks"][0] * WEEK_NS if i == 0 else boundaries[-1]
        if i + 1 < len(runs):
            nxt = runs[i + 1]
            lo = anchor + run["weeks"][-1] * WEEK_NS
            hi = anchor + (nxt["weeks"][0] + 1) * WEEK_NS
            b = _refine_boundary(bars, sec_by_ts, run["shift"], nxt["shift"], lo, hi)
            boundaries.append(b)
            eras.append({"shift_coarse": run["shift"], "start_ts": start, "end_ts": b})
        else:
            eras.append({"shift_coarse": run["shift"], "start_ts": start,
                         "end_ts": bars[-1]["ts"] + HR_NS})
    return eras, boundaries


def _bars_in(bars: list[dict], lo: int, hi: int) -> list[dict]:
    return [b for b in bars if lo <= b["ts"] < hi]


def evaluate_eras(bars: list[dict], sec_by_ts: dict, eras: list[dict]) -> list[dict]:
    """Per era: shift table, discriminator winner/runner (by rate), count winner, guards."""
    out = []
    for k, era in enumerate(eras):
        sub = _bars_in(bars, era["start_ts"], era["end_ts"])
        table = _shift_table(sub, sec_by_ts)
        by_rate = sorted(table, key=_rate_key, reverse=True)
        winner, runner = by_rate[0], by_rate[1]
        max_shared = max((t["shared"] for t in table), default=0)
        by_count = sorted(table, key=lambda t: -t["shared"])
        floor_ok = winner["shared"] >= FLOOR_FRAC * max_shared if max_shared else False
        ratio_ok = winner["agreement_rate"] >= GUARD_RATIO * runner["agreement_rate"]
        abs_ok = winner["agreement_rate"] >= GUARD_ABS
        out.append({
            "era_idx": k, "start_ts": era["start_ts"], "end_ts": era["end_ts"],
            "n_bars": len(sub), "table": table,
            "winner": winner, "runner": runner,
            "count_winner": by_count[0], "count_runner": by_count[1],
            "max_shared": max_shared,
            "floor_ok": floor_ok, "ratio_ok": ratio_ok, "abs_ok": abs_ok,
            "passes": floor_ok and ratio_ok and abs_ok,
            "is_winter": winner["shift_h"] == WINTER_SHIFT,
        })
    return out


def guards_verdict(post: list[dict]) -> dict:
    """The DEVQ-023 STOP decision over evaluated eras (pure; testable).

    ``ok`` is True iff every era passes the two-part guard AND the minimum winter-era
    agreement clears the prediction guard. Never loosens a guard to admit a result.
    """
    failed = [e for e in post if not e["passes"]]
    winter_rates = [e["winner"]["agreement_rate"] for e in post if e["is_winter"]]
    winter_min = min(winter_rates) if winter_rates else 0.0
    prediction_ok = bool(winter_rates) and winter_min >= WINTER_PREDICTION_MIN
    return {"failed": failed, "winter_min": winter_min,
            "prediction_ok": prediction_ok, "ok": (not failed) and prediction_ok}


def prefix_eras(bars: list[dict], sec_by_ts: dict) -> list[dict]:
    """PRE-FIX (RETIRED EU-hardcoded) segmentation, count-winner + tables, for the record."""
    def era_of(ts: int) -> int:
        for i, cut in enumerate(EU_DST_CUTS):
            if ts < cut:
                return i
        return len(EU_DST_CUTS)
    groups: dict[int, list] = {}
    for b in bars:
        groups.setdefault(era_of(b["ts"]), []).append(b)
    out = []
    for idx in sorted(groups):
        sub = groups[idx]
        table = _shift_table(sub, sec_by_ts)
        by_count = sorted(table, key=lambda t: -t["shared"])
        cw, cr = by_count[0], by_count[1]
        margin = 1.0 - (cr["shared"] / cw["shared"]) if cw["shared"] else 1.0
        by_rate = sorted(table, key=_rate_key, reverse=True)
        out.append({"era_idx": idx, "n_bars": len(sub), "table": table,
                    "count_winner": cw, "count_runner": cr, "count_margin": margin,
                    "rate_winner": by_rate[0]})
    return out


# ------------------------------------------------------------------- report / notes
def _fmt_table(table: list[dict]) -> str:
    parts = []
    for t in sorted(table, key=lambda t: t["shift_h"]):
        parts.append(f"{t['shift_h']:+d}h[n={t['shared']},a={t['agree']},"
                     f"r={t['agreement_rate']:.3f}]")
    return " ".join(parts)


def build_notes(pre: list[dict], post: list[dict], boundaries: list[int],
                overall_rate: float) -> str:
    lines = []
    lines.append(
        "ARCH-009 S4.1 second-lens overlap -- tier=BROKER (exness_xauusdm_h1, declared, "
        "never silently upgraded). Discriminator + segmentation per the DEVQ-023 ruling "
        "(Option A + 4 amendments), pre-registered in note 01KYE3BBE2PK0EP87D62S57CE6 "
        "BEFORE this run. Clock: primary = broker server time (US-DST pattern, "
        "empirically detected), second = UTC year-round."
    )
    lines.append(
        "GUARD-FIRED HISTORY: (1) the ORIGINAL sealed discriminator (shared-COUNT max + "
        "5% runner-up guard, EU-hardcoded eras) SELF-STOPPED -- all four EU eras tripped "
        "the 5% ambiguity guard (a dense hourly grid saturates the shared-COUNT of "
        "adjacent shifts). Raised DEVQ-023. (2) The Architect ratified the agreement-rate "
        "discriminator with a two-part guard (>=3x runner-up AND >=0.80) + empirical "
        "US-DST segmentation + a winter<0.90 prediction guard. This run passed every "
        "guard (below)."
    )
    lines.append("PRE-FIX tables (RETIRED EU-hardcoded segmentation; COUNT-winner + "
                 "5%-margin was the failing criterion):")
    for e in pre:
        cw, cr = e["count_winner"], e["count_runner"]
        lines.append(
            f"  EU-era{e['era_idx']} n={e['n_bars']} :: {_fmt_table(e['table'])} :: "
            f"count-winner {cw['shift_h']:+d}h vs {cr['shift_h']:+d}h margin "
            f"{e['count_margin']:.2%} (<5% => AMBIGUOUS); rate-winner "
            f"{e['rate_winner']['shift_h']:+d}h r={e['rate_winner']['agreement_rate']:.3f}"
        )
    lines.append("DETECTED boundary instants (empirical, US-DST; hour-refined): "
                 + ", ".join(f"{b} ({_iso(b)})" for b in boundaries))
    lines.append("POST-FIX tables (empirical segmentation; agreement-RATE discriminator "
                 "+ guards):")
    for e in post:
        w, r = e["winner"], e["runner"]
        lines.append(
            f"  era{e['era_idx']} [{_iso(e['start_ts'])}..{_iso(e['end_ts'])}] "
            f"n={e['n_bars']} :: {_fmt_table(e['table'])} :: CHOSEN {w['shift_h']:+d}h "
            f"r={w['agreement_rate']:.3f} (runner {r['shift_h']:+d}h r={r['agreement_rate']:.3f}); "
            f"floor(count>=90%max={e['max_shared']}):{'ok' if e['floor_ok'] else 'FAIL'} "
            f"3x:{'ok' if e['ratio_ok'] else 'FAIL'} .80:{'ok' if e['abs_ok'] else 'FAIL'} "
            f"{'winter' if e['is_winter'] else 'summer'}"
        )
    winter_rates = [e["winner"]["agreement_rate"] for e in post if e["is_winter"]]
    wmin = min(winter_rates) if winter_rates else float("nan")
    lines.append(
        f"PREDICTION GUARD: min winter agreement = {wmin:.3f} (>={WINTER_PREDICTION_MIN} "
        "required; the Architect predicted ~0.95 -- CONFIRMED). Pooled overlap "
        f"agreement_rate = {overall_rate:.3f} (interpretation threshold >="
        f"{AGREEMENT_THRESHOLD}). Reserve hours (both VIRGINs) excluded by ts range; no "
        "excluded ts appears in the overlap slice (IVF-auditable)."
    )
    return "\n".join(lines)


def _print_report(pre: list[dict], post: list[dict], boundaries: list[int]) -> None:
    print("=" * 78)
    print("ARCH-009 S4.1 clock-era alignment -- DEVQ-023 amended (agreement-rate + guards)")
    print("=" * 78)
    print("\nPRE-FIX (retired EU-hardcoded; count-winner criterion that self-STOPPED):")
    for e in pre:
        cw, cr = e["count_winner"], e["count_runner"]
        print(f"  EU-era{e['era_idx']} n={e['n_bars']:5d} count {cw['shift_h']:+d}h vs "
              f"{cr['shift_h']:+d}h margin {e['count_margin']:.2%} -> AMBIGUOUS")
    print("\nDetected boundaries:", ", ".join(_iso(b) for b in boundaries))
    print("\nPOST-FIX (empirical segmentation; agreement-rate discriminator + guards):")
    for e in post:
        w, r = e["winner"], e["runner"]
        verdict = "PASS" if e["passes"] else "STOP"
        print(f"  era{e['era_idx']} [{_iso(e['start_ts'])}..{_iso(e['end_ts'])}] "
              f"n={e['n_bars']:5d} CHOSEN {w['shift_h']:+d}h r={w['agreement_rate']:.3f} "
              f"runner {r['shift_h']:+d}h r={r['agreement_rate']:.3f} "
              f"floor={e['floor_ok']} 3x={e['ratio_ok']} .80={e['abs_ok']} -> {verdict}")


# ---------------------------------------------------------------------- persistence
def _manifest_id(store: RecordStore, dataset: str) -> str:
    for m in store.query(record_type="bulk_manifest"):
        if m.payload["dataset"] == dataset:
            return m.record_id
    raise SystemExit(
        f"no bulk_manifest for {dataset!r}; rebuild:\n"
        "  F:/QRF/.venv/Scripts/python.exe scripts/ingest_lens_feeds_s9.py --rebuild-bulk"
    )


def _load(store: RecordStore):
    bulk = BulkStore(store, BULK_ROOT)
    prim = bulk.read(_manifest_id(store, PRIMARY)).to_pandas()
    sec = bulk.read(_manifest_id(store, SECOND)).to_pandas()
    prim_manifest = _manifest_id(store, PRIMARY)
    sec_manifest = _manifest_id(store, SECOND)
    return prim, sec, prim_manifest, sec_manifest


def _to_dicts(df) -> tuple[list[dict], dict]:
    bars = [{"ts": int(r.ts), "open": float(r.open), "high": float(r.high),
             "low": float(r.low), "close": float(r.close)}
            for r in df.itertuples(index=False)]
    return bars, {b["ts"]: b for b in bars}


def _overlap_table(bars: list[dict], sec_by_ts: dict,
                   post: list[dict]) -> tuple[pa.Table, int, int]:
    """Aligned overlap slice at each era's CHOSEN shift; returns (table, n_overlap, n_agree)."""
    rows = {"ts": [], "era_idx": [], "shift_h": [],
            "p_open": [], "p_high": [], "p_low": [], "p_close": [],
            "s_open": [], "s_high": [], "s_low": [], "s_close": [], "agree": []}
    n_overlap = n_agree = 0
    for e in post:
        sh = e["winner"]["shift_h"]
        for b in _bars_in(bars, e["start_ts"], e["end_ts"]):
            sr = _matched(b, sec_by_ts, sh)
            if sr is None:
                continue
            ok = _agrees(b, sr)
            n_overlap += 1
            n_agree += int(ok)
            rows["ts"].append(b["ts"] + sh * HR_NS)   # aligned (UTC) stamp
            rows["era_idx"].append(e["era_idx"])
            rows["shift_h"].append(sh)
            for k in ("open", "high", "low", "close"):
                rows[f"p_{k}"].append(b[k])
                rows[f"s_{k}"].append(sr[k])
            rows["agree"].append(ok)
    table = pa.table({
        "ts": pa.array(rows["ts"], pa.int64()),
        "era_idx": pa.array(rows["era_idx"], pa.int64()),
        "shift_h": pa.array(rows["shift_h"], pa.int64()),
        "p_open": pa.array(rows["p_open"], pa.float64()),
        "p_high": pa.array(rows["p_high"], pa.float64()),
        "p_low": pa.array(rows["p_low"], pa.float64()),
        "p_close": pa.array(rows["p_close"], pa.float64()),
        "s_open": pa.array(rows["s_open"], pa.float64()),
        "s_high": pa.array(rows["s_high"], pa.float64()),
        "s_low": pa.array(rows["s_low"], pa.float64()),
        "s_close": pa.array(rows["s_close"], pa.float64()),
        "agree": pa.array(rows["agree"], pa.bool_()),
    })
    return table, n_overlap, n_agree


# --------------------------------------------------------------------- compute step
def compute_overlap(store: RecordStore, *, verbose: bool = True) -> dict:
    """Feeds -> reserve-excluded bars -> empirical eras -> discriminator -> guards ->
    aligned overlap table. The SINGLE compute path shared by the live append and the
    --rebuild-bulk verification. Raises SystemExit if any DEVQ-023 guard fails (never a
    silent pick / loosened guard)."""
    prim_df, sec_df, prim_manifest, sec_manifest = _load(store)
    _, sec_by_ts = _to_dicts(sec_df)
    prim_bars, _ = _to_dicts(prim_df)
    bars = sorted((b for b in prim_bars if not _in_reserve(b["ts"])), key=lambda b: b["ts"])

    pre = prefix_eras(bars, sec_by_ts)
    eras, boundaries = detect_eras(bars, sec_by_ts)
    post = evaluate_eras(bars, sec_by_ts, eras)
    if verbose:
        _print_report(pre, post, boundaries)

    verdict = guards_verdict(post)
    if verdict["failed"]:
        detail = "; ".join(
            f"era{e['era_idx']} {e['winner']['shift_h']:+d}h r="
            f"{e['winner']['agreement_rate']:.3f} floor={e['floor_ok']} "
            f"3x={e['ratio_ok']} .80={e['abs_ok']}" for e in verdict["failed"])
        raise SystemExit(
            "\n" + "!" * 78 + "\nSTOP (DEVQ-023 two-part guard): "
            f"{len(verdict['failed'])}/{len(post)} era(s) failed the discriminator guard "
            f"[{detail}]. No second_lens appended -- raise a DEVQ (a loosened guard to "
            "admit a result is the prohibited move).\n" + "!" * 78)
    if not verdict["prediction_ok"]:
        raise SystemExit(
            "\n" + "!" * 78 + "\nSTOP (DEVQ-023 PREDICTION guard): min winter agreement "
            f"{verdict['winter_min']:.3f} < {WINTER_PREDICTION_MIN} -- the Architect's "
            "US-DST prediction is WRONG for this feed. No second_lens appended; raise a "
            "DEVQ with the residual diagnosed (do not proceed on a 0.8x winter).\n"
            + "!" * 78)

    table, n_overlap, n_agree = _overlap_table(bars, sec_by_ts, post)
    overall_rate = n_agree / n_overlap if n_overlap else 0.0
    return {"table": table, "n_overlap": n_overlap, "n_agree": n_agree,
            "overall_rate": overall_rate, "pre": pre, "post": post,
            "boundaries": boundaries, "winter_min": verdict["winter_min"],
            "prim_manifest": prim_manifest, "sec_manifest": sec_manifest}


# ---------------------------------------------------------------------- rebuild path
def _load_sibling(name: str):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).resolve().parent / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rebuild() -> None:
    """Regenerate the gitignored overlap parquet from (journal + feeds) and assert its
    sha256 EQUALS the recorded overlap_manifest (ARCH-009 §1 discipline: rebuildable +
    byte-exact or loud failure). Appends NOTHING. The feed parquets are rebuilt first
    (reusing the lens ingest path), so a clean checkout reconstructs the whole chain."""
    _load_sibling("ingest_lens_feeds_s9").rebuild()   # feed parquets (hash-verified)

    store = RecordStore(JOURNAL)
    bulk = BulkStore(store, BULK_ROOT)
    n_before = len(store)

    manifests = [m for m in store.query(record_type="bulk_manifest")
                 if m.payload["dataset"] == OVERLAP_DATASET]
    if not manifests:
        raise SystemExit(
            f"no bulk_manifest for {OVERLAP_DATASET!r}; run the overlap engine first "
            "to append the second_lens, then this can verify its rebuild.")
    manifest = manifests[-1]
    recorded_sha = manifest.payload["file_sha256"]

    result = compute_overlap(store, verbose=False)
    path = bulk.path_for(manifest.record_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(result["table"], path)

    actual_sha = _sha256_file(path)
    if actual_sha != recorded_sha:
        raise SystemExit(
            f"REBUILD MISMATCH for {OVERLAP_DATASET} (manifest {manifest.record_id}):\n"
            f"  rebuilt sha256  = {actual_sha}\n  recorded sha256 = {recorded_sha}\n"
            "A rebuild that does not match byte-for-byte is a fabrication.")
    try:
        bulk.read(manifest.record_id)  # re-hashes; raises on any drift
    except BulkIntegrityError as e:  # pragma: no cover - covered by the assert above
        raise SystemExit(f"bulk.read hash gate failed after rebuild: {e}") from e
    assert len(store) == n_before, "rebuild must not append records"
    print(f"rebuilt + sha-verified {OVERLAP_DATASET}: {manifest.record_id} "
          f"({result['table'].num_rows} rows, sha {actual_sha[:16]}... == recorded)")


# ------------------------------------------------------------------------------ main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry", action="store_true", help="compute + print; append nothing")
    ap.add_argument("--rebuild-bulk", action="store_true",
                    help="regenerate the overlap parquet + assert sha == manifest (no append)")
    args = ap.parse_args()

    if args.rebuild_bulk:
        rebuild()
        return

    store = RecordStore(JOURNAL)  # verifies the chain on open

    existing = list(store.query(record_type="second_lens"))
    if existing:
        print(f"second_lens already exists ({existing[0].record_id}); nothing to do.")
        return

    result = compute_overlap(store)
    table, n_overlap, n_agree = result["table"], result["n_overlap"], result["n_agree"]
    overall_rate = result["overall_rate"]
    notes = build_notes(result["pre"], result["post"], result["boundaries"], overall_rate)
    prim_manifest, sec_manifest = result["prim_manifest"], result["sec_manifest"]

    print(f"\nGUARDS PASS. overlap n={n_overlap} agree={n_agree} rate={overall_rate:.3f} "
          f"(winter_min={result['winter_min']:.3f}).")
    if args.dry:
        print("--dry: nothing appended.")
        print("\n--- agreement_summary.notes preview ---\n" + notes)
        return

    bulk = BulkStore(store, BULK_ROOT)
    manifest = bulk.write(OVERLAP_DATASET, table, producer=PRODUCER,
                          parents=[prim_manifest, sec_manifest])
    devq023 = next(n.record_id for n in store.query(record_type="note")
                   if n.payload["text"].startswith(
                       "ARCH-009 S4.1 PRE-REGISTRATION CORRECTION (DEVQ-023"))
    lens = store.append(
        "second_lens",
        {"source_name": SOURCE_NAME, "overlap_manifest": manifest.record_id,
         "agreement_summary": {"n_overlap": n_overlap, "n_agree": n_agree,
                               "agreement_rate": overall_rate, "notes": notes}},
        producer=PRODUCER, event_ts=manifest.payload["ts_max"],
        parents=[manifest.record_id, devq023],
    )
    rep = store.verify()
    print(f"\nappended second_lens {lens.record_id} (overlap_manifest {manifest.record_id})")
    print(f"journal verify ok={rep.ok} n_records={rep.n_records} head={rep.head_hash[:12]}")


if __name__ == "__main__":
    main()

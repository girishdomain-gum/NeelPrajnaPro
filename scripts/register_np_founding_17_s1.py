"""NP-S1 deliverable 6 — register the 17 counted-only founding hypotheses
(NP-ADR-008 Appendix A.4, Owner-accepted 2026-07-30). Roster:
``F:\\NeelPrajna\\knowledge_base\\kb.json``, 18 records H-01..H-18; the 17 =
H-01..H-06, H-08..H-18 (H-07 is the lineage already sealed and registered as
``h007_np_liquidity_sweep_v1_1``, twice, in SNP-S1-03).

**Counting is not selecting** (Appendix A.4): this spends one `trial_count`
attempt per founding hypothesis (QRF-ADR-011 — the cost of an attempt is paid
at conception), all under family `xauusd/neelprajna` so the α-budget binds
across all 19. It does NOT register a full `hypothesis` record for any of the
17 — none has a calibrated instrument, a real ingested window, or a sealed
execution/threshold spec in this Kernel yet, and fabricating those fields to
satisfy the full hypothesis schema would be exactly the "placeholder /
fabrication" Appendix A.4 rules out. Which of the 17 get migrated into real
detectors + registrations, and with what n-floors, is NP-S3's ruling
(Execution Plan §7), informed by this sprint's comparison report — this
script only counts the attempts, honestly, with their kb.json provenance.

Provenance is read LIVE from kb.json (not hand-transcribed) and attached
directly to each `trial_count` record's `meta` field (kb_id, hypothesis text,
lineage tag, executable_definition, status, maturity) — going one step beyond
`TrialCountLedger.bump()`'s own wrapper (which does not expose `meta`) via the
same sanctioned `RecordStore.append` path `bump()` itself uses internally, so
provenance survives permanently on the ledger record itself rather than only
in this script's source.

Idempotent: `TrialCountLedger.bump()`/`store.append()` are NOT idempotent by
themselves (they always append) — this script checks for an existing
`trial_count` record matching `(data_scope, lineage)` before writing, same
convention as `scripts/register_h007_np_liquidity_sweep.py`.

Run:  .venv/Scripts/python.exe scripts/register_np_founding_17_s1.py
"""

from __future__ import annotations

import json
from pathlib import Path

from qrf.kernel.records.record import Record, now_ns
from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"
KB_JSON = Path(r"F:\NeelPrajna\knowledge_base\kb.json")
DATA_SCOPE = "xauusd_np_legacy_roster"  # honest label: not a real ingested Kernel dataset
FAMILY = "xauusd/neelprajna"
EXCLUDE_KB_ID = "H-07"  # already sealed as h007_np_liquidity_sweep_v1_1

# kb_id -> readable lineage slug (hand-chosen for legibility; the kb_id itself
# travels in `meta.kb_id` so the mapping is always independently checkable
# against the live kb.json, not just trusted from this table).
_LINEAGE_SLUGS: dict[str, str] = {
    "H-01": "np_h01_ma_crossover_directional_edge",
    "H-02": "np_h02_htf_candle_colourflip_continuation",
    "H-03": "np_h03_three_candle_reversal_pattern",
    "H-04": "np_h04_key_level_colourflip_bounce",
    "H-05": "np_h05_fibonacci_zigzag_poc_bounce",
    "H-06": "np_h06_smc_structures_institutional_intent",
    "H-08": "np_h08_sweep_mss_fvg_tap_ny_open",
    "H-09": "np_h09_pivot_trendline_touches",
    "H-10": "np_h10_topography_confluence_reversal",
    "H-11": "np_h11_external_poc_vah_val_levels",
    "H-12": "np_h12_l2_microstructure_state_shifts",
    "H-13": "np_h13_kalman_filtered_entry_timing",
    "H-14": "np_h14_regime_classification_sizing",
    "H-15": "np_h15_ma_filter_regime_gate",
    "H-16": "np_h16_tick_momentum_burst_continuation",
    "H-17": "np_h17_candle_pattern_universe_variant",
    "H-18": "np_h18_volume_spike_precedes_move",
}


def load_roster() -> list[dict]:
    doc = json.loads(KB_JSON.read_text(encoding="utf-8"))
    records = doc["records"]
    roster = [rec for kb_id, rec in records.items() if kb_id != EXCLUDE_KB_ID]
    if len(roster) != 17:
        raise SystemExit(
            f"expected 17 non-H-07 records in {KB_JSON}, got {len(roster)} "
            f"(kb.json may have changed since Appendix A was sealed — stop and re-check)"
        )
    missing_slugs = [r["id"] for r in roster if r["id"] not in _LINEAGE_SLUGS]
    if missing_slugs:
        raise SystemExit(f"no lineage slug mapped for kb ids {missing_slugs}")
    return roster


def _existing_bump(store: RecordStore, scope: str, lineage: str) -> Record | None:
    for r in store.query(record_type="trial_count"):
        if r.payload["data_scope"] == scope and r.payload["lineage"] == lineage:
            return r
    return None


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies chain on open
    n_before = len(store)
    roster = load_roster()

    for rec in roster:
        kb_id = rec["id"]
        lineage = _LINEAGE_SLUGS[kb_id]
        existing = _existing_bump(store, DATA_SCOPE, lineage)
        if existing is not None:
            print(f"{kb_id} ({lineage}): already counted, trial_count={existing.record_id}")
            continue

        payload = {
            "data_scope": DATA_SCOPE,
            "lineage": lineage,
            "n_attempts": 1,
            "source": "human",
            "family": FAMILY,
        }
        meta = {
            "kb_id": kb_id,
            "kb_hypothesis": rec["hypothesis"],
            "kb_lineage_tag": rec.get("lineage"),
            "kb_executable_definition": rec.get("executable_definition"),
            "kb_status": rec.get("status"),
            "kb_maturity": rec.get("maturity"),
            "kb_source_path": str(KB_JSON),
            "np_adr_008_appendix_a": "counting is not selecting; NP-S3 rules migration",
        }
        written = store.append(
            "trial_count",
            payload,
            producer="human:girish",
            event_ts=now_ns(),
            parents=[],
            meta=meta,
            schema_version=2,  # family present -> v2 (deflation totals by family)
        )
        print(f"{kb_id} ({lineage}): counted, trial_count={written.record_id}")

    report = store.verify()
    print(
        f"journal verify ok={report.ok} n_records={len(store)} "
        f"(+{len(store) - n_before}) head={report.head_hash[:12]}"
    )


if __name__ == "__main__":
    main()

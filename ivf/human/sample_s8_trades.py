#!/usr/bin/env python3
"""IVF Sprint-8 HUMAN CHECK sampler: Wave-1 verdict trades, both lineages. (rev 1)

Samples N trades per lineage directly from EACH verdict's trades-manifest
parquet — the exact trades the tri-states were computed from — and emits the
two-line input for the NEW sprint-agnostic chart tool
ivf/mt5/IVF_HC_Trades.mq5. Every parquet is sha256-verified against its
journal bulk_manifest BEFORE sampling (same rule as check_s8: if the bytes
hash to the ledger, provenance is irrelevant), and the verdict/hypothesis
ids are looked up from the journal, never hand-typed.

The PROV line carries ``label=HC_S8`` — the chart tool REFUSES to run
without a label and stamps it into every caption and PNG filename, which is
the permanent fix for the S7 captures having shipped as HC_S4_* (the old
tool hardcoded its sprint).

Entry note field (8th): FVG for H-002 rows, MON for H-003 rows — the chart
tool additionally verifies a MON entry bar actually OPENS on a Monday
(DEVQ-019's sealed contract). The exit day is captioned, not asserted: on
the real feed the 22-bar Monday hold exits in the early hours of Tuesday
(the DEVQ-019 ADDENDUM records why the ruling's "within Monday" claim was
an idealized-bars artifact — see checklist_s8.md).

Usage (paste in git bash, from /f/QRF):
  uv run python ivf/human/sample_s8_trades.py --journal datastore/journal/journal.jsonl --trades-h002 .claude/worktrees/qrf-architect-handover-cf5806/datastore/bulk/verdict_trades.h002_fvg_intraweek_follow_through/part-00000.parquet --trades-h003 .claude/worktrees/qrf-architect-handover-cf5806/datastore/bulk/verdict_trades.h003_dow_monday_drift/part-00000.parquet --n 4 --seed 8
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from datetime import UTC, datetime

NS = 1_000_000_000
LABEL = "HC_S8"
H002 = "h002_fvg_intraweek_follow_through"
H003 = "h003_dow_monday_drift"


def load_journal(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--trades-h002", required=True)
    ap.add_argument("--trades-h003", required=True)
    ap.add_argument("--n", type=int, default=4, help="trades per lineage")
    ap.add_argument("--seed", type=int, default=8)
    a = ap.parse_args()

    import pyarrow.parquet as pq

    journal = load_journal(a.journal)
    manifests = {r["payload"]["dataset"]: r for r in journal
                 if r.get("record_type") == "bulk_manifest"}
    hyps = {r["payload"].get("lineage"): r for r in journal
            if r.get("record_type") == "hypothesis"}
    verdicts = {}
    for v in journal:
        if v.get("record_type") == "verdict":
            for lin, h in hyps.items():
                if v["payload"]["hypothesis_ref"] == h["record_id"]:
                    verdicts[lin] = v

    entries: list[str] = []
    vrefs: list[str] = []
    for lineage, path, note in ((H002, a.trades_h002, "FVG"),
                                (H003, a.trades_h003, "MON")):
        dataset = f"verdict_trades.{lineage}"
        man = manifests.get(dataset)
        if man is None:
            print(f"REFUSED: no bulk_manifest for {dataset}")
            return 1
        got = sha256_file(path)
        if got != man["payload"]["file_sha256"]:
            print(f"REFUSED: {path} sha256 {got[:12]}… != manifest "
                  f"{man['record_id']} — not the ledger's bytes")
            return 1
        v = verdicts.get(lineage)
        if v is None:
            print(f"REFUSED: no verdict for lineage {lineage}")
            return 1
        vrefs.append(v["record_id"])

        rows = pq.read_table(path).to_pylist()
        rng = random.Random(a.seed)
        picks = sorted(rng.sample(range(len(rows)), min(a.n, len(rows))))
        print(f"\n{LABEL} · {lineage} · verdict {v['record_id']} "
              f"({v['payload']['verdict']}) — {len(picks)} of {len(rows)} "
              f"trades (seed={a.seed}, manifest {man['record_id']} OK)")
        for i in picks:
            t = rows[i]
            e = datetime.fromtimestamp(int(t["entry_ts"]) // NS, UTC)
            x = datetime.fromtimestamp(int(t["exit_ts"]) // NS, UTC)
            print(f"  trade {i:3d}  dir {int(t['direction']):+d}  "
                  f"entry {e:%Y-%m-%d %H:%M} @ {float(t['entry_price']):.2f}  "
                  f"exit {x:%Y-%m-%d %H:%M} @ {float(t['exit_price']):.2f}  "
                  f"gross {float(t['gross_pnl']):+.2f}  "
                  f"net {float(t['net_pnl']):+.2f}  fold {int(t['fold'])}  "
                  f"[{note}]")
            entries.append(
                f"{e:%Y.%m.%d %H:%M}|{x:%Y.%m.%d %H:%M}|{int(t['direction'])}"
                f"|{float(t['entry_price']):.2f}|{float(t['exit_price']):.2f}"
                f"|{float(t['gross_pnl']):+.2f}|{float(t['net_pnl']):+.2f}"
                f"|{note}")

    prov = (f"PROV|label={LABEL}|verdicts={','.join(vrefs)}"
            f"|seed={a.seed}|n_per_lineage={a.n}"
            f"|sampler=sample_s8_trades rev1")
    print("\nContents for HC_input.txt (copy BOTH lines exactly — the chart "
          "tool takes its label, captions and PNG names from the PROV line):")
    print(prov)
    print(";".join(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# HC-S9 · Human-check checklist · H-004 calendar-exit trades (rev-2 tool debut)

Provenance: 6 trades sampled seed=9 from the ledger's H-004 trades manifest
01KYDH7T64TNPXK0W9M0Y8B170 (sha e980e541… verified before sampling).
Reproduce the exact input any time:
`python - <<'E'` → `import pyarrow.parquet as pq, random; rows=pq.read_table('datastore/bulk/verdict_trades.h004_dow_monday_drift_v2/part-00000.parquet').to_pylist(); print(sorted(random.Random(9).sample(range(len(rows)),6)))` `E`
(indices 8, 11, 17, 23, 29, 39).

## Setup
1. Recompile `ivf/mt5/IVF_HC_Trades.mq5` (now **rev 2**: theme-safe captions,
   63-char-safe lines, dow verdict on its own third line — the REV-S8 OBS-2
   fixes; new MONX note asserts entry AND exit both open on a Monday).
2. `HC_input.txt` is already in your MT5 Files folder (written + read back).
3. XAUUSD H1 chart → drag the script, defaults. 6 PNGs `HC_S9_*.png` →
   move to `F:\QRF\ivf\reports\hc_s9\`.

## What to LOOK at (every row is MONX)
- [ ] Entry arrow at the Monday 02:00 open (second Monday bar on this feed).
- [ ] Exit check-mark at the Monday 22:00 open — **the same Monday**. This
      wave's exits must NOT spill into Tuesday: the calendar exit is the
      DEVQ-019 successor design, and Tuesday anywhere = a finding.
- [ ] Third caption line reads `MATCH eDOW=1 xDOW=1 MON-OK` in green — and
      is fully legible this time (that's the rev-2 fix being verified too).
- [ ] Direction LONG on all six.
- [ ] Line 1 readable against your chart theme (no more white-on-white).

## Reply with
MATCH count (expect 6/6), any NAVFAIL/MISMATCH/MON-BAD, and anything that
surprised you. Surprises are the product.

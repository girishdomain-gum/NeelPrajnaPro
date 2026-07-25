# HC-S8 · Human-check checklist · Wave-1 verdict trades

You are the only component of this system that has eyes. The machine has
already verified every number twice (battery + independent IVF recomputation);
your job is the part no recomputation can do — confirm the trades LOOK like
what the contracts describe, on the broker's own chart.

## Setup (once)
1. `ivf/mt5/IVF_HC_Trades.mq5` → MetaEditor → Compile (F7). This is the NEW
   generation-4 tool: it refuses to run without a `label=` in the input's
   PROV line, and stamps that label on every caption and PNG. The S7-era
   `HC_S4_*` misnaming cannot recur.
2. `HC_input.txt` is ALREADY in your MT5 Files folder (written by the
   Architect and read back; regenerate any time with
   `ivf/human/sample_s8_trades.py` — same seed ⇒ identical bytes).
3. Open an **XAUUSD H1** chart, drag the compiled script onto it, defaults
   (offset 0, tol 0.005). It navigates, annotates, screenshots, cleans up.
4. PNGs land in the Files folder as `HC_S8_<epoch>.png` (8 expected). Move
   them to `F:\QRF\ivf\reports\hc_s8\`.

## What to LOOK at — H-002 rows (4, captioned FVG)
- [ ] The three candles ENDING one bar before the entry arrow form a real
      gap: for a LONG, the candle before last never overlaps the high of the
      one two back (mirror for SHORT), and the middle candle closes in the
      trade's direction.
- [ ] Entry arrow sits at the OPEN of the bar AFTER the signal — never on
      the signal bar itself (no hindsight fill).
- [ ] Exit check-mark is exactly 4 H1 bars after entry, at that bar's OPEN.
- [ ] Caption says MATCH in green (MT5's own opens agree with the ledger).
- [ ] Nothing about the entry neighborhood spans a weekend gap (H-002
      excludes weekend-born FVGs; the IVF verified 0 leaks — your eyes are
      the second lens on that claim).

## What to LOOK at — H-003 rows (4, captioned MON)
- [ ] Entry arrow at the OPEN of the second Monday bar (02:00 UTC on this
      feed — Mondays here begin with the 01:00-open bar). Caption must show
      `MON-OK`.
- [ ] Direction is LONG on every row (the claim is fixed-long).
- [ ] Exit lands in the EARLY HOURS OF TUESDAY (~01:00 open, two rows
      ~03:00). **This is correct, not a bug**: the sealed contract is
      hold-22-bars, and on the real feed that spills past midnight — the
      DEVQ-019 ADDENDUM records that the ruling's original "within Monday"
      wording was an idealized-bars error. If an exit lands anywhere OTHER
      than early Tuesday (or the caption shows MON-BAD), that is a finding.
- [ ] Caption says MATCH in green.

## Then reply to the Architect with
1. MATCH count the script prints at the end (expect 8/8).
2. Any NAVFAIL, MISMATCH, or MON-BAD — filename + what you saw.
3. Anything that surprised you, however small. Surprises are the product.

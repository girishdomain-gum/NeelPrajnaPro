# IVF Human Checklist — Sprint 2 (≈15 minutes)
Owner runs this; sign-off closes HC. Samples are drawn by the tools,
not chosen by you.

## Prep (once)
1. In MT5: MetaEditor → compile `ivf/mt5/IVF_S2_Export.mq5` (copy it to
   the terminal's `MQL5\Scripts\`), then run it on your chart symbol
   with a one-month window, H1, RSI period 14. Output lands in
   `MQL5\Files\IVF_S2_<symbol>_PERIOD_H1.csv` — copy it to `F:\QRF\`.
2. qrf-side event export (implementation side may produce files; IVF
   only consumes them). From F:\QRF, run the sanctioned snippet:

   ```bash
   uv run python - <<'EOF'
   import csv, pyarrow as pa
   from qrf.trading.concepts.seasonality.detector import SeasonalityDetector
   from qrf.trading.concepts.classical.detector_rsi import RSIDetector
   # load the MT5 export; ts basis = CLOSE time (REV-S2 OBS-4)
   rows=[r for r in csv.DictReader(open("IVF_S2_XAUUSD_PERIOD_H1.csv"))]
   ts=[int(r["time_close_sec"])*10**9 for r in rows]
   close=[float(r["close"]) for r in rows]
   bars=pa.table({"ts":pa.array(ts,pa.int64()),"close":pa.array(close,pa.float64())})
   evs=[]
   for det in (SeasonalityDetector(), RSIDetector()):
       t=det.detect(bars)
       evs += [dict(ts=t.column("ts")[i].as_py(),
                    event_type=t.column("event_type")[i].as_py(),
                    direction=t.column("direction")[i].as_py())
               for i in range(t.num_rows)]
   with open("s2_events.csv","w",newline="") as f:
       w=csv.DictWriter(f,["ts","event_type","direction"]); w.writeheader()
       w.writerows(sorted(evs,key=lambda e:e["ts"]))
   print("wrote", len(evs), "events")
   EOF
   ```
   (If SeasonalityDetector's constructor needs session params, copy them
   from its instrument_registered record in the journal — by eye.)

## VC — the independent comparison
```bash
python ivf/checks/check_s2_detectors.py --mt5 IVF_S2_XAUUSD_PERIOD_H1.csv \
  --events s2_events.csv --sessions london=28800-57600 \
  --report ivf/reports/s2_verify.json
```
Expected: GREEN, or AMBER only with near-threshold RSI explanations
(REV-S2 OBS-5) — write a one-line explanation per amber at sign-off.
Any RED: stop; that disagreement is the finding; tell the Architect.

## Drill S2 — the planted hindsight bug (must be caught)
```bash
python ivf/checks/drill_s2.py --events s2_events.csv --bar-seconds 3600 \
  --out s2_events_tampered.csv
python ivf/checks/check_s2_detectors.py --mt5 IVF_S2_XAUUSD_PERIOD_H1.csv \
  --events s2_events_tampered.csv --sessions london=28800-57600 \
  --report ivf/reports/s2_drill.json
```
Expected: RED (timestamp mismatches). Delete s2_events_tampered.csv after.

## HC — eyes on charts (10 events per detector)
```bash
uv run python scripts/hand_audit_s2.py
```
For each sampled RSI event: open that bar on the MT5 chart with RSI(14);
confirm the crossing is visibly there AT THAT BAR'S CLOSE (not a bar
later — hindsight check). For each seasonality marker: confirm the
session/day boundary is where the event says. Anything off → note it.

## Sign-off
Reply to the Architect: "S2 VC <GREEN/AMBER+explained>, drill RED
caught, HC done — sign off Sprint 2" (or raise findings instead).

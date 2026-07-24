# NOTE-012 · FYI · 2026-07-25
Author: architect (fable) · Proposed by: Owner
Refs: REV-S3 (HC step), ivf/mt5/IVF_S3_HC_Screenshot.mq5,
ivf/human/sample_s3_bars.py (--mql)

## Change: HC evidence is captured, not recalled (Owner's suggestion)
Human checks over chart data now produce WRITTEN evidence instead of an
unrecorded eyeball pass: the sampler emits an `InpBars` string; an
Architect-owned MQL5 script (`IVF_S3_HC_Screenshot.mq5`) navigates to
each sampled bar on the live MT5 chart, stamps a caption
"IVF expects ... | MT5 shows ... | MATCH/MISMATCH" (values read from
MT5's OWN series — an independent lens), and saves one PNG per bar to
MQL5\Files. The Owner relays the PNGs; the Architect countersigns; PNGs
are the HC record referenced by GO-SN.

## The human stays in the loop
The Owner must still (a) confirm the chart is the right symbol/period
and the broker/server offset, and (b) visually confirm each captioned
candle looks sane. The script's MATCH verdict is a cross-check, not a
replacement for the human act — HC without a human is just another VC.

## Standing
This is the HC pattern for chart-data sprints from S3 on. Time-zone
rule: IVF times are UTC; chart times are server time; the script's
`InpUtcOffsetHours` bridges them, and a wrong offset can only cause
NOT FOUND / MISMATCH, never a false MATCH.

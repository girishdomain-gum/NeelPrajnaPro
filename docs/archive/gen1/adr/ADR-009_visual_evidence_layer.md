# ADR-009 · Visual evidence capture as a standing verification layer
Status: Accepted · 2026-07-25 · Proposed by: Owner (Girish) · Drafted by: Architect
Refs: NOTE-012, REV-S3 addendum, ivf/mt5/IVF_S3_HC_Screenshot.mq5 (rev 4)

## Context
HC-S3 replaced "trust me, I looked" with captioned chart screenshots taken
by MT5 itself — an independent lens — carrying expected-vs-observed values
and a computed MATCH/MISMATCH. The evidence is written, relayable,
archivable, and countersignable; the human eye stayed in the loop and
caught a real tool defect (rev-2 wrong-period capture) that numeric logs
alone had hidden. Sprints 4+ introduce chart-anchored claims everywhere:
SMC zones, screener candidates, trend structures, entry/exit signals.

## Decision
Visual evidence capture is a STANDING layer of the verification process
for all chart-anchored claims, alongside (never instead of) VC/HC/Drill:

1. **Scope.** HC bar sampling (S3 pattern) and, from Sprint 4 on, signal
   overlays: sampled detector events, screener hits, SMC zones, and
   strategy entries/exits are rendered on the MT5 chart with markers/
   zones/lines plus captions.
2. **Captions are evidence, not decoration.** Every capture carries:
   the claim (expected values/levels/times from QRF records), what MT5's
   own series shows, the computed verdict, and a PROVENANCE line —
   dataset, manifest id, record ids, sampler seed, tool name + rev.
3. **Pictures illustrate, numbers decide.** Verdicts are always computed
   from data (IVF checks, calibration comparisons). A screenshot can
   support, document, or falsify — it can never be the sole basis of a
   PASS. A capture that contradicts the numbers FREEZES the claim until
   resolved (IVF discipline).
4. **Ownership & home.** Capture tools are Architect-owned IVF
   instruments in ivf/mt5/; evidence is archived under ivf/reports/
   (hc_*/ , vis_*/) and referenced by REV-SN / GO-SN. The repo copy of
   an .mq5 tool is the source of truth; the MT5 Scripts copy is a
   deployment the Owner refreshes.
5. **Human in the loop.** The Owner (or Architect over relayed PNGs)
   visually confirms each capture; NOTE-012's rule stands — HC without
   a human is just another VC.

## Consequences
- Per-sprint tooling cost (one capture tool revision per new claim type);
  paid willingly — it bought bug-catches on its first night.
- MT5 must remain available as an independent rendering/data lens.
- Queued first improvement (rev 5, Sprint 4): provenance caption line +
  title-collision fix (REV-S3 addendum).

# PROGRAM RETRO 001 · Sprints 1–6 introspection · 2026-07-25
Requested by: Owner · Written by: Architect · Status: honest, on the record
Companion: docs/reference/External_Libraries_Catalog.md (Owner's compiled
reference, adopted this date)

## What six sprints actually built
An append-only, hash-chained ledger (31 records, never broken) · four
calibrated detectors that must pass planted-truth AND stay silent on
noise before speaking · a data plane that flags and never repairs · a
screener that is structurally incapable of judging and counts every one
of its 500 attempts · an engine that cannot look ahead by construction,
deterministic to the byte, pessimistic about every ambiguous fill · a
judge that passes its own exam daily · corrections that follow CLAIMS
and got stricter mid-flight with the date on file · one pre-registered
hypothesis judged FAIL on a burned year · a VIRGIN reserve no code path
can touch · and a verification culture (IVF + drills + captured visual
HC) that caught 12 first-contact bugs — 10 of them in the CHECKERS —
before any reliance, and independently rediscovered a known library
defect (look-ahead in SMC swings) from first principles.

## Is the validation process sufficient? Honest answer: strong core,
## with named gaps
The 5-screenshot HC is NOT the validation — machine checks are
exhaustive (all events, all trades, all folds, byte determinism). The
pictures buy human comprehension, and the human eye has caught a real
bug. VERDICT: the layering is right. Improvements adopted:
- **HC-1 (adopted, S7 on): stratified HC sampling** — best trade, worst
  trade, one boundary case (gap/weekend), two random. Same cost, more
  signal.
- **G-1 SINGLE DATA LENS (the biggest real gap).** Everything rests on
  one retail CFD broker feed (the Owner's own catalog: "Retail CFD /
  MT5: usually synthetic books — transfer testing mandatory"). Our MT5
  cross-checks verify CONSISTENCY with that lens, not TRUTH about the
  market. Any edge found must survive a second, independent feed before
  it is believed. Action: a second-source ingest (even one overlapping
  month from another broker/provider) becomes a gate BEFORE any PASS
  verdict is trusted for real decisions; full microstructure feeds
  (catalog §4) are the Gen-2 path.
- **G-2 SINGLE INSTRUMENT / TIMEFRAME.** XAUUSD H1 only. Findings may
  be venue or timeframe artifacts. Action: transfer testing enters at
  family-wave time (S8+): a claim that only works on one instrument at
  one timeframe is a weaker claim by declaration.
- **G-3 PLACEBO RUNS not yet standing.** Calibration has noise-silence
  cases (partial placebo), but the FULL pipeline has never been run on
  a label-shuffled / synthetic-null version of real data to confirm it
  finds nothing. Action: placebo battery run becomes part of the
  verdict gate from the next hypothesis on (the catalog names placebo
  survival as first-class — agreed).
- **G-4 STATISTICS ARE DELIBERATELY MINIMAL.** One-sided t + bootstrap
  + Bonferroni. Fine for FAIL-heavy early life; before any PASS is
  celebrated, stronger multiplicity tools (deflated Sharpe, reality
  check) should arrive via ADR. Logged for S8+.

## Were the best tools chosen? With the Owner's catalog now in hand
Choices to date align with the catalog's recommendations
(smartmoneyconcepts for SMC — with our own knowability wrapper fixing
exactly the defect the catalog flags; pandas-ta; vectorbt; scipy/
statsmodels/arch). Adopted from the catalog:
- **T-1:** smc-toolkit noted as a candidate SECOND independent SMC
  implementation — cross-library validation of detectors (IVF pattern
  at the library level) when SMC families expand.
- **T-2:** TA-Lib enters as the TRUSTED BASELINE layer when classical
  families arrive (S8).
- **T-3:** The catalog's Architectural Role Classification (§6) is
  ADOPTED as the standing vocabulary for external code: TRUSTED
  BASELINE / UNPROVEN / VISUAL ONLY / SYNTHETIC FIXTURE. Nothing
  UNPROVEN touches the belief layer except through a calibrated
  detector — which has been our rule; now it has the shared name.
- **T-4:** Microstructure (order flow, DOM, LOB) is explicitly Gen-2:
  the current bar-based laboratory must first prove it can find and
  confirm ANY edge end-to-end. Data-feed economics (catalog §4) make
  this the right sequencing, not a compromise.

## Is the direction correct? Yes — with one warning we give ourselves
The direction is correct BECAUSE the first verdict was a trustworthy
NO: the machinery for honest answers exists, which is the hard part and
the part almost nobody builds. The warning: process can become its own
reward. Six sprints built the courtroom; the next phase must be judged
by DISCOVERY throughput — questions raised (S7), families tested (S8),
hypotheses judged per month — under the same discipline, not by more
courtroom. If, several family waves from now, everything still FAILs,
that too is a finding about retail-visible bar-data edges, and the
Gen-2 microstructure path (better lenses, not looser standards) is the
answer — never threshold erosion.

## Standing decisions from this retro
HC-1 stratified sampling (S7 on) · G-1 second-lens gate before any
trusted PASS · G-3 placebo run in the verdict gate (next hypothesis on)
· T-1..T-4 catalog adoptions · discovery-throughput as the phase-2
success metric. Owner's catalog PDFs to be placed by the Owner under
docs/reference/ (binary; Architect cannot copy them cross-system).

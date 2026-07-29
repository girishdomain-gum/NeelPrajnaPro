# Phase 6 examples — Sequential Strategy Engine (design doc v1.1)

Illustrative artifacts for the SSE design. NOTHING here is parsed by
the EA yet — the InpSeq_* inputs and the SeqCodex parser arrive with
stage 6a. Kept in docs/ (not NPSU_Strategies/) on purpose.

| File | What it shows |
|---|---|
| KL_SweepConfirm.seq | The motivating 2-step chase (initiate T3 → confirm T1\|T8) |
| TrendPullback_Fibo.seq | Guard-as-precondition idiom; WIN:0 waiting step |
| StructBreak_Retest3.seq | K=3; GUARD:NONE + INV carrying protection |
| NeelPrajna_SEQ_KL_SweepConfirm.set | A full MT5 preset carrying the sequence as InpSeq_* strings |
| NeelPrajna_STATIC_T1_B1B6.set | Today's static form + inert InpSeq_ block (backward compat) |
| KL_SweepConfirm.idea | seqgen.py input for the SEQ case |
| T1_B1B6.idea | seqgen.py input for the STATIC case (usable TODAY) |

Generate fresh .seq/.set from an idea:

    python C:\NeelPrajna\repo\tools\seqgen.py <file>.idea

seqgen validates gate classes (GUARD/INV static-only, ADV dynamic-only),
K ≤ 4, window bounds, and stamps both outputs with the FNV-1a content
hash the 6a parser must reproduce (design doc §11, D12).

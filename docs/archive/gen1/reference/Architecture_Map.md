# Architecture Map (one page)

Idea flow:  data → detectors → events → composer → screener →
battery → verdict → beliefs/graph → next question.

Layers (Architecture Ch.4): kernel {records, instruments, registry,
protocol, battery, corrections, belief, observatory, graph, ops} +
trading plug-in {adapters, payloads, simulator, utility, concepts}.

Only writers: store.append (all records) · battery (verdict,
window_burn) · screener (trial_count bumps) · belief.update
(belief_update). Everything else proposes files or reads.

Authoritative order: journal.jsonl > bulk parquet (via manifests) >
DuckDB index (derived, deletable) > dashboards (views only).

Documents: Architecture (what/why, frozen) → Blueprint (how) →
IVF (proof) → ADRs (decisions) → this map (orientation only).

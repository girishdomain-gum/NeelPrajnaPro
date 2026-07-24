# QRF Glossary

Short definitions of the project's dialect. Non-authoritative — the
Architecture and Blueprint define behaviour; this page only reminds.

- **Record** — the atom: immutable, dated, source-stamped assertion in
  the append-only journal. Everything is a typed record.
- **Instrument** — anything that produces records: data feeds,
  detectors, the battery itself. Never trusted uncalibrated.
- **Thermometer test / Calibration** — an instrument must find a
  hand-planted textbook case and stay silent on structured noise
  before its output counts.
- **EventFrame** — the one event table schema every detector emits
  (ts, event_type, direction, level, zone_hi/lo, strength, meta).
- **Knowability** — an event's timestamp is the first moment it could
  have been acted on; confirmation lag lives inside the detector.
- **Freezing / Pre-registration** — rules and outcome meanings are
  hashed into the ledger before any results exist.
- **Window** — a declared data interval: TRAINING, EXPLORATION, or
  VIRGIN (reserved for final verdicts).
- **Burning** — a verdict consumes its window for that lineage; the
  machine refuses overlapping reuse.
- **Contamination rule** — the Observatory may study only spent or
  exploration data, never virgin reserves (the "Tuesday trap").
- **Trial count** — how many things were ever tried against a data
  scope; raises the statistical bar for every survivor (the
  1,000-coins correction).
- **Battery** — the judge: six protections, verdicts PASS / FAIL /
  INSUFFICIENT; must pass its own selftest the day it judges.
- **Belief layer / Trust scores** — per-family odds updated by
  verdicts, weighted by the battery's measured reliability; prioritizes
  the queue, never judges.
- **Mechanism** — an inferred hidden cause stored in the knowledge
  graph ("prediction first, ontology later").
- **Manifest** — journal record holding a bulk parquet file's hash and
  schema; the ledger's handle on heavy data.
- **IVF** — Independent Verification Framework: outside party that
  reproduces results (MT5 tools, reference values, human checklists).
- **Drill** — a deliberately planted bug the IVF must catch before a
  sprint may close.
- **Golden pocket / OTE** — Fibonacci retracement zones (50–61.8% /
  61.8–79%); tested only against width-matched placebo zones.

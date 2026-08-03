# HYPOTHESIS SPECIFICATION — the Concept / Measurement / Judgment separation
**Status:** ARCHITECTURE. Introduced by AM-04 (Owner-originated, O-017).
Applies to every hypothesis family in NeelPrajna, forever.

---

## 0. The distinction this document exists to protect

> A hypothesis is not the same thing as one way of measuring it.

Three separate things, never collapsed into one another:

| | What it is | Changes how often |
|---|---|---|
| **CONCEPT** | The market phenomenon we are trying to understand | Rarely. A change mints a new concept. |
| **MEASUREMENT** | One operational definition used to observe that concept | Several may exist per concept |
| **JUDGMENT** | The statistical evaluation of ONE measurement on virgin time | Once per registered measurement |

**The failure this prevents:** registering "sweeps predict reversal within 12
bars", getting a verdict, and thereafter treating 12 bars as the meaning of
the concept. The horizon was an instrument. The concept was never about 12.

**Corollary, binding:** no measurement may be described anywhere — in code,
report, verdict or Contract — as if it were the concept. A verdict speaks
about the MEASUREMENT it judged, and about the concept only to the degree the
specification says that measurement bears on it.

---

## 1. The six required sections

Every CONCEPT SPECIFICATION carries exactly these, written BEFORE any
measurement is registered.

### 1.1 SCIENTIFIC CLAIM
The phenomenon, in plain language, with no numbers, no timeframes, no bar
counts, no thresholds. If a constant appears here, it belongs in a
measurement instead. One or two sentences. It must be possible for the world
to fail to contain this phenomenon.

### 1.2 OBSERVABLE CONSEQUENCES
What must be TRUE OF THE DATA if the claim holds — still stated without
operational constants. These are the bridge between an idea and anything
testable, and they are what later measurements must each be traceable to.
State also what would be true if the claim is FALSE; a consequence that
obtains either way is not a consequence.

### 1.3 ALTERNATIVE MEASUREMENT METHODS
**Every** operational definition this concept licenses, enumerated NOW, each
with: its name, exactly what it computes, which consequence in §1.2 it
observes, and what would count as evidence for and against.

This section is where the constants live — horizons, thresholds, ratios. They
are properties of an INSTRUMENT, never of the concept.

**BINDING (the anti-fishing rule):** measurements not listed here may still be
used later, but each is then a NEW registration, disclosed as a
post-specification addition and charged accordingly. Enumerating five
measurements and reporting only the one that reached significance is
forbidden — every registered measurement's result is reported, including
those that found nothing.

### 1.4 DETECTOR DEPENDENCIES
Which detectors each measurement requires, at which versions. A measurement
whose detectors do not yet exist is legitimate to specify and NOT yet
registrable — it waits. This section makes "we cannot test this yet" a
visible fact rather than a silent omission.

### 1.5 ASSUMPTIONS
What must hold for a measurement of this concept to mean anything: data
integrity, instrument, session structure, clock basis, sampling. Each stated
so it could be checked, and marked whether it currently IS checked.

### 1.6 BOUNDARY CONDITIONS
Where the concept is NOT claimed to apply, and what would make a result
inapplicable rather than merely negative. A claim with no boundary is not a
claim about the world.

---

## 2. How alpha is charged (AM-03 + AM-04 together)

The concept holds an allocation from its family's budget. Each REGISTERED
MEASUREMENT spends from it. Consequences:

- Measurements are pre-declared (§1.3), so the number of ways this concept
  could be tested is known BEFORE any of them is run.
- A measurement that is specified but never registered spends nothing.
- Every registered measurement's verdict is recorded and reported, whatever
  it says. Silence about a null result is the fishing this structure exists
  to prevent.
- A later, unspecified measurement is a new registration, marked
  post-specification, never retro-fitted into the original.

## 3. What a verdict may then say

A verdict states: this MEASUREMENT, on this data, on this window, produced
this statistic, with this p-value, against this alpha, under this null.

It may NOT state that the concept is true. The concept accumulates evidence
across measurements; a single verdict is one observation of one consequence
through one instrument. The belief layer (S08) is where that accumulation
happens — and it consumes verdicts, never raw measurements.

## 4. Relationship to existing law

- **AM-01** (Detector SDK): detectors produce observations; measurements are
  computed FROM observations. A detector still never vouches for itself, and
  now also never defines a concept.
- **AM-02** (thin hands, one brain): concepts and measurements both live in
  the left organ. The runtime holds neither.
- **AM-03** (per-family budget): unchanged. This document says WHERE within a
  family the spending happens — per measurement, from the concept's share.
- **DOC-IS-SPEC**: the concept specification is the governing document. Where
  code and specification diverge, the specification governs and the code is
  a finding.

## 5. Format and location

One markdown file per concept: `docs/concepts/<CONCEPT-ID>.md`, with the six
sections in order. Versioned in git. Amendments to a specification follow the
usual rule — history is never rewritten; a change that alters §1.1 mints a
NEW concept rather than editing the old one.

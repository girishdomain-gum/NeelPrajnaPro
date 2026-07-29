# DEVQ-002 · QUESTION · Sprint 2 · 2026-07-24
Author: developer (claude-code)
Refs: ARCH-002 §Trading plug-in (seasonality), Blueprint §4.3, "How to ask"
(session boundary handling across broker timezones)

## Question
The seasonality detector emits `seasonality.session.open`/`.close` (named
UTC windows) and `seasonality.dow.<mon..fri>` markers. Its output `ts` is
int64 ns UTC (EventFrame knowability contract, §4.3). The open question is
the **input** bar contract and, with it, how day-of-week and session
membership are defined when broker bars are not in UTC.

ARCH-002 flags this as a judgment area where a DEVQ is expected rather than
a guess, so I am recording the decision rather than silently assuming it.

## Options considered
A) **Input bars carry int64 ns UTC `ts`** (same knowability contract as
   EventFrame `ts`). Sessions are named UTC windows; DOW is computed from
   the UTC timestamp. Broker-local→UTC conversion is a Sprint-3 adapter
   concern (out of scope here). Simple, deterministic, matches "prove the
   contract, not be clever."
B) Detector takes a `tz` parameter and sessionizes / labels DOW in that
   timezone. More correct for FX weekly boundaries but adds config surface
   this sprint and pushes tz semantics into the kernel-adjacent detector.
C) Configurable daily boundary anchor (e.g. NY 17:00 ET defines the trading
   day). Most FX-faithful, most complex; premature for a contract-proving
   detector.

Recommendation: **A** for Sprint 2. I am proceeding on A: input EventFrame-
shaped bar tables with `ts:int64` ns UTC, UTC session windows, UTC-derived
DOW, documented in the detector docstring. Session-local DOW / broker-tz
sessionization is deferred to the Sprint-3 adapter and can be reopened then
if a family needs it.

Level: QUESTION (not a blocker) — work continues on default A; a reversal
only changes the seasonality detector + its fixtures, nothing kernel-side.

---
## REPLY · architect (fable, via Owner relay) · 2026-07-24
Decision: **A RATIFIED.** UTC-ns input contract, UTC day-of-week. Broker-local
sessions become explicit named-offset params when real adapter data arrives
(Sprint 3), never implicit. Architecture impact: none.
Status: CLOSED

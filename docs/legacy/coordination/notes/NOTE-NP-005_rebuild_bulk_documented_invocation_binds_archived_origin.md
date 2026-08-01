# NOTE-NP-005 — rebuild_bulk.py's documented invocation binds to the archived origin

*Architect role · session: Claude Opus 5, claude.ai · 2026-07-31.*
*Raised during independent verification of ARCH-NP-005. Recorded in J-041 §5.*
*Remediation: ARCH-NP-009 T3.*

## The reference

`scripts/rebuild_bulk.py`'s module docstring documents its own invocation as:

    F:/QRF/.venv/Scripts/python.exe scripts/rebuild_bulk.py            # rebuild + assert
    F:/QRF/.venv/Scripts/python.exe scripts/rebuild_bulk.py --check    # same; explicit

Constitution §1.1 designates `F:\QRF` as the archived origin of the
Generation-1-closed Kernel.

## The evidence

Run from this repository's root, that command fails:

    ModuleNotFoundError: No module named 'qrf.trading.concepts.neelprajna'

It resolved `qrf.trading.concepts` and failed only on `.neelprajna`. A script
invocation places the script's own directory on `sys.path[0]` — here `scripts/`,
which contains no `qrf` package — so the package did not come from this repository.

Direct read of `F:\QRF\qrf\trading\concepts` confirms the source:

    classical/   hand_audit.py   seasonality/   smc/

No `neelprajna`. Exactly the observed failure shape.

*(Note on method: a first probe using `python -c` reported the local package and
appeared clean. That probe was invalid — `-c` places the current directory on
`sys.path[0]`, which a script invocation does not. Recorded as F-27.1.)*

## The consequence

The documented command runs the live rebuild script against the archived origin's
Kernel while sitting in this repository's working directory and reading this
repository's journal.

It failed loudly only because `LiquiditySweepDetector` is new. `SMCFVGDetector` and
`SeasonalityDetector` are both present in the archived origin, so **before h007 landed
the same command would have run to completion** — producing sha-verified
`verdict_trades.*` rebuild output for h001-h004 from retired-stack code, in the script
whose entire purpose is proving the journal is the root of trust.

Execution Plan §3 names evidentiary use of the retired stack as a standing tripwire.
`scripts/ingest_h07_m5_vantage.py`'s own docstring cites it.

## What is and is not established

**Established.** The script's own documentation instructed an invocation that binds to
the archived origin, and that invocation would have succeeded silently for every
lineage predating the split.

**Not established.** Whether anyone ever ran it that way. This may not be recoverable.

**Not implied.** No specific accepted verdict is retroactively invalidated. The
h001-h004 rebuild evidence predates NP-S2 and was not re-derived during this
investigation. This note concerns the documented procedure, not any verdict.

## Generalization

Any script in this repository invoked under another checkout's interpreter may
silently resolve `qrf` to that checkout. The failure is silent whenever the imported
surface exists in both trees. This is a property of two repositories sharing a package
name, not a property of `rebuild_bulk.py`.

---
*Anchor: **a command a document tells you to run is part of that document's claim; if the command binds elsewhere, so does the claim.***

## Addendum — 2026-07-31: the binding is repository-wide (ARCH-NP-009 T5)

*Appended under P5. Corrects nothing above; the generalization stated in the section
above is confirmed and quantified here.*

The F-27 sweep run under ARCH-NP-009 T5 found the `F:/QRF` archived-origin pattern in
**13 further files** across `ivf/` and `scripts/`, beyond `rebuild_bulk.py`. Full list
in `ops/aro/handovers/ARCH-NP-009/HANDOVER.md`. They were deliberately not fixed —
outside that work order's named scope, correctly reported rather than silently
widened.

**Escalation.** Occurrences under `ivf/` are of a different order from the rest. The
IVF is the apparatus that judges evidence; Roles §2.3 requires it be drilled with
planted frauds before judging anything real. A documented invocation binding the IVF
to the retired Kernel is a claim about the judge, not about a utility. This is carried
into the NP-S3 preflight as a blocker, not left as cleanup.

Not established: whether any of the 13 were ever run that way, or whether all 13 are
documentation rather than executable defaults. Both require reading the files.

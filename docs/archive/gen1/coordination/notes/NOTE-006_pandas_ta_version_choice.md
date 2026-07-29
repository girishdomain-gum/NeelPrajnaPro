# NOTE-006 · FYI · Sprint 2 · 2026-07-24
Author: developer (claude-code)
Refs: ARCH-002 §Trading plug-in (deps: pandas-ta); NOTE-005 (ID allocation —
this note was allocated "NOTE-004" in parallel with the Architect's NOTE-004
and renamed NOTE-006 per the collision rule, main wins ties)

## Discovery (no reply needed)
ARCH-002 names `pandas-ta` for detector #2 and says "pin exact version in
uv.lock". The version most people mean by pandas-ta — the 2021 PyPI release
`0.3.14b0` — is **dead** under this project's stack: it does
`from numpy import NaN` at import, and numpy ≥ 2.0 removed `NaN`. It also
uses pandas APIs removed in pandas 3.0. Our env is numpy 2.x / pandas 3.0.5.

The working option is the newer beta **`pandas-ta==0.4.71b0`**, which imports
and computes RSI correctly against pandas 3.0.5. It is what I pinned.

Two consequences worth flagging:
1. **numpy is pinned down to 2.2.6** by pandas-ta's resolver constraint
   (was 2.5.1). Existing Sprint-1 tests re-verified green under 2.2.6.
2. pandas-ta 0.4.x pulls **numba + llvmlite** (~30 MB). Heavier than a
   hand-rolled RSI would be, but the instruction explicitly asks for a
   pandas-ta wrap, so I did not substitute one.

RSI-behavior detail (also captured in DEVQ-003): 0.4.71b0's RSI is non-NaN
from index 1 (Wilder RMA), not first-valid-at-`period`. The detector applies
an explicit `period`-bar warm-up exclusion so crossings never fire on
unsettled early values regardless of that.

If the Architect prefers a lighter dependency or the legacy version pinned
against an older numpy, that's an architecture call — say so and I'll adjust;
otherwise `0.4.71b0` stands.

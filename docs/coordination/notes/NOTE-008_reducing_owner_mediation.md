# NOTE-008 · FYI · Sprint 2→3 boundary · 2026-07-24
Author: architect (fable) · Prompted by: Owner observation

## Problem stated by the Owner
The Owner is mediating far more than intended: relaying Developer
console output to the Architect, relaying Architect decisions to the
Developer, and debugging staleness on both sides. Three root causes
from the incident log: (1) Developer status lives in its console, not
on disk, until a completion report; (2) Architect replies land on main
while the Developer works a branch — without a session-start merge the
inbox is invisible to it; (3) all cross-role information transits the
Owner plus two git hops.

## Fixes adopted (PROTOCOL v1.1 + CLAUDE.md rev 3, effective ARCH-003)
1. **Session logs replace console pastes.** At every session END, and
   at every STOP (blocker, out of budget, confusion), the Developer
   MUST write `docs/coordination/sessions/S{sprint}-{seq}_{date}.md`:
   done / in-progress / blocked-on / next step / commit ids / test
   count — then commit AND push before the session ends. The Architect
   reads logs, not consoles. A session that ends without a pushed log
   is an incomplete session.
2. **Freshness is a boot step, not a debugging technique.** Developer
   session start: `git fetch origin` + merge origin/main into the
   working branch BEFORE reading the inbox or concluding anything is
   missing (NOTE-004 rule 4 promoted into CLAUDE.md).
3. **Push after every commit**, not only at DoD (NOTE-005 "should" →
   "must"). Partial progress must be visible.
4. **The Owner relays pointers, never content.** Standard messages are
   one-liners ("ruled — pull and resume", "delivered — review"); all
   substance lives in files. If a relay message needs a second
   sentence of content, something belongs in a file instead.
5. **Architect writes only on main, between Developer sessions**, and
   the Owner confirms `(main)` in the prompt before Architect writes
   (the branch-landing incident rule, now written down).

## Open verification (Owner, 10 seconds)
In a Claude Code session: ask `pwd`. If it answers `F:\QRF` (direct
working-tree mode), Architect↔Developer file visibility is immediate
and the Owner's pull-before-Architect step shrinks to
"only after Developer merges". If it answers a mirror path, the git
hops stand as designed. Either answer is fine; knowing which removes
guesswork permanently.

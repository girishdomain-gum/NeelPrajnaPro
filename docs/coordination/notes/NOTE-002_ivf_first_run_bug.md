# NOTE-002 · FYI · Sprint 1 close · 2026-07-24
Author: architect (fable)
Refs: ivf/verify_journal.py, IVF v1.0 §5.4 ("the IVF can be the buggy one")

## Discovery (no reply needed)
On its first real invocation, ivf/verify_journal.py rev 1 crashed
(IndexError) instead of reporting: the summary computation assumed every
finding key contains a dot, but the missing-file finding key ("file")
does not. The very first failure path — journal absent — was therefore
unreportable.

Recorded openly because IVF §5.4 anticipates exactly this: the verifier
is code too, and its defects are findings of the same standing as
implementation defects. Fixed in rev 2 (robust `implicated()` helper;
C5 also hardened against self-parent references; C4 no longer lets a
malformed id poison the monotonicity baseline).

Secondary finding, expected: no journal existed at first verification —
Sprint 1 built the machinery without appending records. Genesis records
are seeded at Go/No-Go (Owner action) so Drill S1 has something real to
tamper with.

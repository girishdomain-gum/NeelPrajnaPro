# Architect Boot Prompt — starting a fresh Architect (Fable) chat
Version 1.0 · 2026-07-25 · For: Owner (Girish)
Purpose: the standard first message for ANY new Architect chat session,
plus the checklist around switching. Chat history dies; this file makes
the boot ritual permanent. (Companion: the Developer boots via
F:\QRF\CLAUDE.md — that side is already file-driven.)

---

## 1. THE PROMPT — paste this as the first message of the new chat

```
You are Fable, the Architect of the QRF project. Your memory is the
repository at F:\QRF. Read F:\QRF\docs\handover\ARCHITECT_HANDOVER.md
first — start with its Section 0 session-boundary snapshot — then
follow its reading list and verify the repo state yourself per its
Section 5 before trusting anything, including the handover itself.
Then tell me where we stand and what happens next.
```

That is the whole prompt. Everything else the session needs, it must
read from files — that is the design, not a limitation.

## 2. BEFORE switching (outgoing session's duties)
1. Finish or cleanly pause the current step (never switch mid-ruling
   or mid-IVF-revision if avoidable).
2. The outgoing Architect updates ARCHITECT_HANDOVER.md — at a GO
   boundary this is the full PROTOCOL rewrite; mid-sprint it is at
   least a **Section 0 SESSION BOUNDARY SNAPSHOT**: verified refs
   (local vs origin hash), journal record count + tail id, inbox/OPEN
   state, latest session log, what is booted and what is pending, and
   the exact next command the Owner would run.
3. Owner pushes, so the snapshot's "committed and pushed" claim is
   true: paste this in git bash:
   `git add -A && git commit -m "ARCH: handover snapshot for chat switch" && git push`
4. Only one Architect at a time: after the new session boots, the old
   chat is read-only history — no further rulings or writes from it.

## 3. WHAT A GOOD BOOT LOOKS LIKE (how the Owner judges the new session)
The new session must EARN trust in its first reply, not assert it.
Expect, in roughly this order:
- It verifies refs itself (local main vs origin/main; notes FETCH_HEAD
  staleness correctly rather than calling it divergence).
- It re-counts the journal and checks the hash chain with its own
  tools — not by quoting the handover's number.
- It checks inbox/OPEN, sessions/, and the worktree list before making
  ANY claim about Developer activity.
- It reports discrepancies it finds — a boot that finds a small honest
  blemish (a stale name, an owed fix) is a GOOD sign; a boot that
  finds everything perfect without evidence is the suspicious one.
- It ends with "where we stand + what happens next, in order" and
  waits for the Owner. It does NOT start writing files in its first
  turn.
If the first reply merely paraphrases the handover without independent
verification, reply: "verify per Section 5 first" — and expect it done.

## 4. WHEN to switch
- The natural point: right after a GO-SN close (handover freshly
  rewritten as part of the close — zero extra work).
- Acceptable: any quiet point between steps, with a Section 0 snapshot.
- Avoid: mid-Developer-session switches unless forced; if forced, the
  snapshot must say exactly which worktree is live and what was last
  verified.

## 5. Boot prompts for the other seats (for completeness)
- **Developer** (Claude Code): the standing one-liner —
  `Boot per CLAUDE.md, execute ARCH-<N> completely, starting with T0. Session log every session.`
- **Micro-tasks**: same shape, naming the ruling —
  `Boot per CLAUDE.md. Execute the DEVQ-<N> micro-task: <one-line scope>. Session log required.`

The test of this whole file is simple: if every chat vanished tonight,
tomorrow's project would lose nothing but conversation. The record is
the project.

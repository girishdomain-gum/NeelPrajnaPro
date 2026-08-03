# GIT_WORKFLOW.md — version control rules for NeelPrajnaPro
Authoritative for all git activity. Referenced by COMMS_PROTOCOL.md.
Repo: https://github.com/girishdomain-gum/NeelPrajnaPro (PRIVATE — never make public,
never add collaborators without the Owner's explicit say). Repo root: F:\NeelPrajnaPro
(code + docs versioned; comms\ is NOT versioned — COMMS_PROTOCOL v1.4 law: the ONE
live copy is the absolute path F:\NeelPrajnaPro\comms\, gitignored from commit
a150574).

*NeelPrajnaPro adaptation (D-5, Owner-accepted 2026-08-01; deltas in
ADOPTION_ADAPTATIONS.md): this is a pure-Python repo — no MT5 terminal, no
deploy.bat, no bridge. "Compile" = `.venv/Scripts/python.exe -m pytest tests/`
(no extra -q — incident I-02) + the firewall test. §3.6 baseline-deploys and §10
are kept verbatim from the kit but are N/A here until MT5 jobs enter this loop;
baselines here are named COMMIT IDs the Developer checks out in a read-only
worktree for comparison runs. All other rules apply verbatim, D-004 path fix
applied (the kit's /f/Fable checkpoints are /f/NeelPrajnaPro here).*

## 1. Branch model
- `main`  — owned by the ARCHITECT. Receives code ONLY via the merge ritual (§4).
            Always releasable; every state of main has passed Architect acceptance.
            F:\NeelPrajnaPro keeps main checked out PERMANENTLY (decided after the first
            accept-merge, O-014): the primary tree always shows the accepted state.
- `dev`   — owned by the DEVELOPER (Claude Code). All implementation work happens
            here, inside Claude Code's own WORKTREE (dev stays checked out there;
            this is why main-side commands can never checkout dev — by design).
            Never force-pushed, never rebased after pushing. After every accept-
            merge, the DEVELOPER syncs dev at its next session start:
            git fetch origin && git merge origin/main && git push origin dev.
- No other long-lived branches. Short experiment branches off dev are allowed
  (`dev-tryX`), must merge back to dev or be deleted within the same session.
  (Legacy branches — claude/*, maint/*, sprint/NP-S2 — are retired pointers;
  cleanup is WO-04.)

## 2. Who runs git
- DEVELOPER: runs git itself in Claude Code (commit, push, diff, log — on dev only).
- ARCHITECT: has no shell. The Architect issues exact copy-paste command blocks in
  chat; the OWNER runs them. Every Architect block states in one plain sentence what
  it does and cites the authorizing message id. The Owner never improvises git
  commands for main; if unsure, ask the Architect first.
- COMMAND-BLOCK SAFETY (binding, from incident O-005): Architect blocks use
  BASH-style paths (/f/NeelPrajnaPro — the Owner's shell is Git Bash); the first
  line is always a location checkpoint (cd + pwd with the expected output stated);
  the Owner runs blocks ONE LINE AT A TIME and STOPS on any error or unexpected
  checkpoint output.
- OWNER: also free to run read-only commands anytime (git log, git status, git diff).

## 3. Developer commit rules (dev branch)
1. Commit at the END of every working turn, and additionally BEFORE and AFTER any
   risky multi-file edit. Small, frequent, honest commits.
2. Message format:  S<nn>/WO-<xx>: <what changed> (refs D-<id>[, A-<id>])
   Examples:
     S02/WO-01: rename verifier rule R7_EB->R_EB per AM-02 (refs A-006, A-007)
     S03/WO-02: sprAdj + entry-bar effH/effL in VB_ManageBE/Trail (refs A-008, D-012)
   Comms/docs-only commits use:  comms: <summary>   or   docs: <summary>
3. Push dev after every commit:  git push origin dev
4. NEVER: touch main, force-push, rewrite pushed history, commit secrets/credentials/
   broker data, commit tester CSVs (gitignored), or bypass .gitignore with -f.
5. If a commit was wrong: fix forward with a new commit (revert if needed). History
   is never rewritten once pushed.
6. BASELINE BUILDS (AM-05 convention; NeelPrajnaPro form): every before/after
   acceptance test names its baseline as a COMMIT ID in the session's MY ACTIONS
   ("before = <hash>"). [Kit's deploy.bat leg N/A here — D-5.] A read-only
   baseline worktree remains allowed when the DEVELOPER itself needs to run
   analysis on the old code, and is removed after that WO's tests.
7. SYNC DUTY: at the start of every session that follows an accept-merge:
   `git fetch origin && git merge origin/main && git push origin dev` — expect
   fast/clean; on ANY conflict: STOP, message the Architect, touch nothing.

## 4. Merge ritual (dev -> main) — acceptance made executable
Preconditions, ALL required:
  (a) the session's WO(s) show DONE on STATE.md with TEST-RESULT message(s) on file;
  (b) for gated sessions (marked REVIEW-GATED on the board): an Architect
      REVIEW-RESULT APPROVED;
  (c) the Architect has reviewed the actual diff (see §6).
Then the Architect issues the Owner a block of this shape (never run it without the
cited message id existing):

    :: Accept S<nn> — authorized by <A-xxx APPROVED / A-xxx ratification>
    cd /f/NeelPrajnaPro && pwd
    git checkout main
    git pull origin main
    git merge --no-ff dev -m "Accept S<nn>/WO-<xx> - <A-xxx>"
    git push origin main

(That is the whole Owner block — F:\NeelPrajnaPro stays on main. The dev-side sync is the
DEVELOPER'S duty at its next session start, per §1.)

COMPLETION RULE (added after incident O-029 — the S3 merge that "landed" but had
not): the accept ritual is COMPLETE only when (d) the Owner pastes the post-merge
`git log --oneline` into the ARCHITECT'S chat and (e) the Architect confirms the
merge commit is present and updates STATE.md's Git section. Until (e), NOBODY —
including the Architect — states that a merge "landed", and the Owner does not
relay any such claim to the Developer. The Architect never pre-scripts factual
"landed" wording for the Owner; relay lines are written conditionally ("after
the Architect confirms the log, tell the Developer ...").

CHECKPOINTS ARE CLAIMS (added after incident O-044 — bridge files staged
because a checkpoint asserted "bridge/ is ignored" while the ignore rule was
still dev-only): every factual assertion inside a command block's checkpoint
("X is ignored", "you should see Y") must be verified against the CURRENT
BRANCH'S actual state before the block is issued — or written as a
conditional the Owner can check ("if you see bridge/ files staged, STOP").
Claims need evidence; the Owner executes literally.

## 5. Tags (annotated, Architect-authorized, Owner-executed)
Tags are created at milestones the board names (first candidate: adoption
completion). Command shape:
  git tag -a <name> -m "<why, refs message id>" && git push origin <name>

## 6. How the Architect reviews diffs (no shell)
Preferred: the Architect asks the DEVELOPER (who has a shell) to run
  git diff main..dev --stat        and, per file of interest,
  git diff main..dev -- <path>
and paste the output into a REVIEW-REQUEST message. Alternative: the Owner runs the
same commands and pastes to the Architect's chat. The Architect can always read the
working tree directly via the filesystem; the diff output is for change-scope
verification (nothing changed outside the session's declared files).

## 7. One-time setup (HISTORICAL — adoption completed 2026-08-01)
Repo predates adoption with full history preserved. Adoption commits: a150574
(gitignore comms/+bridge/ FIRST, O-044 law) and 170d141 (process layer retired
to docs/legacy/ as git renames). dev fast-forwarded 263cd75→170d141 = main.

## 8. Explore later, one step at a time (Owner's standing wish — do NOT self-start)
- GitHub MCP for the Architect (PR-based review).
- Simple CI gate on push (pytest + firewall) — .github/ exists; far future,
  Owner decides.

## 9. Owner quick reference (read-only — safe anytime; still one line at a time)
```
cd /f/NeelPrajnaPro && pwd          # always first — must print /f/NeelPrajnaPro
git status                          # clean tree? right branch?
git log --oneline -10               # recent history
git log --oneline main..dev         # what dev has that main doesn't (pending work)
git diff main..dev --stat           # files changed on dev vs main
git branch -a                       # all branches, local + remote
git tag -l                          # all tags
```
These change nothing and can never break the repo. If any output looks wrong or
surprising: touch nothing, paste the output to the Architect. Never run reset,
revert, merge, rebase, or any --force/--hard command without an Architect block.

## 10. Deploying code into the MT5 terminal — [N/A in NeelPrajnaPro, D-5]
Kept as kit reference for the day MT5 jobs enter this loop: deploy.bat exports
any COMMITTED ref via git archive into the terminal's MQL5\Experts slot folders;
one compile path for every build; never compile from working directories; never
edit code inside the terminal mirror. Until then, this section gates nothing
here — the "compile" path is the pytest+firewall ritual in the header note.

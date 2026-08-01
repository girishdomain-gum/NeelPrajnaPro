# ADR-006 — A narrow `git` job type for the runner

- Status: **PROPOSED** — awaiting owner ruling (§8)
- Date: 2026-07-27
- Context: the repo was put under git on 2026-07-27 and pushed to a private
  GitHub remote (`girishdomain-gum/NeelPrajna`), first commit `03f8de9`,
  tagged `v5.9.0`. Every commit currently needs the owner at a keyboard.
- Relates to: ADR-005 (operational autonomy — the routine-touch counter),
  automation v2 design v1.1 + amendment v1.2, `docs/AUTOMATION_BRIDGE.md`.
- This ADR proposes a change to the security boundary. It should be read
  slowly and it is fine to reject it.

---

## 1. The problem

Claude can read and write files on the owner's machine. Claude cannot
execute anything there. The only executing parts are the supervisor and the
runner, and the runner accepts exactly three jobs: `deploy`, `compile`,
`backtest`.

`git commit` and `git push` are commands. So under the present design, every
commit is a **routine touch** by the owner. ADR-005 §2 says a routine touch
is a platform defect, not an inconvenience to be explained. This is one.

The cost is not only the owner's time. Work that is not committed as it is
made gets committed in large lumps later, or not at all — which is how the
remote came to be 1.3 versions and two ADRs behind before anyone noticed.

## 2. The boundary being protected

The security boundary is **not** "git is dangerous". The boundary is the
**absence of an arbitrary-command job**. A job that accepts free text and
hands it to a shell would let any faulty reasoning, any malformed file, any
future prompt-injection through a document reach the whole machine.

That property must survive this ADR. A `git` job that took a command string
would destroy it, and would be worse than the problem it solves.

## 3. Proposed decision

Add a **fourth job type**, `git`, to the runner (`tools/np_agent.py`). It
accepts **no command text of any kind**. It takes one enumerated action and,
for `commit`, a message string that is used **only** as a commit message and
is never passed to a shell.

```
{"job": "git", "action": "status"}
{"job": "git", "action": "commit", "message": "<text>"}
{"job": "git", "action": "push"}
{"job": "git", "action": "tag", "name": "v5.9.1", "message": "<text>"}
```

Constraints, all enforced in the runner and all non-negotiable:

1. **Fixed argument vectors.** Each action maps to a hard-coded argument
   list. Invoked with `subprocess.run([...], shell=False)`. Never a string,
   never `shell=True`.
2. **One repository.** Working directory is hard-coded to
   `F:\NeelPrajna\repo`. Not a parameter.
3. **One remote, one branch.** `origin` and `main`, hard-coded. Not
   parameters.
4. **`commit` is always `git add -A` then `git commit`.** No pathspec
   argument, so the job cannot be aimed at a file. `.gitignore` remains the
   only filter, which keeps one rule in one place.
5. **`push` is never forced.** `--force`, `--force-with-lease`, `--delete`
   and `--mirror` do not appear anywhere in the runner source. A rejected
   push fails the job and is reported. It is never retried differently.
6. **Tag names are validated** against `^v\d+\.\d+\.\d+(-[a-z0-9.]+)?$` and
   rejected otherwise. Tags are annotated and never moved or deleted.
7. **Commit messages are length-capped and control characters stripped.**
   The message is passed as an argv element, not interpolated into a string.

## 4. What stays human, permanently

The runner must never be able to do any of these, and the runner source must
not contain the words needed to do them:

- Force push, in any form.
- Delete or move a branch or a tag.
- Rewrite history: `rebase`, `reset --hard`, `filter-branch`, `commit
  --amend`, `push --mirror`.
- Change the remote URL, add a remote, or change the branch.
- `git config` of any kind.
- Merge, or resolve a conflict.
- Anything on any repository other than `F:\NeelPrajna\repo`.

If the runner ever needs one of these, that is a new ADR, not a patch.

## 5. Credentials — the real risk

To push unattended the runner needs a credential on disk. This is the part
of the proposal that actually costs something, and it should decide the
ruling more than the mechanics in §3.

Proposed handling:

- A **fine-grained** GitHub personal access token, scoped to the single
  repository `girishdomain-gum/NeelPrajna`, with **`contents: write` only**.
  No admin, no workflow, no delete, no access to any other repository.
- Stored in `F:\NeelPrajna\lab\` — **outside the repo**, so it can never be
  committed by the `add -A` in §3.4. `lab\` is not a git working copy.
- Given an **expiry** (90 days proposed). Expiry failure is loud and
  fail-closed, which is the correct behaviour: the platform stops pushing
  and says so.
- Never logged, never echoed into a job status file, never placed in a
  manifest.

Worst case if the token leaks: an attacker can write to one private
repository that already contains the strategy. They cannot delete it (no
force, no admin), cannot reach the account, and cannot touch the trading
terminals. The blast radius is one repo's contents, and history makes any
damage reversible.

## 6. Why this does not weaken the boundary

The dangerous property of a shell job is that the **set of reachable
actions is unbounded**. Here the set is four, fixed at code-write time,
visible in the runner source, and reviewable by the owner in a diff.

Two further containments:

- Commits happen **only when a job asks**. The runner never commits on its
  own loop. A runaway loop cannot spam the history.
- Every effect is **additive and reversible**. Without force push and
  without history rewrite, the worst outcome of a faulty commit is a bad
  commit, fixed by another commit.

## 7. Alternatives considered

| Option | Why not |
|---|---|
| Owner runs git (status quo) | Works, but is a permanent routine touch. Delays commits, which is how the remote fell 1.3 versions behind. |
| Generic `shell` job with a whitelist | Whitelists grow. The first argument that needs to be dynamic breaks it. Rejected outright. |
| Local commits by runner, owner pushes | Halves the benefit, keeps the touch, and leaves the off-machine backup dependent on the owner remembering. |
| A second frozen tool beside the supervisor | Better isolation, real cost: another signed artifact to govern. Worth revisiting if §5 is judged too loose. |

## 8. Owner ruling

Not yet ruled. Recommendation is to accept **after A2 is complete**, so that
what gets committed automatically is a sealed, manifested artifact rather
than a moving target.

> Ruling:
>
> Date:

## 9. Acceptance, if accepted

- Runner minor version bump; `docs/AUTOMATION_BRIDGE.md` gains the fourth
  job type with the §3 constraints quoted verbatim.
- A test that a `git` job carrying free text in any field is **rejected**,
  not sanitised.
- A grep test over `tools/np_agent.py` asserting the §4 words are absent.
  This is a cheap, permanent guard and it should live in the repo.

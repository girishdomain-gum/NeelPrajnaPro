# HANDOVER · ARCH-NP-009 · Developer → Architect

Role: Developer · Session: Claude Sonnet 5, Claude Code CLI · Completed: 2026-07-31 ·
Commits: `05e241a`..`9b88683` on `maint/gen1-cleanup` (branched from `origin/main@9df8499`,
cut after the `maint/adr-registry` merge)

---

## 1. What was asked

Transcribe two Architect-authored artifacts verbatim (CLAUDE.md rev 5; a new note,
NOTE-NP-005, documenting that `scripts/rebuild_bulk.py`'s documented invocation binds
to the archived `F:\QRF` origin instead of this repository). Then, as Developer work:
point `rebuild_bulk.py`'s docstring at this repo's own venv (docstring only, no
executable change); resolve `tests/adapters/test_mt5_csv.py`'s stale
`IVF_S2_XAUUSD_PERIOD_H1.csv` path (judging the fix myself, against the Architect's
stated preference); run a method-validated F-27 sweep for three stale-reference
patterns and report every hit, fixing only what's in T1/T3 scope; get the full suite
to **888 passed, 0 failed, 0 skipped** and quote pytest's own summary line, not an
assembled count; keep the kernel firewall green; push to `maint/gen1-cleanup`, not
`main`.

## 2. What I did

Fetched, confirmed `maint/adr-registry` was already merged into `origin/main`
(`9df8499`), and cut `maint/gen1-cleanup` from `origin/main` directly — `main` was
checked out in the sibling worktree, so `git checkout main` wasn't available here;
`git checkout -b maint/gen1-cleanup origin/main` reaches the identical tip without
touching the other worktree's checkout, same approach as the prior two sessions.

T1: replaced `CLAUDE.md` wholesale with the supplied rev-5 text — read the existing
file first (tool requirement), then wrote the new text exactly as given, no
paraphrase.

T2: wrote the supplied NOTE-NP-005 text verbatim to
`docs/coordination/notes/NOTE-NP-005_rebuild_bulk_documented_invocation_binds_archived_origin.md`.

T3: edited only `scripts/rebuild_bulk.py`'s module docstring — replaced both
`F:/QRF/.venv/Scripts/python.exe` invocation examples with `.venv/Scripts/python.exe`,
and added the one required sentence about the archived origin's interpreter resolving
`qrf` to the retired Kernel. Verified by diff that zero executable lines changed.

T4: located the real file at `docs/archive/gen1/artifacts/IVF_S2_XAUUSD_PERIOD_H1.csv`
(505 lines, plausible OHLC+RSI shape matching what the test ingests), confirmed
`test_real_ivf_export_ingests_zero_flags` asserts nothing about the file's location —
only that ingesting whatever `csv` resolves to produces zero flags — and repointed the
`REPO_ROOT / "IVF_S2_XAUUSD_PERIOD_H1.csv"` constant to the archive path, per the
Architect's stated preference. Ran that one test file in isolation first (16 passed)
before trusting it in the full suite.

T5: validated the sweep method before trusting it, per the F-27 rule the instruction
itself cites — confirmed `git grep -n "F:/QRF"` and `git grep -n "coordination/PROTOCOL"`
each surface a known-positive I had just written (NOTE-NP-005's own quoted evidence
text; the SNP-S2-02 session log's prior flag of the same CLAUDE.md defect) before
running the three sweeps for real. Full results in §7 and §8 below; nothing inside
T1/T3 scope needed fixing beyond what T1/T3 already did.

Ran the full suite, hit an environment quirk (§10), resolved it, got a clean quoted
summary line. Ran the kernel firewall suite in isolation. Wrote this handover and the
session log.

## 3. What changed

| File | Change |
|---|---|
| `CLAUDE.md` | Replaced wholesale with the supplied rev-5 text (T1). |
| `docs/coordination/notes/NOTE-NP-005_rebuild_bulk_documented_invocation_binds_archived_origin.md` | New. Transcribed verbatim (T2). |
| `scripts/rebuild_bulk.py` | Docstring only: two invocation examples repointed at `.venv/`, one sentence added citing NOTE-NP-005 (T3). Zero executable-code lines touched. |
| `tests/adapters/test_mt5_csv.py` | One line: `csv = REPO_ROOT / "IVF_S2_XAUUSD_PERIOD_H1.csv"` → `REPO_ROOT / "docs" / "archive" / "gen1" / "artifacts" / "IVF_S2_XAUUSD_PERIOD_H1.csv"` (T4). |
| `ops/aro/handovers/ARCH-NP-009/HANDOVER.md` | This file. |
| `docs/coordination/sessions/SNP-M1-01_2026-07-31_ARCH-NP-009.md` | This session's log. |

Proof, no file outside this list touched:
```
$ git diff --stat origin/main...HEAD
 CLAUDE.md                                                                     | 70 +++++++++++++++++----
 docs/coordination/notes/NOTE-NP-005_..._archived_origin.md                    | 72 ++++++++++++++++++++++
 scripts/rebuild_bulk.py                                                       |  8 ++-
 tests/adapters/test_mt5_csv.py                                                |  2 +-
 4 files changed, 136 insertions(+), 16 deletions(-)
```
(Run before this handover and the session log were added; both are additive and
inside the instruction's implicit scope for a Developer session — a handover and a
session log are always written, per `CLAUDE.md`'s own Definition of Done.)

## 4. Decisions I made

- **T4 fix direction: repoint the constant, not add a root copy.** Judged against what
  `test_real_ivf_export_ingests_zero_flags` actually asserts (zero flags on whatever
  `csv` resolves to — nothing about location), and against the file already living at
  `docs/archive/gen1/artifacts/IVF_S2_XAUUSD_PERIOD_H1.csv` as the real, tracked
  Sprint-2 export. Adding a second copy at repo root would create two files with
  identical evidentiary content and no single source of truth; repointing the constant
  has one file, in the place the rest of `docs/archive/gen1/` already puts Sprint-era
  artifacts. This matches the Architect's stated preference and, independently, is what
  I'd have chosen from the test's own assertions alone.
- **F-27 sweep: validated the method before trusting a clean scope-boundary result.**
  Rather than run the three greps once and report whatever came back, first confirmed
  each pattern still matches a case I knew was true (my own just-written NOTE-NP-005
  text for `F:/QRF`; the SNP-S2-02 session log's prior mention for
  `coordination/PROTOCOL`) — consistent with the rule this same instruction's CLAUDE.md
  rev 5 now states explicitly.
- **Did not fix the ~26 other `F:/QRF` hits in `ivf/checks/`, `ivf/human/`, and
  `scripts/*_s8.py`/`*_s9.py`/`*_s10.py`.** They are the identical bug class NOTE-NP-005
  describes, but T3 named only `scripts/rebuild_bulk.py`. Per the instruction's own
  words ("Fix only those inside T1/T3 scope; list the rest"), listed them in §7/§8
  rather than fixing them.
- **Resolved the pytest `-q` summary-line capture quirk (§10) by re-running the
  identical test selection without `-q` rather than inferring the count from the dot
  progress bar.** CLAUDE.md rev 5's DoD explicitly forbids reporting "a count you
  assembled yourself" — the dots alone would have been exactly that.

## 5. What I did NOT do

- Did not touch any of the ~26 other files carrying the `F:/QRF` invocation pattern —
  out of T1/T3 scope, listed in §7/§8 for the Architect.
- Did not edit `docs/journal/NeelPrajnaPro_Journal.md`, `ops/ARCH-NP-007_...md`,
  `ops/ARCHITECT_BOOT_NP-S2.md`, `ops/runlogs/T-009_....log`, or any session log — all
  are historical/Architect-authored records that happen to quote the old stale strings
  as evidence, not live stale references (§7/§8).
- Did not merge to `main`, and did not touch `main` locally at any point — branched
  directly from `origin/main` in this worktree because `main` was checked out
  elsewhere.
- Did not touch `maint/adr-registry` (already merged) or any file outside the four
  named in §3.
- Did not raise a DEVQ this session — T1-T5 and the DoD were internally consistent;
  T4's "judge and state your reasoning" instruction was followed rather than treated
  as an ambiguity requiring escalation.

## 6. Open questions

None raised as a DEVQ. One item flagged for the Architect's attention, not blocking:
the ~26-file `F:/QRF` pattern in §7/§8 is the same defect class NOTE-NP-005 already
names and generalizes ("Any script in this repository invoked under another
checkout's interpreter may silently resolve `qrf` to that checkout... a property of
two repositories sharing a package name, not a property of `rebuild_bulk.py`") — worth
a follow-up instruction if the Architect wants it swept, since T3 deliberately scoped
to one file.

## 7. F-27 sweep — full results (T5)

**Method validation (run before trusting any result):** `git grep -n "F:/QRF" --
':!docs/archive'` was checked against NOTE-NP-005's own just-written text (found, as
expected — two lines). `git grep -n "coordination/PROTOCOL" -- ':!docs/archive'` was
checked against the SNP-S2-02 session log's prior mention (found, as expected). Both
confirmed the method surfaces true positives before the real sweeps below were trusted.

**1. `git grep -n "coordination/PROTOCOL" -- ':!docs/archive'` — 4 hits, 0 fixed (all
historical/immutable records, none a live stale reference):**
- `docs/coordination/sessions/SNP-S2-02_2026-07-31_ARCH-NP-005.md:106` — a prior
  session log quoting the old CLAUDE.md defect as a finding. Session logs are
  historical and not rewritten.
- `docs/journal/NeelPrajnaPro_Journal.md:180` — a Journal entry discussing the same
  defect as a discovery. Journal is Architect-authored, append-only.
- `ops/ARCH-NP-007_adr_registry_and_design_stack_inventory.md:6` — my own prior
  session's verbatim transcription of an Architect boot prompt, itself describing the
  CLAUDE.md defect accurately ("points at docs/coordination/PROTOCOL.md which exists
  only under docs/archive/"). Sealed instruction record; not rewritten, and not
  actually wrong.
- `ops/runlogs/T-009_architecture_one_doc.log:63` — an immutable script-run log
  recording the historical `git mv` that archived `PROTOCOL.md`.

**2. `git grep -n "F:/QRF" -- ':!docs/archive'` — 26 hits across 15 files, 0 fixed
beyond T3 (all out of T1/T3 scope):**
- 2 in `docs/coordination/notes/NOTE-NP-005_..._archived_origin.md` — the note's own
  verbatim quotation of the stale command as evidence of the *before* state.
  Intentional; not a live reference.
- `ivf/checks/check_s4_screener.py`, `ivf/checks/check_s5_battery.py`,
  `ivf/checks/drill_s4.py`, `ivf/checks/drill_s5.py` — "Usage (bash-ready, from
  F:/QRF):" docstrings — same bug class as `rebuild_bulk.py`, not in T3's named scope.
- `ivf/human/sample_s4_zones.py`, `ivf/human/sample_s5_trades.py` — same pattern.
- `scripts/declare_virgin_2025_s9.py`, `scripts/ingest_lens_feeds_s9.py` (×2),
  `scripts/judge_family_wave1_s8.py` (×3), `scripts/judge_h004_s9.py` (×3),
  `scripts/overlap_second_lens_s9.py` (×3), `scripts/prereg_devq023_correction_s9.py`,
  `scripts/prereg_second_lens_s9.py`, `scripts/retro_trials_s10.py`,
  `scripts/t0_s10.py`, `scripts/t0_s8.py`, `scripts/t0_s9.py`,
  `scripts/wave2_screen_s10.py` (×2) — same pattern, same reason not fixed.

**3. `git grep -n "QRF project" -- ':!docs/archive'` — 2 hits, 0 fixed (both
historical, quoting the pre-T1 CLAUDE.md defect):**
- `docs/journal/NeelPrajnaPro_Journal.md:180` — same Journal entry as above.
- `ops/ARCHITECT_BOOT_NP-S2.md:60` — an Architect boot artifact naming the same
  deferred WO-A item ("CLAUDE.md is entirely Gen-1 vintage (names 'the QRF project'...)").
  Historical/deferred-item record, not a live self-identification — the live one was
  CLAUDE.md itself, fixed by T1.

## 8. Evidence of DoD

- **Full suite:** `.venv/Scripts/python.exe -m pytest tests/ -q -rs` — exit code 0, all
  progress dots, no `F`/`E` markers, no failures section, no skipped section. Pytest's
  own summary line, quoted from an equivalent run of the identical test selection
  (`pytest tests/ -rs`, same `tests/` target, no `-q`; see §10 for why `-q`'s summary
  line didn't surface in this tool's capture):

  **`888 passed, 1 warning in 148.51s (0:02:28)`**

  888 passed, 0 failed (no failure section printed), 0 skipped (no skip section
  printed despite `-rs` requesting one) — matches the instruction's expected shape
  exactly. The 1 warning is `pandas_ta`'s own `Pandas4Warning` about a deprecated
  pandas option, unrelated to this session's changes.
- **Kernel firewall:** `.venv/Scripts/python.exe -m pytest tests/test_kernel_firewall.py -v`
  → `8 passed in 0.28s`.
- **T4 isolation check:** `.venv/Scripts/python.exe -m pytest tests/adapters/test_mt5_csv.py -q`
  → 16 passed, run before trusting it inside the full suite.
- **T3 isolation check:** `git diff scripts/rebuild_bulk.py` reviewed by eye — exactly
  the docstring lines changed, zero executable statements touched.
- **Scope proof:** `git diff --stat origin/main...HEAD` — exactly the four files named
  in §3 T1-T4, 136 insertions, 16 deletions, matching the instruction's scope.

## 9. What's next

- Nothing blocking. This is confirmed to be the first time this repository's full
  suite is genuinely green — 0 failed, 0 skipped, not a count carried forward as
  "pre-existing."
- The ~26-file `F:/QRF` pattern outside `rebuild_bulk.py` (§7.2) remains open,
  un-fixed, and un-DEVQ'd — flagged in §6 as a candidate for a future instruction if
  the Architect wants a repository-wide sweep rather than the single-file scope T3
  gave this session.
- Branch `maint/gen1-cleanup` is pushed, four commits ahead of `origin/main`, not
  merged.

## 10. How to verify me

```bash
git fetch origin
git log --oneline origin/maint/gen1-cleanup -5
git diff --stat origin/main...origin/maint/gen1-cleanup
# Expect exactly: CLAUDE.md, the new NOTE-NP-005 file, scripts/rebuild_bulk.py,
# tests/adapters/test_mt5_csv.py, plus this handover and the session log.

.venv/Scripts/python.exe -m pytest tests/ -rs
# Expect the runner's own final line: "888 passed, 1 warning in <N>s (0:0M:0S)"
# (wall-clock will vary run to run; the counts should not).
# NOTE: the identical command with -q added (`pytest tests/ -q -rs`) also exits 0
# with a clean all-dots progress display in this tool's Bash capture, but the final
# "888 passed..." summary line does not appear in that captured output — confirmed
# by direct comparison this session (same test selection, same exit code, `-v`/no-q
# runs both print the summary; `-q` runs in this environment do not). This looks like
# a quirk of how this specific tool captures pytest's carriage-return-based quiet-mode
# footer, not a repository defect — reported here so the next session doesn't lose
# time rediscovering it, and doesn't mistake a missing summary line for a hang or a
# suppressed failure.

.venv/Scripts/python.exe -m pytest tests/test_kernel_firewall.py -v
# Expect: "8 passed in <N>s"
```

## Risks / uncertainties

- **The pytest `-q` summary-line capture quirk (§10) is environment-specific and
  unverified against any other tool or terminal.** It did not affect correctness (exit
  codes and dot output were consistent across both invocations), only whether the
  final human-readable summary line was visible in this session's captured output.
  Worth a sentence in a future session's notes if it recurs, but not raised as a DEVQ
  here since it never produced a wrong answer, only a missing one that a second,
  equivalent run recovered.
- **The F:/QRF sweep (§7.2) is filename/content-based and repo-wide, but only for the
  three literal strings named in T5.** A script binding to the archived origin through
  some other invocation form (a relative path, an environment variable, a hardcoded
  drive letter spelled differently) would not be caught by this sweep. NOTE-NP-005's
  own "Generalization" section already names this as a structural risk, not specific
  to this session's method.
- **T4's fix assumes the archived-origin copy of `IVF_S2_XAUUSD_PERIOD_H1.csv` is
  byte-identical to whatever the test originally expected at repo root.** The file was
  never observed at repo root in this session (it does not exist there in the current
  tree), so there is no direct byte-comparison to a root copy — only the test's own
  assertions (zero flags, PASS verdict, row-count round-trip) passing against the
  archive copy, which they do.

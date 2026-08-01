"""WO-06 (S2, refs A-006) — drill law for tools/accept.sh: each refusal path
must be shown able to go RED before the guard is trusted (this repo's own
F-27 rule), and the happy path must be shown able to go GREEN without ever
touching the real NeelPrajnaPro repo. Every test builds its own disposable
scratch git repo (a work tree + a bare "origin") and points the script at it
via ACCEPT_REPO_ROOT — the script's own wrong-cwd guard means the Owner's
real invocations (no override set) still enforce the real F:\\NeelPrajnaPro
path; this env var exists only so it can be drilled here.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ACCEPT_SH = REPO_ROOT / "tools" / "accept.sh"

APPROVED_BLOCK = """id: D-100
from: ARCHITECT
to: DEVELOPER
type: REVIEW-RESULT
reply_to: D-099
requires_reply: NO
priority: NORMAL
subject: Stest APPROVED

Diff reviewed, scope exact. APPROVED.
"""

REJECTED_BLOCK = """id: D-101
from: ARCHITECT
to: DEVELOPER
type: REVIEW-RESULT
reply_to: D-098
requires_reply: NO
priority: NORMAL
subject: Stest REJECTED

Scope creep outside the write set. REJECTED, fix and resubmit.
"""


def _git(args, cwd):
    out = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True
    )
    return out.stdout


def _bash_pwd(cwd):
    """The exact string bash's own `pwd` produces for `cwd` (avoids hand
    translating a Windows path to Git-Bash POSIX form — asks bash itself)."""
    out = subprocess.run(
        ["bash", "-c", "pwd"], cwd=str(cwd), capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _build_scratch_repo(tmp_path: Path) -> Path:
    """A disposable repo: bare 'origin' + a work tree with main + dev pushed,
    main checked out (mirrors the real repo's permanent-main convention),
    plus comms\\developer.md carrying one APPROVED and one REJECTED
    REVIEW-RESULT."""
    origin = tmp_path / "origin.git"
    work = tmp_path / "work"
    _git(["init", "--bare", "-b", "main", str(origin)], tmp_path)
    _git(["init", "-b", "main", str(work)], tmp_path)
    _git(["config", "user.email", "test@example.com"], work)
    _git(["config", "user.name", "Test"], work)
    (work / "README.md").write_text("initial\n", encoding="utf-8")
    (work / ".gitignore").write_text("comms/\n", encoding="utf-8")  # mirrors the real repo
    _git(["add", "README.md", ".gitignore"], work)
    _git(["commit", "-m", "initial"], work)
    _git(["remote", "add", "origin", str(origin)], work)
    _git(["push", "origin", "main"], work)

    _git(["checkout", "-b", "dev"], work)
    (work / "feature.txt").write_text("dev work\n", encoding="utf-8")
    _git(["add", "feature.txt"], work)
    _git(["commit", "-m", "dev commit"], work)
    _git(["push", "origin", "dev"], work)
    _git(["checkout", "main"], work)

    comms = work / "comms"
    comms.mkdir()
    (comms / "developer.md").write_text(
        "# developer.md — DEVELOPER'S INBOX\n\n---\n"
        + APPROVED_BLOCK
        + "\n---\n"
        + REJECTED_BLOCK,
        encoding="utf-8",
    )
    return work


def _run(work: Path, args, cwd=None):
    root = _bash_pwd(work)
    env = {**os.environ, "ACCEPT_REPO_ROOT": root}
    return subprocess.run(
        ["bash", str(ACCEPT_SH), *args],
        cwd=str(cwd if cwd is not None else work),
        capture_output=True,
        text=True,
        env=env,
    )


# --- refusal paths (drilled: each must go RED) --------------------------------
def test_refuses_missing_id(tmp_path):
    work = _build_scratch_repo(tmp_path)
    before = _git(["rev-parse", "main"], work)
    result = _run(work, ["Stest", "D-999", "--dry-run"])
    assert result.returncode != 0
    assert "REFUSED" in result.stderr
    assert "D-999" in result.stderr
    assert _git(["rev-parse", "main"], work) == before  # untouched


def test_refuses_non_approved_id(tmp_path):
    work = _build_scratch_repo(tmp_path)
    result = _run(work, ["Stest", "D-101", "--dry-run"])
    assert result.returncode != 0
    assert "REFUSED" in result.stderr
    assert "APPROVED" in result.stderr


def test_refuses_dirty_tree(tmp_path):
    work = _build_scratch_repo(tmp_path)
    (work / "uncommitted.txt").write_text("oops\n", encoding="utf-8")
    result = _run(work, ["Stest", "D-100", "--dry-run"])
    assert result.returncode != 0
    assert "REFUSED" in result.stderr
    assert "dirty" in result.stderr


def test_refuses_wrong_cwd(tmp_path):
    work = _build_scratch_repo(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    result = _run(work, ["Stest", "D-100", "--dry-run"], cwd=elsewhere)
    assert result.returncode != 0
    assert "REFUSED" in result.stderr
    assert "must run from" in result.stderr


# --- happy path: dry-run authorizes but never touches git state ---------------
def test_dry_run_happy_path_authorizes_without_touching_git(tmp_path):
    work = _build_scratch_repo(tmp_path)
    main_before = _git(["rev-parse", "main"], work)
    dev_before = _git(["rev-parse", "dev"], work)
    result = _run(work, ["Stest", "D-100", "--dry-run"])
    assert result.returncode == 0
    assert "AUTHORIZED" in result.stdout
    assert "DRY RUN" in result.stdout
    assert _git(["rev-parse", "main"], work) == main_before
    assert _git(["rev-parse", "dev"], work) == dev_before
    assert not (work / "comms" / "accept_Stest.log").exists()


# --- the real ritual: executes, logs completely, prints the COMPLETION line --
def test_real_run_merges_and_logs_completely(tmp_path):
    work = _build_scratch_repo(tmp_path)
    dev_sha = _git(["rev-parse", "dev"], work).strip()

    result = _run(work, ["Stest", "D-100"])
    assert result.returncode == 0, result.stderr

    log_lines = _git(["log", "--oneline", "-5"], work)
    assert "Accept Stest - D-100 APPROVED" in log_lines
    ancestors = _git(["log", "--format=%H"], work)
    assert dev_sha in ancestors  # dev's commit really landed on main

    log_file = work / "comms" / "accept_Stest.log"
    assert log_file.exists()
    log_text = log_file.read_text(encoding="utf-8")
    assert "git checkout main" in log_text
    assert "git merge --no-ff origin/dev" in log_text

    assert "post-merge git log" in result.stdout


def test_refuses_when_authorizing_id_is_not_a_review_result(tmp_path):
    work = _build_scratch_repo(tmp_path)
    (work / "comms" / "developer.md").write_text(
        "# developer.md\n\n---\nid: D-100\n"
        "from: ARCHITECT\nto: DEVELOPER\ntype: STATUS\n"
        "requires_reply: NO\npriority: NORMAL\nsubject: not a review result\n\n"
        "Contains the word APPROVED but is not a REVIEW-RESULT.\n",
        encoding="utf-8",
    )
    result = _run(work, ["Stest", "D-100", "--dry-run"])
    assert result.returncode != 0
    assert "REFUSED" in result.stderr
    assert "not a REVIEW-RESULT" in result.stderr


def test_usage_with_too_few_args():
    result = subprocess.run(
        ["bash", str(ACCEPT_SH), "Stest"], capture_output=True, text=True
    )
    assert result.returncode == 2
    assert "Usage" in result.stderr

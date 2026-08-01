"""WO-09 (S3, refs A-009) — drill law for tools/run_job.sh: each refusal path
must be shown able to go RED before the guard is trusted, and the happy path
(including a real command failure mid-job) must be shown able to go GREEN,
end to end, against a disposable scratch repo — never the real NeelPrajnaPro
repo. RUN_JOB_REPO_ROOT points the script at the scratch repo the same way
ACCEPT_REPO_ROOT does for tools/accept.sh.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_JOB_SH = REPO_ROOT / "tools" / "run_job.sh"


def _git(args, cwd):
    out = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True
    )
    return out.stdout


def _bash_pwd(cwd):
    """The exact string bash's own `pwd` produces for `cwd` (avoids hand
    translating a Windows path to Git-Bash POSIX form)."""
    out = subprocess.run(
        ["bash", "-c", "pwd"], cwd=str(cwd), capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _build_scratch_repo(tmp_path: Path) -> Path:
    """A disposable repo: a work tree with an initial commit, comms\\developer.md
    carrying one message (A-100) that job files may cite via refs:, and empty
    comms\\jobs\\pending / done directories."""
    work = tmp_path / "work"
    _git(["init", "-b", "main", str(work)], tmp_path)
    _git(["config", "user.email", "test@example.com"], work)
    _git(["config", "user.name", "Test"], work)
    (work / "README.md").write_text("initial\n", encoding="utf-8")
    _git(["add", "README.md"], work)
    _git(["commit", "-m", "initial"], work)

    comms = work / "comms"
    comms.mkdir()
    (comms / "developer.md").write_text(
        "# developer.md — DEVELOPER'S INBOX\n\n---\n"
        "id: A-100\n"
        "from: ARCHITECT\n"
        "to: DEVELOPER\n"
        "type: DIRECTIVE\n"
        "requires_reply: NO\n"
        "priority: NORMAL\n"
        "subject: test job authorization\n\n"
        "Authorizes test jobs.\n",
        encoding="utf-8",
    )
    (comms / "jobs" / "pending").mkdir(parents=True)
    (comms / "jobs" / "done").mkdir(parents=True)
    return work


def _write_job(work: Path, job_id: str, refs: str, job_type: str, commands, mtime=None):
    path = work / "comms" / "jobs" / "pending" / f"{job_id}.job"
    body = f"id: {job_id}\nrefs: {refs}\ntype: {job_type}\n\n" + "\n".join(commands) + "\n"
    path.write_text(body, encoding="utf-8")
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


def _run(work: Path, cwd=None):
    root = _bash_pwd(work)
    env = {**os.environ, "RUN_JOB_REPO_ROOT": root}
    return subprocess.run(
        ["bash", str(RUN_JOB_SH)],
        cwd=str(cwd if cwd is not None else work),
        capture_output=True,
        text=True,
        env=env,
    )


# --- refusal paths (drilled: each must go RED) --------------------------------
def test_refuses_wrong_cwd(tmp_path):
    work = _build_scratch_repo(tmp_path)
    _write_job(work, "JOB-001", "A-100", "git_block", ["git status"])
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    result = _run(work, cwd=elsewhere)
    assert result.returncode != 0
    assert "REFUSED" in result.stderr
    assert "must run from" in result.stderr
    assert (work / "comms" / "jobs" / "pending" / "JOB-001.job").exists()


def test_refuses_empty_pending(tmp_path):
    work = _build_scratch_repo(tmp_path)
    result = _run(work)
    assert result.returncode != 0
    assert "REFUSED" in result.stderr
    assert "no pending jobs" in result.stderr


def test_refuses_unknown_refs_id(tmp_path):
    work = _build_scratch_repo(tmp_path)
    job = _write_job(work, "JOB-001", "A-999", "git_block", ["git status"])
    result = _run(work)
    assert result.returncode != 0
    assert "REFUSED" in result.stderr
    assert "A-999" in result.stderr
    assert job.exists()  # untouched — no log, no move
    assert not (work / "comms" / "jobs" / "done" / "JOB-001.log").exists()


def test_refuses_non_whitelisted_line(tmp_path):
    work = _build_scratch_repo(tmp_path)
    job = _write_job(
        work, "JOB-001", "A-100", "git_block", ["git status", "rm -rf /"]
    )
    result = _run(work)
    assert result.returncode != 0
    assert "REFUSED" in result.stderr
    assert "non-whitelisted" in result.stderr
    assert "rm -rf /" in result.stderr
    # refused BEFORE executing anything: job untouched, nothing moved/logged
    assert job.exists()
    assert not (work / "comms" / "jobs" / "done" / "JOB-001.log").exists()
    assert not (work / "comms" / "jobs" / "done" / "JOB-001.job").exists()


def test_refuses_line_with_shell_metacharacters(tmp_path):
    """A-011 required sharpening: the whitelist only checks prefixes, so
    chaining a second command after a whitelisted prefix must be refused
    separately (`bash -c` would otherwise happily run both)."""
    work = _build_scratch_repo(tmp_path)
    job = _write_job(
        work, "JOB-001", "A-100", "git_block", ["git status && rm -rf /"]
    )
    result = _run(work)
    assert result.returncode != 0
    assert "REFUSED" in result.stderr
    assert "metacharacters" in result.stderr
    # refused BEFORE executing anything: job untouched, nothing moved/logged
    assert job.exists()
    assert not (work / "comms" / "jobs" / "done" / "JOB-001.log").exists()
    assert not (work / "comms" / "jobs" / "done" / "JOB-001.job").exists()


# --- oldest-first selection ----------------------------------------------------
def test_picks_oldest_pending_job_by_mtime(tmp_path):
    work = _build_scratch_repo(tmp_path)
    _write_job(work, "JOB-002", "A-100", "git_block", ["git status"], mtime=2000)
    _write_job(work, "JOB-001", "A-100", "git_block", ["git status"], mtime=1000)
    result = _run(work)
    assert result.returncode == 0, result.stderr
    assert (work / "comms" / "jobs" / "done" / "JOB-001.job").exists()
    assert (work / "comms" / "jobs" / "done" / "JOB-001.log").exists()
    # the newer one is untouched
    assert (work / "comms" / "jobs" / "pending" / "JOB-002.job").exists()


# --- happy path: full success, log content proven -----------------------------
def test_happy_path_logs_completely_and_moves_job(tmp_path):
    work = _build_scratch_repo(tmp_path)
    _write_job(
        work,
        "JOB-001",
        "A-100",
        "git_block",
        ["git status", "git log --oneline -1"],
    )
    result = _run(work)
    assert result.returncode == 0, result.stderr
    assert "PROCESSING: JOB-001" in result.stdout

    log_file = work / "comms" / "jobs" / "done" / "JOB-001.log"
    assert log_file.exists()
    log_text = log_file.read_text(encoding="utf-8")
    assert "+ git status" in log_text
    assert "+ git log --oneline -1" in log_text
    assert "RESULT: OK" in log_text

    assert (work / "comms" / "jobs" / "done" / "JOB-001.job").exists()
    assert not (work / "comms" / "jobs" / "pending" / "JOB-001.job").exists()


# --- failing command mid-job: still logs completely, still moves, exit != 0 ---
def test_failing_command_logs_failure_and_still_moves_job(tmp_path):
    work = _build_scratch_repo(tmp_path)
    _write_job(
        work,
        "JOB-001",
        "A-100",
        "git_block",
        ["git status", "git this-is-not-a-real-git-subcommand", "git log --oneline -1"],
    )
    result = _run(work)
    assert result.returncode != 0

    log_file = work / "comms" / "jobs" / "done" / "JOB-001.log"
    assert log_file.exists()
    log_text = log_file.read_text(encoding="utf-8")
    assert "+ git status" in log_text
    assert "+ git this-is-not-a-real-git-subcommand" in log_text
    assert "RESULT: FAILED at line 6" in log_text
    # the third command (line 7) never ran — the job stopped at the failure
    assert "git log --oneline -1" not in log_text.split("RESULT: FAILED")[0].split(
        "git this-is-not-a-real-git-subcommand"
    )[1]

    assert (work / "comms" / "jobs" / "done" / "JOB-001.job").exists()
    assert not (work / "comms" / "jobs" / "pending" / "JOB-001.job").exists()

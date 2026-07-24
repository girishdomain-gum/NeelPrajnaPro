#!/usr/bin/env python3
"""gen_state.py — regenerate docs/handover/AI_PROJECT_STATE.md (ADR-007, v1).

ADR-007: the handover/status file is *generated*, not hand-written, so a second
source of truth cannot silently diverge from the ledger.

**Status-table row model (DEVQ-004 decision).** The Status table has two row
classes:

* **DERIVED** rows the generator recomputes from evidence every run:
  - ``Test suite``  — from a pytest run,
  - ``ADR register`` — from the ADR file list,
  - ``Journal``     — record count = non-empty lines in journal.jsonl,
  - ``Git branch``  — current branch + short commit, from git.
* **HAND** rows — sprint statuses and the like — preserved **verbatim**, exactly
  like the two hand-maintained prose sections. The generator never edits them;
  the Architect owns them.

DERIVED rows found in the existing table are updated in place (keeping their
position and Area label); any missing DERIVED row is appended after the last
table row. Everything else — every HAND row, both hand-maintained sections, and
all prose — survives byte-for-byte. The full ledger-derived version (deriving
sprint/verification status from records) waits for its ADR-007 trigger.

Usage:
    python scripts/gen_state.py                 # regenerate the real file
    python scripts/gen_state.py --out PATH       # write elsewhere (dry review)
    python scripts/gen_state.py --check          # print, do not write
    python scripts/gen_state.py --no-tests       # skip running the test suite
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = REPO_ROOT / "docs" / "handover" / "AI_PROJECT_STATE.md"
ADR_DIR = REPO_ROOT / "docs" / "adr"
JOURNAL_FILE = REPO_ROOT / "datastore" / "journal" / "journal.jsonl"

HAND_MAINTAINED_HEADINGS = (
    "## Next immediate task (hand-maintained)",
    "## Don't change without discussion (hand-maintained)",
)


def _git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return ""


def git_branch() -> str:
    return _git("rev-parse", "--abbrev-ref", "HEAD") or "unknown"


def git_commit_short() -> str:
    return _git("rev-parse", "--short", "HEAD") or "unknown"


def adr_range() -> tuple[str, int]:
    nums = sorted(
        int(m.group(1))
        for p in ADR_DIR.glob("ADR-*.md")
        if (m := re.match(r"ADR-(\d+)", p.name))
    )
    if not nums:
        return "none", 0
    return f"ADR-{nums[0]:03d}..{nums[-1]:03d}", len(nums)


def journal_record_count() -> int:
    """Records = non-empty lines in journal.jsonl (one record per line)."""
    if not JOURNAL_FILE.exists():
        return 0
    return sum(1 for ln in JOURNAL_FILE.read_text(encoding="utf-8").splitlines() if ln.strip())


def test_summary(run: bool) -> tuple[str, str]:
    """Return (summary_line, status) where status is 'green' | 'RED' | 'not run'."""
    if not run:
        return "not run (--no-tests)", "not run"
    try:
        proc = subprocess.run(
            # -o addopts= neutralizes the project's ini addopts ("-q"); otherwise
            # our own -q would stack to -qq and pytest suppresses the summary line.
            [
                sys.executable, "-m", "pytest",
                "-o", "addopts=", "-q", "--no-header", "-p", "no:cacheprovider",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
    except (subprocess.SubprocessError, OSError) as e:
        return f"could not run pytest ({e})", "unknown"
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    # Pick pytest's result line (e.g. "83 passed in 8.0s"), not the progress dots.
    summary = "no output"
    for ln in reversed(lines):
        low = ln.lower()
        if any(k in low for k in ("passed", "failed", "error", "no tests ran")):
            summary = ln.lstrip(". ")
            break
    else:
        if lines:
            summary = lines[-1]
    return summary, "green" if proc.returncode == 0 else "RED"


# --- Status table: DERIVED vs HAND rows (DEVQ-004) ---------------------------
def _derived_values(run_tests: bool) -> dict[str, str]:
    rng, _count = adr_range()
    summary, status = test_summary(run_tests)
    return {
        "adr": rng,
        "test": f"{summary} ({status})",
        "journal": f"{journal_record_count()} records",
        "branch": f"{git_branch()} ({git_commit_short()})",
    }


# Canonical Area label for a DERIVED row that must be appended when absent.
_DERIVED_LABELS = {"adr": "ADR register", "test": "Test suite",
                   "journal": "Journal", "branch": "Git branch"}
# Order in which missing DERIVED rows are appended.
_DERIVED_ORDER = ("adr", "test", "journal", "branch")


def _classify_area(area: str) -> str | None:
    """Map a Status-row Area cell to a DERIVED key, or None for a HAND row."""
    a = area.strip().lower()
    if "adr register" in a:
        return "adr"
    if a == "journal":
        return "journal"
    if "test suite" in a:
        return "test"
    if "git branch" in a:
        return "branch"
    return None


def _is_table_row(line: str) -> bool:
    return line.lstrip().startswith("|")


def _is_header_or_separator(cells: list[str]) -> bool:
    if not cells:
        return True
    first = cells[0].strip()
    # Header row ("Area") or separator ("---", ":--:", etc.).
    return first == "Area" or (bool(first) and set(first) <= set("-: "))


def rebuild_status(status_section: str, run_tests: bool) -> str:
    """Rebuild the Status section: recompute DERIVED rows, preserve HAND rows."""
    derived = _derived_values(run_tests)
    lines = status_section.splitlines()
    out: list[str] = []
    seen: set[str] = set()
    last_table_idx = -1  # index in `out` of the final table row

    for line in lines:
        if not _is_table_row(line):
            out.append(line)
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if _is_header_or_separator(cells):
            out.append(line)
            last_table_idx = len(out) - 1
            continue
        area = cells[0]
        key = _classify_area(area)
        if key is not None:
            out.append(f"| {area} | {derived[key]} |")  # DERIVED: recompute value
            seen.add(key)
        else:
            out.append(line)  # HAND: verbatim
        last_table_idx = len(out) - 1

    # Append any DERIVED rows that were not already present, after the last row.
    missing = [f"| {_DERIVED_LABELS[k]} | {derived[k]} |"
               for k in _DERIVED_ORDER if k not in seen]
    if missing:
        insert_at = last_table_idx + 1
        out[insert_at:insert_at] = missing

    # Normalize the trailing separator to exactly one blank line before the next
    # heading (splitlines()/join would otherwise collapse the trailing blank).
    return "\n".join(out).rstrip("\n") + "\n\n"


def regenerate(text: str, run_tests: bool) -> str:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    comment = (
        f"<!-- GENERATED by scripts/gen_state.py (ADR-007). The Status table's\n"
        f"     DERIVED rows (test suite, ADR range, journal count, git branch) are\n"
        f"     recomputed; its HAND rows and the two hand-maintained sections are\n"
        f"     preserved verbatim. Generated-at: {now}. Branch: {git_branch()}. -->"
    )
    # Replace the first HTML comment (the generated-at header).
    text = re.sub(r"(?s)<!--.*?-->", lambda _: comment, text, count=1)

    # Rebuild the Status section (up to the next '## ' heading or EOF) in place.
    m = re.search(r"(?ms)^## Status\b.*?(?=^## |\Z)", text)
    if m is None:
        raise SystemExit("error: could not locate a '## Status' section to regenerate")
    new_status = rebuild_status(m.group(0), run_tests)
    text = text[: m.start()] + new_status + text[m.end():]

    # Safety: the two hand-maintained sections must survive unchanged.
    for heading in HAND_MAINTAINED_HEADINGS:
        if heading not in text:
            raise SystemExit(f"error: hand-maintained section vanished: {heading!r}")
    return text


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=None, help="write to this path instead")
    ap.add_argument("--check", action="store_true", help="print to stdout, do not write")
    ap.add_argument("--no-tests", action="store_true", help="skip running the test suite")
    args = ap.parse_args(argv)

    if not STATE_FILE.exists():
        raise SystemExit(f"error: {STATE_FILE} not found")
    original = STATE_FILE.read_text(encoding="utf-8")
    regenerated = regenerate(original, run_tests=not args.no_tests)

    if args.check:
        sys.stdout.write(regenerated)
        return 0
    dest = args.out or STATE_FILE
    dest.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n": keep LF endings (.gitattributes enforces eol=lf); the default
    # would emit CRLF on Windows and churn the file on every run.
    dest.write_text(regenerated, encoding="utf-8", newline="\n")
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

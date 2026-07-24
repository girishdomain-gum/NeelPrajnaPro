#!/usr/bin/env python3
"""IVF Sprint-1 verifier: independent journal integrity check.

INDEPENDENCE (IVF v1.0 rules IND-1..IND-4):
  * This file imports NOTHING from qrf.* — stdlib only.
  * Canonical serialization below is re-implemented from the SPEC TEXT of
    Implementation Blueprint v1.0 §1.3 / §1.1, deliberately not from
    qrf/kernel/records/record.py. If the two implementations disagree, that
    disagreement is precisely the finding this tool exists to produce.

Checks (Verification Framework §7, Sprint 1):
  C1 every line parses as JSON with exactly the 11 wire fields
  C2 content_hash == sha256(canonical({record_type, schema_version, producer,
       event_ts, parents, payload}))            [EXACT]
  C3 prev_hash chain: genesis "0"*64, then each == previous content_hash [EXACT]
  C4 record_ids are 26-char ULIDs, strictly increasing                  [EXACT]
  C5 every parent id refers to an EARLIER record in the journal         [EXACT]
  C6 file ends with a newline (no torn tail)                            [EXACT]
  C7 re-serializing each parsed line canonically reproduces the on-disk
       bytes exactly (byte-identity of the journal representation)      [EXACT]

Output: human summary to stdout; JSON difference report (IVF §5.2 shape) to
--report PATH if given. Exit code 0 = GREEN, 1 = RED.

Usage:
  python ivf/verify_journal.py datastore/journal/journal.jsonl [--report out.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time

WIRE_FIELDS = {
    "record_id", "record_type", "schema_version", "producer", "event_ts",
    "recorded_ts", "parents", "payload", "meta", "content_hash", "prev_hash",
}
HASHED = ("record_type", "schema_version", "producer", "event_ts", "parents", "payload")
GENESIS = "0" * 64
ULID_ALPHABET = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")  # Crockford base32


def canonical(d: dict) -> bytes:
    """Blueprint §1.3, re-implemented from spec text: sorted keys, no
    whitespace, UTF-8, floats via json default (repr), NaN/Inf forbidden."""
    return json.dumps(d, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def is_ulid(s) -> bool:
    return isinstance(s, str) and len(s) == 26 and set(s) <= ULID_ALPHABET


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("journal")
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    diffs: list[dict] = []
    n = 0

    def red(key: str, expected, got, why: str) -> None:
        diffs.append({"key": key, "expected": str(expected)[:120],
                      "got": str(got)[:120], "delta": why, "band": "EXACT",
                      "status": "RED", "explanation": None})

    try:
        raw = open(args.journal, "rb").read()
    except OSError as e:
        red("file", "readable journal", str(e), "cannot open")
        raw = b""

    if raw and not raw.endswith(b"\n"):
        tail = raw[raw.rfind(b"\n") + 1:]
        red("C6.torn_tail", "file ends with newline",
            f"{len(tail)} trailing bytes", "torn final line")
        raw = raw[: raw.rfind(b"\n") + 1]

    prev_hash = GENESIS
    prev_id = ""
    seen: set[str] = set()

    for lineno, ln in enumerate(x for x in raw.split(b"\n") if x):
        n += 1
        where = f"line {lineno}"
        try:
            d = json.loads(ln.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            red(f"C1.{where}.json", "valid JSON", repr(ln[:60]), str(e))
            continue
        rid = d.get("record_id", f"<missing@{where}>")
        where = f"{rid}"

        if set(d) != WIRE_FIELDS:
            red(f"C1.{where}.fields", sorted(WIRE_FIELDS), sorted(d),
                "wire field set mismatch")
        # C7: byte-identity — canonical re-serialization must equal disk bytes
        try:
            if canonical(d) != ln:
                red(f"C7.{where}.bytes", "canonical(json) == disk line",
                    "differs", "journal line not in canonical form")
        except ValueError as e:
            red(f"C7.{where}.canonical", "serializable", str(e), "NaN/Inf?")

        # C2: content hash from spec-side recomputation
        try:
            body = {k: d[k] for k in HASHED}
            want = hashlib.sha256(canonical(body)).hexdigest()
            if d.get("content_hash") != want:
                red(f"C2.{where}.content_hash", want, d.get("content_hash"),
                    "stored field(s) tampered or hash rule drift")
        except (KeyError, ValueError) as e:
            red(f"C2.{where}.inputs", "six hashed fields present/serializable",
                str(e), "cannot recompute")
            want = None

        # C3: chain link
        if d.get("prev_hash") != prev_hash:
            red(f"C3.{where}.prev_hash", prev_hash, d.get("prev_hash"),
                "broken chain link")
        prev_hash = d.get("content_hash", prev_hash)

        # C4: ULID form + strict monotonicity
        if not is_ulid(rid):
            red(f"C4.{where}.ulid_form", "26-char Crockford ULID", rid, "bad id")
        elif prev_id and rid <= prev_id:
            red(f"C4.{where}.order", f"> {prev_id}", rid, "ids not increasing")
        prev_id = rid if isinstance(rid, str) else prev_id

        # C5: parents strictly earlier
        for p in d.get("parents", []):
            if p not in seen:
                red(f"C5.{where}.parent", "earlier record id", p,
                    "unknown or forward parent reference")
        if isinstance(rid, str):
            seen.add(rid)

    verdict = "GREEN" if not diffs else "RED"
    report = {
        "check_id": "s1.verify_journal", "sprint": 1, "class": "EXACT",
        "inputs": {"journal": args.journal}, "rows_compared": n,
        "green": n - len({d0["key"].split(".")[1] for d0 in diffs}) if diffs else n,
        "amber": 0, "red": len(diffs), "diffs": diffs, "verdict": verdict,
        "generated_ts": time.time_ns(),
    }
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    print(f"[IVF s1.verify_journal] records={n} verdict={verdict}")
    for d0 in diffs[:20]:
        print(f"  RED {d0['key']}: {d0['delta']} (expected {d0['expected']}, "
              f"got {d0['got']})")
    if len(diffs) > 20:
        print(f"  ... and {len(diffs) - 20} more")
    return 0 if verdict == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main())

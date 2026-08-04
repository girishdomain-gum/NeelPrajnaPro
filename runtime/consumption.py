"""Consumption: the runtime organ acting on an `Instruction`, and
execution feedback returning as observations (A-029 §2 IN list).

`consume()` is the ONE gate an instruction passes through before it can
reach the EA: expired is refused (`ExpiredInstruction`) BEFORE the
instruction is staged to the file the EA reads. This is defence in depth,
not redundant with the EA's own expiry check (3.2/W5) -- W5 explicitly
requires the refusal proven IN THE EA ITSELF, since a Python-side check
alone could be bypassed by staging the file directly. Both sides refuse
independently, on purpose.

FEEDBACK is deliberately NOT written through qrf's hash-chained
RecordStore: `runtime/` cannot import qrf.kernel (the firewall), and this
log is runtime bookkeeping, never evidence a verdict is computed from --
S08's judgment reads only from qrf's own ledgers. A plain JSONL append is
enough for that purpose; inventing a second hash-chain implementation
here would be exactly the kind of "second copy of logic we already own"
this project has already declined once (S07 import plan, F:\\Fable's
ivf/ and analyzer/).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from runtime.contract import Instruction
from runtime.errors import ExpiredInstruction


@dataclass(frozen=True)
class ConsumptionResult:
    instruction_id: str
    staged_path: Path


def consume(instruction: Instruction, now: int, stage_path: Path) -> ConsumptionResult:
    """Refuses an expired instruction before writing anything. Only on
    success does the instruction get staged (as JSON) for the EA to read
    -- mirroring S03's launcher staging pattern (a plain file the MT5 side
    polls), never a live IPC call.
    """
    if instruction.is_expired(now):
        raise ExpiredInstruction(instruction.instruction_id, instruction.valid_until, now)

    stage_path = Path(stage_path)
    stage_path.parent.mkdir(parents=True, exist_ok=True)
    # COMPACT JSON, no spaces (separators=(",", ":")): RefusalEA.mq5's own
    # hand-written JSON reader matches the literal `"key":"value"` shape
    # with no space after the colon -- proven the hard way (A-030 R2's
    # live run): the default json.dumps() spacing parsed on the Python
    # side but silently failed EVERY field lookup on the real EA, which
    # then refused with "missing instruction_id" on a payload that in
    # fact carried one. Never caught by a Python-only test; only running
    # the compiled EA against a real staged file surfaced it.
    stage_path.write_text(
        json.dumps(instruction.to_dict(), sort_keys=True, separators=(",", ":")),
        encoding="ascii",
    )
    return ConsumptionResult(instruction_id=instruction.instruction_id, staged_path=stage_path)


def ingest_feedback(feedback: dict, log_path: Path) -> dict:
    """Appends one execution-feedback record (whatever the EA's own log
    reports back -- e.g. "refused, reason X" or, in a later sprint once
    orders exist, a fill) as one JSON line. Returns the record as written,
    with an added `logged_seq` so a reader can tell append order without
    re-deriving it from file position.
    """
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    seq = 0
    if log_path.exists():
        with open(log_path, encoding="utf-8") as f:
            seq = sum(1 for _ in f)
    record = dict(feedback)
    record["logged_seq"] = seq
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
    return record

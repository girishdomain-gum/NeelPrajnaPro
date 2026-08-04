"""The Contract: turns a piece of belief into a CONDITIONAL, EXPIRING
instruction (A-029 §2.4, and the cost AM-02 named when thin hands was
ruled: "if price reaches X before time T, do Y", refused once T has
passed).

CLOCK SOURCE, stated explicitly because A-029 §2.4 required it: an
`Instruction`'s `valid_until` is a plain UTC unix-epoch second, produced
by the CALLER (Python's `time.time()` is UTC by definition, regardless of
machine timezone -- no conversion needed). This is deliberately NOT built
on S03's `clock_drift_probe_seconds`: that value is latency-inflated and
explicitly documented as never a timezone constant (F-04). The EA side
(mql5/EA/QRF/RefusalEA.mq5) compares against `TimeGMT()` -- the
terminal's own GMT-normalized broker time, not our noisy probe, and not
raw server time either. A few seconds of possible skew between the two
clocks is accepted deliberately: this EA places no orders, so "well
within" vs. "well past" its validity window is the only resolution that
matters, and expiry windows are sized in minutes, not seconds.
"""

from __future__ import annotations

from dataclasses import dataclass

from runtime.types import ReleasedKnowledge

ACTIONS = frozenset({"open"})


@dataclass(frozen=True)
class Instruction:
    instruction_id: str
    hypothesis_id: str
    measurement_id: str
    direction: str
    action: str
    trigger_price: float
    valid_from: int
    valid_until: int

    def is_expired(self, now: int) -> bool:
        return now > self.valid_until

    def to_dict(self) -> dict:
        return {
            "instruction_id": self.instruction_id,
            "hypothesis_id": self.hypothesis_id,
            "measurement_id": self.measurement_id,
            "direction": self.direction,
            "action": self.action,
            "trigger_price": self.trigger_price,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
        }


def build_instruction(
    release: ReleasedKnowledge,
    *,
    trigger_price: float,
    action: str = "open",
) -> Instruction:
    """Builds an instruction FROM belief already released -- `release`'s
    own `valid_from`/`valid_until` are carried through unchanged; the
    Contract does not invent a new validity window, it acts within the
    one the release already committed to.
    """
    if action not in ACTIONS:
        raise ValueError(f"action must be one of {sorted(ACTIONS)}, got {action!r}")
    if not release.significant or release.direction is None:
        raise ValueError(
            "cannot build an instruction from a not-significant release "
            "(A-030 R1: direction is structurally absent when significant is False)"
        )
    return Instruction(
        instruction_id=f"{release.release_id}:{action}",
        hypothesis_id=release.hypothesis_id,
        measurement_id=release.measurement_id,
        direction=release.direction,
        action=action,
        trigger_price=trigger_price,
        valid_from=release.valid_from,
        valid_until=release.valid_until,
    )

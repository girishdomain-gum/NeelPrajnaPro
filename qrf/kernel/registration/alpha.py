"""Alpha allocation: spent INCREMENTALLY per registration, never divided
up front (AM-03, Architect addition adopted by the Owner).

WHY NOT A FLAT DIVISION: capacity is 100 per family, but a flat division
(total_alpha / 100) would require EVERY test to clear p < 0.0005 --
representing that small a p-value needs thousands of resamples, and
against a population the size of a typical H-07 window (~300-3000
sweeps) that bar is close to unreachable. A budget set generously in the
name of research freedom would thereby make the family's FIRST verdict
nearly unpassable.

THE CHOSEN RULE: GEOMETRIC ALPHA SPENDING. The i-th registration in a
family (i = 1, 2, 3, ... in registration order) receives
    alpha_i = TOTAL_ALPHA * (1 - RATIO) * RATIO ** (i - 1)
For TOTAL_ALPHA=0.05, RATIO=0.5: alpha_1=0.025, alpha_2=0.0125,
alpha_3=0.00625, and so on, halving each time.

WHY THIS RULE, SPECIFICALLY:
  - It NEVER exceeds TOTAL_ALPHA cumulatively, at ANY capacity: the sum
    of an infinite geometric series with these terms converges exactly to
    TOTAL_ALPHA (sum_{i=1}^inf alpha_i = TOTAL_ALPHA * (1-r) * 1/(1-r) =
    TOTAL_ALPHA). At capacity 100, RATIO**100 is astronomically small, so
    the cumulative spend after all 100 registrations is TOTAL_ALPHA to
    far more decimal places than matters. The family-wide false-discovery
    protection AM-03 requires is intact regardless of how many of the
    100 slots are ever used.
  - It is INCREMENTAL, not divided up front: an early hypothesis is not
    taxed for ninety-nine that may never be registered. Registration #1
    gets HALF the entire family budget, not 1/100th of it.
  - It is a NAMED, DOCUMENTED, zero-discretion scheme (a geometric
    alpha-spending function, the same family of idea as sequential-trial
    spending functions like Pocock/O'Brien-Fleming, simplified to a
    closed form) -- not an ad hoc number.
  - It is STATED IN EVERY REGISTRATION RECORD (rule name + the two
    constants + the alpha this registration actually received), so a
    verdict is always interpretable under the rule it was judged by, even
    if a LATER family uses a different rule (AM-03's migration
    requirement: policy applies forward only, this record never changes).

This does mean later registrations receive rapidly shrinking alpha, and
therefore need rapidly growing N to remain testable at all (see
qrf.kernel.null.resampling.check_alpha_achievable) -- that tension is
real and is not hidden by this module; it is a KNOWN LIMITATION named in
the sprint report, not a defect of this rule specifically.
"""

from __future__ import annotations

ALLOCATION_RULE_NAME = "geometric_alpha_spending_v1"
TOTAL_ALPHA = 0.05
RATIO = 0.5


def alpha_for_registration_index(index: int) -> float:
    """`index` is 1-based: the 1st registration in a family gets
    `alpha_for_registration_index(1)`, the 2nd gets
    `alpha_for_registration_index(2)`, etc. Raises ValueError for a
    non-positive index -- there is no "0th" registration.
    """
    if index < 1:
        raise ValueError(f"registration index must be >= 1, got {index}")
    return TOTAL_ALPHA * (1 - RATIO) * (RATIO ** (index - 1))

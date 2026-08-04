"""Window-membership check: does a loaded bar set lie entirely inside a
claimed `[start, end)` span? (AM-07 Stage A P2 gate, A-042.)

SEPARATION OF CONCERNS, DELIBERATE (A-042, echoing D-041): the loader
(`qrf.kernel.observation.bars.load_bars_csv`) has no window argument at
all -- it only turns bytes into `Bar` objects. Window membership is a
different concern entirely and lives here, as its own small, pure
function, built and drilled BEFORE any replay uses it (A-042's
sequencing condition: "a boundary check written mid-replay is written
by someone who already wants the replay to proceed").

THE CONVENTION (stated in full in D-041, confirmed by the Architect in
A-042 by independent arithmetic): `Bar.time` is a bar's OWN OPEN TIME.
An M5 bar covers the half-open interval `[time, time + BAR_SECONDS)`.
A window `[start, end)` is half-open on the same open-time axis. A bar
is INSIDE the window iff its ENTIRE covered interval lies inside the
window's: `start <= bar.time` and `bar.time + BAR_SECONDS <= end`.

THE OFF-BY-ONE THIS EXISTS TO NAME: a bar opening EXACTLY at `end` must
FAIL -- it belongs to the NEXT window, not this one, because `end` is
never itself a valid open-time inside `[start, end)`. A bar opening
exactly AT `start` must PASS -- `start` is the first valid open-time.
The containment check above gets both right without a special case for
either edge: `bar.time == end` fails the `bar.time + BAR_SECONDS <= end`
half (since `BAR_SECONDS > 0`); `bar.time == start` passes the
`start <= bar.time` half by definition.
"""

from __future__ import annotations

from collections.abc import Sequence

from qrf.errors import WindowConflict
from qrf.kernel.detection.types import Bar

BAR_SECONDS = 300  # M5, frozen (STATE.md pinned facts)


def assert_bars_within_window(bars: Sequence[Bar], start: int, end: int) -> None:
    """Refuse (WindowConflict) on the FIRST bar whose covered interval is
    not entirely inside `[start, end)`, naming which bar (its index and
    open time) and which edge it violates. Raises nothing if every bar
    is inside, including the empty-sequence case (vacuously true).
    """
    if not start < end:
        raise WindowConflict("boundary", f"window [{start},{end}) is not a valid span")
    for index, bar in enumerate(bars):
        if bar.time < start:
            raise WindowConflict(
                "boundary",
                f"bar {index} (time={bar.time}) opens before the window's start "
                f"({start}) -- violates the start edge",
            )
        if bar.time + BAR_SECONDS > end:
            raise WindowConflict(
                "boundary",
                f"bar {index} (time={bar.time}) covers up to {bar.time + BAR_SECONDS}, "
                f"past the window's end ({end}) -- violates the end edge",
            )

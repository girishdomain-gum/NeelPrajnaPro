"""A self-describing null-test result (F-11, A-044): every null this
project runs -- block-resampling (S05) and circular-shift (F-09/A-035)
-- produces the SAME shape, so `Battery.judge()` can accept either
without knowing which one it got, and a written verdict is never silent
about which null produced it (A-044's requirement 3: "the null's
IDENTITY... is recorded in the verdict record itself, so no future
reader must infer it").

`parameters` carries whatever is specific to THAT null (block-resampling:
`block_length`; circular-shift: `min_offset`, `excluded_count`,
`horizon`) -- a plain dict, not a shared schema, because the two nulls
have genuinely different domain objects (a raw series + statistic_fn vs.
qualifying events + bars) and forcing a shared parameter schema would
either lose information or invent fields that mean nothing for one side.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NullOutcome:
    null_name: str
    p_value: float
    n_resamples: int
    seed: int
    parameters: dict

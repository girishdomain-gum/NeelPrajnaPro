"""Exception types for qrf.

Design after reference/NeelPrajnaPro_v1 @ 67b1d69 (which used named
exceptions for refusals rather than bare asserts), re-implemented.
"""


class QRFError(Exception):
    """Base class for every exception this project raises on purpose."""


class SchemaViolation(QRFError):
    """Raised when data does not match the shape or type it must have."""

    def __init__(self, what: str, value: object) -> None:
        self.what = what
        self.value = value
        super().__init__(f"schema violation: {what} (got: {value!r})")


class IntegrityViolation(QRFError):
    """Raised when data is internally inconsistent (e.g. a broken invariant)."""

    def __init__(self, what: str, value: object) -> None:
        self.what = what
        self.value = value
        super().__init__(f"integrity violation: {what} (got: {value!r})")

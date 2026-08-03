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


class WriterLockHeld(QRFError):
    """Raised when a second writer tries to append while another holds the
    store's single-writer lock. Never "last write wins" — refuse by name.
    """

    def __init__(self, lock_path: object) -> None:
        self.lock_path = lock_path
        super().__init__(f"writer lock held: {lock_path}")


class ChainCorruption(QRFError):
    """Raised when a record store's hash chain is broken: an altered,
    deleted, or reordered record. Distinct from TornTail, which is an
    incomplete final record, not a broken chain.
    """

    def __init__(self, index: int, reason: str) -> None:
        self.index = index
        self.reason = reason
        super().__init__(f"chain corruption at record {index}: {reason}")


class TornTail(QRFError):
    """Raised when a record store's final record is incomplete (a crash
    mid-write). Distinct from ChainCorruption: an incomplete tail is
    recoverable and expected; corruption in the middle of the chain never
    is.
    """

    def __init__(self, index: int, detail: str) -> None:
        self.index = index
        self.detail = detail
        super().__init__(f"torn tail at record {index}: {detail}")


class BulkMismatch(QRFError):
    """Raised when a bulk file's content hash or size does not match its
    manifest entry, or a manifest entry names a file that does not exist.
    """

    def __init__(self, name: str, reason: str) -> None:
        self.name = name
        self.reason = reason
        super().__init__(f"bulk mismatch for {name!r}: {reason}")


class WindowConflict(QRFError):
    """Raised for any window-ledger safety violation: reserving an
    overlapping span, burning an already-burned window, or using a
    TRAINING/EXPLORATION window as evidence.
    """

    def __init__(self, reason: str, detail: str) -> None:
        self.reason = reason
        self.detail = detail
        super().__init__(f"window conflict ({reason}): {detail}")


class LedgerImbalance(QRFError):
    """Raised by the window ledger's accounting check when the totals do
    not add up (e.g. a burn references a window that was never reserved).
    """

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"ledger imbalance: {detail}")

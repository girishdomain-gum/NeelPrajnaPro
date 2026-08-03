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


class SymbolRefused(QRFError):
    """Raised when a requested symbol is not an EXACT match for the pinned
    symbol (A-007 §2.4) — never "closest match", refuse by name.
    """

    def __init__(self, requested: str, pinned: str) -> None:
        self.requested = requested
        self.pinned = pinned
        super().__init__(f"symbol refused: requested {requested!r}, pinned symbol is {pinned!r}")


class ProvenanceViolation(QRFError):
    """Raised when a CSV does not match its provenance twin: a missing
    twin, a twin missing its hash field, or a recomputed hash that does
    not match what the twin records.
    """

    def __init__(self, what: str, detail: str) -> None:
        self.what = what
        self.detail = detail
        super().__init__(f"provenance violation ({what}): {detail}")


class TerminalBusy(QRFError):
    """Raised when the pinned terminal install is already running: MT5
    silently ignores a second /config launch of the same install, which
    would look like success while doing nothing — refuse instead.
    """

    def __init__(self, hits: object) -> None:
        self.hits = hits
        super().__init__(f"terminal busy, refusing to launch a second instance: {hits}")


class TerminalMismatch(QRFError):
    """Raised when a completed export's own metadata (broker/server/
    account/symbol) does not match the pinned facts, even though the
    terminal was launched by an explicit, hard-coded path. Defense in
    depth: an incident this sprint showed a bare `mt5.initialize()` (no
    explicit path) can silently attach to the wrong running terminal
    entirely; this check catches the same class of surprise even if the
    launch path itself were ever wrong.
    """

    def __init__(self, field: str, expected: object, actual: object) -> None:
        self.field = field
        self.expected = expected
        self.actual = actual
        super().__init__(f"terminal mismatch on {field}: expected {expected!r}, got {actual!r}")


class ClockDrift(QRFError):
    """Raised when a newly measured server-clock offset disagrees with the
    pinned offset from an earlier batch — mixing two time bases in one
    dataset silently destroys every timing-based measurement, so this is
    refused rather than guessed past.
    """

    def __init__(self, pinned_offset_seconds: float, measured_offset_seconds: float) -> None:
        self.pinned_offset_seconds = pinned_offset_seconds
        self.measured_offset_seconds = measured_offset_seconds
        super().__init__(
            f"clock drift: pinned offset {pinned_offset_seconds}s, "
            f"measured offset {measured_offset_seconds}s"
        )


class InsufficientResamples(QRFError):
    """Raised when the allocated alpha is smaller than the add-one
    estimator's minimum achievable p-value (1/(1+N)) -- the test cannot
    possibly reject at this N, so the battery refuses to run it rather
    than return a foregone "not significant" (A-015 §2.4).
    """

    def __init__(self, n_resamples: int, alpha: float) -> None:
        self.n_resamples = n_resamples
        self.alpha = alpha
        min_p = 1 / (1 + n_resamples)
        super().__init__(
            f"insufficient resamples: N={n_resamples} gives a minimum "
            f"achievable p-value of {min_p}, which cannot reject at "
            f"alpha={alpha}"
        )


class HypothesisNotRegistered(QRFError):
    """Raised when the battery is asked to judge a hypothesis id that has
    no registration record -- a verdict may only be computed against
    something frozen in advance.
    """

    def __init__(self, hypothesis_id: str) -> None:
        self.hypothesis_id = hypothesis_id
        super().__init__(f"hypothesis not registered: {hypothesis_id!r}")


class BudgetExhausted(QRFError):
    """Raised when a family's registration ledger is already at capacity
    (AM-03: 100 per family) -- a 101st registration is refused, never
    silently accepted past the cap.
    """

    def __init__(self, family_id: str, capacity: int) -> None:
        self.family_id = family_id
        self.capacity = capacity
        super().__init__(f"family {family_id!r} is at capacity ({capacity}); registration refused")


class RegistrationMismatch(QRFError):
    """Raised when a registration attempt reuses an existing hypothesis
    id with any frozen field changed -- a change to a frozen field MINTS
    A NEW HYPOTHESIS, it never edits the old one (A-015 §4.1).
    """

    def __init__(self, hypothesis_id: str, field: str) -> None:
        self.hypothesis_id = hypothesis_id
        self.field = field
        super().__init__(
            f"registration {hypothesis_id!r} already exists with a different "
            f"{field!r}; a changed frozen field must be a NEW hypothesis id"
        )


class CeremonyRefused(QRFError):
    """Raised when a registration ceremony's typed phrase is missing or
    does not match the expected hash. The phrase itself never appears in
    this exception, in any log, or anywhere on disk -- only its hash is
    ever compared or stored (A-015 §4.3).
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"ceremony refused: {reason}")


class UnverifiedObservations(QRFError):
    """Raised when an ObservationSet's source_sha256 does not match the
    hash the caller independently verified (e.g. via S03's
    provenance.verify()) -- the battery never trusts an ObservationSet's
    own say-so about its provenance (A-015 §3.3/B5).
    """

    def __init__(self, expected_sha256: str, actual_sha256: str) -> None:
        self.expected_sha256 = expected_sha256
        self.actual_sha256 = actual_sha256
        super().__init__(
            f"unverified observations: expected sha256 {expected_sha256!r}, "
            f"got {actual_sha256!r}"
        )

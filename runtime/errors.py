"""runtime/'s own exception types. Deliberately independent of
qrf.errors: `runtime/` may not import qrf.kernel (the firewall enforces
this), and full severance -- not merely "importing the parts that happen
to be allowed" -- keeps the two organs honestly decoupled.
"""


class RuntimeError_(Exception):
    """Base class for every exception this package raises on purpose.
    Named with a trailing underscore only to avoid shadowing the
    builtin `RuntimeError`.
    """


class MalformedRelease(RuntimeError_):
    """Raised when a dict claiming to be a knowledge release is missing a
    required field, has a field of the wrong type, or fails its sealed-
    hash check -- refused before it can become a `ReleasedKnowledge`.
    """

    def __init__(self, reason: str, detail: object = None) -> None:
        self.reason = reason
        self.detail = detail
        super().__init__(f"malformed release: {reason} (detail: {detail!r})")


class UntypedInput(RuntimeError_):
    """Raised when `Belief.update()` is given anything other than a real
    `ReleasedKnowledge` instance -- a raw dict is refused by name, even a
    dict with every field present and correct, because passing the type
    itself is the whole point of the check (A-029 §2.1).
    """

    def __init__(self, operation: str, got: object) -> None:
        self.operation = operation
        self.got_type = type(got).__name__
        super().__init__(f"{operation} requires a ReleasedKnowledge instance, got {self.got_type}")


class ExpiredInstruction(RuntimeError_):
    """Raised when an instruction's validity window has already passed at
    the moment it is consumed -- a thin hand that acts late is worse than
    one that does nothing (AM-02's own words, A-029 §1).
    """

    def __init__(self, instruction_id: str, valid_until: int, now: int) -> None:
        self.instruction_id = instruction_id
        self.valid_until = valid_until
        self.now = now
        super().__init__(
            f"instruction {instruction_id!r} expired: valid_until={valid_until}, now={now}"
        )


class ActionCapableControl(RuntimeError_):
    """Raised by the dashboard's own drill when a rendered surface (or its
    source) contains anything that could steer -- a buy/sell/close/enable/
    disable control. The mirror watches; it never steers (A-029 §4).
    """

    def __init__(self, token: str) -> None:
        self.token = token
        super().__init__(f"action-capable control detected: {token!r}")

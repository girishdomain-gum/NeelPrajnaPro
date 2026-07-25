"""The ``Simulator`` type the battery will accept — and reject the screener by (§4.7).

Blueprint §4.7: ``EvidenceBattery.run(..., simulator: Simulator, ...)`` and its
invariant *"simulator must be the audited engine (screener class rejected by
type)"*. The screener is a telescope (arrow 8) — it sweeps a grid to build a
shortlist and carries zero evidential weight; the engine is the judge's audited
simulator. They must never be confused, so the distinction is a **type** the
battery can check, not a naming convention.

A conforming simulator (1) exposes a ``simulate`` method and (2) carries the
``is_audited_simulator = True`` marker. The screener has neither — its public
method is ``run`` and it sets no marker — so ``isinstance(screener, Simulator)``
is ``False`` and :func:`require_audited_simulator` refuses it. The marker is a
positive, deliberate opt-in: a class becomes an audited simulator only by
declaring itself one, so a future screener-like class cannot drift into the type
by accidentally growing a ``simulate`` method.

This module is kernel: it names no prices and imports no trading code; the engine
that satisfies the protocol lives in ``qrf.trading`` and is injected.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Simulator(Protocol):
    """The audited-engine contract the battery judges through (structural)."""

    is_audited_simulator: bool

    def simulate(self, *args: Any, **kwargs: Any) -> Any:
        """Run the audited, no-look-ahead simulation and return its trades."""
        ...


def is_audited_simulator(obj: object) -> bool:
    """True iff ``obj`` is a conforming audited simulator (marker + ``simulate``)."""
    return isinstance(obj, Simulator) and getattr(obj, "is_audited_simulator", False) is True


def require_audited_simulator(obj: object) -> None:
    """Raise :class:`TypeError` unless ``obj`` is an audited simulator.

    The battery calls this before judging: a screener (or anything else lacking
    the marker + ``simulate``) is rejected by type, not by inspection of what it
    happens to do.
    """
    if not is_audited_simulator(obj):
        raise TypeError(
            f"object of type {type(obj).__name__!r} is not an audited Simulator "
            "(needs is_audited_simulator=True and a simulate() method); the screener "
            "class is rejected here by design (Blueprint §4.7)"
        )

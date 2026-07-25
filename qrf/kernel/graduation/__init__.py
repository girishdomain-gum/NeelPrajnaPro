"""Graduation — the promotion gate (ARCH-008 §2, G-1).

A claim graduates to a ``promotion`` record ONLY through all four gates; the
:class:`~qrf.kernel.graduation.promoter.Promoter` is the sole writer.
"""

from qrf.kernel.graduation.promoter import GraduationRefused, Promoter

__all__ = ["GraduationRefused", "Promoter"]

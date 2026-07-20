"""Small shared holder for the background scheduler instance.

Kept in the ``backend`` package (rather than ``scheduler``) so the API layer can
report scheduler health without importing the scheduler's heavier dependencies.
"""
from __future__ import annotations

from typing import Any

_scheduler: Any | None = None


def set_scheduler(scheduler: Any | None) -> None:
    global _scheduler
    _scheduler = scheduler


def scheduler_status() -> bool:
    """Return True if a scheduler is registered and running."""
    return bool(_scheduler is not None and getattr(_scheduler, "running", False))

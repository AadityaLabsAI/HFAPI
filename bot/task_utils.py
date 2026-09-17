"""Small asyncio task lifecycle helpers used by bot handlers."""

from __future__ import annotations

import asyncio
from typing import Any


def cancel_task_safely(task: asyncio.Task[Any] | None) -> bool:
    """Request cancellation for a live owned task without raising.

    Returns ``True`` when cancellation was requested and ``False`` when the
    task is missing or already complete. The owner should still await the task
    to consume cancellation when appropriate.
    """
    if task is None or task.done():
        return False
    task.cancel()
    return True

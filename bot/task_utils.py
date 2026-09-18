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


async def cancel_and_wait(task: asyncio.Task[Any] | None) -> bool:
    """Cancel an owned task and await it so cancellation is fully consumed.

    Returns ``True`` when a live task was cancelled and ``False`` when the
    task was missing or already complete. ``CancelledError`` from the owned
    task is intentionally swallowed; cancellation is the expected outcome for
    a task being cleaned up by its owner.
    """
    requested = cancel_task_safely(task)
    if not requested or task is None:
        return False

    try:
        await task
    except asyncio.CancelledError:
        pass
    return True

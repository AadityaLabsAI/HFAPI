"""Deterministic tests for background task lifecycle helpers."""

import asyncio

from bot.task_utils import cancel_task_safely


def test_cancel_task_safely_requests_cancellation_and_task_stops():
    async def sleeper():
        await asyncio.sleep(60)

    async def scenario():
        task = asyncio.create_task(sleeper())
        assert cancel_task_safely(task) is True
        try:
            await task
        except asyncio.CancelledError:
            return
        raise AssertionError("cancelled task completed without cancellation")

    asyncio.run(scenario())


def test_cancel_task_safely_is_idempotent_for_missing_or_done_task():
    async def scenario():
        assert cancel_task_safely(None) is False

        async def completed():
            return "done"

        task = asyncio.create_task(completed())
        await task
        assert cancel_task_safely(task) is False

    asyncio.run(scenario())

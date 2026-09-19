"""Deterministic tests for background task lifecycle helpers."""

import asyncio

import pytest

from bot.task_utils import cancel_and_wait, cancel_task_safely


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


def test_cancel_and_wait_consumes_expected_cancellation():
    async def sleeper():
        await asyncio.sleep(60)

    async def scenario():
        task = asyncio.create_task(sleeper())
        assert await cancel_and_wait(task) is True
        assert task.done()
        assert task.cancelled()

    asyncio.run(scenario())


def test_cancel_and_wait_is_safe_for_missing_or_done_task():
    async def scenario():
        assert await cancel_and_wait(None) is False

        async def completed():
            return "done"

        task = asyncio.create_task(completed())
        await task
        assert await cancel_and_wait(task) is False

    asyncio.run(scenario())


def test_cancel_and_wait_consumes_completed_task_exception():
    async def failing():
        raise RuntimeError("background failure")

    async def scenario():
        task = asyncio.create_task(failing())
        await asyncio.sleep(0)
        with pytest.raises(RuntimeError, match="background failure"):
            await cancel_and_wait(task)
        assert task.done()

    asyncio.run(scenario())

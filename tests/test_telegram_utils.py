"""Deterministic tests for Telegram transport safety helpers."""

import asyncio

import pytest
from telegram.error import BadRequest

from bot.telegram_utils import _is_markup_error, reply_text_safe


class FakeMessage:
    def __init__(self, failures=0, error_message="Can't parse entities"):
        self.failures = failures
        self.error_message = error_message
        self.calls = []

    async def reply_text(self, text, **kwargs):
        self.calls.append((text, kwargs))
        if self.failures:
            self.failures -= 1
            raise BadRequest(self.error_message)
        return "sent"


def test_reply_text_safe_retries_without_markup_after_bad_request():
    message = FakeMessage(failures=1)

    result = asyncio.run(
        reply_text_safe(message, "dynamic *status*", parse_mode="MarkdownV2")
    )

    assert result == "sent"
    assert len(message.calls) == 2
    assert message.calls[0][1]["parse_mode"] == "MarkdownV2"
    assert "parse_mode" not in message.calls[1][1]


def test_reply_text_safe_preserves_fallback_delivery_options():
    message = FakeMessage(failures=1)

    result = asyncio.run(
        reply_text_safe(
            message,
            "**status**",
            parse_mode="MarkdownV2",
            disable_web_page_preview=True,
        )
    )

    assert result == "sent"
    assert message.calls[1][1] == {"disable_web_page_preview": True}


def test_markup_error_detection_covers_telegram_variants():
    assert _is_markup_error(BadRequest("Can't parse inline expression"))
    assert _is_markup_error(BadRequest("Entity is not closed"))
    assert not _is_markup_error(BadRequest("Message is too long"))


def test_reply_text_safe_preserves_non_markup_bad_request():
    message = FakeMessage(failures=1)

    with pytest.raises(BadRequest, match="Can't parse entities"):
        asyncio.run(reply_text_safe(message, "plain text"))

    assert len(message.calls) == 1


def test_reply_text_safe_does_not_retry_unrelated_bad_request():
    message = FakeMessage(failures=1, error_message="Message is too long")

    with pytest.raises(BadRequest, match="Message is too long"):
        asyncio.run(
            reply_text_safe(message, "**large response**", parse_mode="MarkdownV2")
        )

    assert len(message.calls) == 1


def test_reply_text_safe_does_not_change_successful_formatted_reply():
    message = FakeMessage()

    result = asyncio.run(
        reply_text_safe(message, "**ready**", parse_mode="MarkdownV2", disable_web_page_preview=True)
    )

    assert result == "sent"
    assert len(message.calls) == 1
    assert message.calls[0][1] == {
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True,
    }

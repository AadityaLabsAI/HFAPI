"""Small Telegram transport helpers shared by bot handlers.

The Bot API rejects messages whose markup is malformed or whose text exceeds
its message-size limit. Model output and runtime status values are dynamic, so
formatting and payload size must never be a single point of failure for a
user-facing response.
"""

from __future__ import annotations

import logging
from typing import Any

from telegram.error import BadRequest

logger = logging.getLogger(__name__)

# Telegram currently limits text messages to 4096 characters. Keep a small
# safety margin so boundary-sized responses remain transport-safe.
TELEGRAM_TEXT_LIMIT = 4096
_REPLY_CHUNK_LIMIT = TELEGRAM_TEXT_LIMIT - 16

_MARKUP_ERROR_MARKERS = (
    "can't parse entities",
    "cant parse entities",
    "can't find end of the entity",
    "cant find end of the entity",
    "entity is not closed",
    "can't parse inline expression",
    "cant parse inline expression",
)


def _is_markup_error(error: BadRequest) -> bool:
    """Return whether Telegram rejected the message because of formatting."""
    message = str(error).strip().lower()
    return any(marker in message for marker in _MARKUP_ERROR_MARKERS)


def _split_text(text: str, limit: int = _REPLY_CHUNK_LIMIT) -> list[str]:
    """Split text into transport-safe chunks, preferring whitespace boundaries."""
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    remaining = text
    while len(remaining) > limit:
        boundary = remaining.rfind("\n", 0, limit + 1)
        if boundary < limit // 2:
            boundary = remaining.rfind(" ", 0, limit + 1)
        if boundary < limit // 2:
            boundary = limit

        chunk = remaining[:boundary].rstrip()
        if not chunk:
            chunk = remaining[:limit]
            boundary = len(chunk)

        chunks.append(chunk)
        remaining = remaining[boundary:].lstrip()

    if remaining:
        chunks.append(remaining)
    return chunks


async def reply_text_safe(message: Any, text: str, **kwargs: Any) -> Any:
    """Reply safely, falling back from markup and splitting oversized text.

    Existing formatting is preserved when valid. Malformed Markdown/MarkdownV2
    is retried as plain text, while oversized responses are split before they
    reach Telegram. Non-markup ``BadRequest`` failures are propagated because
    retrying them can hide real delivery errors.

    For a multi-part response, the return value is the Telegram result of the
    final successfully delivered chunk, matching normal single-message use.
    """
    chunks = _split_text(text)
    last_result: Any = None

    for chunk in chunks:
        try:
            last_result = await message.reply_text(chunk, **kwargs)
        except BadRequest as exc:
            parse_mode = kwargs.get("parse_mode")
            if not parse_mode or not _is_markup_error(exc):
                raise

            logger.warning(
                "Telegram rejected formatted reply; retrying as plain text",
                exc_info=True,
            )
            fallback_kwargs = dict(kwargs)
            fallback_kwargs.pop("parse_mode", None)
            last_result = await message.reply_text(chunk, **fallback_kwargs)

    return last_result

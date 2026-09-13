"""Small Telegram transport helpers shared by bot handlers.

The Bot API rejects messages whose markup is malformed. Model output and
runtime status values are dynamic, so MarkdownV2 formatting must never be a
single point of failure for a user-facing response.
"""

from __future__ import annotations

import logging
from typing import Any

from telegram.error import BadRequest

logger = logging.getLogger(__name__)


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


async def reply_text_safe(message: Any, text: str, **kwargs: Any) -> Any:
    """Reply with the requested formatting and fall back to plain text.

    This preserves existing formatting when it is valid while ensuring a
    malformed Markdown/MarkdownV2 response does not prevent the user from
    receiving the underlying message. Non-markup ``BadRequest`` failures are
    propagated unchanged because retrying them can hide real delivery errors
    such as invalid chat state or an overlong payload.
    """
    try:
        return await message.reply_text(text, **kwargs)
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
        return await message.reply_text(text, **fallback_kwargs)

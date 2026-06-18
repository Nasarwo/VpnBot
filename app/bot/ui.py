from __future__ import annotations

import logging
from typing import Any

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

logger = logging.getLogger(__name__)


async def edit(callback: CallbackQuery, text: str, **kwargs: Any) -> None:
    """Безопасно редактирует сообщение callback'а.

    ``callback.message`` может быть ``None`` или ``InaccessibleMessage`` (старое
    сообщение, к которому у бота нет доступа) — в этом случае молча пропускаем.
    """
    msg = callback.message
    if isinstance(msg, Message):
        await msg.edit_text(text, **kwargs)


async def answer(callback: CallbackQuery, text: str, **kwargs: Any) -> None:
    """Безопасно отправляет ответ в чат callback'а (если сообщение доступно)."""
    msg = callback.message
    if isinstance(msg, Message):
        await msg.answer(text, **kwargs)


async def answer_callback(
    callback: CallbackQuery,
    text: str | None = None,
    **kwargs: Any,
) -> None:
    """Отвечает на callback и игнорирует протухшие query-id после сетевых лагов."""
    try:
        await callback.answer(text, **kwargs)
    except TelegramBadRequest as exc:
        message = str(exc).lower()
        if "query is too old" in message or "query id is invalid" in message:
            logger.debug("Callback answer skipped: %s", exc)
            return
        raise

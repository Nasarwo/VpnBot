from __future__ import annotations

from typing import Any

from aiogram.types import CallbackQuery, Message


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

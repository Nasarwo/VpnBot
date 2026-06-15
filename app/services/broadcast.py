from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BroadcastResult:
    total: int
    sent: int
    failed: int


async def send_broadcast(
    bot: Bot | None,
    telegram_ids: list[int],
    text: str,
    *,
    delay: float = 0.05,
) -> BroadcastResult:
    """Рассылает текстовое сообщение всем пользователям.

    Сообщение отправляется обычным текстом (без parse_mode), чтобы произвольный
    текст администратора не ломал разметку. Ошибки доставки отдельным
    пользователям не прерывают рассылку; учитывается лимит частоты Telegram.
    """
    if bot is None:
        return BroadcastResult(total=len(telegram_ids), sent=0, failed=0)
    sent = 0
    failed = 0
    for tid in telegram_ids:
        try:
            await bot.send_message(tid, text)
            sent += 1
        except TelegramRetryAfter as exc:
            await asyncio.sleep(float(exc.retry_after) + 1.0)
            try:
                await bot.send_message(tid, text)
                sent += 1
            except TelegramAPIError:
                failed += 1
        except TelegramAPIError:
            failed += 1
        if delay:
            await asyncio.sleep(delay)
    logger.info(
        "Рассылка завершена: всего=%s доставлено=%s ошибок=%s",
        len(telegram_ids),
        sent,
        failed,
    )
    return BroadcastResult(total=len(telegram_ids), sent=sent, failed=failed)

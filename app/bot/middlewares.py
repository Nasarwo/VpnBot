from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram.types import User as TgUser

from app.config import Settings, get_settings
from app.db.repositories import UserRepository, VpnClientRepository
from app.db.session import get_sessionmaker
from app.services.access import resolve_effective_role

logger = logging.getLogger(__name__)

_SENSITIVE_COMMANDS = frozenset({"addserver"})


def _command_name(text: str) -> str:
    token = text.split(maxsplit=1)[0]
    if token.startswith("/"):
        return token.split("@", 1)[0][1:].lower()
    return ""


def _describe_message(event: Message) -> str:
    if event.text and event.text.startswith("/"):
        name = _command_name(event.text)
        if name in _SENSITIVE_COMMANDS:
            return f"command:{name} [redacted]"
        if " " in event.text.strip():
            return f"command:{name} [args redacted]"
        return f"command:{name}"

    if event.caption:
        return f"message:{event.content_type} caption[len={len(event.caption)}]"
    if event.text:
        return f"message:text[len={len(event.text)}]"
    return f"message:{event.content_type}"


def _describe_callback(event: CallbackQuery) -> str:
    data = event.data or ""
    if not data:
        return "callback:empty"
    parts = data.split(":")
    if len(parts) >= 2:
        return f"callback:{parts[0]} action={parts[1]}"
    return f"callback:{parts[0]}"


def _describe_event(event: TelegramObject) -> str:
    if isinstance(event, Message):
        return _describe_message(event)
    if isinstance(event, CallbackQuery):
        return _describe_callback(event)
    return event.__class__.__name__


class DbSessionMiddleware(BaseMiddleware):
    """Открывает сессию БД, получает/создаёт пользователя и кладёт их в data."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        settings: Settings = get_settings()
        sessionmaker = get_sessionmaker()
        tg_user_log: TgUser | None = data.get("event_from_user")
        if tg_user_log is not None:
            logger.info(
                "Апдейт от tg=%s (@%s): %s",
                tg_user_log.id,
                tg_user_log.username,
                _describe_event(event),
            )
        async with sessionmaker() as session:
            data["session"] = session
            data["settings"] = settings

            tg_user: TgUser | None = data.get("event_from_user")
            if tg_user is not None and not tg_user.is_bot:
                repo = UserRepository(session)
                existing = await repo.get_by_telegram_id(tg_user.id)
                client = None
                if existing is not None:
                    client = await VpnClientRepository(session).get_for_user(existing.id)
                desired_role = resolve_effective_role(settings, tg_user.id, client)
                db_user, _ = await repo.get_or_create(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    role=desired_role,
                )
                if db_user.role != desired_role:
                    db_user.role = desired_role
                await session.commit()
                data["db_user"] = db_user

            return await handler(event, data)

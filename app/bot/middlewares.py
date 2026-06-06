from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types import User as TgUser

from app.config import Settings, get_settings
from app.db.enums import UserRole
from app.db.repositories import UserRepository
from app.db.session import get_sessionmaker


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
        async with sessionmaker() as session:
            data["session"] = session
            data["settings"] = settings

            tg_user: TgUser | None = data.get("event_from_user")
            if tg_user is not None and not tg_user.is_bot:
                repo = UserRepository(session)
                desired_role = (
                    UserRole.ADMIN
                    if settings.is_admin(tg_user.id)
                    else UserRole.USER
                )
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

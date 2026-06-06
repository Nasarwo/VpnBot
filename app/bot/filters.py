from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from app.db.enums import UserRole
from app.db.models import User


class IsAdmin(BaseFilter):
    """Пропускает событие только если пользователь — администратор."""

    async def __call__(self, event: TelegramObject, db_user: User | None = None) -> bool:
        return db_user is not None and db_user.role == UserRole.ADMIN

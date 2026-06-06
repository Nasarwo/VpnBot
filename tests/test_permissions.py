from __future__ import annotations

from app.bot.filters import IsAdmin
from app.config import Settings
from app.db.enums import UserRole
from app.db.models import User


async def test_is_admin_filter_rejects_regular_user():
    flt = IsAdmin()
    user = User(telegram_id=1, role=UserRole.USER)
    assert await flt(object(), db_user=user) is False


async def test_is_admin_filter_accepts_admin():
    flt = IsAdmin()
    user = User(telegram_id=1, role=UserRole.ADMIN)
    assert await flt(object(), db_user=user) is True


async def test_is_admin_filter_rejects_missing_user():
    flt = IsAdmin()
    assert await flt(object(), db_user=None) is False


def test_settings_is_admin():
    settings = Settings(admin_telegram_ids=[10, 20])
    assert settings.is_admin(10) is True
    assert settings.is_admin(30) is False


def test_settings_parses_admin_ids_from_string():
    settings = Settings(admin_telegram_ids="10, 20 ,30")
    assert settings.admin_telegram_ids == [10, 20, 30]

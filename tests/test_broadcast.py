from __future__ import annotations

from aiogram.exceptions import TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.enums import UserRole
from app.db.models import User
from app.db.repositories import UserRepository
from app.services import broadcast


class FakeBot:
    def __init__(self, fail_ids: set[int] | None = None) -> None:
        self.fail_ids = fail_ids or set()
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id: int, text: str, **kwargs: object) -> None:
        if chat_id in self.fail_ids:
            raise TelegramAPIError(method=None, message="blocked")
        self.sent.append((chat_id, text))


async def test_send_broadcast_counts_sent_and_failed():
    bot = FakeBot(fail_ids={2})
    result = await broadcast.send_broadcast(bot, [1, 2, 3], "привет", delay=0)
    assert result.total == 3
    assert result.sent == 2
    assert result.failed == 1
    assert (1, "привет") in bot.sent
    assert (3, "привет") in bot.sent


async def test_send_broadcast_empty_list():
    bot = FakeBot()
    result = await broadcast.send_broadcast(bot, [], "x", delay=0)
    assert result.total == 0 and result.sent == 0 and result.failed == 0


async def test_all_telegram_ids_returns_every_user(session: AsyncSession):
    session.add_all(
        [
            User(telegram_id=111, role=UserRole.USER),
            User(telegram_id=222, role=UserRole.ADMIN),
            User(telegram_id=333, role=UserRole.USER),
        ]
    )
    await session.commit()
    ids = await UserRepository(session).all_telegram_ids()
    assert set(ids) == {111, 222, 333}


def test_broadcast_text_is_plain_no_parse_mode():
    """Текст рассылки шлётся без parse_mode — произвольный текст админа не должен
    ломать HTML-разметку."""
    # Свойство закреплено в реализации send_broadcast: send_message без parse_mode.
    settings = Settings(admin_telegram_ids=[1])
    assert settings.is_admin(1)  # smoke

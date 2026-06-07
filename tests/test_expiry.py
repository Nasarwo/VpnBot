from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, VpnClient
from app.db.repositories import VpnClientRepository
from app.services import expiry
from tests.conftest import utcnow


class FakeBot:
    def __init__(self) -> None:
        self.messages: list[tuple[int, str, dict]] = []

    async def send_message(self, chat_id: int, text: str, **kwargs: object) -> None:
        self.messages.append((chat_id, text, kwargs))


def test_target_stage_boundaries():
    now = utcnow()
    assert expiry._target_stage(now + timedelta(days=2), now) == 0
    assert expiry._target_stage(now + timedelta(hours=20), now) == 1
    assert expiry._target_stage(now + timedelta(minutes=30), now) == 2
    assert expiry._target_stage(now - timedelta(minutes=1), now) == 3


async def test_notifies_day_before_once(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    vpn_client.expires_at = utcnow() + timedelta(hours=12)
    await session.commit()

    bot = FakeBot()
    sent = await expiry.process_expiry_notifications(session, bot)
    assert sent == 1
    assert bot.messages[0][0] == user.telegram_id
    assert bot.messages[0][2].get("parse_mode") == "HTML"

    refreshed = await VpnClientRepository(session).get_for_user(user.id)
    assert refreshed.expiry_notify_stage == 1

    # Повторный прогон не дублирует уведомление той же стадии.
    bot2 = FakeBot()
    assert await expiry.process_expiry_notifications(session, bot2) == 0


async def test_progresses_through_stages(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    vpn_client.expires_at = utcnow() + timedelta(hours=12)
    await session.commit()
    bot = FakeBot()
    await expiry.process_expiry_notifications(session, bot)  # стадия 1

    vpn_client.expires_at = utcnow() + timedelta(minutes=30)
    await session.commit()
    assert await expiry.process_expiry_notifications(session, bot) == 1  # стадия 2

    vpn_client.expires_at = utcnow() - timedelta(minutes=1)
    await session.commit()
    assert await expiry.process_expiry_notifications(session, bot) == 1  # стадия 3

    refreshed = await VpnClientRepository(session).get_for_user(user.id)
    assert refreshed.expiry_notify_stage == 3

    # После финальной стадии больше ничего не шлём.
    assert await expiry.process_expiry_notifications(session, bot) == 0


async def test_no_notification_when_far_from_expiry(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    vpn_client.expires_at = utcnow() + timedelta(days=10)
    await session.commit()
    bot = FakeBot()
    assert await expiry.process_expiry_notifications(session, bot) == 0


async def test_stage_resets_allow_new_cycle(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    """После продления (стадия сброшена в 0) уведомления идут заново."""
    vpn_client.expires_at = utcnow() - timedelta(minutes=1)
    vpn_client.expiry_notify_stage = 3
    await session.commit()
    bot = FakeBot()
    assert await expiry.process_expiry_notifications(session, bot) == 0

    # Продлили: срок в будущем, стадия сброшена.
    vpn_client.expires_at = utcnow() + timedelta(hours=12)
    vpn_client.expiry_notify_stage = 0
    await session.commit()
    assert await expiry.process_expiry_notifications(session, bot) == 1

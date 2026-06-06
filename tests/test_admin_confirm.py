from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import notify
from app.config import Settings
from app.db.models import User, VpnClient
from app.db.repositories import PaymentRepository
from app.services import billing, payments
from app.services.panel_updater import MockPanelUpdater


@dataclass
class FakeBot:
    messages: list[dict[str, Any]] = field(default_factory=list)

    async def send_message(self, chat_id: int, text: str, **kwargs: Any) -> None:
        self.messages.append({"chat_id": chat_id, "text": text, **kwargs})

    async def send_photo(self, chat_id: int, photo: str, **kwargs: Any) -> None:
        self.messages.append({"chat_id": chat_id, "photo": photo, **kwargs})

    async def send_document(self, chat_id: int, document: str, **kwargs: Any) -> None:
        self.messages.append({"chat_id": chat_id, "document": document, **kwargs})


async def test_admin_notified_about_new_request(session: AsyncSession, user: User):
    settings = Settings(admin_telegram_ids=[111, 222])
    payment = await payments.create_request(
        session, user_id=user.id, amount=175, period_days=30
    )
    bot = FakeBot()

    await notify.notify_admins_new_request(bot, settings, payment, user)

    assert {m["chat_id"] for m in bot.messages} == {111, 222}
    assert payment.payment_code in bot.messages[0]["text"]


async def test_confirm_then_notify_user(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    payment = await payments.create_request(
        session, user_id=user.id, amount=175, period_days=30
    )
    result = await billing.confirm_payment(
        session, payment.id, actor_user_id=user.id, updater=MockPanelUpdater()
    )
    assert result.applied is True

    bot = FakeBot()
    refreshed_client = vpn_client
    await session.refresh(refreshed_client)
    await notify.notify_user_extended(bot, user.telegram_id, refreshed_client)

    assert bot.messages[0]["chat_id"] == user.telegram_id
    assert "продл" in bot.messages[0]["text"].lower()


async def test_reject_then_notify_user(session: AsyncSession, user: User):
    payment = await payments.create_request(
        session, user_id=user.id, amount=175, period_days=30
    )
    await billing.reject_payment(session, payment.id, actor_user_id=user.id)
    refreshed = await PaymentRepository(session).get_by_id_with_relations(payment.id)

    bot = FakeBot()
    await notify.notify_user_rejected(
        bot, refreshed.user.telegram_id, refreshed.payment_code
    )
    assert bot.messages[0]["chat_id"] == user.telegram_id
    assert refreshed.payment_code in bot.messages[0]["text"]

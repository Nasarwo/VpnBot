from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import admin_handlers
from app.config import Settings
from app.db.models import User, VpnClient
from app.db.repositories import VpnClientRepository
from app.services import subscription_delete
from app.services.panel_updater import MockPanelUpdater


@dataclass
class _FakeBot:
    messages: list[dict[str, Any]] = field(default_factory=list)

    async def send_message(self, chat_id: int, text: str, **kwargs: Any) -> None:
        self.messages.append({"chat_id": chat_id, "text": text, **kwargs})


@dataclass
class _FakeMessage:
    text: str
    bot: _FakeBot = field(default_factory=_FakeBot)
    answers: list[dict[str, Any]] = field(default_factory=list)

    async def answer(self, text: str, **kwargs: Any) -> None:
        self.answers.append({"text": text, **kwargs})


@dataclass
class _FakeState:
    cleared: bool = False

    async def clear(self) -> None:
        self.cleared = True


async def test_delete_subscription_removes_panel_and_local_client(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    updater = MockPanelUpdater()

    result = await subscription_delete.delete_user_subscription(
        session, user, updater, actor_user_id=None
    )

    assert result.deleted is True
    assert updater.deleted == [(1, ("test@local",))]
    assert await VpnClientRepository(session).get_for_user(user.id) is None
    assert await session.get(User, user.id) is not None


async def test_delete_subscription_keeps_local_client_on_panel_failure(
    session: AsyncSession, user: User, vpn_client: VpnClient, server
):
    updater = MockPanelUpdater(fail_server_ids={server.id})

    result = await subscription_delete.delete_user_subscription(
        session, user, updater, actor_user_id=None
    )

    assert result.deleted is False
    assert result.failed_servers
    assert await VpnClientRepository(session).get_for_user(user.id) is not None


async def test_delete_subscription_without_client_is_noop(
    session: AsyncSession, user: User
):
    result = await subscription_delete.delete_user_subscription(
        session, user, MockPanelUpdater(), actor_user_id=None
    )

    assert result.deleted is False
    assert result.no_client is True


async def test_admin_delete_subscription_uses_client_id_not_telegram_id(
    session: AsyncSession,
    user: User,
    admin: User,
    vpn_client: VpnClient,
    monkeypatch,
):
    user.public_id = "6B8A6580"
    await session.commit()
    monkeypatch.setattr(
        admin_handlers,
        "_get_updater",
        lambda settings: MockPanelUpdater(),
    )

    wrong_message = _FakeMessage(str(user.telegram_id))
    wrong_state = _FakeState()
    await admin_handlers.admin_delete_subscription_by_client_id(
        wrong_message,
        session,
        wrong_state,
        admin,
        Settings(admin_telegram_ids=[admin.telegram_id]),
    )

    assert wrong_state.cleared is False
    assert "не найден" in wrong_message.answers[-1]["text"]
    assert await VpnClientRepository(session).get_for_user(user.id) is not None

    right_message = _FakeMessage("6b8a6580")
    right_state = _FakeState()
    await admin_handlers.admin_delete_subscription_by_client_id(
        right_message,
        session,
        right_state,
        admin,
        Settings(admin_telegram_ids=[admin.telegram_id]),
    )

    assert right_state.cleared is True
    assert await VpnClientRepository(session).get_for_user(user.id) is None
    assert right_message.bot.messages[0]["chat_id"] == user.telegram_id
    assert any("6B8A6580" in answer["text"] for answer in right_message.answers)

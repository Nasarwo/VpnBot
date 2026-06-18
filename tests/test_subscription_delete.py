from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, VpnClient
from app.db.repositories import VpnClientRepository
from app.services import subscription_delete
from app.services.panel_updater import MockPanelUpdater


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

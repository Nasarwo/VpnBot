from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, VpnClient
from app.db.repositories import UserRepository, VpnClientRepository
from app.services import billing
from app.services.panel_updater import MockPanelUpdater


async def test_grant_trial_success(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    result = await billing.grant_trial(
        session, user_id=user.id, updater=MockPanelUpdater(), period_days=2
    )
    assert result.applied is True
    assert result.new_expires_at is not None

    refreshed_user = await UserRepository(session).get_by_id(user.id)
    assert refreshed_user.trial_used is True

    client = await VpnClientRepository(session).get_for_user(user.id)
    assert client.expires_at is not None
    assert client.is_active is True


async def test_trial_only_once(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    first = await billing.grant_trial(
        session, user_id=user.id, updater=MockPanelUpdater(), period_days=2
    )
    assert first.applied is True
    expiry_after_first = first.new_expires_at

    second = await billing.grant_trial(
        session, user_id=user.id, updater=MockPanelUpdater(), period_days=2
    )
    assert second.applied is False
    assert second.already_used is True

    client = await VpnClientRepository(session).get_for_user(user.id)
    assert client.expires_at == expiry_after_first


async def test_trial_without_client(session: AsyncSession, user: User):
    result = await billing.grant_trial(
        session, user_id=user.id, updater=MockPanelUpdater(), period_days=2
    )
    assert result.applied is False
    assert result.no_client is True

    refreshed_user = await UserRepository(session).get_by_id(user.id)
    assert refreshed_user.trial_used is False


async def test_trial_failure_can_be_retried(
    session: AsyncSession, user: User, vpn_client: VpnClient, server
):
    failing = await billing.grant_trial(
        session,
        user_id=user.id,
        updater=MockPanelUpdater(fail_server_ids={server.id}),
        period_days=2,
    )
    assert failing.applied is False
    assert failing.failed_servers

    # Триал не должен считаться использованным после ошибки.
    refreshed_user = await UserRepository(session).get_by_id(user.id)
    assert refreshed_user.trial_used is False

    retry = await billing.grant_trial(
        session, user_id=user.id, updater=MockPanelUpdater(), period_days=2
    )
    assert retry.applied is True
    refreshed_user = await UserRepository(session).get_by_id(user.id)
    assert refreshed_user.trial_used is True


async def test_trial_extends_active_subscription(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    from tests.conftest import utcnow

    old_expiry = utcnow() + timedelta(days=10)
    vpn_client.expires_at = old_expiry
    await session.commit()

    result = await billing.grant_trial(
        session, user_id=user.id, updater=MockPanelUpdater(), period_days=2
    )
    assert result.applied is True
    # +2 дня к активному сроку
    assert result.new_expires_at == old_expiry + timedelta(days=2)

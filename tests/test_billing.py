from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import PaymentStatus, Protocol
from app.db.models import ClientServerMapping, PendingServerUpdate, Server, User, VpnClient
from app.db.repositories import PaymentRepository, VpnClientRepository
from app.services import billing
from app.services.panel_updater import MockPanelUpdater
from tests.conftest import utcnow


def test_compute_new_expiry_active():
    now = utcnow()
    current = now + timedelta(days=10)
    result = billing.compute_new_expiry(current, now, 30)
    assert result == current + timedelta(days=30)


def test_compute_new_expiry_expired():
    now = utcnow()
    current = now - timedelta(days=5)
    result = billing.compute_new_expiry(current, now, 30)
    assert result == now + timedelta(days=30)


def test_compute_new_expiry_none():
    now = utcnow()
    result = billing.compute_new_expiry(None, now, 30)
    assert result == now + timedelta(days=30)


async def _make_waiting_payment(
    session: AsyncSession, user: User, period_days: int = 30
):
    repo = PaymentRepository(session)
    payment = await repo.create(
        user_id=user.id,
        amount=175,
        period_days=period_days,
        payment_code="PAY-1042",
        status=PaymentStatus.WAITING_ADMIN,
    )
    await session.commit()
    return payment


async def test_confirm_payment_extends_expired(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    payment = await _make_waiting_payment(session, user)
    updater = MockPanelUpdater()

    result = await billing.confirm_payment(
        session, payment.id, actor_user_id=user.id, updater=updater
    )

    assert result.applied is True
    assert result.first_purchase is True
    assert result.payment.status == PaymentStatus.APPLIED
    assert result.payment.applied_at is not None
    refreshed = await VpnClientRepository(session).get_for_user(user.id)
    assert refreshed.is_active is True
    assert refreshed.expires_at is not None
    assert len(updater.calls) == 1


async def test_double_confirm_is_idempotent(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    payment = await _make_waiting_payment(session, user)
    updater = MockPanelUpdater()

    first = await billing.confirm_payment(
        session, payment.id, actor_user_id=user.id, updater=updater
    )
    expiry_after_first = first.new_expires_at

    second = await billing.confirm_payment(
        session, payment.id, actor_user_id=user.id, updater=updater
    )

    assert second.already_applied is True
    assert second.applied is False
    refreshed = await VpnClientRepository(session).get_for_user(user.id)
    assert refreshed.expires_at == expiry_after_first
    # Панель не должна вызываться повторно
    assert len(updater.calls) == 1


async def test_second_purchase_is_not_first(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    repo = PaymentRepository(session)
    first = await repo.create(
        user_id=user.id,
        amount=175,
        period_days=30,
        payment_code="PAY-3001",
        status=PaymentStatus.WAITING_ADMIN,
    )
    await session.commit()
    updater = MockPanelUpdater()
    r1 = await billing.confirm_payment(
        session, first.id, actor_user_id=user.id, updater=updater
    )
    assert r1.first_purchase is True

    second = await repo.create(
        user_id=user.id,
        amount=175,
        period_days=30,
        payment_code="PAY-3002",
        status=PaymentStatus.WAITING_ADMIN,
    )
    await session.commit()
    r2 = await billing.confirm_payment(
        session, second.id, actor_user_id=user.id, updater=updater
    )
    assert r2.applied is True
    assert r2.first_purchase is False


async def test_confirm_queues_failed_server_update(
    session: AsyncSession, user: User, vpn_client: VpnClient, server
):
    payment = await _make_waiting_payment(session, user)
    updater = MockPanelUpdater(fail_server_ids={server.id})

    result = await billing.confirm_payment(
        session, payment.id, actor_user_id=user.id, updater=updater
    )

    assert result.applied is True
    assert result.payment.status == PaymentStatus.APPLIED
    assert result.failed_servers
    refreshed = await VpnClientRepository(session).get_for_user(user.id)
    assert refreshed.expires_at is not None
    rows = (await session.execute(PendingServerUpdate.__table__.select())).all()
    assert len(rows) == 1


async def test_confirm_applies_available_servers_and_queues_unavailable(
    session: AsyncSession, user: User, vpn_client: VpnClient, server
):
    second = Server(
        name="srv-2",
        country="DE",
        panel_url="http://panel-2.local:2053",
        username="admin",
        password="secret",
        enabled=True,
    )
    session.add(second)
    await session.flush()
    session.add(
        ClientServerMapping(
            vpn_client_id=vpn_client.id,
            server_id=second.id,
            inbound_id=1,
            protocol=Protocol.VLESS,
            client_uuid="uuid-1",
            email="test@local",
            enabled=True,
        )
    )
    await session.commit()

    payment = await _make_waiting_payment(session, user)
    updater = MockPanelUpdater(fail_server_ids={second.id})

    result = await billing.confirm_payment(
        session, payment.id, actor_user_id=user.id, updater=updater
    )

    assert result.applied is True
    assert [call[0] for call in updater.calls] == [server.id, second.id]
    assert [r.server_id for r in result.failed_servers] == [second.id]
    pending_rows = (await session.execute(PendingServerUpdate.__table__.select())).all()
    assert len(pending_rows) == 1


async def test_pending_update_applies_same_target_later(
    session: AsyncSession, user: User, vpn_client: VpnClient, server
):
    payment = await _make_waiting_payment(session, user)
    failing = MockPanelUpdater(fail_server_ids={server.id})
    now = utcnow()
    await billing.confirm_payment(
        session, payment.id, actor_user_id=user.id, updater=failing, now=now
    )

    applied = await PaymentRepository(session).get_by_id(payment.id)
    assert applied.target_expires_at is not None
    target = billing._as_aware(applied.target_expires_at)

    from app.services import pending_updates

    healthy = MockPanelUpdater()
    pending_results = await pending_updates.apply_pending_for_server(
        session, server.id, healthy
    )

    assert [item.ok for item in pending_results] == [True]
    refreshed = await VpnClientRepository(session).get_for_user(user.id)
    assert billing._as_aware(refreshed.expires_at) == target
    assert healthy.calls[-1] == (server.id, billing.expiry_to_ms(target))


async def test_manual_extend_fails_without_mappings(
    session: AsyncSession, user: User
):
    client = VpnClient(user_id=user.id, is_active=False)
    session.add(client)
    await session.commit()

    result = await billing.manual_extend(
        session,
        client.id,
        period_days=30,
        actor_user_id=user.id,
        updater=MockPanelUpdater(),
    )
    assert result.applied is False
    refreshed = await VpnClientRepository(session).get_for_user(user.id)
    assert refreshed.expires_at is None


async def test_confirm_stores_target_before_panel_failure(
    session: AsyncSession, user: User, vpn_client: VpnClient, server
):
    payment = await _make_waiting_payment(session, user)
    now = utcnow()
    await billing.confirm_payment(
        session,
        payment.id,
        actor_user_id=user.id,
        updater=MockPanelUpdater(fail_server_ids={server.id}),
        now=now,
    )
    refreshed = await PaymentRepository(session).get_by_id(payment.id)
    assert billing._as_aware(refreshed.target_expires_at) == now + timedelta(days=30)
    assert refreshed.status == PaymentStatus.APPLIED


async def test_confirm_requires_waiting_status(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    repo = PaymentRepository(session)
    payment = await repo.create(
        user_id=user.id,
        amount=175,
        period_days=30,
        payment_code="PAY-2000",
        status=PaymentStatus.CREATED,
    )
    await session.commit()

    with pytest.raises(billing.BillingError):
        await billing.confirm_payment(
            session, payment.id, actor_user_id=user.id, updater=MockPanelUpdater()
        )


async def test_confirm_no_client_marks_failed(session: AsyncSession, user: User):
    payment = await _make_waiting_payment(session, user)
    result = await billing.confirm_payment(
        session, payment.id, actor_user_id=user.id, updater=MockPanelUpdater()
    )
    assert result.applied is False
    assert result.payment.status == PaymentStatus.FAILED


async def test_reject_payment(session: AsyncSession, user: User):
    payment = await _make_waiting_payment(session, user)
    result = await billing.reject_payment(
        session, payment.id, actor_user_id=user.id, comment="нет оплаты"
    )
    assert result.status == PaymentStatus.REJECTED
    assert result.admin_comment == "нет оплаты"

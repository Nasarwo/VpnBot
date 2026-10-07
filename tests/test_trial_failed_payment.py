"""Принятая оплата подписки закрывает trial, даже если применение доступа завершилось ``failed``.

Принятие оплаты (решение администратора, ``confirmed_at``/``target_expires_at``)
отделено от результата применения. ``failed`` после принятия — сбой конфигурации,
оплата остаётся принятой; ``failed`` до принятия (заявка упала до фиксации срока)
подпиской не считается. Правило общее для сервиса, кнопки бота, профиля сайта и
устойчивой записи ``subscription_purchases``.
"""
from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import func, select, update

from app.bot import texts, user_handlers
from app.db.enums import PaymentStatus, Protocol
from app.db.models import (
    PAYMENT_KIND_TRAFFIC,
    ClientServerMapping,
    PaymentRequest,
    Server,
    ServerInbound,
    SubscriptionPurchase,
    TrialGrant,
    User,
    VpnClient,
    WebAccount,
    WhitelistLedger,
)
from app.services import billing, payments, whitelist
from app.services.panel_updater import MockPanelUpdater
from app.services.user_reset import ResetBlock
from tests.conftest import utcnow
from tests.test_trial_reset import _file_db, _fresh, bridge  # noqa: F401
from tests.test_trial_subscription_rule import _old_trial_button, _state
from tests.test_user_reset import _reset
from tests.test_whitelist import service_on, std_target, wl_server  # noqa: F401

GIB = whitelist.GIB


async def _trial(session, user_id, panel):
    return await billing.grant_trial(session, user_id, panel, period_days=3)


async def _set_mappings(session, client_id: int, enabled: bool) -> None:
    await session.execute(
        update(ClientServerMapping)
        .where(ClientServerMapping.vpn_client_id == client_id)
        .values(enabled=enabled)
    )
    await session.commit()


async def _accepted_failed(session, user, client) -> PaymentRequest:
    """Администратор принял оплату, но все назначения клиента отключены → ``failed``.

    После этого конфигурацию «чинят» (назначения снова включены): trial выдал бы
    панели и пакет услуги, если бы правило не учитывало принятую оплату.
    """
    await _set_mappings(session, client.id, False)
    payment = await payments.create_request(session, user.id, 175, 30)
    result = await billing.confirm_payment(session, payment.id, None, MockPanelUpdater())
    assert not result.applied and payment.status == PaymentStatus.FAILED
    assert payment.confirmed_at is not None and payment.target_expires_at is not None
    await _set_mappings(session, client.id, True)
    return payment


async def _purchases(session) -> list[SubscriptionPurchase]:
    return (
        await session.scalars(
            select(SubscriptionPurchase).execution_options(populate_existing=True)
        )
    ).all()


# --- Принятая оплата + сбой применения блокирует trial ---------------------------------


async def test_accepted_failed_purchase_blocks_trial_without_side_effects(
    session, user, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    payment = await _accepted_failed(session, user, vpn_client)
    before = await _state(session, user.id, panel)
    # Пакет услуги выдан при принятии (10 ГиБ); trial добавил бы ещё 3 ГиБ.
    assert before["balance"] == (10 * GIB, 0)
    assert before["trial_used"] is False and before["grants"] == 0

    assert await billing.subscription_already_purchased(session, user)
    assert not await billing.trial_available(session, user)
    assert not await user_handlers._trial_available(session, user)
    result = await _trial(session, user.id, panel)
    callback = await _old_trial_button(session, user, panel, monkeypatch)

    assert not result.applied and result.subscription_purchased
    assert not result.already_used and not result.no_client
    assert callback.message.edits == [texts.trial_subscription_purchased()]
    assert await _state(session, user.id, panel) == before
    assert payment.status == PaymentStatus.FAILED  # trial заявку не трогает


async def test_accepted_failed_purchase_blocks_trial_on_site(
    session, user, vpn_client, bridge  # noqa: F811
):
    call, bridge_panel = bridge
    await _accepted_failed(session, user, vpn_client)
    account = WebAccount(email="f@example.com", password_hash="x", verified=True,
                         user_id=user.id)
    session.add(account)
    await session.commit()

    status, profile = await call("profile", account.id)
    assert status == 200 and profile["trial_available"] is False
    status, _ = await call("trial", account.id)

    assert status == 409
    assert bridge_panel.provisioned == [] and bridge_panel.calls == []
    assert await session.scalar(select(func.count()).select_from(TrialGrant)) == 0


async def test_accepted_failed_without_confirmed_at_is_recognised_by_target(
    session, user, std_target  # noqa: F811
):
    """Устаревшая строка: срок зафиксирован, ``confirmed_at`` не проставлен."""
    payment = await payments.create_request(session, user.id, 175, 30)
    payment.status = PaymentStatus.FAILED
    payment.target_expires_at = utcnow()
    await session.commit()

    assert await billing.subscription_already_purchased(session, user)
    assert (await _trial(session, user.id, MockPanelUpdater())).subscription_purchased


# --- Отказ до принятия оплаты отличается от сбоя после принятия ------------------------


async def test_failed_before_acceptance_does_not_block_trial_by_itself(session, user):
    """Нет клиента и серверов: заявка падает до фиксации срока, оплата не принята."""
    payment = await payments.create_request(session, user.id, 175, 30)
    result = await billing.confirm_payment(session, payment.id, None, MockPanelUpdater())
    assert not result.applied and payment.status == PaymentStatus.FAILED
    assert payment.confirmed_at is None and payment.target_expires_at is None

    assert not await billing.subscription_already_purchased(session, user)
    assert await billing.trial_available(session, user)
    # Конфигурацию восстановили (сервер с inbound'ом): trial доступен.
    server = Server(name="srv-1", panel_url="http://panel.local:2053", username="a",
                    password="b", enabled=True)
    session.add(server)
    await session.flush()
    session.add(ServerInbound(server_id=server.id, inbound_id=1, protocol=Protocol.VLESS))
    await session.commit()
    trial = await _trial(session, user.id, MockPanelUpdater())
    assert trial.applied and not trial.subscription_purchased

    # Повтор той же заявки теперь принимает оплату: фиксируется confirmed_at.
    retried = await billing.retry_payment(session, payment.id, None, MockPanelUpdater())
    assert retried.applied and payment.status == PaymentStatus.APPLIED
    assert payment.confirmed_at is not None


@pytest.mark.parametrize(
    "status", [PaymentStatus.CREATED, PaymentStatus.WAITING_ADMIN, PaymentStatus.REJECTED]
)
async def test_unaccepted_statuses_are_not_accepted_payment(
    session, user, std_target, status  # noqa: F811
):
    payment = await payments.create_request(session, user.id, 175, 30)
    payment.status = status
    await session.commit()

    assert not await billing.subscription_already_purchased(session, user)
    assert await billing.trial_available(session, user)
    assert (await _trial(session, user.id, MockPanelUpdater())).applied


async def test_rejected_after_failure_releases_trial(session, user, vpn_client):
    """Администратор отклонил заявку после сбоя: оплата не принята (существующая семантика).

    Отдельного механизма возврата в коде нет; ``reject_payment`` из ``failed`` — единственный
    способ снять принятие, и ``confirmed_at`` его не удерживает.
    """
    payment = await _accepted_failed(session, user, vpn_client)
    assert await billing.subscription_already_purchased(session, user)

    await billing.reject_payment(session, payment.id, None, comment="возврат")

    assert payment.status == PaymentStatus.REJECTED and payment.confirmed_at is not None
    assert not await billing.subscription_already_purchased(session, user)
    assert (await _trial(session, user.id, MockPanelUpdater())).applied


@pytest.mark.parametrize("status", list(PaymentStatus))
async def test_traffic_purchase_is_never_a_subscription(
    session, user, std_target, status  # noqa: F811
):
    session.add(
        PaymentRequest(
            user_id=user.id, amount=300, period_days=0, kind=PAYMENT_KIND_TRAFFIC,
            traffic_bytes=25 * GIB, status=status, payment_code=f"TR-{status.value}",
            confirmed_at=utcnow(), target_expires_at=utcnow(),
        )
    )
    await session.commit()

    assert not await billing.subscription_already_purchased(session, user)
    assert await user_handlers._trial_available(session, user)
    assert (await _trial(session, user.id, MockPanelUpdater())).applied


# --- Идемпотентный повтор и устойчивый учёт --------------------------------------------


async def test_successful_retry_of_accepted_failed_is_idempotent(
    session, user, vpn_client, service_on, wl_server  # noqa: F811
):
    panel = MockPanelUpdater()
    payment = await _accepted_failed(session, user, vpn_client)
    target = payment.target_expires_at
    grants = await session.scalar(
        select(func.count()).select_from(WhitelistLedger)
        .where(WhitelistLedger.user_id == user.id)
    )
    assert not (await _trial(session, user.id, panel)).applied

    first = await billing.retry_payment(session, payment.id, None, panel)
    second = await billing.retry_payment(session, payment.id, None, panel)
    await session.refresh(vpn_client)

    assert first.applied and not first.already_applied
    assert payment.status == PaymentStatus.APPLIED
    assert second.already_applied and not second.applied
    # Срок равен сохранённому target и не растёт при повторе; trial его не прибавил.
    assert vpn_client.expires_at.replace(tzinfo=None) == target.replace(tzinfo=None)
    # Пакет услуги выдан один раз: повтор его не дублирует.
    assert await session.scalar(
        select(func.count()).select_from(WhitelistLedger)
        .where(WhitelistLedger.user_id == user.id)
    ) == grants
    [purchase] = await _purchases(session)
    assert purchase.payment_request_id == payment.id
    assert not await billing.trial_available(session, user)
    assert (await _trial(session, user.id, panel)).subscription_purchased


async def test_accepted_failed_request_blocks_reset_and_trial_survives_it(
    session, user, vpn_client
):
    """``failed`` блокирует сброс, поэтому записи в subscription_purchases до применения нет.

    Пока заявка не применена, trial закрывает она сама; после повтора факт оплаты
    попадает в устойчивую запись и переживает сброс.
    """
    telegram_id = user.telegram_id
    payment = await _accepted_failed(session, user, vpn_client)

    callback = await _reset(session, user)
    assert callback.alerts[-1] == texts.reset_blocked(ResetBlock.OPEN_PAYMENT)
    assert await session.get(PaymentRequest, payment.id) is not None
    assert await _purchases(session) == []

    panel = MockPanelUpdater()
    assert (await billing.retry_payment(session, payment.id, None, panel)).applied
    callback = await _reset(session, user)
    assert callback.alerts[-1] == "Данные сброшены"
    fresh = await _fresh(session, telegram_id)

    assert [p.telegram_id for p in await _purchases(session)] == [telegram_id]
    assert not await user_handlers._trial_available(session, fresh)
    result = await _trial(session, fresh.id, panel)
    assert not result.applied and result.subscription_purchased


async def _legacy_client(maker, user_id: int, *, enabled: bool) -> int:
    """Клиент с одним назначением на сервер без inbound'ов (режим без целей)."""
    async with maker() as session:
        client = VpnClient(user_id=user_id, display_name="c", email="c@local",
                           expires_at=None, is_active=False)
        session.add(client)
        await session.flush()
        session.add(ClientServerMapping(
            vpn_client_id=client.id, server_id=await session.scalar(select(Server.id)),
            inbound_id=1, protocol=Protocol.VLESS, client_uuid="u", email="c@local",
            enabled=enabled,
        ))
        await session.commit()
        return client.id


# --- Гонка подтверждения оплаты и trial ---------------------------------------------------


async def test_confirmation_failing_after_acceptance_racing_trial_blocks_trial(
    tmp_path, monkeypatch
):
    engine, maker, user_id = await _file_db(tmp_path, targets=False)
    client_id = await _legacy_client(maker, user_id, enabled=False)
    async with maker() as session:
        payment = await payments.create_request(session, user_id, 175, 30)
        payment.status = PaymentStatus.WAITING_ADMIN
        await session.commit()
        payment_id = payment.id

    # Подтверждение держит блокировку пользователя до принятия и падает в ``failed``.
    original = whitelist.grant_for_subscription_payment

    async def slow(*args, **kwargs):
        await asyncio.sleep(0.1)
        return await original(*args, **kwargs)

    monkeypatch.setattr(billing.whitelist, "grant_for_subscription_payment", slow)
    panel = MockPanelUpdater()

    async def confirm():
        async with maker() as session:
            return await billing.confirm_payment(session, payment_id, None, panel)

    async def grant():
        async with maker() as session:
            return await _trial(session, user_id, panel)

    try:
        async with maker() as session:
            assert await billing.trial_available(session, await session.get(User, user_id))
        confirming = asyncio.create_task(confirm())
        await asyncio.sleep(0.02)
        trial = await grant()
        confirmed = await confirming
        # Конфигурацию восстановили: trial всё равно закрыт принятой оплатой.
        async with maker() as session:
            await _set_mappings(session, client_id, True)
            again = await _trial(session, user_id, panel)
            stored = await session.get(PaymentRequest, payment_id)
            grants = await session.scalar(select(func.count()).select_from(TrialGrant))
            expires = await session.scalar(
                select(VpnClient.expires_at).where(VpnClient.id == client_id)
            )
    finally:
        await engine.dispose()

    assert not confirmed.applied and stored.status == PaymentStatus.FAILED
    assert stored.confirmed_at is not None
    assert not trial.applied and trial.subscription_purchased
    assert not again.applied and again.subscription_purchased
    assert grants == 0 and expires is None
    assert panel.provisioned == [] and panel.calls == []


async def test_trial_before_confirmation_is_the_allowed_order_even_if_payment_fails(
    tmp_path,
):
    """Trial выдан до принятия оплаты; последующий сбой применения его не отменяет."""
    engine, maker, user_id = await _file_db(tmp_path, targets=False)
    client_id = await _legacy_client(maker, user_id, enabled=True)
    panel = MockPanelUpdater()
    try:
        async with maker() as session:
            assert (await _trial(session, user_id, panel)).applied
            payment = await payments.create_request(session, user_id, 175, 30)
            await _set_mappings(session, client_id, False)
            result = await billing.confirm_payment(session, payment.id, None, panel)
            grants = await session.scalar(select(func.count()).select_from(TrialGrant))
    finally:
        await engine.dispose()

    assert not result.applied and payment.status == PaymentStatus.FAILED
    assert payment.confirmed_at is not None
    assert grants == 1

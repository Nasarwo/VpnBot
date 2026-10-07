"""Оплата подписки закрывает trial по Telegram ID и после сброса бота.

Сброс удаляет ``User`` вместе с заявками; факт оплаты хранится в
``subscription_purchases`` и учитывается ``grant_trial`` для нового ``User``.
"""
from __future__ import annotations

from datetime import timedelta
from weakref import WeakValueDictionary

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.bot import texts, user_handlers
from app.db.enums import PaymentStatus, UserRole
from app.db.models import (
    PAYMENT_KIND_TRAFFIC,
    ClientServerMapping,
    PaymentRequest,
    SubscriptionPurchase,
    TrialGrant,
    User,
    VpnClient,
    WebAccount,
)
from app.services import billing, operation_lock, payments
from app.services.panel_updater import MockPanelUpdater
from tests.conftest import utcnow
from tests.test_trial_reset import _file_db, _fresh, bridge  # noqa: F401
from tests.test_trial_subscription_rule import _old_trial_button
from tests.test_user_reset import _reset
from tests.test_whitelist import _buy, _pay, service_on, std_target, wl_server  # noqa: F401

DONE = "Данные сброшены"


async def _trial(session, user_id, panel):
    return await billing.grant_trial(session, user_id, panel, period_days=3)


async def _purchases(session) -> list[SubscriptionPurchase]:
    return (
        await session.scalars(
            select(SubscriptionPurchase).execution_options(populate_existing=True)
        )
    ).all()


async def _paid_and_reset(session, user) -> tuple[User, PaymentRequest]:
    """Оплата подписки без trial → настоящий обработчик сброса → новый User."""
    telegram_id = user.telegram_id
    payment, _ = await _pay(session, user, MockPanelUpdater())
    assert not user.trial_used
    callback = await _reset(session, user)
    assert callback.alerts[-1] == DONE
    fresh = await _fresh(session, telegram_id)
    assert fresh.trial_used is False
    assert await session.get(PaymentRequest, payment.id) is None  # история удалена
    return fresh, payment


async def test_paid_subscription_then_reset_refuses_trial(
    session, user, std_target, monkeypatch  # noqa: F811
):
    old_id = user.id
    fresh, payment = await _paid_and_reset(session, user)
    panel = MockPanelUpdater()

    assert not await user_handlers._trial_available(session, fresh)
    result = await _trial(session, fresh.id, panel)
    callback = await _old_trial_button(session, fresh, panel, monkeypatch)

    assert not result.applied and result.subscription_purchased
    assert not result.already_used
    assert callback.message.edits == [texts.trial_subscription_purchased()]
    assert panel.provisioned == [] and panel.calls == []
    assert await session.scalar(select(VpnClient).where(VpnClient.user_id == fresh.id)) is None
    assert await session.scalar(select(TrialGrant)) is None
    [purchase] = await _purchases(session)
    assert (purchase.telegram_id, purchase.user_id, purchase.payment_request_id) == (
        fresh.telegram_id, old_id, payment.id
    )


async def test_repeated_resets_keep_refusal(session, user, std_target):  # noqa: F811
    telegram_id = user.telegram_id
    fresh, _ = await _paid_and_reset(session, user)
    for _ in range(2):
        assert (await _reset(session, fresh)).alerts[-1] == DONE
        fresh = await _fresh(session, telegram_id)

    result = await _trial(session, fresh.id, MockPanelUpdater())

    assert not result.applied and result.subscription_purchased
    assert len(await _purchases(session)) == 1


async def test_refusal_after_paid_reset_survives_process_restart(tmp_path, monkeypatch):
    engine, maker, user_id = await _file_db(tmp_path, targets=True)
    async with maker() as session:
        await _pay(session, await session.get(User, user_id), MockPanelUpdater())
        callback = await _reset(session, await session.get(User, user_id))
        assert callback.alerts[-1] == DONE
    await engine.dispose()

    # Новый процесс: пустые in-process блокировки, новый движок и сессия.
    monkeypatch.setattr(operation_lock, "_locks", WeakValueDictionary())
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'bot.sqlite3'}")
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    panel = MockPanelUpdater()
    try:
        async with maker() as session:
            fresh = await _fresh(session, 4242)
            assert not await user_handlers._trial_available(session, fresh)
            result = await _trial(session, fresh.id, panel)
    finally:
        await engine.dispose()

    assert not result.applied and result.subscription_purchased
    assert panel.provisioned == []


async def test_other_telegram_id_still_gets_trial(session, user, std_target):  # noqa: F811
    await _paid_and_reset(session, user)
    other = User(telegram_id=654321, username="other", role=UserRole.USER)
    session.add(other)
    await session.commit()
    assert await user_handlers._trial_available(session, other)

    result = await _trial(session, other.id, MockPanelUpdater())

    assert result.applied
    assert [p.telegram_id for p in await _purchases(session)] == [user.telegram_id]


async def test_site_linked_after_paid_reset_cannot_take_trial(
    session, user, std_target, bridge  # noqa: F811
):
    call, panel = bridge
    fresh, _ = await _paid_and_reset(session, user)
    account = WebAccount(email="paid@example.com", password_hash="x", verified=True,
                         user_id=fresh.id)
    session.add(account)
    await session.commit()

    status, profile = await call("profile", account.id)
    assert status == 200 and profile["trial_available"] is False
    status, _ = await call("trial", account.id)

    assert status == 409
    assert panel.provisioned == []


# --- Что не считается оплатой подписки --------------------------------------------


async def test_traffic_purchase_is_not_recorded_as_subscription(
    session, user, vpn_client, service_on, wl_server  # noqa: F811
):
    """Доступ без оплаты подписки (привязанная подписка) и покупка трафика."""
    vpn_client.expires_at = utcnow() + timedelta(days=10)
    vpn_client.is_active = True
    await session.commit()
    panel = MockPanelUpdater()
    payment, result = await _buy(session, user, panel, 25)
    assert result.applied and payment.kind == PAYMENT_KIND_TRAFFIC
    assert payment.status == PaymentStatus.APPLIED

    assert await _purchases(session) == []
    assert await user_handlers._trial_available(session, user)
    assert (await _trial(session, user.id, panel)).applied


async def test_rejected_request_then_reset_still_allows_trial(
    session, user, std_target  # noqa: F811
):
    telegram_id = user.telegram_id
    payment = await payments.create_request(session, user.id, 175, 30)
    await billing.reject_payment(session, payment.id, None)
    assert (await _reset(session, user)).alerts[-1] == DONE
    fresh = await _fresh(session, telegram_id)

    assert await _purchases(session) == []
    assert (await _trial(session, fresh.id, MockPanelUpdater())).applied


async def test_waiting_request_is_not_recorded(session, user):
    payment = await payments.create_request(session, user.id, 175, 30)
    assert payment.status == PaymentStatus.WAITING_ADMIN

    assert await _purchases(session) == []
    assert not await billing.subscription_already_purchased(session, user)


async def _assert_failed_not_recorded(session, user, *, confirmed: bool) -> None:
    payment = await payments.create_request(session, user.id, 175, 30)
    result = await billing.confirm_payment(session, payment.id, None, MockPanelUpdater())
    assert not result.applied and payment.status == PaymentStatus.FAILED
    assert (payment.confirmed_at is not None) == confirmed

    # Устойчивая запись появляется только при применении; принятая ``failed``
    # закрывает trial самой заявкой (сброс при ней запрещён), непринятая — нет.
    assert await _purchases(session) == []
    assert await billing.subscription_already_purchased(session, user) is confirmed


async def test_failed_request_without_client_is_not_recorded(session, user):
    """Нет клиента и серверов: заявка падает до принятия оплаты и trial не закрывает."""
    await _assert_failed_not_recorded(session, user, confirmed=False)


async def test_failed_request_after_confirmation_is_not_recorded_durably(session, user, vpn_client):
    """Все назначения отключены: оплата принята, затем ``failed``; запись не нужна.

    Закрытие trial принятой ``failed`` — в ``test_trial_failed_payment.py``.
    """
    await session.execute(
        update(ClientServerMapping)
        .where(ClientServerMapping.vpn_client_id == vpn_client.id)
        .values(enabled=False)
    )
    await session.commit()
    await _assert_failed_not_recorded(session, user, confirmed=True)


# --- Порядок «trial, затем оплата» --------------------------------------------------


async def test_trial_then_payment_is_allowed_and_reset_keeps_both_facts(
    session, user, std_target  # noqa: F811
):
    telegram_id = user.telegram_id
    panel = MockPanelUpdater()
    trial = await _trial(session, user.id, panel)
    assert trial.applied
    payment, paid = await _pay(session, user, panel)

    # Оплаченные дни добавляются к trial.
    assert paid.new_expires_at - trial.new_expires_at > timedelta(days=29, hours=23)
    [purchase] = await _purchases(session)
    assert purchase.payment_request_id == payment.id

    assert (await _reset(session, user)).alerts[-1] == DONE
    fresh = await _fresh(session, telegram_id)
    again = await _trial(session, fresh.id, panel)
    assert not again.applied and again.already_used


async def test_first_payment_is_kept_on_later_payments(session, user, std_target):  # noqa: F811
    first, _ = await _pay(session, user, MockPanelUpdater())
    await _pay(session, user, MockPanelUpdater(), now=utcnow() + timedelta(days=1))

    [purchase] = await _purchases(session)
    assert purchase.payment_request_id == first.id


async def test_user_without_telegram_id_is_not_recorded(session, std_target):  # noqa: F811
    site_only = User(public_id="SITE0001", role=UserRole.USER, onboarding_done=True)
    session.add(site_only)
    await session.commit()

    await _pay(session, site_only, MockPanelUpdater())

    assert await _purchases(session) == []
    assert await billing.subscription_already_purchased(session, site_only)


@pytest.mark.parametrize("telegram_id", [None, 4242])
async def test_trial_available_requires_both_rules(session, telegram_id):
    user = User(telegram_id=telegram_id, role=UserRole.USER)
    session.add(user)
    await session.commit()
    assert await billing.trial_available(session, user)
    if telegram_id is not None:
        session.add(SubscriptionPurchase(telegram_id=telegram_id, user_id=999))
        await session.commit()
        assert not await billing.trial_available(session, user)

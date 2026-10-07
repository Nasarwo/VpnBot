"""Trial допустим только до первой подписки и проверяется в ``grant_trial``.

Кнопка бота и веб-мост лишь скрывают действие; старая кнопка или параллельный
запрос не должны добавлять бесплатные дни к оплаченной подписке.
"""
from __future__ import annotations

import asyncio
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.bot import texts, user_handlers
from app.config import Settings
from app.db.enums import PaymentStatus
from app.db.models import (
    PAYMENT_KIND_TRAFFIC,
    PaymentRequest,
    TrialGrant,
    User,
    VpnClient,
    WebAccount,
    WhitelistAccount,
    WhitelistLedger,
)
from app.services import billing, payments, web_bridge, whitelist
from app.services.panel_updater import MockPanelUpdater
from tests.conftest import utcnow
from tests.test_trial_reset import _file_db, _SlowPanel, bridge  # noqa: F401
from tests.test_whitelist import _pay, service_on, std_target, wl_server  # noqa: F401
from tests.test_whitelist_bot import FakeCallback

GIB = whitelist.GIB


async def _trial(session, user_id, panel):
    return await billing.grant_trial(session, user_id, panel, period_days=3)


async def _state(session, user_id, panel) -> dict:
    """Всё, что trial не должен менять после отказа."""
    balance = (
        await session.execute(
            select(WhitelistAccount.free_bytes, WhitelistAccount.paid_bytes)
            .where(WhitelistAccount.user_id == user_id)
            .execution_options(populate_existing=True)
        )
    ).first()
    return {
        "expires_at": await session.scalar(
            select(VpnClient.expires_at).where(VpnClient.user_id == user_id)
        ),
        "clients": await session.scalar(
            select(func.count()).select_from(VpnClient).where(VpnClient.user_id == user_id)
        ),
        "trial_used": await session.scalar(select(User.trial_used).where(User.id == user_id)),
        "grants": await session.scalar(select(func.count()).select_from(TrialGrant)),
        "balance": tuple(balance) if balance else None,
        "ledger": await session.scalar(
            select(func.count()).select_from(WhitelistLedger)
            .where(WhitelistLedger.user_id == user_id)
        ),
        "provisioned": list(panel.provisioned),
        "calls": list(panel.calls),
    }


async def _old_trial_button(session, user, panel, monkeypatch) -> FakeCallback:
    """Нажатие trial в старом сообщении, когда кнопка уже скрыта в новом меню."""
    monkeypatch.setattr(user_handlers, "build_updater", lambda **_: panel)

    async def no_sync(*_args, **_kwargs):
        return None

    monkeypatch.setattr(user_handlers, "trigger_configured_sync", no_sync)
    callback = FakeCallback()
    await user_handlers._activate_trial(callback, session, user, Settings())
    return callback


async def test_old_trial_button_after_paid_subscription_is_refused(
    session, user, std_target, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    await _pay(session, user, panel)
    assert not await user_handlers._trial_available(session, user)
    before = await _state(session, user.id, panel)
    assert before["balance"] == (10 * GIB, 0)  # пакет подписки; trial дал бы ещё 3 ГБ

    result = await _trial(session, user.id, panel)
    callback = await _old_trial_button(session, user, panel, monkeypatch)

    assert not result.applied and result.subscription_purchased
    assert not result.already_used and not result.no_client
    assert callback.message.edits == [texts.trial_subscription_purchased()]
    assert await _state(session, user.id, panel) == before


async def test_expired_paid_subscription_still_blocks_trial(
    session, user, std_target, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    await _pay(session, user, panel)
    client = await session.scalar(select(VpnClient).where(VpnClient.user_id == user.id))
    client.expires_at = utcnow() - timedelta(days=5)
    await session.commit()
    before = await _state(session, user.id, panel)

    assert not await user_handlers._trial_available(session, user)
    result = await _trial(session, user.id, panel)
    callback = await _old_trial_button(session, user, panel, monkeypatch)

    assert not result.applied and result.subscription_purchased
    assert callback.message.edits == [texts.trial_subscription_purchased()]
    assert await _state(session, user.id, panel) == before


async def test_new_user_gets_trial(session, user, std_target, service_on, wl_server):  # noqa: F811
    panel = MockPanelUpdater()
    assert await user_handlers._trial_available(session, user)

    result = await _trial(session, user.id, panel)

    assert result.applied and not result.subscription_purchased
    state = await _state(session, user.id, panel)
    assert state["trial_used"] and state["grants"] == 1
    assert state["balance"] == (3 * GIB, 0)
    assert not await user_handlers._trial_available(session, user)


@pytest.mark.parametrize(
    "status",
    [PaymentStatus.REJECTED, PaymentStatus.WAITING_ADMIN, PaymentStatus.CREATED],
)
async def test_unaccepted_subscription_request_does_not_block_trial(
    session, user, std_target, service_on, wl_server, status  # noqa: F811
):
    payment = await payments.create_request(session, user.id, 175, 30)
    payment.status = status
    await session.commit()
    assert await user_handlers._trial_available(session, user)

    result = await _trial(session, user.id, MockPanelUpdater())

    assert result.applied and not result.subscription_purchased


async def test_rejected_by_admin_request_does_not_block_trial(
    session, user, std_target, service_on, wl_server  # noqa: F811
):
    payment = await payments.create_request(session, user.id, 175, 30)
    payment.status = PaymentStatus.WAITING_ADMIN
    await session.commit()
    await billing.reject_payment(session, payment.id, None)
    assert payment.status == PaymentStatus.REJECTED

    assert (await _trial(session, user.id, MockPanelUpdater())).applied


@pytest.mark.parametrize("status", [PaymentStatus.APPLIED, PaymentStatus.CONFIRMED])
async def test_traffic_purchase_is_not_a_subscription(
    session, user, std_target, service_on, wl_server, status  # noqa: F811
):
    session.add(
        PaymentRequest(
            user_id=user.id, amount=300, period_days=0, kind=PAYMENT_KIND_TRAFFIC,
            traffic_bytes=25 * GIB, status=status, payment_code="TR-1",
        )
    )
    await session.commit()
    assert await user_handlers._trial_available(session, user)

    assert (await _trial(session, user.id, MockPanelUpdater())).applied


async def test_deleted_paid_subscription_blocks_trial_in_bot_and_site(
    session, user, std_target, service_on, wl_server, bridge  # noqa: F811
):
    """Клиент удалён, а оплата осталась: бот, сервис и сайт отказывают одинаково."""
    call, bridge_panel = bridge
    panel = MockPanelUpdater()
    await _pay(session, user, panel)
    client = await session.scalar(select(VpnClient).where(VpnClient.user_id == user.id))
    await session.delete(client)
    account = WebAccount(email="p@example.com", password_hash="x", verified=True,
                         user_id=user.id)
    session.add(account)
    await session.commit()
    assert await session.scalar(
        select(func.count()).select_from(VpnClient).where(VpnClient.user_id == user.id)
    ) == 0

    assert not await user_handlers._trial_available(session, user)
    status, profile = await call("profile", account.id)
    assert status == 200 and profile["trial_available"] is False
    status, _ = await call("trial", account.id)
    assert status == 409
    direct = await _trial(session, user.id, panel)

    assert direct.subscription_purchased and not direct.applied
    assert bridge_panel.provisioned == []
    assert await session.scalar(
        select(func.count()).select_from(VpnClient).where(VpnClient.user_id == user.id)
    ) == 0


async def test_site_trial_race_with_payment_maps_to_conflict(
    session, user, std_target, service_on, wl_server, bridge, monkeypatch  # noqa: F811
):
    """Оплата принята между проверкой моста и grant_trial: ответ 409, не 503."""
    call, bridge_panel = bridge
    await _pay(session, user, MockPanelUpdater())
    client = await session.scalar(select(VpnClient).where(VpnClient.user_id == user.id))
    await session.delete(client)
    account = WebAccount(email="r@example.com", password_hash="x", verified=True,
                         user_id=user.id)
    session.add(account)
    await session.commit()

    async def stale_ok(*_args):
        return True

    monkeypatch.setattr(web_bridge.billing, "trial_available", stale_ok)
    status, _ = await call("trial", account.id)

    assert status == 409
    assert bridge_panel.provisioned == []


# --- Конкуренция подтверждения оплаты и trial ------------------------------------


async def _waiting_payment(maker, user_id):
    async with maker() as session:
        payment = await payments.create_request(session, user_id, 175, 30)
        payment.status = PaymentStatus.WAITING_ADMIN
        await session.commit()
        return payment.id


async def _confirm(maker, payment_id, panel):
    async with maker() as session:
        return await billing.confirm_payment(session, payment_id, None, panel)


async def _grant(maker, user_id, panel):
    async with maker() as session:
        return await _trial(session, user_id, panel)


async def _final(maker, user_id):
    async with maker() as session:
        return (
            await session.scalar(
                select(VpnClient.expires_at).where(VpnClient.user_id == user_id)
            ),
            await session.scalar(select(func.count()).select_from(TrialGrant)),
            await session.scalar(select(PaymentRequest.status)),
        )


async def test_payment_confirmation_racing_trial_cannot_stack_free_days(tmp_path):
    engine, maker, user_id = await _file_db(tmp_path, targets=True)
    panel = _SlowPanel()
    try:
        payment_id = await _waiting_payment(maker, user_id)
        async with maker() as session:
            user = await session.get(User, user_id)
            assert await user_handlers._trial_available(session, user)  # кнопка видна

        confirm = asyncio.create_task(_confirm(maker, payment_id, panel))
        await asyncio.sleep(0.02)  # подтверждение уже держит блокировку пользователя
        trial = await _grant(maker, user_id, panel)
        confirmed = await confirm
        expires_at, grants, status = await _final(maker, user_id)
    finally:
        await engine.dispose()

    assert confirmed.applied and status == PaymentStatus.APPLIED
    assert not trial.applied and trial.subscription_purchased
    assert grants == 0
    # Срок равен оплаченным 30 дням без добавки trial.
    assert expires_at.replace(tzinfo=None) - utcnow().replace(tzinfo=None) < timedelta(
        days=30, minutes=1
    )
    assert len(panel.provisioned) == 1


async def test_trial_before_payment_confirmation_is_the_allowed_order(tmp_path):
    engine, maker, user_id = await _file_db(tmp_path, targets=True)
    panel = _SlowPanel()
    try:
        payment_id = await _waiting_payment(maker, user_id)
        trial_task = asyncio.create_task(_grant(maker, user_id, panel))
        await asyncio.sleep(0.02)
        confirmed = await _confirm(maker, payment_id, panel)
        trial = await trial_task
        expires_at, grants, status = await _final(maker, user_id)
    finally:
        await engine.dispose()

    assert trial.applied and confirmed.applied
    assert grants == 1 and status == PaymentStatus.APPLIED
    # Trial был до первой подписки, поэтому его дни складываются с оплаченными.
    assert expires_at.replace(tzinfo=None) - utcnow().replace(tzinfo=None) > timedelta(
        days=32, hours=23
    )

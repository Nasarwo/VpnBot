from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import keyboards, texts, user_handlers
from app.bot.callbacks import MenuCallback
from app.config import Settings
from app.db.enums import BindRequestStatus, PaymentStatus, UserRole
from app.db.models import (
    BindRequest,
    PaymentRequest,
    TrafficPackage,
    User,
    VpnClient,
    WebAccount,
    WebLinkRequest,
    WhitelistLedger,
)
from app.db.repositories import UserRepository, VpnClientRepository
from app.services import billing, payments, whitelist
from app.services.panel_updater import MockPanelUpdater
from app.services.user_reset import ResetBlock
from tests.test_whitelist import _buy, _pay, service_on, wl_server  # noqa: F401
from tests.test_whitelist_bot import FakeCallback, FakeState


def _all_buttons(markup):
    return [btn for row in markup.inline_keyboard for btn in row]


def test_reset_confirm_keyboard():
    buttons = _all_buttons(keyboards.reset_bot_confirm_keyboard())
    assert buttons[0].text == texts.BTN_RESET_YES
    assert buttons[0].style == "danger"
    assert MenuCallback.unpack(buttons[0].callback_data).action == "reset_yes"
    assert buttons[1].text == texts.BTN_CANCEL
    assert MenuCallback.unpack(buttons[1].callback_data).action == "home"


async def test_delete_user_removes_related_data(session: AsyncSession, user: User):
    user.onboarding_done = True
    user.trial_used = True
    user.public_id = "ABCD1234"
    session.add(
        VpnClient(
            user_id=user.id,
            display_name="c1",
            email="u@local",
            is_active=True,
        )
    )
    session.add(
        PaymentRequest(
            user_id=user.id,
            payment_code="PAY1",
            amount=100.0,
            period_days=30,
            status=PaymentStatus.CONFIRMED,
        )
    )
    session.add(
        BindRequest(
            user_id=user.id,
            request_code="BIND1",
            subscription_link="https://example.com/sub/x",
            public_id="x",
        )
    )
    await session.commit()
    telegram_id = user.telegram_id

    repo = UserRepository(session)
    await repo.delete_user(user)
    await session.commit()

    assert await repo.get_by_telegram_id(telegram_id) is None
    assert (await session.execute(select(VpnClient))).scalars().all() == []
    assert (await session.execute(select(PaymentRequest))).scalars().all() == []
    assert (await session.execute(select(BindRequest))).scalars().all() == []


async def test_get_or_create_after_delete_starts_fresh(session: AsyncSession):
    old = User(
        telegram_id=777,
        username="old",
        first_name="Old",
        role=UserRole.USER,
        onboarding_done=True,
        trial_used=True,
        public_id="OLDID111",
    )
    session.add(old)
    await session.flush()
    session.add(
        VpnClient(
            user_id=old.id,
            display_name="c",
            email="e@local",
            is_active=False,
        )
    )
    await session.commit()

    repo = UserRepository(session)
    await repo.delete_user(old)
    await session.commit()

    new_user, created = await repo.get_or_create(
        telegram_id=777,
        username="old",
        first_name="Old",
    )
    await session.commit()

    assert created is True
    assert new_user.public_id != "OLDID111"
    assert new_user.onboarding_done is False
    assert new_user.trial_used is False
    assert await VpnClientRepository(session).get_for_user(new_user.id) is None
    assert await repo.get_by_telegram_id(777) is new_user


# --- Сброс и финансовые обязательства -------------------------------------------

GIB = whitelist.GIB


async def _reset(session, user) -> FakeCallback:
    callback = FakeCallback()
    await user_handlers._reset_bot_user(callback, session, user, Settings(), FakeState())
    return callback


async def _purchase_during_outage(session, user, wl_server):  # noqa: F811
    panel = MockPanelUpdater()
    await _pay(session, user, panel)
    panel.read_fail_server_ids.add(wl_server.id)
    payment, result = await _buy(session, user, panel, 25)
    assert result.applied and result.whitelist_pending
    return payment


async def _assert_purchase_kept(session, user_id, payment_id, status):
    session.expire_all()
    assert await session.get(User, user_id) is not None
    payment = await session.get(PaymentRequest, payment_id)
    assert payment is not None and payment.status == PaymentStatus.APPLIED
    event = await session.scalar(
        select(WhitelistLedger).where(WhitelistLedger.payment_request_id == payment_id)
    )
    assert event is not None
    assert (event.kind, event.status, event.paid_delta) == ("purchase", status, 25 * GIB)


@pytest.mark.parametrize("status", ["pending", "uncertain"])
async def test_reset_keeps_purchase_awaiting_reconciliation(
    session, user, vpn_client, service_on, wl_server, status  # noqa: F811
):
    payment = await _purchase_during_outage(session, user, wl_server)
    event = await session.scalar(
        select(WhitelistLedger).where(WhitelistLedger.payment_request_id == payment.id)
    )
    event.status = status
    await session.commit()
    assert (await whitelist.get_account(session, user.id)).paid_bytes == 0

    callback = await _reset(session, user)

    assert callback.alerts[-1] == texts.reset_blocked(ResetBlock.PENDING_CREDIT)
    assert callback.message.edits == []
    await _assert_purchase_kept(session, user.id, payment.id, status)


async def test_reset_keeps_pending_paid_subscription_grant(
    session, user, vpn_client, service_on, wl_server  # noqa: F811
):
    panel = MockPanelUpdater()
    await _pay(session, user, panel)
    panel.read_fail_server_ids.add(wl_server.id)
    payment, result = await _pay(session, user, panel)
    assert result.whitelist_pending
    assert await whitelist.list_open_events(session, user.id)

    callback = await _reset(session, user)

    assert callback.alerts[-1] == texts.reset_blocked(ResetBlock.PENDING_CREDIT)
    assert await session.get(PaymentRequest, payment.id) is not None
    assert await whitelist.list_open_events(session, user.id)


async def test_reset_refused_with_paid_traffic_balance(
    session, user, vpn_client, service_on, wl_server  # noqa: F811
):
    panel = MockPanelUpdater()
    await _pay(session, user, panel)
    payment, _ = await _buy(session, user, panel, 25)
    assert (await whitelist.get_account(session, user.id)).paid_bytes == 25 * GIB

    callback = await _reset(session, user)

    assert callback.alerts[-1] == texts.reset_blocked(ResetBlock.PAID_TRAFFIC)
    await _assert_purchase_kept(session, user.id, payment.id, "settled")


async def test_reset_refused_with_open_payment_request(
    session, user, vpn_client, service_on, wl_server  # noqa: F811
):
    panel = MockPanelUpdater()
    await _pay(session, user, panel)
    package = await session.scalar(
        select(TrafficPackage).where(
            TrafficPackage.traffic_bytes == 25 * GIB
        )
    )
    request = await payments.create_traffic_request(session, user.id, package.id)
    assert request.status == PaymentStatus.WAITING_ADMIN

    callback = await _reset(session, user)

    assert callback.alerts[-1] == texts.reset_blocked(ResetBlock.OPEN_PAYMENT)
    assert await session.get(PaymentRequest, request.id) is not None
    # Заявку по-прежнему можно подтвердить: начисление не теряется.
    result = await billing.confirm_payment(session, request.id, None, panel)
    assert result.applied and result.traffic_bytes == 25 * GIB


async def test_reset_refused_with_waiting_bind_request(session, user):
    session.add(
        BindRequest(
            user_id=user.id,
            request_code="BIND1",
            subscription_link="https://example.com/sub/x",
            public_id="x",
            status=BindRequestStatus.WAITING_ADMIN,
        )
    )
    await session.commit()

    callback = await _reset(session, user)

    assert callback.alerts[-1] == texts.reset_blocked(ResetBlock.OPEN_BIND)
    assert await session.get(User, user.id) is not None


async def test_reset_refused_with_pending_web_link(session, user):
    account = WebAccount(email="u@example.com", password_hash="x", verified=True)
    session.add(account)
    await session.flush()
    session.add(WebLinkRequest(account_id=account.id, target_user_id=user.id))
    await session.commit()

    callback = await _reset(session, user)

    assert callback.alerts[-1] == texts.reset_blocked(ResetBlock.WEB_LINK)
    assert await session.get(User, user.id) is not None


async def test_reset_refused_for_linked_web_account(session, user):
    session.add(WebAccount(email="u@example.com", password_hash="x", user_id=user.id))
    await session.commit()

    callback = await _reset(session, user)

    assert callback.alerts[-1] == texts.reset_blocked(ResetBlock.WEB_LINKED)
    assert await session.get(User, user.id) is not None


async def test_reset_without_financial_obligations_still_works(
    session, user, vpn_client, service_on, wl_server  # noqa: F811
):
    panel = MockPanelUpdater()
    payment, _ = await _pay(session, user, panel)
    account = await whitelist.get_account(session, user.id)
    assert account.paid_bytes == 0 and account.free_bytes == 10 * GIB
    assert await whitelist.list_open_events(session, user.id) == []
    old_id, telegram_id = user.id, user.telegram_id

    callback = await _reset(session, user)

    assert callback.alerts[-1] == "Данные сброшены"
    assert callback.message.edits[-1] == texts.onboarding_legacy_question()
    session.expire_all()
    fresh = await UserRepository(session).get_by_telegram_id(telegram_id)
    assert fresh is not None and fresh.onboarding_done is False
    assert await session.get(User, old_id) in (None, fresh)
    assert await session.get(PaymentRequest, payment.id) is None
    assert (await session.execute(select(WhitelistLedger))).scalars().all() == []

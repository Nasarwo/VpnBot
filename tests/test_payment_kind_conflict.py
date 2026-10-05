"""D-1: заявку с отправленной квитанцией нельзя превратить в заявку другого вида."""
from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.bot import admin_handlers, user_handlers
from app.bot.callbacks import PaymentCallback, PlanCallback, WhitelistCallback
from app.bot.states import ProofStates
from app.config import Settings
from app.db.enums import AttachmentType, PaymentStatus
from app.db.models import (
    PAYMENT_KIND_SUBSCRIPTION,
    PAYMENT_KIND_TRAFFIC,
    PaymentAttachment,
    PaymentRequest,
    TrafficPackage,
)
from app.services import billing, payments, whitelist
from app.services.panel_updater import MockPanelUpdater
from tests.test_whitelist import service_on, wl_server  # noqa: F401
from tests.test_whitelist_bot import GIB, FakeCallback, FakeState

SETTINGS = Settings(payment_details_text="Карта 0000")


@pytest.fixture
def panel(monkeypatch) -> MockPanelUpdater:
    panel = MockPanelUpdater()
    monkeypatch.setattr(user_handlers, "build_updater", lambda **_: panel)
    monkeypatch.setattr(admin_handlers, "_get_updater", lambda _settings: panel)
    return panel


@pytest.fixture
async def active_user(session, user, vpn_client, service_on, wl_server, panel):  # noqa: F811
    """Пользователь с оплаченной подпиской: покупка трафика доступна."""
    first = await payments.create_request(session, user.id, 175, 30)
    await billing.confirm_payment(session, first.id, None, panel)
    return user


async def _package(session, gib: int = 10) -> TrafficPackage:
    return await session.scalar(
        select(TrafficPackage).where(TrafficPackage.traffic_bytes == gib * GIB)
    )


async def _traffic_with_proof(session, user) -> PaymentRequest:
    package = await _package(session)
    request = await payments.create_traffic_request(session, user.id, package.id)
    await payments.attach_proof(session, request.id, AttachmentType.TEXT, caption="Оплатил")
    return request


async def _subscription_with_proof(session, user, amount=175, days=30) -> PaymentRequest:
    request = await payments.create_request(session, user.id, amount, days)
    await payments.attach_proof(session, request.id, AttachmentType.TEXT, caption="Оплатил")
    return request


async def _snapshot(session, payment_id: int) -> dict:
    p = await session.get(PaymentRequest, payment_id)
    await session.refresh(p)
    attachments = await session.scalar(
        select(func.count()).select_from(PaymentAttachment)
        .where(PaymentAttachment.payment_request_id == payment_id)
    )
    return {
        "kind": p.kind, "amount": str(p.amount), "period_days": p.period_days,
        "traffic_bytes": p.traffic_bytes, "package_id": p.traffic_package_id,
        "title": p.traffic_package_title, "status": p.status,
        "code": p.payment_code, "attachments": attachments,
    }


async def _open_count(session, user_id: int) -> int:
    return await session.scalar(
        select(func.count()).select_from(PaymentRequest).where(
            PaymentRequest.user_id == user_id,
            PaymentRequest.status.in_([PaymentStatus.CREATED, PaymentStatus.WAITING_ADMIN]),
        )
    )


# --- Сервисный слой ---------------------------------------------------------------


async def test_subscription_choice_is_refused_while_traffic_proof_pending(
    session, active_user
):
    request = await _traffic_with_proof(session, active_user)
    before = await _snapshot(session, request.id)

    with pytest.raises(payments.PendingRequestExists) as exc:
        await payments.create_request(session, active_user.id, 175, 30)

    assert exc.value.payment.id == request.id
    assert await _snapshot(session, request.id) == before
    assert before["kind"] == PAYMENT_KIND_TRAFFIC and before["attachments"] == 1
    assert await _open_count(session, active_user.id) == 1


async def test_traffic_choice_is_refused_while_subscription_proof_pending(
    session, active_user
):
    request = await _subscription_with_proof(session, active_user)
    before = await _snapshot(session, request.id)
    package = await _package(session, 25)

    with pytest.raises(payments.PendingRequestExists) as exc:
        await payments.create_traffic_request(session, active_user.id, package.id)

    assert exc.value.payment.id == request.id
    assert await _snapshot(session, request.id) == before
    assert before["kind"] == PAYMENT_KIND_SUBSCRIPTION
    assert await _open_count(session, active_user.id) == 1


async def test_same_kind_repeat_returns_pending_request_unchanged(session, active_user):
    request = await _subscription_with_proof(session, active_user)
    before = await _snapshot(session, request.id)

    repeated = await payments.create_request(session, active_user.id, 175, 30)

    assert repeated.id == request.id
    assert await _snapshot(session, request.id) == before
    assert await _open_count(session, active_user.id) == 1


async def test_kind_switch_without_proof_still_converts_single_request(session, active_user):
    package = await _package(session)
    traffic = await payments.create_traffic_request(session, active_user.id, package.id)

    subscription = await payments.create_request(session, active_user.id, 175, 30)
    assert subscription.id == traffic.id
    after = await _snapshot(session, traffic.id)
    assert after["kind"] == PAYMENT_KIND_SUBSCRIPTION
    assert after["traffic_bytes"] is None and after["package_id"] is None
    assert after["amount"] == "175.00" and after["period_days"] == 30

    back = await payments.create_traffic_request(session, active_user.id, package.id)
    assert back.id == traffic.id
    after = await _snapshot(session, traffic.id)
    assert after["kind"] == PAYMENT_KIND_TRAFFIC
    assert after["traffic_bytes"] == 10 * GIB and after["period_days"] == 0
    assert await _open_count(session, active_user.id) == 1


# --- Обработчики бота ----------------------------------------------------------------


async def test_select_plan_reports_pending_traffic_request(session, active_user):
    request = await _traffic_with_proof(session, active_user)
    before = await _snapshot(session, request.id)
    state = FakeState()
    await state.set_state(ProofStates.waiting_proof)
    callback = FakeCallback()

    await user_handlers.select_plan(
        callback, PlanCallback(code="1m"), session, active_user, SETTINGS, state
    )

    assert callback.message.edits == []  # «Заявка создана» не показывается
    alert = callback.alerts[-1]
    assert request.payment_code in alert and "на проверке" in alert
    assert "трафик" in alert.lower() and "10 ГБ" in alert
    assert state.state is None  # квитанции больше не ждём
    assert await _snapshot(session, request.id) == before


async def test_whitelist_buy_reports_pending_subscription_request(session, active_user):
    request = await _subscription_with_proof(session, active_user)
    before = await _snapshot(session, request.id)
    package = await _package(session, 25)
    state = FakeState()
    callback = FakeCallback()

    await user_handlers.whitelist_menu(
        callback, WhitelistCallback(action="buy", value=package.id),
        session, active_user, SETTINGS, state,
    )

    assert callback.message.edits == []
    alert = callback.alerts[-1]
    assert request.payment_code in alert and "на проверке" in alert
    assert "продление" in alert.lower() and "30 дней" in alert
    assert state.state is None
    assert await _snapshot(session, request.id) == before


async def test_select_plan_repeat_of_same_kind_keeps_request_and_waits_for_proof(
    session, active_user
):
    request = await _subscription_with_proof(session, active_user)
    before = await _snapshot(session, request.id)
    state = FakeState()
    callback = FakeCallback()

    await user_handlers.select_plan(
        callback, PlanCallback(code="1m"), session, active_user, SETTINGS, state
    )

    assert request.payment_code in callback.message.edits[-1]
    assert await _snapshot(session, request.id) == before
    assert await _open_count(session, active_user.id) == 1


async def test_select_plan_without_proof_still_creates_and_switches(session, active_user):
    package = await _package(session)
    traffic = await payments.create_traffic_request(session, active_user.id, package.id)
    state = FakeState()
    callback = FakeCallback()

    await user_handlers.select_plan(
        callback, PlanCallback(code="1m"), session, active_user, SETTINGS, state
    )

    assert "создана" in callback.message.edits[-1]
    assert state.state == ProofStates.waiting_proof
    assert (await _snapshot(session, traffic.id))["kind"] == PAYMENT_KIND_SUBSCRIPTION
    assert await _open_count(session, active_user.id) == 1


# --- Начисление после подтверждения ----------------------------------------------------


async def test_conflicted_traffic_request_credits_traffic_once_and_no_subscription_time(
    session, active_user, admin, panel
):
    request = await _traffic_with_proof(session, active_user)
    from app.db.repositories import VpnClientRepository

    client = await VpnClientRepository(session).get_for_user(active_user.id)
    expires_before = client.expires_at.replace(tzinfo=None)
    paid_before = (await whitelist.get_account(session, active_user.id)).paid_bytes

    await user_handlers.select_plan(
        FakeCallback(), PlanCallback(code="1m"), session, active_user, SETTINGS, FakeState()
    )
    for _ in range(2):  # двойное нажатие администратора
        await admin_handlers.on_payment_action(
            FakeCallback(), PaymentCallback(action="confirm", payment_id=request.id),
            session, admin, SETTINGS,
        )

    client = await VpnClientRepository(session).get_for_user(active_user.id)
    await session.refresh(client)
    account = await whitelist.get_account(session, active_user.id)
    await session.refresh(account)
    assert account.paid_bytes == paid_before + 10 * GIB
    assert client.expires_at.replace(tzinfo=None) == expires_before
    assert (await _snapshot(session, request.id))["status"] == PaymentStatus.APPLIED


async def test_conflicted_subscription_request_extends_once_and_adds_no_traffic(
    session, active_user, admin, panel
):
    request = await _subscription_with_proof(session, active_user)
    from app.db.repositories import VpnClientRepository

    client = await VpnClientRepository(session).get_for_user(active_user.id)
    expires_before = client.expires_at.replace(tzinfo=None)
    paid_before = (await whitelist.get_account(session, active_user.id)).paid_bytes
    package = await _package(session, 25)

    await user_handlers.whitelist_menu(
        FakeCallback(), WhitelistCallback(action="buy", value=package.id),
        session, active_user, SETTINGS, FakeState(),
    )
    for _ in range(2):
        await admin_handlers.on_payment_action(
            FakeCallback(), PaymentCallback(action="confirm", payment_id=request.id),
            session, admin, SETTINGS,
        )

    client = await VpnClientRepository(session).get_for_user(active_user.id)
    await session.refresh(client)
    account = await whitelist.get_account(session, active_user.id)
    await session.refresh(account)
    assert (client.expires_at.replace(tzinfo=None) - expires_before).days == 30
    assert account.paid_bytes == paid_before  # купленного трафика не прибавилось

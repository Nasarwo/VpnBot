"""Статус заявки на покупку трафика следует за фактическим применением начисления."""
from __future__ import annotations

from sqlalchemy import select

from app.bot import admin_handlers, texts, user_handlers
from app.bot.callbacks import PaymentCallback, WhitelistCallback
from app.config import Settings
from app.db.models import PaymentRequest
from app.services import billing, whitelist
from app.services.panel_updater import MockPanelUpdater
from tests.test_whitelist import (  # noqa: F401
    EMAIL,
    _account,
    _buy,
    _ledger_count,
    _pay,
    service_on,
    wl_server,
)
from tests.test_whitelist_bot import FakeCallback, FakeState

GIB = whitelist.GIB
WAITING = "ожидается применение"
CREDITED = "трафик начислен"


def _down(working: MockPanelUpdater, server_id: int) -> MockPanelUpdater:
    """Недоступная панель с общим состоянием квот."""
    panel = MockPanelUpdater(fail_server_ids={server_id})
    panel.quota_clients = working.quota_clients
    return panel


async def _fresh(session, payment) -> PaymentRequest:
    await session.refresh(payment)
    return payment


async def _queue(session, user, panel) -> int:
    """Фоновая очередь: сбрасывает backoff, как по истечении next_sync_at."""
    account = await _account(session, user)
    account.next_sync_at = None
    await session.commit()
    return await whitelist.process_due(session, panel)


def _is_waiting(payment) -> bool:
    return WAITING in texts.payment_status_label(payment)


async def test_credit_during_outage_shows_waiting(
    session, user, vpn_client, service_on, wl_server  # noqa: F811
):
    working = MockPanelUpdater()
    await _pay(session, user, working)
    payment, result = await _buy(session, user, _down(working, wl_server.id), 25)
    assert result.applied and result.whitelist_pending
    payment = await _fresh(session, payment)
    assert _is_waiting(payment)
    assert WAITING in texts.admin_payment_card(payment, user)
    # Ожидание — не ошибка заявки: поле ошибки не используется для статуса.
    assert payment.last_error is None
    assert "Ошибка:" not in texts.admin_payment_card(payment, user)


async def test_successful_queue_clears_waiting(
    session, user, vpn_client, service_on, wl_server  # noqa: F811
):
    working = MockPanelUpdater()
    await _pay(session, user, working)
    payment, _ = await _buy(session, user, _down(working, wl_server.id), 25)
    assert _is_waiting(await _fresh(session, payment))
    assert await _queue(session, user, working) == 1
    payment = await _fresh(session, payment)
    assert not _is_waiting(payment)
    assert texts.payment_status_label(payment) == CREDITED
    assert "Ошибка:" not in texts.admin_payment_card(payment, user)
    assert working.quota_clients[(wl_server.id, EMAIL)].total_bytes == 35 * GIB


async def test_failed_retry_keeps_waiting(
    session, user, vpn_client, service_on, wl_server  # noqa: F811
):
    working = MockPanelUpdater()
    await _pay(session, user, working)
    down = _down(working, wl_server.id)
    payment, _ = await _buy(session, user, down, 25)
    assert await _queue(session, user, down) == 0
    assert _is_waiting(await _fresh(session, payment))
    # Повтор подтверждения администратором при недоступной панели.
    again = await billing.retry_payment(session, payment.id, None, down)
    assert again.already_applied
    assert _is_waiting(await _fresh(session, payment))
    assert await _ledger_count(session, user.id, "purchase") == 1


async def test_pending_event_keeps_waiting_until_usage_is_reconciled(
    session, user, vpn_client, service_on, wl_server  # noqa: F811
):
    """Запись квоты прошла, но расход не сверен: начисление ещё не учтено."""
    working = MockPanelUpdater()
    await _pay(session, user, working)
    payment, _ = await _buy(session, user, _down(working, wl_server.id), 25)
    working.read_fail_server_ids.add(wl_server.id)
    await _queue(session, user, working)
    assert _is_waiting(await _fresh(session, payment))
    working.read_fail_server_ids.clear()
    await _queue(session, user, working)
    assert not _is_waiting(await _fresh(session, payment))


async def test_multiple_purchases_and_old_retries_keep_statuses_independent(
    session, user, vpn_client, service_on, wl_server  # noqa: F811
):
    working = MockPanelUpdater()
    await _pay(session, user, working)
    down = _down(working, wl_server.id)
    first, _ = await _buy(session, user, down, 10)
    assert await _queue(session, user, working) == 1
    assert not _is_waiting(await _fresh(session, first))

    second, _ = await _buy(session, user, down, 25)
    assert _is_waiting(await _fresh(session, second))
    assert not _is_waiting(await _fresh(session, first))

    # Повтор давно применённой заявки при недоступной панели не возвращает ей
    # ожидание (версия desired выросла) и не снимает ожидание с новой.
    await billing.retry_payment(session, first.id, None, down)
    await billing.confirm_payment(session, first.id, None, down)
    assert not _is_waiting(await _fresh(session, first))
    assert _is_waiting(await _fresh(session, second))

    # Третья покупка при той же недоступности — свой статус.
    third, _ = await _buy(session, user, down, 10)
    assert _is_waiting(await _fresh(session, third))
    assert await _queue(session, user, working) == 1
    for payment in (first, second, third):
        assert not _is_waiting(await _fresh(session, payment))
    assert await _ledger_count(session, user.id, "purchase") == 3
    account = await _account(session, user)
    assert account.paid_bytes == 45 * GIB


async def test_applied_version_gates_each_payment_separately(
    session, user, vpn_client, service_on, wl_server  # noqa: F811
):
    """Применена версия между двумя заявками: ожидание снимается только с ранней."""
    working = MockPanelUpdater()
    await _pay(session, user, working)
    down = _down(working, wl_server.id)
    first, _ = await _buy(session, user, down, 10)
    second, _ = await _buy(session, user, down, 25)
    first, second = await _fresh(session, first), await _fresh(session, second)
    assert first.apply_pending_version < second.apply_pending_version
    account = await _account(session, user)
    # Закрываем события учёта, чтобы проверить только сравнение версий.
    for event in await whitelist.list_open_events(session, user.id):
        event.status = whitelist.EVENT_SETTLED
    account.applied_version = first.apply_pending_version
    await whitelist.release_applied_credits(session, account)
    await session.commit()
    assert not _is_waiting(await _fresh(session, first))
    assert _is_waiting(await _fresh(session, second))
    account.applied_version = second.apply_pending_version
    await whitelist.release_applied_credits(session, account)
    await session.commit()
    assert not _is_waiting(await _fresh(session, second))


async def test_other_payment_errors_are_not_cleared(
    session, user, vpn_client, service_on, wl_server  # noqa: F811
):
    working = MockPanelUpdater()
    await _pay(session, user, working)
    payment, _ = await _buy(session, user, _down(working, wl_server.id), 25)
    payment = await _fresh(session, payment)
    payment.last_error = "Иная ошибка заявки"
    await session.commit()
    await _queue(session, user, working)
    payment = await _fresh(session, payment)
    assert not _is_waiting(payment)
    assert payment.last_error == "Иная ошибка заявки"


async def test_repeat_confirmation_never_credits_twice(
    session, user, vpn_client, service_on, wl_server  # noqa: F811
):
    working = MockPanelUpdater()
    await _pay(session, user, working)
    down = _down(working, wl_server.id)
    payment, _ = await _buy(session, user, down, 25)
    for panel in (down, down, working, working):
        again = await billing.confirm_payment(session, payment.id, None, panel)
        assert again.already_applied and not again.applied
    await _queue(session, user, working)
    assert not _is_waiting(await _fresh(session, payment))
    assert await _ledger_count(session, user.id, "purchase") == 1
    account = await _account(session, user)
    assert account.paid_bytes == 25 * GIB
    assert working.quota_clients[(wl_server.id, EMAIL)].total_bytes == 35 * GIB


async def test_repeat_confirmation_with_working_panel_clears_waiting(
    session, user, vpn_client, service_on, wl_server  # noqa: F811
):
    working = MockPanelUpdater()
    await _pay(session, user, working)
    payment, _ = await _buy(session, user, _down(working, wl_server.id), 25)
    assert _is_waiting(await _fresh(session, payment))
    again = await billing.confirm_payment(session, payment.id, None, working)
    assert again.already_applied
    assert not _is_waiting(await _fresh(session, payment))
    assert (await _account(session, user)).paid_bytes == 25 * GIB


async def test_admin_and_user_screens_follow_application(
    session, user, admin, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    working = MockPanelUpdater()
    await _pay(session, user, working)
    down = _down(working, wl_server.id)
    monkeypatch.setattr(admin_handlers, "_get_updater", lambda _settings: down)
    monkeypatch.setattr(user_handlers, "build_updater", lambda **_: down)
    from app.services import payments

    package = await whitelist.list_packages(session)
    request = await payments.create_traffic_request(
        session, user.id, next(p for p in package if p.traffic_bytes == 25 * GIB).id
    )
    callback = FakeCallback()
    await admin_handlers.on_payment_action(
        callback, PaymentCallback(action="confirm", payment_id=request.id),
        session, admin, Settings(),
    )
    confirm_card = callback.message.edits[-1]
    assert "Применение на сервере ожидается" in confirm_card
    assert WAITING in confirm_card and "Ошибка:" not in confirm_card

    async def user_screen() -> str:
        screen_callback = FakeCallback()
        await user_handlers.whitelist_menu(
            screen_callback, WhitelistCallback(action="home"), session, user,
            Settings(), FakeState(),
        )
        return screen_callback.message.edits[-1]

    assert "Оплата сохранена" in await user_screen()
    history = texts.admin_history(
        list((await session.scalars(select(PaymentRequest))).all())
    )
    assert WAITING in history

    assert await _queue(session, user, working) == 1
    request = await _fresh(session, request)
    assert texts.payment_status_label(request) == CREDITED
    assert WAITING not in texts.admin_history(
        list((await session.scalars(select(PaymentRequest))).all())
    )
    assert "Оплата сохранена" not in await user_screen()
    # Карточка после повторного нажатия: уже применена, без ожидания.
    again = FakeCallback()
    await admin_handlers.on_payment_action(
        again, PaymentCallback(action="confirm", payment_id=request.id),
        session, admin, Settings(),
    )
    assert again.alerts[-1] == "Заявка уже применена ранее"
    assert WAITING not in texts.admin_payment_card(await _fresh(session, request), user)

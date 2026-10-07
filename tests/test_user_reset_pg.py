"""Сброс бота против подтверждения оплаты и привязки сайта на PostgreSQL.

Запуск: VPNBOT_TEST_PG_URL=postgresql+asyncpg://user@/db?host=/run/... pytest
База должна быть отдельной тестовой: схема пересоздаётся каждым тестом.
In-process asyncio.Lock подменяется (фикстура ``pg``), поэтому операции
сериализуются только advisory lock и блокировками строк PostgreSQL.
"""
from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.bot import texts, user_handlers
from app.config import Settings
from app.db.enums import AttachmentType, PaymentStatus
from app.db.models import (
    PaymentRequest,
    TrafficPackage,
    User,
    WebAccount,
    WebLinkRequest,
    WhitelistLedger,
)
from app.services import billing, payments, user_reset, web_bridge
from app.services.panel_updater import MockPanelUpdater
from app.services.user_reset import ResetBlock
from tests.test_whitelist_bot import FakeCallback, FakeState
from tests.test_whitelist_pg import GIB, PG_URL, SlowPanel, pg  # noqa: F401

pytestmark = pytest.mark.skipif(not PG_URL, reason="VPNBOT_TEST_PG_URL is not set")

DONE = "Данные сброшены"


def _pause_after_check(monkeypatch, delay=0.3):
    """Держит сброс между проверкой допуска и удалением (окно гонки)."""
    original = user_reset.find_reset_blocker
    entered = asyncio.Event()

    async def slow(session, user):
        reason = await original(session, user)
        entered.set()
        await asyncio.sleep(delay)
        return reason

    monkeypatch.setattr(user_reset, "find_reset_blocker", slow)
    return entered


async def _reset(maker, user_id) -> FakeCallback:
    async with maker() as session:
        user = await session.get(User, user_id)
        callback = FakeCallback()
        await user_handlers._reset_bot_user(
            callback, session, user, Settings(), FakeState()
        )
        return callback


async def _traffic_request(maker, user_id) -> int:
    async with maker() as session:
        package = await session.scalar(
            select(TrafficPackage).where(TrafficPackage.traffic_bytes == 25 * GIB)
        )
        payment = await payments.create_traffic_request(session, user_id, package.id)
        await payments.attach_proof(session, payment.id, AttachmentType.TEXT, caption="ok")
        return payment.id


async def _subscription_payment(maker, user_id) -> int:
    async with maker() as session:
        return (await payments.create_request(session, user_id, 175, 30)).id


async def _confirm(maker, payment_id, panel):
    async with maker() as session:
        return await billing.confirm_payment(session, payment_id, None, panel)


@pytest.mark.parametrize("first", ["reset", "confirm"])
async def test_concurrent_purchase_confirmation_and_reset_keep_purchase(
    pg, monkeypatch, first  # noqa: F811
):
    maker, ids = pg
    panel = SlowPanel()
    # Учёт услуги с контрольной точкой; затем статистика становится недоступной.
    await _confirm(maker, await _subscription_payment(maker, ids["user"]), panel)
    payment_id = await _traffic_request(maker, ids["user"])
    panel.read_fail_server_ids.add(ids["wl"])
    entered = _pause_after_check(monkeypatch)

    if first == "reset":
        reset = asyncio.create_task(_reset(maker, ids["user"]))
        await asyncio.wait_for(entered.wait(), 5)
        confirm = asyncio.create_task(_confirm(maker, payment_id, panel))
    else:
        confirm = asyncio.create_task(_confirm(maker, payment_id, panel))
        await asyncio.sleep(0.02)
        reset = asyncio.create_task(_reset(maker, ids["user"]))
    callback, result = await asyncio.gather(reset, confirm)

    assert result.applied and result.traffic_bytes == 25 * GIB
    assert callback.alerts[-1] in {
        texts.reset_blocked(ResetBlock.OPEN_PAYMENT),
        texts.reset_blocked(ResetBlock.PENDING_CREDIT),
    }
    async with maker() as session:
        assert await session.get(User, ids["user"]) is not None
        payment = await session.get(PaymentRequest, payment_id)
        assert payment.status == PaymentStatus.APPLIED
        event = await session.scalar(
            select(WhitelistLedger).where(WhitelistLedger.payment_request_id == payment_id)
        )
        assert (event.kind, event.status, event.paid_delta) == (
            "purchase", "pending", 25 * GIB,
        )


async def test_reset_check_and_new_payment_request_are_serialized(
    pg, monkeypatch  # noqa: F811
):
    """Заявка, созданная в окне между проверкой и удалением, не теряется."""
    maker, ids = pg
    entered = _pause_after_check(monkeypatch)

    reset = asyncio.create_task(_reset(maker, ids["user"]))
    await asyncio.wait_for(entered.wait(), 5)
    created = await asyncio.gather(_traffic_request(maker, ids["user"]),
                                   return_exceptions=True)
    callback = await reset

    async with maker() as session:
        survivors = (await session.scalars(select(PaymentRequest))).all()
    if isinstance(created[0], BaseException):
        # Сброс выиграл блокировку: заявка не создана, удалять было нечего.
        assert callback.alerts[-1] == DONE
        assert survivors == []
    else:
        # Иначе заявка должна сохраниться вместе с пользователем.
        assert [p.id for p in survivors] == [created[0]]
        assert callback.alerts[-1] != DONE


async def test_web_link_approval_during_reset_is_serialized(pg, monkeypatch):  # noqa: F811
    """Привязка сайта в окне сброса не одобряется к удалённому пользователю."""
    maker, ids = pg
    async with maker() as session:
        account = WebAccount(email="web@example.com", password_hash="x", verified=True)
        session.add(account)
        await session.commit()
        account_id = account.id
    entered = _pause_after_check(monkeypatch)

    async def link_and_approve():
        async with maker() as session:
            request = WebLinkRequest(account_id=account_id, target_user_id=ids["user"])
            session.add(request)
            try:
                await session.commit()
            except IntegrityError:
                return "insert_failed"
            return await web_bridge.decide_link(session, request.id, True)

    reset = asyncio.create_task(_reset(maker, ids["user"]))
    await asyncio.wait_for(entered.wait(), 5)
    linked = await link_and_approve()
    callback = await reset

    async with maker() as session:
        account = await session.get(WebAccount, account_id)
        old_user = await session.get(User, ids["user"])
    if callback.alerts[-1] == DONE:
        assert old_user is None and account.user_id is None
        assert linked in {"insert_failed", "Заявка не найдена", "Заявка уже обработана"}
    else:
        assert old_user is not None
        assert account.user_id in {None, ids["user"]}


async def test_reset_without_obligations_still_works_on_postgresql(pg):  # noqa: F811
    maker, ids = pg
    # Подписка без покупки трафика: обязательств нет.
    payment_id = await _subscription_payment(maker, ids["user"])
    await _confirm(maker, payment_id, MockPanelUpdater())
    callback = await _reset(maker, ids["user"])
    assert callback.alerts[-1] == DONE
    async with maker() as session:
        assert await session.get(User, ids["user"]) is None
        fresh = await session.scalar(select(User).where(User.telegram_id == 77))
        assert fresh is not None and fresh.id != ids["user"]


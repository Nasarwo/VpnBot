"""Сценарии Telegram-бота услуги «Обход белых списков» (пользователь и админ)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select

from app.bot import admin_handlers, keyboards, texts, user_handlers
from app.bot.callbacks import AdminCallback, PaymentCallback, WhitelistCallback
from app.config import Settings
from app.db.enums import PaymentStatus
from app.db.models import PAYMENT_KIND_TRAFFIC, PaymentRequest, Server, TrafficPackage
from app.services import billing, payments, provisioning, whitelist
from app.services.panel_updater import MockPanelUpdater
from tests.test_admin_confirm import FakeBot
from tests.test_whitelist import EMAIL, _Panel, service_on, wl_server  # noqa: F401
from tests.whitelist_inbounds import vless_reality

GIB = whitelist.GIB


@dataclass
class FakeMessage:
    bot: FakeBot = field(default_factory=FakeBot)
    edits: list[str] = field(default_factory=list)
    answers: list[str] = field(default_factory=list)
    text: str | None = None
    from_user: Any = None

    async def edit_text(self, text: str, **_: Any) -> None:
        self.edits.append(text)

    async def answer(self, text: str, **_: Any) -> None:
        self.answers.append(text)


@dataclass
class FakeCallback:
    message: FakeMessage = field(default_factory=FakeMessage)
    alerts: list[str | None] = field(default_factory=list)

    @property
    def bot(self) -> FakeBot:
        return self.message.bot

    async def answer(self, text: str | None = None, **_: Any) -> None:
        self.alerts.append(text)


class FakeState:
    def __init__(self) -> None:
        self.state = None
        self.data: dict[str, Any] = {}

    async def set_state(self, state) -> None:
        self.state = state

    async def update_data(self, **kwargs: Any) -> None:
        self.data.update(kwargs)

    async def get_data(self) -> dict[str, Any]:
        return dict(self.data)

    async def get_state(self):
        return self.state

    async def clear(self) -> None:
        self.state = None
        self.data = {}


def _texts_without_internal_terms(text: str) -> None:
    lowered = text.lower()
    for term in ("ledger", "checkpoint", "epoch", "totalgb", "версия", "advisory"):
        assert term not in lowered, term


async def test_user_sees_balances_and_buys_package(
    session, user, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    monkeypatch.setattr(user_handlers, "build_updater", lambda **_: panel)
    payment = await payments.create_request(session, user.id, 175, 30)
    await billing.confirm_payment(session, payment.id, None, panel)
    settings = Settings(payment_details_text="Карта 0000")

    callback = FakeCallback()
    await user_handlers.whitelist_menu(
        callback, WhitelistCallback(action="home"), session, user, settings, FakeState()
    )
    screen = callback.message.edits[-1]
    assert "Бесплатный остаток: <b>10 ГБ</b>" in screen
    assert "Купленный остаток: <b>0 ГБ</b>" in screen
    assert "25 ГБ — 99 ₽" in screen
    _texts_without_internal_terms(screen)

    package = await session.scalar(
        select(TrafficPackage).where(TrafficPackage.traffic_bytes == 25 * GIB)
    )
    state = FakeState()
    callback = FakeCallback()
    await user_handlers.whitelist_menu(
        callback, WhitelistCallback(action="buy", value=package.id),
        session, user, settings, state,
    )
    created = callback.message.edits[-1]
    assert "Трафик «Обход белых списков»: 25 ГБ" in created and "99 ₽" in created
    assert state.state is not None
    request = await session.scalar(
        select(PaymentRequest).where(PaymentRequest.kind == PAYMENT_KIND_TRAFFIC)
    )
    assert request.status == PaymentStatus.WAITING_ADMIN
    assert "Покупка трафика" in texts.admin_payment_card(request, user)


async def test_expired_user_gets_clear_explanation(
    session, user, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    monkeypatch.setattr(user_handlers, "build_updater", lambda **_: panel)
    await whitelist.get_account(session, user.id, create=True)
    vpn_client.expires_at = datetime.now(UTC) - timedelta(days=1)
    await session.commit()
    callback = FakeCallback()
    await user_handlers.whitelist_menu(
        callback, WhitelistCallback(action="home"), session, user, Settings(), FakeState()
    )
    screen = callback.message.edits[-1]
    assert "подписка истекла" in screen and "после продления" in screen
    assert "99 ₽" not in screen  # покупка недоступна без активной подписки


async def test_admin_confirms_purchase_and_user_is_notified(
    session, user, admin, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    monkeypatch.setattr(admin_handlers, "_get_updater", lambda _settings: panel)
    payment = await payments.create_request(session, user.id, 175, 30)
    await billing.confirm_payment(session, payment.id, None, panel)
    package = await session.scalar(
        select(TrafficPackage).where(TrafficPackage.traffic_bytes == 10 * GIB)
    )
    request = await payments.create_traffic_request(session, user.id, package.id)
    callback = FakeCallback()
    await admin_handlers.on_payment_action(
        callback, PaymentCallback(action="confirm", payment_id=request.id),
        session, admin, Settings(),
    )
    assert "Начислено 10 ГБ" in callback.message.edits[-1]
    user_message = callback.bot.messages[-1]
    assert user_message["chat_id"] == user.telegram_id
    assert "Начислено 10 ГБ" in user_message["text"]
    # Двойное нажатие ничего не начисляет повторно.
    again = FakeCallback()
    await admin_handlers.on_payment_action(
        again, PaymentCallback(action="confirm", payment_id=request.id),
        session, admin, Settings(),
    )
    assert again.alerts[-1] == "Заявка уже применена ранее"
    assert (await whitelist.get_account(session, user.id)).paid_bytes == 10 * GIB


async def test_admin_adds_whitelist_server_with_automatic_inventory(
    session, admin, monkeypatch
):
    monkeypatch.setattr(
        provisioning, "XuiClient",
        lambda **_: _Panel([vless_reality(12)]),
    )
    state = FakeState()
    callback = FakeCallback()
    await admin_handlers.admin_nav(
        callback, AdminCallback(action="add_whitelist"), session, admin, Settings(), state
    )
    assert state.data["server_purpose"] == "whitelist"
    message = FakeMessage(text="WL|LV|https://cc.example.test:2053|admin|pw")
    await admin_handlers.admin_add_server_line(message, session, state, Settings(), admin)
    assert "готов к выдаче" in message.answers[-1]
    server = await whitelist.get_active_server(session)
    assert server.purpose == "whitelist" and whitelist.server_ready(server)

    # Второй включённый сервер услуги не добавляется.
    state = FakeState()
    callback = FakeCallback()
    await admin_handlers.admin_nav(
        callback, AdminCallback(action="add_whitelist"), session, admin, Settings(), state
    )
    assert "Уже есть" in (callback.alerts[-1] or "")
    servers = (await session.scalars(select(Server))).all()
    assert len(servers) == 1


async def test_admin_failed_first_sync_is_visible_and_retryable(
    session, admin, monkeypatch
):
    from app.services.xui_client import XuiError

    monkeypatch.setattr(
        provisioning, "XuiClient", lambda **_: _Panel(error=XuiError("connect timeout"))
    )
    state = FakeState()
    await state.update_data(server_purpose="whitelist")
    message = FakeMessage(text="WL|LV|https://cc.example.test:2053|admin|pw")
    await admin_handlers.admin_add_server_line(message, session, state, Settings(), admin)
    assert "не готов" in message.answers[-1] and "connect timeout" in message.answers[-1]
    assert not whitelist.server_ready(await whitelist.get_active_server(session))

    monkeypatch.setattr(
        provisioning, "XuiClient",
        lambda **_: _Panel([vless_reality(12)]),
    )
    from app.bot.callbacks import WhitelistAdminCallback

    callback = FakeCallback()
    await admin_handlers.whitelist_admin(
        callback, WhitelistAdminCallback(action="sync"), session, admin, Settings(),
        FakeState(),
    )
    assert whitelist.server_ready(await whitelist.get_active_server(session))
    assert "готов к выдаче" in callback.message.edits[-1]


async def test_outage_payment_is_shown_as_awaiting_and_admin_resolves(
    session, user, admin, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    from aiogram.filters import CommandObject

    panel = MockPanelUpdater()
    monkeypatch.setattr(user_handlers, "build_updater", lambda **_: panel)
    monkeypatch.setattr(admin_handlers, "_get_updater", lambda _settings: panel)
    first = await payments.create_request(session, user.id, 175, 30)
    await billing.confirm_payment(session, first.id, None, panel)
    panel.read_fail_server_ids.add(wl_server.id)
    second = await payments.create_request(session, user.id, 175, 30)
    paid_at = datetime.now(UTC) - timedelta(minutes=30)
    result = await billing.confirm_payment(session, second.id, None, panel, now=paid_at)
    assert result.applied and result.whitelist_pending

    async def user_screen() -> str:
        callback = FakeCallback()
        await user_handlers.whitelist_menu(
            callback, WhitelistCallback(action="home"), session, user, Settings(),
            FakeState(),
        )
        screen = callback.message.edits[-1]
        _texts_without_internal_terms(screen)
        return screen

    screen = await user_screen()
    assert "ещё не учитывают" in screen and "будет восстановлен до 10 ГБ" in screen
    assert "Сервер временно не отвечает" in screen and "Оплата сохранена" in screen

    panel.consume(wl_server.id, EMAIL, 4 * GIB, at=paid_at + timedelta(minutes=10))
    panel.read_fail_server_ids.clear()
    screen = await user_screen()
    assert "уточняет администратор" in screen

    async def command(handler, args: str, *actor) -> str:
        message = FakeMessage()
        await handler(
            message, CommandObject(prefix="/", command="x", args=args), session, *actor,
            Settings(),
        )
        return message.answers[-1]

    resolve = admin_handlers.whitelist_resolve_cmd
    card = await command(admin_handlers.whitelist_user_cmd, str(user.telegram_id))
    assert "нужно решение" in card
    assert "до: бесплатный 10 ГБ, купленный 0 ГБ" in card
    assert "после: бесплатный 6 ГБ, купленный 0 ГБ" in card
    assert "/wlresolve" in card
    usage = await command(resolve, f"{user.telegram_id} куда", admin)
    assert usage.startswith("Использование: /wlresolve")
    done = await command(resolve, f"{user.telegram_id} до расход до оплаты", admin)
    assert "нужно решение" not in done
    account = await whitelist.get_account(session, user.id)
    assert (account.free_bytes, account.paid_bytes) == (10 * GIB, 0)
    again = await command(resolve, f"{user.telegram_id} после повтор", admin)
    assert again.startswith("Не изменено")


def test_whitelist_texts_and_keyboards():
    overview = whitelist.Overview(
        status="active", free_bytes=int(7.5 * GIB), paid_bytes=25 * GIB,
        expires_at=datetime(2027, 3, 31, tzinfo=UTC), stale=True,
        last_synced_at=datetime(2026, 10, 4, tzinfo=UTC), pending=True, can_buy=True,
        packages=[TrafficPackage(id=1, traffic_bytes=10 * GIB, price=49, enabled=True)],
    )
    text = texts.whitelist_overview(overview, 10 * GIB)
    assert "7,5 ГБ" in text and "25 ГБ" in text and "последний" in text
    _texts_without_internal_terms(text)
    lifetime = texts.whitelist_overview(whitelist.Overview(status="lifetime"), 10 * GIB)
    assert "без ограничений" in lifetime and "Бесплатный" not in lifetime
    markups = [
        keyboards.whitelist_keyboard(overview),
        keyboards.welcome_menu(True, show_whitelist=True),
        keyboards.subscription_menu(show_whitelist=True),
        keyboards.admin_add_server_type_keyboard(),
        keyboards.admin_whitelist_keyboard(None),
        keyboards.admin_whitelist_packages_keyboard(overview.packages),
        keyboards.admin_whitelist_package_keyboard(overview.packages[0]),
        keyboards.admin_whitelist_rollout_keyboard(),
        keyboards.admin_whitelist_user_keyboard(1, True),
    ]
    for markup in markups:
        for row in markup.inline_keyboard:
            for button in row:
                assert button.style in {"primary", "success", "danger"}, button.text
    assert texts.fmt_gb(0) == "0 ГБ" and texts.fmt_gb(3 * GIB) == "3 ГБ"

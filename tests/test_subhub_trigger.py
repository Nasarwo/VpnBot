"""Быстрый триггер SubHub (POST /admin/sync) из обработчиков бота.

Вместо SubHub — локальный HTTP-сервер на 127.0.0.1 (настоящий сокет и httpx):
он записывает запросы либо принимает соединение и закрывает его без ответа,
как опубликованный порт контейнера SubHub во время его перезапуска
(наблюдалось на стенде приёмки: ``httpx.RemoteProtocolError``). Это проверка
поведения бота, а не интеграции с настоящим SubHub — её даёт
``ops/acceptance/whitelist_background_e2e.py``.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from aiogram.filters import CommandObject
from sqlalchemy import select

from app.bot import admin_handlers, user_handlers
from app.bot.callbacks import PaymentCallback, PlanCallback
from app.config import Settings
from app.db.enums import PaymentStatus
from app.db.models import PaymentRequest
from app.services import billing, payments, whitelist
from app.services.panel_updater import MockPanelUpdater
from app.services.subhub_client import SubHubClient, SubHubError, trigger_configured_sync
from tests.test_whitelist import EMAIL, service_on, wl_server  # noqa: F401
from tests.test_whitelist_bot import FakeCallback, FakeMessage, FakeState

GIB = whitelist.GIB


class LocalSubHub:
    """HTTP-сервер вместо SubHub: ``accept`` — 202 и запись, ``drop`` — разрыв без ответа."""

    def __init__(self, mode: str = "accept") -> None:
        self.mode = mode
        self.requests: list[tuple[str, str]] = []
        self.url = ""
        self._server: asyncio.Server | None = None

    async def __aenter__(self) -> LocalSubHub:
        self._server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        port = self._server.sockets[0].getsockname()[1]
        self.url = f"http://127.0.0.1:{port}"
        return self

    async def __aexit__(self, *_: object) -> None:
        assert self._server is not None
        self._server.close()
        await self._server.wait_closed()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            head = await reader.readuntil(b"\r\n\r\n")
            method, path, _ = head.split(b"\r\n", 1)[0].decode().split(" ", 2)
            length = 0
            for line in head.decode().split("\r\n")[1:]:
                name, _, value = line.partition(":")
                if name.strip().lower() == "content-length":
                    length = int(value.strip())
            if length:
                await reader.readexactly(length)
            self.requests.append((method, path))
            if self.mode == "accept":
                writer.write(b"HTTP/1.1 202 Accepted\r\nContent-Length: 0\r\n"
                             b"Connection: close\r\n\r\n")
                await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionError):
            pass
        finally:
            writer.close()

    @property
    def syncs(self) -> int:
        return sum(1 for method, path in self.requests if (method, path) == ("POST", "/admin/sync"))


def _settings(hub: LocalSubHub) -> Settings:
    return Settings(subhub_url=hub.url, subhub_admin_token="admin-secret",
                    subhub_timeout_seconds=2)


async def _command(handler, args: str, session, admin, settings: Settings) -> str:
    message = FakeMessage()
    await handler(message, CommandObject(prefix="/", command="x", args=args), session, admin,
                  settings)
    return message.answers[-1]


# --- Разрыв соединения SubHub: триггер остаётся best-effort ------------------------------


async def test_dropped_connection_does_not_escape_best_effort_trigger():
    async with LocalSubHub("drop") as hub:
        assert await trigger_configured_sync(hub.url, "admin-secret", timeout=2) is False
        assert hub.syncs == 1  # запрос дошёл до сервера, ответа не было


async def test_dropped_connection_is_subhub_unavailable_for_resolve():
    async with LocalSubHub("drop") as hub:
        async with SubHubClient(hub.url, "admin-secret", timeout=2) as client:
            with pytest.raises(SubHubError):
                await client.resolve(email="client-id")


async def test_payment_confirmation_finishes_when_subhub_drops_connection(
    session, user, admin, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    monkeypatch.setattr(admin_handlers, "_get_updater", lambda _settings: panel)
    payment = await payments.create_request(session, user.id, 175, 30)
    async with LocalSubHub("drop") as hub:
        callback = FakeCallback()
        await admin_handlers.on_payment_action(
            callback, PaymentCallback(action="confirm", payment_id=payment.id),
            session, admin, _settings(hub),
        )
        assert hub.syncs == 1
    stored = await session.get(PaymentRequest, payment.id)
    assert stored.status == PaymentStatus.APPLIED
    # Администратор видит результат, пользователь уведомлён о продлении.
    assert callback.message.edits and "Доступ продлён" in callback.message.edits[-1]
    assert [m for m in callback.bot.messages if m["chat_id"] == user.telegram_id]
    again = FakeCallback()
    await admin_handlers.on_payment_action(
        again, PaymentCallback(action="confirm", payment_id=payment.id),
        session, admin, Settings(),
    )
    assert again.alerts[-1] == "Заявка уже применена ранее"
    grants = await session.scalars(
        select(whitelist.WhitelistLedger.id).where(
            whitelist.WhitelistLedger.source_key == f"payment:{payment.id}"
        )
    )
    assert len(grants.all()) == 1


async def test_trial_activation_finishes_when_subhub_drops_connection(
    session, user, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    monkeypatch.setattr(user_handlers, "build_updater", lambda **_: panel)
    async with LocalSubHub("drop") as hub:
        callback = FakeCallback()
        await user_handlers.select_plan(
            callback, PlanCallback(code="trial"), session, user, _settings(hub), FakeState(),
        )
        assert hub.syncs == 1
    assert callback.message.edits and "пробн" in callback.message.edits[-1].lower()
    assert (await whitelist.get_account(session, user.id)).free_bytes == 3 * GIB


# --- Административные изменения доступа вызывают быстрый триггер -------------------------


async def _paid(session, user, panel) -> PaymentRequest:
    payment = await payments.create_request(session, user.id, 175, 30)
    result = await billing.confirm_payment(session, payment.id, None, panel)
    assert result.applied
    return payment


async def test_manual_extend_triggers_subhub(
    session, user, admin, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    monkeypatch.setattr(admin_handlers, "_get_updater", lambda _settings: panel)
    await _paid(session, user, panel)
    async with LocalSubHub() as hub:
        answer = await _command(admin_handlers.manual_extend, f"{user.telegram_id} 30", session,
                                admin, _settings(hub))
        assert answer.startswith("Клиент продлён")
        assert hub.syncs == 1


async def test_sync_command_triggers_subhub(
    session, user, admin, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    monkeypatch.setattr(admin_handlers, "_get_updater", lambda _settings: panel)
    await _paid(session, user, panel)
    async with LocalSubHub() as hub:
        answer = await _command(admin_handlers.sync_user, str(user.telegram_id), session, admin,
                                _settings(hub))
        assert answer.startswith("Синхронизация завершена")
        assert hub.syncs == 1


async def test_balance_adjustment_applied_on_panel_triggers_subhub(
    session, user, admin, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    monkeypatch.setattr(admin_handlers, "_get_updater", lambda _settings: panel)
    await _paid(session, user, panel)
    async with LocalSubHub() as hub:
        answer = await _command(admin_handlers.whitelist_adjust_cmd,
                                f"{user.telegram_id} 0 5 компенсация", session, admin,
                                _settings(hub))
        assert answer.startswith("Применено на сервере")
        assert hub.syncs == 1


async def test_uncertainty_resolution_applied_on_panel_triggers_subhub(
    session, user, admin, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    monkeypatch.setattr(admin_handlers, "_get_updater", lambda _settings: panel)
    await _paid(session, user, panel)
    # Оплата при недоступной статистике, после неё панель видела трафик: расход
    # нельзя разделить автоматически — нужно решение администратора.
    panel.read_fail_server_ids.add(wl_server.id)
    second = await payments.create_request(session, user.id, 175, 30)
    paid_at = datetime.now(UTC) - timedelta(minutes=30)
    await billing.confirm_payment(session, second.id, None, panel, now=paid_at)
    panel.consume(wl_server.id, EMAIL, 4 * GIB, at=paid_at + timedelta(minutes=10))
    panel.read_fail_server_ids.clear()
    await whitelist.user_overview(session, user.id, panel)
    assert [e for e in await whitelist.list_open_events(session, user.id)
            if e.status == whitelist.EVENT_UNCERTAIN]
    async with LocalSubHub() as hub:
        answer = await _command(admin_handlers.whitelist_resolve_cmd,
                                f"{user.telegram_id} до расход до оплаты", session, admin,
                                _settings(hub))
        assert answer.startswith("Применено на сервере")
        assert hub.syncs == 1


# --- Фоновый цикл: возобновление прерванной оплаты -------------------------------------


class _Maker:
    def __call__(self):
        return self

    async def __aenter__(self):
        return "session"

    async def __aexit__(self, *exc):
        return False


@pytest.mark.parametrize(("recovered", "syncs"), [(1, 1), (0, 0)])
async def test_health_poller_triggers_subhub_after_recovering_payment(
    monkeypatch, recovered, syncs
):
    from app import main as app_main
    from app.services import health

    async def fake_recover(session, updater):
        return recovered

    async def fake_check(session, **kwargs):
        return {}

    async def stop(session, updater):  # конец первой итерации цикла
        raise asyncio.CancelledError

    monkeypatch.setattr(app_main, "get_sessionmaker", lambda: _Maker())
    monkeypatch.setattr(app_main, "build_updater", lambda **_: object())
    monkeypatch.setattr(billing, "recover_confirmed_payments", fake_recover)
    monkeypatch.setattr(health, "check_servers", fake_check)
    monkeypatch.setattr(whitelist, "process_due", stop)
    async with LocalSubHub() as hub:
        settings = _settings(hub).model_copy(update={"server_health_poll_seconds": 60})
        with pytest.raises(asyncio.CancelledError):
            await app_main._server_health_poller(settings)
        assert hub.syncs == syncs

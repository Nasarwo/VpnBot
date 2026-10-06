"""Перенос клиентов при смене цели: админ-сценарии бота, SubHub и ops-сверка.

Обработчики вызываются напрямую (транспорт Telegram — заглушки), SubHub —
локальный HTTP-сервер ``LocalSubHub``; панель — ``MockPanelUpdater``.
"""
from __future__ import annotations

from datetime import UTC, datetime

from aiogram.filters import CommandObject

from app.bot import admin_handlers
from app.bot.callbacks import WhitelistAdminCallback
from app.services import whitelist
from app.services.panel_updater import MockPanelUpdater
from ops import whitelist_check
from tests.test_subhub_trigger import LocalSubHub, _settings
from tests.test_whitelist import EMAIL, _pay, _wl_state, service_on, wl_server  # noqa: F401
from tests.test_whitelist_bot import FakeCallback, FakeMessage, FakeState
from tests.test_whitelist_retarget import _add_candidate, _links, _live, _placed


async def _callback(session, admin, settings, action: str, value: int = 0) -> FakeCallback:
    callback = FakeCallback()
    await admin_handlers.whitelist_admin(
        callback, WhitelistAdminCallback(action=action, value=value), session, admin,
        settings, FakeState(),
    )
    return callback


async def _command(handler, args: str, session, admin) -> str:
    message = FakeMessage()
    await handler(message, CommandObject(prefix="/", command="x", args=args), session, admin)
    return message.answers[-1]


async def test_choosing_target_moves_clients_notifies_subhub_and_shows_progress(
    session, user, admin, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    monkeypatch.setattr(admin_handlers, "_get_updater", lambda _settings: panel)
    await _pay(session, user, panel)
    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)
    async with LocalSubHub() as hub:
        callback = await _callback(session, admin, _settings(hub), "choose", 8)
        assert hub.syncs == 1  # выдача изменилась — SubHub перечитывает панель
    assert _wl_state(panel, wl_server).inbound_ids == [8]
    home = callback.message.edits[-1]
    assert "Размещение на inbound 8 (flow: нет): подтверждено 1 из 1; ожидает 0; ошибка 0" in home

    # Повторный выбор той же цели: применять нечего, SubHub не дёргается.
    async with LocalSubHub() as hub:
        await _callback(session, admin, _settings(hub), "choose", 8)
        assert hub.syncs == 0


async def test_failed_move_is_shown_as_error_not_as_ready(
    session, user, admin, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    monkeypatch.setattr(admin_handlers, "_get_updater", lambda _settings: panel)
    await _pay(session, user, panel)
    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)
    panel.panel_inbounds[wl_server.id] = {7: True}  # 8 на панели не найден
    async with LocalSubHub() as hub:
        callback = await _callback(session, admin, _settings(hub), "choose", 8)
        assert hub.syncs == 0
    home = callback.message.edits[-1]
    assert "Сервер: #" in home and "готов" in home
    assert "подтверждено 0 из 1; ожидает 0; ошибка 1" in home
    assert "Перенос клиентов не завершён" in home
    assert _wl_state(panel, wl_server).inbound_ids == [7]


async def test_manual_inbound_commands_pause_service_until_sync(
    session, user, admin, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    monkeypatch.setattr(admin_handlers, "_get_updater", lambda _settings: panel)
    await _pay(session, user, panel)
    sid = wl_server.id
    answer = await _command(admin_handlers.del_inbound, f"{sid} 7", session, admin)
    assert "не готов до синхронизации" in answer
    answer = await _command(
        admin_handlers.add_inbound, f"{sid} 7 vless xtls-rprx-vision", session, admin
    )
    assert "не готов до синхронизации" in answer
    server = await whitelist.get_active_server(session)
    assert not whitelist.server_ready(server)
    # flow ещё не проверен на совместимость: панель не трогается.
    assert await whitelist.process_due(session, panel) == 0
    assert _wl_state(panel, wl_server).inbound_flows == {7: ""}

    _live(monkeypatch, 7)
    async with LocalSubHub() as hub:
        await _callback(session, admin, _settings(hub), "sync")
        assert hub.syncs == 1
    assert _wl_state(panel, wl_server).inbound_flows == {7: "xtls-rprx-vision"}
    assert await _placed(session, user, wl_server, 7, "xtls-rprx-vision")


async def test_claim_command_releases_legacy_attachment(
    session, user, admin, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    await _pay(session, user, panel)
    # Привязка к 7 неизвестного происхождения (учёт до миграции).
    for row in await whitelist._list_placements(session, user.id):
        await session.delete(row)
    await session.commit()
    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)
    await whitelist.choose_inbound(session, wl_server, 8, admin.id)
    await whitelist.process_due(session, panel)
    assert _wl_state(panel, wl_server).inbound_ids == [7, 8]

    answer = await _command(admin_handlers.whitelist_claim_cmd, "8 причина", session, admin)
    assert answer.startswith("Не изменено") and "текущая цель" in answer
    await session.refresh(admin)  # каждое обновление Telegram — новая сессия и db_user
    answer = await _command(
        admin_handlers.whitelist_claim_cmd, "7 inbound 7 был целью услуги", session, admin
    )
    assert "Признано привязок к inbound 7: 1" in answer
    await whitelist.process_due(session, panel)
    assert _wl_state(panel, wl_server).inbound_ids == [8]
    assert await _links(session, user) == [(8, "attached", "service")]


async def test_whitelist_check_reports_actual_placement(
    session, user, vpn_client, service_on, wl_server, monkeypatch  # noqa: F811
):
    panel = MockPanelUpdater()
    await _pay(session, user, panel)
    now = datetime.now(UTC)
    counts, problems = await whitelist_check.collect(session, panel, now)
    assert (counts["mismatch"], counts["placement_mismatch"], counts["placement_pending"]) == (
        0, 0, 0
    )

    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)
    await whitelist.choose_inbound(session, wl_server, 8, None)
    counts, problems = await whitelist_check.collect(session, panel, now)
    assert counts["placement_mismatch"] == 1 and counts["placement_pending"] == 1
    assert any("нет привязки к целевому inbound 8" in line for line in problems)

    await whitelist.process_due(session, panel)
    counts, _ = await whitelist_check.collect(session, panel, now)
    assert (counts["placement_mismatch"], counts["placement_pending"]) == (0, 0)
    # Клиент снова прикреплён к прежней цели услуги вручную — это видно.
    state = _wl_state(panel, wl_server)
    state.inbound_ids = [7, 8]
    state.inbound_flows[7] = ""
    session.add(whitelist.WhitelistPlacement(
        user_id=user.id, server_id=wl_server.id, inbound_id=7, panel_email=EMAIL,
        state="attached", origin="claimed", created_at=now,
    ))
    await session.commit()
    counts, problems = await whitelist_check.collect(session, panel, now)
    assert counts["placement_mismatch"] == 1
    assert any("не сняты прежние привязки услуги [7]" in line for line in problems)
    await session.rollback()

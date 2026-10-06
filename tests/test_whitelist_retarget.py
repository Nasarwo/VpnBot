"""Смена целевого inbound whitelist-сервера: перенос синхронизированных клиентов.

P1 ревью 2026-10-06 (`docs/REVIEW_2026-10-06.md`): после выбора нового inbound
сервер становился «готов», а очередь не применяла ни одного учёта — клиенты
оставались на прежнем inbound.

Модель панели — ``MockPanelUpdater`` с семантикой 3x-ui 3.2–3.9 (сверена с
исходниками ``ClientService.Attach/Detach/Update``): attach копирует общую
запись клиента и не трогает счётчик, detach сохраняет строку статистики, update
с фильтром ``inboundIds`` меняет flow только в inbound'ах фильтра (3.2.0 фильтра
не знает — ``update_filter_supported=False``). Проверяется фактическое
размещение на панели, квота и доступный объём, а не только записи в БД.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bot import texts
from app.db.enums import Protocol
from app.db.models import (
    ServerInbound,
    VpnClient,
    WhitelistAccount,
    WhitelistLedger,
    WhitelistPlacement,
)
from app.services import provisioning, whitelist
from app.services.panel_updater import MockPanelUpdater, PanelUpdateError
from tests.test_whitelist import (  # noqa: F401
    EMAIL,
    _account,
    _ago,
    _baseline,
    _buy,
    _ledger_count,
    _pay,
    _set_balance,
    _wl_state,
    panel,
    service_on,
    wl_server,
)
from tests.whitelist_inbounds import plain_vless, vless_reality

GIB = whitelist.GIB


def _live(monkeypatch, *inbounds) -> None:
    """Список inbound'ов панели, который читает сверка реестра (id или готовый dict)."""
    raw = [vless_reality(i) if isinstance(i, int) else i for i in inbounds]

    async def fetch(*_args, **_kwargs):
        return raw

    monkeypatch.setattr(provisioning, "fetch_inbounds", fetch)


async def _add_candidate(session, server, inbound_id: int, flow: str | None = None) -> None:
    session.add(
        ServerInbound(
            server_id=server.id, inbound_id=inbound_id, protocol=Protocol.VLESS,
            enabled=False, flow=flow,
        )
    )
    await session.commit()


async def _choose(session, server, inbound_id: int) -> whitelist.InventoryResult:
    result = await whitelist.choose_inbound(session, server, inbound_id, None)
    assert result.status == whitelist.INVENTORY_READY, result.error
    return result


async def _expire_backoff(session, user) -> None:
    account = await _account(session, user)
    account.next_sync_at = datetime.now(UTC) - timedelta(seconds=1)
    await session.commit()


async def _links(session, user) -> list[tuple[int, str, str]]:
    rows = (
        await session.scalars(
            select(WhitelistPlacement)
            .where(WhitelistPlacement.user_id == user.id)
            .order_by(WhitelistPlacement.inbound_id)
            .execution_options(populate_existing=True)
        )
    ).all()
    return [(row.inbound_id, row.state, row.origin) for row in rows]


def _available(mock, server) -> int:
    state = _wl_state(mock, server)
    if not state.enable:
        return 0
    return max(0, state.total_bytes - (state.used_bytes or 0))


async def _placed(session, user, server, inbound_id: int, flow: str = "") -> bool:
    account = await _account(session, user)
    return (
        account.placement_server_id, account.placement_inbound_id, account.placement_flow
    ) == (server.id, inbound_id, flow)


async def _snapshot(session, user, mock, server) -> dict:
    account = await _account(session, user)
    client = await session.scalar(select(VpnClient).where(VpnClient.user_id == user.id))
    await session.refresh(client)
    state = _wl_state(mock, server)
    ledger = await session.scalar(
        select(WhitelistLedger.id).order_by(WhitelistLedger.id.desc()).limit(1)
    )
    return {
        "free": account.free_bytes,
        "paid": account.paid_bytes,
        "checkpoint": account.usage_checkpoint_bytes,
        "observed": account.usage_observed_bytes,
        "row": account.traffic_row_id,
        "email": account.panel_email,
        "blocked": account.admin_blocked,
        "expires": client.expires_at,
        "total": state.total_bytes,
        "used": state.used_bytes,
        "panel_row": state.traffic_row_id,
        "expiry_ms": state.expiry_ms,
        "enable": state.enable,
        "last_ledger": ledger,
    }


async def test_existing_user_moves_to_new_inbound(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _pay(session, user, panel)
    account = await _account(session, user)
    assert account.desired_version == account.applied_version
    assert _wl_state(panel, wl_server).inbound_ids == [7]
    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)

    result = await whitelist.choose_inbound(session, wl_server, 8, None)
    assert result.status == whitelist.INVENTORY_READY
    applied = await whitelist.process_due(session, panel)

    assert applied == 1
    assert _wl_state(panel, wl_server).inbound_ids == [8]


# --- Сохранение идентичности, срока, остатков и расхода ------------------------------


async def test_move_keeps_identity_term_balances_counter_and_grants_nothing(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _pay(session, user, panel)
    await _set_balance(session, user, panel, 3, 20)
    panel.consume(wl_server.id, EMAIL, 5 * GIB)
    await whitelist.user_overview(session, user.id, panel)
    before = await _snapshot(session, user, panel, wl_server)
    assert (before["free"], before["paid"]) == (0, 18 * GIB)
    assert await _links(session, user) == [(7, "attached", "service")]
    assert await _placed(session, user, wl_server, 7)
    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)

    await _choose(session, wl_server, 8)
    assert await whitelist.process_due(session, panel) == 1

    after = await _snapshot(session, user, panel, wl_server)
    assert _wl_state(panel, wl_server).inbound_ids == [8]
    # Счётчик и его строка те же, квота и срок не изменились, пакет не выдан.
    assert after == before
    assert await _ledger_count(session, user.id, "free_grant") == 1
    assert await _placed(session, user, wl_server, 8)
    assert await _links(session, user) == [(8, "attached", "service")]
    assert panel.detached == [(wl_server.id, EMAIL, (7,))]
    # Расход после переноса списывается с тех же остатков по тому же счётчику.
    panel.consume(wl_server.id, EMAIL, GIB)
    overview = await whitelist.user_overview(session, user.id, panel)
    assert (overview.free_bytes, overview.paid_bytes) == (0, 17 * GIB)
    # Повтор очереди ничего не меняет.
    attached = len(panel.attached)
    assert await whitelist.process_due(session, panel) == 0
    assert len(panel.attached) == attached and len(panel.detached) == 1


async def test_rechoosing_the_same_target_changes_nothing(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _pay(session, user, panel)
    _live(monkeypatch, 7)
    calls = (len(panel.quota_applied), len(panel.attached), len(panel.detached))
    for _ in range(2):
        await _choose(session, wl_server, 7)
        assert await whitelist.process_due(session, panel) == 0
    assert (len(panel.quota_applied), len(panel.attached), len(panel.detached)) == calls
    assert _wl_state(panel, wl_server).inbound_ids == [7]


# --- Прежний inbound: существует, удалён, несовместим -----------------------------------


async def test_old_inbound_deleted_on_panel_target_changes_via_registry_sync(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _pay(session, user, panel)
    # Inbound 7 удалён на панели (3x-ui снимает его привязки), появился 8: сверка
    # реестра сама делает 8 целью — без выбора администратором.
    panel.remove_inbound(wl_server.id, 7)
    assert _wl_state(panel, wl_server).inbound_ids == []
    _live(monkeypatch, 8)
    result = await whitelist.sync_inventory(session, wl_server)
    await session.commit()
    assert result.status == whitelist.INVENTORY_READY
    server = await whitelist.get_active_server(session)
    assert whitelist.target_inbound(server).inbound_id == 8

    assert await whitelist.process_due(session, panel) == 1
    assert _wl_state(panel, wl_server).inbound_ids == [8]
    assert panel.detached == []  # снимать нечего
    assert await _links(session, user) == [(8, "attached", "service")]
    assert await _placed(session, user, wl_server, 8)


async def test_incompatible_old_target_is_left_after_choosing_compatible_one(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _pay(session, user, panel)
    await _add_candidate(session, wl_server, 8)
    # 7 стал несовместим с SubHub (REALITY снят): сервер не готов, панель не трогается.
    _live(monkeypatch, plain_vless(7), vless_reality(8))
    result = await whitelist.sync_inventory(session, wl_server)
    await session.commit()
    assert result.status == whitelist.INVENTORY_INCOMPATIBLE
    calls = len(panel.quota_applied)
    assert await whitelist.process_due(session, panel) == 0
    assert len(panel.quota_applied) == calls

    await _choose(session, wl_server, 8)
    assert await whitelist.process_due(session, panel) == 1
    assert _wl_state(panel, wl_server).inbound_ids == [8]
    assert panel.detached == [(wl_server.id, EMAIL, (7,))]


# --- Недоступная цель и сбои шагов ------------------------------------------------------


async def test_unavailable_new_target_keeps_client_on_old_inbound(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _pay(session, user, panel)
    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)
    await _choose(session, wl_server, 8)
    panel.panel_inbounds[wl_server.id] = {7: True, 8: False}  # выключен на панели

    assert await whitelist.process_due(session, panel) == 0
    assert _wl_state(panel, wl_server).inbound_ids == [7]
    account = await _account(session, user)
    assert "Недоступные inbound" in account.last_error
    assert whitelist._aware(account.next_sync_at) > datetime.now(UTC)
    assert await _placed(session, user, wl_server, 7)  # прежнее подтверждение не снято
    progress = await whitelist.placement_progress(session)
    assert (progress.placed, progress.pending, progress.failed) == (0, 0, 1)
    # Backoff соблюдается: до его истечения панель не трогается.
    calls = len(panel.quota_applied)
    assert await whitelist.process_due(session, panel) == 0
    assert len(panel.quota_applied) == calls

    panel.panel_inbounds[wl_server.id][8] = True
    await _expire_backoff(session, user)
    assert await whitelist.process_due(session, panel) == 1
    assert _wl_state(panel, wl_server).inbound_ids == [8]
    progress = await whitelist.placement_progress(session)
    assert (progress.placed, progress.pending, progress.failed) == (1, 0, 0)


@pytest.mark.parametrize(
    "step",
    ["attach", "attach_lost", "update", "verify", "detach", "detach_lost", "detach_ignored"],
)
async def test_step_failure_is_resumed_without_losing_access_or_ownership(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch, step  # noqa: F811
):
    await _pay(session, user, panel)
    await _set_balance(session, user, panel, 4, 6)
    before = await _snapshot(session, user, panel, wl_server)
    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)
    await _choose(session, wl_server, 8)
    panel.fail_steps = {step}

    await whitelist.process_due(session, panel)
    ids = _wl_state(panel, wl_server).inbound_ids
    # Прежняя привязка снимается только после подтверждения новой.
    assert 7 in ids or (step == "detach_lost" and ids == [8])
    account = await _account(session, user)
    assert account.last_error and whitelist._aware(account.next_sync_at) > datetime.now(UTC)
    assert not await _placed(session, user, wl_server, 8)  # успех не зафиксирован
    progress = await whitelist.placement_progress(session)
    assert progress.failed == 1 and not progress.complete
    assert (account.free_bytes, account.paid_bytes) == (4 * GIB, 6 * GIB)

    panel.fail_steps = set()
    await _expire_backoff(session, user)
    await whitelist.process_due(session, panel)
    assert _wl_state(panel, wl_server).inbound_ids == [8]
    assert await _placed(session, user, wl_server, 8)
    # Привязка к 8 создана услугой (в т. ч. при потерянном ответе attach).
    assert await _links(session, user) == [(8, "attached", "service")]
    after = await _snapshot(session, user, panel, wl_server)
    assert after == before
    assert (await whitelist.placement_progress(session)).complete


class _Crash(RuntimeError):
    """Процесс завершился после запроса к панели, до commit."""


class _CrashAfterApply(MockPanelUpdater):
    async def apply_quota_client(self, server, spec, target):
        await super().apply_quota_client(server, spec, target)
        raise _Crash("process killed after attach")


class _CrashAfterDetach(MockPanelUpdater):
    async def detach_quota_client(self, server, email, inbound_ids):
        await super().detach_quota_client(server, email, inbound_ids)
        raise _Crash("process killed after detach")


def _share(source: MockPanelUpdater, target: MockPanelUpdater) -> MockPanelUpdater:
    target.quota_clients = source.quota_clients
    target._next_row_id = source._next_row_id
    return target


async def _restart(session) -> AsyncSession:
    """Новый процесс: новая сессия к той же БД (несохранённое потеряно)."""
    await session.close()
    maker = async_sessionmaker(bind=session.bind, expire_on_commit=False, class_=AsyncSession)
    return maker()


async def test_restart_after_attach_keeps_ownership_and_finishes_later(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _pay(session, user, panel)
    await _add_candidate(session, wl_server, 8)
    await _add_candidate(session, wl_server, 9)
    _live(monkeypatch, 7, 8, 9)
    await _choose(session, wl_server, 8)

    assert await whitelist.process_due(session, _share(panel, _CrashAfterApply())) == 0
    assert _wl_state(panel, wl_server).inbound_ids == [7, 8]
    fresh = await _restart(session)
    # Намерение сохранено до запроса: привязка к 8 известна как созданная услугой.
    assert await _links(fresh, user) == [(7, "attached", "service"), (8, "attaching", "service")]
    assert await whitelist.process_due(fresh, panel) == 1
    assert _wl_state(panel, wl_server).inbound_ids == [8]
    assert await _links(fresh, user) == [(8, "attached", "service")]

    # Позже цель снова меняется — привязка к 8 снимается как привязка услуги.
    server = await whitelist.get_active_server(fresh)
    await _choose(fresh, server, 9)
    assert await whitelist.process_due(fresh, panel) == 1
    assert _wl_state(panel, server).inbound_ids == [9]
    await fresh.close()


async def test_restart_after_detach_before_commit_confirms_placement(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _pay(session, user, panel)
    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)
    await _choose(session, wl_server, 8)

    crashed = _share(panel, _CrashAfterDetach())
    assert await whitelist.process_due(session, crashed) == 0
    assert crashed.detached == [(wl_server.id, EMAIL, (7,))]
    assert _wl_state(panel, wl_server).inbound_ids == [8]
    fresh = await _restart(session)
    # Квота и новая привязка сохранены до снятия; снятие ещё не подтверждено.
    assert await _links(fresh, user) == [(7, "detaching", "service"), (8, "attached", "service")]
    account = await _account(fresh, user)
    assert account.applied_version == account.desired_version
    assert not await _placed(fresh, user, wl_server, 8)
    assert await whitelist.process_due(fresh, panel) == 1
    assert await _placed(fresh, user, wl_server, 8)
    assert await _links(fresh, user) == [(8, "attached", "service")]
    assert panel.detached == []  # привязки уже нет: повторный detach не нужен
    await fresh.close()


# --- Несколько смен цели и конкуренция ------------------------------------------------


async def test_several_target_changes_follow_the_latest_target_with_backoff(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _pay(session, user, panel)
    for inbound_id in (8, 9):
        await _add_candidate(session, wl_server, inbound_id)
    _live(monkeypatch, 7, 8, 9)
    await _choose(session, wl_server, 8)
    panel.fail_steps = {"update"}  # 8 прикреплён, параметры не применены
    await whitelist.process_due(session, panel)
    assert _wl_state(panel, wl_server).inbound_ids == [7, 8]

    await _choose(session, wl_server, 9)
    panel.fail_steps = set()
    # Backoff прежней попытки сохраняется и для новой цели.
    assert await whitelist.process_due(session, panel) == 0
    assert _wl_state(panel, wl_server).inbound_ids == [7, 8]
    progress = await whitelist.placement_progress(session)
    assert progress.inbound_id == 9 and progress.failed == 1

    await _expire_backoff(session, user)
    assert await whitelist.process_due(session, panel) == 1
    assert _wl_state(panel, wl_server).inbound_ids == [9]
    assert panel.detached[-1] == (wl_server.id, EMAIL, (7, 8))
    # Устаревшая цель 8 больше не прикрепляется: ни очередью, ни прямым повтором.
    await whitelist.sync_user(session, user.id, panel)
    assert [ids for *_, ids in panel.attached] == [(7,), (8,), (9,)]
    assert await _placed(session, user, wl_server, 9)
    assert await _links(session, user) == [(9, "attached", "service")]


async def test_purchase_and_renewal_during_unfinished_move_lose_nothing(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _pay(session, user, panel)
    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)
    await _choose(session, wl_server, 8)
    panel.fail_steps = {"detach"}
    await whitelist.process_due(session, panel)
    assert _wl_state(panel, wl_server).inbound_ids == [7, 8]
    client = await session.scalar(select(VpnClient).where(VpnClient.user_id == user.id))
    expires_before = client.expires_at

    payment, result = await _buy(session, user, panel, 25)
    assert result.applied
    await session.refresh(payment)
    # Квота с покупкой применена на клиенте, хотя перенос ещё не завершён.
    assert payment.apply_pending_version is None
    assert _wl_state(panel, wl_server).total_bytes == 35 * GIB
    await _pay(session, user, panel)
    await session.refresh(client)
    assert whitelist._aware(client.expires_at) > whitelist._aware(expires_before)
    assert _wl_state(panel, wl_server).inbound_ids == [7, 8]

    panel.fail_steps = set()
    await _expire_backoff(session, user)
    await whitelist.process_due(session, panel)
    state = _wl_state(panel, wl_server)
    account = await _account(session, user)
    assert state.inbound_ids == [8] and state.enable
    assert (account.free_bytes, account.paid_bytes) == (10 * GIB, 25 * GIB)
    assert state.total_bytes == 35 * GIB
    assert await _ledger_count(session, user.id, "free_grant") == 2
    assert await _ledger_count(session, user.id, "purchase") == 1
    assert await _placed(session, user, wl_server, 8)


# --- Истёкшая подписка, блокировка, бессрочный доступ ----------------------------------


@pytest.mark.parametrize("case", ["expired", "blocked", "lifetime"])
async def test_access_state_is_kept_by_the_move(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch, case  # noqa: F811
):
    if case == "lifetime":
        vpn_client.expires_at = None
        vpn_client.is_active = True
        await session.commit()
        await whitelist.run_rollout(
            session, panel, include_ambiguous=False, actor_user_id=None
        )
    else:
        await _pay(session, user, panel)
    if case == "expired":
        vpn_client.expires_at = datetime.now(UTC) - timedelta(days=1)
        await session.commit()
        await whitelist.after_access_change(session, user.id, panel)
    if case == "blocked":
        await whitelist.set_admin_block(session, user.id, True, None, panel)
    before = await _snapshot(session, user, panel, wl_server)
    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)
    await _choose(session, wl_server, 8)

    assert await whitelist.process_due(session, panel) == 1
    state = _wl_state(panel, wl_server)
    assert state.inbound_ids == [8]
    assert await _snapshot(session, user, panel, wl_server) == before
    if case == "lifetime":
        assert (state.total_bytes, state.expiry_ms, state.enable) == (0, 0, True)
    else:
        assert not state.enable  # перенос не включает истёкшего/заблокированного
    if case == "blocked":
        assert (await _account(session, user)).admin_blocked
        await whitelist.set_admin_block(session, user.id, False, None, panel)
        assert _wl_state(panel, wl_server).enable
    if case == "expired":
        await _pay(session, user, panel)
        assert _wl_state(panel, wl_server).enable
        assert _wl_state(panel, wl_server).inbound_ids == [8]


# --- flow цели ------------------------------------------------------------------------


async def test_flow_change_and_clearing_on_current_target(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _pay(session, user, panel)
    assert _wl_state(panel, wl_server).inbound_flows == {7: ""}
    _live(monkeypatch, 7)
    target = whitelist.target_inbound(await whitelist.get_active_server(session))
    for flow in ("xtls-rprx-vision", None):
        target.flow = flow
        await session.commit()
        assert await whitelist.process_due(session, panel) == 1
        assert _wl_state(panel, wl_server).inbound_flows == {7: flow or ""}
        assert await _placed(session, user, wl_server, 7, flow or "")
        assert await whitelist.process_due(session, panel) == 0
    assert _wl_state(panel, wl_server).inbound_ids == [7]


@pytest.mark.parametrize("filter_supported", [True, False])
async def test_flow_during_coexistence_of_old_and_new_target(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch,  # noqa: F811
    filter_supported,
):
    server = await whitelist.get_active_server(session)
    whitelist.target_inbound(server).flow = "xtls-rprx-vision"
    await session.commit()
    await _pay(session, user, panel)
    assert _wl_state(panel, wl_server).inbound_flows == {7: "xtls-rprx-vision"}
    panel.update_filter_supported = filter_supported
    await _add_candidate(session, wl_server, 8)  # без flow: прежний flow очищается
    _live(monkeypatch, 7, vless_reality(8, network="xhttp"))
    await _choose(session, wl_server, 8)
    panel.fail_steps = {"detach"}  # временное сосуществование старой и новой цели
    await whitelist.process_due(session, panel)
    flows = _wl_state(panel, wl_server).inbound_flows
    if filter_supported:
        # 3.3+: update фильтруется — прежняя цель сохраняет свой flow до снятия.
        assert flows == {7: "xtls-rprx-vision", 8: ""}
    else:
        # 3.2.0: flow — общая запись; прежняя цель получает flow новой. Доступ по
        # старой ссылке с vision до снятия привязки не гарантируется.
        assert flows == {7: "", 8: ""}
    panel.fail_steps = set()
    await _expire_backoff(session, user)
    await whitelist.process_due(session, panel)
    assert _wl_state(panel, wl_server).inbound_flows == {8: ""}
    assert await _placed(session, user, wl_server, 8, "")


# --- Чужие привязки и учёты до миграции -----------------------------------------------


@pytest.mark.parametrize("filter_supported", [True, False])
async def test_foreign_attachment_is_never_detached(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch,  # noqa: F811
    filter_supported,
):
    await _pay(session, user, panel)
    # Администратор вручную прикрепил клиента ещё к inbound 5 со своим flow.
    state = _wl_state(panel, wl_server)
    state.inbound_ids = [5, 7]
    state.inbound_flows[5] = "xtls-rprx-vision"
    panel.update_filter_supported = filter_supported
    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)
    await _choose(session, wl_server, 8)

    assert await whitelist.process_due(session, panel) == 1
    state = _wl_state(panel, wl_server)
    assert state.inbound_ids == [5, 8]
    assert panel.detached == [(wl_server.id, EMAIL, (7,))]
    assert await _placed(session, user, wl_server, 8)
    # 3.2.0 переписывает flow общей записи во всех привязках (ограничение панели).
    assert state.inbound_flows[5] == ("xtls-rprx-vision" if filter_supported else "")
    progress = await whitelist.placement_progress(session)
    assert progress.complete and progress.placed == 1


async def test_legacy_attachment_of_unknown_origin_is_kept_until_claimed(
    session, user, admin, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _pay(session, user, panel)
    # Учёт до миграции a4b5c6d7e8f9: ни подтверждённого размещения, ни строк привязок.
    account = await _account(session, user)
    account.placement_server_id = account.placement_inbound_id = None
    account.placement_flow = account.placement_at = None
    for row in (await session.scalars(select(WhitelistPlacement))).all():
        await session.delete(row)
    await session.commit()

    # Очередь один раз проверяет размещение; происхождение 7 не объявляется своим.
    assert await whitelist.process_due(session, panel) == 1
    assert await _placed(session, user, wl_server, 7)
    assert await _links(session, user) == []
    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)
    await _choose(session, wl_server, 8)
    assert await whitelist.process_due(session, panel) == 1
    assert _wl_state(panel, wl_server).inbound_ids == [7, 8]
    assert panel.detached == []
    assert await _links(session, user) == [(8, "attached", "service")]

    with pytest.raises(whitelist.WhitelistError, match="текущая цель"):
        await whitelist.claim_inbound(session, 8, actor_user_id=admin.id, reason="тест")
    assert await whitelist.claim_inbound(
        session, 7, actor_user_id=admin.id, reason="7 был целью услуги"
    ) == 1
    progress = await whitelist.placement_progress(session)
    assert progress.stale_links == 1 and progress.pending == 1
    assert await whitelist.process_due(session, panel) == 1
    assert _wl_state(panel, wl_server).inbound_ids == [8]
    assert await _links(session, user) == [(8, "attached", "service")]
    # Повторное признание после снятия ничего не создаёт навсегда: строка снимется.
    assert await whitelist.claim_inbound(session, 7, actor_user_id=admin.id, reason="r") == 1
    assert await whitelist.process_due(session, panel) == 1
    assert panel.detached == [(wl_server.id, EMAIL, (7,))]
    assert await _links(session, user) == [(8, "attached", "service")]


# --- Расход, отрицательная точка и неопределённые события ------------------------------


async def test_move_keeps_uncertain_event_negative_checkpoint_and_available_volume(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _baseline(session, user, panel, wl_server, 2, 15, used_gb=100)
    panel.read_fail_server_ids.add(wl_server.id)
    await _pay(session, user, panel, now=_ago(30))
    panel.consume(wl_server.id, EMAIL, 5 * GIB, at=_ago(20))
    panel.read_fail_server_ids.clear()
    await whitelist.user_overview(session, user.id, panel)
    await whitelist.process_due(session, panel)
    events = await whitelist.list_open_events(session, user.id)
    assert [e.status for e in events] == ["uncertain"]
    # Внешний сброс счётчика: новая эпоха с отрицательной точкой.
    panel.reset_traffic(wl_server.id, EMAIL)
    await whitelist.sync_user(session, user.id, panel)
    account = await _account(session, user)
    assert account.usage_checkpoint_bytes < 0
    available = _available(panel, wl_server)
    assert available == 20 * GIB
    before = await _snapshot(session, user, panel, wl_server)
    anchors = [(e.anchor_min_bytes, e.anchor_max_bytes, e.status) for e in events]

    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)
    await _choose(session, wl_server, 8)
    assert await whitelist.process_due(session, panel) == 1

    assert _wl_state(panel, wl_server).inbound_ids == [8]
    assert await _snapshot(session, user, panel, wl_server) == before
    assert _available(panel, wl_server) == available
    events = await whitelist.list_open_events(session, user.id)
    assert [(e.anchor_min_bytes, e.anchor_max_bytes, e.status) for e in events] == anchors
    assert await _ledger_count(session, user.id, "usage_rebase") == 1


async def test_counter_recreated_by_detach_does_not_add_quota(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _pay(session, user, panel)
    panel.consume(wl_server.id, EMAIL, 4 * GIB)
    await whitelist.user_overview(session, user.id, panel)
    available = _available(panel, wl_server)
    assert available == 6 * GIB
    # Защитная модель: панель, пересоздающая строку статистики при detach.
    panel.detach_recreates_traffic = True
    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)
    await _choose(session, wl_server, 8)

    assert await whitelist.process_due(session, panel) == 1
    state = _wl_state(panel, wl_server)
    assert state.inbound_ids == [8] and state.used_bytes == 0
    assert _available(panel, wl_server) == available  # не 10 ГиБ
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (6 * GIB, 0)
    assert await _ledger_count(session, user.id, "usage_rebase") == 1
    assert await _placed(session, user, wl_server, 8)


# --- Фоновая сверка размещения ---------------------------------------------------------


async def test_reconcile_detects_actual_placement_drift_and_queue_restores_it(
    session, user, vpn_client, service_on, panel, wl_server  # noqa: F811
):
    await _pay(session, user, panel)
    status = whitelist.ReconcileStatus()
    report = await whitelist.reconcile_cycle(session, panel, status=status)
    assert report.changed == 0

    # Клиента сняли с целевого inbound на панели вручную.
    state = _wl_state(panel, wl_server)
    state.inbound_ids = []
    state.inbound_flows = {}
    report = await whitelist.reconcile_cycle(session, panel, status=status)
    assert report.changed == 1
    assert not await _placed(session, user, wl_server, 7)
    assert await whitelist.process_due(session, panel) == 1
    assert _wl_state(panel, wl_server).inbound_ids == [7]
    assert await _placed(session, user, wl_server, 7)

    # flow клиента на целевом inbound изменили на панели.
    _wl_state(panel, wl_server).inbound_flows[7] = "xtls-rprx-vision"
    report = await whitelist.reconcile_cycle(session, panel, status=status)
    assert report.changed == 1
    assert await whitelist.process_due(session, panel) == 1
    assert _wl_state(panel, wl_server).inbound_flows == {7: ""}


async def test_reconcile_keeps_backoff_of_unfinished_move(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _pay(session, user, panel)
    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)
    await _choose(session, wl_server, 8)
    panel.fail_steps = {"detach"}
    await whitelist.process_due(session, panel)
    account = await _account(session, user)
    retry_at, version = account.next_sync_at, account.desired_version
    report = await whitelist.reconcile_cycle(session, panel, status=whitelist.ReconcileStatus())
    assert report.changed == 1  # прежняя привязка услуги ещё на панели
    account = await _account(session, user)
    assert (account.next_sync_at, account.desired_version) == (retry_at, version)
    assert await whitelist.process_due(session, panel) == 0


# --- Удаление подписки ----------------------------------------------------------------


async def test_forgotten_panel_client_clears_placement(
    session, user, vpn_client, service_on, panel, wl_server  # noqa: F811
):
    await _pay(session, user, panel)
    await whitelist.forget_panel_client(session, user.id)
    await session.commit()
    account = await _account(session, user)
    assert account.panel_email is None and account.placement_inbound_id is None
    assert await _links(session, user) == []
    assert (await whitelist.placement_progress(session)).total == 0


# --- Тексты администратора ------------------------------------------------------------


async def test_admin_texts_show_actual_progress_not_server_readiness(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _pay(session, user, panel)
    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)
    await _choose(session, wl_server, 8)
    summary = await whitelist.admin_summary(session)
    home = texts.admin_whitelist_home(
        await whitelist.get_config(session), wl_server, summary, []
    )
    assert "Размещение на inbound 8 (flow: нет): подтверждено 0 из 1; ожидает 1; ошибка 0" in home
    assert "Перенос клиентов не завершён" in home

    panel.fail_steps = {"detach"}
    await whitelist.process_due(session, panel)
    placement = await whitelist.user_placement(session, user.id)
    lines = "\n".join(texts.admin_whitelist_placement(placement))
    assert "не подтверждено: цель — inbound 8" in lines
    assert "7 (снимается)" in lines and "8 (подтверждена)" in lines
    summary = await whitelist.admin_summary(session)
    assert summary.placement.failed == 1

    panel.fail_steps = set()
    await _expire_backoff(session, user)
    await whitelist.process_due(session, panel)
    summary = await whitelist.admin_summary(session)
    home = texts.admin_whitelist_home(
        await whitelist.get_config(session), wl_server, summary, []
    )
    assert "подтверждено 1 из 1; ожидает 0; ошибка 0" in home
    assert "Перенос клиентов не завершён" not in home


async def test_account_without_vpn_client_does_not_block_queue(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    await _pay(session, user, panel)
    account = await _account(session, user)
    await session.delete(vpn_client)
    await session.commit()
    _live(monkeypatch, 7)
    server = await whitelist.get_active_server(session)
    whitelist.target_inbound(server).flow = "xtls-rprx-vision"
    await session.commit()
    assert await whitelist.process_due(session, panel) == 0
    account = await _account(session, user)
    # Пропуск с backoff: учёт не занимает очередь каждые 30 с.
    retry_at = whitelist._aware(account.next_sync_at)
    assert retry_at is not None and retry_at > datetime.now(UTC)


async def test_panel_error_type_is_reported(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch  # noqa: F811
):
    """detach ошибкой панели не превращается в исключение очереди."""
    await _pay(session, user, panel)
    await _add_candidate(session, wl_server, 8)
    _live(monkeypatch, 7, 8)
    await _choose(session, wl_server, 8)
    panel.fail_steps = {"detach"}
    outcome = await whitelist.sync_user(session, user.id, panel)
    assert outcome.applied and outcome.pending and outcome.placement_pending
    assert "mock failure at detach" in (outcome.error or "")
    with pytest.raises(PanelUpdateError):
        await panel.detach_quota_client(wl_server, EMAIL, [7])
    account = await session.scalar(
        select(WhitelistAccount).where(WhitelistAccount.user_id == user.id)
    )
    assert account.last_error.startswith("Перенос: прежняя привязка [7] не снята")

from __future__ import annotations

import json
import logging
from typing import Any

from app.db.models import ClientServerMapping, Server
from app.services.panel_updater import (
    PanelUpdateError,
    QuotaClientState,
    QuotaTarget,
    ServerProvision,
)
from app.services.xui_client import XuiClient, XuiError
from app.services.xui_payloads import (
    build_client_object,
    build_client_record,
    client_identifier,
    client_record_body,
    merge_client_record_for_update,
)

logger = logging.getLogger(__name__)


class XuiPanelUpdater:
    """Реализация PanelUpdater поверх XuiClient.

    На каждый сервер создаётся отдельный XuiClient с его реквизитами.
    Ошибки 3x-ui транслируются в PanelUpdateError, чтобы billing мог их учесть.

    На панелях 3x-ui >= 3.2.x используется новый client-API (глобальный клиент по
    email, привязанный к нескольким inbound'ам). На старых панелях — обратная
    совместимость через per-inbound addClient/updateClient.
    """

    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = timeout

    def _client(self, server: Server) -> XuiClient:
        return XuiClient(
            base_url=server.panel_url,
            username=server.username,
            password=server.password,
            timeout=self._timeout,
        )

    async def provision_server(
        self, server: Server, spec: ServerProvision, expiry_ms: int
    ) -> None:
        inbound_ids = [i.inbound_id for i in spec.inbounds]
        flow = next((i.flow for i in spec.inbounds if i.flow), None)
        logger.info(
            "provision_server: server=%s email=%s inbounds=%s",
            server.id,
            spec.email,
            inbound_ids,
        )
        async with self._client(server) as client:
            try:
                # Validate the configured targets before any panel mutation.
                live = {item["id"]: item for item in await client.list_inbounds()}
                unavailable = [
                    i for i in inbound_ids
                    if i not in live or live[i].get("enable") is False
                ]
                if not inbound_ids or unavailable:
                    raise XuiError(
                        f"Недоступные inbound на сервере {server.id}: {unavailable}. "
                        f"Обновите список командой /importinbounds {server.id}"
                    )
                if await client.supports_clients_api():
                    await self._provision_new(
                        client, spec, inbound_ids, flow, expiry_ms,
                        live_inbound_ids=set(live),
                    )
                else:
                    await self._provision_legacy(
                        client, spec, expiry_ms
                    )
            except XuiError as exc:
                logger.warning(
                    "Ошибка провижининга на сервере %s: %s", server.id, exc
                )
                raise PanelUpdateError(str(exc)) from exc

    async def _provision_new(
        self,
        client: XuiClient,
        spec: ServerProvision,
        inbound_ids: list[int],
        flow: str | None,
        expiry_ms: int,
        *,
        live_inbound_ids: set[int] | None = None,
    ) -> None:
        existing_record = await client.get_client_record(spec.email)
        if (
            existing_record is None
            and spec.sub_id
            and spec.sub_id != spec.email
        ):
            existing_record = await client.find_client_record_by_sub_id(spec.sub_id)

        if existing_record is None:
            client_obj = build_client_record(
                client_uuid=spec.client_uuid,
                password=spec.password,
                email=spec.email,
                sub_id=spec.sub_id,
                expiry_ms=expiry_ms,
                flow=flow,
                tg_id=spec.telegram_id or 0,
            )
            await client.create_client_record(client_obj, inbound_ids)
            return

        existing_body = client_record_body(existing_record)
        if existing_body is None:
            raise XuiError(
                f"Некорректный ответ панели для клиента {spec.email}"
            )
        panel_email = str(existing_body.get("email") or spec.email)
        client_obj = merge_client_record_for_update(
            existing_body,
            email=panel_email,
            sub_id=spec.sub_id,
            expiry_ms=expiry_ms,
            flow=flow,
            tg_id=spec.telegram_id,
        )
        existing_inbound_ids = [
            int(i)
            for i in (existing_record.get("inboundIds") or [])
            if isinstance(i, int) and (live_inbound_ids is None or i in live_inbound_ids)
        ]
        merged_inbound_ids = sorted(set(existing_inbound_ids) | set(inbound_ids))
        await client.update_client_record(
            panel_email, client_obj, inbound_ids=merged_inbound_ids
        )
        missing = sorted(set(inbound_ids) - set(existing_inbound_ids))
        if missing:
            await client.attach_client_record(panel_email, missing)
            verified = await client.get_client_record(panel_email)
            if verified is None or not set(inbound_ids).issubset(
                set(verified.get("inboundIds") or [])
            ):
                raise XuiError(f"Панель не подтвердила inbound-привязки клиента {panel_email}")

    async def _provision_legacy(
        self, client: XuiClient, spec: ServerProvision, expiry_ms: int
    ) -> None:
        """Старые панели: отдельный клиент в каждом inbound (per-inbound email)."""
        for inbound in spec.inbounds:
            # Email is SubHub's global identity. 3x-ui scopes legacy clients to
            # an inbound, so the same email is safe and must not be suffixed.
            email = spec.email
            existing = await client.get_client(
                inbound.inbound_id,
                client_uuid=spec.client_uuid,
                email=email,
            )
            if existing is not None:
                identifier = client_identifier(
                    inbound.protocol,
                    client_uuid=spec.client_uuid,
                    email=email,
                )
                await client.update_client_expiry(
                    inbound_id=inbound.inbound_id,
                    client_uuid=spec.client_uuid,
                    email=email,
                    expiry_ms=expiry_ms,
                    identifier=identifier,
                    tg_id=spec.telegram_id,
                )
                continue
            client_obj = build_client_object(
                inbound.protocol,
                client_uuid=spec.client_uuid,
                password=spec.password,
                email=email,
                sub_id=spec.sub_id,
                expiry_ms=expiry_ms,
                flow=inbound.flow,
                method=inbound.method,
                tg_id=str(spec.telegram_id) if spec.telegram_id is not None else "",
            )
            await client.add_client(inbound.inbound_id, client_obj)

    # --- Клиент с учётом трафика (whitelist-сервер) -------------------------

    @staticmethod
    async def _require_clients_api(client: XuiClient, server: Server) -> None:
        if not await client.supports_clients_api():
            raise XuiError(
                f"Панель сервера {server.id} не поддерживает clients API "
                "(нужна 3x-ui 3.2 или новее): учёт трафика невозможен"
            )

    @staticmethod
    async def _read_quota_state(
        client: XuiClient, email: str
    ) -> QuotaClientState | None:
        record = await client.get_client_record(email)
        if record is None:
            return None
        body = client_record_body(record)
        if body is None:
            raise XuiError(f"Некорректный ответ панели для клиента {email}")
        panel_email = str(body.get("email") or email)
        traffic = await client.get_client_usage(panel_email)
        used: int | None = None
        row_id: int | None = None
        last_online: int | None = None
        if traffic is not None:
            used = int(traffic.get("up") or 0) + int(traffic.get("down") or 0)
            raw_id = traffic.get("id")
            row_id = raw_id if type(raw_id) is int else None
            # client_traffics.last_online: панель сдвигает его при каждом
            # ненулевом приросте up/down (3x-ui >= 3.2). Нет/0 — неизвестно.
            raw_online = traffic.get("lastOnline")
            if type(raw_online) is int and raw_online > 0:
                last_online = raw_online
        total = body.get("totalGB") or 0
        expiry = body.get("expiryTime") or 0
        if type(total) is not int or type(expiry) is not int:
            raise XuiError(f"Некорректные лимиты клиента {panel_email}")
        return QuotaClientState(
            email=panel_email,
            enable=bool(body.get("enable", True)),
            total_bytes=total,
            expiry_ms=expiry,
            inbound_ids=[
                int(i) for i in (record.get("inboundIds") or []) if type(i) is int
            ],
            used_bytes=used,
            traffic_row_id=row_id,
            last_online_ms=last_online,
        )

    async def read_quota_client(
        self, server: Server, email: str
    ) -> QuotaClientState | None:
        async with self._client(server) as client:
            try:
                await self._require_clients_api(client, server)
                return await self._read_quota_state(client, email)
            except XuiError as exc:
                raise PanelUpdateError(str(exc)) from exc

    async def read_quota_clients(
        self, server: Server, emails: list[str]
    ) -> dict[str, QuotaClientState | None | PanelUpdateError]:
        """Сверка расхода пачкой в одной сессии панели (фоновая проверка).

        Список inbound'ов читается один раз на пачку: по нему для каждого клиента
        заполняется flow в его привязках (сверка размещения). Если список не
        прочитался, flow неизвестен (None), расход сверяется как обычно.
        """
        result: dict[str, QuotaClientState | None | PanelUpdateError] = {}
        async with self._client(server) as client:
            try:
                await self._require_clients_api(client, server)
            except XuiError as exc:
                return {email: PanelUpdateError(str(exc)) for email in emails}
            try:
                inbounds: dict[int, dict[str, Any]] | None = {
                    item["id"]: item for item in await client.list_inbounds()
                }
            except XuiError as exc:
                logger.info("Пакетное чтение: список inbound'ов не прочитан: %s", exc)
                inbounds = None
            for email in emails:
                try:
                    state = await self._read_quota_state(client, email)
                except XuiError as exc:
                    result[email] = PanelUpdateError(str(exc))
                    continue
                if state is not None and inbounds is not None:
                    state.inbound_flows = _client_flows(inbounds, state)
                result[email] = state
        return result

    async def apply_quota_client(
        self, server: Server, spec: ServerProvision, target: QuotaTarget
    ) -> QuotaClientState:
        """Задаёт абсолютные totalGB/enable/expiry и размещение; проверяет чтением.

        Повтор с тем же ``target`` идемпотентен: квота не прибавляется, а
        выставляется заново. Секреты, Telegram ID, subId и дополнительные поля
        существующего клиента сохраняются (read-modify-write).

        Порядок (3x-ui 3.2–3.9, ``ClientService.Attach/Update``): недостающие целевые
        inbound'ы прикрепляются (attach копирует общую запись и не трогает счётчик),
        затем ``clients/update`` с фильтром ``inboundIds`` применяет параметры:
        сначала к прочим привязкам с их собственным flow, последним — к цели с её
        явным flow (``None`` — без flow). 3.2.0 фильтр игнорирует и пишет flow тела
        во все привязки — последним остаётся flow цели. Прочие привязки не
        снимаются. Проверка: квота, срок, enable, привязка к цели и flow клиента в
        настройках целевого inbound'а (по ним строят конфиг Xray и ссылку SubHub).
        """
        if target.total_bytes < 0:
            raise PanelUpdateError("Отрицательная квота трафика")
        inbound_ids = [i.inbound_id for i in spec.inbounds]
        target_flows = {i.inbound_id: i.flow or "" for i in spec.inbounds}
        async with self._client(server) as client:
            try:
                live = {item["id"]: item for item in await client.list_inbounds()}
                unavailable = [
                    i for i in inbound_ids
                    if i not in live or live[i].get("enable") is False
                ]
                if not inbound_ids or unavailable:
                    raise XuiError(
                        f"Недоступные inbound на сервере {server.id}: {unavailable}. "
                        "Повторите синхронизацию сервера в админке"
                    )
                await self._require_clients_api(client, server)
                record = await client.get_client_record(spec.email)
                attached: list[int] = []
                plan: dict[str, list[int]] = {}
                if record is None:
                    client_obj = build_client_record(
                        client_uuid=spec.client_uuid,
                        password=spec.password,
                        email=spec.email,
                        sub_id=spec.sub_id,
                        expiry_ms=target.expiry_ms,
                        flow=next((f for f in target_flows.values() if f), None),
                        total_gb=target.total_bytes,
                        tg_id=spec.telegram_id or 0,
                        enable=target.enable,
                        quota_policy=True,
                    )
                    await client.create_client_record(client_obj, inbound_ids)
                    panel_email = spec.email
                    attached = sorted(inbound_ids)
                else:
                    body = client_record_body(record)
                    if body is None:
                        raise XuiError(
                            f"Некорректный ответ панели для клиента {spec.email}"
                        )
                    panel_email = str(body.get("email") or spec.email)
                    current = [
                        int(i) for i in (record.get("inboundIds") or [])
                        if type(i) is int and i in live
                    ]
                    missing = sorted(set(inbound_ids) - set(current))
                    if missing:
                        await client.attach_client_record(panel_email, missing)
                        attached = missing
                    # Прочие привязки (прежняя цель услуги, чужие) сохраняют свой flow.
                    for other in sorted(set(current) - set(inbound_ids)):
                        own = _inbound_client_flow(live[other], panel_email)
                        flow = str(body.get("flow") or "") if own is None else own
                        plan.setdefault(flow, []).append(other)
                    target_plan: dict[str, list[int]] = {}
                    for inbound_id in inbound_ids:
                        target_plan.setdefault(target_flows[inbound_id], []).append(inbound_id)
                    for flow, ids in [*plan.items(), *target_plan.items()]:
                        client_obj = merge_client_record_for_update(
                            body,
                            email=panel_email,
                            sub_id=spec.sub_id,
                            expiry_ms=target.expiry_ms,
                            enable=target.enable,
                            flow=flow,
                            tg_id=spec.telegram_id,
                            total_bytes=target.total_bytes,
                            quota_policy=True,
                            explicit_flow=True,
                        )
                        await client.update_client_record(
                            panel_email, client_obj, inbound_ids=sorted(ids)
                        )
                state = await self._read_quota_state(client, panel_email)
                _verify_quota_state(panel_email, state, target, inbound_ids)
                assert state is not None
                flows: dict[int, str | None] = {
                    inbound_id: _inbound_client_flow(
                        await client.get_inbound(inbound_id), panel_email
                    )
                    for inbound_id in inbound_ids
                }
                _verify_quota_state(
                    panel_email, state, target, inbound_ids,
                    flows=flows, expected_flows=target_flows,
                )
                for flow, ids in plan.items():
                    for other in ids:
                        flows[other] = await _other_flow(client, server, panel_email, other, flow)
                state.inbound_flows = {k: v for k, v in flows.items() if v is not None}
                state.attached_inbound_ids = attached
                return state
            except XuiError as exc:
                logger.warning(
                    "Ошибка применения квоты на сервере %s: %s", server.id, exc
                )
                raise PanelUpdateError(str(exc)) from exc

    async def detach_quota_client(
        self, server: Server, email: str, inbound_ids: list[int]
    ) -> QuotaClientState | None:
        """Снимает привязки клиента к ``inbound_ids`` и подтверждает это чтением.

        ``POST clients/{email}/detach`` (3x-ui 3.2–3.9, ``DetachByEmailMany``):
        отправляются только реально привязанные id; строка статистики остаётся.
        """
        async with self._client(server) as client:
            try:
                await self._require_clients_api(client, server)
                record = await client.get_client_record(email)
                if record is None:
                    return None
                body = client_record_body(record)
                panel_email = str((body or {}).get("email") or email)
                current = {
                    int(i) for i in (record.get("inboundIds") or []) if type(i) is int
                }
                present = sorted(set(inbound_ids) & current)
                if present:
                    await client.detach_client_record(panel_email, present)
                state = await self._read_quota_state(client, panel_email)
                left = sorted(set(inbound_ids) & set(state.inbound_ids if state else []))
                if left:
                    raise XuiError(
                        f"Панель не подтвердила снятие привязок клиента {panel_email}: "
                        f"остались inbound {left}"
                    )
                return state
            except XuiError as exc:
                logger.warning(
                    "Ошибка снятия привязки на сервере %s: %s", server.id, exc
                )
                raise PanelUpdateError(str(exc)) from exc

    async def update_expiry(
        self, server: Server, mapping: ClientServerMapping, expiry_ms: int
    ) -> None:
        async with self._client(server) as client:
            try:
                if await client.supports_clients_api():
                    existing_record = await client.get_client_record(mapping.email)
                    if existing_record is None:
                        raise XuiError(
                            f"Клиент {mapping.email} не найден на панели"
                        )
                    existing_body = client_record_body(existing_record)
                    if existing_body is None:
                        raise XuiError(
                            f"Некорректный ответ панели для клиента {mapping.email}"
                        )
                    client_obj = merge_client_record_for_update(
                        existing_body,
                        email=mapping.email,
                        sub_id=mapping.sub_id or mapping.email,
                        expiry_ms=expiry_ms,
                    )
                    await client.update_client_record(
                        mapping.email, client_obj
                    )
                else:
                    identifier = client_identifier(
                        mapping.protocol,
                        client_uuid=mapping.client_uuid,
                        email=mapping.email,
                    )
                    await client.update_client_expiry(
                        inbound_id=mapping.inbound_id,
                        client_uuid=mapping.client_uuid,
                        email=mapping.email,
                        expiry_ms=expiry_ms,
                        identifier=identifier,
                    )
            except XuiError as exc:
                logger.warning(
                    "Ошибка обновления клиента на сервере %s: %s", server.id, exc
                )
                raise PanelUpdateError(str(exc)) from exc

    async def delete_client(
        self, server: Server, mappings: list[ClientServerMapping]
    ) -> None:
        if not mappings:
            return
        primary = mappings[0]
        async with self._client(server) as client:
            try:
                if await client.supports_clients_api():
                    await self._delete_new(client, primary)
                else:
                    inbound_ids = sorted({m.inbound_id for m in mappings})
                    await self._delete_from_inbounds(
                        client,
                        inbound_ids,
                        [primary.client_uuid, primary.email, primary.sub_id],
                    )
            except XuiError as exc:
                logger.warning(
                    "Ошибка удаления клиента на сервере %s: %s", server.id, exc
                )
                raise PanelUpdateError(str(exc)) from exc

    async def _delete_new(
        self, client: XuiClient, mapping: ClientServerMapping
    ) -> None:
        record = await client.get_client_record(mapping.email)
        if record is None and mapping.sub_id:
            record = await client.find_client_record_by_sub_id(mapping.sub_id)
        if record is None:
            logger.info("delete_client: клиент %s уже отсутствует", mapping.email)
            return
        inbound_ids = [
            int(i) for i in (record.get("inboundIds") or []) if isinstance(i, int)
        ]
        if not inbound_ids:
            inbound_ids = [mapping.inbound_id]
        existing_body = client_record_body(record)
        panel_email = (
            str(existing_body.get("email") or "")
            if existing_body is not None
            else ""
        )
        await self._delete_from_inbounds(
            client,
            inbound_ids,
            [panel_email, mapping.email, mapping.client_uuid, mapping.sub_id],
        )

    async def _delete_from_inbounds(
        self,
        client: XuiClient,
        inbound_ids: list[int],
        identifiers: list[str | None],
    ) -> None:
        candidates = list(dict.fromkeys(i for i in identifiers if i))
        if not candidates:
            raise XuiError("Нет идентификатора клиента для удаления")
        for inbound_id in inbound_ids:
            last_error: XuiError | None = None
            for identifier in candidates:
                try:
                    await client.del_client(inbound_id, identifier)
                    break
                except XuiError as exc:
                    if _is_missing_client_error(str(exc)):
                        logger.info(
                            "delete_client: inbound=%s identifier=%s уже отсутствует",
                            inbound_id,
                            identifier,
                        )
                        break
                    last_error = exc
            else:
                raise last_error or XuiError(
                    f"Не удалось удалить клиента из inbound {inbound_id}"
                )


def _inbound_client_flow(inbound: dict[str, Any] | None, email: str) -> str | None:
    """flow клиента в ``settings.clients[]`` inbound'а; None — клиента там нет."""
    if not isinstance(inbound, dict):
        return None
    raw = inbound.get("settings")
    if isinstance(raw, str):
        try:
            settings = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return None
    else:
        settings = raw if isinstance(raw, dict) else {}
    clients = settings.get("clients") if isinstance(settings, dict) else None
    for item in clients if isinstance(clients, list) else []:
        if isinstance(item, dict) and item.get("email") == email:
            return str(item.get("flow") or "")
    return None


async def _other_flow(
    client: XuiClient, server: Server, email: str, inbound_id: int, expected: str
) -> str | None:
    """flow прочей привязки после обновления (best-effort, для наблюдения).

    В 3x-ui 3.2.0 ``clients/update`` не принимает фильтр inbound'ов и пишет flow тела
    во все привязки общей записи клиента: flow чужой или прежней привязки может
    измениться. Изменение не отменяется (это контракт панели), а пишется в журнал.
    """
    try:
        actual = _inbound_client_flow(await client.get_inbound(inbound_id), email)
    except XuiError as exc:
        logger.info("flow привязки %s клиента %s не прочитан: %s", inbound_id, email, exc)
        return None
    if actual is not None and actual != expected:
        logger.warning(
            "Сервер %s: flow привязки клиента %s к inbound %s изменился (%s → %s): "
            "панель применила обновление общей записи ко всем привязкам",
            server.id, email, inbound_id, expected or "нет", actual or "нет",
        )
    return actual


def _client_flows(
    inbounds: dict[int, dict[str, Any]], state: QuotaClientState
) -> dict[int, str]:
    flows: dict[int, str] = {}
    for inbound_id in state.inbound_ids:
        flow = _inbound_client_flow(inbounds.get(inbound_id), state.email)
        if flow is not None:
            flows[inbound_id] = flow
    return flows


def _verify_quota_state(
    email: str,
    state: QuotaClientState | None,
    target: QuotaTarget,
    inbound_ids: list[int],
    *,
    flows: dict[int, str | None] | None = None,
    expected_flows: dict[int, str] | None = None,
) -> None:
    """Read-after-write: панель должна хранить ровно заданные значения."""
    if state is None:
        raise XuiError(f"Панель не подтвердила клиента {email}")
    problems: list[str] = []
    if state.total_bytes != target.total_bytes:
        problems.append(f"totalGB={state.total_bytes}, ожидалось {target.total_bytes}")
    if state.expiry_ms != target.expiry_ms:
        problems.append(f"expiryTime={state.expiry_ms}, ожидалось {target.expiry_ms}")
    if not set(inbound_ids).issubset(state.inbound_ids):
        problems.append(f"inbound={state.inbound_ids}, ожидалось {inbound_ids}")
    for inbound_id, expected in (expected_flows or {}).items():
        actual = (flows or {}).get(inbound_id)
        if actual is None:
            problems.append(f"клиента нет в настройках inbound {inbound_id}")
        elif actual != expected:
            problems.append(
                f"flow в inbound {inbound_id}={actual or 'нет'}, ожидалось {expected or 'нет'}"
            )
    # Включение подтверждается, если панель не отключила клиента по исчерпанию
    # квоты в промежутке между записью и чтением.
    if target.enable and not state.enable and not state.depleted:
        problems.append("клиент не включён")
    if not target.enable and state.enable:
        problems.append("клиент не отключён")
    if problems:
        raise XuiError(f"Панель не подтвердила квоту клиента {email}: " + "; ".join(problems))


def build_updater(timeout: float = 15.0) -> XuiPanelUpdater:
    return XuiPanelUpdater(timeout=timeout)


def _is_missing_client_error(message: str) -> bool:
    lowered = message.lower()
    markers = ("not found", "not exist", "no such", "не найден", "не существует")
    return any(marker in lowered for marker in markers)

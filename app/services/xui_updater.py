from __future__ import annotations

import logging

from app.db.models import ClientServerMapping, Server
from app.services.panel_updater import (
    PanelUpdateError,
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


def build_updater(timeout: float = 15.0) -> XuiPanelUpdater:
    return XuiPanelUpdater(timeout=timeout)


def _is_missing_client_error(message: str) -> bool:
    lowered = message.lower()
    markers = ("not found", "not exist", "no such", "не найден", "не существует")
    return any(marker in lowered for marker in markers)

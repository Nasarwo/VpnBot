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
                if await client.supports_clients_api():
                    await self._provision_new(
                        client, spec, inbound_ids, flow, expiry_ms
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
    ) -> None:
        existing_record = await client.get_client_record(spec.email)
        if existing_record is None:
            client_obj = build_client_record(
                client_uuid=spec.client_uuid,
                password=spec.password,
                email=spec.email,
                sub_id=spec.sub_id,
                expiry_ms=expiry_ms,
                flow=flow,
            )
            await client.create_client_record(client_obj, inbound_ids)
            return

        existing_body = client_record_body(existing_record)
        if existing_body is None:
            raise XuiError(
                f"Некорректный ответ панели для клиента {spec.email}"
            )
        client_obj = merge_client_record_for_update(
            existing_body,
            email=spec.email,
            sub_id=spec.sub_id,
            expiry_ms=expiry_ms,
            flow=flow,
        )
        existing_inbound_ids = [
            int(i)
            for i in (existing_record.get("inboundIds") or [])
            if isinstance(i, int)
        ]
        merged_inbound_ids = sorted(set(existing_inbound_ids) | set(inbound_ids))
        await client.update_client_record(
            spec.email, client_obj, inbound_ids=merged_inbound_ids
        )

    async def _provision_legacy(
        self, client: XuiClient, spec: ServerProvision, expiry_ms: int
    ) -> None:
        """Старые панели: отдельный клиент в каждом inbound (per-inbound email)."""
        for inbound in spec.inbounds:
            email = f"{spec.email}-{inbound.inbound_id}"
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


def build_updater(timeout: float = 15.0) -> XuiPanelUpdater:
    return XuiPanelUpdater(timeout=timeout)

from __future__ import annotations

import logging

from app.db.models import ClientServerMapping, Server
from app.services.panel_updater import PanelUpdateError, ProvisionTarget
from app.services.xui_client import XuiClient, XuiError
from app.services.xui_payloads import build_client_object, client_identifier

logger = logging.getLogger(__name__)


class XuiPanelUpdater:
    """Реализация PanelUpdater поверх XuiClient.

    На каждый сервер создаётся отдельный XuiClient с его реквизитами.
    Ошибки 3x-ui транслируются в PanelUpdateError, чтобы billing мог их учесть.
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

    async def update_expiry(
        self, server: Server, mapping: ClientServerMapping, expiry_ms: int
    ) -> None:
        async with self._client(server) as client:
            try:
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

    async def ensure_client(
        self, server: Server, target: ProvisionTarget, expiry_ms: int
    ) -> None:
        async with self._client(server) as client:
            try:
                existing = await client.get_client(
                    target.inbound_id,
                    client_uuid=target.client_uuid,
                    email=target.email,
                )
                if existing is not None:
                    identifier = client_identifier(
                        target.protocol,
                        client_uuid=target.client_uuid,
                        email=target.email,
                    )
                    await client.update_client_expiry(
                        inbound_id=target.inbound_id,
                        client_uuid=target.client_uuid,
                        email=target.email,
                        expiry_ms=expiry_ms,
                        identifier=identifier,
                    )
                    return
                client_obj = build_client_object(
                    target.protocol,
                    client_uuid=target.client_uuid,
                    password=target.password,
                    email=target.email,
                    sub_id=target.sub_id,
                    expiry_ms=expiry_ms,
                    flow=target.flow,
                    method=target.method,
                )
                await client.add_client(target.inbound_id, client_obj)
            except XuiError as exc:
                logger.warning(
                    "Ошибка создания клиента на сервере %s: %s", server.id, exc
                )
                raise PanelUpdateError(str(exc)) from exc


def build_updater(timeout: float = 15.0) -> XuiPanelUpdater:
    return XuiPanelUpdater(timeout=timeout)

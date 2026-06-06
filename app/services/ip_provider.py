from __future__ import annotations

import logging
from typing import Protocol

from app.db.models import ClientServerMapping, Server
from app.services.xui_client import XuiClient, XuiError

logger = logging.getLogger(__name__)


class IpProvider(Protocol):
    """Источник списка IP-адресов клиента (для антишеринг-мониторинга)."""

    async def get_ips(
        self, server: Server, mapping: ClientServerMapping
    ) -> list[str]:
        ...


class MockIpProvider:
    """Mock-провайдер для тестов: возвращает заранее заданные IP по server_id."""

    def __init__(self, ips_by_server: dict[int, list[str]] | None = None) -> None:
        self.ips_by_server = ips_by_server or {}

    async def get_ips(
        self, server: Server, mapping: ClientServerMapping
    ) -> list[str]:
        return list(self.ips_by_server.get(server.id, []))


class XuiIpProvider:
    """Реальный провайдер: берёт IP клиента из журнала панели 3x-ui."""

    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = timeout

    async def get_ips(
        self, server: Server, mapping: ClientServerMapping
    ) -> list[str]:
        async with XuiClient(
            base_url=server.panel_url,
            username=server.username,
            password=server.password,
            timeout=self._timeout,
        ) as client:
            try:
                return await client.get_client_ips(mapping.email)
            except XuiError as exc:
                logger.warning(
                    "Не удалось получить IP клиента на сервере %s: %s",
                    server.id,
                    exc,
                )
                return []


def build_ip_provider(timeout: float = 15.0) -> XuiIpProvider:
    return XuiIpProvider(timeout=timeout)

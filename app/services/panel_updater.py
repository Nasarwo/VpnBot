from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol as TypingProtocol

from app.db.enums import Protocol
from app.db.models import ClientServerMapping, Server


class PanelUpdateError(Exception):
    """Ошибка обновления клиента в панели."""


@dataclass(slots=True)
class ServerUpdateResult:
    server_id: int
    ok: bool
    error: str | None = None


@dataclass(slots=True)
class ProvisionTarget:
    """Описание клиента, которого нужно создать/обновить в конкретном inbound."""

    inbound_id: int
    protocol: Protocol
    client_uuid: str
    password: str
    email: str
    sub_id: str
    flow: str | None = None
    method: str | None = None


@dataclass(slots=True)
class ProvisionInbound:
    """Inbound сервера, к которому нужно привязать клиента."""

    inbound_id: int
    protocol: Protocol
    flow: str | None = None
    method: str | None = None


@dataclass(slots=True)
class ServerProvision:
    """Один клиент панели (глобальный по email), привязанный к её inbound'ам.

    Соответствует модели 3x-ui >= 3.2.x: email/subId уникальны в пределах панели,
    клиент привязывается сразу к нескольким inbound'ам разных протоколов.
    """

    email: str
    sub_id: str
    client_uuid: str
    password: str
    inbounds: list[ProvisionInbound]


class PanelUpdater(TypingProtocol):
    """Интерфейс работы с клиентом в панели.

    Реализуется как mock (для тестов/MVP) и как обёртка над XuiClient.
    """

    async def update_expiry(
        self, server: Server, mapping: ClientServerMapping, expiry_ms: int
    ) -> None:
        ...

    async def provision_server(
        self, server: Server, spec: ServerProvision, expiry_ms: int
    ) -> None:
        """Создаёт/обновляет клиента сразу для всех inbound'ов сервера."""
        ...

    async def delete_client(
        self, server: Server, mappings: list[ClientServerMapping]
    ) -> None:
        """Удаляет клиента с сервера по сохранённым привязкам."""
        ...


class MockPanelUpdater:
    """Mock-реализация: ничего не делает либо имитирует сбой нужных серверов."""

    def __init__(self, fail_server_ids: set[int] | None = None) -> None:
        self.fail_server_ids = fail_server_ids or set()
        self.calls: list[tuple[int, int]] = []
        self.provisioned: list[tuple[int, str, tuple[int, ...]]] = []
        self.deleted: list[tuple[int, tuple[str, ...]]] = []

    async def update_expiry(
        self, server: Server, mapping: ClientServerMapping, expiry_ms: int
    ) -> None:
        self.calls.append((server.id, expiry_ms))
        if server.id in self.fail_server_ids:
            raise PanelUpdateError(f"mock failure for server {server.id}")

    async def delete_client(
        self, server: Server, mappings: list[ClientServerMapping]
    ) -> None:
        self.deleted.append((server.id, tuple(m.email for m in mappings)))
        if server.id in self.fail_server_ids:
            raise PanelUpdateError(f"mock failure for server {server.id}")

    async def provision_server(
        self, server: Server, spec: ServerProvision, expiry_ms: int
    ) -> None:
        self.provisioned.append(
            (server.id, spec.email, tuple(i.inbound_id for i in spec.inbounds))
        )
        if server.id in self.fail_server_ids:
            raise PanelUpdateError(f"mock failure for server {server.id}")

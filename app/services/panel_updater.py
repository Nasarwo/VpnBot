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


class PanelUpdater(TypingProtocol):
    """Интерфейс работы с клиентом в панели.

    Реализуется как mock (для тестов/MVP) и как обёртка над XuiClient.
    """

    async def update_expiry(
        self, server: Server, mapping: ClientServerMapping, expiry_ms: int
    ) -> None:
        ...

    async def ensure_client(
        self, server: Server, target: ProvisionTarget, expiry_ms: int
    ) -> None:
        """Создаёт клиента, если его нет, иначе обновляет срок действия."""
        ...


class MockPanelUpdater:
    """Mock-реализация: ничего не делает либо имитирует сбой нужных серверов."""

    def __init__(self, fail_server_ids: set[int] | None = None) -> None:
        self.fail_server_ids = fail_server_ids or set()
        self.calls: list[tuple[int, int]] = []
        self.ensured: list[tuple[int, int, str]] = []

    async def update_expiry(
        self, server: Server, mapping: ClientServerMapping, expiry_ms: int
    ) -> None:
        self.calls.append((server.id, expiry_ms))
        if server.id in self.fail_server_ids:
            raise PanelUpdateError(f"mock failure for server {server.id}")

    async def ensure_client(
        self, server: Server, target: ProvisionTarget, expiry_ms: int
    ) -> None:
        self.ensured.append((server.id, target.inbound_id, target.email))
        if server.id in self.fail_server_ids:
            raise PanelUpdateError(f"mock failure for server {server.id}")

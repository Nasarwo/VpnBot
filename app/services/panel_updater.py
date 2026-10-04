from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
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
    telegram_id: int | None = None


@dataclass(frozen=True, slots=True)
class QuotaTarget:
    """Абсолютное целевое состояние клиента с учётом трафика.

    ``total_bytes`` — значение totalGB панели в байтах; 0 означает безлимит и
    допустим только для бессрочного доступа. ``expiry_ms`` — expiryTime.
    """

    total_bytes: int
    enable: bool
    expiry_ms: int


@dataclass(slots=True)
class QuotaClientState:
    """Прочитанное с панели состояние клиента и его счётчика трафика."""

    email: str
    enable: bool
    total_bytes: int
    expiry_ms: int
    inbound_ids: list[int]
    # up + down строки статистики; None — строки статистики нет.
    used_bytes: int | None
    # Первичный ключ строки client_traffics: меняется при пересоздании клиента.
    traffic_row_id: int | None
    # client_traffics.last_online (мс, часы панели): панель обновляет его при
    # каждом ненулевом приросте up/down. None/0 — неизвестно.
    last_online_ms: int | None = None

    @property
    def depleted(self) -> bool:
        return (
            self.total_bytes > 0
            and self.used_bytes is not None
            and self.used_bytes >= self.total_bytes
        )


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

    async def read_quota_client(
        self, server: Server, email: str
    ) -> QuotaClientState | None:
        """Читает клиента и его счётчик трафика (None — клиента нет)."""
        ...

    async def read_quota_clients(
        self, server: Server, emails: list[str]
    ) -> dict[str, QuotaClientState | None | PanelUpdateError]:
        """Пакетное чтение клиентов одной сессией панели."""
        ...

    async def apply_quota_client(
        self, server: Server, spec: ServerProvision, target: QuotaTarget
    ) -> QuotaClientState:
        """Создаёт/обновляет клиента с квотой и проверяет результат чтением."""
        ...


class MockPanelUpdater:
    """Mock-реализация: ничего не делает либо имитирует сбой нужных серверов.

    Для whitelist-сервера ведёт простую модель панели: клиент по email,
    totalGB/enable/expiry и счётчик up+down; ``consume`` имитирует трафик и
    отключение панелью при исчерпании квоты.
    """

    def __init__(self, fail_server_ids: set[int] | None = None) -> None:
        self.fail_server_ids = fail_server_ids or set()
        self.read_fail_server_ids: set[int] = set()
        self.calls: list[tuple[int, int]] = []
        self.provisioned: list[tuple[int, str, tuple[int, ...]]] = []
        self.deleted: list[tuple[int, tuple[str, ...]]] = []
        self.quota_clients: dict[tuple[int, str], QuotaClientState] = {}
        self.quota_applied: list[tuple[int, str, QuotaTarget]] = []
        self._next_row_id = 100

    def _new_row_id(self) -> int:
        self._next_row_id += 1
        return self._next_row_id

    def consume(
        self, server_id: int, email: str, amount: int, *, at: datetime | None = None
    ) -> None:
        state = self.quota_clients[(server_id, email)]
        if not state.enable:
            return
        state.used_bytes = (state.used_bytes or 0) + amount
        if amount > 0:
            # Как 3x-ui: last_online сдвигается при каждом ненулевом приросте.
            when = at or datetime.now(tz=UTC)
            state.last_online_ms = max(
                state.last_online_ms or 0, int(when.timestamp() * 1000)
            )
        if state.depleted:
            state.enable = False

    def reset_traffic(self, server_id: int, email: str) -> None:
        state = self.quota_clients[(server_id, email)]
        state.used_bytes = 0
        state.enable = True

    def recreate(self, server_id: int, email: str) -> None:
        state = self.quota_clients[(server_id, email)]
        state.used_bytes = 0
        state.traffic_row_id = self._new_row_id()
        state.last_online_ms = None

    async def read_quota_client(
        self, server: Server, email: str
    ) -> QuotaClientState | None:
        if server.id in self.read_fail_server_ids or server.id in self.fail_server_ids:
            raise PanelUpdateError(f"mock read failure for server {server.id}")
        state = self.quota_clients.get((server.id, email))
        if state is None:
            return None
        return QuotaClientState(
            email=state.email,
            enable=state.enable,
            total_bytes=state.total_bytes,
            expiry_ms=state.expiry_ms,
            inbound_ids=list(state.inbound_ids),
            used_bytes=state.used_bytes,
            traffic_row_id=state.traffic_row_id,
            last_online_ms=state.last_online_ms,
        )

    async def read_quota_clients(
        self, server: Server, emails: list[str]
    ) -> dict[str, QuotaClientState | None | PanelUpdateError]:
        result: dict[str, QuotaClientState | None | PanelUpdateError] = {}
        for email in emails:
            try:
                result[email] = await self.read_quota_client(server, email)
            except PanelUpdateError as exc:
                result[email] = exc
        return result

    async def apply_quota_client(
        self, server: Server, spec: ServerProvision, target: QuotaTarget
    ) -> QuotaClientState:
        self.quota_applied.append((server.id, spec.email, target))
        if server.id in self.fail_server_ids:
            raise PanelUpdateError(f"mock failure for server {server.id}")
        inbound_ids = [i.inbound_id for i in spec.inbounds]
        state = self.quota_clients.get((server.id, spec.email))
        if state is None:
            state = QuotaClientState(
                email=spec.email,
                enable=target.enable,
                total_bytes=target.total_bytes,
                expiry_ms=target.expiry_ms,
                inbound_ids=inbound_ids,
                used_bytes=0,
                traffic_row_id=self._new_row_id(),
            )
            self.quota_clients[(server.id, spec.email)] = state
        else:
            state.enable = target.enable
            state.total_bytes = target.total_bytes
            state.expiry_ms = target.expiry_ms
            state.inbound_ids = sorted(set(state.inbound_ids) | set(inbound_ids))
        if state.depleted:
            state.enable = False
        return await self.read_quota_client(server, spec.email)  # type: ignore[return-value]

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
        for mapping in mappings:
            self.quota_clients.pop((server.id, mapping.email), None)

    async def provision_server(
        self, server: Server, spec: ServerProvision, expiry_ms: int
    ) -> None:
        self.provisioned.append(
            (server.id, spec.email, tuple(i.inbound_id for i in spec.inbounds))
        )
        if server.id in self.fail_server_ids:
            raise PanelUpdateError(f"mock failure for server {server.id}")

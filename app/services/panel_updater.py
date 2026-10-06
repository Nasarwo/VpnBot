from __future__ import annotations

from dataclasses import dataclass, field
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
    # flow клиента в настройках inbound'ов (settings.clients[] — по ним строят
    # конфиг Xray и ссылку SubHub). None — не читалось; '' — без flow.
    inbound_flows: dict[int, str] | None = None
    # inbound'ы, к которым этот вызов apply_quota_client прикрепил клиента (или
    # создал его), прочитав перед этим, что привязки нет.
    attached_inbound_ids: list[int] = field(default_factory=list)

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
        """Создаёт/обновляет клиента с квотой и проверяет результат чтением.

        ``spec.inbounds`` — целевые inbound'ы: недостающие прикрепляются (attach)
        до обновления параметров, flow целевых задаётся явно (None — без flow).
        Прочие привязки клиента не снимаются, их flow по возможности сохраняется.
        """
        ...

    async def detach_quota_client(
        self, server: Server, email: str, inbound_ids: list[int]
    ) -> QuotaClientState | None:
        """Снимает привязки клиента к ``inbound_ids`` (счётчик сохраняется).

        Проверяет чтением, что привязок не осталось; None — клиента нет.
        """
        ...


def effective_flow(state: QuotaClientState) -> str:
    """flow, который 3x-ui копирует при attach: первый непустой по id inbound'а."""
    flows = state.inbound_flows or {}
    return next((flows[i] for i in sorted(flows) if flows[i]), "")


class MockPanelUpdater:
    """Mock-реализация: ничего не делает либо имитирует сбой нужных серверов.

    Для whitelist-сервера ведёт модель панели 3x-ui >= 3.2: клиент по email
    (общая запись: totalGB/enable/expiry), привязки к inbound'ам с flow в
    настройках каждого inbound'а и одна строка статистики up+down на email.
    ``consume`` имитирует трафик и отключение панелью при исчерпании квоты.

    Семантика, сверенная с исходниками 3x-ui v3.2.0–v3.9.0:

    * attach копирует общую запись клиента в новый inbound (flow — первый
      непустой flow его привязок) и не трогает счётчик;
    * update с фильтром ``inboundIds`` (3.3+) меняет общую запись, а flow — только
      в inbound'ах фильтра; ``update_filter_supported=False`` моделирует 3.2.0, где
      фильтра нет и flow тела пишется во все привязки;
    * detach снимает привязку, сохраняя строку статистики (keepTraffic);
    * удаление inbound'а на панели снимает его привязки (``remove_inbound``).

    ``fail_steps`` — сбои шагов применения: ``attach``/``update``/``detach`` — до
    изменения; ``attach_lost``/``detach_lost`` — изменение выполнено, ответ
    потерян; ``verify`` — чтение после записи не подтвердило результат;
    ``detach_ignored`` — панель ответила успехом, но привязку не сняла.
    """

    def __init__(self, fail_server_ids: set[int] | None = None) -> None:
        self.fail_server_ids = fail_server_ids or set()
        self.read_fail_server_ids: set[int] = set()
        self.calls: list[tuple[int, int]] = []
        self.provisioned: list[tuple[int, str, tuple[int, ...]]] = []
        self.deleted: list[tuple[int, tuple[str, ...]]] = []
        self.quota_clients: dict[tuple[int, str], QuotaClientState] = {}
        self.quota_applied: list[tuple[int, str, QuotaTarget]] = []
        # Inbound'ы панели: server_id → {inbound_id: включён}. Сервер без записи —
        # любой inbound существует и включён.
        self.panel_inbounds: dict[int, dict[int, bool]] = {}
        self.removed_inbounds: set[tuple[int, int]] = set()
        self.update_filter_supported = True
        self.fail_steps: set[str] = set()
        self.attached: list[tuple[int, str, tuple[int, ...]]] = []
        self.detached: list[tuple[int, str, tuple[int, ...]]] = []
        self.updated: list[tuple[int, str, tuple[int, ...]]] = []
        # Версия панели, пересоздающая строку статистики при detach (защитная модель).
        self.detach_recreates_traffic = False
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

    def remove_inbound(self, server_id: int, inbound_id: int) -> None:
        """Inbound удалён на панели: его привязки исчезают у всех клиентов."""
        self.removed_inbounds.add((server_id, inbound_id))
        self.panel_inbounds.get(server_id, {}).pop(inbound_id, None)
        for (sid, _email), state in self.quota_clients.items():
            if sid == server_id and inbound_id in state.inbound_ids:
                state.inbound_ids = [i for i in state.inbound_ids if i != inbound_id]
                if state.inbound_flows is not None:
                    state.inbound_flows.pop(inbound_id, None)

    def _fail(self, step: str) -> None:
        if step in self.fail_steps:
            raise PanelUpdateError(f"mock failure at {step}")

    async def read_quota_client(
        self, server: Server, email: str
    ) -> QuotaClientState | None:
        if server.id in self.read_fail_server_ids or server.id in self.fail_server_ids:
            raise PanelUpdateError(f"mock read failure for server {server.id}")
        state = self.quota_clients.get((server.id, email))
        if state is None:
            return None
        flows = state.inbound_flows or {}
        return QuotaClientState(
            email=state.email,
            enable=state.enable,
            total_bytes=state.total_bytes,
            expiry_ms=state.expiry_ms,
            inbound_ids=list(state.inbound_ids),
            used_bytes=state.used_bytes,
            traffic_row_id=state.traffic_row_id,
            last_online_ms=state.last_online_ms,
            inbound_flows={i: flows.get(i, "") for i in state.inbound_ids},
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
        flows = {i.inbound_id: i.flow or "" for i in spec.inbounds}
        live = self.panel_inbounds.get(server.id)
        unavailable = [
            i for i in inbound_ids
            if (server.id, i) in self.removed_inbounds
            or (live is not None and not live.get(i, False))
        ]
        if unavailable:
            raise PanelUpdateError(f"Недоступные inbound на сервере {server.id}: {unavailable}")
        state = self.quota_clients.get((server.id, spec.email))
        attached: list[int] = []
        if state is None:
            self._fail("attach")
            state = QuotaClientState(
                email=spec.email,
                enable=target.enable,
                total_bytes=target.total_bytes,
                expiry_ms=target.expiry_ms,
                inbound_ids=sorted(inbound_ids),
                used_bytes=0,
                traffic_row_id=self._new_row_id(),
                inbound_flows=dict(flows),
            )
            self.quota_clients[(server.id, spec.email)] = state
            attached = sorted(inbound_ids)
            self.attached.append((server.id, spec.email, tuple(attached)))
            self._fail("attach_lost")
        else:
            if state.inbound_flows is None:
                state.inbound_flows = dict.fromkeys(state.inbound_ids, "")
            missing = sorted(set(inbound_ids) - set(state.inbound_ids))
            if missing:
                self._fail("attach")
                # attach копирует общую запись: flow — действующий flow клиента.
                copied = effective_flow(state)
                state.inbound_ids = sorted(set(state.inbound_ids) | set(missing))
                for inbound_id in missing:
                    state.inbound_flows[inbound_id] = copied
                attached = missing
                self.attached.append((server.id, spec.email, tuple(missing)))
                self._fail("attach_lost")
            self._fail("update")
            state.enable = target.enable
            state.total_bytes = target.total_bytes
            state.expiry_ms = target.expiry_ms
            scope = inbound_ids if self.update_filter_supported else list(state.inbound_ids)
            self.updated.append((server.id, spec.email, tuple(scope)))
            for inbound_id in scope:
                # Без фильтра (3.2.0) flow тела пишется во все привязки клиента.
                state.inbound_flows[inbound_id] = flows.get(inbound_id, flows[inbound_ids[-1]])
        if state.depleted:
            state.enable = False
        result = await self.read_quota_client(server, spec.email)
        assert result is not None
        self._fail("verify")
        result.attached_inbound_ids = attached
        return result

    async def detach_quota_client(
        self, server: Server, email: str, inbound_ids: list[int]
    ) -> QuotaClientState | None:
        self.detached.append((server.id, email, tuple(inbound_ids)))
        if server.id in self.fail_server_ids:
            raise PanelUpdateError(f"mock failure for server {server.id}")
        state = self.quota_clients.get((server.id, email))
        if state is None:
            return None
        present = [i for i in inbound_ids if i in state.inbound_ids]
        if present and "detach_ignored" not in self.fail_steps:
            self._fail("detach")
            state.inbound_ids = [i for i in state.inbound_ids if i not in present]
            if state.inbound_flows is not None:
                for inbound_id in present:
                    state.inbound_flows.pop(inbound_id, None)
            if self.detach_recreates_traffic:
                state.used_bytes = 0
                state.traffic_row_id = self._new_row_id()
                state.last_online_ms = None
            self._fail("detach_lost")
        result = await self.read_quota_client(server, email)
        if result is not None and set(inbound_ids) & set(result.inbound_ids):
            raise PanelUpdateError(
                f"Панель не подтвердила снятие привязок клиента {email}: "
                f"inbound={result.inbound_ids}"
            )
        return result

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

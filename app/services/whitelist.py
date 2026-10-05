"""Услуга «Обход белых списков»: учёт трафика и квота на whitelist-сервере.

Модель учёта
------------
* ``WhitelistAccount`` хранит два остатка — бесплатный и купленный (байты) — на
  момент контрольной точки ``usage_checkpoint_bytes``: накопленного up+down
  клиента панели. Новый расход Δ = текущий счётчик − контрольная точка
  списывается сначала с бесплатного, затем с купленного остатка; уже учтённый
  расход повторно не списывается, потому что контрольная точка сдвигается.
* Панели задаётся абсолютная квота ``totalGB = checkpoint + free + paid``.
  Повтор применения выставляет то же значение и ничего не прибавляет. При нуле
  остатка клиент отключается, а totalGB остаётся конечным (никогда не 0 —
  это безлимит). Бессрочный доступ — totalGB=0, expiryTime=0.
* Каждая выдача бесплатного пакета и каждое начисление покупки — строка
  ``WhitelistLedger`` с уникальным ``source_key`` исходной операции. Повторное
  подтверждение, retry, рестарт и повтор очереди не дают второй выдачи.
* Строки журнала — упорядоченные события учёта. Событие меняет подтверждённые
  остатки только после списания расхода до него, то есть при известном
  значении счётчика в момент события (``anchor_bytes``). Если статистика
  недоступна, событие сохраняется как ``pending``, а прежние остатки не
  меняются. Ближайшая сверка привязывает его: расход не менялся; панель
  (``last_online``) показывает, что после события активности не было; покупка
  не зависит от порядка, пока остатка хватает. Иначе событие становится
  ``uncertain``: неразделённый расход не списывается до решения администратора.
* Квота панели при неприменённых событиях — гарантированная нижняя граница:
  ``checkpoint + остатки с событиями``; весь расход после точки ей учитывается.
* Сохранённое начисление и применение на панели разделены:
  ``desired_version``/``applied_version``. Панель синхронизируется по текущему
  состоянию БД, поэтому старая задача не может откатить новое состояние.

Все изменения остатков выполняются под пользовательской блокировкой
(``operation_lock.user_operation``); функции с префиксом ``_`` предполагают,
что блокировка уже взята вызывающим кодом.
"""
from __future__ import annotations

import asyncio
import enum
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.db.enums import PaymentStatus
from app.db.models import (
    PAYMENT_KIND_SUBSCRIPTION,
    PAYMENT_KIND_TRAFFIC,
    SERVER_PURPOSE_WHITELIST,
    PaymentRequest,
    Server,
    ServerInbound,
    TrafficPackage,
    User,
    VpnClient,
    WhitelistAccount,
    WhitelistConfig,
    WhitelistLedger,
)
from app.db.repositories import VpnClientRepository
from app.services import audit, provisioning
from app.services.operation_lock import serialized_access
from app.services.panel_updater import (
    PanelUpdateError,
    PanelUpdater,
    QuotaClientState,
    QuotaTarget,
)
from app.services.whitelist_compat import InboundCompat, check_inbound, describe

logger = logging.getLogger(__name__)

GIB = 1024**3
SERVICE_TITLE = "Обход белых списков"

DEFAULT_PAID_FREE_BYTES = 10 * GIB
DEFAULT_TRIAL_FREE_BYTES = 3 * GIB
DEFAULT_PACKAGES: tuple[tuple[int, int], ...] = (
    (10 * GIB, 49),
    (25 * GIB, 99),
    (50 * GIB, 199),
)

INVENTORY_READY = "ready"
INVENTORY_ERROR = "error"
INVENTORY_NEEDS_CHOICE = "needs_choice"
# Целевой inbound выбран, но SubHub не построит для него рабочую ссылку.
INVENTORY_INCOMPATIBLE = "incompatible"

# Ключи журнала: одна выдача/начисление на исходную операцию.
LEDGER_FREE_GRANT = "free_grant"
LEDGER_PURCHASE = "purchase"
LEDGER_ROLLOUT = "rollout"
LEDGER_REBASE = "usage_rebase"
LEDGER_ADJUST = "adjust"

_FREE_GRANT_KINDS = (LEDGER_FREE_GRANT, LEDGER_ROLLOUT)

# Состояние события учёта в журнале.
EVENT_SETTLED = "settled"
EVENT_PENDING = "pending"
EVENT_UNCERTAIN = "uncertain"
_OPEN_EVENTS = (EVENT_PENDING, EVENT_UNCERTAIN)

# Решение администратора по неразделённому расходу.
RESOLVE_BEFORE = "before"
RESOLVE_AFTER = "after"

# Допуск расхождения часов панели (last_online) и бота (время события).
LAST_ONLINE_SKEW = timedelta(minutes=1)


class WhitelistError(Exception):
    """Ошибка бизнес-правил услуги."""


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def gib_to_bytes(value: Decimal | float | int) -> int:
    return int(Decimal(str(value)) * GIB)


def set_volume_gib_text(size_bytes: int | None) -> str:
    """Заданный объём в ГБ (без единицы, точка): так, как он вводился.

    Байты при вводе усекаются (`gib_to_bytes`), поэтому 0,02 ГБ хранится как
    21474836 Б и округление вниз показало бы 0,01. Берётся самая короткая запись
    с 2–4 знаками, которая переводится обратно ровно в те же байты; если такой нет
    (байты не из ввода), значение усекается до сотых — вверх не округляется.
    Учёт и API панели от этого текста не зависят.
    """
    size = max(0, size_bytes or 0)
    exact = Decimal(size) / GIB
    shown = exact.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    for places in (2, 3, 4):
        candidate = exact.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
        if gib_to_bytes(candidate) == size:
            shown = candidate
            break
    return f"{shown:f}".rstrip("0").rstrip(".")


# --- Чистые правила учёта ---------------------------------------------------


def apply_usage(free: int, paid: int, delta: int) -> tuple[int, int]:
    """Списывает новый расход: сначала бесплатный, затем купленный остаток."""
    if delta <= 0:
        return free, paid
    paid_used = max(0, delta - free)
    return max(0, free - delta), max(0, paid - paid_used)


def apply_event(free: int, paid: int, event: WhitelistLedger) -> tuple[int, int]:
    """Действие события: замена бесплатного остатка и/или прибавка купленного."""
    if event.free_set is not None:
        free = event.free_set
    if event.paid_delta is not None:
        paid += event.paid_delta
    return free, paid


def is_open(event: WhitelistLedger) -> bool:
    return event.status in _OPEN_EVENTS


def provisional_balances(
    account: WhitelistAccount, events: list[WhitelistLedger] | tuple[()] = ()
) -> tuple[int, int]:
    """Подтверждённые остатки с неприменёнными событиями, без неучтённого расхода.

    Сумма — гарантированная нижняя граница остатка относительно контрольной
    точки: при любом порядке расход уменьшает её не больше, чем на свой объём.
    """
    free, paid = account.free_bytes, account.paid_bytes
    for event in events:
        if is_open(event):
            free, paid = apply_event(free, paid, event)
    return free, paid


def uncertain_outcomes(
    account: WhitelistAccount, events: list[WhitelistLedger]
) -> tuple[tuple[int, int], tuple[int, int]] | None:
    """Остатки (бесплатный, купленный) на конце неразделённого периода.

    Первая пара — весь расход до события, вторая — весь расход после него.
    None — расход периода не прочитан и вариантов нет.
    """
    event = next((e for e in events if e.status == EVENT_UNCERTAIN), None)
    if (
        event is None
        or event.anchor_min_bytes is None
        or event.anchor_max_bytes is None
        or account.usage_checkpoint_bytes != event.anchor_min_bytes
    ):
        return None
    span = event.anchor_max_bytes - event.anchor_min_bytes
    free, paid = account.free_bytes, account.paid_bytes
    before = apply_event(*apply_usage(free, paid, span), event)
    after = apply_usage(*apply_event(free, paid, event), span)
    return before, after


@dataclass(frozen=True, slots=True)
class AccessState:
    """Доступ к VPN, от которого зависит белосписочный конфиг."""

    lifetime: bool
    active: bool
    expires_at: datetime | None


def access_state(client: VpnClient | None, now: datetime) -> AccessState:
    """Бессрочность определяется сроком подписки, а не ролью администратора."""
    if client is None or not client.is_active:
        expires = _aware(client.expires_at) if client is not None else None
        return AccessState(lifetime=False, active=False, expires_at=expires)
    expires = _aware(client.expires_at)
    if expires is None:
        # Бессрочный доступ существует только у привязанного клиента панели.
        lifetime = bool(client.mappings)
        return AccessState(lifetime=lifetime, active=lifetime, expires_at=None)
    return AccessState(lifetime=False, active=expires > now, expires_at=expires)


def compute_target(
    account: WhitelistAccount,
    access: AccessState,
    now: datetime,
    events: list[WhitelistLedger] | tuple[()] = (),
) -> QuotaTarget:
    """Абсолютное целевое состояние клиента whitelist-панели.

    Неприменённые события входят в квоту без неучтённого расхода — это нижняя
    граница: панель сама списывает с неё весь расход после контрольной точки.
    """
    if access.lifetime:
        return QuotaTarget(total_bytes=0, enable=not account.admin_blocked, expiry_ms=0)
    used = account.usage_checkpoint_bytes or 0
    free, paid = provisional_balances(account, events)
    remaining = max(0, free) + max(0, paid)
    # Исчерпанный лимит остаётся конечным: totalGB=0 означал бы безлимит.
    total = used + remaining if remaining > 0 else max(used, 1)
    # Без срока и без бессрочного доступа клиент считается истёкшим.
    expiry_ms = _ms(access.expires_at) if access.expires_at is not None else 1
    enable = access.active and remaining > 0 and not account.admin_blocked
    return QuotaTarget(total_bytes=total, enable=enable, expiry_ms=expiry_ms)


# --- Настройки и пакеты -------------------------------------------------------


async def get_config(session: AsyncSession) -> WhitelistConfig:
    """Настройки услуги; строка с начальными значениями создаётся один раз."""
    config = await session.get(WhitelistConfig, 1)
    if config is None:
        config = WhitelistConfig(
            id=1,
            service_enabled=False,
            paid_free_bytes=DEFAULT_PAID_FREE_BYTES,
            trial_free_bytes=DEFAULT_TRIAL_FREE_BYTES,
        )
        session.add(config)
        await session.flush()
    return config


async def ensure_defaults(session: AsyncSession) -> None:
    """Идемпотентная инициализация: настройки и начальные пакеты."""
    await get_config(session)
    count = await session.scalar(select(func.count(TrafficPackage.id)))
    if not count:
        for order, (size, price) in enumerate(DEFAULT_PACKAGES, start=1):
            session.add(
                TrafficPackage(
                    traffic_bytes=size, price=Decimal(price), enabled=True, sort_order=order
                )
            )
        await session.flush()
    await session.commit()


async def list_packages(
    session: AsyncSession, *, only_enabled: bool = True
) -> list[TrafficPackage]:
    query = select(TrafficPackage).order_by(TrafficPackage.sort_order, TrafficPackage.id)
    if only_enabled:
        query = query.where(TrafficPackage.enabled.is_(True))
    return list((await session.scalars(query)).all())


async def set_free_volume(
    session: AsyncSession, *, trial: bool, size_bytes: int, actor_user_id: int | None
) -> WhitelistConfig:
    """Меняет объём будущих выдач; текущие остатки не переписываются."""
    if size_bytes < 0:
        raise WhitelistError("Объём не может быть отрицательным")
    config = await get_config(session)
    old = config.trial_free_bytes if trial else config.paid_free_bytes
    if trial:
        config.trial_free_bytes = size_bytes
    else:
        config.paid_free_bytes = size_bytes
    config.updated_at = _utcnow()
    await audit.record(
        session,
        action="whitelist.config_free_volume",
        actor_user_id=actor_user_id,
        entity_type="whitelist_config",
        entity_id=1,
        payload={"trial": trial, "old": old, "new": size_bytes},
    )
    await session.commit()
    return config


async def save_package(
    session: AsyncSession,
    *,
    package_id: int | None,
    size_bytes: int | None = None,
    price: Decimal | None = None,
    enabled: bool | None = None,
    actor_user_id: int | None,
) -> TrafficPackage:
    """Создаёт/меняет пакет. Созданные ранее заявки хранят свой снимок."""
    if package_id is None:
        if size_bytes is None or price is None:
            raise WhitelistError("Для нового пакета нужны объём и цена")
        order = await session.scalar(select(func.max(TrafficPackage.sort_order))) or 0
        package = TrafficPackage(
            traffic_bytes=size_bytes, price=price, enabled=True, sort_order=order + 1
        )
        session.add(package)
    else:
        found = await session.get(TrafficPackage, package_id)
        if found is None:
            raise WhitelistError("Пакет не найден")
        package = found
    before = {
        "bytes": package.traffic_bytes,
        "price": str(package.price) if package.price is not None else None,
        "enabled": package.enabled,
    }
    if size_bytes is not None:
        if size_bytes <= 0:
            raise WhitelistError("Объём пакета должен быть больше нуля")
        package.traffic_bytes = size_bytes
    if price is not None:
        if price <= 0:
            raise WhitelistError("Цена должна быть больше нуля")
        package.price = price
    if enabled is not None:
        package.enabled = enabled
    package.updated_at = _utcnow()
    await session.flush()
    await audit.record(
        session,
        action="whitelist.package_saved",
        actor_user_id=actor_user_id,
        entity_type="traffic_package",
        entity_id=package.id,
        payload={
            "before": before if package_id is not None else None,
            "after": {
                "bytes": package.traffic_bytes,
                "price": str(package.price),
                "enabled": package.enabled,
            },
        },
    )
    await session.commit()
    return package


# --- Сервер услуги ------------------------------------------------------------


async def get_active_server(session: AsyncSession) -> Server | None:
    """Включённый whitelist-сервер (не более одного по уникальному индексу)."""
    result = await session.execute(
        select(Server)
        .where(Server.purpose == SERVER_PURPOSE_WHITELIST, Server.enabled.is_(True))
        .options(selectinload(Server.inbounds))
        .order_by(Server.id)
        .execution_options(populate_existing=True)
    )
    return result.scalars().first()


def target_inbound(server: Server) -> ServerInbound | None:
    enabled = [i for i in server.inbounds if i.enabled]
    return enabled[0] if len(enabled) == 1 else None


def server_ready(server: Server | None) -> bool:
    return (
        server is not None
        and server.enabled
        and server.purpose == SERVER_PURPOSE_WHITELIST
        and server.inventory_status == INVENTORY_READY
        and target_inbound(server) is not None
    )


async def has_other_enabled_whitelist(
    session: AsyncSession, server_id: int | None = None
) -> bool:
    query = select(Server.id).where(
        Server.purpose == SERVER_PURPOSE_WHITELIST, Server.enabled.is_(True)
    )
    if server_id is not None:
        query = query.where(Server.id != server_id)
    return (await session.scalar(query.limit(1))) is not None


@dataclass(slots=True)
class InventoryResult:
    status: str
    summary: list[tuple[int, str, str]] = field(default_factory=list)
    error: str | None = None
    candidates: list[ServerInbound] = field(default_factory=list)
    # Вердикт совместимости целевого inbound с форматом ссылок SubHub.
    target: InboundCompat | None = None


async def sync_inventory(
    session: AsyncSession,
    server: Server,
    *,
    timeout: float = 15.0,
    actor_user_id: int | None = None,
) -> InventoryResult:
    """Сверяет inbound'ы whitelist-сервера; идемпотентна, вызывающий коммитит.

    Используется общая сверка реестра (удалённые/выключенные отключаются,
    ручное отключение сохраняется). Целевой inbound должен быть ровно один:
    при нескольких кандидатах сервер не готов, пока администратор не выберет.
    Готов сервер только с целью, для которой SubHub построит ссылку
    (:mod:`app.services.whitelist_compat`); иначе — ``incompatible``.
    """
    if server.purpose != SERVER_PURPOSE_WHITELIST:
        raise WhitelistError("Сервер не относится к услуге «Обход белых списков»")
    loaded = await session.execute(
        select(ServerInbound).where(ServerInbound.server_id == server.id)
    )
    before_enabled = {i.inbound_id for i in loaded.scalars().all() if i.enabled}
    try:
        raw_inbounds = await provisioning.fetch_inbounds(server, timeout=timeout)
        summary = await provisioning.reconcile_inbounds(session, server, raw_inbounds)
    except PanelUpdateError as exc:
        server.inventory_status = INVENTORY_ERROR
        server.inventory_error = str(exc)[:1000]
        server.inventory_synced_at = _utcnow()
        await audit.record(
            session,
            action="whitelist.inventory_failed",
            actor_user_id=actor_user_id,
            entity_type="server",
            entity_id=server.id,
            payload={"error": str(exc)[:500]},
        )
        return InventoryResult(status=INVENTORY_ERROR, error=str(exc))

    rows = list(
        (
            await session.execute(
                select(ServerInbound)
                .where(ServerInbound.server_id == server.id)
                .order_by(ServerInbound.inbound_id)
                .execution_options(populate_existing=True)
            )
        )
        .scalars()
        .all()
    )
    raw_by_id = {item.get("id"): item for item in raw_inbounds}

    def verdict(row: ServerInbound) -> InboundCompat:
        raw = raw_by_id.get(row.inbound_id) or {
            "id": row.inbound_id, "protocol": row.protocol.value,
        }
        return check_inbound(raw, flow=row.flow)

    enabled = [row for row in rows if row.enabled]
    kept = [row for row in enabled if row.inbound_id in before_enabled]
    result = InventoryResult(status=INVENTORY_READY, summary=summary)
    messages: list[str] = []
    target: ServerInbound | None = None
    if len(kept) == 1:
        # Выбранная ранее цель сохраняется; новые inbound'ы не подключаются
        # автоматически и показываются администратору как расхождение.
        target = kept[0]
        for row in enabled:
            if row is not target:
                row.enabled = False
                result.candidates.append(row)
        if result.candidates:
            messages.append(
                "На панели появились дополнительные inbound'ы: "
                + ", ".join(describe(verdict(r)) for r in result.candidates)
                + f". Целевым остаётся {target.inbound_id}."
            )
    elif len(enabled) == 1:
        target = enabled[0]
    elif not enabled:
        result.status = INVENTORY_ERROR
        messages.append("На панели нет включённого поддерживаемого inbound")
    else:
        for row in enabled:
            row.enabled = False
        result.status = INVENTORY_NEEDS_CHOICE
        result.candidates = enabled
        messages.append(
            "Ожидался один inbound, найдено несколько: "
            + ", ".join(describe(verdict(r)) for r in enabled)
            + ". Выберите целевой inbound."
        )
    if target is not None:
        result.target = verdict(target)
        if not result.target.compatible:
            result.status = INVENTORY_INCOMPATIBLE
        messages.insert(0, "Целевой inbound " + describe(result.target) + ".")
        messages.extend(result.target.notes)
    result.error = "\n".join(messages) or None
    server.inventory_status = result.status
    server.inventory_error = result.error
    server.inventory_synced_at = _utcnow()
    await session.flush()
    await audit.record(
        session,
        action="whitelist.inventory_synced",
        actor_user_id=actor_user_id,
        entity_type="server",
        entity_id=server.id,
        payload={
            "status": result.status,
            "enabled": [r.inbound_id for r in rows if r.enabled],
            "candidates": [r.inbound_id for r in result.candidates],
            "problems": list(result.target.problems) if result.target else [],
        },
    )
    return result


async def choose_inbound(
    session: AsyncSession,
    server: Server,
    inbound_id: int,
    actor_user_id: int | None,
    *,
    timeout: float = 15.0,
) -> InventoryResult:
    """Делает выбранный inbound единственной целью whitelist-сервера.

    Готовность выставляет не выбор, а следующая за ним сверка с панелью:
    она же проверяет совместимость цели с SubHub.
    """
    rows = list(
        (
            await session.execute(
                select(ServerInbound).where(ServerInbound.server_id == server.id)
            )
        )
        .scalars()
        .all()
    )
    chosen = next((row for row in rows if row.inbound_id == inbound_id), None)
    if chosen is None:
        raise WhitelistError("Inbound не найден в реестре сервера")
    for row in rows:
        row.enabled = row is chosen
    await audit.record(
        session,
        action="whitelist.inbound_chosen",
        actor_user_id=actor_user_id,
        entity_type="server",
        entity_id=server.id,
        payload={"inbound_id": inbound_id},
    )
    await session.flush()
    result = await sync_inventory(
        session, server, timeout=timeout, actor_user_id=actor_user_id
    )
    await session.commit()
    return result


# --- Учёт пользователя --------------------------------------------------------


async def get_account(
    session: AsyncSession, user_id: int, *, create: bool = False
) -> WhitelistAccount | None:
    account = await session.scalar(
        select(WhitelistAccount)
        .where(WhitelistAccount.user_id == user_id)
        .execution_options(populate_existing=True)
    )
    if account is None and create:
        account = WhitelistAccount(user_id=user_id, free_bytes=0, paid_bytes=0)
        session.add(account)
        await session.flush()
    return account


def mark_dirty(account: WhitelistAccount) -> None:
    """Состояние в БД изменилось и должно быть применено на панели."""
    account.desired_version = max(account.desired_version, account.applied_version) + 1
    account.next_sync_at = None


async def release_applied_credits(session: AsyncSession, account: WhitelistAccount) -> int:
    """Снимает ожидание с заявок, начисление которых уже применено на панели (без commit).

    Заявка перестаёт ждать, когда одновременно: версия, с которой её начисление
    попало в учёт (``apply_pending_version``), подтверждена панелью
    (``applied_version``), и событие учёта сверено с расходом. Более поздние
    изменения баланса поднимают только ``desired_version`` и на уже применённые
    заявки не влияют. Прочие ошибки заявки (``last_error``) не затрагиваются.
    """
    waiting = (
        await session.scalars(
            select(PaymentRequest)
            .where(PaymentRequest.user_id == account.user_id)
            .where(PaymentRequest.kind == PAYMENT_KIND_TRAFFIC)
            .where(PaymentRequest.apply_pending_version.is_not(None))
            .execution_options(populate_existing=True)
        )
    ).all()
    released = 0
    for payment in waiting:
        required = payment.apply_pending_version
        if required is None or account.applied_version < required:
            continue
        event_status = await session.scalar(
            select(WhitelistLedger.status).where(
                WhitelistLedger.source_key == f"payment:{payment.id}"
            )
        )
        if event_status in _OPEN_EVENTS:
            continue
        payment.apply_pending_version = None
        released += 1
    return released


def _record_ledger(
    session: AsyncSession,
    account: WhitelistAccount,
    *,
    kind: str,
    source_key: str | None,
    free_before: int,
    paid_before: int,
    payment_id: int | None = None,
    actor_user_id: int | None = None,
    note: str | None = None,
) -> None:
    session.add(
        WhitelistLedger(
            user_id=account.user_id,
            kind=kind,
            source_key=source_key,
            payment_request_id=payment_id,
            free_before=free_before,
            free_after=account.free_bytes,
            paid_before=paid_before,
            paid_after=account.paid_bytes,
            actor_user_id=actor_user_id,
            note=note,
        )
    )


async def _ledger_exists(session: AsyncSession, source_key: str) -> bool:
    found = await session.scalar(
        select(WhitelistLedger.id).where(WhitelistLedger.source_key == source_key)
    )
    return found is not None


async def list_open_events(session: AsyncSession, user_id: int) -> list[WhitelistLedger]:
    """Неприменённые события учёта пользователя в порядке возникновения."""
    result = await session.scalars(
        select(WhitelistLedger)
        .where(WhitelistLedger.user_id == user_id)
        .where(WhitelistLedger.status.in_(_OPEN_EVENTS))
        .order_by(WhitelistLedger.id)
        .execution_options(populate_existing=True)
    )
    return list(result.all())


def _append_note(event: WhitelistLedger, text: str) -> None:
    event.note = f"{event.note}. {text}" if event.note else text


def _last_online(state: QuotaClientState) -> datetime | None:
    if not state.last_online_ms or state.last_online_ms <= 0:
        return None
    return datetime.fromtimestamp(state.last_online_ms / 1000, tz=UTC)


def _infer_anchor(
    event: WhitelistLedger,
    *,
    checkpoint: int,
    used: int,
    free: int,
    paid: int,
    last_online: datetime | None,
    access: AccessState,
) -> int | None:
    """Значение счётчика в момент события по сверке после него; None — неизвестно."""
    known = event.anchor_bytes
    if known is not None and checkpoint <= known <= used:
        return known
    if used == checkpoint or access.lifetime:
        # Расхода не было (или он не списывается): порядок не влияет на итог.
        return used
    occurred = _aware(event.created_at)
    if (
        last_online is not None
        and occurred is not None
        and last_online + LAST_ONLINE_SKEW <= occurred
    ):
        # Панель не видела трафика после события: весь расход был до него.
        return used
    if event.free_set is None and used - checkpoint <= free + paid:
        # Покупка коммутирует с расходом, пока остатка хватает при любом порядке.
        return checkpoint
    return None


def _settle_ordered(
    ctx: _Context,
    events: list[WhitelistLedger],
    *,
    used: int,
    last_online: datetime | None,
    read_at: datetime | None,
) -> bool:
    """Применяет события по порядку вместе с расходом до каждого из них.

    ``used`` — значение счётчика той же эпохи, прочитанное после всех ``events``.
    Расход до привязки события списывается со старых остатков, после неё — с
    остатков после события. Событие без определимой привязки становится
    ``uncertain``: следующие ждут, неразделённый расход не списывается.
    Возвращает True, если применены все события.
    """
    account = ctx.account
    checkpoint = account.usage_checkpoint_bytes or 0
    free, paid = account.free_bytes, account.paid_bytes
    charge = not ctx.access.lifetime
    settled_at: datetime | None = None
    blocked = False
    for event in events:
        if not is_open(event):
            continue
        anchor = _infer_anchor(
            event, checkpoint=checkpoint, used=used, free=free, paid=paid,
            last_online=last_online, access=ctx.access,
        )
        if anchor is None:
            event.status = EVENT_UNCERTAIN
            event.anchor_min_bytes = checkpoint
            event.anchor_max_bytes = used
            _append_note(
                event,
                f"Расход {used - checkpoint} байт за время недоступности сверки "
                "нельзя точно отнести до или после события; нужно решение администратора",
            )
            logger.warning(
                "whitelist user=%s: событие #%s без разделения расхода (%s байт)",
                account.user_id, event.id, used - checkpoint,
            )
            blocked = True
            break
        if charge:
            free, paid = apply_usage(free, paid, anchor - checkpoint)
        event.free_before, event.paid_before = free, paid
        free, paid = apply_event(free, paid, event)
        event.free_after, event.paid_after = free, paid
        event.anchor_bytes = anchor
        event.status = EVENT_SETTLED
        checkpoint = anchor
        settled_at = _aware(event.created_at)
    if not blocked:
        if charge:
            free, paid = apply_usage(free, paid, used - checkpoint)
        checkpoint = used
        # Остатки подтверждены на момент чтения; без него — время неизвестно.
        settled_at = read_at
    account.free_bytes, account.paid_bytes = free, paid
    account.usage_checkpoint_bytes = checkpoint
    if settled_at is not None:
        account.last_synced_at = settled_at
    return not blocked


def _settle_reading(
    session: AsyncSession,
    ctx: _Context,
    state: QuotaClientState,
    read_at: datetime,
) -> None:
    """Сверка с прочитанным счётчиком: расход и события строго по порядку.

    Все неприменённые события должны быть созданы до чтения. Уменьшение
    счётчика или смена строки статистики (сброс/пересоздание клиента) не
    считается новым трафиком: учитывается только расход с начала новой эпохи,
    а расхождение фиксируется для администратора.
    """
    if state.used_bytes is None or ctx.server is None:
        return
    account = ctx.account
    server = ctx.server
    if account.server_id is not None and account.server_id != server.id:
        # Счётчик прежнего сервера больше не прочитать.
        _lose_baseline(ctx, "Сменился сервер услуги")
    if any(event.status == EVENT_UNCERTAIN for event in ctx.events):
        # До решения администратора подтверждённые остатки не меняются; квота
        # панели остаётся нижней границей и учитывает весь новый расход.
        return
    used = state.used_bytes
    checkpoint = account.usage_checkpoint_bytes
    if checkpoint is None:
        # Первая точка отсчёта на этом сервере: прежний расход не списывается,
        # поэтому порядок событий относительно него не важен.
        account.usage_checkpoint_bytes = used
    elif used < checkpoint or (
        account.traffic_row_id is not None
        and state.traffic_row_id is not None
        and state.traffic_row_id != account.traffic_row_id
    ):
        note = (
            f"Счётчик панели сброшен или клиент пересоздан: было {checkpoint} "
            f"(строка {account.traffic_row_id}), стало {used} "
            f"(строка {state.traffic_row_id}). Расход между последней сверкой и "
            "сбросом панели неизвестен и не списан."
        )
        account.conflict = note
        _record_ledger(
            session, account, kind=LEDGER_REBASE, source_key=None,
            free_before=account.free_bytes, paid_before=account.paid_bytes, note=note,
        )
        logger.warning("whitelist user=%s: %s", account.user_id, note)
        # Новая эпоха начинается с нуля; привязки старой эпохи недействительны.
        account.usage_checkpoint_bytes = 0
        for event in ctx.events:
            if is_open(event):
                event.anchor_bytes = None
    account.traffic_row_id = state.traffic_row_id
    account.server_id = server.id
    _settle_ordered(
        ctx, ctx.events, used=used, last_online=_last_online(state), read_at=read_at
    )


def _lose_baseline(ctx: _Context, reason: str) -> None:
    """Прежний счётчик больше не прочитать (клиент удалён, сменился сервер).

    Расход до ожидающих событий на нём неизвестен, поэтому они становятся
    неопределёнными, а не применяются с нулевым расходом.
    """
    account = ctx.account
    if account.usage_checkpoint_bytes is not None:
        for event in ctx.events:
            if event.status == EVENT_PENDING:
                event.status = EVENT_UNCERTAIN
                event.anchor_min_bytes = account.usage_checkpoint_bytes
                event.anchor_max_bytes = None
                _append_note(event, f"{reason}: расход до события не прочитан")
    account.usage_checkpoint_bytes = None
    account.traffic_row_id = None


@dataclass(slots=True)
class _Context:
    user: User
    client: VpnClient | None
    account: WhitelistAccount
    server: Server | None
    access: AccessState
    events: list[WhitelistLedger] = field(default_factory=list)


async def _load_context(
    session: AsyncSession, user_id: int, now: datetime, *, create: bool
) -> _Context | None:
    user = await session.get(User, user_id)
    if user is None:
        return None
    account = await get_account(session, user_id, create=create)
    if account is None:
        return None
    client = await VpnClientRepository(session).get_for_user(user_id)
    server = await get_active_server(session)
    return _Context(
        user=user,
        client=client,
        account=account,
        server=server,
        access=access_state(client, now),
        events=await list_open_events(session, user_id),
    )


async def _read_panel(
    ctx: _Context, updater: PanelUpdater
) -> tuple[QuotaClientState | None, str | None]:
    """Читает клиента whitelist-панели; (None, ошибка) при недоступности."""
    if not server_ready(ctx.server) or not ctx.account.panel_email:
        return None, None
    assert ctx.server is not None
    try:
        return await updater.read_quota_client(ctx.server, ctx.account.panel_email), None
    except PanelUpdateError as exc:
        return None, str(exc)


async def _refresh_usage(
    session: AsyncSession, ctx: _Context, updater: PanelUpdater, now: datetime
) -> tuple[QuotaClientState | None, str | None]:
    """Читает счётчик под блокировкой пользователя и сверяет учёт.

    Чтение выполняется после всех сохранённых событий пользователя, поэтому
    может их привязать.
    """
    state, error = await _read_panel(ctx, updater)
    if state is not None and ctx.server is not None:
        _settle_reading(session, ctx, state, now)
        _detect_external_disable(ctx, state, now)
    return state, error


def _detect_external_disable(ctx: _Context, state: QuotaClientState, now: datetime) -> None:
    """Ручное отключение клиента на панели не снимается автоматически.

    Отключение панелью по исчерпанию квоты или сроку — штатное состояние.
    Иное отключение подтверждённо включённого клиента считается решением
    администратора и сохраняется как блокировка.
    """
    if state.enable or ctx.account.applied_enable is not True or ctx.account.admin_blocked:
        return
    expired = 0 < state.expiry_ms <= _ms(now)
    if state.depleted or expired or state.used_bytes is None:
        return
    ctx.account.admin_blocked = True
    ctx.account.conflict = "Клиент отключён на панели вручную; автоматическое включение остановлено"
    mark_dirty(ctx.account)
    logger.warning("whitelist user=%s: клиент отключён на панели вручную", ctx.user.id)


def _consistent_anchor(ctx: _Context, state: QuotaClientState | None) -> int | None:
    """Счётчик текущего чтения, если он продолжает эпоху ожидающих событий."""
    if state is None or state.used_bytes is None or ctx.server is None:
        return None
    account = ctx.account
    if account.server_id != ctx.server.id or state.traffic_row_id != account.traffic_row_id:
        return None
    floor = account.usage_checkpoint_bytes or 0
    for event in ctx.events:
        if is_open(event):
            for bound in (event.anchor_bytes, event.anchor_max_bytes):
                if bound is not None:
                    floor = max(floor, bound)
    return state.used_bytes if state.used_bytes >= floor else None


async def _record_event(
    session: AsyncSession,
    ctx: _Context,
    *,
    kind: str,
    source_key: str,
    free_set: int | None = None,
    paid_delta: int | None = None,
    payment_id: int | None,
    actor_user_id: int | None,
    note: str,
    now: datetime,
    reading: QuotaClientState | None,
) -> WhitelistLedger | None:
    """Записывает событие учёта ровно один раз на ``source_key`` (без commit).

    Событие сразу меняет подтверждённые остатки, только если расход до него
    известен: сверка этой операции прошла и не оставила неприменённых событий,
    либо у клиента панели нет точки отсчёта (прежний расход не списывается).
    Иначе оно сохраняется как ожидающее, а прежние остатки не меняются.
    """
    if await _ledger_exists(session, source_key):
        return None
    account = ctx.account
    open_events = [event for event in ctx.events if is_open(event)]
    measured = reading is not None and reading.used_bytes is not None
    no_baseline = account.panel_email is None or account.usage_checkpoint_bytes is None
    event = WhitelistLedger(
        user_id=account.user_id,
        kind=kind,
        source_key=source_key,
        payment_request_id=payment_id,
        actor_user_id=actor_user_id,
        note=note,
        free_set=free_set,
        paid_delta=paid_delta,
        created_at=now,
    )
    if not open_events and (measured or no_baseline or ctx.access.lifetime):
        event.free_before, event.paid_before = account.free_bytes, account.paid_bytes
        account.free_bytes, account.paid_bytes = apply_event(
            account.free_bytes, account.paid_bytes, event
        )
        event.free_after, event.paid_after = account.free_bytes, account.paid_bytes
        event.anchor_bytes = account.usage_checkpoint_bytes
        event.status = EVENT_SETTLED
    else:
        before = provisional_balances(account, open_events)
        event.free_before, event.paid_before = before
        event.free_after, event.paid_after = apply_event(*before, event)
        event.status = EVENT_PENDING
        # За неопределённым событием: точное значение счётчика сохраняется,
        # чтобы после решения администратора применить это событие точно.
        event.anchor_bytes = _consistent_anchor(ctx, reading) if open_events else None
        logger.info(
            "whitelist user=%s: событие %s ждёт сверки расхода", account.user_id, source_key
        )
    session.add(event)
    ctx.events.append(event)
    mark_dirty(account)
    await session.flush()
    return event


# --- Синхронизация с панелью --------------------------------------------------


@dataclass(slots=True)
class SyncOutcome:
    applied: bool
    pending: bool = False
    skipped: str | None = None
    error: str | None = None
    # Есть сохранённые события, ещё не сверенные с расходом на панели.
    unsettled: bool = False


async def _push(
    session: AsyncSession,
    ctx: _Context,
    updater: PanelUpdater,
    now: datetime,
    *,
    refresh: bool = True,
) -> SyncOutcome:
    """Применяет текущее состояние БД на панели (под блокировкой пользователя)."""
    account = ctx.account
    if not server_ready(ctx.server):
        return SyncOutcome(applied=False, pending=True, skipped="server_not_ready")
    assert ctx.server is not None
    if ctx.client is None:
        return SyncOutcome(applied=False, skipped="no_vpn_client")
    if account.panel_email is None and not (ctx.access.active or ctx.access.lifetime):
        # Клиент ещё не создавался, а доступ не активен — создавать нечего.
        account.applied_version = account.desired_version
        return SyncOutcome(applied=False, skipped="no_access")
    public_id = ctx.user.public_id or ctx.client.email or str(ctx.user.id)
    email, sub_id, secret = await provisioning.client_identity(
        session, ctx.client, public_id
    )
    if account.panel_email not in (None, email) or (
        account.server_id is not None and account.server_id != ctx.server.id
    ):
        # Сменилась идентичность подписки или сервер услуги: счётчик другой
        # панели не является базой для новой квоты.
        _lose_baseline(ctx, "Сменилась идентичность подписки или сервер услуги")
    account.panel_email = email
    version = account.desired_version
    error: str | None = None
    if refresh:
        _, error = await _refresh_usage(session, ctx, updater, now)
    inbound = target_inbound(ctx.server)
    assert inbound is not None
    spec = provisioning.build_provision_spec(
        email, sub_id, secret, [inbound], ctx.user.telegram_id
    )
    target = compute_target(account, ctx.access, now, ctx.events)
    try:
        state = await updater.apply_quota_client(ctx.server, spec, target)
    except PanelUpdateError as exc:
        error = str(exc)
        account.sync_attempts += 1
        account.last_error = error[:1000]
        account.next_sync_at = now + timedelta(
            seconds=min(3600, 60 * 2 ** min(account.sync_attempts - 1, 6))
        )
        logger.info("whitelist user=%s: применение отложено: %s", ctx.user.id, error)
        return SyncOutcome(applied=False, pending=True, error=error)

    if state.used_bytes is not None:
        # Чтение после записи: первая точка отсчёта (квота была задана от
        # нулевой базы) или сверка ожидающих событий меняют целевую квоту.
        _settle_reading(session, ctx, state, now)
        retarget = compute_target(account, ctx.access, now, ctx.events)
        if retarget != target:
            try:
                state = await updater.apply_quota_client(ctx.server, spec, retarget)
            except PanelUpdateError as exc:
                account.last_error = str(exc)[:1000]
                account.next_sync_at = now + timedelta(seconds=60)
                return SyncOutcome(applied=False, pending=True, error=str(exc))
            target = retarget
    account.applied_version = max(account.applied_version, version)
    account.applied_total_bytes = target.total_bytes
    account.applied_enable = target.enable
    account.applied_expiry_ms = target.expiry_ms
    account.applied_at = now
    account.sync_attempts = 0
    account.next_sync_at = None
    account.last_error = None
    await audit.record(
        session,
        action="whitelist.panel_applied",
        entity_type="whitelist_account",
        entity_id=account.id,
        payload={
            "server_id": ctx.server.id,
            "total_bytes": target.total_bytes,
            "enable": target.enable,
            "expiry_ms": target.expiry_ms,
        },
    )
    return SyncOutcome(applied=True)


async def _sync_locked(
    session: AsyncSession,
    user_id: int,
    updater: PanelUpdater,
    now: datetime | None = None,
) -> SyncOutcome:
    now = now or _utcnow()
    ctx = await _load_context(session, user_id, now, create=False)
    if ctx is None:
        return SyncOutcome(applied=False, skipped="no_account")
    outcome = await _push(session, ctx, updater, now)
    outcome.unsettled = any(is_open(event) for event in ctx.events)
    await release_applied_credits(session, ctx.account)
    await session.commit()
    return outcome


async def _sync_after_commit(
    session: AsyncSession,
    user_id: int,
    updater: PanelUpdater,
    now: datetime | None = None,
) -> SyncOutcome:
    """Применение после уже сохранённой операции: сбой не отменяет её.

    Выполняется в отдельной сессии (блокировка пользователя уже взята), чтобы
    откат после непредвиденной ошибки не затрагивал объекты вызывающего кода.
    Учёт остаётся несинхронизированным для очереди, а вызывающий код получает
    «применение ожидается» и может уведомить пользователя.
    """
    maker = async_sessionmaker(
        bind=session.bind, expire_on_commit=False, class_=AsyncSession
    )
    async with maker() as isolated:
        try:
            return await _sync_locked(isolated, user_id, updater, now)
        except Exception as exc:  # noqa: BLE001 - durable операция уже сохранена
            await isolated.rollback()
            logger.exception("whitelist user=%s: ошибка применения после commit", user_id)
            return SyncOutcome(applied=False, pending=True, error=type(exc).__name__)


@serialized_access("user_id", "user")
async def sync_user(
    session: AsyncSession,
    user_id: int,
    updater: PanelUpdater,
    now: datetime | None = None,
) -> SyncOutcome:
    """Применяет состояние учёта пользователя на whitelist-панели."""
    return await _sync_locked(session, user_id, updater, now)


async def after_access_change(
    session: AsyncSession, user_id: int, updater: PanelUpdater
) -> SyncOutcome:
    """Срок/доступ VPN изменился: перенести его на белосписочный конфиг.

    Вызывается внутри уже сериализованной операции пользователя. Бесплатный
    пакет здесь не выдаётся: изменение срока без оплаты не основание для выдачи.
    """
    account = await get_account(session, user_id)
    if account is None:
        return SyncOutcome(applied=False, skipped="no_account")
    mark_dirty(account)
    await session.commit()
    return await _sync_after_commit(session, user_id, updater)


async def process_due(
    session: AsyncSession, updater: PanelUpdater, *, limit: int = 50
) -> int:
    """Фоновая очередь: применяет несинхронизированные состояния с backoff."""
    server = await get_active_server(session)
    if not server_ready(server):
        return 0
    now = _utcnow()
    user_ids = (
        await session.scalars(
            select(WhitelistAccount.user_id)
            .where(WhitelistAccount.desired_version > WhitelistAccount.applied_version)
            .where(
                (WhitelistAccount.next_sync_at.is_(None))
                | (WhitelistAccount.next_sync_at <= now)
            )
            .order_by(WhitelistAccount.id)
            .limit(limit)
        )
    ).all()
    await session.commit()
    applied = 0
    for user_id in user_ids:
        try:
            outcome = await sync_user(session, user_id, updater)
            applied += int(outcome.applied)
        except Exception:  # noqa: BLE001 - одна запись не должна останавливать очередь
            await session.rollback()
            logger.exception("whitelist: ошибка фоновой синхронизации user=%s", user_id)
    return applied


class ReconcileOutcome(enum.Enum):
    """Результат сверки одного учёта по прочитанному состоянию панели."""

    CHANGED = "changed"  # сверен; квоту на панели нужно применить заново
    UNCHANGED = "unchanged"  # сверен; панель уже соответствует учёту
    BUSY = "busy"  # чтение не может быть применено: учёт изменился во время обхода
    GONE = "gone"  # учёт, пользователь или сервер больше не подходят для сверки


@serialized_access("user_id", "user")
async def _reconcile_one(
    session: AsyncSession,
    user_id: int,
    state: QuotaClientState,
    read_at: datetime,
    server_id: int | None = None,
) -> ReconcileOutcome:
    ctx = await _load_context(session, user_id, read_at, create=False)
    if ctx is None or not server_ready(ctx.server):
        return ReconcileOutcome.GONE
    assert ctx.server is not None
    if server_id is not None and ctx.server.id != server_id:
        # Чтение сделано на сервере, который уже не является активным.
        await session.commit()
        return ReconcileOutcome.GONE
    last = _aware(ctx.account.last_synced_at)
    if last is not None and last >= read_at:
        # Чтение устарело: другая операция уже сверила более новый счётчик.
        # Иначе старое значение было бы ошибочно принято за сброс счётчика.
        await session.commit()
        return ReconcileOutcome.BUSY
    if ctx.account.panel_email != state.email or any(
        (_aware(event.created_at) or read_at) >= read_at
        for event in ctx.events
        if is_open(event)
    ):
        # Событие сохранено во время пакетного чтения: значение могло быть
        # прочитано до него и не может служить его привязкой.
        await session.commit()
        return ReconcileOutcome.BUSY
    _settle_reading(session, ctx, state, read_at)
    _detect_external_disable(ctx, state, read_at)
    target = compute_target(ctx.account, ctx.access, read_at, ctx.events)
    changed = target != _applied_target(ctx.account)
    if changed:
        mark_dirty(ctx.account)
    await release_applied_credits(session, ctx.account)
    await session.commit()
    return ReconcileOutcome.CHANGED if changed else ReconcileOutcome.UNCHANGED


# --- Фоновая сверка расхода: обход всех учётов пачками ---------------------------

RECONCILE_BATCH_SIZE = 100
# Подряд идущих пачек, где не прочиталось ни одного клиента, до прерывания обхода.
RECONCILE_MAX_FAILED_BATCHES = 2
# Сколько прерываний на одном месте допускается, прежде чем обход пойдёт дальше.
RECONCILE_MAX_STALLED_RUNS = 3


@dataclass(slots=True)
class ReconcileReport:
    """Итог обхода учётов (накапливается между запусками, если обход прерывали).

    Каждый учёт попадает ровно в одну категорию:
    ``reconciled + skipped_no_client + skipped_busy + skipped_gone + errors``.
    """

    server_id: int
    started_at: datetime
    finished_at: datetime | None = None
    runs: int = 0
    batches: int = 0
    reconciled: int = 0
    changed: int = 0  # из reconciled: квоту на панели нужно применить заново
    skipped_no_client: int = 0  # на панели нет клиента
    skipped_busy: int = 0  # изменились во время обхода и не сверились даже при повторе
    skipped_gone: int = 0  # учёт удалён или перенесён во время обхода
    errors: int = 0  # панель не вернула состояние или сверка завершилась ошибкой
    retried_busy: int = 0  # из reconciled: сверены повторным проходом
    active_seconds: float = 0.0
    cursor: int = 0  # id последнего учёта, до которого дошёл обход
    remaining: int = 0  # при прерывании: учётов впереди курсора
    complete: bool = False
    aborted: str | None = None
    stalled_cursor: int | None = None
    stalled_runs: int = 0
    busy_ids: list[int] = field(default_factory=list)

    @property
    def skipped(self) -> int:
        return self.skipped_no_client + self.skipped_busy + self.skipped_gone

    @property
    def processed(self) -> int:
        return self.reconciled

    @property
    def accounts(self) -> int:
        return self.reconciled + self.skipped + self.errors


@dataclass(slots=True)
class ReconcileStatus:
    """Состояние и наблюдаемость фоновой сверки (хранится в памяти процесса).

    ``current`` — незавершённый обход: его курсор сохраняется между запусками,
    чтобы после сбоя панели обход продолжился, а не начался с первой пачки.
    """

    current: ReconcileReport | None = None
    last_report: ReconcileReport | None = None
    last_run_at: datetime | None = None
    last_run_note: str | None = None
    # Обход дошёл до конца (возможны пропуски и ошибки отдельных учётов).
    last_complete_at: datetime | None = None
    # Обход дошёл до конца без ошибок чтения и сверки.
    last_success_at: datetime | None = None
    last_success_started_at: datetime | None = None
    traversals_completed: int = 0
    runs_aborted: int = 0

    def success_age(self, now: datetime) -> timedelta | None:
        """Сколько прошло с завершения последнего обхода без ошибок."""
        return None if self.last_success_at is None else now - self.last_success_at

    def worst_case_staleness(self, now: datetime) -> timedelta | None:
        """Верхняя граница возраста данных учёта после последнего чистого обхода.

        Учёт мог быть прочитан в самом начале обхода, а не в его конце.
        """
        if self.last_success_started_at is None:
            return None
        return now - self.last_success_started_at


RECONCILE_STATUS = ReconcileStatus()

# Повтор после прерванного обхода и минимальная пауза между обходами, секунды.
RECONCILE_RETRY_SECONDS = 60
RECONCILE_MIN_IDLE_SECONDS = 60


def next_reconcile_delay(
    interval_seconds: float, elapsed_seconds: float, *, complete: bool
) -> float:
    """Пауза до следующего запуска обхода.

    Прерванный обход (панель недоступна) повторяется скоро, чтобы продолжить с
    курсора. Завершённый — не раньше ``interval`` от его начала и не слитно с
    предыдущим: долгий обход не превращается в непрерывную нагрузку на панель.
    """
    floor = min(interval_seconds, RECONCILE_RETRY_SECONDS)
    if not complete:
        return floor
    idle = min(interval_seconds, RECONCILE_MIN_IDLE_SECONDS)
    return max(interval_seconds - elapsed_seconds, idle)


async def _select_reconcile_rows(
    session: AsyncSession,
    server_id: int,
    *,
    after_id: int = 0,
    limit: int,
    account_ids: list[int] | None = None,
) -> list[tuple[int, int, str]]:
    """Следующая пачка учётов: стабильный курсор по id, а не по изменяемой метке."""
    query = (
        select(WhitelistAccount.id, WhitelistAccount.user_id, WhitelistAccount.panel_email)
        .where(WhitelistAccount.panel_email.is_not(None))
        .where(WhitelistAccount.panel_email != "")
        .where(WhitelistAccount.server_id == server_id)
        .order_by(WhitelistAccount.id)
        .limit(limit)
    )
    if account_ids is None:
        query = query.where(WhitelistAccount.id > after_id)
    else:
        query = query.where(WhitelistAccount.id.in_(account_ids))
    rows = [
        (account_id, user_id, email)
        for account_id, user_id, email in (await session.execute(query)).all()
        if email
    ]
    await session.commit()
    return rows


@dataclass(slots=True)
class _BatchResult:
    busy: list[int] = field(default_factory=list)  # id учётов для повторной сверки
    panel_failed: bool = False  # ни один клиент из пачки не прочитался


async def _reconcile_batch(
    session: AsyncSession,
    updater: PanelUpdater,
    server: Server,
    rows: list[tuple[int, int, str]],
    report: ReconcileReport,
    *,
    retry: bool = False,
) -> _BatchResult:
    """Читает пачку одной сессией панели и сверяет учёты по одному.

    Сбой одного учёта не останавливает остальные. Если не прочитался ни один
    клиент пачки, ничего не учитывается — решение (повтор или пропуск) за вызывающим.
    """
    read_at = _utcnow()
    emails = [email for _, _, email in rows]
    try:
        states = await updater.read_quota_clients(server, emails)
    except PanelUpdateError:
        states = {}
    all_failed = all(
        email not in states or isinstance(states[email], PanelUpdateError)
        for email in emails
    )
    result = _BatchResult(panel_failed=all_failed and len(rows) > 1)
    if result.panel_failed:
        return result
    for account_id, user_id, email in rows:
        state = states.get(email, PanelUpdateError("нет в ответе панели"))
        if isinstance(state, PanelUpdateError):
            report.errors += 1
            continue
        if state is None:
            report.skipped_no_client += 1
            continue
        try:
            outcome = await _reconcile_one(session, user_id, state, read_at, server.id)
        except Exception:  # noqa: BLE001 - один учёт не должен останавливать обход
            await session.rollback()
            logger.exception("whitelist: ошибка сверки расхода user=%s", user_id)
            report.errors += 1
            continue
        if outcome is ReconcileOutcome.BUSY:
            if retry:
                report.skipped_busy += 1
            else:
                result.busy.append(account_id)
        elif outcome is ReconcileOutcome.GONE:
            report.skipped_gone += 1
        else:
            report.reconciled += 1
            report.changed += int(outcome is ReconcileOutcome.CHANGED)
    return result


async def _retry_busy(
    session: AsyncSession,
    updater: PanelUpdater,
    server: Server,
    report: ReconcileReport,
    *,
    batch_size: int,
    pause_seconds: float,
    sleep: Callable[[float], Awaitable[object]],
) -> None:
    """Один повторный проход по учётам, изменившимся между чтением и сверкой."""
    pending = list(dict.fromkeys(report.busy_ids))
    report.busy_ids = []
    before = report.reconciled
    for offset in range(0, len(pending), batch_size):
        chunk = pending[offset:offset + batch_size]
        if offset and pause_seconds > 0:
            await sleep(pause_seconds)
        rows = await _select_reconcile_rows(
            session, server.id, limit=batch_size, account_ids=chunk
        )
        report.skipped_gone += len(chunk) - len(rows)
        if not rows:
            continue
        report.batches += 1
        result = await _reconcile_batch(session, updater, server, rows, report, retry=True)
        if result.panel_failed:
            report.skipped_busy += len(rows)
    report.retried_busy = report.reconciled - before


async def _finish_reconcile(
    session: AsyncSession, status: ReconcileStatus, report: ReconcileReport
) -> None:
    now = _utcnow()
    if report.aborted is not None:
        status.runs_aborted += 1
        report.remaining = await session.scalar(
            select(func.count(WhitelistAccount.id))
            .where(WhitelistAccount.server_id == report.server_id)
            .where(WhitelistAccount.panel_email.is_not(None))
            .where(WhitelistAccount.id > report.cursor)
        ) or 0
        status.last_run_note = f"прервана: {report.aborted}"
        logger.warning(
            "whitelist: сверка расхода прервана (%s): обработано %s, ошибок %s, "
            "впереди %s; продолжится с учёта id>%s",
            report.aborted, report.accounts, report.errors, report.remaining, report.cursor,
        )
        return
    report.complete = True
    report.finished_at = now
    status.last_report = report
    status.last_complete_at = now
    status.last_run_note = "обход завершён"
    status.traversals_completed += 1
    if report.errors == 0:
        status.last_success_at = now
        status.last_success_started_at = report.started_at
    status.current = None
    log = logger.warning if report.errors else logger.info
    log(
        "whitelist: сверка расхода завершена за %.1f с (активно %.1f с), пачек %s, "
        "сверено %s (повторно %s, требуют применения %s), пропущено %s "
        "(нет клиента %s, изменились %s, удалены %s), ошибок %s",
        (now - report.started_at).total_seconds(), report.active_seconds, report.batches,
        report.reconciled, report.retried_busy, report.changed, report.skipped,
        report.skipped_no_client, report.skipped_busy, report.skipped_gone, report.errors,
    )


async def reconcile_cycle(
    session: AsyncSession,
    updater: PanelUpdater,
    *,
    batch_size: int = RECONCILE_BATCH_SIZE,
    pause_seconds: float = 0.0,
    status: ReconcileStatus | None = None,
    sleep: Callable[[float], Awaitable[object]] = asyncio.sleep,
) -> ReconcileReport:
    """Полный обход учётов whitelist-сервера ограниченными пачками.

    Пачки берутся по возрастанию ``id`` (курсор не зависит от метки сверки,
    которую пропущенные учёты не обновляют), между пачками — пауза. Учёты,
    добавленные во время обхода, получают больший ``id`` и попадают в него;
    удалённые просто не выбираются. Учёты, изменившиеся между чтением и сверкой
    (продление, покупка, другая сверка), повторяются одним проходом в конце.

    Если панель недоступна (``RECONCILE_MAX_FAILED_BATCHES`` пачек подряд без
    единого прочитанного клиента), обход прерывается; следующий вызов с тем же
    ``status`` продолжает с того же места, а не с первой пачки. Если на одном
    месте обход прерывался ``RECONCILE_MAX_STALLED_RUNS`` раз, эта область
    пропускается как ошибки, чтобы обход не зацикливался.
    Возвращает накопленный отчёт обхода; ``complete`` — обход дошёл до конца.
    """
    status = status if status is not None else ReconcileStatus()
    batch_size = max(1, batch_size)
    started = time.monotonic()
    status.last_run_at = _utcnow()
    server = await get_active_server(session)
    if not server_ready(server):
        status.current = None
        status.last_run_note = "сервер whitelist не готов"
        return ReconcileReport(
            server_id=0, started_at=status.last_run_at, finished_at=status.last_run_at,
            aborted="server_not_ready",
        )
    assert server is not None
    report = status.current
    if report is None or report.server_id != server.id:
        report = status.current = ReconcileReport(server_id=server.id, started_at=_utcnow())
    report.runs += 1
    report.aborted = None
    may_pass_stall = (
        report.stalled_cursor == report.cursor
        and report.stalled_runs >= RECONCILE_MAX_STALLED_RUNS
    )
    failed: list[list[tuple[int, int, str]]] = []
    scan = report.cursor
    first_batch = True

    def flush_failed() -> None:
        for lost in failed:
            report.errors += len(lost)
        failed.clear()

    try:
        while True:
            rows = await _select_reconcile_rows(
                session, server.id, after_id=scan, limit=batch_size
            )
            if not rows:
                break
            if not first_batch and pause_seconds > 0:
                await sleep(pause_seconds)
            first_batch = False
            current = await get_active_server(session)
            if current is None or current.id != server.id or not server_ready(current):
                # Сервер заменён: курсор относится к прежнему, обход начнётся заново.
                status.current = None
                report.aborted = "server_changed"
                break
            report.batches += 1
            result = await _reconcile_batch(session, updater, current, rows, report)
            report.busy_ids.extend(result.busy)
            scan = rows[-1][0]
            if not result.panel_failed:
                flush_failed()
                report.cursor = scan
                continue
            failed.append(rows)
            if len(failed) < RECONCILE_MAX_FAILED_BATCHES:
                continue
            if may_pass_stall:
                flush_failed()
                report.cursor = scan
                report.stalled_cursor, report.stalled_runs = None, 0
                may_pass_stall = False
                continue
            report.aborted = "panel_unavailable"
            if report.stalled_cursor == report.cursor:
                report.stalled_runs += 1
            else:
                report.stalled_cursor, report.stalled_runs = report.cursor, 1
            break
        if report.aborted is None:
            flush_failed()
            report.cursor = scan
            report.stalled_cursor, report.stalled_runs = None, 0
            await _retry_busy(
                session, updater, server, report,
                batch_size=batch_size, pause_seconds=pause_seconds, sleep=sleep,
            )
    finally:
        report.active_seconds += time.monotonic() - started
    await _finish_reconcile(session, status, report)
    return report


async def reconcile_usage(
    session: AsyncSession,
    updater: PanelUpdater,
    *,
    limit: int = RECONCILE_BATCH_SIZE,
    pause_seconds: float = 0.0,
    status: ReconcileStatus | None = None,
) -> int:
    """Фоновая сверка расхода: обходит все учёты пачками по ``limit``.

    Возвращает число учётов, требующих повторного применения квоты.
    """
    report = await reconcile_cycle(
        session, updater, batch_size=limit, pause_seconds=pause_seconds, status=status
    )
    return report.changed


# --- Бизнес-события -------------------------------------------------------------


async def grant_for_subscription_payment(
    session: AsyncSession,
    payment: PaymentRequest,
    updater: PanelUpdater,
    actor_user_id: int | None,
    now: datetime | None = None,
) -> bool:
    """Выдаёт бесплатный пакет за подтверждённую оплату подписки (без commit).

    Сначала сверяется расход (купленный остаток уменьшается по факту), затем
    бесплатный остаток заменяется настроенным объёмом. При недоступной
    статистике выдача сохраняется как ожидающее событие: прежние остатки не
    заменяются, пока расход до оплаты не будет сверен. Оплата на несколько
    месяцев — одна выдача. Повтор той же оплаты ничего не выдаёт.
    """
    if payment.kind != PAYMENT_KIND_SUBSCRIPTION:
        return False
    config = await get_config(session)
    if not config.service_enabled:
        return False
    source_key = f"payment:{payment.id}"
    if await _ledger_exists(session, source_key):
        return False
    now = now or _utcnow()
    ctx = await _load_context(session, payment.user_id, now, create=True)
    if ctx is None:
        return False
    state, _ = await _refresh_usage(session, ctx, updater, now)
    event = await _record_event(
        session, ctx,
        kind=LEDGER_FREE_GRANT, source_key=source_key,
        free_set=config.paid_free_bytes, payment_id=payment.id,
        actor_user_id=actor_user_id,
        note=f"Оплата подписки {payment.payment_code} ({payment.period_days} дн.)",
        now=now, reading=state,
    )
    return event is not None


async def grant_for_trial(
    session: AsyncSession,
    user_id: int,
    updater: PanelUpdater,
    now: datetime | None = None,
) -> bool:
    """Однократная выдача пакета пробного периода (без commit)."""
    config = await get_config(session)
    if not config.service_enabled:
        return False
    source_key = f"trial:{user_id}"
    if await _ledger_exists(session, source_key):
        return False
    now = now or _utcnow()
    ctx = await _load_context(session, user_id, now, create=True)
    if ctx is None:
        return False
    state, _ = await _refresh_usage(session, ctx, updater, now)
    event = await _record_event(
        session, ctx,
        kind=LEDGER_FREE_GRANT, source_key=source_key,
        free_set=config.trial_free_bytes, payment_id=None,
        actor_user_id=user_id, note="Пробный период", now=now, reading=state,
    )
    return event is not None


@dataclass(slots=True)
class PurchaseResult:
    credited: bool
    already_applied: bool = False
    size_bytes: int = 0
    sync: SyncOutcome | None = None


async def confirm_traffic_payment(
    session: AsyncSession,
    payment: PaymentRequest,
    actor_user_id: int | None,
    updater: PanelUpdater,
    now: datetime | None = None,
) -> PurchaseResult:
    """Начисляет оплаченный объём ровно один раз (вызов под блокировкой).

    Срок подписки и бесплатный остаток не меняются. Если подписка истекла после
    создания заявки, объём всё равно начисляется, а конфиг остаётся выключенным
    до продления. Начисление сохраняется и при недоступной статистике: тогда
    оно ждёт сверки расхода как событие учёта.
    """
    if payment.kind != PAYMENT_KIND_TRAFFIC:
        raise WhitelistError("Заявка не относится к покупке трафика")
    size = int(payment.traffic_bytes or 0)
    if payment.status == PaymentStatus.APPLIED:
        return PurchaseResult(credited=False, already_applied=True, size_bytes=size)
    if payment.status != PaymentStatus.WAITING_ADMIN:
        raise WhitelistError(
            f"Заявка в статусе {payment.status.value}, подтверждение невозможно"
        )
    if size <= 0:
        raise WhitelistError("В заявке не указан объём трафика")
    now = now or _utcnow()
    ctx = await _load_context(session, payment.user_id, now, create=True)
    if ctx is None:
        raise WhitelistError("Пользователь заявки не найден")
    source_key = f"payment:{payment.id}"
    credited = False
    if not await _ledger_exists(session, source_key):
        # Перед финансовой операцией сверяем расход, чтобы прошлое превышение
        # лимита не списывалось из новой покупки.
        state, _ = await _refresh_usage(session, ctx, updater, now)
        await _record_event(
            session, ctx,
            kind=LEDGER_PURCHASE, source_key=source_key, paid_delta=size,
            payment_id=payment.id, actor_user_id=actor_user_id,
            note=f"Покупка {payment.payment_code}", now=now, reading=state,
        )
        credited = True
    payment.status = PaymentStatus.APPLIED
    payment.confirmed_at = payment.confirmed_at or now
    payment.applied_at = now
    # Ожидание применения фиксируется вместе с начислением: если процесс прервётся
    # до обращения к панели, заявка не будет выглядеть применённой. Снимет его
    # применение этой версии учёта (release_applied_credits).
    payment.apply_pending_version = ctx.account.desired_version
    await audit.record(
        session,
        action="whitelist.purchase_credited",
        actor_user_id=actor_user_id,
        entity_type="payment_request",
        entity_id=payment.id,
        payload={"traffic_bytes": size, "credited": credited},
    )
    # Начисление сохраняется до обращения к панели.
    await session.commit()
    outcome = await _sync_after_commit(session, payment.user_id, updater, now)
    # Статус снимался в отдельной сессии: перечитываем его для вызывающего кода.
    await session.refresh(payment, ["apply_pending_version"])
    return PurchaseResult(credited=credited, size_bytes=size, sync=outcome)


@serialized_access("user_id", "user")
async def set_admin_block(
    session: AsyncSession,
    user_id: int,
    blocked: bool,
    actor_user_id: int | None,
    updater: PanelUpdater,
) -> SyncOutcome:
    account = await get_account(session, user_id)
    if account is None:
        raise WhitelistError("У пользователя нет учёта услуги")
    account.admin_blocked = blocked
    if not blocked:
        account.conflict = None
        # Панель ещё хранит ручное отключение. Подтверждение «клиент включён»
        # устарело: пока решение не применено, отключение не считается новым
        # ручным (иначе чтение/повтор сразу вернули бы блокировку). Применение
        # заново зафиксирует applied_enable.
        account.applied_enable = None
    mark_dirty(account)
    await audit.record(
        session,
        action="whitelist.admin_block" if blocked else "whitelist.admin_unblock",
        actor_user_id=actor_user_id,
        entity_type="whitelist_account",
        entity_id=account.id,
    )
    await session.commit()
    return await _sync_locked(session, user_id, updater)


@serialized_access("user_id", "user")
async def adjust_balance(
    session: AsyncSession,
    user_id: int,
    *,
    free_bytes: int | None,
    paid_bytes: int | None,
    actor_user_id: int | None,
    reason: str,
    updater: PanelUpdater,
) -> SyncOutcome:
    """Ручная корректировка остатков администратором (с записью в журнал).

    Остатки задаются на текущее значение счётчика, поэтому при существующем
    клиенте панели нужна успешная сверка. Корректировка закрывает ожидающие и
    неопределённые события: администратор задаёт оба остатка явно.
    """
    now = _utcnow()
    ctx = await _load_context(session, user_id, now, create=True)
    assert ctx is not None
    account = ctx.account
    state, error = await _refresh_usage(session, ctx, updater, now)
    measured = state is not None and state.used_bytes is not None
    if account.panel_email is not None and account.usage_checkpoint_bytes is not None:
        if not measured:
            raise WhitelistError(
                "Сервер услуги не вернул расход"
                + (f" ({error})" if error else "")
                + ": корректировка возможна после сверки"
            )
    open_events = [event for event in ctx.events if is_open(event)]
    if open_events and (free_bytes is None or paid_bytes is None):
        raise WhitelistError(
            "Есть начисления, ожидающие сверки расхода: укажите оба остатка явно"
        )
    free_before, paid_before = account.free_bytes, account.paid_bytes
    if free_bytes is not None:
        account.free_bytes = max(0, free_bytes)
    if paid_bytes is not None:
        account.paid_bytes = max(0, paid_bytes)
    if measured and open_events:
        # Остатки заданы на текущий счётчик: он становится новой точкой отсчёта.
        assert state is not None and ctx.server is not None
        account.usage_checkpoint_bytes = state.used_bytes
        account.traffic_row_id = state.traffic_row_id
        account.server_id = ctx.server.id
        account.last_synced_at = now
    for event in open_events:
        event.status = EVENT_SETTLED
        _append_note(event, "закрыто корректировкой администратора")
    account.conflict = None
    _record_ledger(
        session, account, kind=LEDGER_ADJUST, source_key=None,
        free_before=free_before, paid_before=paid_before,
        actor_user_id=actor_user_id, note=reason[:500],
    )
    mark_dirty(account)
    await session.commit()
    return await _sync_locked(session, user_id, updater, now)


@serialized_access("user_id", "user")
async def resolve_uncertain(
    session: AsyncSession,
    user_id: int,
    *,
    choice: str,
    actor_user_id: int | None,
    reason: str,
    updater: PanelUpdater,
) -> SyncOutcome:
    """Решение администратора: неразделённый расход до или после события.

    Применяет первое неопределённое событие с выбранной привязкой (граница
    прочитанного периода), затем продолжает обычную сверку по порядку.
    """
    if choice not in (RESOLVE_BEFORE, RESOLVE_AFTER):
        raise WhitelistError("Укажите, куда отнести расход: до или после события")
    now = _utcnow()
    ctx = await _load_context(session, user_id, now, create=False)
    if ctx is None:
        raise WhitelistError("У пользователя нет учёта услуги")
    event = next((e for e in ctx.events if e.status == EVENT_UNCERTAIN), None)
    if event is None:
        raise WhitelistError("Нет начислений, ожидающих решения")
    if uncertain_outcomes(ctx.account, ctx.events) is None:
        raise WhitelistError(
            "Расход за этот период не прочитан с сервера: задайте остатки через /wladjust"
        )
    assert event.anchor_min_bytes is not None and event.anchor_max_bytes is not None
    before = choice == RESOLVE_BEFORE
    event.anchor_bytes = event.anchor_max_bytes if before else event.anchor_min_bytes
    event.status = EVENT_PENDING
    span = event.anchor_max_bytes - event.anchor_min_bytes
    _append_note(
        event,
        f"Решение администратора: расход {span} байт отнесён "
        f"{'до' if before else 'после'} события ({reason[:200]})",
    )
    # Счётчик на конце периода прочитан после события — применяем по нему.
    _settle_ordered(
        ctx, [event], used=event.anchor_max_bytes, last_online=None, read_at=None
    )
    await audit.record(
        session,
        action="whitelist.uncertain_resolved",
        actor_user_id=actor_user_id,
        entity_type="whitelist_account",
        entity_id=ctx.account.id,
        payload={"event_id": event.id, "choice": choice, "span": span},
    )
    mark_dirty(ctx.account)
    await session.commit()
    return await _sync_locked(session, user_id, updater, now)


# --- Пользовательский обзор ---------------------------------------------------


STATUS_NOT_LAUNCHED = "not_launched"
STATUS_NO_ACCESS = "no_access"
STATUS_EXPIRED = "expired"
STATUS_LIFETIME = "lifetime"
STATUS_ACTIVE = "active"
STATUS_EXHAUSTED = "exhausted"
STATUS_BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class AwaitingCredit:
    """Сохранённое начисление, ещё не сверенное с расходом."""

    free_set: int | None
    paid_delta: int | None


@dataclass(slots=True)
class Overview:
    status: str
    # Подтверждённые остатки на момент last_synced_at (без ожидающих начислений).
    free_bytes: int = 0
    paid_bytes: int = 0
    expires_at: datetime | None = None
    stale: bool = False
    last_synced_at: datetime | None = None
    pending: bool = False
    can_buy: bool = False
    server_ready: bool = False
    packages: list[TrafficPackage] = field(default_factory=list)
    awaiting: list[AwaitingCredit] = field(default_factory=list)
    # Расход нельзя разделить автоматически — нужно решение администратора.
    uncertain: bool = False


@serialized_access("user_id", "user")
async def user_overview(
    session: AsyncSession,
    user_id: int,
    updater: PanelUpdater | None,
    now: datetime | None = None,
) -> Overview:
    """Остатки пользователя; при доступной панели — с актуальной сверкой.

    Чтение баланса никогда не включает клиента: применяется только целевое
    состояние, вычисленное из БД (с учётом блокировок и срока).
    """
    now = now or _utcnow()
    config = await get_config(session)
    client = await VpnClientRepository(session).get_for_user(user_id)
    access = access_state(client, now)
    server = await get_active_server(session)
    ready = server_ready(server)
    packages = await list_packages(session)
    account = await get_account(session, user_id)
    overview = Overview(
        status=STATUS_NOT_LAUNCHED,
        expires_at=access.expires_at,
        server_ready=ready,
        packages=packages,
    )
    if not config.service_enabled:
        await session.commit()
        return overview
    stale = False
    events: list[WhitelistLedger] = []
    if account is not None and updater is not None and ready:
        ctx = await _load_context(session, user_id, now, create=False)
        assert ctx is not None
        state, error = await _refresh_usage(session, ctx, updater, now)
        stale = error is not None or (state is None and account.panel_email is not None)
        events = [event for event in ctx.events if is_open(event)]
        if compute_target(account, access, now, events) != _applied_target(account):
            mark_dirty(account)
    elif account is not None:
        stale = account.panel_email is not None
        events = await list_open_events(session, user_id)
    overview.can_buy = access.active and not access.lifetime and bool(packages)
    remaining = 0
    if account is not None:
        overview.free_bytes = account.free_bytes
        overview.paid_bytes = account.paid_bytes
        overview.last_synced_at = _aware(account.last_synced_at)
        overview.pending = (
            account.desired_version > account.applied_version or account.last_error is not None
        )
        overview.awaiting = [
            AwaitingCredit(free_set=event.free_set, paid_delta=event.paid_delta)
            for event in events
        ]
        overview.uncertain = any(event.status == EVENT_UNCERTAIN for event in events)
        remaining = sum(provisional_balances(account, events))
    overview.stale = stale
    if access.lifetime:
        overview.status = STATUS_LIFETIME
    elif not access.active:
        overview.status = STATUS_EXPIRED if access.expires_at is not None else STATUS_NO_ACCESS
    elif account is not None and account.admin_blocked:
        overview.status = STATUS_BLOCKED
    elif remaining <= 0:
        overview.status = STATUS_EXHAUSTED
    else:
        overview.status = STATUS_ACTIVE
    if access.lifetime and account is not None and account.admin_blocked:
        overview.status = STATUS_BLOCKED
    await session.commit()
    return overview


def _applied_target(account: WhitelistAccount) -> QuotaTarget | None:
    if account.applied_total_bytes is None or account.applied_enable is None:
        return None
    return QuotaTarget(
        total_bytes=account.applied_total_bytes,
        enable=account.applied_enable,
        expiry_ms=account.applied_expiry_ms or 0,
    )


# --- Выдача услуги нынешним пользователям ------------------------------------

ORIGIN_LIFETIME = "lifetime"
ORIGIN_PAID = "paid"
ORIGIN_TRIAL = "trial"
ORIGIN_AMBIGUOUS = "ambiguous"
ORIGIN_INACTIVE = "inactive"


async def classify_origin(
    session: AsyncSession, user: User, client: VpnClient | None, now: datetime
) -> str:
    """Происхождение текущего доступа по достоверным данным.

    ``trial_used`` остаётся истинным после перехода на оплату, поэтому trial
    определяется только при отсутствии оплаты, покрывающей текущий срок.
    Доступ без оплаты и без следа trial (привязка, ручное продление) — неоднозначен.
    """
    access = access_state(client, now)
    if access.lifetime:
        return ORIGIN_LIFETIME
    if not access.active:
        return ORIGIN_INACTIVE
    paid = await session.scalar(
        select(PaymentRequest.id)
        .where(PaymentRequest.user_id == user.id)
        .where(PaymentRequest.kind == PAYMENT_KIND_SUBSCRIPTION)
        .where(PaymentRequest.status == PaymentStatus.APPLIED)
        .where(PaymentRequest.target_expires_at > now)
        .limit(1)
    )
    if paid is not None:
        return ORIGIN_PAID
    if user.trial_used:
        any_payment = await session.scalar(
            select(PaymentRequest.id)
            .where(PaymentRequest.user_id == user.id)
            .where(PaymentRequest.kind == PAYMENT_KIND_SUBSCRIPTION)
            .where(
                PaymentRequest.status.in_([PaymentStatus.APPLIED, PaymentStatus.CONFIRMED])
            )
            .limit(1)
        )
        if any_payment is None:
            return ORIGIN_TRIAL
    return ORIGIN_AMBIGUOUS


@dataclass(slots=True)
class RolloutPlan:
    counts: dict[str, int] = field(default_factory=dict)
    already_served: int = 0
    ambiguous_users: list[tuple[int, str | None, datetime | None]] = field(
        default_factory=list
    )


async def rollout_plan(session: AsyncSession, now: datetime | None = None) -> RolloutPlan:
    now = now or _utcnow()
    plan = RolloutPlan()
    clients = (
        await session.scalars(
            select(VpnClient).options(
                selectinload(VpnClient.user), selectinload(VpnClient.mappings)
            )
        )
    ).all()
    served = set(
        (
            await session.scalars(
                select(WhitelistLedger.user_id).where(
                    WhitelistLedger.kind.in_(_FREE_GRANT_KINDS)
                )
            )
        ).all()
    )
    for client in clients:
        user = client.user
        if user is None:
            continue
        origin = await classify_origin(session, user, client, now)
        if origin == ORIGIN_INACTIVE:
            continue
        if origin != ORIGIN_LIFETIME and user.id in served:
            plan.already_served += 1
            continue
        plan.counts[origin] = plan.counts.get(origin, 0) + 1
        if origin == ORIGIN_AMBIGUOUS:
            plan.ambiguous_users.append(
                (user.telegram_id or 0, user.public_id, _aware(client.expires_at))
            )
    await session.commit()
    return plan


@dataclass(slots=True)
class RolloutReport:
    granted: dict[str, int] = field(default_factory=dict)
    skipped_existing: int = 0
    skipped_ambiguous: int = 0
    lifetime: int = 0


@serialized_access("user_id", "user")
async def _rollout_user(
    session: AsyncSession,
    user_id: int,
    include_ambiguous: bool,
    actor_user_id: int | None,
    now: datetime,
) -> str:
    config = await get_config(session)
    user = await session.get(User, user_id)
    client = await VpnClientRepository(session).get_for_user(user_id)
    if user is None:
        return "skip"
    origin = await classify_origin(session, user, client, now)
    if origin == ORIGIN_INACTIVE:
        await session.commit()
        return "inactive"
    if origin == ORIGIN_AMBIGUOUS and not include_ambiguous:
        await session.commit()
        return "ambiguous_skipped"
    ctx = await _load_context(session, user_id, now, create=True)
    assert ctx is not None
    if origin == ORIGIN_LIFETIME:
        mark_dirty(ctx.account)
        await session.commit()
        return ORIGIN_LIFETIME
    already = await session.scalar(
        select(WhitelistLedger.id)
        .where(WhitelistLedger.user_id == user_id)
        .where(WhitelistLedger.kind.in_(_FREE_GRANT_KINDS))
        .limit(1)
    )
    if already is not None:
        mark_dirty(ctx.account)
        await session.commit()
        return "existing"
    size = config.trial_free_bytes if origin == ORIGIN_TRIAL else config.paid_free_bytes
    # Без сверки: при существующем клиенте панели выдача ждёт привязки к
    # расходу (обычно у нынешних пользователей клиента ещё нет).
    await _record_event(
        session, ctx,
        kind=LEDGER_ROLLOUT, source_key=f"rollout:{user_id}", free_set=size,
        payment_id=None, actor_user_id=actor_user_id,
        note=f"Начальная выдача услуги ({origin})", now=now, reading=None,
    )
    await session.commit()
    return origin


async def run_rollout(
    session: AsyncSession,
    updater: PanelUpdater,
    *,
    include_ambiguous: bool,
    actor_user_id: int | None,
    apply_limit: int = 50,
) -> RolloutReport:
    """Запускает услугу и выдаёт её нынешним активным пользователям.

    Повторный запуск не выдаёт второй начальный пакет и не меняет купленный
    остаток: выдача привязана к ключу ``rollout:<user>`` и пропускается при уже
    полученной выдаче за оплату/trial. Применение на панели идёт через очередь.
    """
    server = await get_active_server(session)
    if not server_ready(server):
        raise WhitelistError("Сервер услуги не готов: выполните синхронизацию inbound'ов")
    config = await get_config(session)
    if not config.service_enabled:
        config.service_enabled = True
        config.updated_at = _utcnow()
        await audit.record(
            session,
            action="whitelist.service_enabled",
            actor_user_id=actor_user_id,
            entity_type="whitelist_config",
            entity_id=1,
        )
    await session.commit()
    now = _utcnow()
    user_ids = (await session.scalars(select(VpnClient.user_id).order_by(VpnClient.id))).all()
    await session.commit()
    report = RolloutReport()
    for user_id in user_ids:
        outcome = await _rollout_user(session, user_id, include_ambiguous, actor_user_id, now)
        if outcome == "existing":
            report.skipped_existing += 1
        elif outcome == "ambiguous_skipped":
            report.skipped_ambiguous += 1
        elif outcome == ORIGIN_LIFETIME:
            report.lifetime += 1
        elif outcome in (ORIGIN_PAID, ORIGIN_TRIAL, ORIGIN_AMBIGUOUS):
            report.granted[outcome] = report.granted.get(outcome, 0) + 1
    await audit.record(
        session,
        action="whitelist.rollout",
        actor_user_id=actor_user_id,
        payload={
            "granted": report.granted,
            "existing": report.skipped_existing,
            "ambiguous_skipped": report.skipped_ambiguous,
            "lifetime": report.lifetime,
        },
    )
    await session.commit()
    await process_due(session, updater, limit=apply_limit)
    return report


@dataclass(slots=True)
class AdminSummary:
    accounts: int
    pending: int
    errors: int
    conflicts: int
    blocked: int
    # Учёты с начислениями, ожидающими сверки расхода / решения администратора.
    unsettled: int = 0
    uncertain: int = 0
    reconcile: ReconcileStatus | None = None


async def admin_summary(session: AsyncSession) -> AdminSummary:
    def count(*conditions):  # type: ignore[no-untyped-def]
        return select(func.count(WhitelistAccount.id)).where(*conditions)

    result = AdminSummary(
        accounts=await session.scalar(count()) or 0,
        pending=await session.scalar(
            count(WhitelistAccount.desired_version > WhitelistAccount.applied_version)
        ) or 0,
        errors=await session.scalar(count(WhitelistAccount.last_error.is_not(None))) or 0,
        conflicts=await session.scalar(count(WhitelistAccount.conflict.is_not(None))) or 0,
        blocked=await session.scalar(count(WhitelistAccount.admin_blocked.is_(True))) or 0,
        reconcile=RECONCILE_STATUS,
    )
    for status in _OPEN_EVENTS:
        users = await session.scalar(
            select(func.count(func.distinct(WhitelistLedger.user_id))).where(
                WhitelistLedger.status == status
            )
        ) or 0
        if status == EVENT_PENDING:
            result.unsettled = users
        else:
            result.uncertain = users
    return result


async def settle_before_removal(
    session: AsyncSession, user_id: int, updater: PanelUpdater
) -> None:
    """Последняя сверка расхода перед удалением клиента панели (без commit).

    Вызывается под блокировкой пользователя. После удаления счётчик уже не
    прочитать, поэтому ожидающие события привязываются сейчас, если возможно.
    """
    now = _utcnow()
    ctx = await _load_context(session, user_id, now, create=False)
    if ctx is not None:
        await _refresh_usage(session, ctx, updater, now)


async def forget_panel_client(session: AsyncSession, user_id: int) -> None:
    """После удаления клиента с панели следующая выдача начнёт новую точку отсчёта.

    Остатки (в т.ч. купленный) сохраняются. Начисления, которые так и не
    удалось сверить с расходом удалённого клиента, остаются неопределёнными.
    """
    ctx = await _load_context(session, user_id, _utcnow(), create=False)
    if ctx is None:
        return
    account = ctx.account
    _lose_baseline(ctx, "Клиент панели удалён вместе с подпиской")
    account.panel_email = None
    account.applied_total_bytes = None
    account.applied_enable = None
    account.applied_expiry_ms = None
    account.applied_version = account.desired_version

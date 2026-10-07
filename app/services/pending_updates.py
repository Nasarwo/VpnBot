from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    SERVER_PURPOSE_STANDARD,
    PaymentRequest,
    PendingServerUpdate,
    Server,
    User,
    VpnClient,
)
from app.db.repositories import (
    MappingRepository,
    PendingServerUpdateRepository,
    ServerRepository,
)
from app.services import audit, provisioning
from app.services.operation_lock import serialized_access
from app.services.panel_updater import PanelUpdateError, PanelUpdater, ServerUpdateResult

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PendingApplyResult:
    update_id: int
    server_id: int
    ok: bool
    error: str | None = None
    # Запись уже обработал другой обработчик: панели в этом вызове не менялись.
    already_done: bool = False


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _expiry_to_ms(expiry: datetime) -> int:
    return int(expiry.timestamp() * 1000)


def retry_delay(attempts: int) -> timedelta:
    """Backoff повтора после ``attempts`` неудачных попыток: 1 мин → 1 ч."""
    return timedelta(seconds=min(3600, 60 * 2 ** min(max(attempts, 1) - 1, 6)))


@dataclass(slots=True)
class RetryBackoff:
    """Backoff повторов в памяти процесса для записей без поля ``next_retry_at``.

    Используется для возобновления прерванных подтверждений: сбойная заявка не
    запрашивается каждый цикл и не вытесняет остальные. После рестарта процесса
    состояние пустое — заявка повторяется сразу, что безопасно: повтор идемпотентен.
    """

    attempts: dict[int, int] = field(default_factory=dict)
    next_at: dict[int, datetime] = field(default_factory=dict)

    def blocked(self, now: datetime) -> list[int]:
        return [key for key, when in self.next_at.items() if when > now]

    def failed(self, key: int, now: datetime) -> timedelta:
        attempts = self.attempts.get(key, 0) + 1
        self.attempts[key] = attempts
        delay = retry_delay(attempts)
        self.next_at[key] = now + delay
        return delay

    def succeeded(self, key: int) -> None:
        self.attempts.pop(key, None)
        self.next_at.pop(key, None)


async def enqueue_failed_servers(
    session: AsyncSession,
    *,
    vpn_client_id: int,
    payment_request_id: int | None,
    target_expires_at: datetime,
    failed_servers: list[ServerUpdateResult],
) -> list[PendingServerUpdate]:
    repo = PendingServerUpdateRepository(session)
    queued: list[PendingServerUpdate] = []
    for result in failed_servers:
        queued.append(
            await repo.upsert_pending(
                vpn_client_id=vpn_client_id,
                server_id=result.server_id,
                payment_request_id=payment_request_id,
                target_expires_at=target_expires_at,
                last_error=result.error,
            )
        )
    return queued


async def apply_pending_for_server(
    session: AsyncSession,
    server_id: int,
    updater: PanelUpdater,
) -> list[PendingApplyResult]:
    repo = PendingServerUpdateRepository(session)
    updates = await repo.list_pending_for_server(server_id)
    results: list[PendingApplyResult] = []
    for update in updates:
        results.append(await apply_pending_update(session, update, updater))
    return results


async def process_due(
    session: AsyncSession,
    updater: PanelUpdater,
    *,
    limit: int = 100,
) -> list[PendingApplyResult]:
    """Обрабатывает очередь отложенных обновлений обычных серверов.

    Единственный автоматический обработчик очереди (фоновый worker
    восстановления продлений); не зависит от проверки доступности серверов.
    Берёт записи, у которых истёк ``next_retry_at``, по всем серверам, кроме
    отключённых. Каждая запись применяется под блокировкой пользователя и
    фиксируется отдельной транзакцией: сбой одной записи не откатывает уже
    применённые и не останавливает остальные, а непредвиденная ошибка
    откладывает запись по тому же backoff, что и ошибка панели.
    """
    identifiers = await PendingServerUpdateRepository(session).list_due_ids(limit=limit)
    results: list[PendingApplyResult] = []
    for identifier in identifiers:
        try:
            update = await session.get(PendingServerUpdate, identifier)
            if update is None or update.status != "pending":
                continue
            results.append(
                await apply_pending_update(session, update, updater, commit=True)
            )
        except Exception as exc:  # noqa: BLE001 - одна запись не останавливает очередь
            await session.rollback()
            logger.exception("Ошибка применения отложенного обновления #%s", identifier)
            results.append(await _defer_after_error(session, identifier, exc))
    return results


async def _defer_after_error(
    session: AsyncSession, identifier: int, exc: Exception
) -> PendingApplyResult:
    error = f"{type(exc).__name__}: {exc}"
    try:
        update = await session.get(PendingServerUpdate, identifier)
        if update is None or update.status != "pending":
            return PendingApplyResult(update_id=identifier, server_id=0, ok=False, error=error)
        _schedule_retry(update, error)
        await session.commit()
        return PendingApplyResult(
            update_id=identifier, server_id=update.server_id, ok=False, error=error
        )
    except Exception:  # noqa: BLE001 - например, БД недоступна: повтор в следующем цикле
        await session.rollback()
        logger.exception("Не удалось отложить обновление #%s после ошибки", identifier)
        return PendingApplyResult(update_id=identifier, server_id=0, ok=False, error=error)


def _schedule_retry(update: PendingServerUpdate, error: str) -> None:
    update.attempts += 1
    update.last_error = error
    update.next_retry_at = datetime.now(UTC) + retry_delay(update.attempts)


async def close_for_server(session: AsyncSession, server_id: int, reason: str) -> int:
    """Закрывает отложенные обновления удаляемого сервера.

    Заявка, у которой не осталось других ожидающих серверов, больше не
    показывается как ожидающая синхронизации. Возвращает число закрытых записей.
    """
    updates = (await session.scalars(
        select(PendingServerUpdate)
        .where(PendingServerUpdate.server_id == server_id)
        .where(PendingServerUpdate.status == "pending")
    )).all()
    for update in updates:
        update.status = "failed"
        update.last_error = reason
        update.next_retry_at = None
    await session.flush()
    for update in updates:
        await _clear_payment_error_if_complete(session, update)
    await session.flush()
    return len(updates)


@serialized_access("update", "pending")
async def apply_pending_update(
    session: AsyncSession,
    update: PendingServerUpdate,
    updater: PanelUpdater,
    *,
    commit: bool = False,
) -> PendingApplyResult:
    """Применяет одно отложенное обновление под блокировкой пользователя.

    ``commit=True`` фиксирует результат до снятия блокировки: другой обработчик
    (в том числе в другом процессе на PostgreSQL) увидит итоговый статус и не
    применит запись повторно.
    """
    # Статус перечитывается под блокировкой: запись могли применить, пока
    # обработчик ждал её (объект загружен до ожидания).
    current = await session.get(PendingServerUpdate, update.id, populate_existing=True)
    if current is None:
        return PendingApplyResult(
            update_id=update.id, server_id=update.server_id, ok=False,
            error="pending update no longer exists",
        )
    result = await _apply_pending_update(session, current, updater)
    if commit:
        await session.commit()
    return result


async def _apply_pending_update(
    session: AsyncSession,
    update: PendingServerUpdate,
    updater: PanelUpdater,
) -> PendingApplyResult:
    if update.status != "pending":
        return PendingApplyResult(update_id=update.id, server_id=update.server_id,
                                  ok=update.status == "applied", error=update.last_error,
                                  already_done=True)
    server = await ServerRepository(session).get_with_inbounds(update.server_id)
    client = await session.get(VpnClient, update.vpn_client_id)
    if server is None or client is None:
        update.status = "failed"
        update.last_error = "server or vpn client no longer exists"
        await session.flush()
        await _clear_payment_error_if_complete(session, update)
        await session.flush()
        return PendingApplyResult(
            update_id=update.id,
            server_id=update.server_id,
            ok=False,
            error=update.last_error,
        )

    if not server.enabled:
        return PendingApplyResult(
            update_id=update.id, server_id=server.id, ok=False,
            error="server disabled",
        )
    if server.purpose != SERVER_PURPOSE_STANDARD:
        # Квоту whitelist-сервера применяет отдельная очередь учёта трафика.
        update.status = "failed"
        update.last_error = "whitelist server is managed by traffic accounting"
        await session.flush()
        await _clear_payment_error_if_complete(session, update)
        await session.flush()
        return PendingApplyResult(
            update_id=update.id, server_id=server.id, ok=False, error=update.last_error,
        )

    expiry = _as_aware(update.target_expires_at)
    if client.expires_at is not None:
        # A delayed older purchase must never shorten a newer paid subscription.
        expiry = max(expiry, _as_aware(client.expires_at))
    try:
        await _apply_to_server(session, client, server, expiry, updater)
    except PanelUpdateError as exc:
        _schedule_retry(update, str(exc))
        await session.flush()
        logger.info(
            "Pending server update #%s still failed for server #%s: %s",
            update.id,
            server.id,
            exc,
        )
        return PendingApplyResult(
            update_id=update.id,
            server_id=server.id,
            ok=False,
            error=str(exc),
        )

    update.status = "applied"
    update.attempts += 1
    update.last_error = None
    update.next_retry_at = None
    await _clear_payment_error_if_complete(session, update)
    await audit.record(
        session,
        action="pending_server_update.applied",
        entity_type="pending_server_update",
        entity_id=update.id,
        payload={
            "server_id": server.id,
            "vpn_client_id": client.id,
            "target_expires_at": expiry.isoformat(),
        },
    )
    await session.flush()
    return PendingApplyResult(update_id=update.id, server_id=server.id, ok=True)


async def _clear_payment_error_if_complete(
    session: AsyncSession, update: PendingServerUpdate
) -> None:
    if update.payment_request_id is None:
        return
    result = await session.execute(
        select(PendingServerUpdate.id)
        .where(PendingServerUpdate.payment_request_id == update.payment_request_id)
        .where(PendingServerUpdate.status == "pending")
        .where(PendingServerUpdate.id != update.id)
        .limit(1)
    )
    if result.first() is not None:
        return
    payment = await session.get(PaymentRequest, update.payment_request_id)
    if payment is not None:
        payment.last_error = None


async def _apply_to_server(
    session: AsyncSession,
    client: VpnClient,
    server: Server,
    expiry: datetime,
    updater: PanelUpdater,
) -> None:
    if any(inbound.enabled for inbound in server.inbounds):
        user = await session.get(User, client.user_id)
        public_id = (user.public_id if user else None) or client.email or str(client.user_id)
        result = await provisioning.apply_access_to_server(
            session, client, public_id, server, expiry, updater
        )
        if not result.ok:
            raise PanelUpdateError(result.error or "panel update failed")
        return

    if server.inbounds:
        raise PanelUpdateError("no_enabled_inbounds")

    mappings = await MappingRepository(session).list_for_client(client.id)
    server_mappings = [
        mapping
        for mapping in mappings
        if mapping.server_id == server.id and mapping.enabled
    ]
    if server_mappings:
        expiry_ms = _expiry_to_ms(expiry)
        for mapping in server_mappings:
            try:
                await updater.update_expiry(server, mapping, expiry_ms)
            except PanelUpdateError:
                raise
            except Exception as exc:  # noqa: BLE001
                raise PanelUpdateError(str(exc)) from exc
        return

    user = await session.get(User, client.user_id)
    public_id = (
        (user.public_id if user is not None else None)
        or client.email
        or str(client.user_id)
    )
    result = await provisioning.apply_access_to_server(
        session, client, public_id, server, expiry, updater
    )
    if not result.ok:
        raise PanelUpdateError(result.error or "panel update failed")

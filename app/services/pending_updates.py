from __future__ import annotations

import logging
from dataclasses import dataclass
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


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _expiry_to_ms(expiry: datetime) -> int:
    return int(expiry.timestamp() * 1000)


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


@serialized_access("update", "pending")
async def apply_pending_update(
    session: AsyncSession,
    update: PendingServerUpdate,
    updater: PanelUpdater,
) -> PendingApplyResult:
    if update.status != "pending":
        return PendingApplyResult(update_id=update.id, server_id=update.server_id,
                                  ok=update.status == "applied", error=update.last_error)
    server = await ServerRepository(session).get_with_inbounds(update.server_id)
    client = await session.get(VpnClient, update.vpn_client_id)
    if server is None or client is None:
        update.status = "failed"
        update.last_error = "server or vpn client no longer exists"
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
        update.attempts += 1
        update.last_error = str(exc)
        update.next_retry_at = datetime.now(UTC) + timedelta(
            seconds=min(3600, 60 * 2 ** min(update.attempts - 1, 6))
        )
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

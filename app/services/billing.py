from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import PaymentStatus
from app.db.models import PaymentRequest, User, VpnClient
from app.db.repositories import (
    MappingRepository,
    PaymentRepository,
    VpnClientRepository,
)
from app.services import audit, provisioning
from app.services.panel_updater import PanelUpdateError, PanelUpdater, ServerUpdateResult

logger = logging.getLogger(__name__)


class BillingError(Exception):
    """Ошибка бизнес-логики продления."""


@dataclass(slots=True)
class BillingResult:
    payment: PaymentRequest | None
    applied: bool
    already_applied: bool = False
    new_expires_at: datetime | None = None
    failed_servers: list[ServerUpdateResult] = field(default_factory=list)


@dataclass(slots=True)
class TrialResult:
    applied: bool
    already_used: bool = False
    no_client: bool = False
    new_expires_at: datetime | None = None
    failed_servers: list[ServerUpdateResult] = field(default_factory=list)


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


def _as_aware(value: datetime | None) -> datetime | None:
    """Гарантирует timezone-aware datetime (SQLite возвращает naive)."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def compute_new_expiry(
    current: datetime | None, now: datetime, period_days: int
) -> datetime:
    """Рассчитывает новую дату окончания доступа.

    Если текущий срок в будущем — продлеваем от него.
    Если срок истёк или отсутствует — продлеваем от текущего времени.
    """
    current = _as_aware(current)
    base = current if current is not None and current > now else now
    return base + timedelta(days=period_days)


def expiry_to_ms(expiry: datetime) -> int:
    """Конвертирует дату в миллисекунды Unix-времени (формат 3x-ui expiryTime)."""
    return int(expiry.timestamp() * 1000)


async def _apply_panels(
    session: AsyncSession,
    client: VpnClient,
    new_expiry: datetime,
    updater: PanelUpdater,
) -> list[ServerUpdateResult]:
    mapping_repo = MappingRepository(session)
    mappings = await mapping_repo.list_for_client(client.id)
    expiry_ms = expiry_to_ms(new_expiry)

    results: list[ServerUpdateResult] = []
    for mapping in mappings:
        server = mapping.server
        if server is None or not server.enabled or not mapping.enabled:
            continue
        try:
            await updater.update_expiry(server, mapping, expiry_ms)
            results.append(ServerUpdateResult(server_id=server.id, ok=True))
        except PanelUpdateError as exc:
            results.append(
                ServerUpdateResult(server_id=server.id, ok=False, error=str(exc))
            )
    return results


async def _extend_and_finalize(
    session: AsyncSession,
    payment: PaymentRequest,
    actor_user_id: int | None,
    updater: PanelUpdater,
    now: datetime,
) -> BillingResult:
    """Расчёт нового срока, обновление панелей и финализация статуса заявки."""
    client_repo = VpnClientRepository(session)
    client = await client_repo.get_for_user(payment.user_id)
    targets = await provisioning.has_targets(session)
    logger.info(
        "Финализация заявки id=%s user_id=%s period=%s: client=%s targets=%s",
        payment.id,
        payment.user_id,
        payment.period_days,
        "есть" if client else "нет",
        targets,
    )

    if client is None and not targets:
        payment.status = PaymentStatus.FAILED
        payment.last_error = "У пользователя нет связанного VPN-клиента"
        await audit.record(
            session,
            action="billing.failed_no_client",
            actor_user_id=actor_user_id,
            entity_type="payment_request",
            entity_id=payment.id,
        )
        await session.commit()
        return BillingResult(payment=payment, applied=False)

    user = await session.get(User, payment.user_id)
    if client is None:
        assert user is not None
        client = await provisioning.ensure_vpn_client(session, user)

    new_expiry = compute_new_expiry(client.expires_at, now, payment.period_days)
    if targets:
        public_id = (user.public_id if user else None) or client.email or str(
            payment.user_id
        )
        results = await provisioning.apply_access(
            session, client, public_id, new_expiry, updater
        )
    else:
        results = await _apply_panels(session, client, new_expiry, updater)
    failed = [r for r in results if not r.ok]
    logger.info(
        "Заявка id=%s: новый срок=%s, серверов_ок=%s, ошибок=%s",
        payment.id,
        new_expiry.isoformat(),
        sum(1 for r in results if r.ok),
        len(failed),
    )

    if failed:
        payment.status = PaymentStatus.FAILED
        payment.last_error = "; ".join(
            f"server {r.server_id}: {r.error}" for r in failed
        )
        await audit.record(
            session,
            action="billing.failed",
            actor_user_id=actor_user_id,
            entity_type="payment_request",
            entity_id=payment.id,
            payload={"failed_servers": [r.server_id for r in failed]},
        )
        await session.commit()
        return BillingResult(
            payment=payment, applied=False, failed_servers=failed
        )

    client.expires_at = new_expiry
    client.is_active = True
    payment.status = PaymentStatus.APPLIED
    payment.applied_at = now
    payment.last_error = None
    await audit.record(
        session,
        action="billing.applied",
        actor_user_id=actor_user_id,
        entity_type="payment_request",
        entity_id=payment.id,
        payload={"new_expires_at": new_expiry.isoformat()},
    )
    await session.commit()
    return BillingResult(
        payment=payment, applied=True, new_expires_at=new_expiry
    )


async def confirm_payment(
    session: AsyncSession,
    payment_id: int,
    actor_user_id: int | None,
    updater: PanelUpdater,
    now: datetime | None = None,
) -> BillingResult:
    """Идемпотентное подтверждение оплаты администратором.

    Повторный вызов для уже применённой заявки не продлевает доступ второй раз.
    """
    now = now or _utcnow()
    repo = PaymentRepository(session)
    payment = await repo.get_by_id(payment_id)
    if payment is None:
        raise BillingError("Заявка не найдена")
    logger.info(
        "confirm_payment: id=%s статус=%s actor=%s",
        payment.id,
        payment.status.value,
        actor_user_id,
    )

    if payment.status == PaymentStatus.APPLIED:
        return BillingResult(payment=payment, applied=False, already_applied=True)

    if payment.status != PaymentStatus.WAITING_ADMIN:
        raise BillingError(
            f"Заявка в статусе {payment.status.value}, подтверждение невозможно"
        )

    payment.status = PaymentStatus.CONFIRMED
    payment.confirmed_at = now
    await session.flush()

    return await _extend_and_finalize(session, payment, actor_user_id, updater, now)


async def retry_payment(
    session: AsyncSession,
    payment_id: int,
    actor_user_id: int | None,
    updater: PanelUpdater,
    now: datetime | None = None,
) -> BillingResult:
    """Повторное применение заявки, ранее завершившейся ошибкой (failed)."""
    now = now or _utcnow()
    repo = PaymentRepository(session)
    payment = await repo.get_by_id(payment_id)
    if payment is None:
        raise BillingError("Заявка не найдена")

    if payment.status == PaymentStatus.APPLIED:
        return BillingResult(payment=payment, applied=False, already_applied=True)

    if payment.status != PaymentStatus.FAILED:
        raise BillingError(
            f"Повторить можно только заявку в статусе failed, текущий: {payment.status.value}"
        )

    return await _extend_and_finalize(session, payment, actor_user_id, updater, now)


async def manual_extend(
    session: AsyncSession,
    vpn_client_id: int,
    period_days: int,
    actor_user_id: int | None,
    updater: PanelUpdater,
    now: datetime | None = None,
) -> BillingResult:
    """Ручное продление клиента администратором без привязки к заявке."""
    now = now or _utcnow()
    client = await VpnClientRepository(session).get_for_user_client(vpn_client_id)
    if client is None:
        raise BillingError("VPN-клиент не найден")

    new_expiry = compute_new_expiry(client.expires_at, now, period_days)
    results = await _apply_panels(session, client, new_expiry, updater)
    failed = [r for r in results if not r.ok]
    if failed:
        await session.commit()
        return BillingResult(payment=None, applied=False, failed_servers=failed)

    client.expires_at = new_expiry
    client.is_active = True
    await audit.record(
        session,
        action="billing.manual_extend",
        actor_user_id=actor_user_id,
        entity_type="vpn_client",
        entity_id=client.id,
        payload={"new_expires_at": new_expiry.isoformat()},
    )
    await session.commit()
    return BillingResult(payment=None, applied=True, new_expires_at=new_expiry)


async def sync_client(
    session: AsyncSession,
    vpn_client_id: int,
    actor_user_id: int | None,
    updater: PanelUpdater,
) -> list[ServerUpdateResult]:
    """Повторно выставляет текущий срок доступа клиента во всех панелях."""
    client = await VpnClientRepository(session).get_for_user_client(vpn_client_id)
    if client is None:
        raise BillingError("VPN-клиент не найден")
    if client.expires_at is None:
        raise BillingError("У клиента не задан срок доступа")

    expiry = _as_aware(client.expires_at)
    assert expiry is not None
    results = await _apply_panels(session, client, expiry, updater)
    await audit.record(
        session,
        action="billing.sync",
        actor_user_id=actor_user_id,
        entity_type="vpn_client",
        entity_id=client.id,
    )
    await session.commit()
    return results


async def grant_trial(
    session: AsyncSession,
    user_id: int,
    updater: PanelUpdater,
    period_days: int = 2,
    now: datetime | None = None,
) -> TrialResult:
    """Выдаёт бесплатный пробный период один раз на аккаунт.

    Пробный период резервируется в той же транзакции, что и продление. При ошибке
    обновления панелей транзакция откатывается, и пользователь может попробовать снова.
    """
    now = now or _utcnow()
    user = await session.get(User, user_id)
    if user is None:
        raise BillingError("Пользователь не найден")
    logger.info(
        "grant_trial: user_id=%s public_id=%s trial_used=%s period=%s",
        user.id,
        user.public_id,
        user.trial_used,
        period_days,
    )

    if user.trial_used:
        return TrialResult(applied=False, already_used=True)

    client = await VpnClientRepository(session).get_for_user(user_id)
    targets = await provisioning.has_targets(session)
    if client is None and not targets:
        return TrialResult(applied=False, no_client=True)
    if client is None:
        client = await provisioning.ensure_vpn_client(session, user)

    new_expiry = compute_new_expiry(client.expires_at, now, period_days)
    if targets:
        public_id = user.public_id or client.email or str(user_id)
        results = await provisioning.apply_access(
            session, client, public_id, new_expiry, updater
        )
    else:
        results = await _apply_panels(session, client, new_expiry, updater)
    failed = [r for r in results if not r.ok]
    logger.info(
        "grant_trial: user_id=%s новый срок=%s ок=%s ошибок=%s",
        user_id,
        new_expiry.isoformat(),
        sum(1 for r in results if r.ok),
        len(failed),
    )

    if failed:
        # Ничего не сохраняем: пробный период остаётся доступным для повторной попытки.
        return TrialResult(applied=False, failed_servers=failed)

    # trial_used и новый срок фиксируются одной транзакцией только при успехе.
    user.trial_used = True
    client.expires_at = new_expiry
    client.is_active = True
    await audit.record(
        session,
        action="billing.trial_granted",
        actor_user_id=user_id,
        entity_type="vpn_client",
        entity_id=client.id,
        payload={"new_expires_at": new_expiry.isoformat(), "period_days": period_days},
    )
    await session.commit()
    return TrialResult(applied=True, new_expires_at=new_expiry)


async def reject_payment(
    session: AsyncSession,
    payment_id: int,
    actor_user_id: int | None,
    comment: str | None = None,
    now: datetime | None = None,
) -> PaymentRequest:
    """Отклонение заявки администратором."""
    now = now or _utcnow()
    repo = PaymentRepository(session)
    payment = await repo.get_by_id(payment_id)
    if payment is None:
        raise BillingError("Заявка не найдена")

    if payment.status in (PaymentStatus.APPLIED, PaymentStatus.REJECTED):
        return payment

    payment.status = PaymentStatus.REJECTED
    payment.admin_comment = comment
    await audit.record(
        session,
        action="billing.rejected",
        actor_user_id=actor_user_id,
        entity_type="payment_request",
        entity_id=payment.id,
    )
    await session.commit()
    return payment

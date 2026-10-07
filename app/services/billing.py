from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import PaymentStatus
from app.db.models import (
    PAYMENT_KIND_SUBSCRIPTION,
    PAYMENT_KIND_TRAFFIC,
    SERVER_PURPOSE_STANDARD,
    PaymentRequest,
    SubscriptionPurchase,
    TrialGrant,
    User,
    VpnClient,
)
from app.db.repositories import (
    MappingRepository,
    PaymentRepository,
    ServerRepository,
    VpnClientRepository,
)
from app.services import audit, pending_updates, provisioning, whitelist
from app.services.operation_lock import serialized_access
from app.services.panel_updater import PanelUpdateError, PanelUpdater, ServerUpdateResult

logger = logging.getLogger(__name__)


class BillingError(Exception):
    """Ошибка бизнес-логики продления."""


@dataclass(slots=True)
class BillingResult:
    payment: PaymentRequest | None
    applied: bool
    already_applied: bool = False
    first_purchase: bool = False
    new_expires_at: datetime | None = None
    failed_servers: list[ServerUpdateResult] = field(default_factory=list)
    # «Обход белых списков»: оплата сохранена, а сверка расхода или применение
    # на сервере ожидается.
    whitelist_pending: bool = False
    # Для покупки трафика — начисленный объём (байты).
    traffic_bytes: int | None = None


@dataclass(slots=True)
class TrialResult:
    applied: bool
    already_used: bool = False
    no_client: bool = False
    # Подписка уже оформлялась: trial допустим только до первой подписки.
    subscription_purchased: bool = False
    new_expires_at: datetime | None = None
    failed_servers: list[ServerUpdateResult] = field(default_factory=list)
    whitelist_pending: bool = False


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


def resolve_target_expiry(
    payment: PaymentRequest,
    client: VpnClient,
    now: datetime,
) -> datetime:
    """Возвращает сохранённый target или вычисляет новый срок для первой попытки."""
    saved = _as_aware(payment.target_expires_at)
    if saved is not None:
        return saved
    return compute_new_expiry(client.expires_at, now, payment.period_days)


async def _count_eligible_mappings(session: AsyncSession, client_id: int) -> int:
    mapping_repo = MappingRepository(session)
    mappings = await mapping_repo.list_for_client(client_id)
    return sum(
        1
        for mapping in mappings
        if mapping.enabled
        and mapping.server is not None
        and mapping.server.enabled
    )


def _evaluate_panel_results(
    results: list[ServerUpdateResult],
    *,
    targets_mode: bool,
    eligible_mappings: int,
) -> tuple[list[ServerUpdateResult], str | None]:
    failed = [r for r in results if not r.ok]
    if failed:
        return failed, None
    if results:
        return [], None
    if targets_mode:
        return [], "Нет доступных серверов или inbound'ов для обновления панели"
    if eligible_mappings == 0:
        return [], "Нет активных привязок к серверам для обновления панели"
    return [], "Панели не обновлены: нет результатов"


async def _apply_panels(
    session: AsyncSession,
    client: VpnClient,
    new_expiry: datetime,
    updater: PanelUpdater,
) -> list[ServerUpdateResult]:
    if await provisioning.has_targets(session):
        user = await session.get(User, client.user_id)
        public_id = (user.public_id if user else None) or client.email or str(client.user_id)
        return await provisioning.apply_access(session, client, public_id, new_expiry, updater)

    mapping_repo = MappingRepository(session)
    mappings = await mapping_repo.list_for_client(client.id)
    expiry_ms = expiry_to_ms(new_expiry)

    results: list[ServerUpdateResult] = []
    for mapping in mappings:
        server = mapping.server
        if server is None or not server.enabled or not mapping.enabled:
            continue
        if server.purpose != SERVER_PURPOSE_STANDARD:
            # Квота whitelist-сервера ведётся отдельным учётом трафика.
            continue
        configured = await ServerRepository(session).get_with_inbounds(server.id)
        if configured is not None and configured.inbounds:
            results.append(ServerUpdateResult(
                server_id=server.id, ok=False, error="no_enabled_inbounds",
            ))
            continue
        try:
            await updater.update_expiry(server, mapping, expiry_ms)
            results.append(ServerUpdateResult(server_id=server.id, ok=True))
        except PanelUpdateError as exc:
            results.append(
                ServerUpdateResult(server_id=server.id, ok=False, error=str(exc))
            )
    return results


async def _persist_target_before_panels(
    session: AsyncSession,
    payment: PaymentRequest,
    target_expiry: datetime,
    now: datetime,
) -> None:
    """Фиксирует целевой срок и статус подтверждения до внешних вызовов к панелям."""
    payment.target_expires_at = target_expiry
    if payment.status == PaymentStatus.WAITING_ADMIN:
        payment.status = PaymentStatus.CONFIRMED
    # Принятие оплаты фиксируется и при повторе заявки, упавшей до принятия
    # (``failed`` без клиента): теперь администратор её принял.
    payment.confirmed_at = payment.confirmed_at or now
    await session.commit()


async def _extend_and_finalize(
    session: AsyncSession,
    payment: PaymentRequest,
    actor_user_id: int | None,
    updater: PanelUpdater,
    now: datetime,
) -> BillingResult:
    """Расчёт нового срока, обновление панелей и финализация статуса заявки."""
    pay_repo = PaymentRepository(session)
    first_purchase = await pay_repo.count_applied_for_user(payment.user_id) == 0
    client_repo = VpnClientRepository(session)
    client = await client_repo.get_for_user(payment.user_id)
    targets = await provisioning.has_targets(session)
    if client is None and not targets:
        targets = await provisioning.ensure_inbounds_imported(session)
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

    if payment.target_expires_at is None:
        reserved = await session.scalar(
            select(func.max(PaymentRequest.target_expires_at)).where(
                PaymentRequest.user_id == payment.user_id,
                PaymentRequest.status == PaymentStatus.CONFIRMED,
                PaymentRequest.kind == PAYMENT_KIND_SUBSCRIPTION,
            )
        )
        base = max(
            [value for value in (_as_aware(client.expires_at), _as_aware(reserved), now)
             if value is not None]
        )
        new_expiry = compute_new_expiry(base, now, payment.period_days)
    else:
        new_expiry = max(resolve_target_expiry(payment, client, now),
                         _as_aware(client.expires_at) or now)
    eligible_mappings = await _count_eligible_mappings(session, client.id)

    # Бесплатный пакет услуги фиксируется в той же транзакции, что и target:
    # повтор/рестарт после commit не выдаст его второй раз (ключ payment:<id>).
    # Выдача — упорядоченное событие учёта: если расход до оплаты не прочитан,
    # прежние остатки не заменяются до его сверки (оплата при этом сохранена).
    await whitelist.grant_for_subscription_payment(session, payment, updater, actor_user_id, now)
    await _persist_target_before_panels(session, payment, new_expiry, now)
    await session.refresh(payment)
    await session.refresh(client)
    new_expiry = _as_aware(payment.target_expires_at) or new_expiry

    if targets:
        public_id = (user.public_id if user else None) or client.email or str(
            payment.user_id
        )
        results = await provisioning.apply_access(
            session, client, public_id, new_expiry, updater
        )
    else:
        results = await _apply_panels(session, client, new_expiry, updater)

    failed, empty_error = _evaluate_panel_results(
        results,
        targets_mode=targets,
        eligible_mappings=eligible_mappings,
    )
    logger.info(
        "Заявка id=%s: целевой срок=%s, серверов_ок=%s, ошибок=%s",
        payment.id,
        new_expiry.isoformat(),
        sum(1 for r in results if r.ok),
        len(failed) + (1 if empty_error else 0),
    )

    ok_results = [r for r in results if r.ok]
    if empty_error:
        payment.status = PaymentStatus.FAILED
        payment.last_error = empty_error
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

    if failed:
        await pending_updates.enqueue_failed_servers(
            session,
            vpn_client_id=client.id,
            payment_request_id=payment.id,
            target_expires_at=new_expiry,
            failed_servers=failed,
        )
        payment.last_error = (
            "Отложено применение на серверы: "
            + "; ".join(f"server {r.server_id}: {r.error}" for r in failed)
        )
        await audit.record(
            session,
            action="billing.deferred_servers",
            actor_user_id=actor_user_id,
            entity_type="payment_request",
            entity_id=payment.id,
            payload={"failed_servers": [r.server_id for r in failed]},
        )
    if not ok_results and failed:
        logger.info(
            "Заявка id=%s не обновила ни один сервер сразу; все серверы отложены",
            payment.id,
        )

    client.expires_at = new_expiry
    client.is_active = True
    client.expiry_notify_stage = 0
    payment.status = PaymentStatus.APPLIED
    payment.applied_at = now
    # Факт оплаты подписки переживает сброс бота и закрывает trial Telegram ID.
    await _record_subscription_purchase(session, user, payment, now)
    if not failed:
        payment.last_error = None
    await audit.record(
        session,
        action="billing.applied",
        actor_user_id=actor_user_id,
        entity_type="payment_request",
        entity_id=payment.id,
        payload={
            "new_expires_at": new_expiry.isoformat(),
            "deferred_servers": [r.server_id for r in failed],
        },
    )
    await session.commit()
    wl = await whitelist.after_access_change(session, payment.user_id, updater)
    return BillingResult(
        payment=payment,
        applied=True,
        first_purchase=first_purchase,
        new_expires_at=new_expiry,
        failed_servers=failed,
        whitelist_pending=wl.pending or wl.unsettled,
    )


@serialized_access("payment_id", "payment")
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
    # FOR UPDATE: сериализует параллельные подтверждения одной заявки до того,
    # как статус будет переведён из waiting_admin (защита от двойного начисления).
    payment = await repo.get_by_id_for_update(payment_id)
    if payment is None:
        raise BillingError("Заявка не найдена")
    logger.info(
        "confirm_payment: id=%s статус=%s actor=%s",
        payment.id,
        payment.status.value,
        actor_user_id,
    )

    if payment.kind == PAYMENT_KIND_TRAFFIC:
        # Покупка трафика не проходит через начисление дней и выдачу пакета.
        return await _confirm_traffic(session, payment, actor_user_id, updater, now)

    if payment.status == PaymentStatus.APPLIED:
        return BillingResult(payment=payment, applied=False, already_applied=True)

    if payment.status != PaymentStatus.WAITING_ADMIN:
        raise BillingError(
            f"Заявка в статусе {payment.status.value}, подтверждение невозможно"
        )

    return await _extend_and_finalize(session, payment, actor_user_id, updater, now)


async def _confirm_traffic(
    session: AsyncSession,
    payment: PaymentRequest,
    actor_user_id: int | None,
    updater: PanelUpdater,
    now: datetime,
) -> BillingResult:
    try:
        result = await whitelist.confirm_traffic_payment(
            session, payment, actor_user_id, updater, now
        )
    except whitelist.WhitelistError as exc:
        raise BillingError(str(exc)) from exc
    if result.already_applied:
        # Повтор подтверждения ничего не начисляет, но догоняет панель.
        await whitelist.after_access_change(session, payment.user_id, updater)
        # Ожидание могло сняться в отдельной сессии применения.
        await session.refresh(payment, ["apply_pending_version"])
        return BillingResult(
            payment=payment, applied=False, already_applied=True,
            traffic_bytes=result.size_bytes,
        )
    return BillingResult(
        payment=payment,
        applied=True,
        traffic_bytes=result.size_bytes,
        whitelist_pending=bool(
            result.sync and (result.sync.pending or result.sync.unsettled)
        ),
    )


@serialized_access("payment_id", "payment")
async def retry_payment(
    session: AsyncSession,
    payment_id: int,
    actor_user_id: int | None,
    updater: PanelUpdater,
    now: datetime | None = None,
) -> BillingResult:
    """Повторяет сбойную или прерванную после фиксации target заявку."""
    now = now or _utcnow()
    repo = PaymentRepository(session)
    payment = await repo.get_by_id_for_update(payment_id)
    if payment is None:
        raise BillingError("Заявка не найдена")

    if payment.kind == PAYMENT_KIND_TRAFFIC:
        return await _confirm_traffic(session, payment, actor_user_id, updater, now)

    if payment.status == PaymentStatus.APPLIED:
        return BillingResult(payment=payment, applied=False, already_applied=True)

    resumable = (
        payment.status == PaymentStatus.CONFIRMED
        and payment.target_expires_at is not None
    )
    if payment.status != PaymentStatus.FAILED and not resumable:
        raise BillingError(
            "Повторить можно заявку с ошибкой или прерванное подтверждение, "
            f"текущий статус: {payment.status.value}"
        )

    return await _extend_and_finalize(session, payment, actor_user_id, updater, now)


@serialized_access("vpn_client_id", "client")
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
    eligible = await _count_eligible_mappings(session, client.id)
    results = await _apply_panels(session, client, new_expiry, updater)
    failed, empty_error = _evaluate_panel_results(
        results,
        targets_mode=False,
        eligible_mappings=eligible,
    )
    if empty_error or failed:
        await session.commit()
        return BillingResult(
            payment=None,
            applied=False,
            failed_servers=failed,
        )

    client.expires_at = new_expiry
    client.is_active = True
    client.expiry_notify_stage = 0
    await audit.record(
        session,
        action="billing.manual_extend",
        actor_user_id=actor_user_id,
        entity_type="vpn_client",
        entity_id=client.id,
        payload={"new_expires_at": new_expiry.isoformat()},
    )
    await session.commit()
    # Ручное изменение срока переносится на конфиг, но пакет не выдаёт.
    wl = await whitelist.after_access_change(session, client.user_id, updater)
    return BillingResult(
        payment=None, applied=True, new_expires_at=new_expiry,
        whitelist_pending=wl.pending or wl.unsettled,
    )


@serialized_access("vpn_client_id", "client")
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
    await whitelist.after_access_change(session, client.user_id, updater)
    return results


async def trial_already_used(session: AsyncSession, user: User) -> bool:
    """Пробный период уже выдавался этому пользователю или его Telegram ID.

    ``users.trial_used`` пропадает при сбросе бота вместе с ``User``; запись
    ``trial_grants`` по Telegram ID сохраняется.
    """
    if user.trial_used:
        return True
    if user.telegram_id is None:
        return False
    grant = await session.scalar(
        select(TrialGrant.telegram_id).where(TrialGrant.telegram_id == user.telegram_id)
    )
    return grant is not None


async def _record_subscription_purchase(
    session: AsyncSession, user: User | None, payment: PaymentRequest, now: datetime
) -> None:
    """Сохраняет первую применённую оплату подписки по Telegram ID пользователя.

    Вызывается под блокировкой пользователя, общей с ``grant_trial`` и сбросом, в
    транзакции, которая переводит заявку в ``applied``. Пользователь без Telegram
    ID (только сайт) не сбрасывается ботом: для него достаточно самих заявок.
    """
    if user is None or user.telegram_id is None:
        return
    if await session.get(SubscriptionPurchase, user.telegram_id) is not None:
        return
    session.add(
        SubscriptionPurchase(
            telegram_id=user.telegram_id,
            user_id=user.id,
            payment_request_id=payment.id,
            paid_at=now,
        )
    )


async def subscription_already_purchased(session: AsyncSession, user: User) -> bool:
    """Подписку уже оформляли этот пользователь или его Telegram ID.

    Оформлена — есть принятая оплата вида ``subscription`` (``confirmed``/``applied``
    либо ``failed`` после принятия администратором: ``confirmed_at``/
    ``target_expires_at``), даже с истёкшим сроком, либо запись ``subscription_purchases``
    по Telegram ID: заявки пропадают при сбросе бота вместе с ``User``, запись
    остаётся.
    """
    if await PaymentRepository(session).has_paid_subscription(user.id):
        return True
    if user.telegram_id is None:
        return False
    found = await session.scalar(
        select(SubscriptionPurchase.telegram_id).where(
            SubscriptionPurchase.telegram_id == user.telegram_id
        )
    )
    return found is not None


async def trial_available(session: AsyncSession, user: User) -> bool:
    """Единое правило допуска trial: он не использован и подписку ещё не оформляли.

    Покупки трафика, ожидающие и отклонённые заявки, а также ``failed`` до принятия
    оплаты подпиской не считаются; ``failed`` после принятия (сбой применения) —
    считается (см. ``subscription_already_purchased``). Кнопка бота и
    веб-мост только скрывают действие по этому правилу; обязательное применение —
    в ``grant_trial`` под блокировкой пользователя.
    """
    if await trial_already_used(session, user):
        return False
    return not await subscription_already_purchased(session, user)


@serialized_access("user_id", "user")
async def grant_trial(
    session: AsyncSession,
    user_id: int,
    updater: PanelUpdater,
    period_days: int = 2,
    now: datetime | None = None,
) -> TrialResult:
    """Выдаёт бесплатный пробный период один раз на Telegram-аккаунт и до первой подписки.

    Использование фиксируется в ``trial_grants``, оплата подписки — в
    ``subscription_purchases``, обе по Telegram ID, поэтому сброс бота (новый
    ``User`` для того же Telegram ID) trial не возвращает. Отметка
    сохраняется в той же транзакции, что и продление; при ошибке обновления панелей
    она не записывается, и пользователь может попробовать снова. Проверка и
    отметка выполняются под блокировкой пользователя, общей со сбросом.
    """
    now = now or _utcnow()
    user = await session.scalar(
        select(User).where(User.id == user_id).with_for_update()
        .execution_options(populate_existing=True)
    )
    if user is None:
        raise BillingError("Пользователь не найден")
    logger.info(
        "grant_trial: user_id=%s public_id=%s trial_used=%s period=%s",
        user.id,
        user.public_id,
        user.trial_used,
        period_days,
    )

    if await trial_already_used(session, user):
        return TrialResult(applied=False, already_used=True)
    # Подтверждение оплаты берёт ту же блокировку пользователя, поэтому оплата,
    # которую уже принял администратор, видна здесь, а новая ждёт окончания trial.
    # Оплата, удалённая сбросом бота, учитывается по Telegram ID.
    if await subscription_already_purchased(session, user):
        return TrialResult(applied=False, subscription_purchased=True)

    client = await VpnClientRepository(session).get_for_user(user_id)
    targets = await provisioning.has_targets(session)
    if client is None and not targets:
        targets = await provisioning.ensure_inbounds_imported(session)
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
    eligible = await _count_eligible_mappings(session, client.id)
    failed, empty_error = _evaluate_panel_results(
        results,
        targets_mode=targets,
        eligible_mappings=eligible,
    )
    logger.info(
        "grant_trial: user_id=%s новый срок=%s ок=%s ошибок=%s",
        user_id,
        new_expiry.isoformat(),
        sum(1 for r in results if r.ok),
        len(failed) + (1 if empty_error else 0),
    )

    if empty_error or failed:
        return TrialResult(applied=False, failed_servers=failed)

    user.trial_used = True
    if user.telegram_id is not None:
        session.add(TrialGrant(telegram_id=user.telegram_id, user_id=user.id, granted_at=now))
    client.expires_at = new_expiry
    client.is_active = True
    client.expiry_notify_stage = 0
    await audit.record(
        session,
        action="billing.trial_granted",
        actor_user_id=user_id,
        entity_type="vpn_client",
        entity_id=client.id,
        payload={"new_expires_at": new_expiry.isoformat(), "period_days": period_days},
    )
    # Пакет пробного периода сохраняется вместе с отметкой trial_used.
    await whitelist.grant_for_trial(session, user_id, updater, now)
    await session.commit()
    wl = await whitelist.after_access_change(session, user_id, updater)
    return TrialResult(
        applied=True, new_expires_at=new_expiry,
        whitelist_pending=wl.pending or wl.unsettled,
    )


@serialized_access("payment_id", "payment")
async def reject_payment(
    session: AsyncSession,
    payment_id: int,
    actor_user_id: int | None,
    comment: str | None = None,
    now: datetime | None = None,
) -> PaymentRequest:
    """Отклонение заявки администратором.

    Сериализуется с подтверждением: отклонение не может перезаписать уже
    применённую (и начисленную) заявку.
    """
    now = now or _utcnow()
    repo = PaymentRepository(session)
    payment = await repo.get_by_id_for_update(payment_id)
    if payment is None:
        raise BillingError("Заявка не найдена")

    if payment.status in (
        PaymentStatus.APPLIED, PaymentStatus.REJECTED, PaymentStatus.CONFIRMED
    ):
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


async def recover_confirmed_payments(
    session: AsyncSession,
    updater: PanelUpdater,
    *,
    backoff: pending_updates.RetryBackoff | None = None,
    now: datetime | None = None,
) -> int:
    """Возобновляет подтверждения, прерванные после фиксации целевого срока.

    Заявка ``CONFIRMED`` с сохранённым ``target_expires_at`` повторяется через
    ``retry_payment`` — под блокировкой пользователя и идемпотентно: срок берётся
    из сохранённого target (более новый оплаченный срок не сокращается), пакет
    продления повторно не выдаётся. Недоступные панели уходят в очередь
    отложенных обновлений. Заявка, повтор которой упал непредвиденной ошибкой,
    откладывается по ``backoff`` и не вытесняет остальные. Возвращает число
    применённых заявок.
    """
    now = now or _utcnow()
    query = select(PaymentRequest.id).where(
        PaymentRequest.status == PaymentStatus.CONFIRMED,
        PaymentRequest.kind == PAYMENT_KIND_SUBSCRIPTION,
        PaymentRequest.target_expires_at.is_not(None),
        PaymentRequest.confirmed_at < now - timedelta(minutes=5),
    )
    blocked = backoff.blocked(now) if backoff is not None else []
    if blocked:
        query = query.where(PaymentRequest.id.not_in(blocked))
    identifiers = (await session.scalars(
        query.order_by(PaymentRequest.id).limit(10)
    )).all()
    recovered = 0
    for identifier in identifiers:
        try:
            result = await retry_payment(session, identifier, None, updater)
        except Exception:  # noqa: BLE001
            await session.rollback()
            if backoff is not None:
                delay = backoff.failed(identifier, now)
                logger.exception(
                    "Failed to recover confirmed payment #%s, next try in %s",
                    identifier, delay,
                )
            else:
                logger.exception("Failed to recover confirmed payment #%s", identifier)
            continue
        if backoff is not None:
            backoff.succeeded(identifier)
        recovered += int(result.applied)
    return recovered

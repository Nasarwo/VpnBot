from __future__ import annotations

import secrets
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import AttachmentType, PaymentStatus
from app.db.models import (
    PAYMENT_KIND_SUBSCRIPTION,
    PAYMENT_KIND_TRAFFIC,
    PaymentAttachment,
    PaymentRequest,
    TrafficPackage,
    User,
)
from app.db.repositories import PaymentRepository, VpnClientRepository
from app.services import audit, whitelist
from app.services.operation_lock import serialized_access

_PAYMENT_CODE_ATTEMPTS = 5


def _new_payment_code() -> str:
    return f"PAY-{secrets.token_hex(4).upper()}"


class PaymentRequestError(Exception):
    """Заявку нельзя создать по бизнес-правилам."""


class PendingRequestExists(PaymentRequestError):
    """У пользователя уже есть заявка с отправленной квитанцией."""

    def __init__(self, payment: PaymentRequest) -> None:
        super().__init__("Предыдущая заявка ещё на проверке")
        self.payment = payment


async def _open_request_for_update(
    session: AsyncSession, user_id: int
) -> tuple[PaymentRequest | None, bool]:
    """Последняя открытая заявка (с блокировкой строки) и наличие квитанции."""
    existing = await PaymentRepository(session).latest_open_for_user(user_id)
    if existing is None:
        return None, False
    existing = await PaymentRepository(session).get_by_id_for_update(existing.id)
    if existing is None or existing.status not in (
        PaymentStatus.CREATED, PaymentStatus.WAITING_ADMIN
    ):
        return None, False
    proof = await session.scalar(
        select(PaymentAttachment.id)
        .where(PaymentAttachment.payment_request_id == existing.id)
        .limit(1)
    )
    return existing, proof is not None


@serialized_access("user_id", "user")
async def create_request(
    session: AsyncSession,
    user_id: int,
    amount: float,
    period_days: int,
    currency: str = "RUB",
) -> PaymentRequest:
    """Создаёт заявку на продление и переводит её в ожидание проверки админом.

    Сериализуется с подтверждением оплат пользователя: открытая заявка без
    квитанции может быть заменена выбором пользователя, но подтверждённая — нет.
    """
    repo = PaymentRepository(session)
    await session.execute(select(User).where(User.id == user_id).with_for_update())

    existing, has_proof = await _open_request_for_update(session, user_id)
    if existing is not None:
        if has_proof:
            if existing.kind != PAYMENT_KIND_SUBSCRIPTION:
                # Квитанция уже относится к другому виду оплаты: заявку не трогаем.
                raise PendingRequestExists(existing)
            return existing
        changed = False
        if existing.kind != PAYMENT_KIND_SUBSCRIPTION:
            existing.kind = PAYMENT_KIND_SUBSCRIPTION
            existing.traffic_bytes = None
            existing.traffic_package_id = None
            existing.traffic_package_title = None
            changed = True
        if float(existing.amount) != float(amount):
            existing.amount = Decimal(str(amount))
            changed = True
        if existing.period_days != period_days:
            existing.period_days = period_days
            changed = True
        if changed:
            await session.commit()
        return existing

    payment: PaymentRequest | None = None
    for _ in range(_PAYMENT_CODE_ATTEMPTS):
        payment_code = _new_payment_code()
        try:
            payment = await repo.create(
                user_id=user_id,
                amount=amount,
                period_days=period_days,
                payment_code=payment_code,
                currency=currency,
                status=PaymentStatus.WAITING_ADMIN,
            )
            await session.commit()
            break
        except IntegrityError:
            await session.rollback()

    if payment is None:
        raise RuntimeError("Не удалось сгенерировать уникальный payment_code")

    await audit.record(
        session,
        action="payment.created",
        actor_user_id=user_id,
        entity_type="payment_request",
        entity_id=payment.id,
        payload={"payment_code": payment.payment_code, "amount": amount},
    )
    await session.commit()
    return payment


@serialized_access("user_id", "user")
async def create_traffic_request(
    session: AsyncSession,
    user_id: int,
    package_id: int,
    now: datetime | None = None,
) -> PaymentRequest:
    """Заявка на покупку пакета «Обход белых списков».

    Создаётся только при активной (не бессрочной) подписке. Цена и объём
    копируются из пакета в заявку и дальше от пакета не зависят.
    """
    now = now or datetime.now(tz=UTC)
    config = await whitelist.get_config(session)
    if not config.service_enabled:
        raise PaymentRequestError("Услуга пока не запущена")
    package = await session.get(TrafficPackage, package_id)
    if package is None or not package.enabled:
        raise PaymentRequestError("Пакет недоступен")
    client = await VpnClientRepository(session).get_for_user(user_id)
    access = whitelist.access_state(client, now)
    if access.lifetime:
        raise PaymentRequestError("У вас безлимитный доступ — покупка трафика не нужна")
    if not access.active:
        raise PaymentRequestError("Покупка трафика доступна при активной подписке")
    await session.execute(select(User).where(User.id == user_id).with_for_update())

    title = whitelist_package_title(package)
    existing, has_proof = await _open_request_for_update(session, user_id)
    if existing is not None:
        if has_proof:
            raise PendingRequestExists(existing)
        existing.kind = PAYMENT_KIND_TRAFFIC
        existing.amount = package.price
        existing.period_days = 0
        existing.traffic_bytes = package.traffic_bytes
        existing.traffic_package_id = package.id
        existing.traffic_package_title = title
        await audit.record(
            session,
            action="payment.traffic_request_updated",
            actor_user_id=user_id,
            entity_type="payment_request",
            entity_id=existing.id,
            payload={"traffic_bytes": package.traffic_bytes, "amount": str(package.price)},
        )
        await session.commit()
        return existing

    payment_code: str | None = None
    for _ in range(_PAYMENT_CODE_ATTEMPTS):
        candidate = _new_payment_code()
        taken = await session.scalar(
            select(PaymentRequest.id).where(PaymentRequest.payment_code == candidate)
        )
        if taken is None:
            payment_code = candidate
            break
    if payment_code is None:
        raise RuntimeError("Не удалось сгенерировать уникальный payment_code")
    payment = PaymentRequest(
        user_id=user_id,
        amount=package.price,
        currency="RUB",
        period_days=0,
        kind=PAYMENT_KIND_TRAFFIC,
        traffic_bytes=package.traffic_bytes,
        traffic_package_id=package.id,
        traffic_package_title=title,
        payment_code=payment_code,
        status=PaymentStatus.WAITING_ADMIN,
    )
    session.add(payment)
    await session.flush()
    await audit.record(
        session,
        action="payment.traffic_request_created",
        actor_user_id=user_id,
        entity_type="payment_request",
        entity_id=payment.id,
        payload={
            "payment_code": payment.payment_code,
            "traffic_bytes": package.traffic_bytes,
            "amount": str(package.price),
        },
    )
    await session.commit()
    return payment


def whitelist_package_title(package: TrafficPackage) -> str:
    return f"{whitelist.set_volume_gib_text(package.traffic_bytes)} ГБ"


@serialized_access("user_id", "user")
async def cancel_open_request(session: AsyncSession, user_id: int) -> str | None:
    """Удаляет открытую заявку без квитанции; возвращает её код.

    Удаление условное: заявку, которую администратор успел подтвердить или к
    которой приложена квитанция, отменить нельзя.
    """
    existing, has_proof = await _open_request_for_update(session, user_id)
    if existing is None or has_proof:
        await session.commit()
        return None
    code = existing.payment_code
    await session.execute(
        delete(PaymentRequest).where(
            PaymentRequest.id == existing.id,
            PaymentRequest.status.in_([PaymentStatus.CREATED, PaymentStatus.WAITING_ADMIN]),
        )
    )
    await session.commit()
    return code


async def attach_proof(
    session: AsyncSession,
    payment_id: int,
    file_type: AttachmentType,
    telegram_file_id: str | None = None,
    caption: str | None = None,
) -> PaymentAttachment:
    """Прикрепляет подтверждение оплаты (текст/фото/документ) к заявке."""
    repo = PaymentRepository(session)
    attachment = await repo.add_attachment(
        payment_request_id=payment_id,
        file_type=file_type,
        telegram_file_id=telegram_file_id,
        caption=caption,
    )
    await audit.record(
        session,
        action="payment.proof_attached",
        entity_type="payment_request",
        entity_id=payment_id,
        payload={"file_type": file_type.value},
    )
    await session.commit()
    return attachment

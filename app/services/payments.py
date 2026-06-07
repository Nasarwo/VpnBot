from __future__ import annotations

import secrets

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import AttachmentType, PaymentStatus
from app.db.models import PaymentAttachment, PaymentRequest
from app.db.repositories import PaymentRepository
from app.services import audit

_PAYMENT_CODE_ATTEMPTS = 5


def _new_payment_code() -> str:
    return f"PAY-{secrets.token_hex(4).upper()}"


async def create_request(
    session: AsyncSession,
    user_id: int,
    amount: float,
    period_days: int,
    currency: str = "RUB",
) -> PaymentRequest:
    """Создаёт заявку на продление и переводит её в ожидание проверки админом."""
    repo = PaymentRepository(session)

    existing = await repo.latest_open_for_user(user_id)
    if existing is not None:
        changed = False
        if float(existing.amount) != float(amount):
            existing.amount = amount
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

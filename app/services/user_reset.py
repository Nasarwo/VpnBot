from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    BindRequest,
    ClientServerMapping,
    IpObservation,
    PaymentAttachment,
    PaymentRequest,
    User,
    VpnClient,
)
from app.services import audit


@dataclass(slots=True)
class UserResetResult:
    telegram_id: int
    user_id: int
    public_id: str | None


async def reset_user_bot_state(session: AsyncSession, user: User) -> UserResetResult:
    """Удаляет пользователя и связанные данные только из БД бота.

    3x-ui панели не трогаются: пользователь сможет снова пройти onboarding и
    привязать существующую подписку через ссылку.
    """
    result = UserResetResult(
        telegram_id=user.telegram_id,
        user_id=user.id,
        public_id=user.public_id,
    )

    vpn_client_ids = select(VpnClient.id).where(VpnClient.user_id == user.id)
    payment_ids = select(PaymentRequest.id).where(PaymentRequest.user_id == user.id)

    await session.execute(
        delete(IpObservation).where(IpObservation.vpn_client_id.in_(vpn_client_ids))
    )
    await session.execute(
        delete(ClientServerMapping).where(
            ClientServerMapping.vpn_client_id.in_(vpn_client_ids)
        )
    )
    await session.execute(delete(VpnClient).where(VpnClient.user_id == user.id))
    await session.execute(
        delete(PaymentAttachment).where(
            PaymentAttachment.payment_request_id.in_(payment_ids)
        )
    )
    await session.execute(delete(PaymentRequest).where(PaymentRequest.user_id == user.id))
    await session.execute(delete(BindRequest).where(BindRequest.user_id == user.id))
    await session.execute(delete(User).where(User.id == user.id))
    await audit.record(
        session,
        action="user.reset_bot_state",
        actor_user_id=None,
        entity_type="user",
        entity_id=result.user_id,
        payload={
            "telegram_id": result.telegram_id,
            "public_id": result.public_id,
            "panel_untouched": True,
        },
    )
    await session.commit()
    return result

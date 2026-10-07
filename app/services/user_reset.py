from __future__ import annotations

import enum
from dataclasses import dataclass

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import BindRequestStatus, PaymentStatus
from app.db.models import (
    BindRequest,
    ClientServerMapping,
    IpObservation,
    PaymentAttachment,
    PaymentRequest,
    User,
    VpnClient,
    WebAccount,
    WebLinkRequest,
    WhitelistLedger,
)
from app.db.repositories import UserRepository
from app.services import audit, whitelist
from app.services.operation_lock import serialized_access


class ResetBlock(str, enum.Enum):
    """Почему самостоятельный сброс потерял бы оплату, начисление или заявку."""

    WEB_LINKED = "web_linked"
    WEB_LINK = "web_link"
    PAID_TRAFFIC = "paid_traffic"
    PENDING_CREDIT = "pending_credit"
    OPEN_PAYMENT = "open_payment"
    OPEN_BIND = "open_bind"


# Заявки, по которым ещё возможно подтверждение, повтор или возврат.
_OPEN_PAYMENT_STATUSES = (
    PaymentStatus.CREATED,
    PaymentStatus.WAITING_ADMIN,
    PaymentStatus.CONFIRMED,
    PaymentStatus.FAILED,
)


async def find_reset_blocker(session: AsyncSession, user: User) -> ResetBlock | None:
    """Финансовое обязательство или заявка, которые удалил бы сброс; None — нет.

    Купленный трафик учитывается и тогда, когда он ещё не в ``paid_bytes``:
    покупка при недоступной статистике ждёт сверки событием журнала
    (pending/uncertain). Неприменённое событие оплаты (покупка, пакет продления)
    тоже блокирует сброс; trial — нет, он не оплачен.
    """
    async def found(query) -> bool:
        return await session.scalar(query.limit(1)) is not None

    if await found(select(WebAccount.id).where(WebAccount.user_id == user.id)):
        return ResetBlock.WEB_LINKED
    if await found(
        select(WebLinkRequest.id).where(
            WebLinkRequest.target_user_id == user.id, WebLinkRequest.status == "pending"
        )
    ):
        return ResetBlock.WEB_LINK
    account = await whitelist.get_account(session, user.id)
    if account is not None and account.paid_bytes > 0:
        return ResetBlock.PAID_TRAFFIC
    if await found(
        select(WhitelistLedger.id).where(
            WhitelistLedger.user_id == user.id,
            WhitelistLedger.status.in_((whitelist.EVENT_PENDING, whitelist.EVENT_UNCERTAIN)),
            or_(
                WhitelistLedger.paid_delta != 0,
                WhitelistLedger.payment_request_id.is_not(None),
            ),
        )
    ):
        return ResetBlock.PENDING_CREDIT
    if await found(
        select(PaymentRequest.id).where(
            PaymentRequest.user_id == user.id,
            PaymentRequest.status.in_(_OPEN_PAYMENT_STATUSES),
        )
    ):
        return ResetBlock.OPEN_PAYMENT
    if await found(
        select(BindRequest.id).where(
            BindRequest.user_id == user.id,
            BindRequest.status == BindRequestStatus.WAITING_ADMIN,
        )
    ):
        return ResetBlock.OPEN_BIND
    return None


@dataclass(slots=True)
class SelfResetOutcome:
    blocker: ResetBlock | None
    telegram_id: int | None = None
    username: str | None = None
    first_name: str | None = None


@serialized_access("user_id", "user")
async def delete_for_self_reset(
    session: AsyncSession, user_id: int
) -> SelfResetOutcome | None:
    """Удаляет пользователя по его запросу, если это не теряет оплат и заявок.

    Проверка и удаление выполняются под блокировкой пользователя — той же, что у
    подтверждения оплаты и создания заявок, — поэтому начисление не может
    появиться между ними. Строка пользователя блокируется FOR UPDATE: одобрение
    привязки сайта (``web_bridge.decide_link``) и новые ссылки на пользователя
    ждут завершения сброса. None — пользователь уже удалён параллельным сбросом.
    """
    user = await session.scalar(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if user is None:
        await session.commit()
        return None
    blocker = await find_reset_blocker(session, user)
    if blocker is not None:
        await session.commit()  # снимает блокировку строки
        return SelfResetOutcome(blocker=blocker)
    outcome = SelfResetOutcome(
        blocker=None,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
    )
    await audit.record(
        session,
        action="user.self_reset",
        actor_user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        payload={"telegram_id": user.telegram_id, "public_id": user.public_id},
    )
    await UserRepository(session).delete_user(user)
    await session.commit()
    return outcome


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

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import BindRequestStatus
from app.db.models import BindRequest, User
from app.db.repositories import BindRequestRepository
from app.services import audit, provisioning
from app.services.panel_updater import PanelUpdateError, PanelUpdater
from app.services.provisioning import _public_id_taken
from app.services.subscription_link import parse_subscription_public_id

logger = logging.getLogger(__name__)


class BindRequestError(Exception):
    """Ошибка бизнес-логики заявки на привязку."""


@dataclass(slots=True)
class BindApproveResult:
    request: BindRequest
    applied: bool
    already_applied: bool = False
    error: str | None = None


async def create_request(
    session: AsyncSession,
    user: User,
    subscription_link: str,
) -> BindRequest:
    """Создаёт заявку на привязку существующей подписки."""
    public_id = parse_subscription_public_id(subscription_link)
    if public_id is None:
        raise BindRequestError(
            "Не удалось распознать ID в ссылке. Пришлите полную ссылку-подписку "
            "или только ваш ID из конца ссылки."
        )

    repo = BindRequestRepository(session)
    existing = await repo.latest_waiting_for_user(user.id)
    if existing is not None:
        existing.subscription_link = subscription_link.strip()
        existing.public_id = public_id
        await session.commit()
        return existing

    if await _public_id_taken(session, public_id, user.id):
        raise BindRequestError(
            f"ID {public_id} уже привязан к другому аккаунту Telegram. "
            "Если это ваш ID — обратитесь в поддержку."
        )

    req = await repo.create(
        user_id=user.id,
        subscription_link=subscription_link.strip(),
        public_id=public_id,
    )
    await audit.record(
        session,
        action="bind_request.created",
        actor_user_id=user.id,
        entity_type="bind_request",
        entity_id=req.id,
        payload={"public_id": public_id, "code": req.request_code},
    )
    await session.commit()
    return req


async def approve_request(
    session: AsyncSession,
    request_id: int,
    actor_user_id: int | None,
    updater: PanelUpdater,
    now: datetime | None = None,
) -> BindApproveResult:
    """Подтверждает заявку и привязывает клиента панели к пользователю."""
    now = now or datetime.now(tz=UTC)
    repo = BindRequestRepository(session)
    req = await repo.get_by_id_with_user(request_id)
    if req is None:
        raise BindRequestError("Заявка не найдена")
    if req.status == BindRequestStatus.APPROVED:
        return BindApproveResult(request=req, applied=False, already_applied=True)
    if req.status != BindRequestStatus.WAITING_ADMIN:
        raise BindRequestError(
            f"Заявка в статусе {req.status.value}, подтверждение невозможно"
        )

    user = req.user
    if user is None:
        raise BindRequestError("Пользователь заявки не найден")

    try:
        await provisioning.bind_user_by_public_id(
            session, user, req.public_id, updater
        )
    except PanelUpdateError as exc:
        req.status = BindRequestStatus.FAILED
        req.last_error = str(exc)
        req.processed_at = now
        await audit.record(
            session,
            action="bind_request.failed",
            actor_user_id=actor_user_id,
            entity_type="bind_request",
            entity_id=req.id,
            payload={"error": str(exc)},
        )
        await session.commit()
        return BindApproveResult(request=req, applied=False, error=str(exc))

    req.status = BindRequestStatus.APPROVED
    req.processed_at = now
    req.last_error = None
    user.onboarding_done = True
    client = await provisioning.ensure_vpn_client(session, user)
    client.expiry_notify_stage = 0

    await audit.record(
        session,
        action="bind_request.approved",
        actor_user_id=actor_user_id,
        entity_type="bind_request",
        entity_id=req.id,
        payload={"public_id": req.public_id},
    )
    await session.commit()
    logger.info(
        "bind_request approved: id=%s user=%s public_id=%s",
        req.id,
        user.id,
        req.public_id,
    )
    return BindApproveResult(request=req, applied=True)


async def reject_request(
    session: AsyncSession,
    request_id: int,
    actor_user_id: int | None,
    comment: str | None = None,
    now: datetime | None = None,
) -> BindRequest:
    """Отклоняет заявку на привязку."""
    now = now or datetime.now(tz=UTC)
    repo = BindRequestRepository(session)
    req = await repo.get_by_id_with_user(request_id)
    if req is None:
        raise BindRequestError("Заявка не найдена")
    if req.status in (BindRequestStatus.APPROVED, BindRequestStatus.REJECTED):
        return req

    req.status = BindRequestStatus.REJECTED
    req.admin_comment = comment
    req.processed_at = now
    user = req.user
    if user is not None:
        user.onboarding_done = False
    await audit.record(
        session,
        action="bind_request.rejected",
        actor_user_id=actor_user_id,
        entity_type="bind_request",
        entity_id=req.id,
    )
    await session.commit()
    return req


async def retry_request(
    session: AsyncSession,
    request_id: int,
    actor_user_id: int | None,
    updater: PanelUpdater,
    now: datetime | None = None,
) -> BindApproveResult:
    """Повторная попытка привязки после ошибки."""
    repo = BindRequestRepository(session)
    req = await repo.get_by_id(request_id)
    if req is None:
        raise BindRequestError("Заявка не найдена")
    if req.status != BindRequestStatus.FAILED:
        raise BindRequestError(
            f"Повторить можно только заявку с ошибкой, текущий: {req.status.value}"
        )
    req.status = BindRequestStatus.WAITING_ADMIN
    req.last_error = None
    await session.flush()
    return await approve_request(
        session, request_id, actor_user_id, updater, now=now
    )

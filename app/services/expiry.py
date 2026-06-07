from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import notify
from app.db.repositories import VpnClientRepository

logger = logging.getLogger(__name__)

_HOUR = timedelta(hours=1)
_DAY = timedelta(hours=24)


def _as_aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _target_stage(expires_at: datetime, now: datetime) -> int:
    """Стадия уведомления по остатку времени до окончания.

    0 — рано, 1 — остался день, 2 — остался час, 3 — срок истёк.
    """
    remaining = _as_aware(expires_at) - now
    if remaining <= timedelta(0):
        return 3
    if remaining <= _HOUR:
        return 2
    if remaining <= _DAY:
        return 1
    return 0


async def process_expiry_notifications(
    session: AsyncSession, bot: Bot, now: datetime | None = None
) -> int:
    """Шлёт уведомления «за день / за час / в момент окончания».

    Каждая стадия отправляется один раз; прогресс хранится в
    VpnClient.expiry_notify_stage и сбрасывается при продлении. Возвращает число
    отправленных сообщений.
    """
    now = now or datetime.now(tz=UTC)
    repo = VpnClientRepository(session)
    clients = await repo.list_for_expiry_notifications(now)

    sent = 0
    changed = False
    for client in clients:
        if client.expires_at is None:
            continue
        target = _target_stage(client.expires_at, now)
        if target <= client.expiry_notify_stage:
            continue
        user = client.user
        if user is None or user.telegram_id is None:
            client.expiry_notify_stage = target
            changed = True
            continue
        # Отправляем все непройденные стадии по порядку (обычно одну).
        for stage in range(client.expiry_notify_stage + 1, target + 1):
            ok = await notify.notify_user_expiry(
                bot, user.telegram_id, stage, client.expires_at
            )
            if ok:
                sent += 1
        client.expiry_notify_stage = target
        changed = True

    if changed:
        await session.commit()
    if sent:
        logger.info("Уведомления об окончании: отправлено %s", sent)
    return sent

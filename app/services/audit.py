from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import AuditRepository


async def record(
    session: AsyncSession,
    action: str,
    actor_user_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Записывает событие в audit_logs."""
    repo = AuditRepository(session)
    serialized = json.dumps(payload, ensure_ascii=False) if payload else None
    await repo.log(
        action=action,
        actor_user_id=actor_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=serialized,
    )

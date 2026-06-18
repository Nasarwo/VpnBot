from __future__ import annotations

from datetime import UTC, datetime

from app.config import Settings
from app.db.enums import UserRole
from app.db.models import VpnClient


def has_active_timed_client(client: VpnClient | None) -> bool:
    if client is None or client.expires_at is None:
        return False
    expires = client.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    return expires > datetime.now(tz=UTC)


def has_unlimited_bound_client(client: VpnClient | None) -> bool:
    return client is not None and client.expires_at is None and bool(client.mappings)


def has_client_access(client: VpnClient | None) -> bool:
    return has_active_timed_client(client) or has_unlimited_bound_client(client)


def resolve_effective_role(
    settings: Settings,
    telegram_id: int,
    client: VpnClient | None,
) -> UserRole:
    if settings.is_admin(telegram_id) or has_unlimited_bound_client(client):
        return UserRole.ADMIN
    return UserRole.USER

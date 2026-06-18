from __future__ import annotations

from datetime import timedelta

from app.config import Settings
from app.db.enums import Protocol, UserRole
from app.db.models import ClientServerMapping, VpnClient
from app.services import access
from tests.conftest import utcnow


def _mapping() -> ClientServerMapping:
    return ClientServerMapping(
        server_id=1,
        inbound_id=1,
        protocol=Protocol.VLESS,
        client_uuid="uuid-1",
        email="user@example",
        enabled=True,
    )


def test_access_rejects_missing_client():
    assert access.has_active_timed_client(None) is False
    assert access.has_unlimited_bound_client(None) is False
    assert access.has_client_access(None) is False


def test_unlimited_client_requires_server_mapping():
    client = VpnClient(user_id=1, expires_at=None)

    assert access.has_unlimited_bound_client(client) is False
    assert access.has_client_access(client) is False
    assert access.resolve_effective_role(
        Settings(admin_telegram_ids=[]), 100, client
    ) == UserRole.USER


def test_unlimited_bound_client_gets_access_and_admin_role():
    client = VpnClient(user_id=1, expires_at=None, mappings=[_mapping()])

    assert access.has_active_timed_client(client) is False
    assert access.has_unlimited_bound_client(client) is True
    assert access.has_client_access(client) is True
    assert access.resolve_effective_role(
        Settings(admin_telegram_ids=[]), 100, client
    ) == UserRole.ADMIN


def test_timed_client_gets_access_without_auto_admin_role():
    client = VpnClient(user_id=1, expires_at=utcnow() + timedelta(days=5))

    assert access.has_active_timed_client(client) is True
    assert access.has_unlimited_bound_client(client) is False
    assert access.has_client_access(client) is True
    assert access.resolve_effective_role(
        Settings(admin_telegram_ids=[]), 100, client
    ) == UserRole.USER


def test_expired_client_has_no_access_or_auto_admin_role():
    client = VpnClient(user_id=1, expires_at=utcnow() - timedelta(days=1))

    assert access.has_active_timed_client(client) is False
    assert access.has_unlimited_bound_client(client) is False
    assert access.has_client_access(client) is False
    assert access.resolve_effective_role(
        Settings(admin_telegram_ids=[]), 100, client
    ) == UserRole.USER


def test_configured_admin_keeps_admin_role_without_client_access():
    assert access.resolve_effective_role(
        Settings(admin_telegram_ids=[100]), 100, None
    ) == UserRole.ADMIN

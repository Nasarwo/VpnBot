from __future__ import annotations

from datetime import UTC

import pytest
from pytest_httpx import HTTPXMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import Protocol
from app.db.models import Server, ServerInbound, User
from app.db.repositories import (
    MappingRepository,
    ServerRepository,
    VpnClientRepository,
)
from app.services import provisioning
from app.services.panel_updater import MockPanelUpdater
from tests.conftest import days_from_now


async def _server_with_inbounds(
    session: AsyncSession, name: str = "de", count: int = 2
) -> Server:
    srv = Server(
        name=name,
        country="DE",
        panel_url="http://panel.local:2053",
        username="admin",
        password="secret",
        kind="direct",
        subscription_base="https://de:2096/sub/",
        enabled=True,
    )
    session.add(srv)
    await session.flush()
    protocols = [Protocol.VLESS, Protocol.TROJAN, Protocol.VMESS]
    for i in range(count):
        session.add(
            ServerInbound(
                server_id=srv.id,
                inbound_id=10 + i,
                protocol=protocols[i % len(protocols)],
                enabled=True,
            )
        )
    await session.commit()
    return srv


async def test_has_targets(session: AsyncSession):
    assert await provisioning.has_targets(session) is False
    await _server_with_inbounds(session)
    assert await provisioning.has_targets(session) is True


async def test_ensure_inbounds_imported_no_servers_no_network(session: AsyncSession):
    # Нет серверов — нет импорта и нет сетевых вызовов.
    assert await provisioning.ensure_inbounds_imported(session) is False


async def test_ensure_inbounds_imported_skips_servers_with_inbounds(
    session: AsyncSession, monkeypatch
):
    await _server_with_inbounds(session)

    called = False

    async def fail_import(sess, srv, timeout=15.0):
        nonlocal called
        called = True
        raise AssertionError("import не должен вызываться для сервера с inbound'ами")

    monkeypatch.setattr(provisioning, "import_inbounds", fail_import)
    assert await provisioning.ensure_inbounds_imported(session) is True
    assert called is False


async def test_ensure_inbounds_imported_imports_when_missing(
    session: AsyncSession, monkeypatch
):
    srv = Server(
        name="se", country="SE", panel_url="http://p:2053",
        username="a", password="b", enabled=True,
    )
    session.add(srv)
    await session.commit()

    async def fake_import(sess, server, timeout=15.0):
        sess.add(
            ServerInbound(
                server_id=server.id, inbound_id=1,
                protocol=Protocol.VLESS, enabled=True,
            )
        )
        await sess.flush()
        return [(1, "vless", "added")]

    monkeypatch.setattr(provisioning, "import_inbounds", fake_import)
    assert await provisioning.has_targets(session) is False
    assert await provisioning.ensure_inbounds_imported(session) is True
    assert await provisioning.has_targets(session) is True


async def test_ensure_vpn_client_creates_once(session: AsyncSession, user: User):
    user.public_id = "PUB123"
    await session.flush()
    c1 = await provisioning.ensure_vpn_client(session, user)
    assert c1.external_client_id
    c2 = await provisioning.ensure_vpn_client(session, user)
    assert c1.id == c2.id


async def test_apply_access_creates_clients_and_mappings(
    session: AsyncSession, user: User
):
    user.public_id = "PUB123"
    await session.flush()
    await _server_with_inbounds(session, count=2)
    client = await provisioning.ensure_vpn_client(session, user)

    updater = MockPanelUpdater()
    results = await provisioning.apply_access(
        session, client, "PUB123", days_from_now(30), updater
    )
    await session.commit()

    assert all(r.ok for r in results)
    # Один глобальный клиент на сервер, привязанный к обоим inbound'ам.
    assert len(updater.provisioned) == 1
    server_id, email, inbound_ids = updater.provisioned[0]
    assert email == "PUB123"
    assert set(inbound_ids) == {10, 11}

    mappings = await MappingRepository(session).list_for_client(client.id)
    assert len(mappings) == 1
    assert mappings[0].email == "PUB123"
    assert mappings[0].sub_id == "PUB123"


async def test_apply_access_idempotent(session: AsyncSession, user: User):
    user.public_id = "PUB123"
    await session.flush()
    await _server_with_inbounds(session, count=2)
    client = await provisioning.ensure_vpn_client(session, user)

    updater = MockPanelUpdater()
    await provisioning.apply_access(
        session, client, "PUB123", days_from_now(30), updater
    )
    await session.commit()
    await provisioning.apply_access(
        session, client, "PUB123", days_from_now(60), updater
    )
    await session.commit()

    mappings = await MappingRepository(session).list_for_client(client.id)
    assert len(mappings) == 1


async def test_apply_access_partial_failure(session: AsyncSession, user: User):
    user.public_id = "PUB123"
    await session.flush()
    srv = await _server_with_inbounds(session, count=2)
    client = await provisioning.ensure_vpn_client(session, user)

    updater = MockPanelUpdater(fail_server_ids={srv.id})
    results = await provisioning.apply_access(
        session, client, "PUB123", days_from_now(30), updater
    )
    assert results
    assert all(not r.ok for r in results)
    mappings = await MappingRepository(session).list_for_client(client.id)
    assert len(mappings) == 0


async def test_apply_access_reuses_existing_identity(
    session: AsyncSession, user: User
):
    user.public_id = "PUB123"
    await session.flush()
    await _server_with_inbounds(session, count=2)
    client = await provisioning.ensure_vpn_client(session, user)
    srv = (await ServerRepository(session).list_enabled_with_inbounds())[0]
    # Заранее привязанный (импортированный) клиент с собственной идентичностью.
    await MappingRepository(session).create(
        vpn_client_id=client.id,
        server_id=srv.id,
        inbound_id=10,
        protocol=Protocol.VLESS,
        client_uuid="EXIST-UUID",
        email="legacy-name",
        sub_id="SUBX",
    )
    await session.commit()

    updater = MockPanelUpdater()
    await provisioning.apply_access(
        session, client, "PUB123", days_from_now(30), updater
    )

    # Провижининг идёт по существующему email/идентичности, а не по public_id.
    assert updater.provisioned
    server_id, email, _ = updater.provisioned[0]
    assert email == "legacy-name"
    assert client.external_client_id == "EXIST-UUID"


async def test_bind_existing_client(
    session: AsyncSession, user: User, server: Server, httpx_mock: HTTPXMock, monkeypatch
):
    base = server.panel_url
    httpx_mock.add_response(
        method="GET",
        url=f"{base}/csrf-token",
        json={"success": True, "obj": "t"},
        is_reusable=True,
    )
    httpx_mock.add_response(
        method="POST", url=f"{base}/login", json={"success": True},
        is_reusable=True,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{base}/panel/api/clients/get/__caps_probe__",
        json={"success": False},
        is_reusable=True,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{base}/panel/api/clients/get/olduser",
        json={
            "success": True,
            "obj": {
                "client": {
                    "email": "olduser",
                    "subId": "SUBX",
                    "uuid": "U-1",
                    "expiryTime": 1_893_456_000_000,
                    "enable": True,
                },
                "inboundIds": [3],
            },
        },
    )

    async def fake_presence(sess, public_id, timeout=15.0):
        info = provisioning.PanelClientInfo(
            email="olduser",
            sub_id="SUBX",
            secret="U-1",
            expiry_ms=1_893_456_000_000,
            enable=True,
            inbound_ids=[3],
        )
        return [provisioning.ServerClientPresence(server=server, info=info)]

    monkeypatch.setattr(
        provisioning, "find_client_presence_on_servers", fake_presence
    )

    result = await provisioning.bind_existing_client(
        session, server, "olduser", user, MockPanelUpdater()
    )
    await session.commit()

    assert result.public_id == "SUBX"
    assert user.public_id == "SUBX"
    client = await VpnClientRepository(session).get_for_user(user.id)
    assert client is not None
    assert client.external_client_id == "U-1"
    mappings = await MappingRepository(session).list_for_client(client.id)
    assert len(mappings) == 1
    assert mappings[0].email == "olduser"
    assert mappings[0].sub_id == "SUBX"
    assert result.synced is True


def _panel_info(
    *,
    email: str = "legacy",
    sub_id: str = "LEGACY1",
    secret: str = "uuid-legacy",
    expiry_ms: int = 1_900_000_000_000,
    inbound_ids: list[int] | None = None,
) -> provisioning.PanelClientInfo:
    return provisioning.PanelClientInfo(
        email=email,
        sub_id=sub_id,
        secret=secret,
        expiry_ms=expiry_ms,
        enable=True,
        inbound_ids=inbound_ids or [10],
    )


async def test_bind_user_by_public_id_creates_missing_on_other_servers(
    session: AsyncSession, user: User, monkeypatch
):
    ru = await _server_with_inbounds(session, name="ru", count=1)
    se = await _server_with_inbounds(session, name="se", count=1)
    de = await _server_with_inbounds(session, name="de", count=1)

    presences = [
        provisioning.ServerClientPresence(server=ru, info=_panel_info()),
        provisioning.ServerClientPresence(
            server=se,
            info=_panel_info(expiry_ms=1_910_000_000_000),
        ),
    ]

    async def fake_presence(sess, public_id, timeout=15.0):
        assert public_id == "LEGACY1"
        return presences

    monkeypatch.setattr(
        provisioning, "find_client_presence_on_servers", fake_presence
    )

    updater = MockPanelUpdater()
    result = await provisioning.bind_user_by_public_id(
        session, user, "LEGACY1", updater
    )
    await session.commit()

    assert result.synced is True
    assert user.public_id == "LEGACY1"
    client = await VpnClientRepository(session).get_for_user(user.id)
    assert client is not None
    assert client.expires_at is not None

    mappings = await MappingRepository(session).list_for_client(client.id)
    assert {m.server_id for m in mappings} == {ru.id, se.id, de.id}
    assert len(updater.provisioned) == 3
    provisioned_ids = {item[0] for item in updater.provisioned}
    assert provisioned_ids == {ru.id, se.id, de.id}


async def test_bind_user_by_public_id_uses_max_expiry_from_presences(
    session: AsyncSession, user: User, monkeypatch
):
    ru = await _server_with_inbounds(session, name="ru", count=1)
    se = await _server_with_inbounds(session, name="se", count=1)
    earlier_ms = 1_900_000_000_000
    later_ms = 1_920_000_000_000
    presences = [
        provisioning.ServerClientPresence(
            server=ru,
            info=_panel_info(expiry_ms=earlier_ms),
        ),
        provisioning.ServerClientPresence(
            server=se,
            info=_panel_info(expiry_ms=later_ms),
        ),
    ]

    async def fake_presence(sess, public_id, timeout=15.0):
        return presences

    monkeypatch.setattr(
        provisioning,
        "find_client_presence_on_servers",
        fake_presence,
    )

    updater = MockPanelUpdater()
    await provisioning.bind_user_by_public_id(session, user, "LEGACY1", updater)

    client = await VpnClientRepository(session).get_for_user(user.id)
    assert client is not None
    expected = provisioning._ms_to_datetime(later_ms)
    actual = client.expires_at
    if actual is not None and actual.tzinfo is None:
        actual = actual.replace(tzinfo=UTC)
    assert actual == expected
    assert updater.provisioned
    assert updater.provisioned[0][1] == "legacy"


async def test_bind_user_by_public_id_syncs_unlimited_expiry(
    session: AsyncSession, user: User, monkeypatch
):
    srv = await _server_with_inbounds(session, name="ru", count=1)
    presences = [
        provisioning.ServerClientPresence(
            server=srv,
            info=_panel_info(expiry_ms=0),
        ),
    ]
    async def fake_presence(sess, public_id, timeout=15.0):
        return presences

    monkeypatch.setattr(
        provisioning,
        "find_client_presence_on_servers",
        fake_presence,
    )

    updater = MockPanelUpdater()
    result = await provisioning.bind_user_by_public_id(
        session, user, "LEGACY1", updater
    )

    client = await VpnClientRepository(session).get_for_user(user.id)
    assert client is not None
    assert client.expires_at is None
    assert result.synced is True
    assert len(updater.provisioned) == 1


async def test_bind_user_by_public_id_fails_if_server_provision_fails(
    session: AsyncSession, user: User, monkeypatch
):
    ru = await _server_with_inbounds(session, name="ru", count=1)
    de = await _server_with_inbounds(session, name="de", count=1)
    presences = [
        provisioning.ServerClientPresence(server=ru, info=_panel_info()),
    ]

    async def fake_presence(sess, public_id, timeout=15.0):
        return presences

    monkeypatch.setattr(
        provisioning,
        "find_client_presence_on_servers",
        fake_presence,
    )

    updater = MockPanelUpdater(fail_server_ids={de.id})
    with pytest.raises(provisioning.PanelUpdateError) as exc:
        await provisioning.bind_user_by_public_id(
            session, user, "LEGACY1", updater
        )
    assert "server" in str(exc.value).lower()


async def test_renewal_after_bind_user_succeeds_on_all_servers(
    session: AsyncSession, user: User, monkeypatch
):
    ru = await _server_with_inbounds(session, name="ru", count=1)
    de = await _server_with_inbounds(session, name="de", count=1)
    presences = [
        provisioning.ServerClientPresence(server=ru, info=_panel_info()),
    ]

    async def fake_presence(sess, public_id, timeout=15.0):
        return presences

    monkeypatch.setattr(
        provisioning,
        "find_client_presence_on_servers",
        fake_presence,
    )

    updater = MockPanelUpdater()
    await provisioning.bind_user_by_public_id(session, user, "LEGACY1", updater)
    await session.commit()

    client = await VpnClientRepository(session).get_for_user(user.id)
    assert client is not None
    updater.provisioned.clear()

    results = await provisioning.apply_access(
        session, client, "LEGACY1", days_from_now(60), updater
    )
    assert len(results) == 2
    assert all(r.ok for r in results)
    assert len(updater.provisioned) == 2
    assert {item[0] for item in updater.provisioned} == {ru.id, de.id}


async def test_bind_user_by_public_id_when_email_differs_from_sub_id(
    session: AsyncSession, user: User, monkeypatch
):
    """Ссылка содержит subId, а в панели email другой — оба поля сохраняются."""
    srv = await _server_with_inbounds(session, name="ru", count=1)
    presences = [
        provisioning.ServerClientPresence(
            server=srv,
            info=_panel_info(
                email="panel-custom-email",
                sub_id="dsh",
                secret="uuid-dsh",
            ),
        ),
    ]

    async def fake_presence(sess, public_id, timeout=15.0):
        assert public_id == "dsh"
        return presences

    monkeypatch.setattr(
        provisioning,
        "find_client_presence_on_servers",
        fake_presence,
    )

    updater = MockPanelUpdater()
    result = await provisioning.bind_user_by_public_id(
        session, user, "dsh", updater
    )
    await session.commit()

    assert user.public_id == "dsh"
    assert result.email == "panel-custom-email"
    client = await VpnClientRepository(session).get_for_user(user.id)
    assert client is not None
    assert client.email == "panel-custom-email"

    mappings = await MappingRepository(session).list_for_client(client.id)
    assert mappings[0].email == "panel-custom-email"
    assert mappings[0].sub_id == "dsh"
    assert updater.provisioned[0][1] == "panel-custom-email"


async def test_find_client_presence_falls_back_to_sub_id_lookup(
    session: AsyncSession, server: Server, monkeypatch
):
    panel_info = _panel_info(email="real-email", sub_id="dsh")

    async def fake_by_email(srv, email, timeout=15.0):
        return None

    async def fake_by_sub_id(srv, sub_id, timeout=15.0):
        if sub_id == "dsh":
            return panel_info
        return None

    monkeypatch.setattr(provisioning, "find_panel_client", fake_by_email)
    monkeypatch.setattr(
        provisioning, "_find_panel_client_by_sub_id", fake_by_sub_id
    )

    found = await provisioning.find_client_presence_on_servers(
        session, "dsh"
    )
    assert len(found) == 1
    assert found[0].info.email == "real-email"
    assert found[0].info.sub_id == "dsh"

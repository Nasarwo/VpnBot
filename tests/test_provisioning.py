from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import Protocol
from app.db.models import Server, ServerInbound, User
from app.db.repositories import MappingRepository
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
    assert len(updater.ensured) == 2

    mappings = await MappingRepository(session).list_for_client(client.id)
    assert len(mappings) == 2
    emails = {m.email for m in mappings}
    assert emails == {"PUB123-10", "PUB123-11"}
    assert all(m.sub_id == "PUB123" for m in mappings)


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
    assert len(mappings) == 2


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

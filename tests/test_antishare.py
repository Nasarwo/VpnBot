from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import Server, User, VpnClient
from app.services import antishare
from app.services.ip_provider import MockIpProvider
from tests.conftest import utcnow


def _settings() -> Settings:
    return Settings(
        anti_sharing_enabled=True,
        default_ip_limit=3,
        warn_threshold_24h=5,
        critical_threshold_24h=8,
    )


def _ips(n: int, prefix: str = "10.0.0.") -> list[str]:
    return [f"{prefix}{i}" for i in range(1, n + 1)]


async def test_record_and_unique_count(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    now = utcnow()
    await antishare.record_ips(
        session, vpn_client.id, None, "e", ["1.1.1.1", "1.1.1.2", "1.1.1.1"], now=now
    )
    count = await antishare.unique_ip_count(
        session, vpn_client.id, now - timedelta(hours=24)
    )
    assert count == 2


async def test_window_separation(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    now = utcnow()
    # 2 IP час назад, 1 IP только что
    await antishare.record_ips(
        session, vpn_client.id, None, "e", ["2.0.0.1", "2.0.0.2"], now=now - timedelta(hours=2)
    )
    await antishare.record_ips(
        session, vpn_client.id, None, "e", ["2.0.0.3"], now=now - timedelta(minutes=5)
    )
    status = await antishare.compute_status(session, vpn_client.id, _settings(), now=now)
    assert status.counts["24h"] == 3
    assert status.counts["1h"] == 1
    assert status.counts["15m"] == 1


async def test_status_ok(session: AsyncSession, user: User, vpn_client: VpnClient):
    now = utcnow()
    await antishare.record_ips(
        session, vpn_client.id, None, "e", _ips(3), now=now - timedelta(hours=2)
    )
    status = await antishare.compute_status(session, vpn_client.id, _settings(), now=now)
    assert status.level == antishare.LEVEL_OK


async def test_status_warn_by_24h(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    now = utcnow()
    await antishare.record_ips(
        session, vpn_client.id, None, "e", _ips(5), now=now - timedelta(hours=2)
    )
    status = await antishare.compute_status(session, vpn_client.id, _settings(), now=now)
    assert status.level == antishare.LEVEL_WARN


async def test_status_warn_by_1h(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    now = utcnow()
    # 4 IP за последний час, но всего < warn_24h
    await antishare.record_ips(
        session, vpn_client.id, None, "e", _ips(4), now=now - timedelta(minutes=10)
    )
    status = await antishare.compute_status(session, vpn_client.id, _settings(), now=now)
    assert status.counts["24h"] == 4
    assert status.level == antishare.LEVEL_WARN


async def test_status_critical(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    now = utcnow()
    await antishare.record_ips(
        session, vpn_client.id, None, "e", _ips(8), now=now - timedelta(hours=2)
    )
    status = await antishare.compute_status(session, vpn_client.id, _settings(), now=now)
    assert status.level == antishare.LEVEL_CRITICAL


async def test_prune_old(session: AsyncSession, user: User, vpn_client: VpnClient):
    now = utcnow()
    await antishare.record_ips(
        session, vpn_client.id, None, "e", ["9.9.9.9"], now=now - timedelta(days=8)
    )
    await antishare.record_ips(
        session, vpn_client.id, None, "e", ["8.8.8.8"], now=now - timedelta(days=1)
    )
    removed = await antishare.prune_old(session, now=now)
    assert removed == 1
    count = await antishare.unique_ip_count(
        session, vpn_client.id, now - timedelta(days=7)
    )
    assert count == 1


async def test_collect_for_client(
    session: AsyncSession, user: User, vpn_client: VpnClient, server: Server
):
    provider = MockIpProvider(ips_by_server={server.id: ["5.5.5.5", "5.5.5.6"]})
    added = await antishare.collect_for_client(session, vpn_client, provider)
    assert added == 2
    count = await antishare.unique_ip_count(
        session, vpn_client.id, utcnow() - timedelta(hours=24)
    )
    assert count == 2


async def test_list_flagged(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    now = utcnow()
    await antishare.record_ips(
        session, vpn_client.id, None, "e", _ips(8), now=now - timedelta(hours=2)
    )
    flagged = await antishare.list_flagged(session, _settings(), now=now)
    assert len(flagged) == 1
    client, status = flagged[0]
    assert client.id == vpn_client.id
    assert status.level == antishare.LEVEL_CRITICAL

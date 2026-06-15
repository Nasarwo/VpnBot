from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import cast

from sqlalchemy import CursorResult, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import Settings
from app.db.models import ClientServerMapping, IpObservation, VpnClient
from app.db.repositories import MappingRepository
from app.services.ip_provider import IpProvider

# Окна наблюдения: метка -> длительность
WINDOWS: dict[str, timedelta] = {
    "15m": timedelta(minutes=15),
    "1h": timedelta(hours=1),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
}

LEVEL_OK = "ok"
LEVEL_WARN = "warn"
LEVEL_CRITICAL = "critical"

# Дольше этого срока наблюдения не нужны (самое длинное окно — 7 дней).
RETENTION = timedelta(days=7)


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


@dataclass(slots=True)
class SharingStatus:
    vpn_client_id: int
    counts: dict[str, int] = field(default_factory=dict)
    level: str = LEVEL_OK

    @property
    def unique_24h(self) -> int:
        return self.counts.get("24h", 0)


async def record_ips(
    session: AsyncSession,
    vpn_client_id: int,
    server_id: int | None,
    email: str | None,
    ips: list[str],
    now: datetime | None = None,
) -> int:
    """Сохраняет наблюдения IP. Возвращает число добавленных записей."""
    now = now or _utcnow()
    added = 0
    for ip in {ip.strip() for ip in ips if ip and ip.strip()}:
        session.add(
            IpObservation(
                vpn_client_id=vpn_client_id,
                server_id=server_id,
                email=email,
                ip=ip,
                observed_at=now,
            )
        )
        added += 1
    if added:
        await session.flush()
    return added


async def unique_ip_count(
    session: AsyncSession, vpn_client_id: int, since: datetime
) -> int:
    result = await session.execute(
        select(func.count(func.distinct(IpObservation.ip)))
        .where(IpObservation.vpn_client_id == vpn_client_id)
        .where(IpObservation.observed_at >= since)
    )
    return int(result.scalar_one())


async def recent_ips(
    session: AsyncSession, vpn_client_id: int, since: datetime
) -> list[str]:
    result = await session.execute(
        select(IpObservation.ip)
        .where(IpObservation.vpn_client_id == vpn_client_id)
        .where(IpObservation.observed_at >= since)
        .distinct()
    )
    return list(result.scalars().all())


def _level_for(counts: dict[str, int], settings: Settings) -> str:
    u24 = counts.get("24h", 0)
    u1 = counts.get("1h", 0)
    if u24 >= settings.critical_threshold_24h:
        return LEVEL_CRITICAL
    if u24 >= settings.warn_threshold_24h:
        return LEVEL_WARN
    if u1 > settings.default_ip_limit:
        return LEVEL_WARN
    return LEVEL_OK


async def compute_status(
    session: AsyncSession,
    vpn_client_id: int,
    settings: Settings,
    now: datetime | None = None,
) -> SharingStatus:
    now = now or _utcnow()
    counts: dict[str, int] = {}
    for label, window in WINDOWS.items():
        counts[label] = await unique_ip_count(session, vpn_client_id, now - window)
    return SharingStatus(
        vpn_client_id=vpn_client_id,
        counts=counts,
        level=_level_for(counts, settings),
    )


async def prune_old(
    session: AsyncSession, now: datetime | None = None
) -> int:
    """Удаляет наблюдения старше срока хранения. Возвращает число удалённых строк."""
    now = now or _utcnow()
    cutoff = now - RETENTION
    result = await session.execute(
        delete(IpObservation).where(IpObservation.observed_at < cutoff)
    )
    await session.flush()
    return int(cast("CursorResult[object]", result).rowcount or 0)


async def collect_for_client(
    session: AsyncSession,
    client: VpnClient,
    provider: IpProvider,
    now: datetime | None = None,
) -> int:
    """Собирает IP клиента со всех его серверов и сохраняет наблюдения."""
    now = now or _utcnow()
    total = 0
    mappings = await MappingRepository(session).list_for_client(client.id)
    for mapping in mappings:
        server = mapping.server
        if server is None or not server.enabled or not mapping.enabled:
            continue
        ips = await provider.get_ips(server, mapping)
        total += await record_ips(
            session,
            vpn_client_id=client.id,
            server_id=server.id,
            email=mapping.email,
            ips=ips,
            now=now,
        )
    return total


async def _active_clients(session: AsyncSession) -> list[VpnClient]:
    result = await session.execute(
        select(VpnClient).options(
            selectinload(VpnClient.mappings).selectinload(
                ClientServerMapping.server
            ),
            selectinload(VpnClient.user),
        )
    )
    return list(result.scalars().all())


async def collect_all(
    session: AsyncSession,
    provider: IpProvider,
    now: datetime | None = None,
) -> int:
    """Собирает IP по всем клиентам. Возвращает число добавленных наблюдений."""
    now = now or _utcnow()
    clients = await _active_clients(session)
    total = 0
    for client in clients:
        total += await collect_for_client(session, client, provider, now=now)
    await prune_old(session, now=now)
    await session.commit()
    return total


async def list_flagged(
    session: AsyncSession,
    settings: Settings,
    now: datetime | None = None,
) -> list[tuple[VpnClient, SharingStatus]]:
    """Возвращает клиентов со статусом warn/critical за последние 24 часа."""
    now = now or _utcnow()
    since = now - WINDOWS["24h"]
    ids_result = await session.execute(
        select(IpObservation.vpn_client_id)
        .where(IpObservation.observed_at >= since)
        .distinct()
    )
    client_ids = [int(cid) for cid in ids_result.scalars().all()]

    flagged: list[tuple[VpnClient, SharingStatus]] = []
    for cid in client_ids:
        status = await compute_status(session, cid, settings, now=now)
        if status.level == LEVEL_OK:
            continue
        client = await session.get(VpnClient, cid)
        if client is not None:
            await session.refresh(client, attribute_names=["user"])
            flagged.append((client, status))
    # Сначала самые проблемные.
    order = {LEVEL_CRITICAL: 0, LEVEL_WARN: 1, LEVEL_OK: 2}
    flagged.sort(key=lambda item: (order[item[1].level], -item[1].unique_24h))
    return flagged

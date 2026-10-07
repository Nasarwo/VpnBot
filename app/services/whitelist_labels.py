"""Confirmed business balances for subscription labels; never changes billing."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from app.config import Settings
from app.db.models import VpnClient, WhitelistAccount, WhitelistLedger
from app.db.session import get_sessionmaker
from app.services.whitelist import (
    EVENT_SETTLED,
    LEDGER_ADJUST,
    LEDGER_FREE_GRANT,
    LEDGER_PURCHASE,
    LEDGER_ROLLOUT,
    access_state,
)

logger = logging.getLogger(__name__)


def package_bases(events) -> dict[int, int]:
    """Replay ordered settled credits; usage and rebases never shrink the package."""
    bases: dict[int, int] = {}
    for event in events:
        if event.status != EVENT_SETTLED:
            continue
        if event.free_set is not None or event.kind in (
            LEDGER_ADJUST, LEDGER_FREE_GRANT, LEDGER_ROLLOUT
        ):
            bases[event.user_id] = event.free_after + event.paid_after
        elif event.kind == LEDGER_PURCHASE and event.user_id in bases:
            delta = event.paid_delta
            if delta is None:
                delta = max(0, event.paid_after - event.paid_before)
            bases[event.user_id] += delta
    return bases


async def confirmed_snapshots(session) -> list[dict]:
    accounts = (await session.scalars(select(WhitelistAccount))).all()
    clients = {c.user_id: c for c in (await session.scalars(
        select(VpnClient).options(selectinload(VpnClient.mappings))
    )).all()}
    events = (await session.scalars(select(WhitelistLedger).where(
        WhitelistLedger.status == EVENT_SETTLED
    ).order_by(WhitelistLedger.id))).all()
    bases = package_bases(events)
    now = datetime.now(UTC)
    snapshots = []
    for account in accounts:
        if not account.panel_email or account.desired_version != account.applied_version:
            continue
        if account.last_error or account.conflict:
            continue
        lifetime = access_state(clients.get(account.user_id), now).lifetime
        if not lifetime and account.user_id not in bases:
            continue
        times = [t.replace(tzinfo=UTC) if t.tzinfo is None else t for t in
                 (account.last_synced_at, account.applied_at) if t is not None]
        if not times:
            continue
        snapshots.append({
            "panel_email": account.panel_email,
            "remaining_bytes": account.free_bytes + account.paid_bytes,
            "package_bytes": bases.get(account.user_id, 0),
            "lifetime": lifetime,
            "as_of": max(times).isoformat(),
            "version": account.applied_version,
        })
    return snapshots


async def publish_confirmed_snapshots(settings: Settings) -> bool:
    if not settings.subhub_url or not settings.subhub_admin_token:
        return False
    try:
        async with get_sessionmaker()() as session:
            if session.get_bind().dialect.name == "postgresql":
                await session.execute(
                    text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                )
            snapshots = await confirmed_snapshots(session)
        async with httpx.AsyncClient(timeout=settings.subhub_timeout_seconds) as client:
            for start in range(0, len(snapshots), 200):
                response = await client.post(
                    settings.subhub_url.rstrip('/') + '/admin/whitelist/traffic',
                    headers={"X-Admin-Token": settings.subhub_admin_token},
                    json={"snapshots": snapshots[start:start + 200]},
                )
                response.raise_for_status()
        return True
    except Exception as exc:  # best effort: payments and background workers keep running
        logger.warning("SubHub: traffic labels deferred (%s)", type(exc).__name__)
        return False

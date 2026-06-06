from __future__ import annotations

import json
import uuid as uuid_lib
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import Protocol
from app.db.models import Server, ServerInbound, User, VpnClient
from app.db.repositories import (
    MappingRepository,
    ServerRepository,
    VpnClientRepository,
)
from app.services import audit
from app.services.panel_updater import (
    PanelUpdateError,
    PanelUpdater,
    ProvisionTarget,
    ServerUpdateResult,
)
from app.services.xui_client import XuiClient, XuiError

# Сопоставление протокола из панели/xray с нашим Enum.
_PROTOCOL_MAP: dict[str, Protocol] = {
    "vless": Protocol.VLESS,
    "vmess": Protocol.VMESS,
    "trojan": Protocol.TROJAN,
    "shadowsocks": Protocol.SHADOWSOCKS,
    "hysteria2": Protocol.HYSTERIA2,
    "hysteria": Protocol.HYSTERIA2,
}


def _expiry_to_ms(expiry: datetime) -> int:
    return int(expiry.timestamp() * 1000)


def _new_secret() -> str:
    return str(uuid_lib.uuid4())


def client_email(public_id: str, inbound_id: int) -> str:
    """Email клиента в панели. Уникален в пределах панели (public_id + inbound)."""
    return f"{public_id}-{inbound_id}"


async def has_targets(session: AsyncSession) -> bool:
    """Есть ли хотя бы один включённый сервер с включённым inbound для провижининга."""
    return await ServerRepository(session).has_provision_targets()


async def ensure_vpn_client(session: AsyncSession, user: User) -> VpnClient:
    """Возвращает VPN-клиента пользователя, создавая его при отсутствии."""
    client = await VpnClientRepository(session).get_for_user(user.id)
    if client is not None:
        if not client.external_client_id:
            client.external_client_id = _new_secret()
            await session.flush()
        return client

    client = VpnClient(
        user_id=user.id,
        display_name=user.username or user.first_name,
        email=user.public_id,
        external_client_id=_new_secret(),
        is_active=False,
    )
    session.add(client)
    await session.flush()
    return client


def _build_target(
    public_id: str,
    secret: str,
    server: Server,  # noqa: ARG001 - оставлено для расширяемости
    inbound: ServerInbound,
) -> ProvisionTarget:
    return ProvisionTarget(
        inbound_id=inbound.inbound_id,
        protocol=inbound.protocol,
        client_uuid=secret,
        password=secret,
        email=client_email(public_id, inbound.inbound_id),
        sub_id=public_id,
        flow=inbound.flow,
        method=inbound.method,
    )


async def apply_access(
    session: AsyncSession,
    vpn_client: VpnClient,
    public_id: str,
    expiry: datetime,
    updater: PanelUpdater,
) -> list[ServerUpdateResult]:
    """Создаёт/обновляет клиента на всех включённых серверах и inbound'ах.

    Идемпотентно: если клиент уже есть в inbound — обновляется срок действия,
    иначе клиент создаётся. Возвращает результат по каждому серверу/inbound.
    """
    expiry_ms = _expiry_to_ms(expiry)
    secret = vpn_client.external_client_id or _new_secret()
    vpn_client.external_client_id = secret

    server_repo = ServerRepository(session)
    mapping_repo = MappingRepository(session)

    servers = await server_repo.list_enabled_with_inbounds()
    existing = {
        (m.server_id, m.inbound_id): m
        for m in await mapping_repo.list_for_client(vpn_client.id)
    }

    results: list[ServerUpdateResult] = []
    covered: set[tuple[int, int]] = set()

    for server in servers:
        for inbound in server.inbounds:
            if not inbound.enabled:
                continue
            key = (server.id, inbound.inbound_id)
            covered.add(key)
            target = _build_target(public_id, secret, server, inbound)
            try:
                await updater.ensure_client(server, target, expiry_ms)
            except PanelUpdateError as exc:
                results.append(
                    ServerUpdateResult(
                        server_id=server.id, ok=False, error=str(exc)
                    )
                )
                continue
            if key not in existing:
                await mapping_repo.create(
                    vpn_client_id=vpn_client.id,
                    server_id=server.id,
                    inbound_id=inbound.inbound_id,
                    protocol=inbound.protocol,
                    client_uuid=secret,
                    email=target.email,
                    sub_id=public_id,
                )
            results.append(ServerUpdateResult(server_id=server.id, ok=True))

    # Унаследованные маппинги без конфигурации inbound — просто продлеваем срок.
    for (server_id, inbound_id), mapping in existing.items():
        if (server_id, inbound_id) in covered:
            continue
        server = mapping.server
        if server is None or not server.enabled or not mapping.enabled:
            continue
        try:
            await updater.update_expiry(server, mapping, expiry_ms)
            results.append(ServerUpdateResult(server_id=server_id, ok=True))
        except PanelUpdateError as exc:
            results.append(
                ServerUpdateResult(server_id=server_id, ok=False, error=str(exc))
            )

    return results


def _ss_method(settings_raw: object) -> str | None:
    if isinstance(settings_raw, str):
        try:
            settings = json.loads(settings_raw)
        except json.JSONDecodeError:
            return None
    elif isinstance(settings_raw, dict):
        settings = settings_raw
    else:
        return None
    method = settings.get("method")
    return method if isinstance(method, str) and method else None


async def import_inbounds(
    session: AsyncSession, server: Server, timeout: float = 15.0
) -> list[tuple[int, str, str]]:
    """Читает inbound'ы панели сервера и заводит недостающие ServerInbound.

    Возвращает список (inbound_id, protocol, action), где action: added/skipped/exists.
    """
    async with XuiClient(
        base_url=server.panel_url,
        username=server.username,
        password=server.password,
        timeout=timeout,
    ) as client:
        try:
            inbounds = await client.list_inbounds()
        except XuiError as exc:
            raise PanelUpdateError(str(exc)) from exc

    existing_ids = set(
        (
            await session.execute(
                select(ServerInbound.inbound_id).where(
                    ServerInbound.server_id == server.id
                )
            )
        )
        .scalars()
        .all()
    )

    summary: list[tuple[int, str, str]] = []
    for inb in inbounds:
        proto_raw = str(inb.get("protocol", "")).lower()
        inbound_id = inb.get("id")
        if not isinstance(inbound_id, int):
            continue
        protocol = _PROTOCOL_MAP.get(proto_raw)
        if protocol is None:
            summary.append((inbound_id, proto_raw or "?", "skipped"))
            continue
        if inbound_id in existing_ids:
            summary.append((inbound_id, protocol.value, "exists"))
            continue
        method = (
            _ss_method(inb.get("settings"))
            if protocol == Protocol.SHADOWSOCKS
            else None
        )
        session.add(
            ServerInbound(
                server_id=server.id,
                inbound_id=inbound_id,
                protocol=protocol,
                flow=None,
                method=method,
                remark=str(inb.get("remark") or "") or None,
                enabled=True,
            )
        )
        summary.append((inbound_id, protocol.value, "added"))
    await session.flush()
    return summary


async def provision_for_user(
    session: AsyncSession,
    user: User,
    expiry: datetime,
    updater: PanelUpdater,
    actor_user_id: int | None = None,
) -> tuple[VpnClient, list[ServerUpdateResult]]:
    """Высокоуровневая обёртка: гарантирует клиента и применяет доступ ко всем панелям."""
    client = await ensure_vpn_client(session, user)
    public_id = user.public_id or client.email or str(user.id)
    results = await apply_access(session, client, public_id, expiry, updater)
    await audit.record(
        session,
        action="provisioning.apply",
        actor_user_id=actor_user_id,
        entity_type="vpn_client",
        entity_id=client.id,
        payload={
            "ok": [r.server_id for r in results if r.ok],
            "failed": [r.server_id for r in results if not r.ok],
        },
    )
    return client, results

from __future__ import annotations

import json
import logging
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
    ProvisionInbound,
    ServerProvision,
    ServerUpdateResult,
)
from app.services.xui_client import XuiClient, XuiError

# Сопоставление протокола из панели/xray с нашим Enum.
logger = logging.getLogger(__name__)

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


def client_email(public_id: str) -> str:
    """Email клиента в панели. Глобален в пределах панели (= public_id).

    В 3x-ui >= 3.2.x клиент один на панель и привязывается ко всем inbound'ам,
    поэтому email и subId совпадают с public_id (по subId работает подписка).
    """
    return public_id


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
            logger.info(
                "ensure_vpn_client: проставлен secret клиенту id=%s", client.id
            )
        return client

    logger.info(
        "ensure_vpn_client: создаю VPN-клиента для user_id=%s public_id=%s",
        user.id,
        user.public_id,
    )
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


def _build_spec(
    public_id: str, secret: str, inbounds: list[ServerInbound]
) -> ServerProvision:
    return ServerProvision(
        email=client_email(public_id),
        sub_id=public_id,
        client_uuid=secret,
        password=secret,
        inbounds=[
            ProvisionInbound(
                inbound_id=i.inbound_id,
                protocol=i.protocol,
                flow=i.flow,
                method=i.method,
            )
            for i in inbounds
        ],
    )


async def apply_access(
    session: AsyncSession,
    vpn_client: VpnClient,
    public_id: str,
    expiry: datetime,
    updater: PanelUpdater,
) -> list[ServerUpdateResult]:
    """Создаёт/обновляет клиента на всех включённых серверах.

    На каждый сервер заводится один глобальный клиент (email=subId=public_id),
    привязанный ко всем включённым inbound'ам этого сервера. Идемпотентно:
    повторный вызов продлевает срок. Возвращает результат по каждому серверу.
    """
    expiry_ms = _expiry_to_ms(expiry)
    secret = vpn_client.external_client_id or _new_secret()
    vpn_client.external_client_id = secret
    email = client_email(public_id)

    server_repo = ServerRepository(session)
    mapping_repo = MappingRepository(session)

    servers = await server_repo.list_enabled_with_inbounds()
    existing_servers = {
        m.server_id for m in await mapping_repo.list_for_client(vpn_client.id)
    }
    logger.info(
        "apply_access: client_id=%s public_id=%s expiry=%s серверов=%s "
        "уже_привязано_серверов=%s",
        vpn_client.id,
        public_id,
        expiry.isoformat(),
        len(servers),
        len(existing_servers),
    )

    results: list[ServerUpdateResult] = []
    covered_any = False

    for server in servers:
        enabled_inbounds = [i for i in server.inbounds if i.enabled]
        if not enabled_inbounds:
            logger.warning(
                "apply_access: у сервера #%s (%s) нет включённых inbound'ов "
                "— пропускаю (сделайте /importinbounds %s)",
                server.id,
                server.name,
                server.id,
            )
            continue
        covered_any = True
        spec = _build_spec(public_id, secret, enabled_inbounds)
        try:
            await updater.provision_server(server, spec, expiry_ms)
        except PanelUpdateError as exc:
            logger.warning(
                "apply_access: ошибка на server=%s email=%s: %s",
                server.id,
                email,
                exc,
            )
            results.append(
                ServerUpdateResult(server_id=server.id, ok=False, error=str(exc))
            )
            continue
        if server.id not in existing_servers:
            primary = enabled_inbounds[0]
            await mapping_repo.create(
                vpn_client_id=vpn_client.id,
                server_id=server.id,
                inbound_id=primary.inbound_id,
                protocol=primary.protocol,
                client_uuid=secret,
                email=email,
                sub_id=public_id,
            )
        results.append(ServerUpdateResult(server_id=server.id, ok=True))

    if not covered_any and not existing_servers:
        logger.warning(
            "apply_access: нет ни одного целевого inbound и ни одной привязки "
            "— клиент не будет создан. Проверьте /servers и /importinbounds."
        )

    ok_count = sum(1 for r in results if r.ok)
    fail_count = len(results) - ok_count
    logger.info(
        "apply_access завершён: client_id=%s успешно=%s ошибок=%s",
        vpn_client.id,
        ok_count,
        fail_count,
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

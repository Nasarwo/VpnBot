from __future__ import annotations

import json
import logging
import uuid as uuid_lib
from dataclasses import dataclass, field
from datetime import UTC, datetime

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
from app.services.xui_payloads import pick_panel_client_secret

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


def _expiry_to_ms(expiry: datetime | None) -> int:
    if expiry is None:
        return 0
    return int(expiry.timestamp() * 1000)


def _ms_to_datetime(expiry_ms: int) -> datetime | None:
    """0/отрицательное значение в 3x-ui означает «без срока» → None."""
    if not expiry_ms or expiry_ms <= 0:
        return None
    return datetime.fromtimestamp(expiry_ms / 1000, tz=UTC)


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
    email: str, sub_id: str, secret: str, inbounds: list[ServerInbound]
) -> ServerProvision:
    return ServerProvision(
        email=email,
        sub_id=sub_id,
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
    expiry: datetime | None,
    updater: PanelUpdater,
) -> list[ServerUpdateResult]:
    """Создаёт/обновляет клиента на всех включённых серверах.

    На каждый сервер заводится один глобальный клиент (email=subId=public_id),
    привязанный ко всем включённым inbound'ам этого сервера. Идемпотентно:
    повторный вызов продлевает срок. ``expiry=None`` — без срока (expiryTime=0).
    Возвращает результат по каждому серверу.
    """
    expiry_ms = _expiry_to_ms(expiry)

    server_repo = ServerRepository(session)
    mapping_repo = MappingRepository(session)

    existing_mappings = await mapping_repo.list_for_client(vpn_client.id)
    existing_servers = {m.server_id for m in existing_mappings}
    # Если у клиента уже есть привязка (в т.ч. импортированный из панели клиент),
    # переиспользуем её идентичность (email/uuid/subId), чтобы продлевать именно
    # существующего клиента, а не плодить нового.
    anchor = existing_mappings[0] if existing_mappings else None
    if anchor is not None:
        secret = anchor.client_uuid
        email = anchor.email
        sub_id = anchor.sub_id or public_id
    else:
        secret = vpn_client.external_client_id or _new_secret()
        email = client_email(public_id)
        sub_id = public_id
    vpn_client.external_client_id = secret

    servers = await server_repo.list_enabled_with_inbounds()
    expiry_label = expiry.isoformat() if expiry is not None else "без срока"
    logger.info(
        "apply_access: client_id=%s public_id=%s expiry=%s серверов=%s "
        "уже_привязано_серверов=%s",
        vpn_client.id,
        public_id,
        expiry_label,
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
        spec = _build_spec(email, sub_id, secret, enabled_inbounds)
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
                sub_id=sub_id,
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


async def ensure_inbounds_imported(
    session: AsyncSession, timeout: float = 15.0
) -> bool:
    """Импортирует inbound'ы для включённых серверов, у которых их ещё нет.

    Нужно для сценария «сервер добавлен, но inbound'ы не импортированы»: тогда
    провижинг нового клиента (оплата/триал) не находил целей и падал в «серверы
    не настроены». Здесь мы один раз подтягиваем inbound'ы с панели.

    Возвращает True, если после импорта появилась хотя бы одна цель провижининга.
    Сетевые ошибки отдельных панелей не прерывают процесс.
    """
    repo = ServerRepository(session)
    servers = await repo.list_enabled_with_inbounds()
    for server in servers:
        if any(i.enabled for i in server.inbounds):
            continue
        try:
            summary = await import_inbounds(session, server, timeout)
            logger.info(
                "ensure_inbounds_imported: сервер #%s (%s) импорт: %s",
                server.id,
                server.name,
                summary,
            )
        except PanelUpdateError as exc:
            logger.warning(
                "ensure_inbounds_imported: сервер #%s (%s) импорт не удался: %s",
                server.id,
                server.name,
                exc,
            )
    return await repo.has_provision_targets()


@dataclass(slots=True)
class PanelClientInfo:
    """Нормализованные данные существующего клиента панели."""

    email: str
    sub_id: str
    secret: str
    expiry_ms: int
    enable: bool
    inbound_ids: list[int]


@dataclass(slots=True)
class ServerClientPresence:
    """Клиент найден на конкретном сервере."""

    server: Server
    info: PanelClientInfo


@dataclass(slots=True)
class BindResult:
    public_id: str
    email: str
    expires_at: datetime | None
    inbound_ids: list[int]
    synced: bool
    results: list[ServerUpdateResult] = field(default_factory=list)


async def list_panel_clients(
    server: Server, timeout: float = 15.0
) -> list[dict[str, object]]:
    """Возвращает список клиентов, уже существующих на панели сервера."""
    async with XuiClient(
        base_url=server.panel_url,
        username=server.username,
        password=server.password,
        timeout=timeout,
    ) as client:
        try:
            return await client.list_client_records()
        except XuiError as exc:
            raise PanelUpdateError(str(exc)) from exc


def _pick_secret(*values: object) -> str:
    """Fallback для legacy API: первое непустое строковое значение."""
    for value in values:
        if isinstance(value, str) and value:
            return value
    return ""


def _panel_client_secret(client: dict[str, object]) -> str:
    secret = pick_panel_client_secret(client)  # type: ignore[arg-type]
    if secret:
        return secret
    return _pick_secret(
        client.get("uuid"), client.get("id"), client.get("password"), client.get("auth")
    )


async def find_panel_client(
    server: Server, email: str, timeout: float = 15.0
) -> PanelClientInfo | None:
    """Ищет клиента панели по email и нормализует его поля."""
    async with XuiClient(
        base_url=server.panel_url,
        username=server.username,
        password=server.password,
        timeout=timeout,
    ) as client:
        try:
            if await client.supports_clients_api():
                record = await client.get_client_record(email)
                if record is None:
                    return None
                c = record.get("client") if isinstance(record, dict) else None
                c = c if isinstance(c, dict) else {}
                inbound_ids = [
                    int(i)
                    for i in (record.get("inboundIds") or [])
                    if isinstance(i, int)
                ]
                secret = _panel_client_secret(c)
                return PanelClientInfo(
                    email=str(c.get("email") or email),
                    sub_id=str(c.get("subId") or ""),
                    secret=secret,
                    expiry_ms=int(c.get("expiryTime") or 0),
                    enable=bool(c.get("enable", True)),
                    inbound_ids=inbound_ids,
                )
            # Старые панели: ищем по settings.clients[] всех inbound'ов.
            records = await client.list_client_records()
        except XuiError as exc:
            raise PanelUpdateError(str(exc)) from exc

    matches = [r for r in records if r.get("email") == email]
    if not matches:
        return None
    inbound_ids = [
        int(r["_inbound_id"])
        for r in matches
        if isinstance(r.get("_inbound_id"), int)
    ]
    first = matches[0]
    secret = _pick_secret(
        first.get("id"), first.get("password"), first.get("auth")
    )
    return PanelClientInfo(
        email=email,
        sub_id=str(first.get("subId") or ""),
        secret=secret,
        expiry_ms=int(first.get("expiryTime") or 0),
        enable=bool(first.get("enable", True)),
        inbound_ids=inbound_ids,
    )


async def find_client_presence_on_servers(
    session: AsyncSession,
    public_id: str,
    timeout: float = 15.0,
) -> list[ServerClientPresence]:
    """Ищет клиента по email или subId на всех включённых серверах."""
    servers = await ServerRepository(session).list_enabled()
    found: list[ServerClientPresence] = []
    for server in servers:
        info = await find_panel_client(server, public_id, timeout)
        if info is None:
            info = await _find_panel_client_by_sub_id(server, public_id, timeout)
        if info is not None:
            found.append(ServerClientPresence(server=server, info=info))
    return found


def _resolve_reference_expiry(
    presences: list[ServerClientPresence],
) -> datetime | None:
    """Берёт максимальный срок среди серверов, где клиент уже есть."""
    if not presences:
        return None
    finite = [p.info.expiry_ms for p in presences if p.info.expiry_ms > 0]
    if not finite:
        return None
    return _ms_to_datetime(max(finite))


def _resolve_client_identity(
    presences: list[ServerClientPresence], public_id: str
) -> tuple[str, str, str]:
    """Возвращает (email, sub_id, secret) для синхронизации по всем серверам.

    ``public_id`` — ID из ссылки-подписки (subId). Email в панели может отличаться
    (например, email=``custom-user``, subId=``dsh``); для подписки всегда
    используем ``public_id`` из ссылки.
    """
    anchor = presences[0]
    for presence in presences:
        if presence.info.secret:
            anchor = presence
            break
    email = anchor.info.email or public_id
    sub_id = public_id
    secret = anchor.info.secret or _new_secret()
    return email, sub_id, secret


async def _ensure_presence_mappings(
    session: AsyncSession,
    client: VpnClient,
    presences: list[ServerClientPresence],
    email: str,
    sub_id: str,
    secret: str,
) -> None:
    """Создаёт записи привязки для серверов, где клиент уже найден на панели."""
    mapping_repo = MappingRepository(session)
    existing_servers = {
        m.server_id for m in await mapping_repo.list_for_client(client.id)
    }
    server_repo = ServerRepository(session)
    for presence in presences:
        server = presence.server
        if server.id in existing_servers:
            continue
        primary_inbound = (
            presence.info.inbound_ids[0] if presence.info.inbound_ids else 0
        )
        configured = await server_repo.get_inbound(server.id, primary_inbound)
        protocol = configured.protocol if configured else Protocol.VLESS
        await mapping_repo.create(
            vpn_client_id=client.id,
            server_id=server.id,
            inbound_id=primary_inbound,
            protocol=protocol,
            client_uuid=secret,
            email=email,
            sub_id=sub_id,
        )
        existing_servers.add(server.id)


async def sync_bound_client_to_all_servers(
    session: AsyncSession,
    client: VpnClient,
    public_id: str,
    expiry: datetime | None,
    updater: PanelUpdater,
    *,
    fail_on_partial: bool = True,
) -> list[ServerUpdateResult]:
    """Создаёт/обновляет клиента на всех серверах с inbound'ами.

    На серверах, где клиента ещё нет, создаёт его с указанным сроком.
    """
    results = await apply_access(session, client, public_id, expiry, updater)
    failed = [r for r in results if not r.ok]
    if fail_on_partial and failed:
        raise PanelUpdateError(
            "; ".join(f"server {r.server_id}: {r.error}" for r in failed)
        )
    return results


async def _finalize_bound_client(
    session: AsyncSession,
    user: User,
    public_id: str,
    presences: list[ServerClientPresence],
    updater: PanelUpdater,
) -> BindResult:
    """Общая логика привязки: клиент в БД + синхронизация по всем серверам."""
    if not presences:
        raise PanelUpdateError(
            f"Клиент с ID {public_id} не найден ни на одном настроенном сервере"
        )

    email, sub_id, secret = _resolve_client_identity(presences, public_id)
    if await _public_id_taken(session, public_id, user.id):
        raise PanelUpdateError(
            f"ID {public_id} уже привязан к другому пользователю"
        )

    user.public_id = public_id
    await session.flush()

    reference_expiry = _resolve_reference_expiry(presences)
    now = datetime.now(tz=UTC)
    is_active = any(p.info.enable for p in presences) and (
        reference_expiry is None or reference_expiry > now
    )

    client = await VpnClientRepository(session).get_for_user(user.id)
    if client is None:
        client = VpnClient(
            user_id=user.id,
            display_name=user.username or user.first_name,
            email=email,
            external_client_id=secret,
            expires_at=reference_expiry,
            is_active=is_active,
        )
        session.add(client)
        await session.flush()
    else:
        client.email = email
        client.external_client_id = secret
        client.expires_at = reference_expiry
        client.is_active = is_active
        await session.flush()

    await _ensure_presence_mappings(
        session, client, presences, email, sub_id, secret
    )

    logger.info(
        "finalize_bound_client: user=%s public_id=%s email=%s "
        "найден_на_серверах=%s expiry=%s",
        user.id,
        public_id,
        email,
        [p.server.id for p in presences],
        reference_expiry.isoformat() if reference_expiry else "без срока",
    )

    results = await sync_bound_client_to_all_servers(
        session,
        client,
        public_id,
        reference_expiry,
        updater,
        fail_on_partial=True,
    )

    inbound_ids = presences[0].info.inbound_ids
    return BindResult(
        public_id=public_id,
        email=email,
        expires_at=reference_expiry,
        inbound_ids=inbound_ids,
        synced=True,
        results=results,
    )


async def _public_id_taken(
    session: AsyncSession, public_id: str, exclude_user_id: int
) -> bool:
    result = await session.execute(
        select(User.id).where(
            User.public_id == public_id, User.id != exclude_user_id
        )
    )
    return result.first() is not None


async def bind_existing_client(
    session: AsyncSession,
    server: Server,
    email: str,
    user: User,
    updater: PanelUpdater,
    timeout: float = 15.0,
) -> BindResult:
    """Привязывает существующего клиента панели к пользователю бота.

    Ищет клиента на всех серверах, создаёт недостающие записи на панелях
    с тем же сроком, что уже выставлен на серверах, где клиент есть.
    """
    info = await find_panel_client(server, email, timeout)
    if info is None:
        raise PanelUpdateError(
            f"Клиент {email} не найден на панели сервера #{server.id}"
        )

    public_id = info.sub_id or user.public_id or info.email
    presences = await find_client_presence_on_servers(session, public_id, timeout)
    if not presences:
        presences = [ServerClientPresence(server=server, info=info)]

    return await _finalize_bound_client(
        session, user, public_id, presences, updater
    )


async def bind_user_by_public_id(
    session: AsyncSession,
    user: User,
    public_id: str,
    updater: PanelUpdater,
    timeout: float = 15.0,
) -> BindResult:
    """Привязывает пользователя по ID из ссылки-подписки.

    Ищет клиента на всех включённых серверах, затем создаёт его на серверах,
    где записи ещё нет, с тем же сроком, что на уже существующих.
    """
    if await _public_id_taken(session, public_id, user.id):
        raise PanelUpdateError(
            f"ID {public_id} уже привязан к другому пользователю бота"
        )

    presences = await find_client_presence_on_servers(session, public_id, timeout)
    return await _finalize_bound_client(
        session, user, public_id, presences, updater
    )


async def _find_panel_client_by_sub_id(
    server: Server, sub_id: str, timeout: float = 15.0
) -> PanelClientInfo | None:
    """Ищет клиента панели по subId (если email не совпадает с public_id)."""
    try:
        records = await list_panel_clients(server, timeout)
    except PanelUpdateError:
        return None
    for record in records:
        client = record.get("client") if isinstance(record.get("client"), dict) else record
        if not isinstance(client, dict):
            continue
        if str(client.get("subId") or "") != sub_id:
            continue
        email = str(client.get("email") or sub_id)
        return await find_panel_client(server, email, timeout)
    return None


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

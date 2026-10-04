from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import Protocol
from app.db.models import ClientServerMapping, IpObservation, Server, User, VpnClient
from app.db.repositories import MappingRepository, VpnClientRepository
from app.services import audit, whitelist
from app.services.operation_lock import serialized_access
from app.services.panel_updater import PanelUpdateError, PanelUpdater, ServerUpdateResult

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SubscriptionDeleteResult:
    deleted: bool
    no_client: bool = False
    failed_servers: list[ServerUpdateResult] = field(default_factory=list)


@serialized_access("user", "user_object")
async def delete_user_subscription(
    session: AsyncSession,
    user: User,
    updater: PanelUpdater,
    actor_user_id: int | None = None,
) -> SubscriptionDeleteResult:
    """Удаляет VPN-подписку пользователя с панелей и из БД бота.

    История оплат, заявки и сам пользователь остаются в БД. Если хотя бы один сервер
    не подтвердил удаление, локальные данные не удаляются, чтобы операцию можно было
    повторить из админки.
    """
    client = await VpnClientRepository(session).get_for_user(user.id)
    if client is None:
        return SubscriptionDeleteResult(deleted=False, no_client=True)

    mappings = await MappingRepository(session).list_for_client(client.id)
    by_server: dict[int, tuple[Server, list[ClientServerMapping]]] = {}
    for mapping in mappings:
        if mapping.server is None:
            continue
        by_server.setdefault(mapping.server.id, (mapping.server, []))[1].append(mapping)

    account = await whitelist.get_account(session, user.id)
    if account is not None and account.panel_email and account.server_id is not None:
        # Расход удаляемого клиента сверяется до удаления его счётчика.
        await whitelist.settle_before_removal(session, user.id, updater)
        wl_server = await session.get(Server, account.server_id)
        if wl_server is not None:
            # Клиент whitelist-панели не хранится в mappings: удаляем по учёту.
            # Временный объект не связан с сессией и не сохраняется в БД.
            by_server.setdefault(wl_server.id, (wl_server, []))[1].append(
                ClientServerMapping(
                    vpn_client_id=client.id,
                    server_id=wl_server.id,
                    inbound_id=0,
                    protocol=Protocol.VLESS,
                    client_uuid=client.external_client_id or account.panel_email,
                    email=account.panel_email,
                    sub_id=account.panel_email,
                )
            )

    failed: list[ServerUpdateResult] = []
    ok: list[ServerUpdateResult] = []
    for server, server_mappings in by_server.values():
        try:
            await updater.delete_client(server, server_mappings)
        except PanelUpdateError as exc:
            failed.append(
                ServerUpdateResult(server_id=server.id, ok=False, error=str(exc))
            )
        else:
            ok.append(ServerUpdateResult(server_id=server.id, ok=True))

    if failed:
        await audit.record(
            session,
            action="subscription_delete.failed",
            actor_user_id=actor_user_id,
            entity_type="vpn_client",
            entity_id=client.id,
            payload={"failed_servers": [r.server_id for r in failed]},
        )
        await session.commit()
        return SubscriptionDeleteResult(deleted=False, failed_servers=failed)

    # Остатки трафика сохраняются; новая выдача начнёт новую точку отсчёта.
    await whitelist.forget_panel_client(session, user.id)
    await _delete_local_subscription(session, client)
    await audit.record(
        session,
        action="subscription_delete.deleted",
        actor_user_id=actor_user_id,
        entity_type="user",
        entity_id=user.id,
        payload={"ok_servers": [r.server_id for r in ok]},
    )
    await session.commit()
    logger.info(
        "subscription deleted: user_id=%s telegram_id=%s servers=%s",
        user.id,
        user.telegram_id,
        [r.server_id for r in ok],
    )
    return SubscriptionDeleteResult(deleted=True)


async def _delete_local_subscription(
    session: AsyncSession, client: VpnClient
) -> None:
    await session.execute(
        delete(IpObservation).where(IpObservation.vpn_client_id == client.id)
    )
    await session.delete(client)
    await session.flush()

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Server
from app.db.repositories import ServerRepository
from app.services import pending_updates
from app.services.panel_updater import PanelUpdater
from app.services.xui_client import XuiClient

logger = logging.getLogger(__name__)


async def check_server(server: Server, timeout: float = 10.0) -> bool:
    """Проверяет доступность панели 3x-ui одного сервера.

    Успешный login считается признаком работоспособности. Любая ошибка
    (сеть/авторизация/таймаут) трактуется как недоступность.
    """
    try:
        async with XuiClient(
            base_url=server.panel_url,
            username=server.username,
            password=server.password,
            timeout=timeout,
        ) as client:
            await client.login()
        return True
    except Exception as exc:  # noqa: BLE001 - любой сбой = сервер недоступен
        logger.info("Health-check сервера #%s неуспешен: %s", server.id, exc)
        return False


async def check_servers(
    session: AsyncSession,
    timeout: float = 10.0,
    updater: PanelUpdater | None = None,
    on_updates_applied: Callable[[], Awaitable[object]] | None = None,
) -> dict[int, bool]:
    """Проверяет все серверы и сохраняет результат в БД.

    Возвращает отображение server_id -> online.
    """
    repo = ServerRepository(session)
    servers = await repo.list_all()
    result: dict[int, bool] = {}
    applied_any = False
    for server in servers:
        online = await check_server(server, timeout=timeout)
        await repo.set_status(server.id, online)
        result[server.id] = online
        if online and updater is not None:
            try:
                pending_results = await pending_updates.apply_pending_for_server(
                    session, server.id, updater
                )
            except Exception:  # noqa: BLE001
                logger.exception(
                    "Ошибка применения отложенных обновлений server #%s", server.id
                )
                continue
            applied = sum(1 for item in pending_results if item.ok)
            applied_any = applied_any or applied > 0
            failed = len(pending_results) - applied
            if pending_results:
                logger.info(
                    "Pending updates server #%s: applied=%s failed=%s",
                    server.id,
                    applied,
                    failed,
                )
    await session.commit()
    if applied_any and on_updates_applied is not None:
        await on_updates_applied()
    logger.info(
        "Health-check серверов: %s",
        ", ".join(f"#{sid}:{'ok' if ok else 'down'}" for sid, ok in result.items())
        or "нет серверов",
    )
    return result

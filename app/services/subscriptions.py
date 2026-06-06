from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import VpnClient
from app.db.repositories import ServerRepository


def _sub_link(base: str, public_id: str) -> str:
    base = base if base.endswith("/") else base + "/"
    return base + public_id


async def collect_links(
    session: AsyncSession, client: VpnClient | None, public_id: str | None
) -> list[tuple[str, str]]:
    """Возвращает список (метка, ссылка-подписка) по всем серверам пользователя.

    Для каждой панели формируется ссылка на встроенную подписку 3x-ui по общему
    sub_id (public_id). Дополнительно учитываются устаревшие статические ссылки.
    """
    links: list[tuple[str, str]] = []

    if public_id:
        servers = await ServerRepository(session).list_enabled()
        for server in servers:
            if not server.subscription_base:
                continue
            label = server.name
            if server.country:
                label = f"{server.name} ({server.country})"
            links.append((label, _sub_link(server.subscription_base, public_id)))

    if client is not None:
        if client.subscription_url_direct:
            links.append(("Прямое подключение", client.subscription_url_direct))
        if client.subscription_url_ru_proxy:
            links.append(
                ("Подключение через RU-прокси", client.subscription_url_ru_proxy)
            )
    return links

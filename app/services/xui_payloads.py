from __future__ import annotations

from app.db.enums import Protocol


class UnsupportedProtocolError(Exception):
    """Протокол не поддерживается провижинингом."""


def build_client_object(
    protocol: Protocol,
    *,
    client_uuid: str,
    password: str,
    email: str,
    sub_id: str,
    expiry_ms: int,
    flow: str | None = None,
    method: str | None = None,
    limit_ip: int = 0,
    total_gb: int = 0,
    tg_id: str = "",
) -> dict[str, object]:
    """Формирует объект клиента 3x-ui для addClient/updateClient.

    Состав полей зависит только от протокола (vless/vmess/trojan/shadowsocks/
    hysteria2). Транспорт (reality/ws/grpc/xhttp/tcp) задаётся на уровне inbound и
    на объект клиента не влияет, кроме flow для vless+reality.
    """
    base: dict[str, object] = {
        "email": email,
        "enable": True,
        "expiryTime": expiry_ms,
        "limitIp": limit_ip,
        "totalGB": total_gb,
        "tgId": tg_id,
        "subId": sub_id,
        "reset": 0,
    }

    if protocol == Protocol.VLESS:
        return {**base, "id": client_uuid, "flow": flow or ""}
    if protocol == Protocol.VMESS:
        return {**base, "id": client_uuid}
    if protocol == Protocol.TROJAN:
        obj = {**base, "password": password}
        if flow:
            obj["flow"] = flow
        return obj
    if protocol == Protocol.SHADOWSOCKS:
        obj = {**base, "password": password}
        if method:
            obj["method"] = method
        return obj
    if protocol == Protocol.HYSTERIA2:
        # В 3x-ui клиент hysteria2 использует поле auth, а не password.
        return {**base, "auth": password}

    raise UnsupportedProtocolError(f"Протокол {protocol} не поддерживается")


def build_client_record(
    *,
    client_uuid: str,
    password: str,
    email: str,
    sub_id: str,
    expiry_ms: int,
    flow: str | None = None,
    limit_ip: int = 0,
    total_gb: int = 0,
) -> dict[str, object]:
    """Унифицированный объект клиента для нового client-API (3x-ui >= 3.2.x).

    Один клиент привязывается сразу к нескольким inbound'ам разных протоколов.
    Панель сама подставляет нужные поля по протоколу каждого inbound (id для
    vless/vmess, password для trojan, ключ для shadowsocks, auth для hysteria2)
    и убирает flow там, где он неприменим. Поэтому здесь задаём «суперсет» полей.
    """
    obj: dict[str, object] = {
        "id": client_uuid,
        "password": password,
        "auth": password,
        "email": email,
        "subId": sub_id,
        "enable": True,
        "expiryTime": expiry_ms,
        "limitIp": limit_ip,
        "totalGB": total_gb,
        "tgId": 0,
        "reset": 0,
    }
    if flow:
        obj["flow"] = flow
    return obj


def client_identifier(protocol: Protocol, *, client_uuid: str, email: str) -> str:
    """Идентификатор клиента в пути updateClient/{id}.

    Для vless/vmess — это UUID клиента, для остальных — email.
    """
    if protocol in (Protocol.VLESS, Protocol.VMESS):
        return client_uuid
    return email

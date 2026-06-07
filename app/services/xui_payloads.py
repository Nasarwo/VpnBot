from __future__ import annotations

from typing import Any

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


def _looks_like_db_id(value: str) -> bool:
    """Числовой id из ClientRecord панели — не UUID клиента."""
    return value.isdigit()


def pick_panel_client_secret(client: dict[str, Any]) -> str:
    """Извлекает стабильный секрет клиента из объекта панели (clients/get).

    Не использует числовой DB-ключ в поле ``id`` — только UUID/пароль/auth.
    """
    uuid_val = client.get("uuid")
    if isinstance(uuid_val, str) and uuid_val and not _looks_like_db_id(uuid_val):
        return uuid_val
    id_val = client.get("id")
    if isinstance(id_val, str) and id_val and not _looks_like_db_id(id_val):
        return id_val
    for key in ("password", "auth"):
        val = client.get(key)
        if isinstance(val, str) and val:
            return val
    return ""


def client_record_body(record: dict[str, Any]) -> dict[str, Any] | None:
    """Извлекает model.Client из ответа ``clients/get``."""
    nested = record.get("client")
    if isinstance(nested, dict):
        return dict(nested)
    if "email" in record:
        return dict(record)
    return None


def merge_client_record_for_update(
    existing: dict[str, Any],
    *,
    email: str,
    sub_id: str,
    expiry_ms: int,
    enable: bool = True,
    flow: str | None = None,
) -> dict[str, Any]:
    """Тело ``clients/update``: сохраняет секреты панели, меняет срок и enable.

    Поля ``id``, ``password``, ``auth``, ``method`` и пр. не перезаписываются —
    иначе ломаются мультипротокольные клиенты (hysteria auth ≠ vless uuid).
    """
    merged = dict(existing)
    merged["email"] = email
    merged["subId"] = sub_id
    merged["enable"] = enable
    merged["expiryTime"] = expiry_ms
    if flow and not merged.get("flow"):
        merged["flow"] = flow
    return merged


def client_identifier(protocol: Protocol, *, client_uuid: str, email: str) -> str:
    """Идентификатор клиента в пути updateClient/{id}.

    Для vless/vmess — это UUID клиента, для остальных — email.
    """
    if protocol in (Protocol.VLESS, Protocol.VMESS):
        return client_uuid
    return email

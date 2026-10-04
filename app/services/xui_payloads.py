from __future__ import annotations

import json
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
    tg_id: int = 0,
    enable: bool = True,
    quota_policy: bool = False,
) -> dict[str, object]:
    """Унифицированный объект клиента для нового client-API (3x-ui >= 3.2.x).

    ``total_gb`` — значение поля totalGB в байтах (0 — безлимит).
    ``quota_policy`` — клиент с учётом трафика: автоматические сбросы панели
    выключены, чтобы счётчик расхода не обнулялся без ведома бота.

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
        "enable": enable,
        "expiryTime": expiry_ms,
        "limitIp": limit_ip,
        "totalGB": total_gb,
        "tgId": tg_id,
        "reset": 0,
    }
    if quota_policy:
        obj.update(_QUOTA_RESET_POLICY)
    if flow:
        obj["flow"] = flow
    return obj


# Панель не должна сама обнулять счётчик или продлевать клиента с квотой:
# бесплатный пакет выдаётся только при оплате, а не по календарю.
_QUOTA_RESET_POLICY: dict[str, object] = {
    "reset": 0,
    "resetDay": 0,
    "resetWeekday": 0,
    "resetMax": 0,
    "trafficReset": "never",
}


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
    tg_id: int | None = None,
    total_bytes: int | None = None,
    quota_policy: bool = False,
) -> dict[str, Any]:
    """Тело ``clients/update``: сохраняет секреты панели, меняет срок и enable.

    Поля ``id``, ``password``, ``auth``, ``method`` и пр. не перезаписываются —
    иначе ломаются мультипротокольные клиенты (hysteria auth ≠ vless uuid).
    ``total_bytes=None`` сохраняет прежний totalGB панели (обычные серверы).
    """
    merged = dict(existing)
    merged["email"] = email
    merged["subId"] = sub_id
    merged["enable"] = enable
    merged["expiryTime"] = expiry_ms
    if total_bytes is not None:
        merged["totalGB"] = total_bytes
    if quota_policy:
        merged.update(_QUOTA_RESET_POLICY)
    if tg_id is not None:
        merged["tgId"] = tg_id
    if flow and not merged.get("flow"):
        merged["flow"] = flow
    return sanitize_client_for_api(merged)


_CLIENT_API_FIELDS = frozenset(
    {
        "id",
        "email",
        "password",
        "auth",
        "subId",
        "enable",
        "expiryTime",
        "limitIp",
        "totalGB",
        "tgId",
        "reset",
        "flow",
        "method", "security", "limitHwid", "group", "comment", "resetDay",
        "resetWeekday", "resetMax", "trafficReset", "trafficResetDay", "reverse",
        "privateKey", "publicKey", "allowedIPs", "preSharedKey", "keepAlive",
        "forwardedPorts", "secret", "adTag",
    }
)


def _client_uuid_for_api(body: dict[str, Any]) -> str | None:
    """UUID vless/vmess для поля ``id`` в clients/update (строка, не DB-ключ)."""
    uuid_val = body.get("uuid")
    if isinstance(uuid_val, str) and uuid_val and not _looks_like_db_id(uuid_val):
        return uuid_val
    id_val = body.get("id")
    if isinstance(id_val, str) and id_val and not _looks_like_db_id(id_val):
        return id_val
    return None


def sanitize_client_for_api(body: dict[str, Any]) -> dict[str, Any]:
    """Оставляет только поля model.Client и исправляет ``id`` (строковый UUID).

    Ответ ``clients/get`` может содержать числовой DB-ключ в ``id``, метаданные
    ``createdAt``/``updatedAt`` и т.п. — их нельзя отправлять в clients/update.
    """
    result: dict[str, Any] = {
        key: body[key] for key in _CLIENT_API_FIELDS if key in body
    }
    # ClientRecord stores tunnel IPs as text; model.Client expects an array.
    ips = result.get("allowedIPs")
    if isinstance(ips, str):
        if ips.strip().startswith("["):
            decoded = json.loads(ips)
            if not isinstance(decoded, list) or not all(isinstance(ip, str) for ip in decoded):
                raise ValueError("Invalid stored allowedIPs")
            result["allowedIPs"] = decoded
        else:
            result["allowedIPs"] = [ip.strip() for ip in ips.split(",") if ip.strip()]
    reverse = result.get("reverse")
    if isinstance(reverse, str):
        result["reverse"] = json.loads(reverse) if reverse.strip() else None
    uuid_str = _client_uuid_for_api(body)
    if uuid_str:
        result["id"] = uuid_str
    elif "id" in result:
        id_val = result["id"]
        if isinstance(id_val, int) or (
            isinstance(id_val, str) and _looks_like_db_id(id_val)
        ):
            del result["id"]
    return result


def client_identifier(protocol: Protocol, *, client_uuid: str, email: str) -> str:
    """Идентификатор клиента в пути updateClient/{id}.

    Для vless/vmess — это UUID клиента, для остальных — email.
    """
    if protocol in (Protocol.VLESS, Protocol.VMESS):
        return client_uuid
    return email

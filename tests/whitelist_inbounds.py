"""Inbound'ы 3x-ui (`/panel/api/inbounds/list`) для тестов сервера услуги."""
from __future__ import annotations

import base64
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


_PRIVATE_KEY = X25519PrivateKey.generate()
PRIVATE = _b64(_PRIVATE_KEY.private_bytes(
    serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
    serialization.NoEncryption(),
))
PUBLIC = _b64(_PRIVATE_KEY.public_key().public_bytes(
    serialization.Encoding.Raw, serialization.PublicFormat.Raw,
))
ALIEN_UUID = "0b7f3a9e-1111-4c2d-9e8f-aaaaaaaaaaaa"
ALIEN_SUB = "aliensubid000001"


def vless_reality(
    inbound_id: int = 12,
    *,
    network: str = "tcp",
    public_key: str | None = PUBLIC,
    private_key: str | None = PRIVATE,
    server_names: list[str] | None = None,
    short_ids: list[str] | None = None,
    decryption: str = "none",
    header: str = "none",
    clients: list[dict] | None = None,
    remark: str = "Обход белых списков",
) -> dict:
    reality: dict = {
        "show": False, "xver": 0, "target": "files.example:443",
        "serverNames": ["files.example"] if server_names is None else server_names,
        "shortIds": ["a1b2c3d4"] if short_ids is None else short_ids,
        "settings": {"fingerprint": "chrome", "spiderX": "/"},
    }
    if private_key is not None:
        reality["privateKey"] = private_key
    if public_key is not None:
        reality["settings"]["publicKey"] = public_key
    stream: dict = {"network": network, "security": "reality", "realitySettings": reality}
    if network in ("tcp", "raw"):
        stream[f"{network}Settings"] = {"header": {"type": header}}
    elif network == "xhttp":
        stream["xhttpSettings"] = {"path": "/wl", "mode": "auto", "host": ""}
    elif network == "grpc":
        stream["grpcSettings"] = {"serviceName": "wl"}
    return {
        "id": inbound_id, "protocol": "vless", "enable": True, "remark": remark,
        "port": 443,
        "settings": json.dumps({"clients": clients or [], "decryption": decryption,
                                "fallbacks": []}),
        "streamSettings": json.dumps(stream),
    }


def plain_vless(inbound_id: int = 12, *, security: str = "none") -> dict:
    stream: dict = {"network": "tcp", "security": security,
                    "tcpSettings": {"header": {"type": "none"}}}
    if security == "tls":
        stream["tlsSettings"] = {"serverName": "wl.example"}
    return {
        "id": inbound_id, "protocol": "vless", "enable": True, "remark": "plain",
        "port": 443, "settings": json.dumps({"clients": [], "decryption": "none"}),
        "streamSettings": json.dumps(stream),
    }


def hysteria(inbound_id: int = 14, *, security: str = "tls") -> dict:
    stream: dict = {"network": "hysteria", "security": security}
    if security == "tls":
        stream["tlsSettings"] = {"serverName": "wl.example"}
    return {
        "id": inbound_id, "protocol": "hysteria", "enable": True, "remark": "hy",
        "port": 8443, "settings": json.dumps({"clients": [], "version": 2}),
        "streamSettings": json.dumps(stream),
    }


def other(protocol: str, inbound_id: int = 15) -> dict:
    return {
        "id": inbound_id, "protocol": protocol, "enable": True, "remark": protocol,
        "port": 443, "settings": json.dumps({"clients": []}),
        "streamSettings": json.dumps({"network": "tcp", "security": "tls",
                                      "tlsSettings": {"serverName": "wl.example"}}),
    }

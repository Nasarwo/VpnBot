from __future__ import annotations

import pytest

from app.db.enums import Protocol
from app.services.xui_payloads import (
    UnsupportedProtocolError,
    build_client_object,
    client_identifier,
)

COMMON = {
    "client_uuid": "uuid-123",
    "password": "pass-123",
    "email": "PUB-7",
    "sub_id": "PUB",
    "expiry_ms": 1_700_000_000_000,
}


def test_vless_has_id_and_flow():
    obj = build_client_object(Protocol.VLESS, flow="xtls-rprx-vision", **COMMON)
    assert obj["id"] == "uuid-123"
    assert obj["flow"] == "xtls-rprx-vision"
    assert obj["subId"] == "PUB"
    assert obj["expiryTime"] == 1_700_000_000_000
    assert obj["enable"] is True


def test_vmess_has_id_no_flow():
    obj = build_client_object(Protocol.VMESS, **COMMON)
    assert obj["id"] == "uuid-123"
    assert "flow" not in obj
    assert "security" not in obj


def test_trojan_uses_password():
    obj = build_client_object(Protocol.TROJAN, **COMMON)
    assert obj["password"] == "pass-123"
    assert "id" not in obj


def test_shadowsocks_includes_method():
    obj = build_client_object(Protocol.SHADOWSOCKS, method="aes-256-gcm", **COMMON)
    assert obj["password"] == "pass-123"
    assert obj["method"] == "aes-256-gcm"


def test_hysteria2_uses_auth():
    obj = build_client_object(Protocol.HYSTERIA2, **COMMON)
    assert obj["auth"] == "pass-123"
    assert "password" not in obj


def test_trojan_omits_empty_flow():
    obj = build_client_object(Protocol.TROJAN, **COMMON)
    assert "flow" not in obj


def test_identifier_by_protocol():
    assert (
        client_identifier(Protocol.VLESS, client_uuid="u", email="e") == "u"
    )
    assert (
        client_identifier(Protocol.TROJAN, client_uuid="u", email="e") == "e"
    )


def test_unsupported_protocol():
    class Fake:
        pass

    with pytest.raises(UnsupportedProtocolError):
        build_client_object(Fake(), **COMMON)  # type: ignore[arg-type]

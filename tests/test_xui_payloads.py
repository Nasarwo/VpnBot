from __future__ import annotations

import pytest

from app.db.enums import Protocol
from app.services.xui_payloads import (
    UnsupportedProtocolError,
    build_client_object,
    client_identifier,
    merge_client_record_for_update,
    pick_panel_client_secret,
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


def test_pick_panel_client_secret_prefers_uuid_over_numeric_id():
    assert pick_panel_client_secret({"uuid": "550e8400-e29b-41d4-a716-446655440000"}) == (
        "550e8400-e29b-41d4-a716-446655440000"
    )
    assert pick_panel_client_secret({"id": "42", "password": "trojan-key"}) == "trojan-key"
    assert pick_panel_client_secret({"id": "real-uuid-here", "auth": "hy-auth"}) == (
        "real-uuid-here"
    )


def test_merge_client_record_preserves_secrets():
    existing = {
        "id": 42,
        "uuid": "vless-uuid",
        "password": "trojan-pass",
        "auth": "hysteria-auth",
        "email": "dimatest",
        "subId": "test",
        "expiryTime": 0,
        "enable": True,
        "createdAt": 123456,
        "comment": "legacy",
    }
    merged = merge_client_record_for_update(
        existing,
        email="dimatest",
        sub_id="test",
        expiry_ms=1_900_000_000_000,
    )
    assert merged["id"] == "vless-uuid"
    assert merged["password"] == "trojan-pass"
    assert merged["auth"] == "hysteria-auth"
    assert merged["expiryTime"] == 1_900_000_000_000
    assert merged["enable"] is True
    assert "createdAt" not in merged
    assert "comment" not in merged


def test_sanitize_client_for_api():
    from app.services.xui_payloads import sanitize_client_for_api

    body = {
        "id": 99,
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "email": "asya",
        "subId": "asya",
        "enable": True,
        "updatedAt": 1,
    }
    clean = sanitize_client_for_api(body)
    assert clean["id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert "updatedAt" not in clean

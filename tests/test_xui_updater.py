from __future__ import annotations

import json

from pytest_httpx import HTTPXMock

from app.db.enums import Protocol
from app.db.models import Server
from app.services.panel_updater import ProvisionInbound, ServerProvision
from app.services.xui_updater import XuiPanelUpdater

BASE = "http://panel.local:2053"


def _server() -> Server:
    srv = Server(
        name="se",
        country="SE",
        panel_url=BASE,
        username="admin",
        password="secret",
        enabled=True,
    )
    srv.id = 1
    return srv


def _spec() -> ServerProvision:
    return ServerProvision(
        email="PUB123",
        sub_id="PUB123",
        client_uuid="uuid-1",
        password="pass-1",
        inbounds=[
            ProvisionInbound(10, Protocol.VLESS, flow="xtls-rprx-vision"),
            ProvisionInbound(11, Protocol.TROJAN),
        ],
    )


def _mock_auth(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/csrf-token",
        json={"success": True, "obj": "csrf-1"},
        is_reusable=True,
    )
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )


async def test_provision_server_new_api_creates(httpx_mock: HTTPXMock):
    _mock_auth(httpx_mock)
    # Capability probe -> new API доступен.
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/clients/get/__caps_probe__",
        json={"success": False},
    )
    # Клиента ещё нет.
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/clients/get/PUB123",
        json={"success": False, "msg": "not found"},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/panel/api/clients/add",
        json={"success": True},
    )

    await XuiPanelUpdater().provision_server(_server(), _spec(), 1_700_000_000_000)

    add_req = [r for r in httpx_mock.get_requests() if r.url.path.endswith("/clients/add")][0]
    body = json.loads(add_req.content)
    assert set(body["inboundIds"]) == {10, 11}
    assert body["client"]["email"] == "PUB123"
    assert body["client"]["subId"] == "PUB123"
    assert body["client"]["expiryTime"] == 1_700_000_000_000
    assert body["client"]["flow"] == "xtls-rprx-vision"


async def test_provision_server_new_api_updates_existing(httpx_mock: HTTPXMock):
    _mock_auth(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/clients/get/__caps_probe__",
        json={"success": False},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/clients/get/PUB123",
        json={
            "success": True,
            "obj": {
                "client": {
                    "id": 42,
                    "uuid": "uuid-1",
                    "email": "PUB123",
                    "subId": "PUB123",
                    "password": "trojan-pass",
                    "auth": "hysteria-auth",
                    "expiryTime": 1,
                    "enable": False,
                    "createdAt": 999,
                },
                "inboundIds": [10, 11],
            },
        },
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/panel/api/clients/update/PUB123?inboundIds=10,11",
        json={"success": True},
    )

    await XuiPanelUpdater().provision_server(_server(), _spec(), 1_800_000_000_000)

    upd_req = [
        r for r in httpx_mock.get_requests()
        if r.url.path.endswith("/clients/update/PUB123")
    ][0]
    body = json.loads(upd_req.content)
    assert body["id"] == "uuid-1"
    assert body["password"] == "trojan-pass"
    assert body["auth"] == "hysteria-auth"
    assert body["subId"] == "PUB123"
    assert body["expiryTime"] == 1_800_000_000_000
    assert body["enable"] is True
    assert "createdAt" not in body


async def test_provision_server_finds_client_by_sub_id(httpx_mock: HTTPXMock):
    _mock_auth(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/clients/get/__caps_probe__",
        json={"success": False},
        is_reusable=True,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/clients/get/asya2",
        json={"success": False, "msg": "not found"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/clients/list",
        json={
            "success": True,
            "obj": [
                {
                    "client": {
                        "email": "asya",
                        "subId": "PUB123",
                        "id": "uuid-asya",
                    },
                    "inboundIds": [10],
                }
            ],
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/clients/get/asya",
        json={
            "success": True,
            "obj": {
                "client": {
                    "id": "uuid-asya",
                    "email": "asya",
                    "subId": "PUB123",
                    "expiryTime": 0,
                    "enable": True,
                },
                "inboundIds": [10],
            },
        },
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/panel/api/clients/update/asya?inboundIds=10,11",
        json={"success": True},
    )

    spec = ServerProvision(
        email="asya2",
        sub_id="PUB123",
        client_uuid="uuid-asya",
        password="pass",
        inbounds=_spec().inbounds,
    )
    await XuiPanelUpdater().provision_server(_server(), spec, 0)

    upd = [
        r for r in httpx_mock.get_requests()
        if "/clients/update/asya" in r.url.path
    ]
    assert len(upd) == 1
    add = [r for r in httpx_mock.get_requests() if r.url.path.endswith("/clients/add")]
    assert not add

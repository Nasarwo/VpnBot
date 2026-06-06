from __future__ import annotations

import json

import httpx
import pytest
from pytest_httpx import HTTPXMock

from app.services.xui_client import XuiAuthError, XuiClient, XuiError

BASE = "http://panel.local:2053"

INBOUND_SETTINGS = json.dumps(
    {
        "clients": [
            {
                "id": "uuid-1",
                "email": "test@local",
                "expiryTime": 0,
                "enable": True,
            }
        ]
    }
)


def _client() -> XuiClient:
    return XuiClient(
        base_url=BASE, username="admin", password="secret", max_retries=3
    )


async def test_login_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    async with _client() as client:
        await client.login()


async def test_login_failure_raises(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": False, "msg": "bad"}
    )
    async with _client() as client:
        with pytest.raises(XuiAuthError):
            await client.login()


async def test_update_client_expiry_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/inbounds/get/1",
        json={"success": True, "obj": {"settings": INBOUND_SETTINGS}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/panel/api/inbounds/updateClient/uuid-1",
        json={"success": True},
    )

    async with _client() as client:
        await client.update_client_expiry(
            inbound_id=1,
            client_uuid="uuid-1",
            email="test@local",
            expiry_ms=1_700_000_000_000,
        )

    update_req = [
        r for r in httpx_mock.get_requests()
        if r.url.path.endswith("/updateClient/uuid-1")
    ][0]
    body = json.loads(update_req.content)
    sent_client = json.loads(body["settings"])["clients"][0]
    assert sent_client["expiryTime"] == 1_700_000_000_000
    assert body["id"] == 1


async def test_update_client_not_found(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/inbounds/get/1",
        json={"success": True, "obj": {"settings": json.dumps({"clients": []})}},
    )
    async with _client() as client:
        with pytest.raises(XuiError):
            await client.update_client_expiry(
                inbound_id=1,
                client_uuid="missing",
                email="missing@local",
                expiry_ms=1,
            )


async def test_retry_on_transient_error_then_success(httpx_mock: HTTPXMock):
    httpx_mock.add_exception(httpx.ConnectError("boom"), url=f"{BASE}/login")
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    async with _client() as client:
        await client.login()
    assert len([r for r in httpx_mock.get_requests() if r.url.path == "/login"]) == 2


async def test_retry_exhausted_raises(httpx_mock: HTTPXMock):
    httpx_mock.add_exception(httpx.ConnectError("boom"), url=f"{BASE}/login")
    httpx_mock.add_exception(httpx.ConnectError("boom"), url=f"{BASE}/login")
    httpx_mock.add_exception(httpx.ConnectError("boom"), url=f"{BASE}/login")
    async with _client() as client:
        with pytest.raises(XuiError):
            await client.login()

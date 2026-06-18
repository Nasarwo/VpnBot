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


def _mock_csrf(httpx_mock: HTTPXMock) -> None:
    """Регистрирует ответ /csrf-token (3x-ui 3.2.x запрашивает его перед login)."""
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/csrf-token",
        json={"success": True, "obj": "csrf-token-abc"},
        is_reusable=True,
    )


async def test_login_success(httpx_mock: HTTPXMock):
    _mock_csrf(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    async with _client() as client:
        await client.login()


async def test_login_failure_raises(httpx_mock: HTTPXMock):
    _mock_csrf(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": False, "msg": "bad"}
    )
    async with _client() as client:
        with pytest.raises(XuiAuthError):
            await client.login()


async def test_login_sends_csrf_header(httpx_mock: HTTPXMock):
    _mock_csrf(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    async with _client() as client:
        await client.login()
    login_req = [r for r in httpx_mock.get_requests() if r.url.path == "/login"][0]
    assert login_req.headers.get("X-CSRF-Token") == "csrf-token-abc"


async def test_update_client_expiry_success(httpx_mock: HTTPXMock):
    _mock_csrf(httpx_mock)
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
    _mock_csrf(httpx_mock)
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
    _mock_csrf(httpx_mock)
    httpx_mock.add_exception(httpx.ConnectError("boom"), url=f"{BASE}/login")
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    async with _client() as client:
        await client.login()
    assert len([r for r in httpx_mock.get_requests() if r.url.path == "/login"]) == 2


async def test_retry_exhausted_raises(httpx_mock: HTTPXMock):
    _mock_csrf(httpx_mock)
    httpx_mock.add_exception(httpx.ConnectError("boom"), url=f"{BASE}/login")
    httpx_mock.add_exception(httpx.ConnectError("boom"), url=f"{BASE}/login")
    httpx_mock.add_exception(httpx.ConnectError("boom"), url=f"{BASE}/login")
    async with _client() as client:
        with pytest.raises(XuiError):
            await client.login()


async def test_relogin_on_expired_session(httpx_mock: HTTPXMock):
    # Первый login, затем API-запрос отдаёт 403 (сессия истекла),
    # выполняется повторный login и повтор запроса.
    _mock_csrf(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/inbounds/list", status_code=403
    )
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/inbounds/list",
        json={"success": True, "obj": []},
    )
    async with _client() as client:
        inbounds = await client.list_inbounds()
    assert inbounds == []
    logins = [r for r in httpx_mock.get_requests() if r.url.path == "/login"]
    assert len(logins) == 2


async def test_no_retry_on_client_error(httpx_mock: HTTPXMock):
    # 404 не должен ретраиться: один запрос get + один (после неудачи) — нет.
    _mock_csrf(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/inbounds/get/9",
        status_code=404,
        json={"success": False, "msg": "not found"},
    )
    async with _client() as client:
        with pytest.raises(XuiError):
            await client.get_inbound(9)
    gets = [
        r for r in httpx_mock.get_requests() if r.url.path.endswith("/get/9")
    ]
    assert len(gets) == 1


async def test_find_client_by_sub_id(httpx_mock: HTTPXMock):
    settings = json.dumps(
        {"clients": [{"id": "u-2", "email": "e@local", "subId": "sub-xyz"}]}
    )
    _mock_csrf(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/inbounds/get/1",
        json={"success": True, "obj": {"settings": settings}},
    )
    async with _client() as client:
        found = await client.find_client(1, sub_id="sub-xyz")
    assert found is not None
    assert found["id"] == "u-2"


async def test_set_client_ip_limit_preserves_fields(httpx_mock: HTTPXMock):
    settings = json.dumps(
        {
            "clients": [
                {
                    "id": "u-3",
                    "email": "e3@local",
                    "expiryTime": 123,
                    "totalGB": 999,
                    "subId": "s3",
                }
            ]
        }
    )
    _mock_csrf(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/inbounds/get/1",
        json={"success": True, "obj": {"settings": settings}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/panel/api/inbounds/updateClient/u-3",
        json={"success": True},
    )
    async with _client() as client:
        await client.set_client_ip_limit(1, 2, client_uuid="u-3")
    req = [
        r for r in httpx_mock.get_requests()
        if r.url.path.endswith("/updateClient/u-3")
    ][0]
    sent = json.loads(json.loads(req.content)["settings"])["clients"][0]
    # Менялся только limitIp, остальные поля сохранены.
    assert sent["limitIp"] == 2
    assert sent["expiryTime"] == 123
    assert sent["totalGB"] == 999
    assert sent["subId"] == "s3"


async def test_get_client_traffic(httpx_mock: HTTPXMock):
    _mock_csrf(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/inbounds/getClientTraffics/e%40local",
        json={"success": True, "obj": {"email": "e@local", "up": 10, "down": 20}},
    )
    async with _client() as client:
        traffic = await client.get_client_traffic("e@local")
    assert traffic == {"email": "e@local", "up": 10, "down": 20}


async def test_get_client_ips_quotes_email_path_segment(httpx_mock: HTTPXMock):
    _mock_csrf(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/clients/get/__caps_probe__",
        json={"success": False, "msg": "not found"},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/panel/api/clients/ips/e%40local%2Fwith-slash",
        json={"success": True, "obj": ["1.1.1.1"]},
    )
    async with _client() as client:
        assert await client.get_client_ips("e@local/with-slash") == ["1.1.1.1"]

    requested_urls = [str(r.url) for r in httpx_mock.get_requests()]
    assert f"{BASE}/panel/api/clients/ips/e%40local%2Fwith-slash" in requested_urls


async def test_del_client_quotes_identifier_path_segment(httpx_mock: HTTPXMock):
    _mock_csrf(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/panel/api/inbounds/7/delClient/e%40local%2Fwith-slash",
        json={"success": True},
    )

    async with _client() as client:
        await client.del_client(7, "e@local/with-slash")

    requested_urls = [str(r.url) for r in httpx_mock.get_requests()]
    assert f"{BASE}/panel/api/inbounds/7/delClient/e%40local%2Fwith-slash" in requested_urls


async def test_supports_clients_api_true(httpx_mock: HTTPXMock):
    _mock_csrf(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/clients/get/__caps_probe__",
        json={"success": False, "msg": "not found"},
    )
    async with _client() as client:
        assert await client.supports_clients_api() is True


async def test_supports_clients_api_false_on_404(httpx_mock: HTTPXMock):
    _mock_csrf(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/clients/get/__caps_probe__",
        status_code=404,
    )
    async with _client() as client:
        assert await client.supports_clients_api() is False


async def test_create_client_record(httpx_mock: HTTPXMock):
    _mock_csrf(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/panel/api/clients/add",
        json={"success": True},
    )
    async with _client() as client:
        await client.create_client_record(
            {"id": "u", "email": "PUB123", "subId": "PUB123"}, [10, 11]
        )
    req = [r for r in httpx_mock.get_requests() if r.url.path.endswith("/clients/add")][0]
    body = json.loads(req.content)
    assert body["inboundIds"] == [10, 11]
    assert body["client"]["email"] == "PUB123"
    assert req.headers.get("X-CSRF-Token") == "csrf-token-abc"


async def test_get_client_record_found(httpx_mock: HTTPXMock):
    _mock_csrf(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login", json={"success": True}
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/clients/get/PUB123",
        json={
            "success": True,
            "obj": {"client": {"email": "PUB123", "id": "u"}, "inboundIds": [10]},
        },
    )
    async with _client() as client:
        rec = await client.get_client_record("PUB123")
    assert rec is not None
    assert rec["client"]["id"] == "u"
    assert rec["inboundIds"] == [10]


async def test_bearer_token_skips_login_and_csrf(httpx_mock: HTTPXMock):
    # С api_token не должно быть ни /login, ни /csrf-token — только Bearer.
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/panel/api/inbounds/list",
        json={"success": True, "obj": []},
    )
    client = XuiClient(
        base_url=BASE,
        username="admin",
        password="secret",
        api_token="secret-bearer",
    )
    async with client:
        await client.list_inbounds()
    paths = [r.url.path for r in httpx_mock.get_requests()]
    assert "/login" not in paths
    assert "/csrf-token" not in paths
    list_req = [
        r for r in httpx_mock.get_requests() if r.url.path.endswith("/inbounds/list")
    ][0]
    assert list_req.headers.get("Authorization") == "Bearer secret-bearer"

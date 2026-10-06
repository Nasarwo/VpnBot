"""HTTP-контракт клиента с квотой на 3x-ui (clients API >= 3.2).

Сверено с MHSanaei/3x-ui: ClientController (/panel/api/clients/*), model.Client
и InboundService.UpdateClientStat — totalGB хранится в байтах, client_traffics
.total = totalGB, исчерпание: total > 0 и up + down >= total.
"""
from __future__ import annotations

import json

import pytest
from pytest_httpx import HTTPXMock

from app.db.enums import Protocol
from app.services.panel_updater import (
    PanelUpdateError,
    ProvisionInbound,
    QuotaTarget,
    ServerProvision,
)
from app.services.xui_client import XuiClient, XuiError
from app.services.xui_updater import XuiPanelUpdater
from tests.test_xui_updater import BASE, _server

GIB = 1024**3


def _spec() -> ServerProvision:
    return ServerProvision(
        email="PUB123",
        sub_id="PUB123",
        client_uuid="uuid-1",
        password="uuid-1",
        telegram_id=1891806016,
        inbounds=[ProvisionInbound(7, Protocol.VLESS)],
    )


def _auth(httpx_mock: HTTPXMock, inbound_ids=(7,), inbounds: list | None = None) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/csrf-token",
        json={"success": True, "obj": "csrf"}, is_reusable=True,
    )
    httpx_mock.add_response(method="POST", url=f"{BASE}/login", json={"success": True})
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/inbounds/list",
        json={"success": True, "obj": inbounds if inbounds is not None else [
            {"id": i, "protocol": "vless", "enable": True} for i in inbound_ids
        ]},
        is_optional=True,
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/__caps_probe__",
        json={"success": False, "msg": "not found"},
    )


def _record(total, enable, expiry, inbounds=(7,), **extra):
    client = {
        "id": 42, "uuid": "uuid-1", "email": "PUB123", "subId": "PUB123",
        "password": "trojan-pass", "auth": "hy-auth", "flow": "xtls-rprx-vision",
        "tgId": 1891806016, "totalGB": total, "expiryTime": expiry, "enable": enable,
        "limitIp": 2, "limitHwid": 3, "comment": "vip", "group": "g1",
        "reset": 30, "resetDay": 5, "trafficReset": "monthly", "createdAt": 1,
        **extra,
    }
    return {"success": True, "obj": {"client": client, "inboundIds": list(inbounds)}}


def _traffic(up, down, row_id=900, last_online=0):
    return {"success": True, "obj": {"id": row_id, "email": "PUB123", "up": up,
                                     "down": down, "total": 0, "enable": True,
                                     "lastOnline": last_online}}


def _body(httpx_mock: HTTPXMock, suffix: str) -> dict:
    request = [r for r in httpx_mock.get_requests() if r.url.path.endswith(suffix)][0]
    return json.loads(request.content)


def _inbound(inbound_id: int, *clients: tuple[str, str]) -> dict:
    """Ответ ``inbounds/get/{id}``: flow клиентов в settings.clients[]."""
    settings = {"clients": [{"email": email, "flow": flow} for email, flow in clients],
                "decryption": "none"}
    return {"success": True, "obj": {"id": inbound_id, "protocol": "vless", "enable": True,
                                     "settings": json.dumps(settings)}}


async def test_create_sends_bytes_and_disables_panel_auto_reset(httpx_mock: HTTPXMock):
    _auth(httpx_mock)
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/PUB123",
        json={"success": False, "msg": "record not found"},
    )
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/panel/api/clients/add", json={"success": True}
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/PUB123",
        json=_record(10 * GIB, True, 1_800_000_000_000, reset=0, resetDay=0,
                     trafficReset="never"),
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/traffic/PUB123", json=_traffic(0, 0)
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/inbounds/get/7", json=_inbound(7, ("PUB123", ""))
    )
    target = QuotaTarget(total_bytes=10 * GIB, enable=True, expiry_ms=1_800_000_000_000)
    state = await XuiPanelUpdater().apply_quota_client(_server(), _spec(), target)
    body = _body(httpx_mock, "/clients/add")
    client = body["client"]
    assert body["inboundIds"] == [7]
    assert client["totalGB"] == 10 * GIB == 10737418240
    assert client["enable"] is True and client["expiryTime"] == 1_800_000_000_000
    assert client["tgId"] == 1891806016 and client["subId"] == "PUB123"
    assert client["reset"] == 0 and client["trafficReset"] == "never"
    assert state.used_bytes == 0 and state.traffic_row_id == 900
    # Клиент создан услугой: привязка к цели — её (чтение перед созданием).
    assert state.attached_inbound_ids == [7] and state.inbound_flows == {7: ""}


async def test_update_preserves_identity_and_fields_and_attaches_missing_inbound(
    httpx_mock: HTTPXMock,
):
    """attach цели → update прочих привязок с их flow → update цели с её flow → чтение."""
    _auth(httpx_mock, inbound_ids=(7, 9))
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/PUB123",
        json=_record(5 * GIB, True, 1, inbounds=(9,)),
    )
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/panel/api/clients/PUB123/attach", json={"success": True}
    )
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/panel/api/clients/update/PUB123?inboundIds=9",
        json={"success": True},
    )
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/panel/api/clients/update/PUB123?inboundIds=7",
        json={"success": True},
    )
    exhausted = 3 * GIB  # исчерпано: конечный лимит, клиент выключен
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/PUB123",
        json=_record(exhausted, False, 1_900_000_000_000, inbounds=(7, 9)),
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/traffic/PUB123",
        json=_traffic(GIB, 2 * GIB),
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/inbounds/get/7", json=_inbound(7, ("PUB123", ""))
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/inbounds/get/9",
        json=_inbound(9, ("PUB123", "xtls-rprx-vision")),
    )
    target = QuotaTarget(total_bytes=exhausted, enable=False, expiry_ms=1_900_000_000_000)
    state = await XuiPanelUpdater().apply_quota_client(_server(), _spec(), target)
    paths = [
        (r.method, r.url.path, r.url.query.decode()) for r in httpx_mock.get_requests()
        if r.method == "POST" and "/clients/" in r.url.path
    ]
    assert paths == [
        ("POST", "/panel/api/clients/PUB123/attach", ""),
        ("POST", "/panel/api/clients/update/PUB123", "inboundIds=9"),
        ("POST", "/panel/api/clients/update/PUB123", "inboundIds=7"),
    ]
    assert _body(httpx_mock, "/PUB123/attach") == {"inboundIds": [7]}
    updates = [
        json.loads(r.content) for r in httpx_mock.get_requests()
        if r.url.path.endswith("/clients/update/PUB123")
    ]
    for body in updates:
        assert body["totalGB"] == exhausted != 0
        assert body["enable"] is False
        assert body["id"] == "uuid-1"  # UUID, не числовой ключ записи
        assert body["password"] == "trojan-pass" and body["auth"] == "hy-auth"
        assert body["tgId"] == 1891806016 and body["subId"] == "PUB123"
        assert (body["limitIp"], body["limitHwid"], body["comment"], body["group"]) == (
            2, 3, "vip", "g1"
        )
        assert body["reset"] == 0 and body["resetDay"] == 0 and body["trafficReset"] == "never"
        assert "createdAt" not in body and "uuid" not in body
    # Прочая привязка сохраняет flow записи; у цели flow явный (не задан — очищается).
    assert updates[0]["flow"] == "xtls-rprx-vision"
    assert updates[1]["flow"] == ""
    assert state.used_bytes == 3 * GIB and state.depleted
    assert state.attached_inbound_ids == [7]
    assert state.inbound_flows == {7: "", 9: "xtls-rprx-vision"}


async def test_panel_that_did_not_store_quota_is_not_reported_as_applied(
    httpx_mock: HTTPXMock,
):
    _auth(httpx_mock)
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/PUB123",
        json=_record(0, True, 1),
    )
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/panel/api/clients/update/PUB123?inboundIds=7",
        json={"success": True},
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/PUB123",
        json=_record(0, True, 1),  # панель «успешно» проигнорировала квоту
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/traffic/PUB123", json=_traffic(0, 0)
    )
    target = QuotaTarget(total_bytes=10 * GIB, enable=True, expiry_ms=1)
    with pytest.raises(PanelUpdateError, match="totalGB=0"):
        await XuiPanelUpdater().apply_quota_client(_server(), _spec(), target)


async def test_read_quota_sums_upload_and_download(httpx_mock: HTTPXMock):
    _auth(httpx_mock)
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/PUB123",
        json=_record(20 * GIB, True, 1),
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/traffic/PUB123",
        json=_traffic(3 * GIB, 4 * GIB, row_id=55, last_online=1_759_600_000_000),
    )
    state = await XuiPanelUpdater().read_quota_client(_server(), "PUB123")
    assert state.used_bytes == 7 * GIB and state.traffic_row_id == 55
    assert state.total_bytes == 20 * GIB
    # client_traffics.last_online — граница последнего прироста трафика.
    assert state.last_online_ms == 1_759_600_000_000


async def test_read_quota_without_last_online_is_unknown(httpx_mock: HTTPXMock):
    _auth(httpx_mock)
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/PUB123",
        json=_record(20 * GIB, True, 1),
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/traffic/PUB123",
        json=_traffic(GIB, 0, last_online=0),
    )
    state = await XuiPanelUpdater().read_quota_client(_server(), "PUB123")
    assert state.used_bytes == GIB and state.last_online_ms is None


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (500, {"success": False}),
        (200, {"success": False, "msg": "trafficGetError"}),
        (200, {"success": True, "obj": {"up": "1", "down": 0}}),
        (200, {"success": True, "obj": {"up": -1, "down": 0}}),
    ],
)
async def test_usage_read_failure_is_not_zero_usage(httpx_mock: HTTPXMock, status, body):
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/traffic/PUB123",
        status_code=status, json=body,
    )
    client = XuiClient(BASE, "u", "p", max_retries=1)
    client._logged_in = True
    with pytest.raises(XuiError):
        await client.get_client_usage("PUB123")
    await client.close()


async def test_missing_traffic_row_is_unknown_not_zero(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/traffic/PUB123",
        json={"success": True, "obj": None},
    )
    client = XuiClient(BASE, "u", "p")
    client._logged_in = True
    assert await client.get_client_usage("PUB123") is None
    await client.close()


async def test_legacy_panel_is_rejected_for_quota(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/csrf-token", status_code=404, is_reusable=True,
    )
    httpx_mock.add_response(method="POST", url=f"{BASE}/login", json={"success": True})
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/__caps_probe__", status_code=404,
    )
    with pytest.raises(PanelUpdateError, match="clients API"):
        await XuiPanelUpdater().read_quota_client(_server(), "PUB123")


# --- Перенос: attach/detach и flow (3x-ui 3.2–3.9, ClientController) ---------------------
#
# POST /panel/api/clients/{email}/attach и /detach принимают {"inboundIds": [...]}
# (attachDetachBody); detach в 3.2–3.9 вызывает DetachByEmailMany: непривязанные id
# пропускаются, строка client_traffics сохраняется (keepTraffic=true).


def _spec_flow(flow):
    spec = _spec()
    spec.inbounds = [ProvisionInbound(7, Protocol.VLESS, flow=flow)]
    return spec


async def test_detach_sends_only_attached_ids_and_confirms_by_read(httpx_mock: HTTPXMock):
    _auth(httpx_mock)
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/PUB123",
        json=_record(10 * GIB, True, 1, inbounds=(7, 8)),
    )
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/panel/api/clients/PUB123/detach", json={"success": True}
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/PUB123",
        json=_record(10 * GIB, True, 1, inbounds=(8,)),
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/traffic/PUB123",
        json=_traffic(GIB, GIB, row_id=900),
    )
    state = await XuiPanelUpdater().detach_quota_client(_server(), "PUB123", [7, 5])
    assert _body(httpx_mock, "/PUB123/detach") == {"inboundIds": [7]}  # 5 не привязан
    # Счётчик и его строка не меняются.
    assert state.inbound_ids == [8] and state.used_bytes == 2 * GIB
    assert state.traffic_row_id == 900


async def test_detach_without_attachment_sends_nothing(httpx_mock: HTTPXMock):
    _auth(httpx_mock)
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/PUB123",
        json=_record(10 * GIB, True, 1, inbounds=(8,)), is_reusable=True,
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/traffic/PUB123", json=_traffic(0, 0)
    )
    state = await XuiPanelUpdater().detach_quota_client(_server(), "PUB123", [7])
    assert state.inbound_ids == [8]
    assert not [r for r in httpx_mock.get_requests() if r.url.path.endswith("/detach")]


@pytest.mark.parametrize(
    ("detach", "after", "match"),
    [
        ({"success": False, "msg": "inbound 7: record not found"}, None, "снятие привязки"),
        ({"success": True}, (7, 8), "остались inbound \\[7\\]"),
    ],
)
async def test_unconfirmed_detach_is_an_error(httpx_mock: HTTPXMock, detach, after, match):
    _auth(httpx_mock)
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/PUB123",
        json=_record(10 * GIB, True, 1, inbounds=(7, 8)),
    )
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/panel/api/clients/PUB123/detach", json=detach
    )
    if after is not None:
        httpx_mock.add_response(
            method="GET", url=f"{BASE}/panel/api/clients/get/PUB123",
            json=_record(10 * GIB, True, 1, inbounds=after),
        )
        httpx_mock.add_response(
            method="GET", url=f"{BASE}/panel/api/clients/traffic/PUB123", json=_traffic(0, 0)
        )
    with pytest.raises(PanelUpdateError, match=match):
        await XuiPanelUpdater().detach_quota_client(_server(), "PUB123", [7])


def _apply_existing(httpx_mock: HTTPXMock, *, record_flow: str, panel_flow: str | None):
    """Клиент уже на цели 7 с flow записи ``record_flow``; ответ inbounds/get/7."""
    _auth(httpx_mock)
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/PUB123",
        json=_record(5 * GIB, True, 1, flow=record_flow), is_reusable=True,
    )
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/panel/api/clients/update/PUB123?inboundIds=7",
        json={"success": True},
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/traffic/PUB123", json=_traffic(0, 0)
    )
    clients = () if panel_flow is None else (("PUB123", panel_flow),)
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/inbounds/get/7", json=_inbound(7, *clients)
    )


@pytest.mark.parametrize(
    ("record_flow", "target_flow", "sent"),
    [
        ("xtls-rprx-vision", None, ""),  # flow цели снят — очищается, а не сохраняется
        ("", "xtls-rprx-vision", "xtls-rprx-vision"),
        ("xtls-rprx-vision", "xtls-rprx-vision", "xtls-rprx-vision"),
    ],
)
async def test_target_flow_is_explicit_and_verified(
    httpx_mock: HTTPXMock, record_flow, target_flow, sent
):
    _apply_existing(httpx_mock, record_flow=record_flow, panel_flow=sent)
    target = QuotaTarget(total_bytes=5 * GIB, enable=True, expiry_ms=1)
    state = await XuiPanelUpdater().apply_quota_client(_server(), _spec_flow(target_flow), target)
    assert _body(httpx_mock, "/clients/update/PUB123")["flow"] == sent
    assert state.inbound_flows == {7: sent} and state.attached_inbound_ids == []


@pytest.mark.parametrize(
    ("panel_flow", "match"),
    [("xtls-rprx-vision", "flow в inbound 7=xtls-rprx-vision, ожидалось нет"),
     (None, "клиента нет в настройках inbound 7")],
)
async def test_unconfirmed_target_flow_is_not_applied(httpx_mock: HTTPXMock, panel_flow, match):
    _apply_existing(httpx_mock, record_flow="xtls-rprx-vision", panel_flow=panel_flow)
    target = QuotaTarget(total_bytes=5 * GIB, enable=True, expiry_ms=1)
    with pytest.raises(PanelUpdateError, match=match):
        await XuiPanelUpdater().apply_quota_client(_server(), _spec_flow(None), target)


async def test_record_level_flow_change_of_other_attachment_is_logged(
    httpx_mock: HTTPXMock, caplog
):
    """3.2.0 не знает фильтра inboundIds: flow чужой привязки меняется — это видно."""
    _auth(httpx_mock, inbound_ids=(5, 7))
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/PUB123",
        json=_record(5 * GIB, True, 1, inbounds=(5, 7)), is_reusable=True,
    )
    for inbound_id in (5, 7):
        httpx_mock.add_response(
            method="POST",
            url=f"{BASE}/panel/api/clients/update/PUB123?inboundIds={inbound_id}",
            json={"success": True},
        )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/traffic/PUB123", json=_traffic(0, 0)
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/inbounds/get/7", json=_inbound(7, ("PUB123", ""))
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/inbounds/get/5", json=_inbound(5, ("PUB123", ""))
    )
    target = QuotaTarget(total_bytes=5 * GIB, enable=True, expiry_ms=1)
    state = await XuiPanelUpdater().apply_quota_client(_server(), _spec_flow(None), target)
    # Прочая привязка получила свой flow (запись: vision) отдельным update до цели.
    bodies = [json.loads(r.content) for r in httpx_mock.get_requests()
              if r.url.path.endswith("/clients/update/PUB123")]
    assert [b["flow"] for b in bodies] == ["xtls-rprx-vision", ""]
    assert state.inbound_flows == {7: "", 5: ""}
    assert "flow привязки клиента PUB123 к inbound 5 изменился" in caplog.text


async def test_batch_read_reports_flow_of_each_attachment(httpx_mock: HTTPXMock):
    _auth(httpx_mock, inbounds=[
        _inbound(7, ("PUB123", "xtls-rprx-vision"), ("OTHER", ""))["obj"],
        _inbound(8)["obj"],
    ])
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/get/PUB123",
        json=_record(5 * GIB, True, 1, inbounds=(7, 8)),
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/panel/api/clients/traffic/PUB123", json=_traffic(1, 2)
    )
    result = await XuiPanelUpdater().read_quota_clients(_server(), ["PUB123"])
    state = result["PUB123"]
    # 8: клиент в записи привязан, но в настройках inbound'а его нет — flow неизвестен.
    assert state.inbound_ids == [7, 8] and state.inbound_flows == {7: "xtls-rprx-vision"}
    assert state.used_bytes == 3

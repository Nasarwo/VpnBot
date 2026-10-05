"""Совместимость целевого inbound услуги с форматом ссылок SubHub.

Импорт inbound не должен объявлять сервер готовым, если SubHub не сможет
построить для него рабочую ссылку (приёмка 5 октября 2026: простой VLESS
не попал в подписку, хотя сервер считался готовым).
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.bot import admin_handlers, keyboards
from app.bot.callbacks import WhitelistAdminCallback
from app.config import Settings
from app.db.enums import Protocol
from app.db.models import Server, ServerInbound, WhitelistLedger
from app.services import provisioning, whitelist
from app.services.panel_updater import MockPanelUpdater
from tests.test_whitelist import _Panel
from tests.test_whitelist_bot import FakeCallback, FakeMessage, FakeState
from tests.whitelist_inbounds import (
    ALIEN_SUB,
    ALIEN_UUID,
    PRIVATE,
    PUBLIC,
    hysteria,
    other,
    plain_vless,
    vless_reality,
)


async def _server(session) -> Server:
    server = Server(name="WL", panel_url="https://cc.example", username="a", password="b",
                    purpose="whitelist", enabled=True)
    session.add(server)
    await session.commit()
    return server


async def _sync(session, monkeypatch, server, inbounds):
    monkeypatch.setattr(provisioning, "XuiClient", lambda **_: _Panel(inbounds))
    result = await whitelist.sync_inventory(session, server)
    await session.commit()
    current = await whitelist.get_active_server(session)
    assert current is not None and current.id == server.id
    return result, current


def _assert_no_secrets(text: str) -> None:
    for secret in (PRIVATE, PUBLIC, ALIEN_UUID, ALIEN_SUB):
        assert secret not in text


# --- Регрессия: одна импортированная строка ещё не готовность ----------------------


@pytest.mark.parametrize(
    "raw, reason",
    [
        (plain_vless(), "REALITY"),
        ({"id": 12, "protocol": "vless", "enable": True}, "REALITY"),
        (plain_vless(security="tls"), "REALITY"),
        (other("trojan"), "trojan"),
        (other("vmess"), "vmess"),
        (other("shadowsocks"), "shadowsocks"),
    ],
)
async def test_single_unsupported_inbound_is_not_ready(session, monkeypatch, raw, reason):
    server = await _server(session)
    result, server = await _sync(session, monkeypatch, server, [raw])
    assert result.status == "incompatible"
    assert not whitelist.server_ready(await whitelist.get_active_server(session))
    assert reason in (server.inventory_error or "")
    # Выдача и очередь ничего не делают с несовместимым сервером.
    assert await whitelist.process_due(session, MockPanelUpdater()) == 0


async def test_admin_sees_incompatibility_when_adding_server(session, admin, monkeypatch):
    monkeypatch.setattr(provisioning, "XuiClient", lambda **_: _Panel([plain_vless()]))
    state = FakeState()
    await state.update_data(server_purpose="whitelist")
    message = FakeMessage(text="WL|LV|https://cc.example.test:2053|admin|pw")
    await admin_handlers.admin_add_server_line(message, session, state, Settings(), admin)
    answer = message.answers[-1]
    assert "не готов" in answer and "готов к выдаче" not in answer
    assert "REALITY" in answer and "SubHub" in answer
    server = await whitelist.get_active_server(session)
    assert server is not None and not whitelist.server_ready(server)
    # Автоматическая первичная синхронизация состоялась: строка импортирована.
    assert [i.inbound_id for i in server.inbounds] == [12]


# --- Совместимые сочетания ------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, kind",
    [
        (vless_reality(), "vless/reality/tcp"),
        (vless_reality(network="raw"), "vless/reality/raw"),
        (vless_reality(network="xhttp"), "vless/reality/xhttp"),
        # Публичный ключ выводится из приватного, как в SubHub.
        (vless_reality(public_key=None), "vless/reality/tcp"),
        (hysteria(), "hysteria"),
    ],
)
async def test_compatible_inbound_is_ready_with_boundary_note(
    session, monkeypatch, raw, kind
):
    server = await _server(session)
    result, server = await _sync(session, monkeypatch, server, [raw])
    assert result.status == "ready", result.error
    assert whitelist.server_ready(await whitelist.get_active_server(session))
    from app.bot import texts

    shown = texts.admin_whitelist_inventory(result)
    assert "готов к выдаче" in shown and kind in shown
    # Граница проверки видна администратору.
    assert "конфигурацию SubHub" in shown
    _assert_no_secrets(shown + (server.inventory_error or ""))


# --- Недостающие параметры ------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, needle",
    [
        (vless_reality(public_key=None, private_key=None), "публичный ключ"),
        (vless_reality(public_key=None, private_key="not-a-key"), "публичный ключ"),
        (vless_reality(server_names=[]), "serverNames"),
        (vless_reality(short_ids=[]), "shortIds"),
        (vless_reality(short_ids=[""]), "shortIds"),
        (vless_reality(decryption="mlkem768x25519plus.native.600s.x"), "decryption"),
        (vless_reality(network="grpc"), "grpc"),
        (vless_reality(network="ws"), "ws"),
        (vless_reality(header="http"), "header"),
        (hysteria(security="none"), "TLS"),
    ],
)
async def test_missing_or_unsupported_parameters_block_readiness(
    session, monkeypatch, raw, needle
):
    server = await _server(session)
    result, server = await _sync(session, monkeypatch, server, [raw])
    assert result.status == "incompatible"
    assert not whitelist.server_ready(server)
    assert needle in server.inventory_error
    _assert_no_secrets(server.inventory_error)


async def test_all_missing_reality_parameters_are_listed_together(session, monkeypatch):
    server = await _server(session)
    raw = vless_reality(public_key=None, private_key=None, server_names=[], short_ids=[])
    _, server = await _sync(session, monkeypatch, server, [raw])
    for needle in ("публичный ключ", "serverNames", "shortIds"):
        assert needle in server.inventory_error


# --- flow: не угадывается и не теряется ---------------------------------------------


async def test_flow_of_foreign_clients_is_reported_not_copied(session, monkeypatch):
    server = await _server(session)
    alien = {"id": ALIEN_UUID, "email": "alien@x", "subId": ALIEN_SUB,
             "flow": "xtls-rprx-vision", "enable": True}
    result, server = await _sync(session, monkeypatch, server, [vless_reality(clients=[alien])])
    assert result.status == "ready"
    target = whitelist.target_inbound(server)
    assert target.flow is None  # flow не подставлен по чужим клиентам
    spec = provisioning.build_provision_spec("u@x", "sub", "uuid", [target], 1)
    assert spec.inbounds[0].flow is None
    assert "xtls-rprx-vision" in server.inventory_error
    assert "без flow" in server.inventory_error
    _assert_no_secrets(server.inventory_error)


async def test_explicit_flow_survives_resync_and_reaches_client_spec(session, monkeypatch):
    server = await _server(session)
    session.add(ServerInbound(server_id=server.id, inbound_id=12, protocol=Protocol.VLESS,
                              flow="xtls-rprx-vision", enabled=True))
    await session.commit()
    for _ in range(2):
        result, server = await _sync(session, monkeypatch, server, [vless_reality()])
        assert result.status == "ready"
        target = whitelist.target_inbound(server)
        assert target.flow == "xtls-rprx-vision"
        assert "flow=xtls-rprx-vision" in server.inventory_error
    spec = provisioning.build_provision_spec("u@x", "sub", "uuid", [target], 1)
    assert spec.inbounds[0].flow == "xtls-rprx-vision"


@pytest.mark.parametrize(
    "network, flow, needle",
    [
        ("xhttp", "xtls-rprx-vision", "xhttp"),
        ("tcp", "xtls-rprx-direct", "xtls-rprx-direct"),
    ],
)
async def test_inapplicable_flow_blocks_readiness(session, monkeypatch, network, flow, needle):
    server = await _server(session)
    session.add(ServerInbound(server_id=server.id, inbound_id=12, protocol=Protocol.VLESS,
                              flow=flow, enabled=True))
    await session.commit()
    result, server = await _sync(session, monkeypatch, server, [vless_reality(network=network)])
    assert result.status == "incompatible"
    assert needle in server.inventory_error and not whitelist.server_ready(server)


# --- Повторная настройка, выбор цели, ручные отключения ------------------------------


async def test_reconfigured_inbound_becomes_ready_and_resync_is_idempotent(
    session, monkeypatch
):
    server = await _server(session)
    result, server = await _sync(session, monkeypatch, server, [plain_vless()])
    assert result.status == "incompatible"
    # Администратор перевёл тот же inbound на REALITY в панели.
    for _ in range(2):
        result, server = await _sync(session, monkeypatch, server, [vless_reality()])
        assert result.status == "ready" and whitelist.server_ready(server)
        assert whitelist.target_inbound(server).inbound_id == 12
    # Потеря REALITY в панели снова снимает готовность — без смены цели.
    result, server = await _sync(session, monkeypatch, server, [vless_reality(short_ids=[])])
    assert result.status == "incompatible" and not whitelist.server_ready(server)
    assert whitelist.target_inbound(server).inbound_id == 12
    # Синхронизация не выдаёт бесплатных пакетов.
    assert await session.scalar(select(func.count(WhitelistLedger.id))) == 0


async def test_several_inbounds_still_require_choice_and_choice_is_verified(
    session, admin, monkeypatch
):
    server = await _server(session)
    inbounds = [plain_vless(3), vless_reality(4)]
    result, server = await _sync(session, monkeypatch, server, inbounds)
    assert result.status == "needs_choice" and not whitelist.server_ready(server)
    assert "3" in server.inventory_error and "несовместим" in server.inventory_error
    assert "4" in server.inventory_error and "совместим" in server.inventory_error

    # Выбор несовместимого: сервер не готов, выбор можно поменять.
    callback = FakeCallback()
    await admin_handlers.whitelist_admin(
        callback, WhitelistAdminCallback(action="choose", value=3), session, admin,
        Settings(), FakeState(),
    )
    server = await whitelist.get_active_server(session)
    assert server.inventory_status == "incompatible" and not whitelist.server_ready(server)
    assert whitelist.target_inbound(server).inbound_id == 3
    assert "REALITY" in callback.alerts[-1]
    _, markup = await admin_handlers._whitelist_home(session)
    choices = [b.callback_data for row in markup.inline_keyboard for b in row
               if "choose" in (b.callback_data or "")]
    assert len(choices) == 2

    callback = FakeCallback()
    await admin_handlers.whitelist_admin(
        callback, WhitelistAdminCallback(action="choose", value=4), session, admin,
        Settings(), FakeState(),
    )
    server = await whitelist.get_active_server(session)
    assert whitelist.server_ready(server) and whitelist.target_inbound(server).inbound_id == 4
    _, markup = await admin_handlers._whitelist_home(session)
    assert not [b for row in markup.inline_keyboard for b in row
                if "choose" in (b.callback_data or "")]

    # Повтор синхронизации: цель прежняя, лишний inbound не подключается.
    for _ in range(2):
        result, server = await _sync(session, monkeypatch, server, inbounds)
        assert result.status == "ready" and whitelist.target_inbound(server).inbound_id == 4


async def test_manual_disable_is_kept_and_not_counted_as_target(session, monkeypatch):
    server = await _server(session)
    _, server = await _sync(session, monkeypatch, server, [vless_reality(4)])
    # Администратор отключил цель вручную — синхронизация её не включает.
    row = (await session.scalars(select(ServerInbound))).one()
    row.enabled = False
    await session.commit()
    result, server = await _sync(session, monkeypatch, server, [vless_reality(4)])
    assert result.status == "error" and not whitelist.server_ready(server)
    assert not (await session.scalars(select(ServerInbound))).one().enabled


def test_keyboard_offers_choice_in_incompatible_state():
    server = Server(id=1, name="WL", panel_url="x", username="a", password="b",
                    purpose="whitelist", enabled=True, inventory_status="incompatible")
    rows = [ServerInbound(inbound_id=3, protocol=Protocol.VLESS, enabled=True)]
    markup = keyboards.admin_whitelist_keyboard(server, rows)
    assert any("choose" in (b.callback_data or "") for r in markup.inline_keyboard for b in r)


# --- Контракт с исходниками SubHub ---------------------------------------------------

_SUBHUB_SCRIPT = r"""
import json, sys
from app.config import ServerConfig
from app.normalizer import normalize_inbound
from app.models import NormalizedClient
from app.link_builder import build_link
from app.auto_profiles import parse_node
from app.mihomo_profiles import _proxy

server = ServerConfig(id="wl", name="WL", panel_url="https://wl.test", username="u",
                      password="p", public_host="wl.test")
out = {}
for case in json.load(sys.stdin):
    inbound = normalize_inbound(case["raw"], server)
    client = NormalizedClient(email="u1", uuid="2b1f9d3c-0000-4000-8000-000000000001",
                              auth="pw-1", password="pw-1", flow=case["flow"], enabled=True)
    link = build_link(inbound, client)
    node = parse_node(link) if link else None
    out[case["name"]] = {"link": link, "mihomo": bool(node and _proxy(node, "n"))}
print(json.dumps(out))
"""

_CONTRACT_CASES = {
    "reality_tcp": (vless_reality(), None),
    "reality_tcp_vision": (vless_reality(), "xtls-rprx-vision"),
    "reality_raw": (vless_reality(network="raw"), None),
    "reality_xhttp": (vless_reality(network="xhttp"), None),
    "reality_derived_key": (vless_reality(public_key=None), None),
    "hysteria_tls": (hysteria(), None),
    "plain_vless": (plain_vless(), None),
    "vless_tls": (plain_vless(security="tls"), None),
    "trojan": (other("trojan"), None),
    "vmess": (other("vmess"), None),
    "shadowsocks": (other("shadowsocks"), None),
    "no_keys": (vless_reality(public_key=None, private_key=None), None),
    "no_server_names": (vless_reality(server_names=[]), None),
    "no_short_ids": (vless_reality(short_ids=[""]), None),
    # SubHub строит ссылку, но без параметров, нужных серверу.
    "reality_grpc": (vless_reality(network="grpc"), None),
    "reality_http_header": (vless_reality(header="http"), None),
    "vless_encryption": (vless_reality(decryption="mlkem768x25519plus.native.600s.x"), None),
    "xhttp_vision": (vless_reality(network="xhttp"), "xtls-rprx-vision"),
}


def _subhub_runner() -> tuple[str, Path] | None:
    python = os.environ.get("VPNBOT_SUBHUB_PYTHON")
    src = Path(os.environ.get(
        "VPNBOT_SUBHUB_SRC",
        Path(__file__).resolve().parents[2] / "SingleLinkVpn" / "subhub",
    ))
    if not python or not Path(python).exists() or not (src / "app" / "link_builder.py").exists():
        return None
    return python, src


@pytest.mark.skipif(_subhub_runner() is None,
                    reason="VPNBOT_SUBHUB_PYTHON/VPNBOT_SUBHUB_SRC не заданы")
def test_verdicts_agree_with_subhub_link_builder():
    """Проверка против исходников SubHub (не рабочего экземпляра и его config.yaml)."""
    from app.services.whitelist_compat import check_inbound

    runner = _subhub_runner()
    assert runner is not None
    python, src = runner
    payload = [{"name": name, "raw": raw, "flow": flow}
               for name, (raw, flow) in _CONTRACT_CASES.items()]
    env = {**os.environ, "PYTHONPATH": str(src)}
    proc = subprocess.run([python, "-c", _SUBHUB_SCRIPT], input=json.dumps(payload),
                          capture_output=True, text=True, cwd=src, env=env, timeout=60,
                          check=True)
    subhub = json.loads(proc.stdout)
    verdicts = {name: check_inbound(raw, flow=flow)
                for name, (raw, flow) in _CONTRACT_CASES.items()}
    for name, verdict in verdicts.items():
        built = subhub[name]
        if verdict.compatible:
            # Совместимое по мнению бота SubHub действительно превращает в ссылку
            # и в профиль Mihomo.
            assert built["link"] and built["mihomo"], name
            if _CONTRACT_CASES[name][1]:
                assert f"flow={_CONTRACT_CASES[name][1]}" in built["link"], name
        if not built["link"]:
            assert not verdict.compatible, name
    assert {n for n, v in verdicts.items() if v.compatible} == {
        "reality_tcp", "reality_tcp_vision", "reality_raw", "reality_xhttp",
        "reality_derived_key", "hysteria_tls",
    }
    # Где SubHub всё же строит ссылку, бот отказывает потому, что ссылка теряет
    # параметр, который требует сервер.
    assert "serviceName" not in subhub["reality_grpc"]["link"]
    assert "headerType" not in subhub["reality_http_header"]["link"]
    assert "encryption=none" in subhub["vless_encryption"]["link"]
    assert "flow" not in subhub["xhttp_vision"]["link"]
    assert not subhub["reality_grpc"]["mihomo"]

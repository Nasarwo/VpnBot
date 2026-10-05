"""Квота трафика 3x-ui → SubHub на реальной панели, без маскирующего ``enable=false``.

SubHub должен скрывать конфиг с конечной квотой, когда ``up + down >= totalGB``
(``totalGB`` — байты, 0 — безлимит), даже если панель ещё не выставила
``enable=false``. Работающая 3x-ui сама отключает исчерпанного клиента задачей
трафика, и это маскирует проверку SubHub. Поэтому сценарий останавливает Xray
whitelist-панели штатным API (``server/stopXrayService``): задача трафика при
остановленном Xray не выполняется (``XrayTrafficJob.Run``), а ручная остановка
не перезапускается сторожем (``isManuallyStopped``). Квота, срок и ``enable``
задаются тем же API, что у веб-интерфейса (``clients/update``); расход — настоящий
VLESS REALITY трафик либо, для контрольного примера, импорт inbound со
статистикой (``inbounds/import`` сохраняет ``clientStats.up/down``).

Стенд: ``ops/acceptance/stack.sh up <state> <subhub-src>``. Production, оплаты и
сообщения пользователям не используются.

    .venv/bin/python ops/acceptance/subhub_quota_e2e.py <state-dir> [--report out.json]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ops.acceptance.whitelist_e2e import (  # noqa: E402
    BLOB,
    GIB,
    Panel,
    Report,
    SubHub,
    link_for,
    load_env,
    observe_d3,
    probe,
)

R = Report()
EMAIL = "quota5@acc.test"
CONTROL = "control5@acc.test"
CONTROL_BYTES = 10 * GIB  # 10737418240 — контрольный пример задачи


async def panel_view(panel: Panel, email: str) -> dict[str, Any]:
    """Что SubHub получает из ``inbounds/list`` для клиента: settings и clientStats."""
    for inbound in await panel.inbounds():
        settings = inbound.get("settings")
        settings = json.loads(settings) if isinstance(settings, str) else settings or {}
        client = next((c for c in settings.get("clients", [])
                       if str(c.get("email", "")).casefold() == email.casefold()), None)
        if client is None:
            continue
        stats = next((s for s in inbound.get("clientStats") or []
                      if str(s.get("email", "")).casefold() == email.casefold()), None)
        return {
            "inbound": inbound.get("id"),
            "settings.enable": client.get("enable"),
            "settings.totalGB": client.get("totalGB"),
            "settings.expiryTime": client.get("expiryTime"),
            "settings has up/down": "up" in client or "down" in client,
            "clientStats.up+down": None if stats is None else stats["up"] + stats["down"],
            "clientStats.total": None if stats is None else stats.get("total"),
            "clientStats.enable": None if stats is None else stats.get("enable"),
        }
    return {}


async def xray_state(panel: Panel) -> str:
    async with panel.api() as c:
        data = (await c._api("GET", "/panel/api/server/status")).json()
    return str(((data.get("obj") or {}).get("xray") or {}).get("state"))


async def xray_command(panel: Panel, action: str) -> None:
    async with panel.api() as c:
        data = (await c._api("POST", f"/panel/api/server/{action}")).json()
    assert data.get("success"), data


async def import_control_inbound(panel: Panel, port: int) -> int:
    """VLESS REALITY inbound с клиентом контрольного примера и его статистикой."""
    keys = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "/app/bin/xray-linux-arm64", panel.image,
         "x25519"], capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    private = next(line.split(":", 1)[1].strip() for line in keys if line.startswith("PrivateKey"))
    public = next(line.split(":", 1)[1].strip() for line in keys if "PublicKey" in line)
    secret = str(uuid.uuid4())
    client = {"id": secret, "email": CONTROL, "subId": CONTROL, "flow": "", "limitIp": 0,
              "totalGB": CONTROL_BYTES, "expiryTime": 0, "enable": True, "tgId": 0, "reset": 0}
    data = {
        "up": 0, "down": 0, "total": 0, "remark": "Контрольный пример", "enable": True,
        "expiryTime": 0, "listen": "", "port": port, "protocol": "vless",
        "settings": json.dumps({"clients": [client], "decryption": "none", "fallbacks": []}),
        "streamSettings": json.dumps({
            "network": "tcp", "security": "reality", "tcpSettings": {"header": {"type": "none"}},
            "realitySettings": {
                "show": False, "xver": 0, "target": "files.acc.test:443",
                "serverNames": ["files.acc.test"], "privateKey": private, "shortIds": ["c0ffee01"],
                "settings": {"publicKey": public, "fingerprint": "chrome", "spiderX": "/"},
            },
        }),
        "sniffing": json.dumps({"enabled": False, "destOverride": []}),
        "clientStats": [{"email": CONTROL, "up": 0, "down": CONTROL_BYTES, "total": CONTROL_BYTES,
                         "expiryTime": 0, "enable": True}],
    }
    async with panel.api() as c:
        result = (await c._api("POST", "/panel/api/inbounds/import",
                               data={"data": json.dumps(data)})).json()
    assert result.get("success"), result
    return int(result["obj"]["id"])


async def stable_usage(panel: Panel, email: str, timeout: float = 60) -> int:
    """Расход, не менявшийся между двумя чтениями с интервалом 12 с."""
    deadline = time.monotonic() + timeout
    previous = await panel.used(email)
    while time.monotonic() < deadline:
        await asyncio.sleep(12)
        current = await panel.used(email)
        if current == previous:
            return current
        previous = current
    return previous


async def scenario(state: Path) -> None:
    env = load_env(state)
    prefix = env["NET"].removesuffix("-net")
    image, network = env["XUI_IMAGE"], env["NET"]
    wl = Panel(env["WL_PANEL"], env["XUI_USER"], env["XUI_PASS"], f"{prefix}-xui-wl", image)
    std = Panel(env["STD_PANEL"], env["XUI_USER"], env["XUI_PASS"], f"{prefix}-xui-std", image)
    subhub = SubHub(env["SUBHUB_URL"], env["SUBHUB_ADMIN_TOKEN"])

    R.start("Стенд")
    R.fact("3x-ui", subprocess.run(["docker", "exec", wl.container, "/app/x-ui", "-v"],
                                   capture_output=True, text=True).stdout.strip())
    digest = subprocess.run(
        ["docker", "exec", f"{prefix}-subhub", "sha256sum", "app/link_builder.py",
         "app/normalizer.py", "app/models.py"], capture_output=True, text=True,
    ).stdout.split()
    R.fact("SubHub в контейнере (sha256)",
           {digest[i + 1]: digest[i][:12] for i in range(0, len(digest), 2)})
    for panel in (std, wl):
        if await panel.allow_private_targets():
            await asyncio.sleep(3)
    std_inbound = await std.ensure_inbound(20444, "Обычный")
    wl_inbound = await wl.ensure_inbound(20443, "Обход белых списков")
    await std.create_legacy_client(EMAIL, [std_inbound])  # обычный: totalGB=0
    await wl.create_legacy_client(EMAIL, [wl_inbound])
    await wl.set_client_fields(EMAIL, totalGB=GIB)  # конечная квота 1 ГиБ

    R.start("Исходная подписка и реальный трафик")
    await subhub.sync()
    token = (await subhub.tokens()).get(EMAIL)
    links = await subhub.links(token) if token else []
    wl_link, std_link = link_for(links, "wl.acc.test"), link_for(links, "std.acc.test")
    R.check("одна ссылка подписки: обычный и whitelist-конфиг",
            token is not None and wl_link is not None and std_link is not None,
            f"конфигов {len(links)}")
    ok, out = probe(std_link or "", image, network)
    R.check("обычный конфиг передаёт трафик", ok, out)
    # Первый трафик через whitelist-панель после подготовки стенда — наблюдение D-3
    # (учёт 3x-ui, docs/WHITELIST_ACCEPTANCE.md §17), отдельно от проверок. Если панель
    # его не учла, следующие загрузки — явно обозначенный прогрев: проверкам квоты
    # ниже нужен ненулевой расход U.
    ok, _ = await observe_d3(R, wl, EMAIL, wl_link, image, network,
                             "первый трафик через whitelist-панель после подготовки стенда")
    R.check("whitelist-конфиг передаёт трафик", ok)
    used = await stable_usage(wl, EMAIL)
    for attempt in range(2, 4):
        if used >= BLOB:
            break
        ok, out = probe(wl_link or "", image, network)
        R.warmup(f"загрузка {attempt}: панель не учла первую (D-3), нужен расход U > 0", out)
        used = await stable_usage(wl, EMAIL)
    R.check("панель учла расход whitelist-клиента", used >= BLOB, f"up+down={used}")
    view = await panel_view(wl, EMAIL)
    R.fact("inbounds/list при работающем Xray", view)
    R.check("up/down приходят в clientStats, а не в settings.clients",
            view.get("settings has up/down") is False and view.get("clientStats.up+down") == used,
            view)

    R.start("Остановка Xray whitelist-панели (снятие маскирующего enable=false)")
    await xray_command(wl, "stopXrayService")
    await asyncio.sleep(2)
    R.check("Xray whitelist-панели остановлен", await xray_state(wl) != "running",
            await xray_state(wl))
    used = await wl.used(EMAIL)
    R.fact("U = up+down whitelist-клиента", used)

    past = int((datetime.now(UTC) - timedelta(days=1)).timestamp() * 1000)
    cases = [
        ("на границе: totalGB = U, enable=true", {"totalGB": used, "enable": True, "expiryTime": 0},
         False),
        ("ниже квоты: totalGB = U + 1", {"totalGB": used + 1}, True),
        ("выше квоты: totalGB = U − 1", {"totalGB": used - 1}, False),
        ("безлимит: totalGB = 0", {"totalGB": 0}, True),
        ("enable=false при остатке (totalGB = U + 1 ГиБ)",
         {"totalGB": used + GIB, "enable": False}, False),
        ("истёкший срок, enable=true, totalGB = 0",
         {"totalGB": 0, "enable": True, "expiryTime": past}, False),
        ("восстановление: totalGB = U + 1 ГиБ, срок 0",
         {"totalGB": used + GIB, "expiryTime": 0}, True),
    ]
    for title, fields, expected in cases:
        R.start(title)
        await wl.set_client_fields(EMAIL, **fields)
        view = await panel_view(wl, EMAIL)
        R.fact(f"панель: {title}", view)
        await subhub.sync()
        current = (await subhub.tokens()).get(EMAIL)
        links = await subhub.links(current) if current else []
        present = link_for(links, "wl.acc.test") is not None
        R.check(f"whitelist-конфиг {'в подписке' if expected else 'скрыт'}", present == expected,
                f"в подписке: {present}")
        R.check("обычный безлимитный конфиг в подписке",
                link_for(links, "std.acc.test") is not None)
        R.check("токен подписки не изменился", current == token)

    R.start("Контрольный пример: totalGB=10737418240, up+down=10737418240, enable=true")
    control_inbound = await import_control_inbound(wl, 20445)
    view = await panel_view(wl, CONTROL)
    R.fact("панель: контрольный пример", view)
    R.check("панель хранит пример без enable=false",
            view.get("settings.enable") is True and view.get("settings.totalGB") == CONTROL_BYTES
            and view.get("clientStats.up+down") == CONTROL_BYTES
            and view.get("clientStats.enable") is True, view)
    await subhub.sync()
    control_token = (await subhub.tokens()).get(CONTROL)
    links = await subhub.links(control_token) if control_token else []
    R.check("исчерпанный клиент контрольного примера скрыт",
            control_token is not None and not links, f"конфигов {len(links)}")
    status, _ = await subhub.resolve(CONTROL)
    R.check("resolve: подписка без активных конфигов (409)", status == 409, f"HTTP {status}")
    await wl.set_client_fields(CONTROL, totalGB=CONTROL_BYTES + 1)
    await subhub.sync()
    links = await subhub.links(control_token) if control_token else []
    R.check("после увеличения квоты на 1 байт конфиг возвращается по той же ссылке",
            len(links) == 1 and (await subhub.tokens()).get(CONTROL) == control_token,
            f"конфигов {len(links)}")
    R.fact("inbound контрольного примера", control_inbound)

    R.start("Маскирующее условие при работающем Xray (справочно)")
    await wl.set_client_fields(CONTROL, totalGB=CONTROL_BYTES)
    await xray_command(wl, "restartXrayService")

    async def disabled_by_panel() -> bool:
        return (await panel_view(wl, CONTROL)).get("settings.enable") is False

    deadline = time.monotonic() + 60
    flipped = await disabled_by_panel()
    while not flipped and time.monotonic() < deadline:
        await asyncio.sleep(3)
        flipped = await disabled_by_panel()
    R.check("работающая панель сама выставляет enable=false исчерпанному клиенту", flipped,
            await panel_view(wl, CONTROL))


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("state", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    started = time.monotonic()
    try:
        await scenario(args.state)
    except Exception as exc:  # noqa: BLE001 - фиксируем, что сценарий прерван
        R.check("сценарий выполнен до конца", False, f"{type(exc).__name__}: {exc}")
        import traceback

        traceback.print_exc()
    failed = [c for c in R.checks if not c["ok"]]
    print(f"\n{R.summary(time.monotonic() - started)}")
    if args.report:
        args.report.write_text(json.dumps(R.dump(), ensure_ascii=False, indent=1))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

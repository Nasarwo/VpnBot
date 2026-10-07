"""D-3: учёт трафика 3x-ui после запуска панели и перезапусков Xray (тестовая панель).

Сценарий не трогает бота и рабочие панели. Он поднимает собственный изолированный
стенд: Docker-сеть, файловый сервер (HTTP-источник трафика и TLS 1.3 цель REALITY)
и для каждого сценария — **новый** контейнер тестовой панели 3x-ui. Трафик —
настоящее VLESS REALITY соединение xray-клиента. Прогревов нет: до измеряемой
передачи через клиента сценария трафик не идёт, а всё, что сценарий делает до неё
(создание inbound и клиента, перезапуск контейнера), перечислено в его шагах.

Для каждой передачи сравниваются три величины:

* ``передано`` — байты, полученные клиентом (curl ``size_download``);
* ``Xray`` — прирост счётчиков пользователя в самом Xray панели
  (``xray api statsquery``: ``user>>>email>>>traffic>>>uplink/downlink``);
* ``панель`` — прирост ``up+down`` строки ``client_traffics``
  (``GET /panel/api/clients/traffic/{email}``) — именно его читает бот.

Проверка ``панель учла трафик`` требует ``панель == Xray`` после того, как прошло
не меньше двух опросов задачи трафика панели (5 с). На 3x-ui v3.9.0 часть
проверок падает — это и есть воспроизведение D-3; на исправленной панели они
должны проходить. Временной ряд счётчиков (каждые 0,5 с) сохраняется в отчёт.

    .venv/bin/python ops/acceptance/xui_traffic_d3.py <state-dir> \\
        [--image ghcr.io/mhsanaei/3x-ui:v3.9.0] [--only s1,s2] [--report out.json] [--keep]

Production, бот, оплаты и сообщения пользователям не используются.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import secrets
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from app.services.xui_client import XuiClient  # noqa: E402
from ops.acceptance.whitelist_e2e import (  # noqa: E402
    MIB,
    Panel,
    Report,
    xray_binary,
    xray_client_config,
)

R = Report()
DEFAULT_IMAGE = "ghcr.io/mhsanaei/3x-ui:v3.9.0"
XRAY = "/app/bin/xray-linux-arm64"
API = "--server=127.0.0.1:62789"
POLL = 5.0  # cadenceXrayTraffic в 3x-ui v3.6–v3.9
QUOTA = 4 * MIB


# --- Стенд ---------------------------------------------------------------------


def sh(*args: str, check: bool = True) -> str:
    proc = subprocess.run(list(args), capture_output=True, text=True)
    if check and proc.returncode:
        raise RuntimeError(f"{' '.join(args[:3])}…: {proc.stderr.strip()[-400:]}")
    return proc.stdout


@dataclass
class Lab:
    state: Path
    image: str
    client_image: str
    prefix: str = "d3acc"
    port: int = 52153
    user: str = "d3admin"
    password: str = field(default_factory=lambda: secrets.token_urlsafe(18))

    @property
    def net(self) -> str:
        return f"{self.prefix}-net"

    @property
    def files(self) -> str:
        return f"{self.prefix}-files"

    @property
    def container(self) -> str:
        return f"{self.prefix}-xui"

    def up(self) -> None:
        files = self.state / "files"
        files.mkdir(parents=True, exist_ok=True)
        self.state.chmod(0o700)
        for name, size in (("blob8m", 8), ("blob32m", 32)):
            if not (files / name).exists():
                sh("dd", "if=/dev/urandom", f"of={files / name}", "bs=1048576", f"count={size}")
        tls = self.state / "tls"
        if not (tls / "cert.pem").exists():
            tls.mkdir(exist_ok=True)
            sh("openssl", "req", "-x509", "-nodes", "-newkey", "ec", "-pkeyopt",
               "ec_paramgen_curve:prime256v1", "-keyout", f"{tls}/key.pem", "-out",
               f"{tls}/cert.pem", "-days", "30", "-subj", "/CN=files.acc.test", "-addext",
               "subjectAltName=DNS:files.acc.test")
            (tls / "key.pem").chmod(0o644)
        (self.state / "nginx.conf").write_text(
            "server { listen 80; root /usr/share/nginx/html; }\n"
            "server { listen 443 ssl; http2 on; server_name files.acc.test;\n"
            "  ssl_certificate /etc/nginx/tls/cert.pem;"
            " ssl_certificate_key /etc/nginx/tls/key.pem;\n"
            "  ssl_protocols TLSv1.3; root /usr/share/nginx/html; }\n")
        if not sh("docker", "network", "ls", "-q", "-f", f"name=^{self.net}$").strip():
            sh("docker", "network", "create", self.net)
        sh("docker", "rm", "-f", self.files, check=False)
        for fixture in files.iterdir():
            fixture.chmod(0o644)
        sh("docker", "create", "--name", self.files, "--network", self.net,
           "--network-alias", "files.acc.test", "nginx:alpine")
        sh("docker", "cp", f"{files}/.", f"{self.files}:/usr/share/nginx/html/")
        sh("docker", "cp", str(tls), f"{self.files}:/etc/nginx/tls")
        sh("docker", "cp", str(self.state / "nginx.conf"),
           f"{self.files}:/etc/nginx/conf.d/default.conf")
        sh("docker", "start", self.files)

    def down(self) -> None:
        sh("docker", "rm", "-f", self.container, self.files, check=False)
        sh("docker", "network", "rm", self.net, check=False)

    def panel(self) -> Panel:
        return Panel(f"http://127.0.0.1:{self.port}/d3panel", self.user, self.password,
                     self.container, self.image)

    async def fresh_panel(self) -> Panel:
        """Новый контейнер панели: учётные данные, шаблон для частной сети, inbound."""
        sh("docker", "rm", "-f", self.container, check=False)
        sh("docker", "run", "-d", "--name", self.container, "--network", self.net,
           "--network-alias", "wl.acc.test", "-p", f"127.0.0.1:{self.port}:2053", self.image)
        await asyncio.sleep(4)
        sh("docker", "exec", self.container, "/app/x-ui", "setting", "-username", self.user,
           "-password", self.password, "-webBasePath", "/d3panel/")
        sh("docker", "restart", self.container)
        panel = self.panel()
        await wait_api(panel)
        await panel.allow_private_targets()
        await panel.add_inbound(20443, "D-3")
        return panel

    async def restart_container(self, panel: Panel) -> None:
        """docker stop/start: новый процесс панели и новый процесс Xray."""
        sh("docker", "restart", "-t", "10", self.container)
        await wait_api(panel)


async def wait_api(panel: Panel, timeout: float = 60) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            await panel.inbounds()
            return
        except Exception:  # noqa: BLE001 - панель ещё запускается
            if time.monotonic() > deadline:
                raise
            await asyncio.sleep(0.3)


async def add_client(panel: Panel, email: str, **fields: Any) -> str:
    inbound = next(i for i in await panel.inbounds() if i.get("port") == 20443)
    secret = await panel.create_legacy_client(email, [int(inbound["id"])])
    if fields:
        await panel.set_client_fields(email, **fields)
    stream = inbound["streamSettings"]
    stream = json.loads(stream) if isinstance(stream, str) else stream
    reality = stream["realitySettings"]
    return (f"vless://{secret}@wl.acc.test:{inbound['port']}?type=tcp&security=reality"
            f"&pbk={reality['settings']['publicKey']}&sni={reality['serverNames'][0]}"
            f"&sid={reality['shortIds'][0]}&fp=chrome&spx=%2F#d3")


async def panel_call(panel: Panel, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    async with panel.api() as c:
        data = (await c._api(method, path, **kwargs)).json()
    assert data.get("success"), data
    return data


async def set_restart_on_disable(panel: Panel, value: bool) -> None:
    current = (await panel_call(panel, "POST", "/panel/api/setting/all"))["obj"]
    current["restartXrayOnClientDisable"] = value
    await panel_call(panel, "POST", "/panel/api/setting/update", json=current)


def xray_snapshot(container: str) -> tuple[str, float | None, dict[str, int]]:
    """PID Xray, его возраст (с) и счётчики пользователей Xray (up+down по email)."""
    out = sh("docker", "exec", container, "sh", "-c",
             "p=$(pgrep -f xray-linux | head -1); echo \"$p\"; "
             "[ -n \"$p\" ] && echo $(cut -d' ' -f1 /proc/uptime) $(cut -d' ' -f22 /proc/$p/stat)"
             " || echo; "
             f"{XRAY} api statsquery {API} -pattern 'user>>>' 2>/dev/null", check=False)
    lines = out.split("\n", 2)
    pid = lines[0].strip() if lines else ""
    age = None
    if len(lines) > 1 and lines[1].strip():
        uptime, start_ticks = lines[1].split()
        age = float(uptime) - int(start_ticks) / 100  # CLK_TCK = 100 в Linux-образе
    usage: dict[str, int] = {}
    try:
        stats = json.loads(lines[2] if len(lines) > 2 and lines[2].strip() else "{}")
    except json.JSONDecodeError:
        stats = {}
    for item in stats.get("stat") or []:
        email = item["name"].split(">>>")[1]
        usage[email] = usage.get(email, 0) + int(item.get("value") or 0)
    return pid, age, usage


def container_started(container: str) -> float:
    raw = sh("docker", "inspect", "-f", "{{.State.StartedAt}}", container).strip()
    head, _, frac = raw.rstrip("Z").partition(".")
    return datetime.fromisoformat(head + "+00:00").timestamp() + float(f"0.{frac or 0}")


# --- Измерения -----------------------------------------------------------------


class Meter:
    """Временной ряд каждые 0,5 с: PID Xray, счётчики Xray и панели по email."""

    def __init__(self, lab: Lab, panel: Panel, emails: list[str]) -> None:
        self.lab, self.panel, self.emails = lab, panel, emails
        self.t0 = time.time()
        self.rows: list[dict[str, Any]] = []
        self.marks: list[tuple[float, str]] = []
        self._task: asyncio.Task | None = None

    def now(self) -> float:
        return round(time.time() - self.t0, 2)

    def mark(self, text: str) -> float:
        t = self.now()
        self.marks.append((t, text))
        print(f"    t={t:7.2f}  {text}", flush=True)
        return t

    async def _panel_usage(self, client: XuiClient) -> dict[str, dict[str, Any] | None]:
        result = {}
        for email in self.emails:
            row = await client.get_client_usage(email)
            result[email] = None if row is None else {
                "used": int(row.get("up") or 0) + int(row.get("down") or 0),
                "enable": row.get("enable"),
            }
        return result

    async def _loop(self) -> None:
        client: XuiClient | None = None
        while True:
            t = self.now()
            pid, age, xray = await asyncio.to_thread(xray_snapshot, self.lab.container)
            panel: dict[str, Any] = {}
            try:
                if client is None:
                    client = XuiClient(self.panel.url, self.panel.user, self.panel.password,
                                       timeout=5)
                    await client.__aenter__()
                panel = await self._panel_usage(client)
            except Exception:  # noqa: BLE001 - панель перезапускается: запишем пропуск
                if client is not None:
                    await client.close()
                client = None
            self.rows.append({"t": t, "pid": pid, "xray_age": age, "xray": xray,
                              "panel": panel})
            await asyncio.sleep(0.5)

    def start(self) -> None:
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def panel_changes(self, email: str, since: float = 0) -> list[tuple[float, int]]:
        """Моменты изменения учёта панели — это моменты опросов задачи трафика."""
        changes: list[tuple[float, int]] = []
        last = None
        for row in self.rows:
            value = ((row["panel"] or {}).get(email) or {}).get("used")
            if value is None:
                continue
            if last is not None and value != last and row["t"] >= since:
                changes.append((row["t"], value - last))
            last = value
        return changes

    def dump(self) -> dict[str, Any]:
        compact, last = [], None
        for row in self.rows:
            key = (row["pid"], json.dumps(row["xray"], sort_keys=True),
                   json.dumps(row["panel"], sort_keys=True))
            if key != last:
                compact.append(row)
                last = key
        return {"marks": self.marks, "series": compact}


@dataclass
class Snapshot:
    pid: str
    xray: int
    panel: int
    enable: Any


async def snapshot(lab: Lab, panel: Panel, email: str) -> Snapshot:
    pid, _, xray = await asyncio.to_thread(xray_snapshot, lab.container)
    async with panel.api() as c:
        row = await c.get_client_usage(email) or {}
    return Snapshot(pid, xray.get(email, 0),
                    int(row.get("up") or 0) + int(row.get("down") or 0), row.get("enable"))


async def settle(lab: Lab, panel: Panel, email: str, minimum: float = 2 * POLL + 1.5) -> Snapshot:
    """Ждёт ≥ двух опросов задачи трафика и неизменности учёта панели в течение опроса."""
    await asyncio.sleep(minimum)
    previous = await snapshot(lab, panel, email)
    for _ in range(12):
        await asyncio.sleep(POLL + 1)
        current = await snapshot(lab, panel, email)
        if (current.panel, current.xray) == (previous.panel, previous.xray):
            return current
        previous = current
    return previous


def transfer_sync(lab: Lab, link: str, path: str = "blob8m", rate: str | None = None,
                  seconds: int = 60) -> str:
    limit = f"--limit-rate {rate} " if rate else ""
    script = (
        f"cat > /tmp/c.json; {XRAY} run -c /tmp/c.json >/tmp/x.log 2>&1 & "
        f"sleep 1.5; curl -s -m {seconds} {limit}--socks5-hostname 127.0.0.1:10808 "
        f"-o /dev/null -w '%{{http_code}} %{{size_download}}' http://files.acc.test/{path}"
    )
    proc = subprocess.run(
        ["docker", "run", "--rm", "-i", "--network", lab.net, "--entrypoint", "sh",
         lab.client_image, "-c", script],
        input=json.dumps(xray_client_config(link)).encode(), capture_output=True,
        timeout=seconds + 30,
    )
    return proc.stdout.decode().strip()


async def transfer(meter: Meter, lab: Lab, link: str, label: str, **kwargs: Any) -> int:
    meter.mark(f"{label}: начало")
    out = await asyncio.to_thread(transfer_sync, lab, link, **kwargs)
    meter.mark(f"{label}: {out}")
    parts = out.split()
    return int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else 0


def delta(before: Snapshot, after: Snapshot) -> tuple[int, int]:
    """Прирост по Xray (с учётом перезапуска Xray) и по панели."""
    xray = after.xray - (before.xray if before.pid == after.pid else 0)
    return xray, after.panel - before.panel


def accounted(name: str, before: Snapshot, after: Snapshot, received: int) -> int:
    xray, panel = delta(before, after)
    lost = xray - panel
    R.check(name, received > 0 and xray >= received and lost == 0,
            f"передано {received} Б, Xray +{xray} Б, панель +{panel} Б, не учтено {lost} Б")
    return lost


# --- Сценарии -----------------------------------------------------------------
#
# Каждый сценарий начинается с нового контейнера панели (fresh_panel) и, где
# сказано, с docker restart — нового процесса панели и Xray без какого-либо
# трафика до измеряемой передачи.


async def s1_start(lab: Lab) -> None:
    R.start("S1. Запуск панели: первый трафик до первого опроса задачи трафика")
    panel = await lab.fresh_panel()
    link = await add_client(panel, "s1@d3")
    await lab.restart_container(panel)
    meter = Meter(lab, panel, ["s1@d3"])
    meter.t0 = container_started(lab.container)
    meter.mark("API панели отвечает (время от старта контейнера)")
    meter.start()
    before = await snapshot(lab, panel, "s1@d3")
    received = await transfer(meter, lab, link, "загрузка 1 (сразу после ответа API)")
    end1 = meter.now()
    after = await settle(lab, panel, "s1@d3")
    lost = accounted("D-3 (запуск): трафик до первого опроса учтён панелью", before, after,
                     received)
    _, age, _ = await asyncio.to_thread(xray_snapshot, lab.container)
    xray_start = meter.now() - (age or 0)
    changes = meter.panel_changes("s1@d3")
    R.fact("S1: Xray запущен, с от старта контейнера", round(xray_start, 1))
    R.fact("S1: загрузка 1 завершена, с от старта контейнера", end1)
    R.fact("S1: изменения учёта панели (t, +Б)", changes)
    before = after
    received = await transfer(meter, lab, link, "загрузка 2")
    end2 = meter.now()
    after = await settle(lab, panel, "s1@d3")
    accounted("следующий трафик того же процесса учтён полностью", before, after, received)
    first = next((t for t, _ in meter.panel_changes("s1@d3", end2)), None)
    if first is not None:
        R.fact("S1: задержка учёта загрузки 2 (с от её конца до изменения в панели)",
               round(first - end2, 1))
    await meter.stop()
    R.facts["S1: временной ряд"] = meter.dump()
    R.facts["S1: потеря, Б"] = lost


async def s1b_start_late(lab: Lab) -> None:
    R.start("S1b. Запуск панели: первый трафик после первых опросов")
    panel = await lab.fresh_panel()
    link = await add_client(panel, "s1b@d3")
    await lab.restart_container(panel)
    meter = Meter(lab, panel, ["s1b@d3"])
    meter.t0 = container_started(lab.container)
    meter.start()
    await asyncio.sleep(max(0.0, 20 - meter.now()))
    before = await snapshot(lab, panel, "s1b@d3")
    received = await transfer(meter, lab, link, "загрузка через 20 с после старта контейнера")
    end = meter.now()
    after = await settle(lab, panel, "s1b@d3")
    accounted("трафик после первого опроса учтён (потеря — не задержка учёта)", before, after,
              received)
    first = next((t for t, _ in meter.panel_changes("s1b@d3", end)), None)
    R.fact("S1b: задержка учёта (с от конца загрузки до изменения в панели)",
           None if first is None else round(first - end, 1))
    await meter.stop()
    R.facts["S1b: временной ряд"] = meter.dump()


async def s1c_window(lab: Lab) -> None:
    R.start("S1c. Запуск панели: длина окна потери (1 МиБ/с с момента ответа API)")
    panel = await lab.fresh_panel()
    link = await add_client(panel, "s1c@d3")
    await lab.restart_container(panel)
    meter = Meter(lab, panel, ["s1c@d3"])
    meter.t0 = container_started(lab.container)
    meter.mark("API панели отвечает")
    meter.start()
    before = await snapshot(lab, panel, "s1c@d3")
    received = await transfer(meter, lab, link, "32 МиБ со скоростью 1 МиБ/с",
                              path="blob32m", rate="1M", seconds=60)
    after = await settle(lab, panel, "s1c@d3")
    lost = accounted("D-3 (запуск): равномерный трафик с первых секунд учтён панелью",
                     before, after, received)
    _, age, _ = await asyncio.to_thread(xray_snapshot, lab.container)
    xray_start = meter.now() - (age or 0)
    changes = meter.panel_changes("s1c@d3")
    # Опрос, ставший базой, прочитал ровно «lost» байт: находим момент, когда
    # счётчик Xray достиг этой величины.
    baseline_t = next((row["t"] for row in meter.rows
                       if lost and row["xray"].get("s1c@d3", 0) >= lost), None)
    R.fact("S1c: Xray запущен, с от старта контейнера", round(xray_start, 1))
    R.fact("S1c: не учтено, Б", lost)
    R.fact("S1c: счётчик Xray достиг не учтённой величины, с от старта контейнера",
           baseline_t)
    R.fact("S1c: изменения учёта панели (t, +Б) — опросы задачи трафика", changes)
    await meter.stop()
    R.facts["S1c: временной ряд"] = meter.dump()


async def _restart_xray_case(lab: Lab, title: str, email: str, before_restart: int,
                             expect_name: str) -> None:
    R.start(title)
    panel = await lab.fresh_panel()
    link = await add_client(panel, email)
    await lab.restart_container(panel)
    meter = Meter(lab, panel, [email])
    meter.start()
    await asyncio.sleep(15)
    for n in range(before_restart):
        before = await snapshot(lab, panel, email)
        received = await transfer(meter, lab, link, f"загрузка A{n + 1} до перезапуска Xray")
        after = await settle(lab, panel, email)
        accounted(f"A{n + 1} учтена", before, after, received)
    base = await snapshot(lab, panel, email)
    await panel_call(panel, "POST", "/panel/api/server/restartXrayService")
    meter.mark("POST server/restartXrayService (перезапуск Xray через API панели)")
    await asyncio.sleep(2 * POLL + 2)
    before = await snapshot(lab, panel, email)
    R.fact(f"{title[:3]}: Xray PID до/после перезапуска", f"{base.pid} → {before.pid}")
    received = await transfer(meter, lab, link, "загрузка B после перезапуска и опросов")
    after = await settle(lab, panel, email)
    accounted(expect_name, before, after, received)
    before = after
    received = await transfer(meter, lab, link, "загрузка C")
    after = await settle(lab, panel, email)
    accounted("C учтена", before, after, received)
    await meter.stop()
    R.facts[f"{title[:3]}: временной ряд"] = meter.dump()


async def s2_xray_restart(lab: Lab) -> None:
    await _restart_xray_case(
        lab, "S2. Перезапуск Xray через API: база задачи трафика не сброшена", "s2@d3", 1,
        "D-3 (перезапуск Xray): B, не меньше старой базы, учтена панелью",
    )


async def s2b_xray_restart_smaller(lab: Lab) -> None:
    await _restart_xray_case(
        lab, "S2b. Перезапуск Xray через API: первый трафик меньше старой базы", "s2b@d3", 2,
        "B меньше старой базы учтена (условие механизма: значение ≥ базы)",
    )


async def _disable_case(lab: Lab, title: str, restart_on_disable: bool) -> None:
    R.start(title)
    panel = await lab.fresh_panel()
    if not restart_on_disable:
        await set_restart_on_disable(panel, False)
    link_a = await add_client(panel, "qa@d3", totalGB=QUOTA)
    link_b = await add_client(panel, "qb@d3")
    await lab.restart_container(panel)
    meter = Meter(lab, panel, ["qa@d3", "qb@d3"])
    meter.start()
    await asyncio.sleep(15)
    pid0 = (await snapshot(lab, panel, "qb@d3")).pid
    await transfer(meter, lab, link_a, "A (квота 4 МиБ) загружает 8 МиБ")
    # Задача трафика сначала фиксирует enable=false, затем (при настройке по
    # умолчанию) перезапускает Xray в том же проходе: ждём оба события.
    deadline = time.monotonic() + 3 * POLL
    disabled_at = None
    pid = pid0
    while time.monotonic() < deadline:
        state = await snapshot(lab, panel, "qa@d3")
        pid = state.pid
        if state.enable is False and disabled_at is None:
            disabled_at = time.monotonic()
        if pid != pid0 or (disabled_at is not None and time.monotonic() - disabled_at > 6):
            break
        await asyncio.sleep(0.2)
    meter.mark(f"A отключена панелью; Xray PID {pid0} → {pid}")
    R.check("панель отключила A по исчерпанию квоты", disabled_at is not None)
    if restart_on_disable:
        R.check("restartXrayOnClientDisable=true (по умолчанию): Xray перезапущен",
                pid != pid0, f"PID {pid0} → {pid}")
    else:
        R.check("restartXrayOnClientDisable=false: Xray не перезапускался", pid == pid0,
                f"PID {pid0} → {pid}")
    before_b = await snapshot(lab, panel, "qb@d3")
    received = await transfer(meter, lab, link_b, "B (безлимит) сразу после отключения A")
    after_b = await settle(lab, panel, "qb@d3")
    accounted("D-3 (перезапуск при отключении клиента): трафик другого клиента учтён",
              before_b, after_b, received)
    before_b = after_b
    received = await transfer(meter, lab, link_b, "B ещё раз")
    after_b = await settle(lab, panel, "qb@d3")
    accounted("последующий трафик B учтён", before_b, after_b, received)
    await meter.stop()
    R.facts[f"{title[:3]}: временной ряд"] = meter.dump()


async def s3_disable_restart(lab: Lab) -> None:
    await _disable_case(lab, "S3. Исчерпание квоты A → перезапуск Xray задачей трафика → B",
                        True)


async def m2_disable_without_restart(lab: Lab) -> None:
    await _disable_case(lab, "M2. То же при restartXrayOnClientDisable=false", False)


async def s4_sighup(lab: Lab) -> None:
    R.start("S4. SIGHUP: перезапуск панели без перезапуска Xray")
    panel = await lab.fresh_panel()
    link = await add_client(panel, "s4@d3")
    await lab.restart_container(panel)
    meter = Meter(lab, panel, ["s4@d3"])
    meter.start()
    await asyncio.sleep(15)
    start = await snapshot(lab, panel, "s4@d3")
    received_a = await transfer(meter, lab, link, "загрузка A до SIGHUP")
    mid = await settle(lab, panel, "s4@d3")
    accounted("A учтена", start, mid, received_a)
    sh("docker", "kill", "-s", "HUP", lab.container)
    meter.mark("SIGHUP процессу панели")
    await asyncio.sleep(1)
    await wait_api(panel)
    meter.mark("API панели отвечает после SIGHUP")
    received_b = await transfer(meter, lab, link, "загрузка B сразу после SIGHUP")
    after = await settle(lab, panel, "s4@d3")
    R.check("Xray не перезапускался (тот же PID)", after.pid == mid.pid,
            f"{mid.pid} → {after.pid}")
    accounted("D-3 (SIGHUP): B учтена новой задачей трафика", mid, after, received_b)
    R.check("A не учтена повторно после SIGHUP (панель ≤ Xray)",
            after.panel - start.panel <= after.xray - start.xray,
            f"панель +{after.panel - start.panel} Б, Xray +{after.xray - start.xray} Б")
    await meter.stop()
    R.facts["S4: временной ряд"] = meter.dump()


async def s5_hot_update(lab: Lab) -> None:
    R.start("S5. Изменение клиента через API без перезапуска Xray")
    panel = await lab.fresh_panel()
    link = await add_client(panel, "s5@d3")
    await lab.restart_container(panel)
    meter = Meter(lab, panel, ["s5@d3"])
    meter.start()
    await asyncio.sleep(15)
    before = await snapshot(lab, panel, "s5@d3")
    received = await transfer(meter, lab, link, "загрузка A")
    mid = await settle(lab, panel, "s5@d3")
    accounted("A учтена", before, mid, received)
    await panel.set_client_fields("s5@d3", totalGB=10 * 1024 * MIB, comment="d3")
    meter.mark("clients/update: totalGB=10 ГиБ, comment")
    received = await transfer(meter, lab, link, "загрузка B сразу после обновления")
    after = await settle(lab, panel, "s5@d3")
    R.check("Xray не перезапускался", after.pid == mid.pid, f"{mid.pid} → {after.pid}")
    accounted("B после clients/update учтена", mid, after, received)
    await meter.stop()


async def _overshoot_case(lab: Lab, title: str, restart_on_disable: bool) -> None:
    R.start(title)
    panel = await lab.fresh_panel()
    if not restart_on_disable:
        await set_restart_on_disable(panel, False)
    link = await add_client(panel, "ov@d3", totalGB=QUOTA)
    await lab.restart_container(panel)
    meter = Meter(lab, panel, ["ov@d3"])
    meter.start()
    await asyncio.sleep(15)
    before = await snapshot(lab, panel, "ov@d3")
    received = await transfer(meter, lab, link, "32 МиБ со скоростью 2 МиБ/с при квоте 4 МиБ",
                              path="blob32m", rate="2M", seconds=40)
    after = await settle(lab, panel, "ov@d3")
    _, panel_delta = delta(before, after)
    crossed = next((row["t"] for row in meter.rows if row["xray"].get("ov@d3", 0) >= QUOTA),
                   None)
    disabled = next((row["t"] for row in meter.rows
                     if ((row["panel"] or {}).get("ov@d3") or {}).get("enable") is False), None)
    R.fact(f"{title[:3]}: получено клиентом, Б", received)
    R.fact(f"{title[:3]}: учтено панелью, Б (квота {QUOTA})", after.panel)
    R.fact(f"{title[:3]}: превышение квоты по панели, Б", after.panel - QUOTA)
    R.fact(f"{title[:3]}: от достижения квоты по Xray до отключения в панели, с",
           None if crossed is None or disabled is None else round(disabled - crossed, 1))
    R.check("панель отключила клиента", after.enable is False)
    if restart_on_disable:
        R.check("превышение ограничено одним интервалом опроса (≤ 2 МиБ/с × (5 + 3) с)",
                after.panel - QUOTA <= 16 * MIB and received < 32 * MIB,
                f"превышение {after.panel - QUOTA} Б, получено {received} Б")
    else:
        R.fact(f"{title[:3]}: соединение продолжилось после отключения (получено всё)",
               received >= 32 * MIB)
    # Всё, что получил клиент, прошло через Xray панели: панель должна учесть не меньше.
    # (Счётчик Xray для сравнения не годится: перезапуск уносит его вместе с процессом.)
    R.check("превышение учтено панелью (учтено ≥ получено клиентом)",
            panel_delta >= received, f"учтено {panel_delta} Б, получено {received} Б")
    await meter.stop()
    R.facts[f"{title[:3]}: временной ряд"] = meter.dump()


async def s6_overshoot(lab: Lab) -> None:
    await _overshoot_case(lab, "S6. Превышение квоты между опросами (по умолчанию)", True)


async def s6b_overshoot_no_restart(lab: Lab) -> None:
    await _overshoot_case(lab, "S6b. Превышение квоты при restartXrayOnClientDisable=false",
                          False)


async def s7_tail(lab: Lab) -> None:
    R.start("S7. Хвост перед перезапуском Xray (трафик после последнего опроса)")
    panel = await lab.fresh_panel()
    link = await add_client(panel, "s7@d3")
    await lab.restart_container(panel)
    meter = Meter(lab, panel, ["s7@d3"])
    meter.start()
    await asyncio.sleep(15)
    before = await snapshot(lab, panel, "s7@d3")

    async def restart_later() -> float:
        # Перезапуск через 4 с после опроса с приростом: хвост ≈ 4 с трафика.
        started = meter.now()
        while not [t for t, _ in meter.panel_changes("s7@d3") if t > started + 3]:
            await asyncio.sleep(0.2)
        await asyncio.sleep(4)
        await panel_call(panel, "POST", "/panel/api/server/restartXrayService")
        return meter.mark("POST server/restartXrayService через 4 с после опроса")

    restarter = asyncio.create_task(restart_later())
    received = await transfer(meter, lab, link, "32 МиБ со скоростью 1 МиБ/с", path="blob32m",
                              rate="1M", seconds=40)
    restarted_at = await restarter
    after = await settle(lab, panel, "s7@d3")
    counted = after.panel - before.panel
    # Клиент получил байты только через Xray панели, поэтому «получено − учтено» —
    # нижняя граница не учтённого хвоста; наибольшее значение счётчика Xray
    # прежнего процесса — его оценка по выборке раз в 0,5 с.
    seen = max([row["xray"].get("s7@d3", 0) for row in meter.rows
                if row["pid"] == before.pid] + [0])
    polls = [t for t, _ in meter.panel_changes("s7@d3") if t < restarted_at]
    R.fact("S7: получено клиентом до обрыва, Б", received)
    R.fact("S7: учтено панелью, Б", counted)
    R.fact("S7: не учтено, нижняя граница (получено − учтено), Б", received - counted)
    R.fact("S7: наибольший счётчик Xray прежнего процесса по выборке, Б", seen)
    R.fact("S7: от последнего опроса с приростом до перезапуска, с",
           round(restarted_at - polls[-1], 1) if polls else None)
    await meter.stop()
    R.facts["S7: временной ряд"] = meter.dump()


async def m1_planned_restart(lab: Lab) -> None:
    R.start("M1. Плановый перезапуск: inbound выключен до первого опроса")
    panel = await lab.fresh_panel()
    link = await add_client(panel, "m1@d3")
    inbound = next(i for i in await panel.inbounds() if i.get("port") == 20443)

    async def set_inbound(enable: bool) -> None:
        current = next(i for i in await panel.inbounds() if i["id"] == inbound["id"])
        payload = {k: current[k] for k in ("up", "down", "total", "remark", "listen", "port",
                                           "protocol", "expiryTime", "settings",
                                           "streamSettings", "sniffing") if k in current}
        for key in ("settings", "streamSettings", "sniffing"):
            if key in payload and not isinstance(payload[key], str):
                payload[key] = json.dumps(payload[key])
        payload["enable"] = enable
        await panel_call(panel, "POST", f"/panel/api/inbounds/update/{inbound['id']}",
                         json=payload)

    await set_inbound(False)
    await lab.restart_container(panel)
    meter = Meter(lab, panel, ["m1@d3"])
    meter.t0 = container_started(lab.container)
    meter.start()
    await asyncio.sleep(max(0.0, 15 - meter.now()))
    await set_inbound(True)
    meter.mark("inbound включён через 15 с после старта контейнера")
    before = await snapshot(lab, panel, "m1@d3")
    received = await transfer(meter, lab, link, "загрузка сразу после включения")
    after = await settle(lab, panel, "m1@d3")
    accounted("трафик после включения inbound учтён", before, after, received)
    await meter.stop()


SCENARIOS = {
    "s1": s1_start, "s1b": s1b_start_late, "s1c": s1c_window, "s2": s2_xray_restart,
    "s2b": s2b_xray_restart_smaller, "s3": s3_disable_restart, "s4": s4_sighup,
    "s5": s5_hot_update, "s6": s6_overshoot, "s6b": s6b_overshoot_no_restart, "s7": s7_tail,
    "m1": m1_planned_restart, "m2": m2_disable_without_restart,
}


async def main() -> int:
    global XRAY
    parser = argparse.ArgumentParser()
    parser.add_argument("state", type=Path)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--client-image", default=DEFAULT_IMAGE)
    parser.add_argument(
        "--prefix", default="d3acc", help="Docker names/network for this isolated run"
    )
    parser.add_argument("--port", type=int, default=52153, help="Local panel API port")
    parser.add_argument("--only", default=",".join(SCENARIOS))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()
    XRAY = xray_binary(args.image)
    if xray_binary(args.client_image) != XRAY:
        raise RuntimeError("Panel and client image architectures must match")
    lab = Lab(args.state, args.image, args.client_image, prefix=args.prefix, port=args.port)
    started = time.monotonic()
    lab.up()
    version = sh("docker", "run", "--rm", "--entrypoint", "/app/x-ui", args.image, "-v").strip()
    R.fact("образ панели", f"{args.image} (x-ui {version})")
    try:
        for name in args.only.split(","):
            try:
                await SCENARIOS[name](lab)
            except Exception as exc:  # noqa: BLE001 - сценарий прерван, продолжаем остальные
                R.check(f"сценарий {name} выполнен до конца", False,
                        f"{type(exc).__name__}: {exc}")
                import traceback

                traceback.print_exc()
    finally:
        if not args.keep:
            lab.down()
    failed = [c for c in R.checks if not c["ok"]]
    print(f"\n{R.summary(time.monotonic() - started)}")
    for check in failed:
        print(f"  FAIL [{check['section'][:3]}] {check['name']} — {check['detail']}")
    if args.report:
        args.report.write_text(json.dumps(R.dump(), ensure_ascii=False, indent=1))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

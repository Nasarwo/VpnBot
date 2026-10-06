"""Сквозная приёмка «Обход белых списков» на реальных 3x-ui и тестовом SubHub.

Стенд поднимается ``ops/acceptance/stack.sh up <state> <subhub-src>``: две
настоящие панели 3x-ui (обычная и whitelist), PostgreSQL 16, файловый сервер
и SubHub в изолированной Docker-сети. Сценарий вызывает те же обработчики
бота, что и Telegram (транспорт Telegram заменён записывающей заглушкой),
реальный ``XuiPanelUpdater`` и реальные advisory lock PostgreSQL. Трафик идёт
через настоящее VLESS-соединение xray-клиента по ссылке из подписки SubHub.

Production, реальные квитанции и сообщения пользователям не используются.

    .venv/bin/python ops/acceptance/whitelist_e2e.py <state-dir> [--report out.json]
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import subprocess
import sys
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import asyncpg  # noqa: E402
import httpx  # noqa: E402
from aiogram.filters import CommandObject  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.bot import admin_handlers, texts, user_handlers  # noqa: E402
from app.bot.callbacks import (  # noqa: E402
    AdminCallback,
    PaymentCallback,
    PlanCallback,
    WhitelistAdminCallback,
    WhitelistCallback,
)
from app.config import Settings  # noqa: E402
from app.db.enums import PaymentStatus, UserRole  # noqa: E402
from app.db.models import (  # noqa: E402
    PAYMENT_KIND_TRAFFIC,
    ClientServerMapping,
    PaymentAttachment,
    PaymentRequest,
    TrafficPackage,
    User,
    VpnClient,
    WhitelistAccount,
    WhitelistLedger,
)
from app.db.repositories import UserRepository, VpnClientRepository  # noqa: E402
from app.services import billing, bind_requests, payments, whitelist  # noqa: E402
from app.services.xui_client import XuiClient  # noqa: E402
from app.services.xui_payloads import (  # noqa: E402
    build_client_record,
    client_record_body,
    sanitize_client_for_api,
)
from app.services.xui_updater import build_updater  # noqa: E402
from tests.test_admin_confirm import FakeBot  # noqa: E402
from tests.test_whitelist_bot import FakeCallback, FakeMessage, FakeState  # noqa: E402

GIB = 1024**3
MIB = 1024**2
BLOB = 8 * MIB
ADMIN_TG = 700001
SMALL_GB = "0.02"  # ≈20,5 МиБ: исчерпание квоты реальным трафиком за минуту
SMALL = whitelist.gib_to_bytes(SMALL_GB)


# --- Отчёт ---------------------------------------------------------------------


@dataclass
class Report:
    checks: list[dict[str, Any]] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)
    # Наблюдения известных дефектов вне кода бота (D-3 — учёт трафика 3x-ui) и
    # прогревы стенда. Ни то ни другое не входит в число OK: итог печатает их
    # отдельно, чтобы успешные проверки не скрывали наблюдение.
    known: list[dict[str, Any]] = field(default_factory=list)
    warmups: list[dict[str, Any]] = field(default_factory=list)
    section: str = ""

    def start(self, title: str) -> None:
        self.section = title
        print(f"\n== {title}", flush=True)

    def check(self, name: str, ok: bool, detail: Any = "") -> bool:
        self.checks.append(
            {"section": self.section, "name": name, "ok": bool(ok), "detail": str(detail)}
        )
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail != "" else ""),
              flush=True)
        return bool(ok)

    def fact(self, key: str, value: Any) -> None:
        self.facts[key] = value
        print(f"  · {key} = {value}", flush=True)

    def known_defect(self, code: str, name: str, reproduced: bool, detail: Any = "") -> None:
        self.known.append({"section": self.section, "code": code, "name": name,
                           "reproduced": bool(reproduced), "detail": str(detail)})
        mark = "ВОСПРОИЗВЕДЁН" if reproduced else "не проявился"
        print(f"  [{code}: {mark}] {name}" + (f" — {detail}" if detail != "" else ""),
              flush=True)

    def warmup(self, reason: str, detail: Any = "") -> None:
        self.warmups.append({"section": self.section, "reason": reason, "detail": str(detail)})
        print(f"  [ПРОГРЕВ] {reason}" + (f" — {detail}" if detail != "" else ""), flush=True)

    def summary(self, seconds: float) -> str:
        failed = sum(not c["ok"] for c in self.checks)
        line = f"Итого: {len(self.checks) - failed} OK, {failed} FAIL"
        if self.known:
            codes = sorted({k["code"] for k in self.known})
            reproduced = sum(k["reproduced"] for k in self.known)
            line += (f"; известные дефекты вне бота ({', '.join(codes)}): воспроизведено "
                     f"{reproduced} из {len(self.known)} наблюдений")
        line += f"; прогревов: {len(self.warmups)}"
        return f"{line}; {seconds:.0f} с"

    def dump(self) -> dict[str, Any]:
        return {"checks": self.checks, "known_defects": self.known, "warmups": self.warmups,
                "facts": self.facts}


R = Report()


# --- Стенд ---------------------------------------------------------------------


def load_env(state: Path) -> dict[str, str]:
    env = {}
    for line in (state / "panel.env").read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            env[key] = value
    return env


class Panel:
    """Прямой доступ к тестовой панели — для проверок и действий «вручную в панели»."""

    def __init__(self, url: str, user: str, password: str, container: str, image: str) -> None:
        self.url, self.user, self.password, self.container = url, user, password, container
        self.image = image

    @asynccontextmanager
    async def api(self):
        async with XuiClient(self.url, self.user, self.password, timeout=10) as client:
            yield client

    async def inbounds(self) -> list[dict[str, Any]]:
        async with self.api() as c:
            return await c.list_inbounds()

    async def allow_private_targets(self) -> bool:
        """Разрешает трафик к частной подсети стенда — только на тестовых панелях.

        Файловый сервер стенда живёт в частной Docker-сети. Шаблон 3x-ui
        направляет geoip:private в blocked, а freedom в Xray 26 по умолчанию
        блокирует частные адреса для VLESS (finalRules). На рабочих панелях
        оба ограничения остаются. Возвращает True, если шаблон изменён.
        """
        allow = [{"action": "allow", "ip": ["172.16.0.0/12"]}]
        async with self.api() as c:
            raw = (await c._api("POST", "/panel/api/xray/")).json()
            template = json.loads(raw["obj"])["xraySetting"]
            rules = template.get("routing", {}).get("rules", [])
            kept = [r for r in rules if "geoip:private" not in (r.get("ip") or [])]
            direct = next(o for o in template["outbounds"] if o.get("tag") == "direct")
            settings = direct.setdefault("settings", {})
            if len(kept) == len(rules) and settings.get("finalRules") == allow:
                return False
            template["routing"]["rules"] = kept
            settings["finalRules"] = allow
            data = (await c._api(
                "POST", "/panel/api/xray/update",
                data={"xraySetting": json.dumps(template)},
            )).json()
        assert data.get("success"), data
        return True

    async def ensure_inbound(self, port: int, remark: str) -> int:
        for item in await self.inbounds():
            if item.get("port") == port:
                return int(item["id"])
        return await self.add_inbound(port, remark)

    async def add_inbound(self, port: int, remark: str) -> int:
        """VLESS + REALITY (TCP), как у рабочих серверов; цель — локальный TLS 1.3."""
        keys = subprocess.run(
            ["docker", "run", "--rm", "--entrypoint", "/app/bin/xray-linux-arm64", self.image,
             "x25519"], capture_output=True, text=True, check=True,
        ).stdout.splitlines()
        private = next(line.split(":", 1)[1].strip() for line in keys
                       if line.startswith("PrivateKey"))
        public = next(line.split(":", 1)[1].strip() for line in keys if "PublicKey" in line)
        reality = {
            "show": False, "xver": 0, "target": "files.acc.test:443",
            "serverNames": ["files.acc.test"], "privateKey": private,
            "minClientVer": "", "maxClientVer": "", "maxTimediff": 0,
            "shortIds": ["a1b2c3d4"],
            "settings": {"publicKey": public, "fingerprint": "chrome",
                         "serverName": "", "spiderX": "/"},
        }
        payload = {
            "up": 0, "down": 0, "total": 0, "remark": remark, "enable": True,
            "expiryTime": 0, "listen": "", "port": port, "protocol": "vless",
            "settings": json.dumps({"clients": [], "decryption": "none", "fallbacks": []}),
            "streamSettings": json.dumps({"network": "tcp", "security": "reality",
                                          "realitySettings": reality,
                                          "tcpSettings": {"header": {"type": "none"}}}),
            "sniffing": json.dumps({"enabled": False, "destOverride": []}),
        }
        async with self.api() as c:
            data = (await c._api("POST", "/panel/api/inbounds/add", json=payload)).json()
        assert data.get("success"), data
        return int(data["obj"]["id"])

    async def del_inbound(self, inbound_id: int) -> None:
        async with self.api() as c:
            data = (await c._api("POST", f"/panel/api/inbounds/del/{inbound_id}")).json()
        assert data.get("success"), data

    async def client(self, email: str) -> dict[str, Any] | None:
        """{'body': тело клиента, 'inboundIds': [...], 'traffic': client_traffics|None}."""
        async with self.api() as c:
            record = await c.get_client_record(email)
            if record is None:
                return None
            body = client_record_body(record) or {}
            traffic = await c.get_client_usage(str(body.get("email") or email))
        return {"body": body, "inboundIds": record.get("inboundIds") or [], "traffic": traffic}

    async def used(self, email: str) -> int:
        record = await self.client(email)
        traffic = (record or {}).get("traffic") or {}
        return int(traffic.get("up") or 0) + int(traffic.get("down") or 0)

    async def create_legacy_client(self, email: str, inbound_ids: list[int]) -> str:
        secret = str(uuid.uuid4())
        obj = build_client_record(client_uuid=secret, password=secret, email=email,
                                  sub_id=email, expiry_ms=0)
        async with self.api() as c:
            await c.create_client_record(obj, inbound_ids)
        return secret

    async def set_client_fields(self, email: str, **fields: Any) -> None:
        """Изменение клиента «вручную в панели» (тот же API, что у веб-интерфейса)."""
        async with self.api() as c:
            record = await c.get_client_record(email)
            body = dict(client_record_body(record) or {})
            body.update(fields)
            await c.update_client_record(email, sanitize_client_for_api(body))

    async def reset_traffic(self, email: str) -> None:
        async with self.api() as c:
            data = (await c._api("POST", f"/panel/api/clients/resetTraffic/{email}")).json()
        assert data.get("success"), data

    def xray_usage(self, email: str) -> int | None:
        """up+down из счётчиков самого Xray панели (statsquery), минуя учёт панели.

        Счётчики живут, пока жив процесс Xray: после его перезапуска — с нуля;
        до первого трафика пользователя счётчика нет (None).
        """
        proc = subprocess.run(
            ["docker", "exec", self.container, "/app/bin/xray-linux-arm64", "api", "statsquery",
             "--server=127.0.0.1:62789", f"-pattern=user>>>{email}>>>"],
            capture_output=True, text=True,
        )
        if proc.returncode:
            raise RuntimeError(f"statsquery: {proc.stderr.strip()[-300:]}")
        stats = json.loads(proc.stdout or "{}").get("stat") or []
        if not stats:
            return None
        return sum(int(s.get("value") or 0) for s in stats)

    def xray_age(self) -> float | None:
        """Сколько секунд работает процесс Xray панели."""
        out = subprocess.run(
            ["docker", "exec", self.container, "sh", "-c",
             "p=$(pgrep -f xray-linux | head -1); [ -n \"$p\" ] && "
             "echo $(cut -d' ' -f1 /proc/uptime) $(cut -d' ' -f22 /proc/$p/stat)"],
            capture_output=True, text=True,
        ).stdout.split()
        return float(out[0]) - int(out[1]) / 100 if len(out) == 2 else None

    def stop(self) -> None:
        subprocess.run(["docker", "stop", self.container], check=True, capture_output=True)

    def start(self) -> None:
        subprocess.run(["docker", "start", self.container], check=True, capture_output=True)


async def observe_d3(report: Report, panel: Panel, email: str, link: str | None, image: str,
                     network: str, context: str) -> tuple[bool, int]:
    """Наблюдение D-3: учла ли панель трафик, который видит сам Xray панели.

    D-3 — свойство 3x-ui, не бота (протокол ``docs/acceptance/xui_traffic_d3_2026-10-06.md``,
    сводка — ``docs/WHITELIST_SERVICE.md`` §9): трафик до первого опроса задачи трафика
    после запуска панели или после перезапуска Xray панель может не учесть. Результат
    записывается как наблюдение известного дефекта, а не как OK/FAIL. Ждёт не меньше
    двух опросов панели (5 с), поэтому после вызова база учёта панели заведомо
    установлена. Возвращает (загрузка прошла,
    не учтённые байты).
    """
    age = await asyncio.to_thread(panel.xray_age)
    xray_before = await asyncio.to_thread(panel.xray_usage, email) or 0
    used_before = await panel.used(email)
    ok, out = await asyncio.to_thread(probe, link or "", image, network)
    await asyncio.sleep(12)
    used_after = await panel.used(email)
    for _ in range(6):
        await asyncio.sleep(6)
        current = await panel.used(email)
        if current == used_after:
            break
        used_after = current
    xray = (await asyncio.to_thread(panel.xray_usage, email) or 0) - xray_before
    counted = used_after - used_before
    lost = xray - counted
    report.known_defect(
        "D-3", f"{context}: трафик учтён панелью", ok and lost > 0,
        f"загрузка {out} через {age:.1f} с после запуска Xray; Xray +{xray} Б, "
        f"панель +{counted} Б, не учтено {lost} Б" if age is not None else out,
    )
    return ok, lost


async def wait_until(predicate, timeout: float, interval: float = 2.0):
    deadline = time.monotonic() + timeout
    while True:
        value = await predicate()
        if value or time.monotonic() > deadline:
            return value
        await asyncio.sleep(interval)


class SubHub:
    def __init__(self, url: str, token: str) -> None:
        self.url, self.token = url.rstrip("/"), token

    async def sync(self) -> None:
        """Полная синхронизация с ожиданием её завершения."""
        headers = {"X-Admin-Token": self.token}
        async with httpx.AsyncClient(timeout=15) as http:
            for _ in range(30):
                # Метка до запроса: фоновая синхронизация может завершиться
                # раньше, чем клиент получит ответ 202.
                started = datetime.now(UTC).replace(tzinfo=None).isoformat()
                response = await http.post(f"{self.url}/admin/sync", headers=headers)
                # Нужен новый проход: «queued» (SubHub с 2026-10-05) или 409 (прежний
                # SubHub) — проход уже идёт и мог прочитать панели до изменений.
                if response.status_code == 202 and response.json().get("status") != "queued":
                    break
                await asyncio.sleep(1)
            for _ in range(60):
                servers = (await http.get(f"{self.url}/admin/servers", headers=headers)).json()
                if all((s["last_success_poll_at"] or "") >= started for s in servers):
                    return
                await asyncio.sleep(0.5)
        raise RuntimeError("SubHub не завершил синхронизацию")

    async def resolve(self, email: str) -> tuple[int, dict[str, Any]]:
        async with httpx.AsyncClient(timeout=15) as http:
            response = await http.post(
                f"{self.url}/admin/subscriptions/resolve",
                headers={"X-Admin-Token": self.token}, json={"email": email},
            )
        return response.status_code, (response.json() if response.content else {})

    async def tokens(self) -> dict[str, str]:
        async with httpx.AsyncClient(timeout=15) as http:
            rows = (await http.get(f"{self.url}/admin/clients",
                                   headers={"X-Admin-Token": self.token})).json()
        return {row["email"]: row["token"] for row in rows}

    async def links(self, token: str) -> list[str]:
        async with httpx.AsyncClient(timeout=15) as http:
            response = await http.get(f"{self.url}/connection/{token}")
        if response.status_code != 200:
            return []
        lines = base64.b64decode(response.text).decode().splitlines()
        return [line for line in lines if line.startswith("vless://")]


def link_for(links: list[str], host: str) -> str | None:
    return next((link for link in links if urlparse(link).hostname == host), None)


def xray_client_config(link: str) -> dict[str, Any]:
    """Конфигурация xray-клиента: SOCKS 127.0.0.1:10808 → VLESS по ссылке."""
    parsed = urlparse(link)
    query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    stream: dict[str, Any] = {"network": query.get("type", "tcp"),
                              "security": query.get("security", "none")}
    if stream["security"] == "reality":
        stream["realitySettings"] = {
            "serverName": query.get("sni", ""), "fingerprint": query.get("fp", "chrome"),
            "publicKey": query.get("pbk", ""), "shortId": query.get("sid", ""),
            "spiderX": query.get("spx", "/"),
        }
    return {
        "log": {"loglevel": "warning"},
        "inbounds": [{"listen": "127.0.0.1", "port": 10808, "protocol": "socks",
                      "settings": {"udp": False}}],
        "outbounds": [{
            "protocol": "vless",
            "settings": {"vnext": [{"address": parsed.hostname, "port": parsed.port,
                                    "users": [{"id": unquote(parsed.username or ""),
                                               "encryption": "none",
                                               "flow": query.get("flow", "")}]}]},
            "streamSettings": stream,
        }],
    }


def probe(link: str, image: str, network: str) -> tuple[bool, str]:
    """Настоящее VLESS-подключение xray по ссылке и загрузка 8 МиБ через него."""
    if not link:
        return False, "нет ссылки в подписке"
    config = xray_client_config(link)
    script = (
        "cat > /tmp/c.json; /app/bin/xray-linux-arm64 run -c /tmp/c.json >/tmp/x.log 2>&1 & "
        "sleep 1.5; curl -s -m 25 --socks5-hostname 127.0.0.1:10808 -o /dev/null "
        "-w '%{http_code} %{size_download}' http://files.acc.test/blob8m"
    )
    proc = subprocess.run(
        ["docker", "run", "--rm", "-i", "--network", network, "--entrypoint", "sh", image,
         "-c", script],
        input=json.dumps(config).encode(), capture_output=True, timeout=90,
    )
    out = proc.stdout.decode().strip()
    ok = out.startswith("200 ") and int(out.split()[1]) == BLOB
    return ok, out


# --- Бот -----------------------------------------------------------------------


class Bot:
    """Обработчики бота с сессией на каждое обновление, как у middleware."""

    def __init__(self, maker: async_sessionmaker, settings: Settings) -> None:
        self.maker = maker
        self.settings = settings
        self.tg = FakeBot()

    @asynccontextmanager
    async def session(self):
        async with self.maker() as session:
            yield session

    async def user(self, telegram_id: int, name: str, role=UserRole.USER) -> User:
        async with self.session() as s:
            user, _ = await UserRepository(s).get_or_create(telegram_id, name, name, role)
            await s.commit()
            return user

    async def reload(self, user: User) -> User:
        async with self.session() as s:
            return await s.get(User, user.id)

    async def admin_callback(self, handler, data, *, state: FakeState | None = None,
                             admin: User) -> FakeCallback:
        callback = FakeCallback(message=FakeMessage(bot=self.tg))
        async with self.session() as s:
            if handler is admin_handlers.on_payment_action:
                await handler(callback, data, s, admin, self.settings)
            else:
                await handler(callback, data, s, admin, self.settings, state or FakeState())
        return callback

    async def admin_text(self, handler, text: str, state: FakeState, admin: User) -> FakeMessage:
        message = FakeMessage(bot=self.tg, text=text)
        async with self.session() as s:
            if handler is admin_handlers.admin_add_server_line:
                await handler(message, s, state, self.settings, admin)
            else:
                await handler(message, s, state, admin)
        return message

    async def admin_command(self, handler, command: str, args: str, admin: User) -> FakeMessage:
        message = FakeMessage(bot=self.tg, text=f"/{command} {args}")
        async with self.session() as s:
            await handler(message, CommandObject(prefix="/", command=command, args=args), s,
                          admin, self.settings)
        return message

    async def add_server(self, admin: User, purpose_action: str, line: str) -> str:
        state = FakeState()
        callback = await self.admin_callback(
            admin_handlers.admin_nav, AdminCallback(action=purpose_action), state=state,
            admin=admin,
        )
        if callback.alerts and callback.alerts[-1]:
            return callback.alerts[-1]
        message = await self.admin_text(admin_handlers.admin_add_server_line, line, state, admin)
        return message.answers[-1]

    async def wl_admin(self, admin: User, action: str, value: int = 0) -> FakeCallback:
        return await self.admin_callback(
            admin_handlers.whitelist_admin, WhitelistAdminCallback(action=action, value=value),
            admin=admin,
        )

    async def wl_admin_value(self, admin: User, action: str, text: str, value: int = 0) -> str:
        state = FakeState()
        await self.admin_callback(
            admin_handlers.whitelist_admin, WhitelistAdminCallback(action=action, value=value),
            state=state, admin=admin,
        )
        message = await self.admin_text(admin_handlers.whitelist_value_input, text, state, admin)
        return message.answers[-1]

    async def receipt(self, user: User, state: FakeState) -> None:
        message = FakeMessage(bot=self.tg, text="Квитанция (тестовая, без оплаты)")
        async with self.session() as s:
            db_user = await s.get(User, user.id)
            await user_handlers.proof_text(message, s, db_user, self.settings, state)

    async def subscribe(self, user: User, days: int = 30, amount: float = 175) -> PaymentRequest:
        """Пользователь создаёт заявку на подписку и присылает квитанцию."""
        async with self.session() as s:
            payment = await payments.create_request(s, user.id, amount, days)
        await self.receipt(user, FakeState())
        return payment

    async def confirm(self, admin: User, payment_id: int, action: str = "confirm") -> FakeCallback:
        return await self.admin_callback(
            admin_handlers.on_payment_action, PaymentCallback(action=action, payment_id=payment_id),
            admin=admin,
        )

    async def trial(self, user: User) -> FakeCallback:
        callback = FakeCallback(message=FakeMessage(bot=self.tg))
        async with self.session() as s:
            db_user = await s.get(User, user.id)
            await user_handlers.select_plan(callback, PlanCallback(code="trial"), s, db_user,
                                            self.settings, FakeState())
        return callback

    async def wl_user(self, user: User, action: str = "home", value: int = 0,
                      state: FakeState | None = None) -> FakeCallback:
        callback = FakeCallback(message=FakeMessage(bot=self.tg))
        async with self.session() as s:
            db_user = await s.get(User, user.id)
            await user_handlers.whitelist_menu(
                callback, WhitelistCallback(action=action, value=value), s, db_user,
                self.settings, state or FakeState(),
            )
        return callback

    async def buy(self, user: User, package_id: int) -> tuple[FakeCallback, PaymentRequest | None]:
        state = FakeState()
        callback = await self.wl_user(user, "buy", package_id, state)
        if state.state is None:
            return callback, None
        await self.receipt(user, state)
        async with self.session() as s:
            payment = await s.scalar(
                select(PaymentRequest).where(PaymentRequest.user_id == user.id)
                .where(PaymentRequest.kind == PAYMENT_KIND_TRAFFIC)
                .order_by(PaymentRequest.id.desc())
            )
        return callback, payment

    async def account(self, user: User) -> WhitelistAccount | None:
        async with self.session() as s:
            return await whitelist.get_account(s, user.id)

    async def overview(self, user: User) -> whitelist.Overview:
        async with self.session() as s:
            return await whitelist.user_overview(s, user.id, build_updater(timeout=8))

    async def client(self, user: User) -> VpnClient | None:
        async with self.session() as s:
            return await VpnClientRepository(s).get_for_user(user.id)

    async def mapping(self, user: User) -> ClientServerMapping | None:
        async with self.session() as s:
            client = await VpnClientRepository(s).get_for_user(user.id)
            return await s.scalar(
                select(ClientServerMapping)
                .where(ClientServerMapping.vpn_client_id == client.id).limit(1)
            )

    async def ledger(self, user: User, kind: str | None = None) -> list[WhitelistLedger]:
        async with self.session() as s:
            query = select(WhitelistLedger).where(WhitelistLedger.user_id == user.id)
            if kind:
                query = query.where(WhitelistLedger.kind == kind)
            return list((await s.scalars(query.order_by(WhitelistLedger.id))).all())

    async def process_due(self) -> int:
        async with self.session() as s:
            return await whitelist.process_due(s, build_updater(timeout=8))

    async def reconcile(self) -> whitelist.ReconcileReport:
        async with self.session() as s:
            return await whitelist.reconcile_cycle(s, build_updater(timeout=8),
                                                   batch_size=100, pause_seconds=0)

    async def set_expiry(self, user: User, when: datetime) -> None:
        """Сдвиг срока в БД вместо ожидания реального окончания (минуты, а не дни)."""
        async with self.session() as s:
            client = await VpnClientRepository(s).get_for_user(user.id)
            client.expires_at = when
            await s.commit()


def ms(value: datetime | None) -> int:
    if value is None:
        return 0
    value = value if value.tzinfo else value.replace(tzinfo=UTC)
    return int(value.timestamp() * 1000)


def gb(value: int) -> str:
    return f"{value / GIB:.6f} ГиБ ({value} Б)"


# --- Сценарий ------------------------------------------------------------------


async def scenario(state: Path) -> None:
    env = load_env(state)
    image, network = env["XUI_IMAGE"], env["NET"]
    wl_panel = Panel(env["WL_PANEL"], env["XUI_USER"], env["XUI_PASS"], "wlacc-xui-wl", image)
    std_panel = Panel(env["STD_PANEL"], env["XUI_USER"], env["XUI_PASS"], "wlacc-xui-std", image)
    subhub = SubHub(env["SUBHUB_URL"], env["SUBHUB_ADMIN_TOKEN"])

    R.start("Подготовка стенда")
    versions = subprocess.run(
        ["docker", "exec", "wlacc-xui-wl", "/app/x-ui", "-v"], capture_output=True, text=True
    ).stdout.strip()
    R.fact("3x-ui", versions or "v3.9.0")
    for panel in (std_panel, wl_panel):
        if await panel.allow_private_targets():
            await asyncio.sleep(3)  # перезапуск xray после смены шаблона
    std_inbound = await std_panel.ensure_inbound(20444, "Обычный")
    wl_inbound = await wl_panel.ensure_inbound(20443, "Обход белых списков")
    R.fact("inbound обычной панели", std_inbound)
    R.fact("inbound whitelist-панели", wl_inbound)

    pg_base = env["PG_URL"]
    conn = await asyncpg.connect(pg_base.replace("+asyncpg", "") + "/postgres")
    await conn.execute('DROP DATABASE IF EXISTS "wlacc_e2e" WITH (FORCE)')
    await conn.execute('CREATE DATABASE "wlacc_e2e"')
    await conn.close()
    db_url = pg_base + "/wlacc_e2e"
    migrate = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT,
        env=dict(os.environ, DATABASE_URL=db_url, BOT_TOKEN="acceptance"),
        capture_output=True, text=True,
    )
    R.check("alembic upgrade head на пустой PostgreSQL 16", migrate.returncode == 0,
            migrate.stderr.strip().splitlines()[-1] if migrate.stderr else "")
    engine = create_async_engine(db_url)
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    settings = Settings(
        bot_token="acceptance", admin_telegram_ids=[ADMIN_TG], database_url=db_url,
        subhub_url=env["SUBHUB_URL"], subhub_admin_token=env["SUBHUB_ADMIN_TOKEN"],
        subhub_timeout_seconds=10, xui_request_timeout=8, trial_period_days=3,
        payment_details_text="Тестовые реквизиты (оплаты нет)",
    )
    bot = Bot(maker, settings)
    async with bot.session() as s:
        await whitelist.ensure_defaults(s)  # как при старте app.main
    admin = await bot.user(ADMIN_TG, "admin", UserRole.ADMIN)

    # --- Обычный сервер и пользователи до запуска услуги -------------------------
    R.start("Обычный сервер и пользователи до запуска услуги")
    answer = await bot.add_server(
        admin, "add_standard",
        f"Обычный|FI|{env['STD_PANEL']}|{env['XUI_USER']}|{env['XUI_PASS']}|direct",
    )
    R.check("обычный сервер добавлен через бота и импортировал inbound",
            "добавлен" in answer and str(std_inbound) in answer, answer.splitlines()[0])

    paid = await bot.user(700002, "paid")
    trial = await bot.user(700003, "trial")
    lifetime = await bot.user(700004, "lifetime")
    payment = await bot.subscribe(paid)
    callback = await bot.confirm(admin, payment.id)
    paid_client = await bot.client(paid)
    R.check("оплата подписки (регрессия): срок выдан, клиент на обычной панели",
            paid_client is not None and paid_client.is_active
            and (await std_panel.client(paid.public_id)) is not None,
            callback.message.edits[-1].splitlines()[0] if callback.message.edits else "")
    R.check("до запуска услуги оплата не создаёт учёт и пакет",
            await bot.account(paid) is None)
    callback = await bot.trial(trial)
    trial_client = await bot.client(trial)
    R.check("trial (регрессия): срок 3 дня, клиент на обычной панели",
            trial_client is not None and trial_client.is_active
            and (await std_panel.client(trial.public_id)) is not None,
            callback.message.edits[-1].splitlines()[0] if callback.message.edits else "")

    await subhub.sync()
    status, resolved = await subhub.resolve(paid.public_id)
    token_before = (await subhub.tokens()).get(paid.public_id.casefold())
    links_before = await subhub.links(token_before) if token_before else []
    R.check("SubHub до услуги: одна ссылка, один обычный конфиг",
            status == 200 and len(links_before) == 1
            and link_for(links_before, "std.acc.test") is not None,
            f"HTTP {status}, конфигов {len(links_before)}")
    R.fact("подписка оплаченного (url)", resolved.get("subscription_url", "—"))
    ok, out = probe(link_for(links_before, "std.acc.test"), image, network)
    R.check("обычный конфиг из подписки реально передаёт трафик", ok, out)

    # --- Добавление whitelist-сервера и первичная синхронизация ------------------
    R.start("Добавление сервера услуги и первичная синхронизация inbound")
    wl_panel.stop()
    line = (f"Обход белых списков|LV|{env['WL_PANEL']}|{env['XUI_USER']}|{env['XUI_PASS']}"
            "|direct")
    answer = await bot.add_server(admin, "add_whitelist", line)
    async with bot.session() as s:
        server = await whitelist.get_active_server(s)
    R.check("панель недоступна: ошибка видна администратору, сервер не готов",
            server is not None and not whitelist.server_ready(server)
            and server.inventory_status == whitelist.INVENTORY_ERROR,
            answer.replace("\n", " ")[:200])
    async with bot.session() as s:
        try:
            await whitelist.run_rollout(s, build_updater(), include_ambiguous=False,
                                        actor_user_id=admin.id)
            refused = False
        except whitelist.WhitelistError:
            refused = True
    R.check("выдача невозможна, пока сервер не готов", refused)
    callback = await bot.add_server(admin, "add_whitelist", line)
    R.check("второй включённый сервер услуги не добавляется", "Уже есть" in callback, callback)

    wl_panel.start()
    await wait_until(lambda: _panel_up(wl_panel), 40)
    extra = await wl_panel.add_inbound(20445, "лишний")
    callback = await bot.wl_admin(admin, "sync")
    async with bot.session() as s:
        server = await whitelist.get_active_server(s)
    R.check("два inbound: расхождение показано, сервер ждёт выбора",
            server.inventory_status == whitelist.INVENTORY_NEEDS_CHOICE
            and not whitelist.server_ready(server), callback.alerts[-1])
    await bot.wl_admin(admin, "choose", wl_inbound)
    async with bot.session() as s:
        server = await whitelist.get_active_server(s)
    R.check("выбран единственный целевой inbound", whitelist.server_ready(server)
            and whitelist.target_inbound(server).inbound_id == wl_inbound)
    await wl_panel.del_inbound(extra)
    for attempt in (1, 2):
        callback = await bot.wl_admin(admin, "sync")
        async with bot.session() as s:
            server = await whitelist.get_active_server(s)
            target = whitelist.target_inbound(server)
            rows = len(server.inbounds)
        R.check(f"повтор синхронизации #{attempt}: готов, цель {wl_inbound}, реестр сверен",
                whitelist.server_ready(server) and target.inbound_id == wl_inbound,
                f"{callback.alerts[-1]}; строк реестра {rows}")
    R.check("до выдачи на whitelist-панели нет клиентов",
            await wl_panel.client(paid.public_id) is None)

    # --- Бессрочный пользователь через привязку ------------------------------------
    R.start("Привязка бессрочной подписки (после добавления сервера услуги)")
    life_email = "LIFEACC0001"
    await std_panel.create_legacy_client(life_email, [std_inbound])
    async with bot.session() as s:
        request = await bind_requests.create_request(
            s, await s.get(User, lifetime.id), f"https://old.example.test/sub/{life_email}"
        )
    async with bot.session() as s:
        result = await bind_requests.approve_request(
            s, request.id, actor_user_id=admin.id, updater=build_updater(timeout=8)
        )
    life_client = await bot.client(lifetime)
    R.check("привязка (регрессия): бессрочный доступ без роли администратора",
            result.applied and life_client is not None and life_client.expires_at is None
            and (await bot.reload(lifetime)).role == UserRole.USER)
    R.check("привязка не создала клиента на whitelist-панели",
            await wl_panel.client(life_email) is None)

    # --- Выдача нынешним пользователям -------------------------------------------
    R.start("Выдача услуги нынешним пользователям")
    callback = await bot.wl_admin(admin, "rollout")
    async with bot.session() as s:
        plan = await whitelist.rollout_plan(s)
    R.check("план: оплаченный, trial, бессрочный",
            plan.counts == {"paid": 1, "trial": 1, "lifetime": 1}, plan.counts)
    await bot.wl_admin(admin, "rollout_strict")
    for _ in range(3):
        await bot.process_due()
    await subhub.sync()
    expectations = [
        (paid, 10 * GIB, ms((await bot.client(paid)).expires_at)),
        (trial, 3 * GIB, ms((await bot.client(trial)).expires_at)),
        (lifetime, 0, 0),
    ]
    for user, total, expiry in expectations:
        mapping = await bot.mapping(user)
        record = await wl_panel.client(mapping.email)
        body = (record or {}).get("body") or {}
        R.check(
            f"{user.username}: totalGB={total} Б, expiryTime={expiry}, enable",
            record is not None and body.get("totalGB") == total
            and body.get("expiryTime") == expiry and body.get("enable") is True,
            f"totalGB={body.get('totalGB')} expiryTime={body.get('expiryTime')} "
            f"enable={body.get('enable')}",
        )
        R.check(
            f"{user.username}: идентичность = обычная подписка (UUID, subId, email, tgId), "
            "целевой inbound, автосбросы выключены",
            record is not None and body.get("uuid") == mapping.client_uuid
            and body.get("subId") == (mapping.sub_id or mapping.email)
            and body.get("email") == mapping.email
            and int(body.get("tgId") or 0) == user.telegram_id
            and record["inboundIds"] == [wl_inbound]
            and body.get("reset", 0) == 0 and body.get("trafficReset") in (None, "never"),
            f"tgId={body.get('tgId')} inbound={record and record['inboundIds']} "
            f"trafficReset={body.get('trafficReset')}",
        )
        std_record = await std_panel.client(mapping.email)
        R.check(f"{user.username}: обычный конфиг остался безлимитным (totalGB=0)",
                std_record is not None and std_record["body"].get("totalGB") == 0)
    ledger_before = sum([len(await bot.ledger(u)) for u, *_ in expectations])
    await bot.wl_admin(admin, "rollout_all")
    await bot.process_due()
    ledger_after = sum([len(await bot.ledger(u)) for u, *_ in expectations])
    record = await wl_panel.client(paid.public_id)
    R.check("повторная выдача идемпотентна: журнал и квоты не изменились",
            ledger_after == ledger_before and record["body"]["totalGB"] == 10 * GIB,
            f"строк журнала {ledger_before}→{ledger_after}")

    token_after = (await subhub.tokens()).get(paid.public_id.casefold())
    links_after = await subhub.links(token_after)
    wl_link = link_for(links_after, "wl.acc.test")
    R.check("SubHub: та же ссылка (токен), добавлен конфиг «Обход белых списков»",
            token_after == token_before and len(links_after) == 2 and wl_link is not None
            and "Обход белых списков" in unquote(wl_link.split("#", 1)[-1]),
            unquote(wl_link.split("#", 1)[-1]) if wl_link else "нет")
    life_token = (await subhub.tokens()).get(life_email.casefold())
    R.check("SubHub: бессрочному добавлен конфиг в ту же ссылку",
            life_token is not None
            and link_for(await subhub.links(life_token), "wl.acc.test") is not None)

    # --- Реальный трафик: учёт и списание сначала бесплатного --------------------
    R.start("Реальный трафик через конфиг услуги")
    # Тест недоступности выше перезапустил whitelist-панель. Первый трафик после
    # этого идёт через безлимитный конфиг бессрочного пользователя: это наблюдение
    # D-3 (учёт 3x-ui), отдельно от проверок. observe_d3 ждёт два опроса панели,
    # поэтому следующие проверки учёта идут уже после установки её базы — эта
    # загрузка служит им прогревом и обозначена в отчёте.
    life_wl = link_for(await subhub.links(life_token), "wl.acc.test")
    await observe_d3(R, wl_panel, life_email, life_wl, image, network,
                     "первый трафик после перезапуска whitelist-панели")
    R.warmup("загрузка бессрочного выше (наблюдение D-3) — первый трафик после перезапуска "
             "панели; проверки учёта ниже выполняются после двух опросов панели")
    overview = await bot.overview(lifetime)
    R.check("бессрочный: расход не ограничивает конфиг (totalGB=0, включён)",
            overview.status == whitelist.STATUS_LIFETIME
            and (await wl_panel.client(life_email))["body"]["totalGB"] == 0)
    ok, out = probe(wl_link, image, network)
    R.check("конфиг услуги из подписки передаёт трафик (8 МиБ)", ok, out)
    used = await wait_until(lambda: _used_at_least(wl_panel, paid.public_id, BLOB), 60) or 0
    R.fact("расход оплаченного на панели (up+down)", used)
    callback = await bot.wl_user(paid)
    account = await bot.account(paid)
    R.check("бот сверил расход: бесплатный уменьшился ровно на расход панели",
            used and account.free_bytes == 10 * GIB - used and account.paid_bytes == 0,
            gb(account.free_bytes))
    screen = callback.message.edits[-1]
    R.check("экран пользователя: остатки раздельно, без внутренних терминов",
            "Бесплатный остаток" in screen and "Купленный остаток" in screen
            and not any(t in screen.lower() for t in ("ledger", "checkpoint", "totalgb")),
            screen.replace("\n", " | ")[:300])

    # --- Пакеты и объёмы, исчерпание квоты ---------------------------------------
    R.start("Исчерпание квоты останавливает только конфиг услуги")
    answer = await bot.wl_admin_value(admin, "free_paid", SMALL_GB)
    R.check("администратор изменил бесплатный объём за оплату", "Сохранено" in answer)
    answer = await bot.wl_admin_value(admin, "pkg_add", f"{SMALL_GB} 1")
    async with bot.session() as s:
        small_pkg = await s.scalar(select(TrafficPackage)
                                   .where(TrafficPackage.traffic_bytes == SMALL))
    R.check("администратор создал тестовый пакет", small_pkg is not None, answer.splitlines()[0])
    small = await bot.user(700006, "small")
    payment = await bot.subscribe(small)
    await bot.confirm(admin, payment.id)
    await subhub.sync()
    small_email = (await bot.mapping(small)).email
    record = await wl_panel.client(small_email)
    R.check("новая оплата получает новый объём (применяется к следующей выдаче)",
            record is not None and record["body"]["totalGB"] == SMALL
            and (await bot.account(small)).free_bytes == SMALL,
            gb(record["body"]["totalGB"]) if record else "нет клиента")
    small_token = (await subhub.tokens()).get(small_email.casefold())
    small_links = await subhub.links(small_token)
    small_wl, small_std = link_for(small_links, "wl.acc.test"), link_for(small_links,
                                                                          "std.acc.test")
    outcomes = [probe(small_wl, image, network) for _ in range(3)]
    R.fact("три загрузки по 8 МиБ через конфиг услуги", [o for _, o in outcomes])
    disabled = await wait_until(lambda: _disabled(wl_panel, small_email), 60)
    record = await wl_panel.client(small_email)
    used = await wl_panel.used(small_email)
    R.check("панель отключила конфиг услуги по исчерпанию квоты",
            disabled and used >= SMALL, f"расход {used} Б, лимит {SMALL} Б")
    ok, out = probe(small_wl, image, network)
    R.check("конфиг услуги больше не передаёт трафик", not ok, out)
    ok, out = probe(small_std, image, network)
    R.check("обычный конфиг того же пользователя продолжает работать", ok, out)
    overview = await bot.overview(small)
    R.check("пользователь видит исчерпание; остатки 0 + 0",
            overview.status == whitelist.STATUS_EXHAUSTED
            and (overview.free_bytes, overview.paid_bytes) == (0, 0), overview.status)
    await bot.process_due()
    record = await wl_panel.client(small_email)
    R.check("повтор очереди не включает и не делает квоту безлимитной (totalGB≠0)",
            record["body"]["enable"] is False and record["body"]["totalGB"] >= SMALL,
            f"enable={record['body']['enable']} totalGB={record['body']['totalGB']}")
    await subhub.sync()
    links = await subhub.links(small_token)
    R.check("SubHub: исчерпанный конфиг услуги скрыт, обычный остался",
            link_for(links, "wl.acc.test") is None and link_for(links, "std.acc.test"))

    R.start("Покупка пакета возобновляет конфиг; сначала бесплатный, затем купленный")
    callback, purchase = await bot.buy(small, small_pkg.id)
    R.check("заявка создана при активной подписке, квитанция принята",
            purchase is not None and purchase.status == PaymentStatus.WAITING_ADMIN
            and purchase.traffic_bytes == SMALL)
    expires_before = (await bot.client(small)).expires_at
    callback = await bot.confirm(admin, purchase.id)
    again = await bot.confirm(admin, purchase.id)
    account = await bot.account(small)
    record = await wl_panel.client(small_email)
    used = await wl_panel.used(small_email)
    R.check("начислен только купленный объём; срок и бесплатный не изменились",
            account.paid_bytes == SMALL and account.free_bytes == 0
            and (await bot.client(small)).expires_at == expires_before,
            f"{gb(account.free_bytes)} + {gb(account.paid_bytes)}")
    R.check("повторное подтверждение ничего не начисляет",
            again.alerts[-1] == "Заявка уже применена ранее"
            and len(await bot.ledger(small, "purchase")) == 1, again.alerts[-1])
    R.check("панель: квота = расход + купленное, конфиг включён",
            record["body"]["enable"] is True and record["body"]["totalGB"] == used + SMALL,
            f"totalGB={record['body']['totalGB']} used={used}")
    ok, out = probe(small_wl, image, network)
    R.check("после покупки конфиг услуги снова передаёт трафик", ok, out)
    used2 = await wait_until(lambda: _used_at_least(wl_panel, small_email, used + BLOB), 60) or used
    account = (await bot.overview(small), await bot.account(small))[1]
    R.check("расход после покупки списан с купленного",
            account.free_bytes == 0 and account.paid_bytes == SMALL - (used2 - used),
            f"{gb(account.free_bytes)} + {gb(account.paid_bytes)}")
    paid_before_renewal = account.paid_bytes

    payment = await bot.subscribe(small)
    await bot.confirm(admin, payment.id)
    account = await bot.account(small)
    R.check("продление: бесплатный := настроенный объём, купленный сохранён",
            account.free_bytes == SMALL and account.paid_bytes == paid_before_renewal,
            f"{gb(account.free_bytes)} + {gb(account.paid_bytes)}")
    base_used = await wl_panel.used(small_email)
    ok, out = probe(small_wl, image, network)
    used3 = await wait_until(
        lambda: _used_at_least(wl_panel, small_email, base_used + BLOB), 60
    ) or base_used
    await bot.overview(small)
    account = await bot.account(small)
    spent = used3 - base_used
    R.check("при двух остатках расход идёт сначала с бесплатного",
            account.free_bytes == SMALL - spent and account.paid_bytes == paid_before_renewal,
            f"расход {spent} Б → {gb(account.free_bytes)} + {gb(account.paid_bytes)}")

    # --- Покупка только при активной подписке ------------------------------------
    R.start("Покупка только при активной подписке")
    stranger = await bot.user(700009, "nosub")
    callback, created = await bot.buy(stranger, small_pkg.id)
    R.check("без подписки заявка не создаётся", created is None, callback.alerts[-1])
    callback, created = await bot.buy(lifetime, small_pkg.id)
    R.check("бессрочному покупка не нужна — заявка не создаётся", created is None,
            callback.alerts[-1])

    # --- Истечение подписки ---------------------------------------------------------
    R.start("Истечение подписки останавливает все конфиги; покупка после истечения")
    callback, late_purchase = await bot.buy(small, small_pkg.id)
    R.check("заявка создана, пока подписка активна", late_purchase is not None)
    await bot.overview(small)
    paid_at_expiry = (await bot.account(small)).paid_bytes
    expire_at = datetime.now(UTC) + timedelta(seconds=45)
    await bot.set_expiry(small, expire_at)
    message = await bot.admin_command(admin_handlers.sync_user, "sync", str(small.telegram_id),
                                      admin)
    R.check("/sync перенёс срок на обе панели",
            (await std_panel.client(small_email))["body"]["expiryTime"] == ms(expire_at)
            and (await wl_panel.client(small_email))["body"]["expiryTime"] == ms(expire_at),
            message.answers[-1])
    await asyncio.sleep(max(0.0, (expire_at - datetime.now(UTC)).total_seconds()) + 1)
    std_off = await wait_until(lambda: _disabled(std_panel, small_email), 90)
    wl_off = await wait_until(lambda: _disabled(wl_panel, small_email), 90)
    R.check("после срока панели отключили оба конфига", std_off and wl_off)
    ok_std, out_std = probe(small_std, image, network)
    ok_wl, out_wl = probe(small_wl, image, network)
    R.check("ни обычный, ни конфиг услуги не передают трафик", not ok_std and not ok_wl,
            f"обычный {out_std}; услуга {out_wl}")
    overview = await bot.overview(small)
    R.check("пользователь видит «подписка истекла», купленный остаток сохранён",
            overview.status == whitelist.STATUS_EXPIRED
            and overview.paid_bytes == paid_at_expiry and not overview.can_buy,
            gb(overview.paid_bytes))
    callback = await bot.wl_user(small)
    R.check("экран истёкшей подписки объясняет недоступность до продления",
            "после продления" in callback.message.edits[-1])
    callback = await bot.confirm(admin, late_purchase.id)
    account = await bot.account(small)
    record = await wl_panel.client(small_email)
    notice = [m["text"] for m in bot.tg.messages if m.get("chat_id") == small.telegram_id][-1]
    R.check("подтверждение после истечения начисляет оплаченный объём",
            account.paid_bytes == paid_at_expiry + SMALL,
            f"{gb(paid_at_expiry)} → {gb(account.paid_bytes)}")
    R.check("…и не включает конфиг услуги", record["body"]["enable"] is False,
            f"enable={record['body']['enable']}")
    R.fact("уведомление пользователю о покупке после истечения", notice.replace("\n", " | "))
    await subhub.sync()
    status, _ = await subhub.resolve(small_email)
    R.check("SubHub: у истёкшей подписки нет активных конфигов", status == 409, f"HTTP {status}")
    payment = await bot.subscribe(small)
    await bot.confirm(admin, payment.id)
    await subhub.sync()
    account = await bot.account(small)
    links = await subhub.links(small_token)
    ok_std, out_std = probe(link_for(links, "std.acc.test"), image, network)
    ok_wl, out_wl = probe(link_for(links, "wl.acc.test"), image, network)
    R.check("после продления оба конфига работают, купленный остаток сохранён",
            ok_std and ok_wl and account.paid_bytes == paid_at_expiry + SMALL,
            f"обычный {out_std}; услуга {out_wl}; купленный {gb(account.paid_bytes)}")

    # --- Оплата на 180 дней и ручное продление -----------------------------------
    R.start("Оплата на несколько месяцев и ручное продление")
    await bot.wl_admin_value(admin, "free_paid", "10")
    late = await bot.user(700005, "late")
    payment = await bot.subscribe(late, days=180, amount=850)
    await bot.confirm(admin, payment.id)
    late_email = (await bot.mapping(late)).email
    record = await wl_panel.client(late_email)
    grants = await bot.ledger(late, whitelist.LEDGER_FREE_GRANT)
    R.check("180 дней — один пакет 10 ГиБ", len(grants) == 1
            and record["body"]["totalGB"] == 10 * GIB, gb(record["body"]["totalGB"]))
    await bot.process_due()
    await bot.reconcile()
    R.check("очередь и фоновая сверка не выдают пакет повторно",
            len(await bot.ledger(late, whitelist.LEDGER_FREE_GRANT)) == 1)
    await subhub.sync()
    late_token = (await subhub.tokens()).get(late_email.casefold())
    late_wl = link_for(await subhub.links(late_token), "wl.acc.test")
    probe(late_wl, image, network)
    await wait_until(lambda: _used_at_least(wl_panel, late_email, BLOB), 60)
    await bot.overview(late)
    free_before_extend = (await bot.account(late)).free_bytes
    message = await bot.admin_command(admin_handlers.manual_extend, "extend",
                                      f"{late.telegram_id} 30", admin)
    client = await bot.client(late)
    record = await wl_panel.client(late_email)
    R.check("/extend переносит новый срок на конфиг услуги",
            record["body"]["expiryTime"] == ms(client.expires_at), message.answers[-1])
    R.check("…и не выдаёт пакет и не сбрасывает бесплатный остаток",
            len(await bot.ledger(late, whitelist.LEDGER_FREE_GRANT)) == 1
            and (await bot.account(late)).free_bytes == free_before_extend,
            gb(free_before_extend))

    # --- Административная блокировка и ручное отключение в панели ----------------
    R.start("Административная блокировка")
    await bot.wl_admin(admin, "block", paid.id)
    record = await wl_panel.client(paid.public_id)
    R.check("блокировка отключает конфиг услуги на панели", record["body"]["enable"] is False)
    await bot.overview(paid)
    await bot.process_due()
    await bot.reconcile()
    record = await wl_panel.client(paid.public_id)
    R.check("чтение баланса, очередь и сверка не включают заблокированного",
            record["body"]["enable"] is False)
    ok, out = probe(link_for(await subhub.links(token_after), "std.acc.test"), image, network)
    R.check("обычный конфиг заблокированного в услуге работает", ok, out)
    await bot.wl_admin(admin, "unblock", paid.id)
    record = await wl_panel.client(paid.public_id)
    R.check("разблокировка включает конфиг", record["body"]["enable"] is True)

    await wl_panel.set_client_fields(late_email, enable=False, comment="отключён вручную")
    await bot.overview(late)
    account = await bot.account(late)
    await bot.process_due()
    record = await wl_panel.client(late_email)
    R.check("ручное отключение в панели распознано как блокировка и не снимается",
            account.admin_blocked and record["body"]["enable"] is False,
            account.conflict)
    await bot.wl_admin(admin, "unblock", late.id)
    record = await wl_panel.client(late_email)
    R.check("после разблокировки клиент включён, поле comment из панели сохранено",
            record["body"]["enable"] is True
            and record["body"].get("comment") == "отключён вручную",
            record["body"].get("comment"))

    # --- Сброс счётчика на панели ----------------------------------------------
    R.start("Сброс счётчика на панели")
    await bot.overview(paid)
    before = await bot.account(paid)
    await wl_panel.reset_traffic(paid.public_id)
    await bot.overview(paid)
    after = await bot.account(paid)
    rebase = await bot.ledger(paid, whitelist.LEDGER_REBASE)
    await bot.process_due()
    record = await wl_panel.client(paid.public_id)
    R.check("сброс не превращается в новый трафик: остатки те же, конфликт записан",
            (after.free_bytes, after.paid_bytes) == (before.free_bytes, before.paid_bytes)
            and after.conflict and len(rebase) == 1,
            f"{gb(before.free_bytes)} → {gb(after.free_bytes)}")
    R.check("квота пересчитана от нового счётчика (старая база не стала трафиком)",
            record["body"]["totalGB"] == await wl_panel.used(paid.public_id)
            + after.free_bytes + after.paid_bytes, record["body"]["totalGB"])

    # --- Недоступная панель, повторные события, рестарт ---------------------------
    R.start("Недоступная панель, повтор подтверждения и рестарт процесса")
    package10 = await _package(bot, 10 * GIB)
    callback, outage_purchase = await bot.buy(late, package10.id)
    paid_before = (await bot.account(late)).paid_bytes
    wl_panel.stop()
    renewal = await bot.subscribe(paid)
    renewal_cb = await bot.confirm(admin, renewal.id)
    callback = await bot.confirm(admin, outage_purchase.id)
    again = await bot.confirm(admin, outage_purchase.id, "retry")
    async with bot.session() as s:
        stored = await s.get(PaymentRequest, outage_purchase.id)
        card = texts.admin_payment_card(stored, await s.get(User, late.id))
    overview = await bot.overview(late)
    R.check("покупка при недоступной панели сохранена и ждёт применения",
            stored.status == PaymentStatus.APPLIED and stored.apply_pending_version is not None,
            callback.message.edits[-1].splitlines()[0])
    R.check("администратор видит «ожидается применение»", "ожидается" in card)
    R.check("пользователь видит устаревшие данные и ожидание, не новый расход",
            overview.stale and overview.pending, f"stale={overview.stale}")
    R.check("повтор/ретрай не начисляют повторно",
            len(await bot.ledger(late, whitelist.LEDGER_PURCHASE)) == 1, again.alerts[-1:])
    renewal_client = await bot.client(paid)
    R.check("продление при недоступной whitelist-панели: обычная панель обновлена",
            (await std_panel.client(paid.public_id))["body"]["expiryTime"]
            == ms(renewal_client.expires_at),
            renewal_cb.message.edits[-1].splitlines()[0])
    await engine.dispose()  # «рестарт процесса»: новое подключение, новая очередь

    wl_panel.start()
    await wait_until(lambda: _panel_up(wl_panel), 40)
    engine = create_async_engine(db_url)
    bot.maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with bot.session() as s:
        await whitelist.ensure_defaults(s)
        await s.execute(
            WhitelistAccount.__table__.update().values(next_sync_at=None)
        )  # не ждать backoff в тесте
        await s.commit()
        await billing.recover_confirmed_payments(s, build_updater(timeout=8))
    applied = 0
    for _ in range(3):
        applied += await bot.process_due()
    async with bot.session() as s:
        stored = await s.get(PaymentRequest, outage_purchase.id)
    account = await bot.account(late)
    record = await wl_panel.client(late_email)
    R.check("после восстановления очередь применила покупку ровно один раз",
            account.paid_bytes == paid_before + 10 * GIB
            and stored.apply_pending_version is None
            and len(await bot.ledger(late, whitelist.LEDGER_PURCHASE)) == 1,
            f"применено {applied}; купленный {gb(account.paid_bytes)}")
    R.check("панель: квота = расход + остатки",
            record["body"]["totalGB"] == await wl_panel.used(late_email)
            + account.free_bytes + account.paid_bytes)
    paid_account = await bot.account(paid)
    record = await wl_panel.client(paid.public_id)
    R.check("продление во время сбоя: пакет выдан после сверки, срок применён",
            paid_account.free_bytes == 10 * GIB
            and record["body"]["expiryTime"] == ms((await bot.client(paid)).expires_at)
            and len(await bot.ledger(paid, whitelist.LEDGER_FREE_GRANT)) == 1,
            gb(paid_account.free_bytes))

    # --- Конкуренция на реальном стеке --------------------------------------------
    R.start("Конкуренция на PostgreSQL и реальной панели")
    # У пользователя одна открытая заявка с квитанцией, поэтому гонки — это
    # двойные нажатия администратора, повтор, очередь, фоновая сверка и чтение.
    callback, race_purchase = await bot.buy(late, package10.id)
    paid_before = (await bot.account(late)).paid_bytes
    purchases_before = len(await bot.ledger(late, whitelist.LEDGER_PURCHASE))

    async def queue_and_reads():
        await bot.process_due()
        await bot.reconcile()
        await bot.overview(late)

    results = await asyncio.gather(
        bot.confirm(admin, race_purchase.id),
        bot.confirm(admin, race_purchase.id),
        bot.confirm(admin, race_purchase.id, "retry"),
        queue_and_reads(), queue_and_reads(),
        return_exceptions=True,
    )
    errors = [r for r in results if isinstance(r, Exception)]
    account = await bot.account(late)
    R.check("покупка: двойное нажатие, retry, очередь, сверка и чтение параллельно — "
            "начислено ровно один раз", not errors
            and account.paid_bytes == paid_before + 10 * GIB
            and len(await bot.ledger(late, whitelist.LEDGER_PURCHASE)) == purchases_before + 1,
            f"ошибки {errors[:1]}; купленный {gb(account.paid_bytes)}")

    renewal = await bot.subscribe(late)
    async with bot.session() as s:
        renewal_kind = (await s.get(PaymentRequest, renewal.id)).kind
    expires_before = (await bot.client(late)).expires_at
    grants_before = len(await bot.ledger(late, whitelist.LEDGER_FREE_GRANT))
    results = await asyncio.gather(
        bot.confirm(admin, renewal.id), bot.confirm(admin, renewal.id),
        bot.confirm(admin, renewal.id, "retry"), queue_and_reads(),
        return_exceptions=True,
    )
    errors = [r for r in results if isinstance(r, Exception)]
    account = await bot.account(late)
    client = await bot.client(late)
    record = await wl_panel.client(late_email)
    R.check("продление: двойное нажатие, retry и очередь параллельно — один срок, один пакет",
            not errors and renewal_kind == "subscription"
            and (client.expires_at - expires_before) == timedelta(days=30)
            and len(await bot.ledger(late, whitelist.LEDGER_FREE_GRANT)) == grants_before + 1
            and account.paid_bytes == paid_before + 10 * GIB,
            f"срок +{client.expires_at - expires_before}; купленный {gb(account.paid_bytes)}")
    R.check("панель согласована с итоговым состоянием",
            record["body"]["totalGB"] == await wl_panel.used(late_email)
            + account.free_bytes + account.paid_bytes
            and record["body"]["expiryTime"] == ms(client.expires_at))

    # --- D-1 (исправлен 2026-10-05): выбор тарифа при ожидающей покупке трафика ----
    R.start("Заявка на подписку при ожидающей проверки покупке трафика")
    callback, pending_purchase = await bot.buy(late, package10.id)

    async def request_state(payment_id: int) -> tuple:
        async with bot.session() as s:
            p = await s.get(PaymentRequest, payment_id)
            proofs = len((await s.execute(
                select(PaymentAttachment.id)
                .where(PaymentAttachment.payment_request_id == payment_id)
            )).all())
            return (p.kind, str(p.amount), p.period_days, p.traffic_bytes,
                    p.traffic_package_id, p.status, proofs)

    state_before = await request_state(pending_purchase.id)
    plan_state = FakeState()
    plan_cb = FakeCallback(message=FakeMessage(bot=bot.tg))
    async with bot.session() as s:
        await user_handlers.select_plan(plan_cb, PlanCallback(code="1m"), s,
                                        await s.get(User, late.id), settings, plan_state)
    async with bot.session() as s:
        open_requests = [
            (p.id, p.kind) for p in (await s.scalars(
                select(PaymentRequest).where(PaymentRequest.user_id == late.id)
                .where(PaymentRequest.status.in_(
                    [PaymentStatus.CREATED, PaymentStatus.WAITING_ADMIN]))
            )).all()
        ]
    alert = (plan_cb.alerts or [""])[-1] or ""
    R.check("выбор «1 месяц» отказан: заявка на трафик на проверке, новая не создана",
            pending_purchase is not None
            and "на проверке" in alert and pending_purchase.payment_code in alert
            and "трафик" in alert.lower()
            and not plan_cb.message.edits
            and open_requests == [(pending_purchase.id, PAYMENT_KIND_TRAFFIC)],
            f"ответ: {alert[:100]}; открытые заявки: {open_requests}")
    R.check("заявка на трафик не изменена (вид, сумма, объём, срок, квитанция), "
            "квитанции больше не ожидаются",
            await request_state(pending_purchase.id) == state_before
            and plan_state.state is None, f"{state_before}")
    async with bot.session() as s:
        await billing.reject_payment(s, pending_purchase.id, admin.id, "приёмка")

    # --- Итоговая сверка -------------------------------------------------------------
    R.start("Итоговая сверка (ops/whitelist_check.py) и SubHub")
    check = subprocess.run(
        [sys.executable, "-m", "ops.whitelist_check", "--details"], cwd=ROOT,
        env=dict(os.environ, DATABASE_URL=db_url, BOT_TOKEN="acceptance"),
        capture_output=True, text=True,
    )
    summary = check.stdout.strip().splitlines()
    R.fact("whitelist_check", " | ".join(summary[-3:]))
    R.check("whitelist_check: расхождений и несверенных событий нет",
            check.returncode == 0 and "mismatch=0" in check.stdout
            and "unsettled=0" in check.stdout and "uncertain=0" in check.stdout,
            check.stderr.strip()[-300:])
    await subhub.sync()
    final_token = (await subhub.tokens()).get(paid.public_id.casefold())
    R.check("ссылка оплаченного пользователя не менялась за весь сценарий",
            final_token == token_before)
    await engine.dispose()


async def _panel_up(panel: Panel) -> bool:
    try:
        await panel.inbounds()
        return True
    except Exception:  # noqa: BLE001
        return False


async def _used_at_least(panel: Panel, email: str, value: int) -> int | None:
    used = await panel.used(email)
    return used if used >= value else None


async def _disabled(panel: Panel, email: str) -> bool:
    record = await panel.client(email)
    return record is not None and record["body"].get("enable") is False


async def _package(bot: Bot, size: int) -> TrafficPackage:
    async with bot.session() as s:
        return await s.scalar(select(TrafficPackage).where(TrafficPackage.traffic_bytes == size))


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

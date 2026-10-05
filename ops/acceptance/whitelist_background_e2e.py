"""R46 без помощи синхронизации: реальные фоновые циклы бота, триггер и опрос SubHub.

Отличие от ``whitelist_e2e.py``: тот сценарий сам вызывает ``POST /admin/sync``
перед каждой проверкой подписки и поэтому доказывает только результат
принудительной синхронизации. Здесь после подготовки стенда сценарий **не
обращается к** ``/admin/sync`` ни одного SubHub (HTTP-клиент наблюдателя такой
запрос отклоняет), а изменения в подписке ждёт с конечным таймаутом.

Стенд (``ops/acceptance/stack.sh up <state> <subhub-src>``):

* SubHub-T — его адрес получает бот; резервный опрос 1 ч, контейнер
  перезапускается при подготовке, поэтому за время сценария (< 1 ч) изменения
  в нём появляются только по быстрому триггеру бота;
* SubHub-P — бот о нём не знает; изменения он видит только резервным опросом
  (``SUBHUB_POLL_SECONDS``, 30 с).

Фоновые задачи запускает ``app.main.start_background_tasks`` — та же сборка,
что у бота рядом с Telegram polling (опрос серверов с очередью и
``recover_confirmed_payments``, обход сверки расхода, уведомления об окончании,
сбор IP). Polling Telegram не запускается, транспорт Telegram заменён
записывающей заглушкой. Обработчики бота вызываются напрямую, как в
``whitelist_e2e.py``; панели, PostgreSQL, SubHub и VLESS-трафик настоящие.

Доказательства каждого изменения: время появления в SubHub-T и SubHub-P,
журнал запросов SubHub (каждый ``POST /admin/sync`` с кодом ответа и каждое
чтение панели), момент применения в БД бота.

    .venv/bin/python ops/acceptance/whitelist_background_e2e.py <state-dir> [--report out.json]

Production, реальные квитанции и сообщения пользователям не используются.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import os
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import asyncpg  # noqa: E402
import httpx  # noqa: E402
import whitelist_e2e as base  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from app import main as app_main  # noqa: E402
from app.bot import admin_handlers  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import session as db_session  # noqa: E402
from app.db.enums import PaymentStatus, UserRole  # noqa: E402
from app.db.models import (  # noqa: E402
    PAYMENT_KIND_TRAFFIC,
    PaymentRequest,
    PendingServerUpdate,
    User,
    WhitelistLedger,
)
from app.logging_config import setup_logging  # noqa: E402
from app.services import billing, whitelist  # noqa: E402
from app.services.subhub_client import trigger_configured_sync  # noqa: E402
from app.services.xui_updater import build_updater  # noqa: E402

GIB = base.GIB
ADMIN_TG = 710001
STD, WL = "std.acc.test", "wl.acc.test"
BOTH = frozenset({STD, WL})
ONLY_STD = frozenset({STD})
NOTHING = frozenset()
# Настройки фоновых циклов на стенде (production: 60 с / 15 мин / 300 с / 15 с).
HEALTH_SECONDS = 5
RECONCILE_MINUTES = 1
EXPIRY_NOTIFY_SECONDS = 5
SUBHUB_TIMEOUT = 5
# Конечные ожидания.
TRIGGER_TIMEOUT = 30  # обработчик → триггер → синхронизация SubHub-T
BACKGROUND_TIMEOUT = 180  # сверка (≤ 60 с) или backoff очереди (60 с) + цикл + синхронизация
LOST_TRIGGER_WINDOW = 60  # сколько ждать изменения без нового триггера

R = base.Report()


# --- Наблюдение за SubHub (только чтение) ----------------------------------------


@dataclass(frozen=True)
class View:
    status: int  # /admin/subscriptions/resolve: 200, 404 (нет клиента), 409 (нет узлов)
    token: str | None
    hosts: frozenset[str]
    links: tuple[str, ...]

    def link(self, host: str) -> str | None:
        return next((item for item in self.links if urlparse(item).hostname == host), None)


@dataclass(frozen=True)
class HubEvent:
    ts: datetime
    kind: str  # "trigger" — POST /admin/sync; "fetch" — чтение панели
    detail: str  # код ответа или "std"/"wl" (+ "!" при ошибке чтения)


def _forbid_sync(request: httpx.Request) -> None:
    if request.url.path.rstrip("/").endswith("/admin/sync"):
        raise AssertionError("сценарий не должен вызывать /admin/sync")


class Hub:
    """SubHub глазами пользователя и администратора; синхронизацию не запускает."""

    def __init__(self, name: str, url: str, token: str, container: str) -> None:
        self.name, self.url, self.token, self.container = name, url.rstrip("/"), token, container

    @asynccontextmanager
    async def http(self):
        async with httpx.AsyncClient(
            base_url=self.url, timeout=10, headers={"X-Admin-Token": self.token},
            event_hooks={"request": [_async(_forbid_sync)]},
        ) as client:
            yield client

    async def view(self, email: str) -> View:
        async with self.http() as http:
            resolved = await http.post("/admin/subscriptions/resolve", json={"email": email})
            rows = (await http.get("/admin/clients")).json()
            token = next((row["token"] for row in rows
                          if (row.get("email") or "").casefold() == email.casefold()), None)
            links: list[str] = []
            if token:
                response = await http.get(f"/connection/{token}")
                if response.status_code == 200:
                    links = [line for line in base64.b64decode(response.text).decode().splitlines()
                             if line.startswith("vless://")]
        hosts = frozenset(urlparse(link).hostname for link in links)
        return View(resolved.status_code, token, frozenset(h for h in hosts if h), tuple(links))

    async def up(self) -> bool:
        try:
            async with self.http() as http:
                return (await http.get("/health")).status_code == 200
        except httpx.HTTPError:
            return False

    def events(self, since: datetime) -> list[HubEvent]:
        out = subprocess.run(
            ["docker", "logs", "--since", f"{since.timestamp() - 1:.3f}", self.container],
            capture_output=True, text=True,
        )
        events = []
        for line in (out.stdout + out.stderr).splitlines():
            try:
                item = json.loads(line)
                ts = datetime.fromisoformat(item["timestamp"])
            except (ValueError, KeyError, TypeError):
                continue
            message = str(item.get("message", ""))
            if item.get("message") == "request" and item.get("route") == "/admin/sync":
                events.append(HubEvent(ts, "trigger", str(item.get("status"))))
            elif item.get("logger") == "httpx" and "/panel/api/inbounds/list" in message:
                host = "wl" if WL in message else "std"
                events.append(HubEvent(ts, "fetch", host + ("" if "200 OK" in message else "!")))
        return [event for event in events if event.ts >= since - timedelta(seconds=1)]

    def started_at(self) -> datetime:
        raw = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.StartedAt}}", self.container],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return datetime.fromisoformat(raw[:26].rstrip("Z") + "+00:00")


def _async(hook):
    async def wrapper(request):
        hook(request)
    return wrapper


class ProcessKilled(BaseException):
    """Имитация гибели процесса: не перехватывается ``except Exception`` кода бота."""


class DiesOnFirstChange:
    """Настоящий updater, у которого первое изменение панели «убивает процесс»."""

    MUTATIONS = ("provision_server", "update_expiry", "apply_quota_client", "delete_client")

    def __init__(self, inner: Any) -> None:
        self.inner = inner

    def __getattr__(self, name: str) -> Any:
        if name in self.MUTATIONS:
            async def die(*_args: Any, **_kwargs: Any) -> None:
                raise ProcessKilled(name)
            return die
        return getattr(self.inner, name)


async def docker(*args: str) -> None:
    # В потоке: цикл событий (и фоновые задачи бота) не останавливается.
    await asyncio.to_thread(subprocess.run, ["docker", *args], check=True, capture_output=True)


async def probe(link: str | None, image: str, network: str) -> tuple[bool, str]:
    """Настоящее VLESS-подключение xray по ссылке из подписки (в потоке)."""
    return await asyncio.to_thread(base.probe, link or "", image, network)


def now() -> datetime:
    return datetime.now(UTC)


def rel(ts: datetime, origin: datetime) -> str:
    return f"{(ts - origin).total_seconds():+.1f}с"


# --- Действия и их окна -------------------------------------------------------------


class Acts:
    """Источник каждого POST /admin/sync в журнале SubHub-T.

    Фоновый цикл бота перед запросом пишет в свой журнал «SubHub: запрос
    синхронизации после фоновых изменений (<причина>)»; запрос сопоставляется
    такой строке. Остальные запросы — из окон обработчиков, которые вызывал
    сценарий («фон?», если не попали ни в одно окно).
    """

    BACKGROUND = "SubHub: запрос синхронизации после фоновых изменений ("

    def __init__(self) -> None:
        self.windows: list[tuple[datetime, datetime, str]] = []
        self.log_path: Path | None = None

    @asynccontextmanager
    async def act(self, label: str):
        started = now()
        try:
            yield
        finally:
            self.windows.append((started, now(), label))

    def background(self) -> list[tuple[datetime, str]]:
        if self.log_path is None or not self.log_path.exists():
            return []
        found = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            if self.BACKGROUND in line:
                # Время журнала бота — локальное (формат logging по умолчанию).
                ts = datetime.strptime(line[:23], "%Y-%m-%d %H:%M:%S,%f").astimezone(UTC)
                found.append((ts, line.split(self.BACKGROUND, 1)[1].rstrip(")")))
        return found

    def window(self, ts: datetime) -> str:
        # SubHub пишет запрос после ответа: допуск 0,3 с на часы контейнера.
        tolerance = timedelta(seconds=0.3)
        best: tuple[timedelta, str] | None = None
        for started, ended, label in self.windows:
            distance = max(started - ts, ts - ended, timedelta(0))
            if distance <= tolerance and (best is None or distance < best[0]):
                best = (distance, label)
        return best[1] if best else "фон?"

    def labels(self, events: list[HubEvent]) -> dict[HubEvent, str]:
        background = self.background()
        used: set[int] = set()
        result: dict[HubEvent, str] = {}
        for event in sorted((e for e in events if e.kind == "trigger"), key=lambda e: e.ts):
            match = next((i for i, (ts, _) in enumerate(background) if i not in used
                          and ts - timedelta(seconds=0.3) <= event.ts
                          <= ts + timedelta(seconds=1.5)), None)
            if match is None:
                result[event] = self.window(event.ts)
            else:
                used.add(match)
                result[event] = f"фон: {background[match][1]}"
        return result


ACTS = Acts()


def from_source(label: str, source: str) -> bool:
    return label.startswith("фон") if source == "фон" else label == source


def describe(events: list[HubEvent], origin: datetime) -> str:
    labels = ACTS.labels(events)
    parts = []
    for event in events:
        if event.kind == "trigger":
            parts.append(f"sync {event.detail}@{rel(event.ts, origin)}[{labels[event]}]")
        else:
            parts.append(f"fetch {event.detail}@{rel(event.ts, origin)}")
    return ", ".join(parts) or "событий нет"


Want = frozenset[str] | Callable[[View], bool]


def matches(view: View, want: Want) -> bool:
    if callable(want):
        return want(view)
    return view.hosts == want and (view.status == 200 if want else view.status != 200)


async def wait_view(hub: Hub, email: str, want: Want, timeout: float,
                    interval: float = 1.0) -> tuple[View, float | None]:
    started = time.monotonic()
    while True:
        view = await hub.view(email)
        if matches(view, want):
            return view, time.monotonic() - started
        if time.monotonic() - started > timeout:
            return view, None
        await asyncio.sleep(interval)


async def expect_trigger(name: str, email: str, hosts: Want, origin: datetime,
                         *, timeout: float = TRIGGER_TIMEOUT, changed_at: datetime | None = None,
                         panel: str | None = None, source: str | None = None) -> View:
    """Изменение появилось в SubHub-T, и его принёс быстрый триггер бота.

    SubHub-T не опрашивает панели сам в пределах сценария, а сценарий не
    вызывает /admin/sync; поэтому доказательство — POST /admin/sync с кодом 202
    после изменения и чтение нужной панели после него.
    """
    view, elapsed = await wait_view(HUB_T, email, hosts, timeout)
    events = HUB_T.events(origin)
    seen_at = now()
    changed_at = changed_at or origin
    accepted = [e for e in events if e.kind == "trigger" and e.detail == "202"
                and changed_at - timedelta(seconds=1) <= e.ts <= seen_at]
    fetched = [e for e in events if e.kind == "fetch" and e.ts >= changed_at
               and (panel is None or e.detail == panel)]
    labels = ACTS.labels(events)
    sourced = source is None or any(from_source(labels[e], source) for e in accepted)
    R.check(
        f"SubHub-T (триггер): {name}",
        elapsed is not None and bool(accepted) and bool(fetched) and sourced,
        f"{_hosts(view)} через {_secs(elapsed)}; {describe(events, origin)}",
    )
    return view


async def expect_poll(name: str, email: str, hosts: Want, origin: datetime) -> None:
    """То же изменение доходит до SubHub-P только резервным опросом."""
    view, elapsed = await wait_view(HUB_P, email, hosts, POLL_SECONDS + 30)
    events = HUB_P.events(origin)
    triggers = [e for e in events if e.kind == "trigger"]
    R.check(
        f"SubHub-P (только опрос {POLL_SECONDS} с): {name}",
        elapsed is not None and not triggers,
        f"{_hosts(view)} через {_secs(elapsed)}; POST /admin/sync: {len(triggers)}; "
        f"чтений панелей: {sum(1 for e in events if e.kind == 'fetch')}",
    )


def _hosts(view: View) -> str:
    names = sorted("услуга" if h == WL else "обычный" for h in view.hosts)
    return f"HTTP {view.status}, конфиги: {', '.join(names) or 'нет'}"


def _secs(value: float | None) -> str:
    return "—(таймаут)" if value is None else f"{value:.1f} с"


# --- Сценарий ------------------------------------------------------------------------


HUB_T: Hub
HUB_P: Hub
POLL_SECONDS = 30
PROBE_STARTED: datetime | None = None  # с этого момента сценарий сам шлёт триггеры (фаза Z)


async def scenario(state: Path) -> None:
    global HUB_T, HUB_P, POLL_SECONDS
    env = base.load_env(state)
    image, network = env["XUI_IMAGE"], env["NET"]
    wl_panel = base.Panel(env["WL_PANEL"], env["XUI_USER"], env["XUI_PASS"], "wlacc-xui-wl", image)
    std_panel = base.Panel(env["STD_PANEL"], env["XUI_USER"], env["XUI_PASS"], "wlacc-xui-std",
                           image)
    HUB_T = Hub("SubHub-T", env["SUBHUB_URL"], env["SUBHUB_ADMIN_TOKEN"], "wlacc-subhub")
    HUB_P = Hub("SubHub-P", env["SUBHUB_POLL_URL"], env["SUBHUB_ADMIN_TOKEN"], "wlacc-subhub-poll")
    POLL_SECONDS = int(env.get("SUBHUB_POLL_SECONDS", "30"))

    # --- Подготовка стенда (до запуска фоновых задач) -----------------------------
    R.start("Подготовка стенда")
    for panel in (std_panel, wl_panel):
        if await panel.allow_private_targets():
            await asyncio.sleep(3)
    std_inbound = await std_panel.ensure_inbound(20444, "Обычный")
    wl_inbound = await wl_panel.ensure_inbound(20443, "Обход белых списков")
    R.fact("inbound обычной / whitelist-панели", f"{std_inbound} / {wl_inbound}")
    conn = await asyncpg.connect(env["PG_URL"].replace("+asyncpg", "") + "/postgres")
    await conn.execute('DROP DATABASE IF EXISTS "wlacc_bg" WITH (FORCE)')
    await conn.execute('CREATE DATABASE "wlacc_bg"')
    await conn.close()
    db_url = env["PG_URL"] + "/wlacc_bg"
    # Настройки — из окружения, как у процесса бота (get_settings), а не аргументами.
    os.environ.update({
        "DATABASE_URL": db_url, "BOT_TOKEN": "acceptance", "ADMIN_TELEGRAM_IDS": str(ADMIN_TG),
        "SUBHUB_URL": env["SUBHUB_URL"], "SUBHUB_ADMIN_TOKEN": env["SUBHUB_ADMIN_TOKEN"],
        "SUBHUB_TIMEOUT_SECONDS": str(SUBHUB_TIMEOUT), "XUI_REQUEST_TIMEOUT": "8",
        "SERVER_HEALTH_POLL_SECONDS": str(HEALTH_SECONDS),
        "WHITELIST_RECONCILE_MINUTES": str(RECONCILE_MINUTES),
        "WHITELIST_RECONCILE_BATCH_PAUSE_SECONDS": "0",
        "EXPIRY_NOTIFY_POLL_SECONDS": str(EXPIRY_NOTIFY_SECONDS),
        "TRIAL_PERIOD_DAYS": "3", "WEB_BRIDGE_TOKEN": "", "LOG_LEVEL": "INFO",
        "PAYMENT_DETAILS_TEXT": "Тестовые реквизиты (оплаты нет)",
    })
    get_settings.cache_clear()
    settings = get_settings()
    for value in (settings.database_url, settings.subhub_url):
        assert urlparse(value.replace("+asyncpg", "")).hostname == "127.0.0.1", value
    assert not settings.web_bridge_token
    migrate = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT,
                             env=dict(os.environ), capture_output=True, text=True)
    R.check("alembic upgrade head", migrate.returncode == 0,
            (migrate.stderr.strip().splitlines() or [""])[-1][-160:])
    maker = db_session.get_sessionmaker()
    bot = base.Bot(maker, settings)
    async with bot.session() as s:
        await whitelist.ensure_defaults(s)  # как run() при старте
    admin = await bot.user(ADMIN_TG, "admin", UserRole.ADMIN)

    # Свежее часовое окно SubHub-T: его плановый опрос — не раньше чем через 1 ч.
    await docker("restart", "wlacc-subhub")
    await base.wait_until(HUB_T.up, 60, 1)
    await asyncio.sleep(3)  # стартовая синхронизация SubHub-T (его собственная)
    hub_t_started = HUB_T.started_at()
    R.fact("SubHub-T запущен", f"{hub_t_started:%H:%M:%S} UTC; плановый опрос не раньше "
           f"{hub_t_started + timedelta(hours=1):%H:%M:%S}")

    log_path = state / "bot-background.log"
    log_path.unlink(missing_ok=True)
    ACTS.log_path = log_path
    root = logging.getLogger()
    root.handlers[:] = [logging.FileHandler(log_path, encoding="utf-8")]
    setup_logging(level="INFO")  # формат и уровни как у процесса бота
    tasks = app_main.start_background_tasks(bot.tg, settings)
    run_started = now()
    R.fact("фоновые задачи (app.main.start_background_tasks)",
           ", ".join(sorted(t.get_coro().__name__ for t in tasks)))
    try:
        await _phases(bot, admin, settings, std_panel, wl_panel, std_inbound, wl_inbound, image,
                      network, run_started)
    finally:
        await app_main.stop_background_tasks(tasks)
        R.start("Итог фоновых задач и SubHub")
        log = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
        errors = [line for line in log.splitlines() if "Ошибка фоновой" in line]
        R.fact("ошибок фоновых циклов в журнале бота", len(errors))
        for line in errors[:5]:
            R.fact("ошибка фонового цикла", line[:200])
        R.check("SubHub-T не мог выполнить плановый опрос за время сценария",
                now() < hub_t_started + timedelta(hours=1), f"окончание {now():%H:%M:%S}")
        events = [e for e in HUB_T.events(run_started)
                  if PROBE_STARTED is None or e.ts < PROBE_STARTED]
        labels = ACTS.labels(events)
        statuses = Counter(f"{e.detail} {'фон' if labels[e].startswith('фон') else 'обработчик'}"
                           for e in events if e.kind == "trigger")
        R.fact("SubHub-T до фазы Z: POST /admin/sync от бота (код, источник)", dict(statuses))
        p_events = HUB_P.events(run_started)
        R.check("SubHub-P: ни одного POST /admin/sync за сценарий",
                not [e for e in p_events if e.kind == "trigger"],
                f"чтений панелей: {sum(1 for e in p_events if e.kind == 'fetch')}")
        check = subprocess.run([sys.executable, "-m", "ops.whitelist_check", "--details"],
                               cwd=ROOT, env=dict(os.environ), capture_output=True, text=True)
        R.fact("whitelist_check", " | ".join(check.stdout.strip().splitlines()[-2:]))
        R.check("whitelist_check: mismatch=0 unsettled=0 uncertain=0",
                check.returncode == 0 and "mismatch=0" in check.stdout
                and "unsettled=0" in check.stdout and "uncertain=0" in check.stdout,
                check.stderr.strip()[-200:])
        await db_session.get_engine().dispose()


async def _phases(bot: base.Bot, admin: User, settings, std_panel: base.Panel,
                  wl_panel: base.Panel, std_inbound: int, wl_inbound: int, image: str,
                  network: str, run_started: datetime) -> None:
    async def email_of(user: User) -> str:
        return (await bot.mapping(user)).email

    async def pay(user: User, label: str, days: int = 30) -> tuple[PaymentRequest, Any]:
        payment = await bot.subscribe(user, days=days)
        async with ACTS.act(label):
            callback = await bot.confirm(admin, payment.id)
        return payment, callback

    async def trial(user: User, label: str):
        async with ACTS.act(label):
            return await bot.trial(user)

    def notices(user: User) -> list[str]:
        return [m.get("text", "") for m in bot.tg.messages if m.get("chat_id") == user.telegram_id]

    # --- Сервера через бота -------------------------------------------------------
    R.start("Серверы добавлены через бота (фоновые задачи уже работают)")
    answer = await bot.add_server(
        admin, "add_standard",
        f"Обычный|FI|{std_panel.url}|{std_panel.user}|{std_panel.password}|direct",
    )
    R.check("обычный сервер добавлен", "добавлен" in answer, answer.splitlines()[0])
    answer = await bot.add_server(
        admin, "add_whitelist",
        f"Обход белых списков|LV|{wl_panel.url}|{wl_panel.user}|{wl_panel.password}"
        "|direct",
    )
    async with bot.session() as s:
        server = await whitelist.get_active_server(s)
    R.check("сервер услуги готов (единственный совместимый inbound)",
            whitelist.server_ready(server) and whitelist.target_inbound(server).inbound_id
            == wl_inbound, answer.replace("\n", " ")[:160])

    # --- A. Оплата и trial до запуска услуги (регрессия обычных конфигов) ------------
    R.start("A. Оплата и trial до запуска услуги")
    p1 = await bot.user(710002, "p1")
    t1 = await bot.user(710003, "t1")
    origin = now()
    _, callback = await pay(p1, "оплата p1")
    p1_email = await email_of(p1)
    view = await expect_trigger("оплата p1 → обычный конфиг в подписке", p1_email, ONLY_STD,
                                origin, panel="std", source="оплата p1")
    p1_token = view.token
    origin = now()
    await trial(t1, "trial t1")
    t1_email = await email_of(t1)
    await expect_trigger("trial t1 → обычный конфиг в подписке", t1_email, ONLY_STD, origin,
                         panel="std", source="trial t1")
    await expect_poll("p1 и t1 с обычным конфигом", t1_email, ONLY_STD, origin)

    # --- B. Выдача whitelist-конфига нынешним пользователям ---------------------------
    R.start("B. Выдача услуги нынешним пользователям")
    origin = now()
    async with ACTS.act("выдача услуги"):
        await bot.wl_admin(admin, "rollout")
        await bot.wl_admin(admin, "rollout_strict")
    view = await expect_trigger("выдача → p1: конфиг услуги в той же ссылке", p1_email, BOTH,
                                origin, panel="wl", source="выдача услуги")
    R.check("ссылка p1 (токен SubHub-T) прежняя", view.token == p1_token)
    await expect_trigger("выдача → t1: конфиг услуги", t1_email, BOTH, origin, panel="wl")
    record = await wl_panel.client(p1_email)
    R.check("квота p1 = 10 ГиБ в байтах", record and record["body"]["totalGB"] == 10 * GIB)
    await expect_poll("выдача p1", p1_email, BOTH, origin)

    # --- C. Оплата и trial после запуска -------------------------------------------
    R.start("C. Оплата и trial после запуска услуги")
    p2 = await bot.user(710004, "p2")
    t2 = await bot.user(710005, "t2")
    origin = now()
    await pay(p2, "оплата p2")
    p2_email = await email_of(p2)
    await expect_trigger("оплата p2 → оба конфига", p2_email, BOTH, origin, source="оплата p2")
    origin = now()
    await trial(t2, "trial t2")
    t2_email = await email_of(t2)
    await expect_trigger("trial t2 → оба конфига", t2_email, BOTH, origin, source="trial t2")
    await expect_poll("оплата p2 и trial t2", t2_email, BOTH, origin)

    # --- D. Исчерпание → фоновая сверка и очередь; покупка после исчерпания ------------
    R.start("D. Исчерпание (фоновая сверка + очередь) и покупка после исчерпания")
    answer = await bot.wl_admin_value(admin, "free_paid", base.SMALL_GB)
    await bot.wl_admin_value(admin, "pkg_add", f"{base.SMALL_GB} 1")
    small_pkg = await base._package(bot, base.SMALL)
    package10 = await base._package(bot, 10 * GIB)
    s1 = await bot.user(710006, "s1")
    s2 = await bot.user(710007, "s2")
    origin = now()
    await pay(s1, "оплата s1")
    await pay(s2, "оплата s2")
    await bot.wl_admin_value(admin, "free_paid", "10")
    s1_email, s2_email = await email_of(s1), await email_of(s2)
    view_s1 = await expect_trigger("оплата s1 (квота 0,02 ГБ) → оба конфига", s1_email, BOTH,
                                   origin, source="оплата s1")
    view_s2 = await expect_trigger("оплата s2 (квота 0,02 ГБ) → оба конфига", s2_email, BOTH,
                                   origin, source="оплата s2")
    # Первый трафик через whitelist-панель в этом прогоне (после смены шаблона Xray
    # при подготовке стенда) — наблюдение D-3 через конфиг p1, отдельно от проверок.
    # observe_d3 ждёт два опроса панели, поэтому загрузка служит прогревом для
    # проверок исчерпания ниже; прогрев обозначен в отчёте.
    p1_view = await HUB_T.view(p1_email)
    await base.observe_d3(R, wl_panel, p1_email, p1_view.link(WL), image, network,
                          "первый трафик через whitelist-панель после подготовки стенда")
    R.warmup("загрузка p1 выше (наблюдение D-3) — первый трафик через whitelist-панель; "
             "исчерпание s1/s2 ниже измеряется после двух опросов панели")
    traffic_started = now()
    for email, view in ((s1_email, view_s1), (s2_email, view_s2)):
        for _ in range(6):
            if await base._disabled(wl_panel, email):
                break
            await probe(view.link(WL), image, network)
            await base.wait_until(lambda e=email: base._disabled(wl_panel, e), 15)
    disabled = [await base._disabled(wl_panel, e) for e in (s1_email, s2_email)]
    R.check("панель сама отключила исчерпанные конфиги s1 и s2", all(disabled),
            f"расход s1 {await wl_panel.used(s1_email)} Б, s2 {await wl_panel.used(s2_email)} Б, "
            f"лимит {base.SMALL} Б")
    for user, email in ((s1, s1_email), (s2, s2_email)):
        view = await expect_trigger(
            f"исчерпание {user.username}: конфиг услуги скрыт без действий пользователя и "
            "администратора", email, ONLY_STD, traffic_started,
            timeout=BACKGROUND_TIMEOUT, changed_at=traffic_started, panel="wl", source="фон",
        )
        account = await bot.account(user)
        R.fact(f"{user.username}: применено очередью",
               f"enable={account.applied_enable} в {account.applied_at:%H:%M:%S} "
               f"({rel(account.applied_at, traffic_started)} от начала трафика)")
    await expect_poll("исчерпание s1", s1_email, ONLY_STD, traffic_started)

    callback, purchase = await bot.buy(s1, small_pkg.id)
    origin = now()
    async with ACTS.act("покупка s1"):
        callback = await bot.confirm(admin, purchase.id)
    view = await expect_trigger("покупка после исчерпания → конфиг услуги вернулся", s1_email,
                                BOTH, origin, panel="wl", source="покупка s1")
    ok, out = await probe(view.link(WL), image, network)
    R.check("после покупки конфиг услуги из подписки SubHub-T передаёт трафик", ok, out)
    await expect_poll("покупка s1", s1_email, BOTH, origin)

    # --- E. Две операции во время идущей синхронизации SubHub-T ---------------------
    R.start("E. Триггер во время идущей синхронизации (медленная обычная панель)")
    _, purchase_p2 = await bot.buy(p2, package10.id)
    _, purchase_s2 = await bot.buy(s2, small_pkg.id)
    await docker("pause", "wlacc-xui-std")  # SubHub-T будет ждать ответа обычной панели
    origin = now()
    try:
        async with ACTS.act("покупка p2"):
            await bot.confirm(admin, purchase_p2.id)
        await asyncio.sleep(2)
        change_at = now()
        async with ACTS.act("покупка s2"):
            await bot.confirm(admin, purchase_s2.id)
        await asyncio.sleep(6)
    finally:
        await docker("unpause", "wlacc-xui-std")
    account = await bot.account(s2)
    R.check("покупка s2 применена на whitelist-панели (enable=true) в обработчике",
            account.applied_enable is True and await base._disabled(wl_panel, s2_email) is False)
    events = HUB_T.events(origin)
    R.fact("SubHub-T во время медленной обычной панели", describe(events, origin))
    await expect_trigger(
        "конфиг s2, возобновлённый во время идущей синхронизации, появился без нового действия",
        s2_email, BOTH, origin, timeout=LOST_TRIGGER_WINDOW, changed_at=change_at, panel="wl",
    )
    await expect_poll("покупка s2 (резервный опрос видит панель)", s2_email, BOTH, change_at)

    # --- F. Истечение и продление; недоступные панели и восстановление -------------
    R.start("F. Истечение (фон), продление при недоступных панелях, восстановление (фон)")
    e1 = await bot.user(710008, "e1")
    e2 = await bot.user(710009, "e2")
    await pay(e1, "оплата e1")
    await pay(e2, "оплата e2")
    e1_email, e2_email = await email_of(e1), await email_of(e2)
    expire_at = now() + timedelta(seconds=40)
    for user in (e1, e2):
        await bot.set_expiry(user, expire_at)  # «прошло 30 дней» — сдвиг срока в БД
        async with ACTS.act(f"/sync {user.username}"):
            await bot.admin_command(admin_handlers.sync_user, "sync", str(user.telegram_id), admin)
    await asyncio.sleep(max(0.0, (expire_at - now()).total_seconds()) + 1)
    for user, email in ((e1, e1_email), (e2, e2_email)):
        await expect_trigger(f"истечение {user.username}: в подписке нет активных конфигов",
                             email, NOTHING, expire_at, timeout=BACKGROUND_TIMEOUT,
                             changed_at=expire_at, source="фон")
    R.check("фоновые уведомления об окончании дошли до заглушки Telegram",
            any("истек" in text.lower() for text in notices(e1)), notices(e1)[-1:])
    await expect_poll("истечение e1", e1_email, NOTHING, expire_at)

    await docker("stop", "wlacc-xui-std", "wlacc-xui-wl")
    try:
        renewal, callback = await pay(e1, "продление e1")
        headline = (callback.message.edits or [""])[-1].splitlines()[0]
        async with bot.session() as s:
            stored = await s.get(PaymentRequest, renewal.id)
            pending_std = await s.scalar(select(func.count()).select_from(PendingServerUpdate)
                                         .where(PendingServerUpdate.payment_request_id
                                                == renewal.id))
        account = await bot.account(e1)
        R.check("продление при недоступных панелях сохранено: APPLIED, обычная панель в "
                "отложенных, услуга ждёт очереди",
                stored.status == PaymentStatus.APPLIED and pending_std == 1
                and account.desired_version > account.applied_version, headline)
        expires_after_renewal = (await bot.client(e1)).expires_at
        await asyncio.sleep(3 * HEALTH_SECONDS)
        R.check("пока панели недоступны, SubHub-T не показывает e1",
                (await HUB_T.view(e1_email)).status != 200)
    finally:
        await docker("start", "wlacc-xui-std", "wlacc-xui-wl")
    recovered = now()
    await base.wait_until(lambda: base._panel_up(std_panel), 60)
    await base.wait_until(lambda: base._panel_up(wl_panel), 60)
    await expect_trigger("восстановление: обычный конфиг e1 применён фоновой проверкой серверов",
                         e1_email, lambda v: v.status == 200 and STD in v.hosts,
                         recovered, timeout=BACKGROUND_TIMEOUT, changed_at=recovered,
                         panel="std", source="фон")
    await expect_trigger("восстановление: конфиг услуги e1 применён фоновой очередью", e1_email,
                         BOTH, recovered, timeout=BACKGROUND_TIMEOUT, changed_at=recovered,
                         panel="wl", source="фон")
    async with bot.session() as s:
        stored = await s.get(PaymentRequest, renewal.id)
        pending_std = await s.scalar(select(func.count()).select_from(PendingServerUpdate)
                                     .where(PendingServerUpdate.payment_request_id == renewal.id)
                                     .where(PendingServerUpdate.status != "applied"))
    grants = await bot.ledger(e1, whitelist.LEDGER_FREE_GRANT)
    account = await bot.account(e1)
    R.check("после восстановления: срок не изменился, пакет за продление выдан один раз, "
            "очередь пуста",
            (await bot.client(e1)).expires_at == expires_after_renewal and len(grants) == 2
            and account.applied_version >= account.desired_version
            and stored.status == PaymentStatus.APPLIED,
            f"выдач {len(grants)}, отложенных обычных {pending_std}")
    await expect_poll("продление e1 после восстановления", e1_email, BOTH, recovered)

    origin = now()
    async with ACTS.act("/extend e2"):
        message = await bot.admin_command(admin_handlers.manual_extend, "extend",
                                          f"{e2.telegram_id} 30", admin)
    R.fact("/extend e2", message.answers[-1:])
    await expect_trigger("ручное продление /extend истёкшего e2 → оба конфига", e2_email, BOTH,
                         origin, timeout=LOST_TRIGGER_WINDOW, source="/extend e2")
    R.check("/extend не выдал пакет", len(await bot.ledger(e2, whitelist.LEDGER_FREE_GRANT)) == 1)

    # --- R. Падение процесса между фиксацией оплаты и панелью ---------------------
    R.start("R. Падение после фиксации оплаты; возобновление фоновым циклом")
    r1 = await bot.user(710014, "r1")
    r1_email = (await bot.reload(r1)).public_id
    payment_r1 = await bot.subscribe(r1)
    died = None
    try:
        async with bot.session() as s:
            await billing.confirm_payment(s, payment_r1.id, admin.id,
                                          DiesOnFirstChange(build_updater(timeout=8)))
    except ProcessKilled as exc:
        died = str(exc)
    async with bot.session() as s:
        stored = await s.get(PaymentRequest, payment_r1.id)
    R.check("«процесс умер» на первом изменении панели: заявка CONFIRMED с целевым сроком, "
            "клиентов на панелях нет",
            died is not None and stored.status == PaymentStatus.CONFIRMED
            and stored.target_expires_at is not None
            and await std_panel.client(r1_email) is None
            and await wl_panel.client(r1_email) is None, f"остановлено на {died}")
    target_r1 = stored.target_expires_at
    await asyncio.sleep(2 * HEALTH_SECONDS)
    async with bot.session() as s:
        still = (await s.get(PaymentRequest, payment_r1.id)).status
    R.check("до истечения 5 минут фоновый цикл заявку не трогает", still
            == PaymentStatus.CONFIRMED, still)
    async with bot.session() as s:  # «прошло 5 минут» — сдвиг времени подтверждения
        stored = await s.get(PaymentRequest, payment_r1.id)
        stored.confirmed_at = stored.confirmed_at - timedelta(minutes=6)
        await s.commit()
    origin = now()
    await expect_trigger("возобновлённая фоновым циклом оплата r1 → оба конфига", r1_email,
                         BOTH, origin, timeout=LOST_TRIGGER_WINDOW, source="фон")
    async with bot.session() as s:
        stored = await s.get(PaymentRequest, payment_r1.id)
    grants = await bot.ledger(r1, whitelist.LEDGER_FREE_GRANT)
    client = await bot.client(r1)
    R.check("возобновление: APPLIED, срок = сохранённый целевой, пакет выдан один раз",
            stored.status == PaymentStatus.APPLIED and len(grants) == 1
            and client.expires_at == target_r1
            and (await bot.account(r1)).free_bytes == 10 * GIB,
            f"{stored.status}; выдач {len(grants)}")

    # --- G. Сбой SubHub-T ------------------------------------------------------------
    R.start("G. Сбой SubHub: оплата сохраняется, без повторного начисления, обновление потом")
    g1 = await bot.user(710010, "g1")
    await docker("stop", "wlacc-subhub")
    try:
        started = time.monotonic()
        payment_g1, callback = await pay(g1, "оплата g1 (SubHub-T остановлен)")
        duration = time.monotonic() - started
        g1_email = await email_of(g1)
        async with bot.session() as s:
            stored = await s.get(PaymentRequest, payment_g1.id)
        R.check("SubHub-T остановлен: подтверждение завершено, администратор видит результат, "
                "пользователь уведомлён",
                stored.status == PaymentStatus.APPLIED and bool(callback.message.edits)
                and bool(notices(g1)),
                f"{duration:.1f} с; {(callback.message.edits or ['—'])[-1].splitlines()[0]}")
        R.check("клиенты g1 созданы на обеих панелях",
                await std_panel.client(g1_email) is not None
                and await wl_panel.client(g1_email) is not None)
        expires_g1 = (await bot.client(g1)).expires_at
        rows_before = len(await bot.ledger(g1))
        again = await bot.confirm(admin, payment_g1.id)
        await asyncio.sleep(4 * HEALTH_SECONDS)  # recover_confirmed_payments, очередь
        account = await bot.account(g1)
        R.check("повторное подтверждение и фоновые циклы без SubHub не начисляют повторно",
                (again.alerts or [""])[-1] == "Заявка уже применена ранее"
                and len(await bot.ledger(g1)) == rows_before
                and (await bot.client(g1)).expires_at == expires_g1
                and account.free_bytes == 10 * GIB,
                f"строк журнала {rows_before}; {again.alerts[-1:]}")
    finally:
        restart_started = now()
        await docker("start", "wlacc-subhub")
    await base.wait_until(HUB_T.up, 60, 1)
    view, elapsed = await wait_view(HUB_T, g1_email, BOTH, TRIGGER_TIMEOUT)
    R.check("после запуска SubHub-T оплата g1 в подписке (его стартовая синхронизация)",
            elapsed is not None,
            f"{_hosts(view)}; {describe(HUB_T.events(restart_started)[:8], restart_started)}")
    g2 = await bot.user(710011, "g2")
    origin = now()
    await trial(g2, "trial g2")
    await expect_trigger("следующее изменение после сбоя (trial g2) доходит триггером",
                         await email_of(g2), BOTH, origin, source="trial g2")

    g3 = await bot.user(710012, "g3")
    await docker("pause", "wlacc-subhub")
    try:
        started = time.monotonic()
        payment_g3, callback = await pay(g3, "оплата g3 (SubHub-T завис)")
        duration = time.monotonic() - started
    finally:
        await docker("unpause", "wlacc-subhub")
    unpaused = now()
    g3_email = await email_of(g3)
    async with bot.session() as s:
        stored = await s.get(PaymentRequest, payment_g3.id)
    R.check("SubHub-T завис: подтверждение завершено после таймаута триггера, пользователь "
            "уведомлён", stored.status == PaymentStatus.APPLIED and bool(notices(g3))
            and bool(callback.message.edits), f"{duration:.1f} с (таймаут {SUBHUB_TIMEOUT} с)")
    view, elapsed = await wait_view(HUB_T, g3_email, BOTH, 20)
    R.fact("g3 после снятия паузы без нового действия",
           f"{_hosts(view)} через {_secs(elapsed)}; {describe(HUB_T.events(unpaused), unpaused)}")
    g4 = await bot.user(710013, "g4")
    origin = now()
    await trial(g4, "trial g4")
    await expect_trigger("следующее действие (trial g4) доходит триггером", await email_of(g4),
                         BOTH, origin, source="trial g4")
    view, elapsed = await wait_view(HUB_T, g3_email, BOTH, TRIGGER_TIMEOUT)
    R.check("после следующего триггера в подписке и g3", elapsed is not None, _hosts(view))
    async with bot.session() as s:
        credits = await s.scalar(select(func.count()).select_from(WhitelistLedger)
                                 .where(WhitelistLedger.source_key
                                        .in_([f"payment:{payment_g1.id}",
                                              f"payment:{payment_g3.id}"])))
        traffic = await s.scalar(select(func.count()).select_from(PaymentRequest)
                                 .where(PaymentRequest.kind == PAYMENT_KIND_TRAFFIC)
                                 .where(PaymentRequest.status == PaymentStatus.APPLIED))
    R.check("оплаты g1 и g3 выданы ровно по одному разу", credits == 2, credits)
    R.fact("применённых покупок трафика за сценарий", traffic)
    R.check("ссылка p1 не менялась за весь сценарий",
            (await HUB_T.view(p1_email)).token == p1_token)

    # --- Z. Best-effort триггер при перезапуске SubHub-T (после всех проверок R46) ---
    # Здесь сценарий сам вызывает production-функцию trigger_configured_sync — это
    # проверка её устойчивости, а не помощь синхронизации: изменений после неё нет.
    global PROBE_STARTED
    R.start("Z. trigger_configured_sync во время перезапуска SubHub-T")
    PROBE_STARTED = now()
    outcomes: Counter[str] = Counter()
    restarter = await asyncio.create_subprocess_exec(
        "docker", "restart", "wlacc-subhub",
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 30
    ready_streak = 0
    while time.monotonic() < deadline and ready_streak < 20:
        try:
            result = await trigger_configured_sync(settings.subhub_url,
                                                   settings.subhub_admin_token, timeout=3)
            outcomes["True" if result else "False"] += 1
            ready_streak = ready_streak + 1 if result and restarter.returncode is not None else 0
        except Exception as exc:  # noqa: BLE001 - фиксируем, что функция бросила
            outcomes[f"исключение {type(exc).__name__}"] += 1
            ready_streak = 0
        await asyncio.sleep(0.05)
    await restarter.wait()
    R.check("trigger_configured_sync (best-effort) во время перезапуска SubHub-T не бросает "
            "исключений", not any(k.startswith("исключение") for k in outcomes), dict(outcomes))


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
        args.report.write_text(json.dumps(R.dump(), ensure_ascii=False, indent=1, default=str))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

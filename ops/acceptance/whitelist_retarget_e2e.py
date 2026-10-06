"""Real 3x-ui transfer acceptance; only the local stack.sh fixture is allowed.

Creates a separate PostgreSQL database and synthetic users. Telegram transport
is recorded, panels, PostgreSQL locks, SubHub and VLESS traffic are real.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import asyncpg  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app import main as app_main  # noqa: E402
from app.config import Settings, get_settings  # noqa: E402
from app.db import session as db_session  # noqa: E402
from app.db.enums import UserRole  # noqa: E402
from app.services import whitelist  # noqa: E402
from app.services.panel_updater import PanelUpdateError  # noqa: E402
from app.services.xui_updater import build_updater  # noqa: E402
from ops.acceptance import whitelist_e2e as base  # noqa: E402

R = base.Report()


class LostDetachResponse:
    """Perform the real detach, then simulate losing its HTTP acknowledgement."""

    def __init__(self):
        self.real = build_updater(timeout=8)
        self.lost = False

    def __getattr__(self, name):
        return getattr(self.real, name)

    async def detach_quota_client(self, *args, **kwargs):
        result = await self.real.detach_quota_client(*args, **kwargs)
        if not self.lost:
            self.lost = True
            raise PanelUpdateError("acceptance: lost detach response")
        return result


async def scenario(state: Path) -> None:
    env = base.load_env(state)
    for key in ("PG_URL", "WL_PANEL", "STD_PANEL", "SUBHUB_URL"):
        if urlparse(env[key]).hostname not in ("127.0.0.1", "localhost"):
            raise RuntimeError("Only local acceptance endpoints are permitted")
    image, network = env["XUI_IMAGE"], env["NET"]
    wl = base.Panel(env["WL_PANEL"], env["XUI_USER"], env["XUI_PASS"], "wlacc-xui-wl", image)
    std = base.Panel(env["STD_PANEL"], env["XUI_USER"], env["XUI_PASS"], "wlacc-xui-std", image)
    hub = base.SubHub(env["SUBHUB_URL"], env["SUBHUB_ADMIN_TOKEN"])
    conn = await asyncpg.connect(env["PG_URL"].replace("+asyncpg", "") + "/postgres")
    await conn.execute('DROP DATABASE IF EXISTS "wlacc_retarget" WITH (FORCE)')
    await conn.execute('CREATE DATABASE "wlacc_retarget"')
    await conn.close()
    url = env["PG_URL"] + "/wlacc_retarget"
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT,
                   env=dict(os.environ, DATABASE_URL=url), check=True, capture_output=True)
    engine = create_async_engine(url)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    settings = Settings(bot_token="acceptance", admin_telegram_ids=[730001], database_url=url,
                        subhub_url=env["SUBHUB_URL"], subhub_admin_token=env["SUBHUB_ADMIN_TOKEN"],
                        xui_request_timeout=8)
    bot = base.Bot(maker, settings)
    admin = await bot.user(730001, "moveadmin", UserRole.ADMIN)
    user = await bot.user(730002, "moveuser")
    old = await wl.ensure_inbound(20510, "Transfer old")
    new = await wl.ensure_inbound(20511, "Transfer new")
    third = await wl.ensure_inbound(20512, "Transfer recovery")
    await std.ensure_inbound(20444, "Обычный")
    await bot.add_server(admin, "add_standard",
                         f"Ordinary|FI|{env['STD_PANEL']}|{env['XUI_USER']}|{env['XUI_PASS']}|direct")
    payment = await bot.subscribe(user)
    await bot.confirm(admin, payment.id)
    await bot.add_server(admin, "add_whitelist",
                         f"Whitelist|LV|{env['WL_PANEL']}|{env['XUI_USER']}|{env['XUI_PASS']}|direct")
    await bot.wl_admin(admin, "choose", old)
    await bot.wl_admin(admin, "rollout_strict")
    package = await base._package(bot, 25 * base.GIB)
    _, purchase = await bot.buy(user, package.id)
    if purchase is None:
        raise RuntimeError("Synthetic purchase was not created")
    await bot.confirm(admin, purchase.id)
    await bot.confirm(admin, purchase.id)
    await hub.sync()
    token = (await hub.tokens())[user.public_id.casefold()]
    record = await wl.client(user.public_id)
    identity = {k: record["body"].get(k) for k in ("uuid", "email", "subId", "tgId")}
    R.start("Initial placement and real traffic")
    R.check("Initial owned binding", record["inboundIds"] == [old])
    R.check("Paid package credited exactly once",
            (await bot.account(user)).paid_bytes == 25 * base.GIB
            and len(await bot.ledger(user, "purchase")) == 1)
    link = base.link_for(await hub.links(token), "wl.acc.test")
    # Wait beyond 3x-ui's initial traffic-job baseline (known upstream D-3).
    await asyncio.sleep(15)
    ok, detail = await asyncio.to_thread(base.probe, link, image, network)
    R.check("Initial VLESS configuration transfers 8 MiB", ok, detail)
    await base.wait_until(lambda: base._used_at_least(wl, user.public_id, base.BLOB), 40)
    await bot.overview(user)
    before = await bot.account(user)
    R.check("Panel accounted real traffic", await wl.used(user.public_id) >= base.BLOB)

    R.start("Real transfer and subscription update")
    await bot.wl_admin(admin, "choose", new)
    await bot.process_due()
    record = await wl.client(user.public_id)
    account = await bot.account(user)
    R.check("Only new binding remains; placement confirmed",
            record["inboundIds"] == [new] and account.placement_inbound_id == new)
    R.check("Identity preserved", identity == {k: record["body"].get(k) for k in identity})
    R.check("Subscription expiry preserved",
            record["body"]["expiryTime"] == base.ms((await bot.client(user)).expires_at))
    R.check("Transfer grants no extra free or purchased traffic",
            account.free_bytes <= before.free_bytes
            and account.paid_bytes == before.paid_bytes)
    await hub.sync()
    R.check("Subscription token unchanged",
            (await hub.tokens())[user.public_id.casefold()] == token)
    link = base.link_for(await hub.links(token), "wl.acc.test")
    R.check("SubHub publishes new port only", urlparse(link).port == 20511)
    await asyncio.sleep(15)
    ok, detail = await asyncio.to_thread(base.probe, link, image, network)
    R.check("New VLESS configuration transfers 8 MiB", ok, detail)

    R.start("Lost acknowledgement and fresh DB connection")
    # The admin handler applies its queue immediately. Select through the same
    # service first, so the next actual HTTP operation can be interrupted.
    async with bot.session() as session:
        server = await whitelist.get_active_server(session)
        chosen = await whitelist.choose_inbound(session, server, third, admin.id)
        R.check("Recovery target selected without applying its queue",
                chosen.status == whitelist.INVENTORY_READY)
    interrupted = LostDetachResponse()
    async with bot.session() as session:
        result = await whitelist.sync_user(session, user.id, interrupted)
    R.check("Real detach completed but result remains pending", interrupted.lost and result.pending)
    await engine.dispose()
    engine = create_async_engine(url)
    bot = base.Bot(async_sessionmaker(engine, expire_on_commit=False), settings)
    # Honor the actual queue backoff, then retry with fresh connections.
    await asyncio.sleep(62)
    applied = await bot.process_due()
    account = await bot.account(user)
    record = await wl.client(user.public_id)
    R.check("Queue recovers after lost detach acknowledgement",
            applied > 0 and account.placement_inbound_id == third
            and record["inboundIds"] == [third])
    R.check("Repeat queue is idempotent", await bot.process_due() == 0)
    R.check("Recovery preserves paid package and its single ledger entry",
            account.paid_bytes == 25 * base.GIB and len(await bot.ledger(user, "purchase")) == 1)

    R.start("Real queue worker with health polling and reconciliation disabled")
    await hub.sync()
    baseline_link = base.link_for(await hub.links(token), "wl.acc.test")
    R.check("SubHub baseline is the confirmed recovery port",
            bool(baseline_link) and urlparse(baseline_link).port == 20512)
    async with bot.session() as session:
        server = await whitelist.get_active_server(session)
        await whitelist.choose_inbound(session, server, new, admin.id)
    wl.stop()
    try:
        async with bot.session() as session:
            deferred = await whitelist.sync_user(session, user.id, build_updater(timeout=2))
        R.check("Unavailable panel defers transfer", deferred.pending)
    finally:
        wl.start()
        await base.wait_until(lambda: base._panel_up(wl), 40)
    os.environ["DATABASE_URL"] = url
    get_settings.cache_clear()
    worker_settings = settings.model_copy(update={
        "server_health_poll_seconds": 0, "whitelist_reconcile_minutes": 0,
        "anti_sharing_enabled": False, "expiry_notify_poll_seconds": 0,
        "whitelist_queue_poll_seconds": 1,
    })
    tasks = app_main.start_background_tasks(bot.tg, worker_settings)
    R.check("Only the real queue worker starts",
            [t.get_coro().__name__ for t in tasks] == ["_whitelist_queue_worker"])

    async def recovered_without_commands():
        account = await bot.account(user)
        link = base.link_for(await hub.links(token), "wl.acc.test")
        return account.placement_inbound_id == new and bool(link) and urlparse(link).port == 20511

    try:
        recovered = await base.wait_until(recovered_without_commands, 100, 1)
        R.check("Worker recovers placement and updates SubHub without admin commands", recovered)
    finally:
        await app_main.stop_background_tasks(tasks)
        await db_session.get_engine().dispose()
    R.check("Worker recovery preserves paid package",
            (await bot.account(user)).paid_bytes == 25 * base.GIB)

    R.start("Manual block and expired subscription during transfer")
    async with bot.session() as session:
        await whitelist.set_admin_block(session, user.id, True, admin.id, build_updater(timeout=8))
    await bot.wl_admin(admin, "choose", new)
    await bot.process_due()
    record = await wl.client(user.public_id)
    R.check("Moving a blocked client does not enable it",
            record["inboundIds"] == [new] and record["body"]["enable"] is False)
    async with bot.session() as session:
        await whitelist.set_admin_block(session, user.id, False, admin.id, build_updater(timeout=8))
    record = await wl.client(user.public_id)
    R.check("Explicit unblock applies to new placement", record["body"]["enable"] is True)
    await bot.set_expiry(user, datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1))
    await bot.wl_admin(admin, "choose", third)
    await bot.process_due()
    record = await wl.client(user.public_id)
    R.check("Moving an expired client does not enable it",
            record["inboundIds"] == [third] and record["body"]["enable"] is False)
    ordinary = await std.client(user.public_id)
    R.check("Whitelist transfer leaves ordinary identity intact",
            ordinary["body"].get("uuid") == identity["uuid"])
    await engine.dispose()


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    try:
        await scenario(args.state)
    except Exception as exc:
        R.check("Scenario completed", False, f"{type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc()
    args.report.write_text(json.dumps(R.dump(), ensure_ascii=False, indent=2))
    print(R.summary(time.monotonic() - started))
    return int(any(not c["ok"] for c in R.checks))


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

"""Prepare a synthetic Happ account on the isolated acceptance stack for LAN use.

Only VLESS ports and GET /connection/<token> are exposed on the specified LAN IP.
Panel and SubHub admin APIs remain bound to loopback. No Telegram transport is used.
"""
from __future__ import annotations

import argparse
import asyncio
import ipaddress
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import asyncpg  # noqa: E402
import httpx  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app.config import Settings  # noqa: E402
from app.db.enums import UserRole  # noqa: E402
from ops.acceptance import whitelist_e2e as base  # noqa: E402


def docker(*args: str) -> str:
    result = subprocess.run(["docker", *args], text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"Docker {args[0]} failed: {result.stderr[-300:]}")
    return result.stdout.strip()


async def prepare(state: Path, lan: str, gateway_port: int) -> None:
    address = ipaddress.IPv4Address(lan)
    if not address.is_private or address.is_loopback or address.is_unspecified:
        raise ValueError("A private LAN IPv4 address is required")
    env = base.load_env(state)
    prefix = env["NET"].removesuffix("-net")
    if not re.fullmatch(r"[a-z][a-z0-9-]+", prefix) or prefix != "happacc":
        raise ValueError("Only the dedicated happacc fixture is supported")
    if (state / "happ-ready.json").exists():
        raise RuntimeError("Fixture already prepared; reuse its saved subscription")
    image = env["XUI_IMAGE"]
    panels = []
    for kind, api_port, vless_port, alias in (
        ("wl", 52355, 52443, "wl.acc.test"),
        ("std", 52356, 52444, "std.acc.test"),
    ):
        name = f"{prefix}-xui-{kind}"
        docker("rm", "-fv", name)
        docker("run", "-d", "--name", name, "--network", env["NET"],
               "--network-alias", alias, "-p", f"127.0.0.1:{api_port}:2053",
               "-p", f"{lan}:{vless_port}:{vless_port}", image)
        await asyncio.sleep(4)
        docker("exec", name, "/app/x-ui", "setting", "-username", env["XUI_USER"],
               "-password", env["XUI_PASS"], "-webBasePath", env["XUI_PATH"])
        docker("restart", name)
        panel = base.Panel(env[f"{kind.upper()}_PANEL"], env["XUI_USER"],
                           env["XUI_PASS"], name, image)
        for _ in range(30):
            try:
                await panel.inbounds()
                break
            except Exception:
                await asyncio.sleep(1)
        if await panel.allow_private_targets():
            await asyncio.sleep(3)
        inbound = await panel.ensure_inbound(vless_port, "Happ whitelist" if kind == "wl"
                                           else "Happ ordinary")
        panels.append((panel, inbound))

    config = state / "subhub.yaml"
    content = config.read_text().replace('public_host: "std.acc.test"',
                                         f'public_host: "{lan}"')
    content = content.replace('public_host: "wl.acc.test"', f'public_host: "{lan}"')
    config.write_text(content)
    docker("cp", str(config), f"{prefix}-subhub:/app/config.yaml")
    docker("restart", f"{prefix}-subhub")

    pg = env["PG_URL"]
    conn = await asyncpg.connect(pg.replace("+asyncpg", "") + "/postgres")
    try:
        await conn.execute('CREATE DATABASE "wlacc_happ"')
    finally:
        await conn.close()
    url = pg + "/wlacc_happ"
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT,
                   env=dict(os.environ, DATABASE_URL=url), check=True, capture_output=True)
    engine = create_async_engine(url)
    try:
        bot = base.Bot(async_sessionmaker(engine, expire_on_commit=False), Settings(
            bot_token="acceptance", database_url=url, admin_telegram_ids=[740001],
            subhub_url=env["SUBHUB_URL"], subhub_admin_token=env["SUBHUB_ADMIN_TOKEN"],
            xui_request_timeout=8,
        ))
        admin = await bot.user(740001, "happ_admin", UserRole.ADMIN)
        user = await bot.user(740002, "happ_android")
        await bot.add_server(admin, "add_standard",
                             f"Happ ordinary|LAN|{env['STD_PANEL']}|"
                             f"{env['XUI_USER']}|{env['XUI_PASS']}|direct")
        payment = await bot.subscribe(user)
        await bot.confirm(admin, payment.id)
        await bot.add_server(admin, "add_whitelist",
                             f"Happ whitelist|LAN|{env['WL_PANEL']}|"
                             f"{env['XUI_USER']}|{env['XUI_PASS']}|direct")
        await bot.wl_admin(admin, "choose", panels[0][1])
        await bot.wl_admin(admin, "rollout_strict")
        await bot.process_due()
        hub = base.SubHub(env["SUBHUB_URL"], env["SUBHUB_ADMIN_TOKEN"])
        await hub.sync()
        token = (await hub.tokens())[user.public_id.casefold()]
        links = await hub.links(token)
        if len(links) != 2:
            raise RuntimeError("Expected two active synthetic configurations")
        account = await bot.account(user)
        if account.free_bytes != 10 * base.GIB or account.paid_bytes != 0:
            raise RuntimeError("Synthetic balance differs from expected 10 GiB + 0")
        subscription = f"http://{lan}:{gateway_port}/connection/{token}"
        proxy = state / "happ-gateway.conf"
        proxy.write_text(
            "server { listen 8080; server_tokens off;\n"
            " location ~ ^/connection/[A-Za-z0-9_-]+$ {\n"
            "  limit_except GET { deny all; }\n"
            f"  proxy_pass http://{prefix}-subhub:8080;\n"
            "  proxy_set_header Host $host; }\n"
            " location / { return 404; }\n}\n"
        )
        docker("create", "--name", f"{prefix}-gateway", "--network", env["NET"],
               "-p", f"{lan}:{gateway_port}:8080", "nginx:alpine")
        docker("cp", str(proxy), f"{prefix}-gateway:/etc/nginx/conf.d/default.conf")
        docker("start", f"{prefix}-gateway")
        async with httpx.AsyncClient(trust_env=False) as http:
            for _ in range(20):
                try:
                    response = await http.get(subscription)
                    if response.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(1)
            else:
                raise RuntimeError("LAN subscription gateway is not reachable")
            denied = await http.get(f"http://{lan}:{gateway_port}/admin/servers")
            if denied.status_code != 404:
                raise RuntimeError("LAN gateway unexpectedly exposes admin API")
        result = {"subscription": subscription, "user_id": user.id,
                  "email": user.public_id, "database": "wlacc_happ",
                  "free_bytes": account.free_bytes, "paid_bytes": account.paid_bytes,
                  "ports": {"whitelist": 52443, "ordinary": 52444},
                  "image": image, "device": "Android / Happ 4.6.0"}
        target = state / "happ-ready.json"
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        target.chmod(0o600)
        print(subscription)
        print("Two test configurations; 10 GiB free, 0 purchased; admin gateway returns 404")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--lan-ip", required=True)
    parser.add_argument("--gateway-port", type=int, default=58580)
    args = parser.parse_args()
    asyncio.run(prepare(args.state, args.lan_ip, args.gateway_port))

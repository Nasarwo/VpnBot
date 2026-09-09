"""Real Go/PostgreSQL/SMTP smoke test, with Telegram and 3x-ui replaced by mocks.

Only runs against the explicit local compose.test.yml database. No production secrets.
Usage: DATABASE_URL=postgresql+asyncpg://dvpn_test:local-test-only@127.0.0.1:15432/dvpn_test
       .venv/bin/python -m tests.web_smoke [--serve]
Build /private/tmp/dvpn-api from VPNSite/backend first; apply migrations to the test DB.
"""

from __future__ import annotations

import asyncio
import base64
import os
import re
import secrets
import sys
from contextlib import suppress
from types import SimpleNamespace

import httpx
from aiohttp import web
from sqlalchemy import select

from app.config import Settings
from app.db.enums import Protocol, UserRole
from app.db.models import Server, ServerInbound, User, WebAccount, WebDelivery, WebLinkRequest
from app.db.session import get_engine, get_sessionmaker
from app.services import billing, web_bridge
from app.services.panel_updater import MockPanelUpdater

TEST_DB = "postgresql+asyncpg://dvpn_test:local-test-only@127.0.0.1:15432/dvpn_test"
BRIDGE_TOKEN = "local-test-bridge-token-32-characters-only"
PASSWORD = "Local-test-2026!"


class TelegramMock:
    def __init__(self):
        self.messages = []

    async def send_message(self, chat_id, text, **kwargs):
        self.messages.append((chat_id, text, kwargs))
        return SimpleNamespace(document=None)

    async def send_document(self, chat_id, document, **kwargs):
        self.messages.append((chat_id, "document", kwargs))
        return SimpleNamespace(document=SimpleNamespace(file_id="mock-receipt-file"))


async def code_from_mail(client, email, ignored=None):
    for _ in range(30):
        inbox = (await client.get("http://127.0.0.1:18025/api/v1/messages")).json()
        for message in inbox.get("messages", []):
            if message["ID"] == ignored:
                continue
            if any(recipient["Address"] == email for recipient in message["To"]):
                detail = (
                    await client.get(f"http://127.0.0.1:18025/api/v1/message/{message['ID']}")
                ).json()
                match = re.search(r": (\d{6})", detail["Text"])
                if match:
                    return match[1], message["ID"]
        await asyncio.sleep(0.1)
    raise AssertionError("SMTP message missing")


async def main():
    if os.environ.get("DATABASE_URL") != TEST_DB:
        raise SystemExit("Refusing anything except the explicit isolated local test database")
    settings = Settings(
        _env_file=None,
        database_url=TEST_DB,
        web_bridge_token=BRIDGE_TOKEN,
        web_bridge_port=18090,
        admin_telegram_ids=[999],
        subhub_url="http://127.0.0.1:18091",
        subhub_admin_token="mock-subhub-token",
        trial_period_days=3,
    )
    updater = MockPanelUpdater()
    web_bridge.build_updater = lambda **kwargs: updater
    bot = TelegramMock()
    async with get_sessionmaker()() as session:
        server = await session.scalar(select(Server).where(Server.name == "Test Netherlands"))
        if not server:
            server = Server(
                name="Test Netherlands",
                country="NL",
                panel_url="http://127.0.0.1:18091",
                username="mock",
                password="mock",
                enabled=True,
                is_online=True,
            )
            session.add(server)
            await session.flush()
            session.add(
                ServerInbound(
                    server_id=server.id, inbound_id=1, protocol=Protocol.VLESS, enabled=True
                )
            )
            await session.commit()

    async def resolve(request):
        payload = await request.json()
        return web.json_response(
            {
                "email": payload["email"],
                "subscription_url": "https://example.test/connection/mock-subscription",
                "raw_subscription_url": "https://example.test/connection/raw/mock-subscription",
                "happ_url": "https://example.test/happ/mock-subscription",
            }
        )

    hub = web.Application()
    hub.router.add_post("/admin/subscriptions/resolve", resolve)
    hub.router.add_post("/admin/sync", lambda _: web.Response(status=202))
    hub_runner = web.AppRunner(hub)
    await hub_runner.setup()
    await web.TCPSite(hub_runner, "127.0.0.1", 18091).start()
    runner = await web_bridge.start_bridge(bot, settings)
    worker = asyncio.create_task(web_bridge.delivery_loop(bot))
    env = dict(
        os.environ,
        DATABASE_URL=TEST_DB.replace("+asyncpg", ""),
        PUBLIC_ORIGIN="http://localhost:5173",
        WEB_BRIDGE_TOKEN=BRIDGE_TOKEN,
        AUTH_SECRET="local-test-auth-secret-32-characters-only",
        COOKIE_SECURE="false",
        BOT_BRIDGE_URL="http://127.0.0.1:18090",
        SMTP_HOST="127.0.0.1",
        SMTP_PORT="11025",
        SMTP_FROM="noreply@example.test",
        SMTP_ALLOW_INSECURE="true",
        PAYMENT_DETAILS_TEXT="Тестовые реквизиты — переводить деньги не нужно.",
    )
    proc = await asyncio.create_subprocess_exec("/private/tmp/dvpn-api", env=env)
    try:
        async with httpx.AsyncClient(
            base_url="http://127.0.0.1:8081",
            timeout=20,
            headers={"Origin": "http://localhost:5173"},
        ) as client:
            for _attempt in range(50):
                try:
                    if (await client.get("/api/health")).status_code == 200:
                        break
                except httpx.ConnectError:
                    pass
                await asyncio.sleep(0.1)
            else:
                raise AssertionError("Go API did not start")

            async def post(path, data, status=200):
                response = await client.post(path, json=data)
                assert response.status_code == status, (path, response.status_code, response.text)
                return response

            suffix = secrets.token_hex(4)
            email = f"smoke-{suffix}@example.test"
            credentials = {"email": email, "password": PASSWORD}
            await post("/api/auth/register", credentials)
            code, mail_id = await code_from_mail(client, email)
            await post("/api/auth/login", credentials, 401)
            await post("/api/auth/verify", dict(credentials, code="invalid"), 400)
            verified = await post("/api/auth/verify", dict(credentials, code=code))
            assert "HttpOnly" in verified.headers["set-cookie"]
            profile = (await client.get("/api/account/profile")).json()
            assert profile["email"] == email and not profile["telegram_linked"]
            await post("/api/account/trial", {}, 409)
            assert (await client.get("/api/account/connection")).status_code == 403
            rejected = await client.post(
                "/api/logout", json={}, headers={"Origin": "https://evil.test"}
            )
            assert rejected.status_code == 403
            await post("/api/account/payment", {"plan": "1m", "comment": "Test payment"}, 201)
            await post("/api/account/payment", {"plan": "12m", "comment": "Duplicate"}, 409)
            profile = (await client.get("/api/account/profile")).json()
            assert len(profile["payments"]) == 1
            payment_id = profile["payments"][0]["id"]
            assert profile["payments"][0]["amount"] == 175
            await post("/api/account/link", {"public_id": "anything"}, 409)
            async with get_sessionmaker()() as session:
                result = await billing.confirm_payment(session, payment_id, None, updater)
                assert result.applied
                repeated = await billing.confirm_payment(session, payment_id, None, updater)
                assert repeated.already_applied
            profile = (await client.get("/api/account/profile")).json()
            assert profile["active"] and profile["payments"][0]["status"] == "applied"
            connection = (await client.get("/api/account/connection")).json()
            assert connection["url"].startswith("https://example.test/")

            await post("/api/auth/forgot", {"email": email})
            reset_code, _ = await code_from_mail(client, email, mail_id)
            await post(
                "/api/auth/reset",
                {"email": email, "password": PASSWORD + "new", "code": reset_code},
            )
            assert (await client.get("/api/account/profile")).status_code == 401
            await post("/api/auth/login", credentials, 401)
            credentials["password"] = PASSWORD + "new"
            await post("/api/auth/login", credentials)
            await post("/api/logout", {})
            assert (await client.get("/api/account/profile")).status_code == 401

            # Independent account: binding requires admin approval and opens trial.
            second_email = f"link-{suffix}@example.test"
            second = {"email": second_email, "password": PASSWORD}
            await post("/api/auth/register", second)
            second_code, _ = await code_from_mail(client, second_email)
            await post("/api/auth/verify", dict(second, code=second_code))
            async with get_sessionmaker()() as session:
                target = User(
                    telegram_id=int(suffix, 16) + 10000000000,
                    public_id="TG" + suffix,
                    role=UserRole.USER,
                    onboarding_done=True,
                )
                session.add(target)
                await session.commit()
                target_public = target.public_id
            await post("/api/account/link", {"public_id": target_public}, 201)
            await post("/api/account/payment", {"plan": "1m", "comment": "During link"}, 409)
            async with get_sessionmaker()() as session:
                account = await session.scalar(
                    select(WebAccount).where(WebAccount.email == second_email)
                )
                link = await session.scalar(
                    select(WebLinkRequest).where(WebLinkRequest.account_id == account.id)
                )
                assert await web_bridge.decide_link(session, link.id, True) == "Привязка одобрена"
            profile = (await client.get("/api/account/profile")).json()
            assert profile["telegram_linked"] and profile["trial_available"]
            await post("/api/account/trial", {})
            await post("/api/account/trial", {}, 409)
            profile = (await client.get("/api/account/profile")).json()
            assert profile["active"] and not profile["trial_available"]
            await post(
                "/api/account/payment",
                {"plan": "6m", "receipt": base64.b64encode(b"%PDF-1.7\nMock").decode()},
                201,
            )
            for _ in range(50):
                async with get_sessionmaker()() as session:
                    due = await session.scalar(
                        select(WebDelivery.id).where(WebDelivery.status == "pending").limit(1)
                    )
                if due is None:
                    break
                await asyncio.sleep(0.2)
            assert due is None, "Telegram outbox did not drain"
            assert any(message[1] == "document" for message in bot.messages)
            assert any("Источник: сайт" in message[1] for message in bot.messages)
            print(
                "PASS: registration, SMTP code, login, CSRF, payment, duplicate confirmation, "
                "SubHub, password reset/session revocation, binding approval, trial, PDF delivery",
                flush=True,
            )
            if "--serve" in sys.argv:
                print(f"LOCAL TEST PREVIEW: email={email} password={PASSWORD}new", flush=True)
                await asyncio.Event().wait()
    finally:
        worker.cancel()
        with suppress(asyncio.CancelledError):
            await worker
        if runner:
            await runner.cleanup()
        await hub_runner.cleanup()
        if proc.returncode is None:
            proc.terminate()
            await proc.wait()
        await get_engine().dispose()


if __name__ == "__main__":
    asyncio.run(main())

"""Одноразовый trial по Telegram ID переживает сброс бота (новый ``User``)."""
from __future__ import annotations

import asyncio
from weakref import WeakValueDictionary

import aiohttp
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.bot import user_handlers
from app.config import Settings
from app.db.base import Base
from app.db.enums import Protocol, UserRole
from app.db.models import Server, ServerInbound, TrialGrant, User, WebAccount
from app.db.repositories import UserRepository
from app.services import billing, operation_lock, web_bridge
from app.services.panel_updater import MockPanelUpdater
from tests.test_user_reset import _reset
from tests.test_whitelist import std_target  # noqa: F401


async def _fresh(session, telegram_id) -> User:
    session.expire_all()
    fresh = await UserRepository(session).get_by_telegram_id(telegram_id)
    assert fresh is not None
    return fresh


async def _trial(session, user_id, panel):
    return await billing.grant_trial(session, user_id, panel, period_days=3)


async def _grants(session) -> list[TrialGrant]:
    return (await session.scalars(select(TrialGrant))).all()


async def test_trial_after_bot_reset_is_refused(session, user, std_target):  # noqa: F811
    panel = MockPanelUpdater()
    telegram_id, old_id = user.telegram_id, user.id
    first = await _trial(session, user.id, panel)
    assert first.applied
    identities = list(panel.provisioned)
    assert identities

    callback = await _reset(session, user)
    assert callback.alerts[-1] == "Данные сброшены"
    fresh = await _fresh(session, telegram_id)
    assert fresh.trial_used is False

    second = await _trial(session, fresh.id, panel)

    assert not second.applied and second.already_used
    # Вторая идентичность на панели не создана.
    assert panel.provisioned == identities
    assert not await user_handlers._trial_available(session, fresh)
    [grant] = await _grants(session)
    assert (grant.telegram_id, grant.user_id) == (telegram_id, old_id)


async def test_other_telegram_id_still_gets_trial(session, user, std_target):  # noqa: F811
    panel = MockPanelUpdater()
    assert (await _trial(session, user.id, panel)).applied
    await _reset(session, user)

    other = User(telegram_id=654321, username="other", role=UserRole.USER)
    session.add(other)
    await session.commit()
    assert await user_handlers._trial_available(session, other)

    result = await _trial(session, other.id, panel)

    assert result.applied
    assert {g.telegram_id for g in await _grants(session)} == {user.telegram_id, 654321}


async def test_failed_trial_is_not_recorded_and_can_be_retried(
    session, user, std_target  # noqa: F811
):
    telegram_id, user_id = user.telegram_id, user.id
    failing = MockPanelUpdater(fail_server_ids={std_target.id})
    failed = await _trial(session, user_id, failing)
    assert not failed.applied and failed.failed_servers
    await session.rollback()  # как сессия запроса бота после обработчика
    assert await _grants(session) == []

    # Ни сброс после неудачи, ни повтор не считаются использованием trial.
    await _reset(session, await session.get(User, user_id))
    fresh = await _fresh(session, telegram_id)
    assert await user_handlers._trial_available(session, fresh)
    retry = await _trial(session, fresh.id, MockPanelUpdater())

    assert retry.applied
    [grant] = await _grants(session)
    assert (grant.telegram_id, grant.user_id) == (telegram_id, fresh.id)


# --- Файловая SQLite: перезапуск процесса и параллельные запросы -----------------


async def _file_db(tmp_path, *, targets: bool):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'bot.sqlite3'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        user = User(telegram_id=4242, username="u", role=UserRole.USER, onboarding_done=True)
        server = Server(name="std", panel_url="http://panel.local", username="a", password="b")
        session.add_all([user, server])
        await session.flush()
        if targets:
            session.add(
                ServerInbound(server_id=server.id, inbound_id=1, protocol=Protocol.VLESS)
            )
        await session.commit()
        return engine, maker, user.id


async def test_refusal_survives_process_restart(tmp_path, monkeypatch):
    engine, maker, user_id = await _file_db(tmp_path, targets=True)
    async with maker() as session:
        assert (await _trial(session, user_id, MockPanelUpdater())).applied
        callback = await _reset(session, await session.get(User, user_id))
        assert callback.alerts[-1] == "Данные сброшены"
    await engine.dispose()

    # Новый процесс: пустые in-process блокировки, новый движок и сессия.
    monkeypatch.setattr(operation_lock, "_locks", WeakValueDictionary())
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'bot.sqlite3'}")
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    panel = MockPanelUpdater()
    try:
        async with maker() as session:
            fresh = await _fresh(session, 4242)
            assert fresh.trial_used is False
            result = await _trial(session, fresh.id, panel)
    finally:
        await engine.dispose()

    assert not result.applied and result.already_used
    assert panel.provisioned == []


class _SlowPanel(MockPanelUpdater):
    async def provision_server(self, server, spec, expiry_ms):
        await asyncio.sleep(0.05)
        await super().provision_server(server, spec, expiry_ms)


async def test_parallel_trial_requests_grant_once(tmp_path):
    engine, maker, user_id = await _file_db(tmp_path, targets=True)
    panel = _SlowPanel()

    async def request():
        async with maker() as session:
            return await _trial(session, user_id, panel)

    try:
        results = await asyncio.gather(request(), request(), request())
        async with maker() as session:
            grants = await session.scalar(select(func.count()).select_from(TrialGrant))
    finally:
        await engine.dispose()

    assert sorted(r.applied for r in results) == [False, False, True]
    assert sum(r.already_used for r in results) == 2
    assert len(panel.provisioned) == 1
    assert grants == 1


# --- Связанный аккаунт сайта ----------------------------------------------------


@pytest.fixture
async def bridge(session, monkeypatch):
    """Внутренний HTTP-мост сайта на свободном локальном порту и тестовой БД."""
    maker = async_sessionmaker(session.bind, expire_on_commit=False, class_=AsyncSession)
    panel = MockPanelUpdater()
    monkeypatch.setattr(web_bridge, "get_sessionmaker", lambda: maker)
    monkeypatch.setattr(web_bridge, "build_updater", lambda **_: panel)

    async def no_sync(*_args, **_kwargs):
        return None

    monkeypatch.setattr(web_bridge, "trigger_configured_sync", no_sync)
    token = "t" * 32
    settings = Settings(web_bridge_token=token, web_bridge_port=0)
    runner = await web_bridge.start_bridge(None, settings)
    host, port = runner.addresses[0][:2]

    async def call(action, account_id):
        async with aiohttp.ClientSession() as http:
            async with http.post(
                f"http://{host}:{port}/internal/{action}",
                json={"account_id": account_id},
                headers={"X-Bridge-Token": token},
            ) as response:
                return response.status, await response.json()

    try:
        yield call, panel
    finally:
        await runner.cleanup()


async def test_site_linked_after_reset_cannot_take_trial_again(
    session, user, std_target, bridge  # noqa: F811
):
    call, panel = bridge
    telegram_id = user.telegram_id
    assert (await _trial(session, user.id, MockPanelUpdater())).applied
    await _reset(session, user)
    fresh = await _fresh(session, telegram_id)
    # Аккаунт сайта привязан к новому User того же Telegram ID.
    account = WebAccount(email="u@example.com", password_hash="x", verified=True,
                         user_id=fresh.id)
    session.add(account)
    await session.commit()

    status, profile = await call("profile", account.id)
    assert status == 200 and profile["trial_available"] is False
    status, _ = await call("trial", account.id)

    assert status == 409
    assert panel.provisioned == []
    assert len(await _grants(session)) == 1

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.enums import Protocol, UserRole
from app.db.models import ClientServerMapping, Server, User, VpnClient


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as s:
        yield s

    await engine.dispose()


@pytest_asyncio.fixture
async def user(session: AsyncSession) -> User:
    u = User(
        telegram_id=123456,
        username="testuser",
        first_name="Test",
        role=UserRole.USER,
    )
    session.add(u)
    await session.commit()
    return u


@pytest_asyncio.fixture
async def admin(session: AsyncSession) -> User:
    u = User(
        telegram_id=999,
        username="admin",
        first_name="Admin",
        role=UserRole.ADMIN,
    )
    session.add(u)
    await session.commit()
    return u


@pytest_asyncio.fixture
async def server(session: AsyncSession) -> Server:
    srv = Server(
        name="srv-1",
        country="NL",
        panel_url="http://panel.local:2053",
        username="admin",
        password="secret",
        enabled=True,
    )
    session.add(srv)
    await session.commit()
    return srv


@pytest_asyncio.fixture
async def vpn_client(session: AsyncSession, user: User, server: Server) -> VpnClient:
    client = VpnClient(
        user_id=user.id,
        display_name="Test client",
        email="test@local",
        expires_at=None,
        is_active=False,
        subscription_url_direct="https://sub.example/direct/abc",
    )
    session.add(client)
    await session.flush()
    mapping = ClientServerMapping(
        vpn_client_id=client.id,
        server_id=server.id,
        inbound_id=1,
        protocol=Protocol.VLESS,
        client_uuid="uuid-1",
        email="test@local",
        enabled=True,
    )
    session.add(mapping)
    await session.commit()
    return client


def utcnow() -> datetime:
    return datetime.now(tz=UTC)


def days_from_now(days: int) -> datetime:
    return utcnow() + timedelta(days=days)

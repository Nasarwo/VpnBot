"""Serialize access mutations per user, including commits and panel calls."""
from __future__ import annotations

import asyncio
import inspect
from contextlib import asynccontextmanager
from functools import wraps
from weakref import WeakValueDictionary

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.db.models import PaymentRequest, VpnClient

_locks: WeakValueDictionary = WeakValueDictionary()


@asynccontextmanager
async def user_operation(session, user_id):
    # Local serialization prevents waiting operations consuming pooled DB connections.
    key = (asyncio.get_running_loop(), user_id)
    lock = _locks.setdefault(key, asyncio.Lock())
    async with lock:
        bind = session.get_bind()
        if bind.dialect.name != "postgresql":
            yield
            return
        # An independent connection keeps the advisory lock across session commits.
        # NullPool avoids starving the application's transaction pool.
        engine = create_async_engine(bind.url, poolclass=NullPool)
        try:
            async with engine.connect() as connection:
                await connection.execute(
                    text("SELECT pg_advisory_lock(176884, :owner)"), {"owner": user_id}
                )
                try:
                    yield
                finally:
                    await connection.execute(
                        text("SELECT pg_advisory_unlock(176884, :owner)"), {"owner": user_id}
                    )
        finally:
            await engine.dispose()


def serialized_access(id_name, entity):
    def decorate(function):
        signature = inspect.signature(function)

        @wraps(function)
        async def wrapped(*args, **kwargs):
            values = signature.bind(*args, **kwargs).arguments
            session = values["session"]
            identifier = values[id_name]
            if entity in ("user", "user_object"):
                owner = identifier.id if entity == "user_object" else identifier
            else:
                model = PaymentRequest if entity == "payment" else VpnClient
                if entity == "pending":
                    identifier = identifier.vpn_client_id
                owner = await session.scalar(select(model.user_id).where(model.id == identifier))
            if owner is None:
                return await function(*args, **kwargs)
            async with user_operation(session, owner):
                if session.get_bind().dialect.name == "postgresql":
                    if entity == "pending":
                        await session.refresh(values[id_name])
                    await session.execute(
                        select(VpnClient).where(VpnClient.user_id == owner)
                        .execution_options(populate_existing=True)
                    )
                return await function(*args, **kwargs)
        return wrapped
    return decorate

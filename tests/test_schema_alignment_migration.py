"""Migration head must agree with ORM metadata after upgrading the GitHub schema."""
from __future__ import annotations

import asyncio

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.db.base import Base
from tests.test_migrations_pg import _reset_schema
from tests.test_trial_grants_migration import _alembic
from tests.test_whitelist_pg import PG_URL


async def _schema(url):
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            def read(sync):
                columns = inspect(sync).get_columns("servers")
                length = next(c["type"].length for c in columns if c["name"] == "password")
                drift = compare_metadata(
                    MigrationContext.configure(sync, opts={"compare_type": True}),
                    Base.metadata,
                )
                saved = sync.execute(text("SELECT password FROM servers WHERE id=1")).scalar()
                return length, drift, saved
            return await conn.run_sync(read)
    finally:
        await engine.dispose()


@pytest.mark.parametrize("postgres", [
    False,
    pytest.param(True, marks=pytest.mark.skipif(not PG_URL, reason="VPNBOT_TEST_PG_URL unset")),
])
def test_github_schema_upgrades_without_model_drift_or_data_loss(tmp_path, monkeypatch, postgres):
    url = PG_URL if postgres else f"sqlite+aiosqlite:///{tmp_path / 'migration.sqlite'}"
    if postgres:
        asyncio.run(_reset_schema())
    config = _alembic(monkeypatch, url)
    try:
        # GitHub main currently ends here; local review fixes extend this chain.
        command.upgrade(config, "a4b5c6d7e8f9")

        async def seed():
            engine = create_async_engine(url)
            try:
                async with engine.begin() as conn:
                    await conn.execute(text(
                        "INSERT INTO servers "
                        "(id,name,panel_url,username,password,country,enabled,created_at) "
                        "VALUES (1,'test','https://panel.invalid','test','ciphertext','NL',true,"
                        "CURRENT_TIMESTAMP)"
                    ))
            finally:
                await engine.dispose()
        asyncio.run(seed())
        command.upgrade(config, "head")
        length, drift, saved = asyncio.run(_schema(url))
        assert length == 1024
        assert drift == []
        assert saved == "ciphertext"

        command.downgrade(config, "e3f4a5b6c7d8")
        assert asyncio.run(_schema(url))[0] == 512
        command.upgrade(config, "head")
        assert asyncio.run(_schema(url)) == (1024, [], "ciphertext")

        async def store_long_password():
            engine = create_async_engine(url)
            try:
                async with engine.begin() as conn:
                    await conn.execute(
                        text("UPDATE servers SET password=:value WHERE id=1"),
                        {"value": "x" * 600},
                    )
            finally:
                await engine.dispose()
        asyncio.run(store_long_password())
        with pytest.raises(RuntimeError, match="downgrade is unsafe"):
            command.downgrade(config, "e3f4a5b6c7d8")
        assert asyncio.run(_schema(url)) == (1024, [], "x" * 600)
    finally:
        get_settings.cache_clear()

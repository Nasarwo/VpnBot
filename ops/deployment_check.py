"""Run against a restored scratch database only; never calls real panel APIs."""
import asyncio
import os

os.environ["DATABASE_URL"] = os.environ["DATABASE_URL"].rsplit("/", 1)[0] + "/vpnbot_restorecheck"

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.db.enums import PaymentStatus
from app.db.models import User, VpnClient
from app.db.repositories import PaymentRepository
from app.db.session import get_engine, get_sessionmaker
from app.services import billing
from app.services.operation_lock import user_operation
from app.services.panel_updater import MockPanelUpdater


async def main():
    factory = get_sessionmaker()
    async with factory() as session:
        user = await session.scalar(select(User).join(VpnClient).limit(1))
        client = await session.scalar(select(VpnClient).where(VpnClient.user_id == user.id))
        client.expires_at = datetime.now(UTC) + timedelta(days=10)
        base = client.expires_at
        import secrets
        repo = PaymentRepository(session)
        first = await repo.create(user_id=user.id, amount=850, period_days=180,
                                  payment_code="TEST-" + secrets.token_hex(4), currency="RUB",
                                  status=PaymentStatus.WAITING_ADMIN)
        second = await repo.create(user_id=user.id, amount=850, period_days=180,
                                   payment_code="TEST-" + secrets.token_hex(4), currency="RUB",
                                   status=PaymentStatus.WAITING_ADMIN)
        await session.commit()
        owner, ids = user.id, (first.id, second.id)

    async def confirm(identifier):
        async with factory() as session:
            return await billing.confirm_payment(session, identifier, None, MockPanelUpdater())

    await asyncio.gather(*(confirm(i) for i in ids))
    async with factory() as session:
        client = await session.scalar(select(VpnClient).where(VpnClient.user_id == owner))
        assert client.expires_at == base + timedelta(days=360), "lost paid period"
        original = client.expires_at
        await billing.confirm_payment(session, ids[0], None, MockPanelUpdater())
        await session.refresh(client)
        assert client.expires_at == original, "duplicate credit"

    # Exercise PostgreSQL advisory lock across commit and exceptional exit.
    async with factory() as session:
        try:
            async with user_operation(session, owner):
                await session.commit()
                raise RuntimeError("interruption")
        except RuntimeError:
            pass
        await asyncio.wait_for(check_released(session, owner), timeout=5)
    print("PostgreSQL: concurrent periods, idempotency, lock release verified")
    await get_engine().dispose()


async def check_released(session, owner):
    async with user_operation(session, owner):
        pass


asyncio.run(main())

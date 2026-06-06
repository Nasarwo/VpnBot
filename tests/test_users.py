from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import UserRepository


async def test_get_or_create_assigns_public_id(session: AsyncSession):
    repo = UserRepository(session)
    user, created = await repo.get_or_create(
        telegram_id=555, username="u", first_name="U"
    )
    await session.commit()
    assert created is True
    assert user.public_id
    assert len(user.public_id) == 8


async def test_public_id_is_stable_and_unique(session: AsyncSession):
    repo = UserRepository(session)
    u1, _ = await repo.get_or_create(telegram_id=1, username="a", first_name="A")
    u2, _ = await repo.get_or_create(telegram_id=2, username="b", first_name="B")
    await session.commit()
    assert u1.public_id != u2.public_id

    again, created = await repo.get_or_create(
        telegram_id=1, username="a", first_name="A"
    )
    assert created is False
    assert again.public_id == u1.public_id


async def test_backfills_public_id_for_existing(session: AsyncSession):
    from app.db.enums import UserRole
    from app.db.models import User

    user = User(telegram_id=777, username="old", first_name="Old", role=UserRole.USER)
    session.add(user)
    await session.commit()
    assert user.public_id is None

    repo = UserRepository(session)
    same, created = await repo.get_or_create(
        telegram_id=777, username="old", first_name="Old"
    )
    await session.commit()
    assert created is False
    assert same.public_id is not None

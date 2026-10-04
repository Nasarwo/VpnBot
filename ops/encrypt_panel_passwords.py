"""Idempotently encrypt existing panel credentials with configured SECRET_KEY."""
import asyncio

from sqlalchemy import text

from app.config import get_settings
from app.crypto import decrypt, encrypt, is_encrypted
from app.db.session import get_engine, get_sessionmaker


async def main():
    assert get_settings().secret_key, "SECRET_KEY is required"
    async with get_sessionmaker()() as session:
        rows = (await session.execute(text("SELECT id,password FROM servers FOR UPDATE"))).all()
        for identifier, value in rows:
            encoded = encrypt(value)
            assert is_encrypted(encoded) and decrypt(encoded) == decrypt(value)
            await session.execute(
                text("UPDATE servers SET password=:value WHERE id=:id"),
                {"id": identifier, "value": encoded},
            )
        await session.commit()
        count = await session.scalar(text(
            "SELECT count(*) FROM servers WHERE password NOT LIKE 'enc::%'"
        ))
        assert count == 0
        print(f"Encrypted and verified {len(rows)} panel credentials")
    await get_engine().dispose()


asyncio.run(main())

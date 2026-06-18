"""Тесты шифрования секретов в БД (пароли панелей).

Проверяют:
- round-trip encrypt/decrypt при заданном SECRET_KEY;
- обратную совместимость: legacy-значения в открытом виде читаются как есть;
- без SECRET_KEY значения проходят насквозь (dev-режим);
- неверный ключ не позволяет расшифровать (нет «тихой» подмены);
- на уровне ORM пароль сервера хранится в БД зашифрованным, а читается открытым.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import crypto
from app.config import Settings
from app.db.models import Server


@pytest.fixture
def secret_key(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Включает шифрование с тестовым ключом и сбрасывает кеш Fernet."""
    key = "unit-test-secret-key"
    monkeypatch.setattr(crypto, "get_settings", lambda: Settings(secret_key=key))
    crypto._fernet.cache_clear()
    yield key
    crypto._fernet.cache_clear()


@pytest.fixture
def no_key(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(crypto, "get_settings", lambda: Settings(secret_key=""))
    crypto._fernet.cache_clear()
    yield
    crypto._fernet.cache_clear()


def test_encrypt_decrypt_round_trip(secret_key: str) -> None:
    plaintext = "Super_Secret_Panel_Pass_123"
    token = crypto.encrypt(plaintext)
    assert token != plaintext
    assert crypto.is_encrypted(token)
    assert plaintext not in token  # шифротекст не содержит исходный пароль
    assert crypto.decrypt(token) == plaintext


def test_encrypt_is_idempotent_on_already_encrypted(secret_key: str) -> None:
    token = crypto.encrypt("pw")
    assert crypto.encrypt(token) == token


def test_decrypt_passes_through_legacy_plaintext(secret_key: str) -> None:
    # Значение без маркера enc:: считается legacy-данными в открытом виде.
    assert crypto.decrypt("legacy_plain_password") == "legacy_plain_password"


def test_without_key_values_pass_through(no_key: None) -> None:
    assert crypto.encrypt("pw") == "pw"
    assert crypto.decrypt("pw") == "pw"


def test_wrong_key_cannot_decrypt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(crypto, "get_settings", lambda: Settings(secret_key="key-a"))
    crypto._fernet.cache_clear()
    token = crypto.encrypt("pw")

    monkeypatch.setattr(crypto, "get_settings", lambda: Settings(secret_key="key-b"))
    crypto._fernet.cache_clear()
    with pytest.raises(RuntimeError):
        crypto.decrypt(token)
    crypto._fernet.cache_clear()


async def test_server_password_encrypted_at_rest(
    session: AsyncSession, secret_key: str
) -> None:
    srv = Server(
        name="enc-srv",
        panel_url="http://panel.local:2053",
        username="admin",
        password="PlainPanelPass",
        enabled=True,
    )
    session.add(srv)
    await session.commit()
    sid = srv.id
    session.expunge_all()

    # Сырое значение в БД — зашифровано (минуя ORM-расшифровку).
    raw = (
        await session.execute(
            text("SELECT password FROM servers WHERE id = :id"), {"id": sid}
        )
    ).scalar_one()
    assert crypto.is_encrypted(raw)
    assert "PlainPanelPass" not in raw

    # Через ORM — расшифровано прозрачно.
    loaded = await session.get(Server, sid)
    assert loaded is not None
    assert loaded.password == "PlainPanelPass"

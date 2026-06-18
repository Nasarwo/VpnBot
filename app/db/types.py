from __future__ import annotations

from typing import Any

from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

from app import crypto


class EncryptedString(TypeDecorator):
    """Прозрачно шифрует значение при записи и расшифровывает при чтении.

    - Если SECRET_KEY не задан — значения хранятся в открытом виде (dev/тесты).
    - Старые записи в открытом виде читаются без ошибок: см. crypto.decrypt
      (обратная совместимость с БД, заполненной до включения шифрования).
    - При следующей перезаписи такого сервера пароль шифруется автоматически.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect: Any) -> str | None:
        if value is None:
            return None
        return crypto.encrypt(value)

    def process_result_value(self, value: str | None, dialect: Any) -> str | None:
        if value is None:
            return None
        return crypto.decrypt(value)

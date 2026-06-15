from __future__ import annotations

import base64
import hashlib
import logging
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

logger = logging.getLogger(__name__)

# Маркер зашифрованного значения в БД. Позволяет отличать зашифрованные
# данные от legacy-значений в открытом виде (обратная совместимость).
_PREFIX = "enc::"


@lru_cache
def _fernet() -> Fernet | None:
    """Возвращает Fernet, выведенный из SECRET_KEY, либо None если ключ не задан.

    SECRET_KEY может быть произвольной строкой-парольной фразой: из неё
    детерминированно выводится 32-байтный ключ Fernet (SHA-256).
    """
    secret = get_settings().secret_key
    if not secret:
        return None
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def is_encrypted(value: str) -> bool:
    return value.startswith(_PREFIX)


def encrypt(value: str) -> str:
    """Шифрует строку. Без SECRET_KEY возвращает значение как есть (dev/тесты)."""
    fernet = _fernet()
    if fernet is None:
        return value
    if is_encrypted(value):
        return value
    token = fernet.encrypt(value.encode("utf-8")).decode("ascii")
    return _PREFIX + token


def decrypt(value: str) -> str:
    """Расшифровывает строку. Legacy-значения в открытом виде возвращает как есть."""
    if not is_encrypted(value):
        return value
    fernet = _fernet()
    if fernet is None:
        raise RuntimeError(
            "Значение в БД зашифровано, но SECRET_KEY не задан — расшифровать "
            "невозможно. Укажите тот же SECRET_KEY, что использовался при записи."
        )
    try:
        return fernet.decrypt(value[len(_PREFIX):].encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError(
            "Не удалось расшифровать значение (неверный SECRET_KEY?)."
        ) from exc

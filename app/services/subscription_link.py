from __future__ import annotations

import re
from urllib.parse import urlparse

# Допустимые символы ID подписки (hex, буквы, цифры, дефис, подчёркивание).
_PUBLIC_ID_CHARS_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_MIN_LEN_FROM_URL = 1
_MIN_LEN_BARE = 3
_MAX_LEN = 64


def _is_valid_public_id(value: str, *, from_url: bool) -> bool:
    if not value or len(value) > _MAX_LEN:
        return False
    min_len = _MIN_LEN_FROM_URL if from_url else _MIN_LEN_BARE
    if len(value) < min_len:
        return False
    return _PUBLIC_ID_CHARS_RE.match(value) is not None


def parse_subscription_public_id(link: str) -> str | None:
    """Извлекает ID подписки из последнего сегмента URL.

    Примеры:
    - https://host:2096/sub/AB12CD34 -> AB12CD34
    - https://host:2096/subscribe/legacy-id -> legacy-id
    """
    raw = (link or "").strip()
    if not raw:
        return None
    # Если прислали только ID без URL.
    if "://" not in raw and _is_valid_public_id(raw, from_url=False):
        return raw
    try:
        parsed = urlparse(raw)
    except ValueError:
        return None
    if not parsed.scheme or not parsed.netloc:
        return None
    path = parsed.path.strip("/")
    if not path:
        return None
    public_id = path.split("/")[-1].strip()
    if not _is_valid_public_id(public_id, from_url=True):
        return None
    return public_id


SUBSCRIPTION_LINK_EXAMPLE = "https://example.com:2096/sub/ID"


def subscription_link_example() -> str:
    """Абстрактный пример ссылки для подсказки пользователю (без реального домена)."""
    return SUBSCRIPTION_LINK_EXAMPLE

from __future__ import annotations

import re
from urllib.parse import urlparse

# Допустимые символы ID подписки в конце URL (hex, буквы, цифры, дефис).
_PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9_-]{4,64}$")


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
    if "://" not in raw and _PUBLIC_ID_RE.match(raw):
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
    if not public_id or not _PUBLIC_ID_RE.match(public_id):
        return None
    return public_id


SUBSCRIPTION_LINK_EXAMPLE = "https://example.com:2096/sub/ID"


def subscription_link_example() -> str:
    """Абстрактный пример ссылки для подсказки пользователю (без реального домена)."""
    return SUBSCRIPTION_LINK_EXAMPLE

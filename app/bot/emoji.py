from __future__ import annotations

"""Анимированные кастом-эмодзи из набора RestrictedEmoji.

Владелец бота имеет Telegram Premium, поэтому бот может использовать кастом-эмодзи
в личных сообщениях. На кнопках значок задаётся полем icon_custom_emoji_id,
в тексте — через HTML-тег <tg-emoji emoji-id="...">unicode</tg-emoji>.

Если клиент не поддерживает кастом-эмодзи, на кнопке значок просто не покажется,
а в тексте отрендерится обычный unicode-эмодзи (graceful degradation).

id получены через getStickerSet(name="RestrictedEmoji").
"""

# name -> (unicode-фоллбэк, custom_emoji_id)
ICONS: dict[str, tuple[str, str]] = {
    "buy": ("\U0001f6d2", "5431499171045581032"),       # 🛒 оформить подписку
    "subscription": ("\U0001faaa", "5422683699130933153"),  # 🪪 моя подписка
    "support": ("\U0001f4ac", "5465300082628763143"),   # 💬 поддержка
    "extend": ("\U0001f504", "5264727218734524899"),    # 🔄 продлить
    "connect": ("\U0001f517", "5375129357373165375"),   # 🔗 подключение
    "trial": ("\U0001f381", "5199749070830197566"),     # 🎁 пробный доступ
    "paid": ("\U0001f4b0", "5375296873982604963"),      # 💰 платный тариф
    "back": ("\U0001f448", "5469735272017043817"),      # 👈 назад
    "cancel": ("\u274c", "5465665476971471368"),        # ❌ отмена
    "add": ("\u2795", "5226945370684140473"),           # ➕ добавить
    "server": ("\U0001f6f0", "5321304062715517873"),    # 🛰 сервер
    "ok": ("\u2705", "5427009714745517609"),            # ✅ сервер доступен
    "down": ("\u274c", "5465665476971471368"),          # ❌ сервер недоступен
    "unknown": ("\u2753", "5467666648263564704"),       # ❓ статус неизвестен
}


def emoji_char(name: str) -> str:
    """Возвращает unicode-символ значка (без анимации)."""
    return ICONS[name][0]


def custom_emoji_id(name: str) -> str | None:
    """Возвращает custom_emoji_id значка или None, если значок не найден."""
    item = ICONS.get(name)
    return item[1] if item else None


def tg(name: str) -> str:
    """HTML-строка с анимированным значком для вставки в текст сообщения."""
    item = ICONS.get(name)
    if item is None:
        return ""
    char, emoji_id = item
    return f'<tg-emoji emoji-id="{emoji_id}">{char}</tg-emoji>'

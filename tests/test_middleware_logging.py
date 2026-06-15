from __future__ import annotations

from aiogram.types import CallbackQuery, Chat, Message
from aiogram.types import User as TgUser

from app.bot.middlewares import _describe_event


def _tg_user() -> TgUser:
    return TgUser(id=1, is_bot=False, first_name="Test")


def _private_chat() -> Chat:
    return Chat(id=1, type="private")


def test_describe_addserver_redacts_secrets():
    msg = Message(
        message_id=1,
        date=0,
        chat=_private_chat(),
        from_user=_tg_user(),
        text="/addserver DE|DE|https://panel:2053|admin|secretpass",
    )
    assert _describe_event(msg) == "command:addserver [redacted]"


def test_describe_command_without_args_shows_name():
    msg = Message(
        message_id=1,
        date=0,
        chat=_private_chat(),
        from_user=_tg_user(),
        text="/admin",
    )
    assert _describe_event(msg) == "command:admin"


def test_describe_text_message_masks_body():
    text = "https://host/sub/abc123 оплатил 175 руб"
    msg = Message(
        message_id=1,
        date=0,
        chat=_private_chat(),
        from_user=_tg_user(),
        text=text,
    )
    assert _describe_event(msg) == f"message:text[len={len(text)}]"


def test_describe_callback_shows_action_only():
    cb = CallbackQuery(
        id="1",
        from_user=_tg_user(),
        chat_instance="x",
        data="pay:confirm:42",
    )
    assert _describe_event(cb) == "callback:pay action=confirm"

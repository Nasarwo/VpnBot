from __future__ import annotations

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import AnswerCallbackQuery

from app.bot import ui


class _Callback:
    def __init__(self, exc: Exception | None = None) -> None:
        self.exc = exc
        self.calls = 0

    async def answer(self, text=None, **kwargs):
        self.calls += 1
        if self.exc is not None:
            raise self.exc


def _bad_request(message: str) -> TelegramBadRequest:
    return TelegramBadRequest(
        method=AnswerCallbackQuery(callback_query_id="cbq"),
        message=message,
    )


async def test_answer_callback_ignores_expired_query_id():
    callback = _Callback(
        _bad_request(
            "Bad Request: query is too old and response timeout expired "
            "or query ID is invalid"
        )
    )

    await ui.answer_callback(callback)

    assert callback.calls == 1


async def test_answer_callback_reraises_other_bad_request():
    callback = _Callback(_bad_request("Bad Request: another error"))

    with pytest.raises(TelegramBadRequest):
        await ui.answer_callback(callback)

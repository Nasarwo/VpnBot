from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.bot.callbacks import PaymentCallback, PlanCallback
from app.bot.texts import (
    BTN_EXTEND,
    BTN_MY_ACCESS,
    BTN_MY_LINKS,
    BTN_SUPPORT,
    BTN_TRIAL,
)
from app.services.plans import PLANS


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_MY_ACCESS), KeyboardButton(text=BTN_EXTEND)],
            [KeyboardButton(text=BTN_TRIAL)],
            [KeyboardButton(text=BTN_MY_LINKS), KeyboardButton(text=BTN_SUPPORT)],
        ],
        resize_keyboard=True,
    )


def plans_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for plan in PLANS:
        if plan.savings_rub > 0:
            label = f"{plan.title} — {plan.amount_rub} ₽ (выгода {plan.savings_rub} ₽)"
        else:
            label = f"{plan.title} — {plan.amount_rub} ₽"
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=PlanCallback(code=plan.code).pack(),
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_payment_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подтвердить",
                    callback_data=PaymentCallback(
                        action="confirm", payment_id=payment_id
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="Отклонить",
                    callback_data=PaymentCallback(
                        action="reject", payment_id=payment_id
                    ).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="История",
                    callback_data=PaymentCallback(
                        action="history", payment_id=payment_id
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="Профиль",
                    callback_data=PaymentCallback(
                        action="profile", payment_id=payment_id
                    ).pack(),
                ),
            ],
        ]
    )


def admin_retry_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Повторить применение",
                    callback_data=PaymentCallback(
                        action="retry", payment_id=payment_id
                    ).pack(),
                )
            ]
        ]
    )

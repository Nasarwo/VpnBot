from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class PaymentCallback(CallbackData, prefix="pay"):
    """Callback админских действий над заявкой."""

    action: str  # confirm | reject | retry | history | profile
    payment_id: int


class PlanCallback(CallbackData, prefix="plan"):
    """Callback выбора тарифа пользователем."""

    code: str

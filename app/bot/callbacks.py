from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class PaymentCallback(CallbackData, prefix="pay"):
    """Callback админских действий над заявкой."""

    action: str  # confirm | reject | retry | history | profile
    payment_id: int


class BindCallback(CallbackData, prefix="bind"):
    """Callback админских действий над заявкой на привязку подписки."""

    action: str  # confirm | reject | retry
    request_id: int


class PlanCallback(CallbackData, prefix="plan"):
    """Callback выбора тарифа пользователем.

    code — код тарифа из PLANS (1m/6m/12m) либо специальное значение "trial"
    для активации пробного периода.
    """

    code: str


class MenuCallback(CallbackData, prefix="menu"):
    """Навигация по inline-меню (редактирование сообщения на месте).

    action: home | subscription | extend | connect | buy | support | install |
            free_proxies | cancel_payment | reset | reset_yes
    """

    action: str


class OnboardCallback(CallbackData, prefix="onb"):
    """Онбординг: был ли пользователь клиентом до внедрения бота."""

    answer: str  # yes | no


class AdminCallback(CallbackData, prefix="adm"):
    """Навигация по админ-панели (/admin).

    action: home | servers | server | toggle | import | clients | del | del_yes |
            add | pending | sharing | broadcast
    server_id используется для действий над конкретным сервером.
    """

    action: str
    server_id: int = 0

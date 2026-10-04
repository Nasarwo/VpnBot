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
            free_proxies | news_channel | cancel_payment | reset | reset_yes
    """

    action: str


class OnboardCallback(CallbackData, prefix="onb"):
    """Онбординг: был ли пользователь клиентом до внедрения бота."""

    answer: str  # yes | no


class AdminCallback(CallbackData, prefix="adm"):
    """Навигация по админ-панели (/admin).

    action: home | servers | server | rename | subscription_url | toggle | import |
            clients | del | del_yes | add | pending | sharing | sharing_all | broadcast
    server_id используется для действий над конкретным сервером.
    """

    action: str
    server_id: int = 0


class WhitelistCallback(CallbackData, prefix="wl"):
    """Пользовательский раздел «Обход белых списков».

    action: home | refresh | buy (value — id пакета)
    """

    action: str
    value: int = 0


class WhitelistAdminCallback(CallbackData, prefix="wla"):
    """Админ-раздел услуги «Обход белых списков».

    action: home | sync | choose (value — inbound) | free_paid | free_trial |
            packages | pkg | pkg_size | pkg_price | pkg_toggle | pkg_add |
            rollout | rollout_all | rollout_strict | block | unblock | usersync
            (value — id пакета или пользователя)
    """

    action: str
    value: int = 0

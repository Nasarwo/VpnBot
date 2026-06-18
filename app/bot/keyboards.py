from __future__ import annotations

from aiogram.types import (
    CopyTextButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from app.bot import texts
from app.bot.callbacks import (
    AdminCallback,
    BindCallback,
    MenuCallback,
    OnboardCallback,
    PaymentCallback,
    PlanCallback,
)
from app.bot.emoji import custom_emoji_id
from app.db.models import Server
from app.services.plans import PLANS

# Подписи кнопок-тарифов (как просил пользователь): короткие формы.
PLAN_BUTTON_NAMES: dict[str, str] = {
    "1m": "Месяц",
    "6m": "Полгода",
    "12m": "Год",
}


def _btn(
    text: str,
    *,
    callback_data: str | None = None,
    copy: str | None = None,
    url: str | None = None,
    style: str | None = None,
    icon: str | None = None,
) -> InlineKeyboardButton:
    """Строит кнопку с цветом (style) и анимированным значком (icon)."""
    kwargs: dict[str, object] = {"text": text}
    if callback_data is not None:
        kwargs["callback_data"] = callback_data
    if copy is not None:
        kwargs["copy_text"] = CopyTextButton(text=copy)
    if url is not None:
        kwargs["url"] = url
    kwargs["style"] = style or "primary"
    if icon is not None:
        emoji_id = custom_emoji_id(icon)
        if emoji_id:
            kwargs["icon_custom_emoji_id"] = emoji_id
    return InlineKeyboardButton(**kwargs)


def _plan_label(plan) -> str:
    name = PLAN_BUTTON_NAMES.get(plan.code, plan.title)
    return f"{name} — {plan.amount_rub} ₽"


def _back_button(action: str) -> InlineKeyboardButton:
    return _btn(texts.BTN_BACK, callback_data=MenuCallback(action=action).pack(),
                icon="back")


def back_keyboard(action: str) -> InlineKeyboardMarkup:
    """Клавиатура с единственной кнопкой «Назад» на указанный экран."""
    return InlineKeyboardMarkup(inline_keyboard=[[_back_button(action)]])


def cancel_payment_keyboard() -> InlineKeyboardMarkup:
    """Кнопка «Отмена» под заявкой на оплату — удаляет заявку."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn(
                    texts.BTN_CANCEL,
                    callback_data=MenuCallback(action="cancel_payment").pack(),
                    style="danger",
                    icon="cancel",
                )
            ]
        ]
    )


def welcome_menu(has_active: bool) -> InlineKeyboardMarkup:
    """Главное меню под приветствием. Зависит от наличия активной подписки."""
    if has_active:
        primary = _btn(
            texts.BTN_MY_SUBSCRIPTION,
            callback_data=MenuCallback(action="subscription").pack(),
            style="primary",
            icon="subscription",
        )
    else:
        primary = _btn(
            texts.BTN_BUY,
            callback_data=MenuCallback(action="buy").pack(),
            style="primary",
            icon="buy",
        )
    support = _btn(
        texts.BTN_SUPPORT,
        callback_data=MenuCallback(action="support").pack(),
        style="success",
        icon="support",
    )
    install = _btn(
        texts.BTN_INSTALL,
        callback_data=MenuCallback(action="install").pack(),
        icon="install",
    )
    free_proxies = _btn(
        texts.BTN_FREE_PROXIES,
        callback_data=MenuCallback(action="free_proxies").pack(),
        icon="globe",
    )
    reset = _btn(
        texts.BTN_RESET,
        callback_data=MenuCallback(action="reset").pack(),
        style="danger",
        icon="cancel",
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[[primary], [install], [free_proxies], [support], [reset]]
    )


def reset_bot_confirm_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение сброса данных пользователя в боте."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn(
                    texts.BTN_RESET_YES,
                    callback_data=MenuCallback(action="reset_yes").pack(),
                    style="danger",
                    icon="cancel",
                )
            ],
            [
                _btn(
                    texts.BTN_CANCEL,
                    callback_data=MenuCallback(action="home").pack(),
                    icon="back",
                )
            ],
        ]
    )


def install_guides_keyboard() -> InlineKeyboardMarkup:
    """Гайды по установке клиента — ссылки на Telegraph."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn(
                    texts.BTN_GUIDE_WINDOWS,
                    url=texts.INSTALL_GUIDE_WINDOWS_URL,
                    style="primary",
                    icon="laptop",
                )
            ],
            [
                _btn(
                    texts.BTN_GUIDE_ANDROID_IOS,
                    url=texts.INSTALL_GUIDE_ANDROID_IOS_URL,
                    style="primary",
                    icon="phone",
                )
            ],
            [_back_button("home")],
        ]
    )


def free_proxies_keyboard() -> InlineKeyboardMarkup:
    """Бесплатные прокси Telegram — ссылки t.me/proxy и t.me/socks."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn(
                    texts.BTN_PROXY_MTPROTO,
                    url=texts.FREE_PROXY_MTPROTO_URL,
                    style="primary",
                    icon="connect",
                ),
                _btn(
                    texts.BTN_PROXY_SOCKS5,
                    url=texts.FREE_PROXY_SOCKS5_URL,
                    style="primary",
                    icon="server",
                ),
            ],
            [_back_button("home")],
        ]
    )


def news_channel_keyboard() -> InlineKeyboardMarkup:
    """Кнопка подписки на канал с новостями."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn(
                    texts.BTN_NEWS_CHANNEL,
                    url=texts.NEWS_CHANNEL_URL,
                    style="primary",
                )
            ]
        ]
    )


def subscription_menu() -> InlineKeyboardMarkup:
    """Меню активной подписки: продлить / подключение / назад."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn(
                    texts.BTN_EXTEND,
                    callback_data=MenuCallback(action="extend").pack(),
                    style="primary",
                    icon="extend",
                )
            ],
            [
                _btn(
                    texts.BTN_CONNECT,
                    callback_data=MenuCallback(action="connect").pack(),
                    style="success",
                    icon="connect",
                )
            ],
            [_back_button("home")],
        ]
    )


def extend_plans_keyboard() -> InlineKeyboardMarkup:
    """Тарифы продления (без пробного). Назад — в меню подписки."""
    rows = [
        [
            _btn(
                _plan_label(plan),
                callback_data=PlanCallback(code=plan.code).pack(),
                style="primary",
                icon="paid",
            )
        ]
        for plan in PLANS
    ]
    rows.append([_back_button("subscription")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def purchase_plans_keyboard(show_trial: bool) -> InlineKeyboardMarkup:
    """Тарифы оформления. Пробный — только если доступен. Назад — на главную."""
    rows: list[list[InlineKeyboardButton]] = []
    if show_trial:
        rows.append(
            [
                _btn(
                    texts.BTN_TRIAL,
                    callback_data=PlanCallback(code="trial").pack(),
                    style="success",
                    icon="trial",
                )
            ]
        )
    for plan in PLANS:
        rows.append(
            [
                _btn(
                    _plan_label(plan),
                    callback_data=PlanCallback(code=plan.code).pack(),
                    style="primary",
                    icon="paid",
                )
            ]
        )
    rows.append([_back_button("home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def connection_keyboard(
    servers: list[Server], public_id: str | None
) -> InlineKeyboardMarkup:
    """Кнопки серверов: тап копирует ссылку-подписку. Назад — в меню подписки."""
    rows: list[list[InlineKeyboardButton]] = []
    if public_id:
        for server in servers:
            if not server.subscription_base:
                continue
            base = server.subscription_base
            link = (base if base.endswith("/") else base + "/") + public_id
            label = texts.server_button_label(server)
            rows.append([_btn(label, copy=link, style="primary")])
    rows.append([_back_button("subscription")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _adm(action: str, server_id: int = 0) -> str:
    return AdminCallback(action=action, server_id=server_id).pack()


def admin_home_keyboard() -> InlineKeyboardMarkup:
    """Главное меню /admin."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn("Серверы", callback_data=_adm("servers"), style="primary",
                  icon="server")],
            [_btn("Заявки в ожидании", callback_data=_adm("pending"),
                  style="success", icon="subscription")],
            [_btn("Удалить инбаунды", callback_data=_adm("delete_subscription"),
                  style="danger", icon="cancel")],
            [_btn("Рассылка всем", callback_data=_adm("broadcast"),
                  style="success", icon="support")],
            [_btn("Антишеринг", callback_data=_adm("sharing"), style="success")],
        ]
    )


def admin_servers_keyboard(servers: list[Server]) -> InlineKeyboardMarkup:
    """Список серверов: кнопка на каждый + добавить + назад."""
    rows: list[list[InlineKeyboardButton]] = []
    for srv in servers:
        if srv.is_online is True:
            mark = "\U0001f7e2"  # 🟢
        elif srv.is_online is False:
            mark = "\U0001f534"  # 🔴
        else:
            mark = "\u26aa"  # ⚪
        state = "вкл" if srv.enabled else "выкл"
        label = f"{mark} #{srv.id} {srv.name} [{state}]"
        rows.append([_btn(label, callback_data=_adm("server", srv.id))])
    rows.append(
        [_btn("Добавить сервер", callback_data=_adm("add"), style="success",
              icon="add")]
    )
    rows.append([_btn(texts.BTN_BACK, callback_data=_adm("home"), icon="back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_server_keyboard(server: Server) -> InlineKeyboardMarkup:
    """Управление конкретным сервером."""
    toggle = "Выключить" if server.enabled else "Включить"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(toggle, callback_data=_adm("toggle", server.id),
                  style="primary")],
            [_btn("Импорт inbound'ов", callback_data=_adm("import", server.id),
                  style="success")],
            [_btn("Клиенты панели", callback_data=_adm("clients", server.id))],
            [_btn("Удалить сервер", callback_data=_adm("del", server.id),
                  style="danger", icon="cancel")],
            [_btn("К списку серверов", callback_data=_adm("servers"),
                  icon="back")],
        ]
    )


def admin_confirm_delete_keyboard(server_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn("Да, удалить", callback_data=_adm("del_yes", server_id),
                  style="danger", icon="cancel")],
            [_btn(texts.BTN_CANCEL, callback_data=_adm("server", server_id),
                  icon="back")],
        ]
    )


def admin_back_keyboard(action: str, server_id: int = 0) -> InlineKeyboardMarkup:
    """Единственная кнопка «Назад» на нужный экран админки."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(texts.BTN_BACK, callback_data=_adm(action, server_id),
                  icon="back")]
        ]
    )


def onboarding_legacy_keyboard() -> InlineKeyboardMarkup:
    """Вопрос: был ли пользователь клиентом до бота."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn(
                    texts.BTN_ONBOARD_YES,
                    callback_data=OnboardCallback(answer="yes").pack(),
                    style="primary",
                )
            ],
            [
                _btn(
                    texts.BTN_ONBOARD_NO,
                    callback_data=OnboardCallback(answer="no").pack(),
                    style="success",
                )
            ],
        ]
    )


def admin_bind_keyboard(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn(
                    text="Привязать",
                    callback_data=BindCallback(
                        action="confirm", request_id=request_id
                    ).pack(),
                    style="success",
                ),
                _btn(
                    text="Отклонить",
                    callback_data=BindCallback(
                        action="reject", request_id=request_id
                    ).pack(),
                    style="danger",
                ),
            ],
        ]
    )


def admin_bind_retry_keyboard(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn(
                    text="Повторить привязку",
                    callback_data=BindCallback(
                        action="retry", request_id=request_id
                    ).pack(),
                    style="success",
                )
            ]
        ]
    )


def admin_payment_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn(
                    text="Подтвердить",
                    callback_data=PaymentCallback(
                        action="confirm", payment_id=payment_id
                    ).pack(),
                    style="success",
                ),
                _btn(
                    text="Отклонить",
                    callback_data=PaymentCallback(
                        action="reject", payment_id=payment_id
                    ).pack(),
                    style="danger",
                ),
            ],
            [
                _btn(
                    text="История",
                    callback_data=PaymentCallback(
                        action="history", payment_id=payment_id
                    ).pack(),
                ),
                _btn(
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
                _btn(
                    text="Повторить применение",
                    callback_data=PaymentCallback(
                        action="retry", payment_id=payment_id
                    ).pack(),
                    style="success",
                )
            ]
        ]
    )

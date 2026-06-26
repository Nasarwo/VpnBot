from __future__ import annotations

from datetime import UTC, datetime
from html import escape

from app.bot import emoji
from app.db.enums import PaymentStatus
from app.db.models import PaymentRequest, Server, User, VpnClient

# Кнопки пользовательского меню (inline)
BTN_MY_SUBSCRIPTION = "Моя подписка"
BTN_BUY = "Оформить подписку"
BTN_ADMIN_PANEL = "\u0410\u0434\u043c\u0438\u043d-\u043f\u0430\u043d\u0435\u043b\u044c"
BTN_INSTALL = "Как установить"
BTN_FREE_PROXIES = "Бесплатные прокси"
BTN_SUPPORT = "Поддержка"
BTN_RESET = "Сбросить бота"
BTN_RESET_YES = "Да, сбросить"
BTN_EXTEND = "Продлить"
BTN_CONNECT = "Подключение"
BTN_TRIAL = "3 дня — Пробный доступ"
BTN_BACK = "Назад"
BTN_CANCEL = "Отмена"
BTN_ONBOARD_YES = "Да, была подписка"
BTN_ONBOARD_NO = "Нет, я новый пользователь"
BTN_GUIDE_WINDOWS = "Windows"
BTN_GUIDE_ANDROID_IOS = "Android & IOS"
BTN_PROXY_MTPROTO = "MTProto 1"
BTN_PROXY_MTPROTO_2 = "MTProto 2"

INSTALL_GUIDE_WINDOWS_URL = (
    "https://telegra.ph/Gajd-po-podklyucheniyu-Windows--07062026-06-07"
)
INSTALL_GUIDE_ANDROID_IOS_URL = (
    "https://telegra.ph/Gajd-po-podklyucheniyu-Android--IOS--07062026-06-07"
)

NEWS_CHANNEL_URL = "https://t.me/+FJMJEtjqREU3ODQy"
BTN_NEWS_CHANNEL = "Подписаться на канал"

FREE_PROXY_MTPROTO_URL = (
    "https://t.me/proxy?server=mt.artobject.pro&port=443"
    "&secret=6336c46e4f0029eba43cc4c511fa325f"
)
FREE_PROXY_MTPROTO_2_URL = (
    "https://t.me/proxy?server=us.denezhkin.com&port=443"
    "&secret=915936e5f690a65f9da50a8116d0ccc2"
)

# Дословный текст акции «приведи друга» (используется при продлении и оформлении).
REFERRAL_PROMO = (
    "Также действуют акция приведи друга и получи месяц бесплатно, то есть "
    "если вы приведете одного человека и он оформит подписку, то получаете "
    "месяц бесплатно. Повторять можно сколько угодно. За получением обращаться "
    "в поддержку."
)

STATUS_LABELS: dict[PaymentStatus, str] = {
    PaymentStatus.CREATED: "создана",
    PaymentStatus.WAITING_ADMIN: "ожидает проверки",
    PaymentStatus.CONFIRMED: "подтверждена",
    PaymentStatus.REJECTED: "отклонена",
    PaymentStatus.APPLIED: "доступ продлён",
    PaymentStatus.FAILED: "ошибка применения",
}


def _fmt_date(value: datetime | None) -> str:
    if value is None:
        return "—"
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.strftime("%d.%m.%Y %H:%M UTC")


def welcome(user: User) -> str:
    """Приветствие. Использует HTML-разметку: ID завёрнут в <code> —
    Telegram копирует его в буфер по нажатию. Отправлять с parse_mode='HTML'."""
    name = escape(user.first_name or "пользователь")
    public_id = escape(user.public_id or "—")
    return (
        f"Здравствуйте, {name}.\n\n"
        "Это бот управления вашей подпиской на личный доступ.\n"
        f"Ваш ID: <code>{public_id}</code>\n"
        "Сообщите этот ID при обращении в поддержку.\n\n"
        "Выберите действие в меню."
    )


def install_guides_intro() -> str:
    return (
        "Доступные гайды по настройке клиент-приложений под разные системы."
    )


def free_proxies_intro() -> str:
    return (
        "Бесплатные прокси для Telegram, существующие благодаря пользователям "
        "этого сервиса. Можно свободно распространять."
    )


def reset_bot_prompt() -> str:
    return (
        "Сбросить бота? Все ваши данные в боте будут удалены,\n"
        "но купленная подписка продолжит работать.\n"
        "После сброса общение с ботом начнётся заново\n"
        "и вам нужно будет по новой привязать подписку."
    )


def onboarding_legacy_question() -> str:
    return (
        "Вы пользовались услугами сервиса до внедрения бота?\n\n"
        "Если у вас уже была подписка — выберите «Да», и мы привяжем "
        "существующий доступ к этому аккаунту Telegram."
    )


def onboarding_send_link_prompt(example_link: str) -> str:
    example = escape(example_link)
    return (
        "Отправьте свою ссылку на подписку (одну любую). "
        "Администратор проверит подлинность владельца и привяжет ваш аккаунт.\n\n"
        f"Пример: <code>{example}</code>"
    )


def onboarding_invalid_link(example_link: str) -> str:
    example = escape(example_link)
    return (
        "Не удалось найти ID подписки в вашем сообщении.\n\n"
        "Пришлите полную ссылку-подписку или только ID из конца ссылки "
        "(как в примере ниже).\n\n"
        f"Пример: <code>{example}</code>"
    )


def bind_request_received(request_code: str) -> str:
    return (
        f"Заявка <code>{escape(request_code)}</code> отправлена администратору.\n\n"
        "После проверки ссылки вы получите доступ с вашим прежним ID подписки. "
        "Обычно это занимает немного времени."
    )


def bind_request_waiting(request_code: str) -> str:
    return (
        f"Заявка <code>{escape(request_code)}</code> на привязку ожидает проверки "
        "администратором.\n\n"
        "Как только доступ будет подтверждён, вы получите уведомление."
    )


def bind_request_rejected(request_code: str) -> str:
    return (
        f"Заявка <code>{escape(request_code)}</code> отклонена.\n\n"
        "Вы можете попробовать снова: отправьте другую ссылку или выберите, "
        "были ли вы клиентом сервиса раньше.\n\n"
        "Если уверены, что ссылка верная — напишите в поддержку."
    )


def bind_request_approved(public_id: str) -> str:
    pid = escape(public_id)
    return (
        f"{emoji.tg('ok')} Аккаунт привязан.\n\n"
        f"Ваш ID подписки: <code>{pid}</code>\n"
        "Доступ восстановлен — откройте «Моя подписка» в меню."
    )


def subscription_deleted_by_admin() -> str:
    return "Ваша подписка была удалена администратором."


def admin_bind_card(req, user: User) -> str:
    username = f"@{escape(user.username)}" if user.username else "—"
    pid = f"<code>{escape(req.public_id)}</code>"
    link = escape(req.subscription_link)
    return (
        f"Привязка подписки <code>{escape(req.request_code)}</code>\n\n"
        f"Пользователь: {username}\n"
        f"Telegram ID: {user.telegram_id}\n"
        f"Имя: {escape(user.first_name or '—')}\n"
        f"ID из ссылки: {pid}\n"
        f"Ссылка:\n<code>{link}</code>"
    )


def admin_bind_pending(requests: list) -> str:
    if not requests:
        return "Заявок на привязку в ожидании нет."
    lines = ["Заявки на привязку подписки:\n"]
    for req in requests:
        user = req.user
        username = f"@{escape(user.username)}" if user and user.username else "—"
        lines.append(
            f"<code>{escape(req.request_code)}</code> — {username} — "
            f"ID <code>{escape(req.public_id)}</code>"
        )
    lines.append("\nПодтвердить: кнопка в карточке или /confirmbind КОД")
    return "\n".join(lines)


def country_flag(country: str | None) -> str:
    """Эмодзи-флаг по ISO2-коду страны (напр. 'SE' -> 🇸🇪). Иначе пусто."""
    if not country:
        return ""
    code = country.strip().upper()
    if len(code) != 2 or not code.isalpha():
        return ""
    return "".join(chr(0x1F1E6 + (ord(ch) - ord("A"))) for ch in code)


def server_button_label(server: Server) -> str:
    # Флаг не добавляем автоматически: его указывают прямо в названии сервера,
    # иначе он дублируется.
    return server.name


def _days_left(expires: datetime | None) -> int | None:
    if expires is None:
        return None
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    delta = expires - datetime.now(tz=UTC)
    if delta.total_seconds() <= 0:
        return 0
    return delta.days


def subscription_overview(client: VpnClient | None, public_id: str | None) -> str:
    """Экран «Моя подписка»: дни и ID. Отправлять с parse_mode='HTML'."""
    pid = escape(public_id or "—")
    days = _days_left(client.expires_at if client else None)
    header = f"{emoji.tg('subscription')} <b>Ваша подписка активна</b>"
    lines = [
        header,
        "",
        f"ID подписки: <code>{pid}</code>",
        f"Осталось дней: {days if days is not None else '—'}",
    ]
    if client and client.expires_at is not None:
        lines.append(f"Действует до: {_fmt_date(client.expires_at)}")
    lines.append("")
    lines.append("Выберите действие:")
    return "\n".join(lines)


def extend_info(last_plan_title: str | None) -> str:
    """Экран «Продлить»: прошлый тариф + промо. parse_mode='HTML'."""
    lines = [f"{emoji.tg('extend')} <b>Продление подписки</b>", ""]
    if last_plan_title:
        lines.append(f"Ваш прошлый тариф: <b>{escape(last_plan_title)}</b>.")
        lines.append("")
    lines.append(f"<i>{escape(REFERRAL_PROMO)}</i>")
    lines.append("")
    lines.append("Выберите тариф для продления:")
    return "\n".join(lines)


def purchase_info(show_trial: bool) -> str:
    """Экран «Оформить подписку»: цены и правила. parse_mode='HTML'."""
    lines = [
        f"{emoji.tg('buy')} <b>Оформление подписки</b>",
        "",
        "При покупке вы получаете доступ к высокоскоростным серверам на все "
        "ваши устройства, трафик не ограничен.",
        "",
        "Тарифы:",
        "Месячный - 175 рублей",
        "Полугодовой - 850 рублей (на 200 рублей дороже если платить ежемесячно)",
        "Годовой - 1600 рублей (на 500 рублей дороже если платить ежемесячно)",
    ]
    if show_trial:
        lines.append("")
        lines.append("Доступен бесплатный пробный доступ на 3 дня.")
    lines.append("")
    lines.append(f"<i>{escape(REFERRAL_PROMO)}</i>")
    lines.append("")
    lines.append("Выберите тариф:")
    return "\n".join(lines)


def connection_overview(servers: list[Server]) -> str:
    """Экран «Подключение»: доступность серверов. parse_mode='HTML'."""
    lines = [f"{emoji.tg('connect')} <b>Подключение</b>", "", "Доступность серверов:"]
    visible = [s for s in servers if s.subscription_base]
    if not visible:
        lines.append("")
        lines.append("Серверы пока не настроены. Обратитесь в поддержку.")
        return "\n".join(lines)
    for server in visible:
        if server.is_online is True:
            status = emoji.tg("ok")
        elif server.is_online is False:
            status = emoji.tg("down")
        else:
            status = emoji.tg("unknown")
        lines.append(f"{escape(server_button_label(server))} — {status}")
    lines.append("")
    lines.append("Нажмите на сервер ниже, чтобы скопировать ссылку-подписку.")
    return "\n".join(lines)


def period_label(period_days: int) -> str:
    from app.services.plans import PLANS

    for plan in PLANS:
        if plan.period_days == period_days:
            return f"{period_days} дней ({plan.title})"
    return f"{period_days} дней"


def payment_created(
    payment: PaymentRequest, details_text: str
) -> str:
    amount = int(payment.amount) if payment.amount == int(payment.amount) else payment.amount
    return (
        f"Заявка <code>{escape(payment.payment_code)}</code> создана.\n\n"
        f"Сумма: {amount} ₽\n"
        f"Срок: {period_label(payment.period_days)}\n\n"
        "Переведите оплату по реквизитам:\n"
        f"{details_text}\n\n"
        "После оплаты отправьте сюда чек, скриншот или сообщение об оплате."
    )


def proof_received(payment_code: str) -> str:
    return (
        f"Подтверждение по заявке <code>{escape(payment_code)}</code> получено.\n"
        "Администратор проверит оплату и продлит доступ. Мы пришлём уведомление."
    )


def no_open_request() -> str:
    return (
        "Активной заявки нет.\n"
        "Откройте меню и выберите тариф, чтобы создать заявку."
    )


def trial_granted(client: VpnClient, period_days: int) -> str:
    return (
        f"{emoji.tg('ok')} Пробный доступ на {period_days} дня активирован.\n"
        f"Срок действия до: {_fmt_date(client.expires_at)}\n\n"
        "Ссылки для подключения — в разделе «Моя подписка» → «Подключение»."
    )


def trial_already_used() -> str:
    return (
        "Пробный период уже был использован на этом аккаунте.\n"
        "Оформить полный доступ можно в меню."
    )


def trial_no_client() -> str:
    return (
        "Пробный доступ пока недоступен: серверы ещё не настроены.\n"
        "Попробуйте чуть позже."
    )


def trial_failed() -> str:
    return (
        "Не удалось активировать пробный доступ из-за временной ошибки.\n"
        "Попробуйте ещё раз позже."
    )


def support_message(contact: str, public_id: str | None = None) -> str:
    id_line = f"Ваш ID: <code>{public_id}</code>\n" if public_id else ""
    return (
        f"{id_line}"
        f"По вопросам подключения и оплаты обращайтесь: {contact}\n"
        "Укажите свой ID — так время ожидания ответа кратно уменьшится ;)."
    )


def access_extended(client: VpnClient) -> str:
    return (
        f"{emoji.tg('ok')} Доступ продлён.\n"
        f"Новый срок действия: {_fmt_date(client.expires_at)}\n\n"
        "Актуальные ссылки — в разделе «Моя подписка» → «Подключение»."
    )


def first_purchase_channel_prompt() -> str:
    return (
        "Подпишитесь на наш канал с новостями о сервисе — "
        "там публикуем важные объявления и обновления."
    )


def expiry_notice(stage: int, expires_at: datetime | None) -> str:
    """Уведомление об окончании подписки. parse_mode='HTML'.

    stage: 1 — за день, 2 — за час, 3 — подписка истекла.
    """
    until = _fmt_date(expires_at)
    if stage == 1:
        return (
            f"{emoji.tg('extend')} <b>Подписка истекает через 1 день</b>\n"
            f"Действует до: {until}\n\n"
            "Продлите доступ заранее, чтобы не потерять подключение: "
            "«Моя подписка» → «Продлить»."
        )
    if stage == 2:
        return (
            f"{emoji.tg('extend')} <b>Подписка истекает через час</b>\n"
            f"Действует до: {until}\n\n"
            "Продлите доступ, чтобы не прерывать подключение: "
            "«Моя подписка» → «Продлить»."
        )
    return (
        f"{emoji.tg('cancel')} <b>Подписка закончилась</b>\n"
        f"Срок действия истёк: {until}\n\n"
        "Доступ приостановлен. Оформите продление, чтобы снова подключиться: "
        "«Оформить подписку»."
    )


def payment_rejected(payment_code: str) -> str:
    return (
        f"Заявка <code>{escape(payment_code)}</code> отклонена.\n"
        "Если это ошибка, свяжитесь с поддержкой."
    )


# --- Админские тексты ---


def admin_payment_card(payment: PaymentRequest, user: User) -> str:
    username = f"@{escape(user.username)}" if user.username else "—"
    amount = int(payment.amount) if payment.amount == int(payment.amount) else payment.amount
    status = escape(STATUS_LABELS.get(payment.status, payment.status.value))
    pid = f"<code>{escape(user.public_id)}</code>" if user.public_id else "—"
    text = (
        f"Новая заявка <code>{escape(payment.payment_code)}</code>\n\n"
        f"Пользователь: {username}\n"
        f"ID: {pid}\n"
        f"Telegram ID: {user.telegram_id}\n"
        f"Сумма: {amount} ₽\n"
        f"Срок: +{payment.period_days} дней\n"
        f"Статус: {status}"
    )
    if payment.last_error:
        text += f"\n\nОшибка: {escape(payment.last_error)}"
    return text


def admin_profile(user: User, client: VpnClient | None) -> str:
    username = f"@{user.username}" if user.username else "—"
    lines = [
        "Профиль пользователя",
        f"ID: {user.public_id or '—'}",
        f"Telegram ID: {user.telegram_id}",
        f"Username: {username}",
        f"Имя: {user.first_name or '—'}",
        f"Роль: {user.role.value}",
    ]
    if client is not None:
        lines.append(f"Срок доступа: {_fmt_date(client.expires_at)}")
        lines.append(f"Активен: {'да' if client.is_active else 'нет'}")
    else:
        lines.append("VPN-клиент: не привязан")
    return "\n".join(lines)


def admin_history(payments: list[PaymentRequest]) -> str:
    if not payments:
        return "История оплат пуста."
    lines = ["История оплат:\n"]
    for p in payments:
        status = escape(STATUS_LABELS.get(p.status, p.status.value))
        lines.append(
            f"<code>{escape(p.payment_code)}</code> — {int(p.amount)} ₽ — "
            f"{status} — {_fmt_date(p.created_at)}"
        )
    return "\n".join(lines)


def admin_pending(payments: list[PaymentRequest]) -> str:
    if not payments:
        return "Заявок в ожидании проверки нет."
    lines = ["Заявки в ожидании проверки:\n"]
    for p in payments:
        user = p.user
        username = f"@{escape(user.username)}" if user and user.username else "—"
        amount = int(p.amount) if p.amount == int(p.amount) else p.amount
        lines.append(
            f"<code>{escape(p.payment_code)}</code> — {username} — "
            f"{amount} ₽ — +{p.period_days} дн."
        )
    lines.append("\nПодтвердить: /confirm КОД\nОтклонить: /reject КОД")
    return "\n".join(lines)


_LEVEL_LABELS = {
    "ok": "норма",
    "warn": "внимание",
    "critical": "критично",
}


def sharing_level_label(level: str) -> str:
    return _LEVEL_LABELS.get(level, level)


def sharing_summary(items: list) -> str:
    """items: список кортежей (VpnClient, SharingStatus)."""
    if not items:
        return "Подозрительной активности по IP не обнаружено."
    lines = ["Антишеринг: клиенты с повышенной активностью по IP (за 24 ч):\n"]
    for client, status in items:
        user = client.user
        username = f"@{user.username}" if user and user.username else "—"
        pid = (user.public_id if user else None) or "—"
        lines.append(
            f"{sharing_level_label(status.level).upper()} — {username} (ID {pid}) — "
            f"уник. IP 24ч: {status.unique_24h} "
            f"(1ч: {status.counts.get('1h', 0)}, 15м: {status.counts.get('15m', 0)})"
        )
    lines.append("\nПодробно: /sharing <telegram_id>")
    return "\n".join(lines)


def sharing_detail(
    user: User | None,
    status,
    ips: list[str],
    settings_summary: str,
) -> str:
    username = f"@{user.username}" if user and user.username else "—"
    pid = (user.public_id if user else None) or "—"
    c = status.counts
    lines = [
        f"Антишеринг — отчёт по пользователю {username} (ID {pid})",
        f"Статус: {sharing_level_label(status.level)}",
        "",
        "Уникальные IP за окна:",
        f"  15 мин: {c.get('15m', 0)}",
        f"  1 час:  {c.get('1h', 0)}",
        f"  24 часа: {c.get('24h', 0)}",
        f"  7 дней: {c.get('7d', 0)}",
        "",
        settings_summary,
    ]
    if ips:
        shown = ", ".join(ips[:15])
        more = "" if len(ips) <= 15 else f" и ещё {len(ips) - 15}"
        lines.append(f"\nIP за 24 ч: {shown}{more}")
    return "\n".join(lines)


def admin_servers(servers: list) -> str:
    if not servers:
        return (
            "Серверы не настроены.\n"
            "Добавьте: /addserver name|country|panel_url|username|password|"
            "[kind]|[subscription_base], затем /addinbound."
        )
    lines = ["Серверы:"]
    for srv in servers:
        status = "вкл" if srv.enabled else "выкл"
        sub = "есть" if srv.subscription_base else "нет"
        lines.append(
            f"#{srv.id} {srv.name} [{srv.kind}] {srv.country or '—'} — {status}, "
            f"подписка: {sub}"
        )
        inbounds = list(getattr(srv, "inbounds", []))
        if not inbounds:
            lines.append("   inbound'ы: нет (добавьте /addinbound)")
        for inb in inbounds:
            flow = f", flow={inb.flow}" if inb.flow else ""
            on = "" if inb.enabled else " (выкл)"
            lines.append(
                f"   inbound {inb.inbound_id}: {inb.protocol.value}{flow}{on}"
            )
    lines.append(
        "\nУдалить лишний inbound: /delinbound <server_id> <inbound_id>"
    )
    lines.append("Удалить все inbound'ы сервера: /clearinbounds <server_id>")
    return "\n".join(lines)


def _server_status_mark(server) -> str:
    if server.is_online is True:
        return "🟢"
    if server.is_online is False:
        return "🔴"
    return "⚪"


def admin_panel_home(servers: list) -> str:
    total = len(servers)
    online = sum(1 for s in servers if s.is_online is True)
    enabled = sum(1 for s in servers if s.enabled)
    lines = [
        "Панель администратора",
        "",
        f"Серверов: {total} (включено: {enabled}, онлайн: {online})",
        "Выберите раздел.",
    ]
    return "\n".join(lines)


def admin_servers_title(servers: list) -> str:
    if not servers:
        return (
            "Серверы не настроены.\n\n"
            "Нажмите «Добавить сервер», чтобы подключить первую панель 3x-ui."
        )
    return (
        "Серверы. Нажмите на сервер, чтобы открыть управление.\n"
        "🟢 онлайн · 🔴 офлайн · ⚪ не проверялся"
    )


def admin_server_detail(server) -> str:
    inbounds = list(getattr(server, "inbounds", []))
    enabled_inbounds = sum(1 for i in inbounds if i.enabled)
    last = (
        server.last_checked_at.strftime("%d.%m %H:%M UTC")
        if server.last_checked_at
        else "—"
    )
    if server.is_online is True:
        online = "онлайн 🟢"
    elif server.is_online is False:
        online = "офлайн 🔴"
    else:
        online = "не проверялся ⚪"
    lines = [
        f"{_server_status_mark(server)} Сервер #{server.id} — {server.name}".strip(),
        "",
        f"Состояние: {'включён' if server.enabled else 'выключен'}",
        f"Доступность: {online} (проверка: {last})",
        f"Тип: {server.kind}",
        f"Страна: {server.country or '—'}",
        f"Панель: {server.panel_url}",
        f"Подписка: {server.subscription_base or '—'}",
        f"Inbound'ы: {len(inbounds)} (активных: {enabled_inbounds})",
    ]
    for inb in inbounds:
        flow = f", flow={inb.flow}" if inb.flow else ""
        on = "" if inb.enabled else " (выкл)"
        lines.append(f"   • inbound {inb.inbound_id}: {inb.protocol.value}{flow}{on}")
    return "\n".join(lines)


def admin_add_server_prompt() -> str:
    return (
        "Добавление сервера.\n\n"
        "Пришлите одной строкой поля через «|»:\n"
        "name|country|panel_url|username|password|[kind]|[subscription_base]\n\n"
        "Пример:\n"
        "Германия|DE|https://de.example.com:2053/panel|admin|pass|direct|"
        "https://de.example.com:2096/sub/\n\n"
        "country — ISO2-код страны (DE, SE, FI…), для флажка и подписи.\n"
        "kind и subscription_base необязательны.\n\n"
        "Отправьте /cancel, чтобы отменить."
    )


def admin_server_added(server) -> str:
    return (
        f"Сервер добавлен: #{server.id} {server.name}.\n"
        "Теперь импортируйте inbound'ы кнопкой «Импорт inbound'ов» в карточке сервера."
    )


def admin_confirm_delete(server) -> str:
    return (
        f"Удалить сервер #{server.id} {server.name}?\n\n"
        "Будут удалены его inbound'ы и привязки клиентов в боте. "
        "На самой панели 3x-ui клиенты останутся. Действие необратимо."
    )


def admin_server_deleted(server_id: int, name: str) -> str:
    return f"Сервер #{server_id} {name} удалён из бота."


def admin_add_cancelled() -> str:
    return "Добавление сервера отменено."


def admin_broadcast_prompt(user_count: int) -> str:
    return (
        "Рассылка сообщения всем пользователям.\n\n"
        f"Получателей: {user_count}.\n"
        "Пришлите текст сообщения — он будет отправлен всем, кто запускал бота.\n\n"
        "Отправьте /cancel, чтобы отменить."
    )


def admin_broadcast_cancelled() -> str:
    return "Рассылка отменена."


def admin_broadcast_result(total: int, sent: int, failed: int) -> str:
    return (
        "Рассылка завершена.\n"
        f"Получателей: {total}\n"
        f"Доставлено: {sent}\n"
        f"Не доставлено: {failed}"
    )


def _fmt_expiry_ms(expiry_ms: object) -> str:
    try:
        ms = int(expiry_ms or 0)
    except (TypeError, ValueError):
        return "?"
    if ms <= 0:
        return "без срока"
    from datetime import UTC, datetime

    return datetime.fromtimestamp(ms / 1000, tz=UTC).strftime("%Y-%m-%d")


def admin_panel_clients(server_id: int, clients: list, limit: int = 50) -> str:
    if not clients:
        return f"На сервере #{server_id} нет клиентов или нет доступа."
    total = len(clients)
    lines = [f"Клиенты панели сервера #{server_id} (всего {total}):"]
    for c in clients[:limit]:
        body = c.get("client") if isinstance(c.get("client"), dict) else c
        email = body.get("email") or "—"
        sub = body.get("subId") or "—"
        state = "вкл" if body.get("enable", True) else "выкл"
        exp = _fmt_expiry_ms(body.get("expiryTime"))
        lines.append(f"  {email} | subId={sub} | {state} | до {exp}")
    if total > limit:
        lines.append(f"  …и ещё {total - limit}")
    lines.append(
        "\nПривязать к боту: /bind <server_id> <email> <telegram_id>"
    )
    return "\n".join(lines)


def admin_bind_result(result) -> str:
    lines = [
        "Клиент привязан к боту.",
        f"Email в панели: {result.email}",
        f"ID в боте (public_id): {result.public_id}",
    ]
    if result.expires_at is not None:
        lines.append(f"Срок действия: до {result.expires_at:%Y-%m-%d %H:%M} UTC")
    else:
        lines.append("Срок действия: без срока (продлите командой /extend)")
    if result.synced:
        ok = sum(1 for r in result.results if r.ok)
        failed = [(r.server_id, r.error) for r in result.results if not r.ok]
        lines.append(f"Синхронизировано серверов: {ok}")
        for sid, err in failed:
            lines.append(f"  ошибка server {sid}: {err}")
    else:
        lines.append(
            "Синхронизация по серверам пропущена (бессрочный клиент). "
            "После /extend доступ применится ко всем серверам."
        )
    return "\n".join(lines)


def admin_panel_inbounds(server_id: int, inbounds: list) -> str:
    if not inbounds:
        return f"На сервере #{server_id} нет inbound'ов или нет доступа."
    lines = [f"Inbound'ы панели сервера #{server_id} (id — порт — протокол):"]
    for inb in inbounds:
        iid = inb.get("id")
        port = inb.get("port")
        proto = inb.get("protocol")
        remark = inb.get("remark") or ""
        lines.append(f"  {iid} — :{port} — {proto} {remark}".rstrip())
    lines.append("\nДобавить нужные: /importinbounds <server_id> (автоматически)")
    return "\n".join(lines)


def admin_import_inbounds(
    server_id: int, summary: list[tuple[int, str, str]]
) -> str:
    if not summary:
        return f"На сервере #{server_id} не найдено inbound'ов для импорта."
    added = [s for s in summary if s[2] == "added"]
    exists = [s for s in summary if s[2] == "exists"]
    skipped = [s for s in summary if s[2] == "skipped"]
    lines = [f"Импорт inbound'ов сервера #{server_id}:"]
    if added:
        lines.append("Добавлены:")
        for iid, proto, _ in added:
            lines.append(f"  {iid} — {proto}")
    if exists:
        lines.append(
            "Уже были: " + ", ".join(str(iid) for iid, _, _ in exists)
        )
    if skipped:
        lines.append(
            "Пропущены (протокол не поддержан): "
            + ", ".join(f"{iid}/{proto}" for iid, proto, _ in skipped)
        )
    lines.append(
        "\nДля vless+reality при необходимости задайте flow вручную через "
        "/addinbound или отредактируйте server_inbounds."
    )
    return "\n".join(lines)


def admin_provision_result(
    ok: list[int], failed: list[tuple[int, str | None]]
) -> str:
    lines = ["Провижининг выполнен."]
    lines.append(f"Успешно (server_id): {', '.join(map(str, ok)) or '—'}")
    if failed:
        lines.append("Ошибки:")
        for server_id, err in failed:
            lines.append(f"  server {server_id}: {err}")
    return "\n".join(lines)


def sharing_disabled() -> str:
    return "Антишеринг-мониторинг отключён (ANTI_SHARING_ENABLED=false)."


def admin_clients_list(title: str, clients: list[VpnClient]) -> str:
    if not clients:
        return f"{title}: список пуст."
    lines = [f"{title}:\n"]
    for c in clients:
        user = c.user
        username = f"@{user.username}" if user and user.username else "—"
        tg_id = user.telegram_id if user else "?"
        lines.append(f"{username} (TG {tg_id}) — до {_fmt_date(c.expires_at)}")
    return "\n".join(lines)

from __future__ import annotations

from datetime import UTC, datetime
from html import escape

from app.bot import emoji
from app.db.enums import PaymentStatus
from app.db.models import (
    PAYMENT_KIND_TRAFFIC,
    SERVER_PURPOSE_WHITELIST,
    PaymentRequest,
    Server,
    User,
    VpnClient,
)

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
BTN_NEWS = "Новостной канал"
BTN_WHITELIST = "Обход белых списков"
BTN_WHITELIST_REFRESH = "Обновить остаток"

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
    """Unified SubHub connection screen with live server availability."""
    lines = [f"{emoji.tg('connect')} <b>Подключение</b>", "", "Доступность серверов:"]
    if not servers:
        lines.extend(["", "Серверы пока не настроены. Обратитесь в поддержку."])
        return "\n".join(lines)
    for server in servers:
        if server.is_online is True:
            status = emoji.tg("ok")
        elif server.is_online is False:
            status = emoji.tg("down")
        else:
            status = emoji.tg("unknown")
        lines.append(f"{escape(server_button_label(server))} — {status}")
    return "\n".join(lines)


def connection_preparing() -> str:
    return (
        f"{emoji.tg('connect')} <b>Подписка подготавливается</b>\n\n"
        "Серверы уже получили ваш доступ. Обновление единой ссылки может занять "
        "несколько секунд — откройте этот раздел ещё раз."
    )


def connection_unavailable() -> str:
    return (
        f"{emoji.tg('connect')} <b>Подключение временно недоступно</b>\n\n"
        "Не удалось получить единую ссылку. Попробуйте ещё раз немного позже "
        "или обратитесь в поддержку."
    )


def fmt_gb_set(size_bytes: int | None) -> str:
    """Заданный объём (пакет, начисление, бесплатный пакет): как его ввёл администратор.

    Для остатков не использовать — их показывает `fmt_gb` (с округлением вниз).
    """
    from app.services.whitelist import set_volume_gib_text

    return f"{set_volume_gib_text(size_bytes).replace('.', ',')} ГБ"


def fmt_gb(size_bytes: int | None) -> str:
    """Остаток или расход в ГБ (1 ГБ = 1024³ байт), округлённый вниз: лишнего не обещаем."""
    from decimal import ROUND_DOWN, Decimal

    value = (Decimal(max(0, size_bytes or 0)) / Decimal(1024**3)).quantize(
        Decimal("0.01"), rounding=ROUND_DOWN
    )
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{text.replace('.', ',')} ГБ"


def fmt_money(amount: object) -> str:
    from decimal import Decimal

    value = Decimal(str(amount))
    if value == value.to_integral_value():
        return f"{int(value)} ₽"
    return f"{value:.2f} ₽".replace(".", ",")


def payment_subject(payment: PaymentRequest) -> str:
    if payment.kind == PAYMENT_KIND_TRAFFIC:
        return f"Трафик «{BTN_WHITELIST}»: {fmt_gb_set(payment.traffic_bytes)}"
    return f"Срок: {period_label(payment.period_days)}"


def period_label(period_days: int) -> str:
    from app.services.plans import PLANS

    for plan in PLANS:
        if plan.period_days == period_days:
            return f"{period_days} дней ({plan.title})"
    return f"{period_days} дней"


def payment_pending_review(payment: PaymentRequest) -> str:
    """Отказ создать новую заявку: прежняя с квитанцией ждёт проверки."""
    purpose = (
        f"покупка трафика, {fmt_gb_set(payment.traffic_bytes)}"
        if payment.kind == PAYMENT_KIND_TRAFFIC
        else f"продление подписки, {period_label(payment.period_days)}"
    )
    return (
        f"Заявка {payment.payment_code} ({purpose}) уже на проверке. "
        "Дождитесь решения администратора."
    )


def payment_created(
    payment: PaymentRequest, details_text: str
) -> str:
    return (
        f"Заявка <code>{escape(payment.payment_code)}</code> создана.\n\n"
        f"Сумма: {fmt_money(payment.amount)}\n"
        f"{escape(payment_subject(payment))}\n\n"
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


def access_update_pending(client: VpnClient, pending_servers: int) -> str:
    return (
        "Оплата учтена.\n"
        f"Срок подписки сохранён до {_fmt_date(client.expires_at)}.\n\n"
        f"Обновление серверов ещё выполняется: {pending_servers}. "
        "Часть подключений может быть недоступна. Повторно оплачивать не нужно."
    )


def first_purchase_channel_prompt() -> str:
    return (
        "Подпишитесь на наш канал с новостями о сервисе — "
        "там публикуем важные объявления и обновления."
    )


def news_channel_prompt() -> str:
    return (
        "Присоединяйтесь к новостному каналу сервиса.\n\n"
        "Там публикуем важные объявления, обновления и новости."
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


def payment_status_label(payment: PaymentRequest) -> str:
    if payment.kind == PAYMENT_KIND_TRAFFIC and payment.status == PaymentStatus.APPLIED:
        if payment.apply_pending_version is not None:
            return "трафик начислен, ожидается применение на сервере"
        return "трафик начислен"
    if payment.status == PaymentStatus.APPLIED and payment.last_error:
        return "оплата учтена, ожидается синхронизация серверов"
    return STATUS_LABELS.get(payment.status, payment.status.value)


def admin_payment_card(payment: PaymentRequest, user: User) -> str:
    username = f"@{escape(user.username)}" if user.username else "—"
    status = escape(payment_status_label(payment))
    pid = f"<code>{escape(user.public_id)}</code>" if user.public_id else "—"
    if payment.kind == PAYMENT_KIND_TRAFFIC:
        subject = f"Покупка трафика «{BTN_WHITELIST}»: {fmt_gb_set(payment.traffic_bytes)}"
    else:
        subject = f"Срок: +{payment.period_days} дней"
    text = (
        f"Новая заявка <code>{escape(payment.payment_code)}</code>\n\n"
        f"Пользователь: {username}\n"
        f"ID: {pid}\n"
        f"Telegram ID: {user.telegram_id}\n"
        f"Сумма: {fmt_money(payment.amount)}\n"
        f"{escape(subject)}\n"
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
        status = escape(payment_status_label(p))
        kind = f" — трафик {fmt_gb_set(p.traffic_bytes)}" if p.kind == PAYMENT_KIND_TRAFFIC else ""
        lines.append(
            f"<code>{escape(p.payment_code)}</code> — {fmt_money(p.amount)}{kind} — "
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
        subject = (
            f"трафик {fmt_gb_set(p.traffic_bytes)}"
            if p.kind == PAYMENT_KIND_TRAFFIC else f"+{p.period_days} дн."
        )
        lines.append(
            f"<code>{escape(p.payment_code)}</code> — {username} — "
            f"{fmt_money(p.amount)} — {subject}"
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


def sharing_all(items: list) -> str:
    """Полный краткий отчёт по IP-наблюдениям всех VPN-клиентов."""
    if not items:
        return "VPN-клиентов для IP-отчёта пока нет."
    lines = ["Антишеринг: все клиенты, уникальные IP (за 24 ч):\n"]
    for client, status in items:
        user = client.user
        username = f"@{user.username}" if user and user.username else "—"
        pid = (user.public_id if user else None) or "—"
        lines.append(
            f"{sharing_level_label(status.level).upper()} — {username} (ID {pid}) — "
            f"24ч: {status.unique_24h}; 1ч: {status.counts.get('1h', 0)}; "
            f"7д: {status.counts.get('7d', 0)}"
        )
    lines.append("\nДетали: /sharing <telegram_id>")
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


_INVENTORY_LABELS = {
    "ready": "готов к выдаче",
    "error": "ошибка синхронизации",
    "needs_choice": "нужно выбрать целевой inbound",
    "incompatible": "целевой inbound несовместим с SubHub",
}


def server_purpose_label(server) -> str:
    if getattr(server, "purpose", None) == SERVER_PURPOSE_WHITELIST:
        return BTN_WHITELIST
    return "Обычный VPN"


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
        f"Услуга: {server_purpose_label(server)}",
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
    if getattr(server, "purpose", None) == SERVER_PURPOSE_WHITELIST:
        status = _INVENTORY_LABELS.get(server.inventory_status or "", "не синхронизирован")
        lines.append(f"Готовность услуги: {status}")
        if server.inventory_error:
            lines.append(f"Сверка: {server.inventory_error}")
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
    disabled = [s for s in summary if s[2] == "disabled"]
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
    if disabled:
        lines.append(
            "Отключены (удалены или выключены в панели): "
            + ", ".join(str(iid) for iid, _, _ in disabled)
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


# --- «Обход белых списков» -----------------------------------------------------

_WL_STATUS = {
    "not_launched": "услуга ещё не запущена",
    "no_access": "нужна активная подписка",
    "expired": "подписка истекла — конфиг остановлен",
    "lifetime": "работает, трафик без ограничений",
    "active": "работает",
    "exhausted": "трафик закончился — конфиг остановлен",
    "blocked": "отключён администратором",
}


def whitelist_overview(ov, paid_free_bytes: int) -> str:
    """Раздел услуги для пользователя. parse_mode='HTML'."""
    lines = [
        f"{emoji.tg('connect')} <b>{BTN_WHITELIST}</b>",
        "",
        f"Статус: {_WL_STATUS.get(ov.status, ov.status)}",
    ]
    if ov.status == "not_launched":
        lines.extend([
            "",
            "Отдельный конфиг для работы при ограничениях по белым спискам "
            "скоро появится в вашей подписке.",
        ])
        return "\n".join(lines)
    if ov.status == "lifetime":
        lines.append("Подписка VPN: бессрочная")
    elif ov.expires_at is not None:
        lines.append(f"Подписка VPN: до {_fmt_date(ov.expires_at)}")
    if ov.status != "lifetime":
        lines.extend([
            "",
            f"Бесплатный остаток: <b>{fmt_gb(ov.free_bytes)}</b>",
            f"Купленный остаток: <b>{fmt_gb(ov.paid_bytes)}</b>",
            "",
            "Сначала расходуется бесплатный трафик, затем купленный. "
            f"Каждая оплата подписки восстанавливает бесплатный остаток до "
            f"{fmt_gb_set(paid_free_bytes)}. Купленный трафик не сгорает.",
        ])
    if ov.status in ("expired", "no_access"):
        lines.extend([
            "",
            "Пока подписка не активна, конфиг не работает, даже если трафик "
            "остался. Сохранённый остаток станет доступен после продления.",
        ])
    elif ov.status == "exhausted":
        lines.extend([
            "",
            "Обычные конфиги подписки продолжают работать. Чтобы возобновить "
            "этот конфиг, купите пакет или дождитесь следующей оплаты подписки.",
        ])
    elif ov.status == "blocked":
        lines.extend(["", "По вопросам обратитесь в поддержку."])
    when = _fmt_date(ov.last_synced_at) if ov.last_synced_at else "—"
    if ov.awaiting and ov.status != "lifetime":
        lines.extend(["", f"{emoji.tg('unknown')} Остатки показаны на {when} и ещё не учитывают:"])
        for credit in ov.awaiting:
            if credit.free_set is not None:
                lines.append(
                    f"• бесплатный остаток будет восстановлен до {fmt_gb_set(credit.free_set)}"
                )
            if credit.paid_delta is not None:
                lines.append(f"• купленный трафик +{fmt_gb_set(credit.paid_delta)}")
        if ov.uncertain:
            tail = "Расход за время, когда сервер не отвечал, уточняет администратор."
        elif ov.stale:
            tail = "Сервер временно не отвечает — остатки пересчитаются после сверки расхода."
        else:
            tail = "Остатки пересчитаются после сверки расхода с сервером."
        lines.append(f"Оплата сохранена. {tail}")
    elif ov.stale:
        lines.extend([
            "",
            f"{emoji.tg('unknown')} Сервер временно не отвечает: показан последний "
            f"подтверждённый остаток (сверка: {when}).",
        ])
    if ov.pending:
        lines.extend([
            "",
            "Изменения применяются на сервере — обычно это занимает несколько минут.",
        ])
    if ov.status in ("active", "lifetime", "exhausted"):
        lines.extend([
            "",
            f"Конфиг «{BTN_WHITELIST}» входит в вашу обычную ссылку подписки "
            "(«Подключение»). Отдельная ссылка не нужна.",
        ])
    if ov.can_buy and ov.packages:
        lines.extend(["", "Пакеты трафика:"])
        for package in ov.packages:
            lines.append(f"• {fmt_gb_set(package.traffic_bytes)} — {fmt_money(package.price)}")
    return "\n".join(lines)


def whitelist_package_button(package) -> str:
    return f"{fmt_gb_set(package.traffic_bytes)} — {fmt_money(package.price)}"


def traffic_credited(size_bytes: int | None, pending: bool) -> str:
    text = (
        f"{emoji.tg('ok')} Оплата подтверждена. Начислено "
        f"{fmt_gb_set(size_bytes)} трафика «{BTN_WHITELIST}».\n"
        "Срок подписки не меняется, купленный трафик не сгорает."
    )
    if pending:
        text += (
            "\n\nПрименение на сервере ещё выполняется. Повторно оплачивать не нужно."
        )
    return text


def traffic_credited_expired(size_bytes: int | None) -> str:
    return (
        f"{emoji.tg('ok')} Оплата подтверждена. Начислено {fmt_gb_set(size_bytes)} "
        f"трафика «{BTN_WHITELIST}».\n\n"
        "Подписка сейчас не активна, поэтому конфиг остановлен. Трафик сохранён и "
        "станет доступен после продления подписки."
    )


def whitelist_pending_note() -> str:
    return (
        f"\n\nКонфиг «{BTN_WHITELIST}» обновится на сервере в течение нескольких "
        "минут."
    )


def _fmt_span(seconds: float) -> str:
    seconds = max(0, int(seconds))
    if seconds < 90:
        return f"{seconds} с"
    if seconds < 5400:
        return f"{round(seconds / 60)} мин"
    return f"{seconds / 3600:.1f} ч".replace(".", ",")


def reconcile_status_lines(status, now: datetime | None = None) -> list[str]:
    """Состояние фоновой сверки расхода для админ-раздела (по данным процесса)."""
    now = now or datetime.now(UTC)
    report = status.last_report
    lines: list[str] = []
    if status.last_success_at is None:
        lines.append("Сверка расхода: чистый обход с запуска бота ещё не завершён")
    else:
        age = _fmt_span(status.success_age(now).total_seconds())
        worst = _fmt_span(status.worst_case_staleness(now).total_seconds())
        lines.append(
            f"Сверка расхода: последний обход без ошибок завершён {age} назад "
            f"(данные учёта не старше {worst})"
        )
    if report is not None:
        lines.append(
            f"  последний обход: {_fmt_span(report.active_seconds)}, пачек {report.batches}, "
            f"сверено {report.reconciled}, пропущено {report.skipped}, "
            f"ошибок {report.errors}"
        )
    current = status.current
    if current is not None and current.aborted:
        lines.append(
            f"  обход прерван ({current.aborted}), впереди учётов: {current.remaining}"
        )
    return lines


def admin_whitelist_home(config, server, summary, packages) -> str:
    lines = [f"Услуга «{BTN_WHITELIST}»", ""]
    lines.append(f"Услуга: {'запущена' if config.service_enabled else 'не запущена'}")
    if server is None:
        lines.append("Сервер: не добавлен (Серверы → Добавить → «Обход белых списков»)")
    else:
        status = _INVENTORY_LABELS.get(server.inventory_status or "", "не синхронизирован")
        online = {True: "онлайн", False: "офлайн"}.get(server.is_online, "не проверялся")
        lines.append(f"Сервер: #{server.id} {server.name} — {status}, {online}")
        targets = [i for i in server.inbounds if i.enabled]
        if len(targets) == 1:
            remark = f" «{targets[0].remark}»" if targets[0].remark else ""
            lines.append(
                f"Целевой inbound: {targets[0].inbound_id} "
                f"({targets[0].protocol.value}){remark}"
            )
        if server.inventory_error:
            lines.append(f"Сверка: {server.inventory_error}")
    lines.extend([
        "",
        f"Бесплатно за оплату подписки: {fmt_gb_set(config.paid_free_bytes)}",
        f"Бесплатно за пробный период: {fmt_gb_set(config.trial_free_bytes)}",
        "",
        "Пакеты покупки:",
    ])
    if not packages:
        lines.append("  нет")
    for package in packages:
        state = "" if package.enabled else " (отключён)"
        lines.append(
            f"  #{package.id}: {fmt_gb_set(package.traffic_bytes)} — "
            f"{fmt_money(package.price)}{state}"
        )
    lines.extend([
        "",
        f"Учётов: {summary.accounts}; ожидают применения: {summary.pending}; "
        f"ошибок: {summary.errors}; расхождений: {summary.conflicts}; "
        f"заблокировано: {summary.blocked}",
        f"Начисления ждут сверки расхода: {summary.unsettled}; "
        f"требуют решения: {summary.uncertain}",
    ])
    if summary.reconcile is not None:
        lines.extend(reconcile_status_lines(summary.reconcile))
    lines.append("Пользователь: /wl <telegram_id>")
    return "\n".join(lines)


def admin_whitelist_inventory(result) -> str:
    labels = {
        "ready": "Сервер готов к выдаче конфигов.",
        "error": "Сервер не готов: синхронизация не удалась.",
        "needs_choice": "Сервер не готов: выберите единственный целевой inbound.",
        "incompatible": "Сервер не готов: SubHub не построит ссылку для целевого inbound.",
    }
    lines = [labels.get(result.status, result.status)]
    if result.error:
        lines.append(result.error)
    if result.status == "incompatible":
        lines.append(
            "Конфиг не попал бы в подписку. Исправьте inbound в панели и "
            "синхронизируйте сервер или выберите другой inbound."
        )
    if result.status == "ready":
        lines.append(
            "Проверен только формат inbound для ссылок SubHub. Это не подтверждает, "
            "что панель добавлена в конфигурацию SubHub: проверьте её там "
            "(GET /admin/servers) до выдачи."
        )
    return "\n".join(lines)


def admin_whitelist_rollout_plan(plan, config) -> str:
    counts = plan.counts
    lines = [
        f"Выдача услуги «{BTN_WHITELIST}» нынешним пользователям",
        "",
        f"Оплаченная подписка: {counts.get('paid', 0)} → {fmt_gb_set(config.paid_free_bytes)}",
        f"Пробный период: {counts.get('trial', 0)} → {fmt_gb_set(config.trial_free_bytes)}",
        f"Бессрочный доступ: {counts.get('lifetime', 0)} → без ограничений",
        f"Неоднозначные: {counts.get('ambiguous', 0)} (нет оплаты, покрывающей "
        "текущий срок, и нет следа пробного периода — например, привязка или "
        "ручное продление)",
        f"Уже получили пакет: {plan.already_served} (повторно не выдаётся)",
    ]
    if plan.ambiguous_users:
        lines.append("")
        lines.append("Неоднозначные (TG / ID / срок):")
        for telegram_id, public_id, expires in plan.ambiguous_users[:20]:
            lines.append(f"  {telegram_id} / {public_id or '—'} / {_fmt_date(expires)}")
        if len(plan.ambiguous_users) > 20:
            lines.append(f"  …и ещё {len(plan.ambiguous_users) - 20}")
    lines.extend([
        "",
        "Повторный запуск безопасен: второй начальный пакет не выдаётся, купленный "
        "остаток не меняется. Применение на сервере идёт в фоне.",
    ])
    return "\n".join(lines)


def admin_whitelist_rollout_report(report) -> str:
    granted = report.granted
    return (
        "Выдача выполнена.\n"
        f"Оплаченные: {granted.get('paid', 0)}, пробные: {granted.get('trial', 0)}, "
        f"неоднозначные (как оплаченные): {granted.get('ambiguous', 0)}\n"
        f"Бессрочные: {report.lifetime}\n"
        f"Уже имели пакет: {report.skipped_existing}\n"
        f"Неоднозначные пропущены: {report.skipped_ambiguous}\n\n"
        "Конфиги создаются на сервере в фоне; прогресс — «ожидают применения»."
    )


def admin_whitelist_packages(packages) -> str:
    if not packages:
        return "Пакетов нет. Добавьте первый."
    lines = ["Пакеты покупки трафика (созданные заявки хранят свою цену и объём):", ""]
    for package in packages:
        state = "включён" if package.enabled else "отключён"
        lines.append(
            f"#{package.id}: {fmt_gb_set(package.traffic_bytes)} — "
            f"{fmt_money(package.price)} — {state}"
        )
    return "\n".join(lines)


def _wl_event_label(event) -> str:
    parts = []
    if event.free_set is not None:
        parts.append(f"бесплатный := {fmt_gb_set(event.free_set)}")
    if event.paid_delta is not None:
        parts.append(f"купленный +{fmt_gb_set(event.paid_delta)}")
    state = {"pending": "ждёт сверки", "uncertain": "нужно решение"}.get(
        event.status, event.status
    )
    note = f" — {event.note}" if event.note else ""
    return f"  #{event.id} {_fmt_date(event.created_at)}: {', '.join(parts)} [{state}]{note}"


def admin_whitelist_user(user, account, overview, events=(), outcomes=None) -> str:
    lines = [
        f"«{BTN_WHITELIST}»: {user.public_id or '—'} (TG {user.telegram_id})",
        f"Статус: {_WL_STATUS.get(overview.status, overview.status)}",
    ]
    if account is None:
        lines.append("Учёта нет (пакеты не выдавались).")
        return "\n".join(lines)
    lines.extend([
        f"Бесплатный: {fmt_gb(account.free_bytes)} ({account.free_bytes} байт)",
        f"Купленный: {fmt_gb(account.paid_bytes)} ({account.paid_bytes} байт)",
        f"Счётчик панели на сверке: {account.usage_checkpoint_bytes}",
        f"Последняя сверка: {_fmt_date(account.last_synced_at)}",
        f"Применено на панели: totalGB={account.applied_total_bytes}, "
        f"enable={account.applied_enable}, версия {account.applied_version}/"
        f"{account.desired_version}",
        f"Заблокирован админом: {'да' if account.admin_blocked else 'нет'}",
    ])
    if account.last_error:
        lines.append(f"Ошибка применения: {account.last_error}")
    if account.conflict:
        lines.append(f"Расхождение: {account.conflict}")
    if events:
        lines.append("Начисления, не применённые к остаткам выше (по порядку):")
        lines.extend(_wl_event_label(event) for event in events)
    uncertain = next((e for e in events if e.status == "uncertain"), None)
    if uncertain is not None:
        tg = user.telegram_id
        if outcomes is not None:
            (free_b, paid_b), (free_a, paid_a) = outcomes
            span = (uncertain.anchor_max_bytes or 0) - (uncertain.anchor_min_bytes or 0)
            lines.extend([
                f"Расход {fmt_gb(span)} нельзя автоматически отнести до или после "
                f"начисления #{uncertain.id}. Варианты на конец этого периода:",
                f"  до: бесплатный {fmt_gb(free_b)}, купленный {fmt_gb(paid_b)}",
                f"  после: бесплатный {fmt_gb(free_a)}, купленный {fmt_gb(paid_a)}",
                f"Решение: /wlresolve {tg} до|после <причина> или "
                f"/wladjust {tg} <бесплатно ГБ> <куплено ГБ> <причина>",
            ])
        else:
            lines.append(
                f"Расход до начисления #{uncertain.id} не прочитан с сервера. Задайте "
                f"остатки: /wladjust {tg} <бесплатно ГБ> <куплено ГБ> <причина>"
            )
    return "\n".join(lines)

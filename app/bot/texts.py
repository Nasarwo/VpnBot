from __future__ import annotations

from datetime import UTC, datetime

from app.db.enums import PaymentStatus
from app.db.models import PaymentRequest, User, VpnClient

# Кнопки пользовательского меню
BTN_MY_ACCESS = "Мой доступ"
BTN_EXTEND = "Продлить"
BTN_TRIAL = "Пробные 2 дня"
BTN_MY_LINKS = "Мои ссылки"
BTN_SUPPORT = "Поддержка"

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
    name = user.first_name or "пользователь"
    return (
        f"Здравствуйте, {name}.\n\n"
        "Это бот управления вашей подпиской на личный доступ.\n"
        f"Ваш ID: {user.public_id or '—'}\n"
        "Сообщите этот ID при обращении в поддержку.\n\n"
        "Выберите действие в меню ниже."
    )


def access_status(client: VpnClient | None, public_id: str | None = None) -> str:
    prefix = f"Ваш ID: {public_id}\n\n" if public_id else ""
    if client is None or client.expires_at is None:
        return prefix + (
            "Срок доступа: не активирован.\n\n"
            "Нажмите «Продлить», чтобы оформить подписку."
        )
    expires = client.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    now = datetime.now(tz=UTC)
    if expires > now:
        days_left = (expires - now).days
        return prefix + (
            f"Срок доступа активен до: {_fmt_date(expires)}\n"
            f"Осталось дней: {days_left}"
        )
    return prefix + (
        f"Срок доступа истёк: {_fmt_date(expires)}\n\n"
        "Нажмите «Продлить», чтобы возобновить доступ."
    )


def choose_plan() -> str:
    return (
        "Выберите тариф продления подписки:\n\n"
        "Чем длиннее срок, тем выгоднее месяц доступа."
    )


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
        f"Заявка {payment.payment_code} создана.\n\n"
        f"Сумма: {amount} ₽\n"
        f"Срок: {period_label(payment.period_days)}\n\n"
        "Переведите оплату по реквизитам:\n"
        f"{details_text}\n\n"
        "После оплаты отправьте сюда чек, скриншот или сообщение об оплате."
    )


def proof_received(payment_code: str) -> str:
    return (
        f"Подтверждение по заявке {payment_code} получено.\n"
        "Администратор проверит оплату и продлит доступ. Мы пришлём уведомление."
    )


def no_open_request() -> str:
    return (
        "Активной заявки нет.\n"
        "Нажмите «Продлить», чтобы создать заявку на продление."
    )


def links_message(links: list[tuple[str, str]]) -> str:
    if not links:
        return (
            "Ссылки подключения пока недоступны.\n"
            "Они появятся после активации или продления доступа."
        )
    lines = ["Ваши ссылки подключения:\n"]
    for label, url in links:
        lines.append(f"{label}:\n{url}\n")
    return "\n".join(lines)


def trial_granted(client: VpnClient, period_days: int) -> str:
    return (
        f"Пробный доступ на {period_days} дня активирован.\n"
        f"Срок действия до: {_fmt_date(client.expires_at)}\n\n"
        "Ссылки подключения доступны по кнопке «Мои ссылки»."
    )


def trial_already_used() -> str:
    return (
        "Пробный период уже был использован на этом аккаунте.\n"
        "Оформить полный доступ можно по кнопке «Продлить»."
    )


def trial_no_client() -> str:
    return (
        "Для активации пробного периода обратитесь в поддержку: "
        "ваш профиль ещё не подключён."
    )


def trial_failed() -> str:
    return (
        "Не удалось активировать пробный период из-за временной ошибки.\n"
        "Попробуйте ещё раз позже или обратитесь в поддержку."
    )


def support_message(contact: str, public_id: str | None = None) -> str:
    id_line = f"Ваш ID: {public_id}\n" if public_id else ""
    return (
        "Поддержка.\n\n"
        f"{id_line}"
        f"По вопросам подключения и оплаты обращайтесь: {contact}\n"
        "Укажите свой ID — так мы быстрее вас найдём."
    )


def access_extended(client: VpnClient) -> str:
    return (
        "Доступ продлён.\n"
        f"Новый срок действия: {_fmt_date(client.expires_at)}\n\n"
        "Актуальные ссылки доступны по кнопке «Мои ссылки»."
    )


def payment_rejected(payment_code: str) -> str:
    return (
        f"Заявка {payment_code} отклонена.\n"
        "Если это ошибка, свяжитесь с поддержкой."
    )


# --- Админские тексты ---


def admin_payment_card(payment: PaymentRequest, user: User) -> str:
    username = f"@{user.username}" if user.username else "—"
    amount = int(payment.amount) if payment.amount == int(payment.amount) else payment.amount
    status = STATUS_LABELS.get(payment.status, payment.status.value)
    text = (
        f"Новая заявка {payment.payment_code}\n\n"
        f"Пользователь: {username}\n"
        f"ID: {user.public_id or '—'}\n"
        f"Telegram ID: {user.telegram_id}\n"
        f"Сумма: {amount} ₽\n"
        f"Срок: +{payment.period_days} дней\n"
        f"Статус: {status}"
    )
    if payment.last_error:
        text += f"\n\nОшибка: {payment.last_error}"
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
        status = STATUS_LABELS.get(p.status, p.status.value)
        lines.append(
            f"{p.payment_code} — {int(p.amount)} ₽ — {status} — {_fmt_date(p.created_at)}"
        )
    return "\n".join(lines)


def admin_pending(payments: list[PaymentRequest]) -> str:
    if not payments:
        return "Заявок в ожидании проверки нет."
    lines = ["Заявки в ожидании проверки:\n"]
    for p in payments:
        user = p.user
        username = f"@{user.username}" if user and user.username else "—"
        amount = int(p.amount) if p.amount == int(p.amount) else p.amount
        lines.append(
            f"{p.payment_code} — {username} — {amount} ₽ — +{p.period_days} дн."
        )
    lines.append("\nПодтвердить: /confirm <код>\nОтклонить: /reject <код>")
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

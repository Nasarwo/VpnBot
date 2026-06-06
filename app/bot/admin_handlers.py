from __future__ import annotations

import logging
from datetime import UTC, datetime

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import keyboards, notify, texts
from app.bot.callbacks import PaymentCallback
from app.bot.filters import IsAdmin
from app.config import Settings
from app.db.enums import PaymentStatus, Protocol
from app.db.models import Server, ServerInbound, User
from app.db.repositories import (
    PaymentRepository,
    ServerRepository,
    UserRepository,
    VpnClientRepository,
)
from app.services import antishare, billing, provisioning
from app.services.ip_provider import build_ip_provider
from app.services.panel_updater import PanelUpdateError, PanelUpdater
from app.services.xui_client import XuiClient, XuiError
from app.services.xui_updater import build_updater

logger = logging.getLogger(__name__)

router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


def _get_updater(settings: Settings) -> PanelUpdater:
    return build_updater(timeout=float(settings.xui_request_timeout))


@router.callback_query(PaymentCallback.filter())
async def on_payment_action(
    callback: CallbackQuery,
    callback_data: PaymentCallback,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
) -> None:
    action = callback_data.action
    payment_id = callback_data.payment_id
    logger.info(
        "Админ tg=%s действие=%s по заявке id=%s",
        db_user.telegram_id,
        action,
        payment_id,
    )
    pay_repo = PaymentRepository(session)

    if action == "history":
        payment = await pay_repo.get_by_id_with_relations(payment_id)
        if payment is None:
            await callback.answer("Заявка не найдена", show_alert=True)
            return
        history = await pay_repo.history_for_user(payment.user_id)
        await callback.message.answer(texts.admin_history(history))
        await callback.answer()
        return

    if action == "profile":
        payment = await pay_repo.get_by_id_with_relations(payment_id)
        if payment is None:
            await callback.answer("Заявка не найдена", show_alert=True)
            return
        client = await VpnClientRepository(session).get_for_user(payment.user_id)
        await callback.message.answer(texts.admin_profile(payment.user, client))
        await callback.answer()
        return

    if action == "reject":
        payment = await billing.reject_payment(
            session, payment_id, actor_user_id=db_user.id
        )
        payment = await pay_repo.get_by_id_with_relations(payment_id)
        if payment is not None:
            await notify.notify_user_rejected(
                callback.bot, payment.user.telegram_id, payment.payment_code
            )
        await callback.message.edit_text(
            f"Заявка отклонена.\n\n{texts.admin_payment_card(payment, payment.user)}"
        )
        await callback.answer("Заявка отклонена")
        return

    if action in ("confirm", "retry"):
        updater = _get_updater(settings)
        if action == "confirm":
            result = await billing.confirm_payment(
                session, payment_id, actor_user_id=db_user.id, updater=updater
            )
        else:
            result = await billing.retry_payment(
                session, payment_id, actor_user_id=db_user.id, updater=updater
            )

        payment = await pay_repo.get_by_id_with_relations(payment_id)

        if result.already_applied:
            await callback.answer("Заявка уже применена ранее", show_alert=True)
            return

        if result.applied and payment is not None:
            client = await VpnClientRepository(session).get_for_user(payment.user_id)
            if client is not None:
                await notify.notify_user_extended(
                    callback.bot, payment.user.telegram_id, client
                )
            await callback.message.edit_text(
                f"Готово. Доступ продлён.\n\n"
                f"{texts.admin_payment_card(payment, payment.user)}"
            )
            await callback.answer("Доступ продлён")
            return

        if payment is not None:
            await notify.notify_admins_failed(
                callback.bot, settings, payment, payment.user
            )
            await callback.message.edit_text(
                f"Ошибка применения.\n\n"
                f"{texts.admin_payment_card(payment, payment.user)}",
                reply_markup=keyboards.admin_retry_keyboard(payment_id),
            )
        await callback.answer("Не удалось применить продление", show_alert=True)
        return

    await callback.answer("Неизвестное действие", show_alert=True)


@router.message(Command("pending"))
async def list_pending(message: Message, session: AsyncSession) -> None:
    payments = await PaymentRepository(session).list_waiting_admin()
    await message.answer(texts.admin_pending(payments))


@router.message(Command("confirm"))
async def confirm_cmd(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
) -> None:
    code = (command.args or "").strip()
    if not code:
        await message.answer("Использование: /confirm <код заявки>, например /confirm PAY-1042")
        return

    pay_repo = PaymentRepository(session)
    payment = await pay_repo.get_by_code(code)
    if payment is None:
        await message.answer("Заявка с таким кодом не найдена")
        return

    updater = _get_updater(settings)
    try:
        if payment.status == PaymentStatus.FAILED:
            result = await billing.retry_payment(
                session, payment.id, actor_user_id=db_user.id, updater=updater
            )
        else:
            result = await billing.confirm_payment(
                session, payment.id, actor_user_id=db_user.id, updater=updater
            )
    except billing.BillingError as exc:
        await message.answer(str(exc))
        return

    full = await pay_repo.get_by_id_with_relations(payment.id)
    if result.already_applied:
        await message.answer(f"Заявка {code} уже была применена ранее.")
        return
    if result.applied and full is not None:
        client = await VpnClientRepository(session).get_for_user(full.user_id)
        if client is not None:
            await notify.notify_user_extended(
                message.bot, full.user.telegram_id, client
            )
        await message.answer(f"Готово. Заявка {code} подтверждена, доступ продлён.")
        return

    if full is not None:
        await notify.notify_admins_failed(message.bot, settings, full, full.user)
    await message.answer(
        f"Не удалось применить продление по заявке {code} "
        "(серверы 3x-ui недоступны). Повторите команду /confirm позже."
    )


@router.message(Command("reject"))
async def reject_cmd(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    db_user: User,
) -> None:
    code = (command.args or "").strip()
    if not code:
        await message.answer("Использование: /reject <код заявки>, например /reject PAY-1042")
        return

    pay_repo = PaymentRepository(session)
    payment = await pay_repo.get_by_code(code)
    if payment is None:
        await message.answer("Заявка с таким кодом не найдена")
        return

    await billing.reject_payment(session, payment.id, actor_user_id=db_user.id)
    full = await pay_repo.get_by_id_with_relations(payment.id)
    if full is not None:
        await notify.notify_user_rejected(
            message.bot, full.user.telegram_id, full.payment_code
        )
    await message.answer(f"Заявка {code} отклонена.")


@router.message(Command("sharing"))
async def sharing_report(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    settings: Settings,
) -> None:
    if not settings.anti_sharing_enabled:
        await message.answer(texts.sharing_disabled())
        return

    args = (command.args or "").strip()
    if not args:
        flagged = await antishare.list_flagged(session, settings)
        await message.answer(texts.sharing_summary(flagged))
        return

    try:
        telegram_id = int(args.split()[0])
    except ValueError:
        await message.answer("Использование: /sharing [telegram_id]")
        return

    target = await UserRepository(session).get_by_telegram_id(telegram_id)
    if target is None:
        await message.answer("Пользователь не найден")
        return
    client = await VpnClientRepository(session).get_for_user(target.id)
    if client is None:
        await message.answer("У пользователя нет VPN-клиента")
        return

    now = datetime.now(tz=UTC)
    status = await antishare.compute_status(session, client.id, settings, now=now)
    since = now - antishare.WINDOWS["24h"]
    ips = await antishare.recent_ips(session, client.id, since)
    settings_summary = (
        f"Пороги: лимит IP {settings.default_ip_limit}, "
        f"warn 24ч {settings.warn_threshold_24h}, "
        f"critical 24ч {settings.critical_threshold_24h}"
    )
    await message.answer(
        texts.sharing_detail(target, status, ips, settings_summary)
    )


@router.message(Command("ipscan"))
async def ip_scan(
    message: Message, session: AsyncSession, settings: Settings
) -> None:
    if not settings.anti_sharing_enabled:
        await message.answer(texts.sharing_disabled())
        return
    await message.answer("Запускаю сбор IP из 3x-ui…")
    provider = build_ip_provider(timeout=float(settings.xui_request_timeout))
    added = await antishare.collect_all(session, provider)
    flagged = await antishare.list_flagged(session, settings)
    await message.answer(
        f"Сбор завершён. Добавлено наблюдений: {added}.\n\n"
        + texts.sharing_summary(flagged)
    )


@router.message(Command("servers"))
async def list_servers(message: Message, session: AsyncSession) -> None:
    servers = await ServerRepository(session).list_all()
    await message.answer(texts.admin_servers(servers))


@router.message(Command("addserver"))
async def add_server(
    message: Message, command: CommandObject, session: AsyncSession
) -> None:
    raw = (command.args or "").strip()
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 5:
        await message.answer(
            "Формат: /addserver name|country|panel_url|username|password"
            "|[kind]|[subscription_base]\n"
            "Пример: /addserver Германия|DE|https://de:2053|admin|pass|direct|"
            "https://de:2096/sub/"
        )
        return
    name, country, panel_url, username, password = parts[:5]
    kind = parts[5] if len(parts) > 5 and parts[5] else "direct"
    sub_base = parts[6] if len(parts) > 6 and parts[6] else None
    server = Server(
        name=name,
        country=country or None,
        panel_url=panel_url,
        username=username,
        password=password,
        kind=kind,
        subscription_base=sub_base,
        enabled=True,
    )
    session.add(server)
    await session.commit()
    await message.answer(f"Сервер добавлен: #{server.id} {server.name}")


@router.message(Command("addinbound"))
async def add_inbound(
    message: Message, command: CommandObject, session: AsyncSession
) -> None:
    args = (command.args or "").split()
    if len(args) < 3:
        await message.answer(
            "Формат: /addinbound <server_id> <inbound_id> <protocol> [flow] [method]\n"
            "protocol: vless|vmess|trojan|shadowsocks|hysteria2\n"
            "Пример: /addinbound 1 7 vless xtls-rprx-vision"
        )
        return
    try:
        server_id = int(args[0])
        inbound_id = int(args[1])
    except ValueError:
        await message.answer("server_id и inbound_id должны быть числами")
        return
    try:
        protocol = Protocol(args[2].lower())
    except ValueError:
        await message.answer(
            "Неизвестный протокол. Допустимо: vless, vmess, trojan, "
            "shadowsocks, hysteria2"
        )
        return
    server = await ServerRepository(session).get_by_id(server_id)
    if server is None:
        await message.answer("Сервер не найден")
        return
    flow = args[3] if len(args) > 3 else None
    method = args[4] if len(args) > 4 else None
    inbound = ServerInbound(
        server_id=server_id,
        inbound_id=inbound_id,
        protocol=protocol,
        flow=flow,
        method=method,
        enabled=True,
    )
    session.add(inbound)
    await session.commit()
    await message.answer(
        f"Inbound добавлен на сервер #{server_id}: id={inbound_id} "
        f"{protocol.value}"
    )


@router.message(Command("delinbound"))
async def del_inbound(
    message: Message, command: CommandObject, session: AsyncSession
) -> None:
    args = (command.args or "").split()
    if len(args) < 2:
        await message.answer(
            "Формат: /delinbound <server_id> <inbound_id>\n"
            "inbound_id — это id панели (см. /servers). "
            "Удаляет inbound только из настроек бота, на панели он остаётся.\n"
            "Удалить все сразу: /clearinbounds <server_id>"
        )
        return
    try:
        server_id = int(args[0])
        inbound_id = int(args[1])
    except ValueError:
        await message.answer("server_id и inbound_id должны быть числами")
        return
    repo = ServerRepository(session)
    if await repo.get_by_id(server_id) is None:
        await message.answer("Сервер не найден")
        return
    deleted = await repo.delete_inbound(server_id, inbound_id)
    if not deleted:
        await message.answer(
            f"На сервере #{server_id} нет настроенного inbound {inbound_id}."
        )
        return
    await session.commit()
    logger.info(
        "Админ tg=%s удалил inbound %s сервера #%s (записей: %s)",
        message.from_user.id if message.from_user else "?",
        inbound_id,
        server_id,
        deleted,
    )
    await message.answer(
        f"Inbound {inbound_id} удалён из настроек сервера #{server_id}. "
        "Новым клиентам он больше не выдаётся."
    )


@router.message(Command("clearinbounds"))
async def clear_inbounds(
    message: Message, command: CommandObject, session: AsyncSession
) -> None:
    args = (command.args or "").split()
    if not args:
        await message.answer("Использование: /clearinbounds <server_id>")
        return
    try:
        server_id = int(args[0])
    except ValueError:
        await message.answer("server_id должен быть числом")
        return
    repo = ServerRepository(session)
    if await repo.get_by_id(server_id) is None:
        await message.answer("Сервер не найден")
        return
    deleted = await repo.clear_inbounds(server_id)
    await session.commit()
    logger.info(
        "Админ tg=%s очистил inbound'ы сервера #%s (записей: %s)",
        message.from_user.id if message.from_user else "?",
        server_id,
        deleted,
    )
    await message.answer(
        f"Удалено настроенных inbound'ов: {deleted} (сервер #{server_id})."
    )


@router.message(Command("inbounds"))
async def list_panel_inbounds(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    settings: Settings,
) -> None:
    args = (command.args or "").split()
    if not args:
        await message.answer("Использование: /inbounds <server_id>")
        return
    try:
        server_id = int(args[0])
    except ValueError:
        await message.answer("server_id должен быть числом")
        return
    server = await ServerRepository(session).get_by_id(server_id)
    if server is None:
        await message.answer("Сервер не найден")
        return
    try:
        async with XuiClient(
            base_url=server.panel_url,
            username=server.username,
            password=server.password,
            timeout=float(settings.xui_request_timeout),
        ) as client:
            inbounds = await client.list_inbounds()
    except XuiError as exc:
        await message.answer(f"Ошибка панели: {exc}")
        return
    await message.answer(texts.admin_panel_inbounds(server_id, inbounds))


@router.message(Command("importinbounds"))
async def import_panel_inbounds(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    settings: Settings,
) -> None:
    args = (command.args or "").split()
    if not args:
        await message.answer("Использование: /importinbounds <server_id>")
        return
    try:
        server_id = int(args[0])
    except ValueError:
        await message.answer("server_id должен быть числом")
        return
    server = await ServerRepository(session).get_by_id(server_id)
    if server is None:
        await message.answer("Сервер не найден")
        return
    try:
        summary = await provisioning.import_inbounds(
            session, server, timeout=float(settings.xui_request_timeout)
        )
    except PanelUpdateError as exc:
        await message.answer(f"Ошибка панели: {exc}")
        return
    await session.commit()
    await message.answer(texts.admin_import_inbounds(server_id, summary))


@router.message(Command("provision"))
async def provision_user(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    settings: Settings,
) -> None:
    args = (command.args or "").split()
    if not args:
        await message.answer("Использование: /provision <telegram_id>")
        return
    try:
        telegram_id = int(args[0])
    except ValueError:
        await message.answer("telegram_id должен быть числом")
        return
    target = await UserRepository(session).get_by_telegram_id(telegram_id)
    if target is None:
        await message.answer("Пользователь не найден")
        return

    client = await provisioning.ensure_vpn_client(session, target)
    expiry = client.expires_at or datetime.now(tz=UTC)
    results = await provisioning.apply_access(
        session,
        client,
        target.public_id or client.email or str(target.id),
        expiry,
        _get_updater(settings),
    )
    await session.commit()
    ok = [r.server_id for r in results if r.ok]
    failed = [(r.server_id, r.error) for r in results if not r.ok]
    await message.answer(texts.admin_provision_result(ok, failed))


@router.message(Command("active"))
async def list_active(message: Message, session: AsyncSession) -> None:
    clients = await VpnClientRepository(session).list_active()
    await message.answer(texts.admin_clients_list("Активные клиенты", clients))


@router.message(Command("expired"))
async def list_expired(message: Message, session: AsyncSession) -> None:
    clients = await VpnClientRepository(session).list_expired()
    await message.answer(texts.admin_clients_list("Истёкшие клиенты", clients))


@router.message(Command("extend"))
async def manual_extend(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
) -> None:
    args = (command.args or "").split()
    if not args:
        await message.answer("Использование: /extend <telegram_id> [дней]")
        return
    try:
        telegram_id = int(args[0])
        days = int(args[1]) if len(args) > 1 else settings.payment_period_days
    except ValueError:
        await message.answer("Некорректные аргументы. /extend <telegram_id> [дней]")
        return

    target = await UserRepository(session).get_by_telegram_id(telegram_id)
    if target is None:
        await message.answer("Пользователь не найден")
        return
    client = await VpnClientRepository(session).get_for_user(target.id)
    if client is None:
        await message.answer("У пользователя нет VPN-клиента")
        return

    result = await billing.manual_extend(
        session,
        vpn_client_id=client.id,
        period_days=days,
        actor_user_id=db_user.id,
        updater=_get_updater(settings),
    )
    if result.applied:
        await message.answer(
            f"Клиент продлён до {result.new_expires_at:%d.%m.%Y %H:%M UTC}"
        )
        await notify.notify_user_extended(message.bot, telegram_id, client)
    else:
        servers = ", ".join(str(r.server_id) for r in result.failed_servers)
        await message.answer(f"Не удалось обновить серверы: {servers}")


@router.message(Command("sync"))
async def sync_user(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
) -> None:
    if not command.args:
        await message.answer("Использование: /sync <telegram_id>")
        return
    try:
        telegram_id = int(command.args.strip())
    except ValueError:
        await message.answer("Некорректный telegram_id")
        return

    target = await UserRepository(session).get_by_telegram_id(telegram_id)
    if target is None:
        await message.answer("Пользователь не найден")
        return
    client = await VpnClientRepository(session).get_for_user(target.id)
    if client is None:
        await message.answer("У пользователя нет VPN-клиента")
        return

    try:
        results = await billing.sync_client(
            session,
            vpn_client_id=client.id,
            actor_user_id=db_user.id,
            updater=_get_updater(settings),
        )
    except billing.BillingError as exc:
        await message.answer(str(exc))
        return

    ok = sum(1 for r in results if r.ok)
    failed = [r for r in results if not r.ok]
    text = f"Синхронизация завершена. Успешно: {ok}, ошибок: {len(failed)}."
    if failed:
        text += "\n" + "\n".join(
            f"server {r.server_id}: {r.error}" for r in failed
        )
    await message.answer(text)

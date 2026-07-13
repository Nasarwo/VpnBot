from __future__ import annotations

import logging
from datetime import UTC, datetime
from html import escape
from urllib.parse import urlparse

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import keyboards, notify, texts, ui
from app.bot.callbacks import AdminCallback, BindCallback, PaymentCallback
from app.bot.filters import IsAdmin
from app.bot.states import AdminStates
from app.config import Settings
from app.db.enums import BindRequestStatus, PaymentStatus, Protocol
from app.db.models import Server, ServerInbound, User
from app.db.repositories import (
    BindRequestRepository,
    PaymentRepository,
    ServerRepository,
    UserRepository,
    VpnClientRepository,
)
from app.services import (
    antishare,
    billing,
    bind_requests,
    broadcast,
    provisioning,
    subscription_delete,
)
from app.services.ip_provider import build_ip_provider
from app.services.panel_updater import PanelUpdateError, PanelUpdater
from app.services.subhub_client import trigger_configured_sync
from app.services.xui_client import XuiClient, XuiError
from app.services.xui_updater import build_updater

logger = logging.getLogger(__name__)

router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


def _get_updater(settings: Settings) -> PanelUpdater:
    return build_updater(timeout=float(settings.xui_request_timeout))


def _parse_server_line(raw: str) -> tuple[Server | None, str | None]:
    """Парсит строку 'name|country|panel_url|username|password|[kind]|[sub]'.

    Возвращает (server, None) при успехе или (None, текст ошибки).
    """
    parts = [p.strip() for p in (raw or "").split("|")]
    if len(parts) < 5:
        return None, (
            "Нужно минимум 5 полей через «|».\n"
            "Формат: name|country|panel_url|username|password|[kind]|[sub]"
        )
    name, country, panel_url, username, password = parts[:5]
    if not all([name, panel_url, username, password]):
        return None, "Обязательны поля: name, panel_url, username, password."
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
    return server, None


def _validate_server_name(raw: str) -> tuple[str | None, str | None]:
    name = (raw or "").strip()
    if not name:
        return None, "Название не может быть пустым."
    if len(name) > 255:
        return None, (
            "Название слишком длинное (максимум 255 символов)."
        )
    return name, None


def _validate_subscription_base(
    raw: str,
) -> tuple[str | None, str | None]:
    value = (raw or "").strip()
    if value in {"-", "—"}:
        return None, None
    if not value:
        return None, (
            "URL не может быть пустым. Для удаления отправьте «-»."
        )
    if len(value) > 512:
        return None, "URL слишком длинный (максимум 512 символов)."
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None, "Введите полный URL с http:// или https://."
    return value, None


async def _finalize_new_server(
    session: AsyncSession, server: Server, settings: Settings
) -> str:
    """Сохраняет сервер и сразу пытается импортировать его inbound'ы.

    Так добавленный сервер становится готовой целью провижининга без отдельного
    ручного шага импорта.
    """
    await ServerRepository(session).add(server)
    await session.commit()
    text = f"Сервер добавлен: #{server.id} {server.name}"
    try:
        summary = await provisioning.import_inbounds(
            session, server, timeout=float(settings.xui_request_timeout)
        )
        await session.commit()
        text += "\n\n" + texts.admin_import_inbounds(server.id, summary)
    except PanelUpdateError as exc:
        text += (
            f"\n\nInbound'ы не импортированы автоматически: {exc}\n"
            "Запустите импорт вручную в /admin → сервер → «Импорт inbound'ов»."
        )
    return text


async def _edit_panel(
    callback: CallbackQuery,
    text: str,
    markup,
    alert: str | None = None,
    parse_mode: str | None = None,
) -> None:
    """Редактирует сообщение админ-панели, мягко гасит ошибки.

    parse_mode=None — обычный текст (безопасно для URL/email в карточках серверов).
    parse_mode="HTML" — там, где в тексте есть разметка (например, <code> в заявках).
    """
    try:
        await callback.message.edit_text(
            text, reply_markup=markup, parse_mode=parse_mode
        )
    except TelegramBadRequest:
        # сообщение не изменилось / нельзя отредактировать — игнорируем
        pass
    await ui.answer_callback(callback, alert, show_alert=bool(alert))


@router.message(Command("admin"))
async def admin_panel(message: Message, session: AsyncSession) -> None:
    servers = await ServerRepository(session).list_all()
    await message.answer(
        texts.admin_panel_home(servers),
        reply_markup=keyboards.admin_home_keyboard(),
    )


@router.callback_query(AdminCallback.filter())
async def admin_nav(
    callback: CallbackQuery,
    callback_data: AdminCallback,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
    state: FSMContext,
) -> None:
    action = callback_data.action
    sid = callback_data.server_id
    repo = ServerRepository(session)
    logger.info(
        "Админ tg=%s панель действие=%s server_id=%s",
        db_user.telegram_id,
        action,
        sid,
    )

    if action == "home":
        await state.clear()
        servers = await repo.list_all()
        await _edit_panel(
            callback, texts.admin_panel_home(servers),
            keyboards.admin_home_keyboard(),
        )
        return

    if action == "servers":
        await state.clear()
        servers = await repo.list_all()
        await _edit_panel(
            callback, texts.admin_servers_title(servers),
            keyboards.admin_servers_keyboard(servers),
        )
        return

    if action == "server":
        await state.clear()
        server = await repo.get_with_inbounds(sid)
        if server is None:
            servers = await repo.list_all()
            await _edit_panel(
                callback, texts.admin_servers_title(servers),
                keyboards.admin_servers_keyboard(servers),
                alert="Сервер не найден",
            )
            return
        await _edit_panel(
            callback, texts.admin_server_detail(server),
            keyboards.admin_server_keyboard(server),
        )
        return

    if action == "toggle":
        server = await repo.get_by_id(sid)
        if server is None:
            await ui.answer_callback(callback, "Сервер не найден", show_alert=True)
            return
        server.enabled = not server.enabled
        await session.commit()
        server = await repo.get_with_inbounds(sid)
        await _edit_panel(
            callback, texts.admin_server_detail(server),
            keyboards.admin_server_keyboard(server),
            alert="Включён" if server.enabled else "Выключен",
        )
        return

    if action == "rename":
        server = await repo.get_by_id(sid)
        if server is None:
            await ui.answer_callback(callback, "Сервер не найден", show_alert=True)
            return
        await state.set_state(AdminStates.waiting_server_name)
        await state.update_data(server_id=sid)
        await _edit_panel(
            callback,
            f"Текущее название сервера #{sid}: {server.name}\n\n"
            "Пришлите новое название. Отмена: /cancel.",
            keyboards.admin_back_keyboard("server", sid),
        )
        return

    if action == "subscription_url":
        server = await repo.get_by_id(sid)
        if server is None:
            await ui.answer_callback(callback, "Сервер не найден", show_alert=True)
            return
        await state.set_state(AdminStates.waiting_server_subscription_url)
        await state.update_data(server_id=sid)
        await _edit_panel(
            callback,
            f"URL подписки сервера #{sid}: "
            f"{server.subscription_base or 'не задан'}\n\n"
            "Пришлите новый полный URL. Чтобы удалить URL, отправьте «-». "
            "Отмена: /cancel.",
            keyboards.admin_back_keyboard("server", sid),
        )
        return

    if action == "import":
        server = await repo.get_by_id(sid)
        if server is None:
            await ui.answer_callback(callback, "Сервер не найден", show_alert=True)
            return
        try:
            summary = await provisioning.import_inbounds(
                session, server, timeout=float(settings.xui_request_timeout)
            )
        except PanelUpdateError as exc:
            await ui.answer_callback(
                callback, f"Ошибка панели: {exc}"[:200], show_alert=True
            )
            return
        await session.commit()
        server = await repo.get_with_inbounds(sid)
        await _edit_panel(
            callback,
            texts.admin_import_inbounds(sid, summary)
            + "\n\n"
            + texts.admin_server_detail(server),
            keyboards.admin_server_keyboard(server),
            alert="Inbound'ы импортированы",
        )
        return

    if action == "clients":
        server = await repo.get_by_id(sid)
        if server is None:
            await ui.answer_callback(callback, "Сервер не найден", show_alert=True)
            return
        try:
            clients = await provisioning.list_panel_clients(
                server, timeout=float(settings.xui_request_timeout)
            )
        except PanelUpdateError as exc:
            await ui.answer_callback(
                callback, f"Ошибка панели: {exc}"[:200], show_alert=True
            )
            return
        await _edit_panel(
            callback, texts.admin_panel_clients(sid, clients),
            keyboards.admin_back_keyboard("server", sid),
        )
        return

    if action == "del":
        server = await repo.get_by_id(sid)
        if server is None:
            await ui.answer_callback(callback, "Сервер не найден", show_alert=True)
            return
        await _edit_panel(
            callback, texts.admin_confirm_delete(server),
            keyboards.admin_confirm_delete_keyboard(sid),
        )
        return

    if action == "del_yes":
        server = await repo.get_by_id(sid)
        name = server.name if server else "?"
        deleted = await repo.delete(sid)
        if deleted:
            await session.commit()
            logger.info("Админ tg=%s удалил сервер #%s", db_user.telegram_id, sid)
        servers = await repo.list_all()
        await _edit_panel(
            callback, texts.admin_servers_title(servers),
            keyboards.admin_servers_keyboard(servers),
            alert=(
                texts.admin_server_deleted(sid, name)
                if deleted
                else "Сервер не найден"
            ),
        )
        return

    if action == "add":
        await state.set_state(AdminStates.waiting_server_line)
        await _edit_panel(
            callback, texts.admin_add_server_prompt(),
            keyboards.admin_back_keyboard("servers"),
        )
        return

    if action == "broadcast":
        await state.set_state(AdminStates.waiting_broadcast)
        count = await UserRepository(session).count()
        await _edit_panel(
            callback, texts.admin_broadcast_prompt(count),
            keyboards.admin_back_keyboard("home"),
        )
        return

    if action == "delete_subscription":
        await state.set_state(AdminStates.waiting_delete_subscription_client_id)
        await _edit_panel(
            callback,
            "Пришлите внутренний ID клиента из 3x-ui, чью подписку нужно удалить.\n"
            "Например: <code>6B8A6580</code>\n\n"
            "Клиент будет удалён со всех серверов и из бота. Отмена: /cancel.",
            keyboards.admin_back_keyboard("home"),
            parse_mode="HTML",
        )
        return

    if action == "pending":
        payments = await PaymentRepository(session).list_waiting_admin()
        binds = await BindRequestRepository(session).list_waiting_admin()
        body = texts.admin_pending(payments)
        body += "\n\n" + texts.admin_bind_pending(binds)
        await _edit_panel(
            callback, body,
            keyboards.admin_back_keyboard("home"),
            parse_mode="HTML",
        )
        return

    if action == "sharing":
        if not settings.anti_sharing_enabled:
            await _edit_panel(
                callback, texts.sharing_disabled(),
                keyboards.admin_back_keyboard("home"),
            )
            return
        flagged = await antishare.list_flagged(session, settings)
        await _edit_panel(
            callback, texts.sharing_summary(flagged),
            keyboards.admin_back_keyboard("home"),
        )
        return

    await ui.answer_callback(callback, "Неизвестное действие", show_alert=True)


@router.message(AdminStates.waiting_server_line, Command("cancel"))
async def admin_add_server_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.admin_add_cancelled())


@router.message(AdminStates.waiting_server_line, F.text)
async def admin_add_server_line(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    settings: Settings,
) -> None:
    server, error = _parse_server_line(message.text or "")
    if error is not None:
        await message.answer(error + "\n\nИли отправьте /cancel.")
        return
    text = await _finalize_new_server(session, server, settings)
    await state.clear()
    logger.info(
        "Админ tg=%s добавил сервер #%s через панель",
        message.from_user.id if message.from_user else "?",
        server.id,
    )
    servers = await ServerRepository(session).list_all()
    await message.answer(
        text, reply_markup=keyboards.admin_servers_keyboard(servers)
    )


@router.message(AdminStates.waiting_server_name, Command("cancel"))
async def admin_rename_server_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Переименование отменено.")


@router.message(AdminStates.waiting_server_name, F.text)
async def admin_rename_server_name(
    message: Message, session: AsyncSession, state: FSMContext, db_user: User
) -> None:
    name, error = _validate_server_name(message.text or "")
    if error is not None:
        await message.answer(
            error + "\n\nПришлите другое название или /cancel."
        )
        return
    data = await state.get_data()
    server_id = data.get("server_id")
    if not isinstance(server_id, int):
        await state.clear()
        await message.answer(
            "Не удалось определить сервер. Откройте его карточку снова."
        )
        return
    server = await ServerRepository(session).rename(server_id, name)
    if server is None:
        await state.clear()
        await message.answer("Сервер не найден — возможно, он был удалён.")
        return
    await session.commit()
    await state.clear()
    logger.info(
        "Админ tg=%s переименовал сервер #%s в %r",
        db_user.telegram_id,
        server.id,
        server.name,
    )
    renamed_server = await ServerRepository(session).get_with_inbounds(server.id)
    if renamed_server is None:  # Защита от удаления после commit.
        await message.answer("Сервер был удалён сразу после переименования.")
        return
    await message.answer(
        f"Название сервера #{renamed_server.id} изменено на "
        f"«{renamed_server.name}».\n\n"
        + texts.admin_server_detail(renamed_server),
        reply_markup=keyboards.admin_server_keyboard(renamed_server),
    )


@router.message(AdminStates.waiting_server_subscription_url, Command("cancel"))
async def admin_subscription_url_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Изменение URL подписки отменено.")


@router.message(AdminStates.waiting_server_subscription_url, F.text)
async def admin_subscription_url_value(
    message: Message, session: AsyncSession, state: FSMContext, db_user: User
) -> None:
    value, error = _validate_subscription_base(message.text or "")
    if error is not None:
        await message.answer(error + "\n\nПришлите другой URL, «-» или /cancel.")
        return
    data = await state.get_data()
    server_id = data.get("server_id")
    if not isinstance(server_id, int):
        await state.clear()
        await message.answer(
            "Не удалось определить сервер. Откройте его карточку снова."
        )
        return
    server = await ServerRepository(session).set_subscription_base(server_id, value)
    if server is None:
        await state.clear()
        await message.answer("Сервер не найден — возможно, он был удалён.")
        return
    await session.commit()
    await state.clear()
    logger.info(
        "Админ tg=%s изменил URL подписки сервера #%s",
        db_user.telegram_id,
        server.id,
    )
    server = await ServerRepository(session).get_with_inbounds(server.id)
    if server is None:
        await message.answer("Сервер был удалён сразу после изменения URL.")
        return
    result = value or "удалён"
    await message.answer(
        f"URL подписки сервера #{server.id}: {result}.\n\n"
        + texts.admin_server_detail(server),
        reply_markup=keyboards.admin_server_keyboard(server),
    )


@router.message(AdminStates.waiting_broadcast, Command("cancel"))
async def admin_broadcast_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.admin_broadcast_cancelled())


@router.message(AdminStates.waiting_broadcast, F.text)
async def admin_broadcast_send(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    db_user: User,
) -> None:
    text = message.text or ""
    await state.clear()
    telegram_ids = await UserRepository(session).all_telegram_ids()
    logger.info(
        "Админ tg=%s запустил рассылку на %s получателей",
        db_user.telegram_id,
        len(telegram_ids),
    )
    await message.answer(f"Начинаю рассылку на {len(telegram_ids)} получателей…")
    result = await broadcast.send_broadcast(message.bot, telegram_ids, text)
    await message.answer(
        texts.admin_broadcast_result(result.total, result.sent, result.failed),
        reply_markup=keyboards.admin_home_keyboard(),
    )


@router.message(AdminStates.waiting_delete_subscription_client_id, Command("cancel"))
async def admin_delete_subscription_cancel(
    message: Message, state: FSMContext
) -> None:
    await state.clear()
    await message.answer(
        "Удаление подписки отменено.",
        reply_markup=keyboards.admin_home_keyboard(),
    )


@router.message(AdminStates.waiting_delete_subscription_client_id, F.text)
async def admin_delete_subscription_by_client_id(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    db_user: User,
    settings: Settings,
) -> None:
    raw = (message.text or "").strip()
    if not raw:
        await message.answer("ID клиента не должен быть пустым. Отмена: /cancel.")
        return

    target = await UserRepository(session).get_by_public_id(raw)
    if target is None:
        await message.answer("Клиент с таким ID не найден. Отмена: /cancel.")
        return

    await message.answer("Удаляю клиента с серверов и из бота...")
    result = await subscription_delete.delete_user_subscription(
        session,
        target,
        _get_updater(settings),
        actor_user_id=db_user.id,
    )
    if result.no_client:
        await state.clear()
        await message.answer(
            "У пользователя нет подписки в боте.",
            reply_markup=keyboards.admin_home_keyboard(),
        )
        return

    if result.failed_servers:
        await state.clear()
        failed = "\n".join(
            f"server {r.server_id}: {r.error}" for r in result.failed_servers
        )
        await message.answer(
            "Не удалось удалить подписку со всех серверов. "
            "Локальные данные в боте не удалены.\n\n"
            f"{failed}\n\nПовторите позже или проверьте панели.",
            reply_markup=keyboards.admin_home_keyboard(),
        )
        return

    await trigger_configured_sync(
        settings.subhub_url,
        settings.subhub_admin_token,
        timeout=settings.subhub_timeout_seconds,
    )
    await state.clear()
    await notify.notify_user_subscription_deleted(message.bot, target.telegram_id)
    logger.info(
        "Админ tg=%s удалил подписку клиента public_id=%s user_tg=%s",
        db_user.telegram_id,
        target.public_id,
        target.telegram_id,
    )
    await message.answer(
        f"Подписка клиента {target.public_id or raw} удалена со всех серверов и из бота.",
        reply_markup=keyboards.admin_home_keyboard(),
    )


@router.callback_query(BindCallback.filter())
async def on_bind_action(
    callback: CallbackQuery,
    callback_data: BindCallback,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
) -> None:
    action = callback_data.action
    request_id = callback_data.request_id
    logger.info(
        "Админ tg=%s действие=%s по привязке id=%s",
        db_user.telegram_id,
        action,
        request_id,
    )
    bind_repo = BindRequestRepository(session)
    updater = _get_updater(settings)

    if action == "reject":
        try:
            await bind_requests.reject_request(
                session, request_id, actor_user_id=db_user.id
            )
        except bind_requests.BindRequestError as exc:
            await ui.answer_callback(callback, str(exc), show_alert=True)
            return
        full = await bind_repo.get_by_id_with_user(request_id)
        if full is not None and full.user is not None:
            await notify.notify_user_bind_rejected(
                callback.bot, full.user.telegram_id, full.request_code
            )
        await callback.message.edit_text(
            f"Привязка отклонена.\n\n{texts.admin_bind_card(full, full.user)}",
            parse_mode="HTML",
        )
        await ui.answer_callback(callback, "Привязка отклонена")
        return

    if action in ("confirm", "retry"):
        try:
            if action == "confirm":
                result = await bind_requests.approve_request(
                    session, request_id, actor_user_id=db_user.id, updater=updater
                )
            else:
                result = await bind_requests.retry_request(
                    session, request_id, actor_user_id=db_user.id, updater=updater
                )
        except bind_requests.BindRequestError as exc:
            await ui.answer_callback(callback, str(exc), show_alert=True)
            return

        full = await bind_repo.get_by_id_with_user(request_id)
        if full is None:
            await ui.answer_callback(callback, "Заявка не найдена", show_alert=True)
            return

        if result.already_applied:
            await ui.answer_callback(
                callback, "Привязка уже выполнена ранее", show_alert=True
            )
            return

        if result.applied and full.user is not None:
            await trigger_configured_sync(
                settings.subhub_url,
                settings.subhub_admin_token,
                timeout=settings.subhub_timeout_seconds,
            )
            await notify.notify_user_bind_approved(
                callback.bot, full.user.telegram_id, full.public_id
            )
            await callback.message.edit_text(
                f"Готово. Аккаунт привязан.\n\n"
                f"{texts.admin_bind_card(full, full.user)}",
                parse_mode="HTML",
            )
            await ui.answer_callback(callback, "Привязка выполнена")
            return

        if full.user is not None:
            await notify.notify_admins_bind_failed(
                callback.bot, settings, full, full.user
            )
        card = texts.admin_bind_card(full, full.user)
        if full.last_error:
            card += f"\n\nОшибка: {escape(full.last_error)}"
        await callback.message.edit_text(
            f"Ошибка привязки.\n\n{card}",
            reply_markup=keyboards.admin_bind_retry_keyboard(request_id),
            parse_mode="HTML",
        )
        await ui.answer_callback(callback, "Не удалось привязать", show_alert=True)
        return

    await ui.answer_callback(callback, "Неизвестное действие", show_alert=True)


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
            await ui.answer_callback(callback, "Заявка не найдена", show_alert=True)
            return
        history = await pay_repo.history_for_user(payment.user_id)
        await callback.message.answer(
            texts.admin_history(history), parse_mode="HTML"
        )
        await ui.answer_callback(callback)
        return

    if action == "profile":
        payment = await pay_repo.get_by_id_with_relations(payment_id)
        if payment is None:
            await ui.answer_callback(callback, "Заявка не найдена", show_alert=True)
            return
        client = await VpnClientRepository(session).get_for_user(payment.user_id)
        await callback.message.answer(texts.admin_profile(payment.user, client))
        await ui.answer_callback(callback)
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
            f"Заявка отклонена.\n\n{texts.admin_payment_card(payment, payment.user)}",
            parse_mode="HTML",
        )
        await ui.answer_callback(callback, "Заявка отклонена")
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
            await ui.answer_callback(
                callback, "Заявка уже применена ранее", show_alert=True
            )
            return

        if result.applied and payment is not None:
            await trigger_configured_sync(
                settings.subhub_url,
                settings.subhub_admin_token,
                timeout=settings.subhub_timeout_seconds,
            )
            client = await VpnClientRepository(session).get_for_user(payment.user_id)
            if client is not None:
                await notify.notify_user_extended(
                    callback.bot,
                    payment.user.telegram_id,
                    client,
                    first_purchase=result.first_purchase,
                )
            await callback.message.edit_text(
                f"Готово. Доступ продлён.\n\n"
                f"{texts.admin_payment_card(payment, payment.user)}",
                parse_mode="HTML",
            )
            await ui.answer_callback(callback, "Доступ продлён")
            return

        if payment is not None:
            await notify.notify_admins_failed(
                callback.bot, settings, payment, payment.user
            )
            await callback.message.edit_text(
                f"Ошибка применения.\n\n"
                f"{texts.admin_payment_card(payment, payment.user)}",
                reply_markup=keyboards.admin_retry_keyboard(payment_id),
                parse_mode="HTML",
            )
        await ui.answer_callback(
            callback, "Не удалось применить продление", show_alert=True
        )
        return

    await ui.answer_callback(callback, "Неизвестное действие", show_alert=True)


@router.message(Command("pending"))
async def list_pending(message: Message, session: AsyncSession) -> None:
    payments = await PaymentRepository(session).list_waiting_admin()
    binds = await BindRequestRepository(session).list_waiting_admin()
    body = texts.admin_pending(payments) + "\n\n" + texts.admin_bind_pending(binds)
    await message.answer(body, parse_mode="HTML")


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
    code_html = f"<code>{escape(code)}</code>"
    if result.already_applied:
        await message.answer(
            f"Заявка {code_html} уже была применена ранее.", parse_mode="HTML"
        )
        return
    if result.applied and full is not None:
        await trigger_configured_sync(
            settings.subhub_url,
            settings.subhub_admin_token,
            timeout=settings.subhub_timeout_seconds,
        )
        client = await VpnClientRepository(session).get_for_user(full.user_id)
        if client is not None:
            await notify.notify_user_extended(
                message.bot,
                full.user.telegram_id,
                client,
                first_purchase=result.first_purchase,
            )
        await message.answer(
            f"Готово. Заявка {code_html} подтверждена, доступ продлён.",
            parse_mode="HTML",
        )
        return

    if full is not None:
        await notify.notify_admins_failed(message.bot, settings, full, full.user)
    await message.answer(
        f"Не удалось применить продление по заявке {code_html} "
        "(серверы 3x-ui недоступны). Повторите команду /confirm позже.",
        parse_mode="HTML",
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
    await message.answer(
        f"Заявка <code>{escape(code)}</code> отклонена.", parse_mode="HTML"
    )


@router.message(Command("confirmbind"))
async def confirm_bind_cmd(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
) -> None:
    code = (command.args or "").strip()
    if not code:
        await message.answer(
            "Использование: /confirmbind <код>, например /confirmbind BIND-2001"
        )
        return

    bind_repo = BindRequestRepository(session)
    req = await bind_repo.get_by_code(code)
    if req is None:
        await message.answer("Заявка на привязку с таким кодом не найдена")
        return

    updater = _get_updater(settings)
    try:
        if req.status == BindRequestStatus.FAILED:
            result = await bind_requests.retry_request(
                session, req.id, actor_user_id=db_user.id, updater=updater
            )
        else:
            result = await bind_requests.approve_request(
                session, req.id, actor_user_id=db_user.id, updater=updater
            )
    except bind_requests.BindRequestError as exc:
        await message.answer(str(exc))
        return

    full = await bind_repo.get_by_id_with_user(req.id)
    code_html = f"<code>{escape(code)}</code>"
    if result.already_applied:
        await message.answer(
            f"Заявка {code_html} уже была применена ранее.", parse_mode="HTML"
        )
        return
    if result.applied and full is not None and full.user is not None:
        await trigger_configured_sync(
            settings.subhub_url,
            settings.subhub_admin_token,
            timeout=settings.subhub_timeout_seconds,
        )
        await notify.notify_user_bind_approved(
            message.bot, full.user.telegram_id, full.public_id
        )
        await message.answer(
            f"Готово. Заявка {code_html} подтверждена, аккаунт привязан.",
            parse_mode="HTML",
        )
        return

    if full is not None and full.user is not None:
        await notify.notify_admins_bind_failed(message.bot, settings, full, full.user)
    await message.answer(
        f"Не удалось привязать по заявке {code_html}. "
        "Повторите /confirmbind позже.",
        parse_mode="HTML",
    )


@router.message(Command("rejectbind"))
async def reject_bind_cmd(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    db_user: User,
) -> None:
    code = (command.args or "").strip()
    if not code:
        await message.answer(
            "Использование: /rejectbind <код>, например /rejectbind BIND-2001"
        )
        return

    bind_repo = BindRequestRepository(session)
    req = await bind_repo.get_by_code(code)
    if req is None:
        await message.answer("Заявка на привязку с таким кодом не найдена")
        return

    await bind_requests.reject_request(session, req.id, actor_user_id=db_user.id)
    full = await bind_repo.get_by_id_with_user(req.id)
    if full is not None and full.user is not None:
        await notify.notify_user_bind_rejected(
            message.bot, full.user.telegram_id, full.request_code
        )
    await message.answer(
        f"Заявка <code>{escape(code)}</code> отклонена.", parse_mode="HTML"
    )


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
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    settings: Settings,
) -> None:
    raw = (command.args or "").strip()
    if not raw:
        await message.answer(
            "Формат: /addserver name|country|panel_url|username|password"
            "|[kind]|[subscription_base]\n"
            "Пример: /addserver Германия|DE|https://de:2053|admin|pass|direct|"
            "https://de:2096/sub/"
        )
        return
    server, error = _parse_server_line(raw)
    if error is not None:
        await message.answer(error)
        return
    text = await _finalize_new_server(session, server, settings)
    await message.answer(text)


@router.message(Command("renameserver"))
async def rename_server(
    message: Message, command: CommandObject, session: AsyncSession, db_user: User
) -> None:
    raw = (command.args or "").strip()
    server_id_raw, separator, name_raw = raw.partition(" ")
    if not separator:
        await message.answer("Формат: /renameserver <server_id> <новое название>")
        return
    try:
        server_id = int(server_id_raw)
    except ValueError:
        await message.answer("server_id должен быть числом")
        return
    name, error = _validate_server_name(name_raw)
    if error is not None:
        await message.answer(error)
        return
    server = await ServerRepository(session).rename(server_id, name)
    if server is None:
        await message.answer("Сервер не найден")
        return
    await session.commit()
    logger.info(
        "Админ tg=%s переименовал сервер #%s в %r",
        db_user.telegram_id,
        server.id,
        server.name,
    )
    await message.answer(f"Сервер #{server.id} переименован в «{server.name}».")


@router.message(Command("setsubscriptionurl"))
async def set_subscription_url(
    message: Message, command: CommandObject, session: AsyncSession, db_user: User
) -> None:
    raw = (command.args or "").strip()
    server_id_raw, separator, url_raw = raw.partition(" ")
    if not separator:
        await message.answer(
            "Формат: /setsubscriptionurl <server_id> <URL или ->"
        )
        return
    try:
        server_id = int(server_id_raw)
    except ValueError:
        await message.answer("server_id должен быть числом")
        return
    value, error = _validate_subscription_base(url_raw)
    if error is not None:
        await message.answer(error)
        return
    server = await ServerRepository(session).set_subscription_base(server_id, value)
    if server is None:
        await message.answer("Сервер не найден")
        return
    await session.commit()
    logger.info(
        "Админ tg=%s изменил URL подписки сервера #%s",
        db_user.telegram_id,
        server.id,
    )
    await message.answer(
        f"URL подписки сервера #{server.id} "
        + (f"изменён на {value}." if value else "удалён.")
    )


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
    if any(result.ok for result in results):
        await trigger_configured_sync(
            settings.subhub_url,
            settings.subhub_admin_token,
            timeout=settings.subhub_timeout_seconds,
        )
    ok = [r.server_id for r in results if r.ok]
    failed = [(r.server_id, r.error) for r in results if not r.ok]
    await message.answer(texts.admin_provision_result(ok, failed))


@router.message(Command("panelclients"))
async def list_panel_clients_cmd(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    settings: Settings,
) -> None:
    args = (command.args or "").split()
    if not args:
        await message.answer("Использование: /panelclients <server_id>")
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
        clients = await provisioning.list_panel_clients(
            server, timeout=float(settings.xui_request_timeout)
        )
    except PanelUpdateError as exc:
        await message.answer(f"Ошибка панели: {exc}")
        return
    await message.answer(texts.admin_panel_clients(server_id, clients))


@router.message(Command("bind"))
async def bind_panel_client(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    settings: Settings,
) -> None:
    args = (command.args or "").split()
    if len(args) < 3:
        await message.answer(
            "Формат: /bind <server_id> <email> <telegram_id>\n"
            "email — имя клиента в панели (см. /panelclients), "
            "telegram_id — пользователь, который уже запустил бота.\n"
            "Привязывает существующего клиента панели к боту и включает продление."
        )
        return
    try:
        server_id = int(args[0])
        telegram_id = int(args[2])
    except ValueError:
        await message.answer("server_id и telegram_id должны быть числами")
        return
    email = args[1]
    server = await ServerRepository(session).get_by_id(server_id)
    if server is None:
        await message.answer("Сервер не найден")
        return
    target = await UserRepository(session).get_by_telegram_id(telegram_id)
    if target is None:
        await message.answer(
            "Пользователь не найден. Попросите его сначала запустить бота (/start)."
        )
        return
    try:
        result = await provisioning.bind_existing_client(
            session,
            server,
            email,
            target,
            _get_updater(settings),
            timeout=float(settings.xui_request_timeout),
        )
    except PanelUpdateError as exc:
        await session.rollback()
        await message.answer(f"Не удалось привязать: {exc}")
        return
    await session.commit()
    logger.info(
        "Админ tg=%s привязал клиента %s сервера #%s к user tg=%s",
        message.from_user.id if message.from_user else "?",
        email,
        server_id,
        telegram_id,
    )
    await message.answer(texts.admin_bind_result(result))


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
    elif result.failed_servers:
        servers = ", ".join(str(r.server_id) for r in result.failed_servers)
        await message.answer(f"Не удалось обновить серверы: {servers}")
    else:
        await message.answer(
            "Нет активных привязок к серверам — срок в базе не изменён"
        )


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

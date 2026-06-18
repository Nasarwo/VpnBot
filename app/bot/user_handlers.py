from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import keyboards, notify, texts
from app.bot.callbacks import MenuCallback, OnboardCallback, PlanCallback
from app.bot.states import OnboardingStates, ProofStates
from app.config import Settings
from app.db.enums import AttachmentType, UserRole
from app.db.models import User, VpnClient
from app.db.repositories import (
    BindRequestRepository,
    PaymentRepository,
    ServerRepository,
    UserRepository,
    VpnClientRepository,
)
from app.services import access, audit, billing, bind_requests, payments, plans
from app.services.subscription_link import (
    parse_subscription_public_id,
    subscription_link_example,
)
from app.services.xui_updater import build_updater

logger = logging.getLogger(__name__)

router = Router(name="user")


def _is_active(client: VpnClient | None) -> bool:
    return access.has_active_timed_client(client)


def _welcome_markup(client: VpnClient | None, db_user: User):
    return keyboards.welcome_menu(
        access.has_client_access(client),
        is_admin=db_user.role == UserRole.ADMIN,
    )


async def _trial_available(session: AsyncSession, db_user: User) -> bool:
    """Пробный доступен, если им не пользовались и подписку никогда не оформляли."""
    if db_user.trial_used:
        return False
    last = await PaymentRepository(session).last_successful_for_user(db_user.id)
    return last is None


def _plan_title_for_period(period_days: int) -> str | None:
    for plan in plans.PLANS:
        if plan.period_days == period_days:
            return plan.title
    return None


def _needs_onboarding(db_user: User, client: VpnClient | None) -> bool:
    """Показываем вопрос только новым пользователям без VPN-клиента."""
    if db_user.onboarding_done:
        return False
    return client is None


async def _send_welcome(message: Message, db_user: User, client: VpnClient | None) -> None:
    await message.answer(
        texts.welcome(db_user),
        reply_markup=_welcome_markup(client, db_user),
        parse_mode="HTML",
    )


async def _edit(callback: CallbackQuery, text: str, markup) -> None:
    """Редактирует текущее сообщение (без спама в чат). При сбое — отправляет новое."""
    try:
        await callback.message.edit_text(
            text, reply_markup=markup, parse_mode="HTML"
        )
    except TelegramBadRequest as exc:
        # "message is not modified" игнорируем; иначе отправляем новое сообщение.
        if "message is not modified" in str(exc).lower():
            return
        await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    session: AsyncSession,
    db_user: User,
    state: FSMContext,
) -> None:
    client = await VpnClientRepository(session).get_for_user(db_user.id)
    try:
        stale = await message.answer(
            "\u2026", reply_markup=ReplyKeyboardRemove()
        )
        await stale.delete()
    except TelegramBadRequest:
        pass

    pending_bind = await BindRequestRepository(session).latest_waiting_for_user(
        db_user.id
    )
    if pending_bind is not None:
        await message.answer(
            texts.bind_request_waiting(pending_bind.request_code),
            parse_mode="HTML",
        )
        return

    current = await state.get_state()
    if current == OnboardingStates.waiting_legacy_link.state:
        await message.answer(
            texts.onboarding_send_link_prompt(subscription_link_example()),
            parse_mode="HTML",
        )
        return

    if _needs_onboarding(db_user, client):
        await message.answer(
            texts.onboarding_legacy_question(),
            reply_markup=keyboards.onboarding_legacy_keyboard(),
        )
        return

    await _send_welcome(message, db_user, client)


@router.callback_query(OnboardCallback.filter())
async def onboard_legacy(
    callback: CallbackQuery,
    callback_data: OnboardCallback,
    session: AsyncSession,
    db_user: User,
    state: FSMContext,
) -> None:
    if callback_data.answer == "no":
        db_user.onboarding_done = True
        await session.commit()
        await state.clear()
        client = await VpnClientRepository(session).get_for_user(db_user.id)
        await _edit(
            callback,
            texts.welcome(db_user),
            _welcome_markup(client, db_user),
        )
        await callback.answer()
        return

    await state.set_state(OnboardingStates.waiting_legacy_link)
    await _edit(
        callback,
        texts.onboarding_send_link_prompt(subscription_link_example()),
        None,
    )
    await callback.answer()


@router.message(OnboardingStates.waiting_legacy_link, F.text)
async def onboard_legacy_link(
    message: Message,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
    state: FSMContext,
) -> None:
    link = (message.text or "").strip()
    if link.startswith("/"):
        return
    example = subscription_link_example()
    if parse_subscription_public_id(link) is None:
        await message.answer(
            texts.onboarding_invalid_link(example),
            parse_mode="HTML",
        )
        return
    try:
        req = await bind_requests.create_request(session, db_user, link)
    except bind_requests.BindRequestError as exc:
        await message.answer(str(exc))
        return

    await notify.notify_admins_new_bind_request(
        message.bot, settings, req, db_user
    )
    await state.clear()
    await message.answer(
        texts.bind_request_received(req.request_code),
        parse_mode="HTML",
    )


@router.message(Command("admin"))
async def admin_denied(message: Message) -> None:
    # Сюда попадают только не-админы: для админов /admin перехватывает admin-роутер.
    await message.answer("У вас нет прав для этой команды.")


@router.callback_query(MenuCallback.filter())
async def menu_nav(
    callback: CallbackQuery,
    callback_data: MenuCallback,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
    state: FSMContext,
) -> None:
    action = callback_data.action
    logger.info("Меню tg=%s action=%s", db_user.telegram_id, action)
    client = await VpnClientRepository(session).get_for_user(db_user.id)
    has_access = access.has_client_access(client)
    is_admin = db_user.role == UserRole.ADMIN

    if action == "cancel_payment":
        await _cancel_payment(session, db_user, state)
        await _edit(
            callback, texts.welcome(db_user), _welcome_markup(client, db_user)
        )
        await callback.answer("Заявка отменена")
        return

    if action == "home":
        await _edit(
            callback, texts.welcome(db_user), _welcome_markup(client, db_user)
        )
    elif action == "admin_panel":
        if not is_admin:
            await callback.answer("Нет прав", show_alert=True)
            return
        servers = await ServerRepository(session).list_all()
        await _edit(
            callback,
            texts.admin_panel_home(servers),
            keyboards.admin_home_keyboard(),
        )
    elif action == "subscription":
        await _edit(
            callback,
            texts.subscription_overview(client, db_user.public_id),
            keyboards.subscription_menu(),
        )
    elif action == "extend":
        last = await PaymentRepository(session).last_successful_for_user(db_user.id)
        title = _plan_title_for_period(last.period_days) if last else None
        await _edit(
            callback, texts.extend_info(title), keyboards.extend_plans_keyboard()
        )
    elif action in {"connect", "connect_home"}:
        if not has_access:
            await callback.answer("Нет активной подписки", show_alert=True)
            return
        servers = await ServerRepository(session).list_enabled()
        await _edit(
            callback,
            texts.connection_overview(servers),
            keyboards.connection_keyboard(
                servers,
                db_user.public_id,
                back_action="home" if action == "connect_home" else "subscription",
            ),
        )
    elif action == "buy":
        show_trial = await _trial_available(session, db_user)
        await _edit(
            callback,
            texts.purchase_info(show_trial),
            keyboards.purchase_plans_keyboard(show_trial),
        )
    elif action == "install":
        await _edit(
            callback,
            texts.install_guides_intro(),
            keyboards.install_guides_keyboard(),
        )
    elif action == "free_proxies":
        await _edit(
            callback,
            texts.free_proxies_intro(),
            keyboards.free_proxies_keyboard(),
        )
    elif action == "support":
        await _edit(
            callback,
            texts.support_message(settings.support_contact, db_user.public_id),
            keyboards.back_keyboard("home"),
        )
    elif action == "reset":
        await _edit(
            callback,
            texts.reset_bot_prompt(),
            keyboards.reset_bot_confirm_keyboard(),
        )
    elif action == "reset_yes":
        await _reset_bot_user(callback, session, db_user, settings, state)
        return
    await callback.answer()


async def _reset_bot_user(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
    state: FSMContext,
) -> None:
    """Удаляет данные пользователя в боте и показывает онбординг заново."""
    await state.clear()
    telegram_id = db_user.telegram_id
    username = db_user.username
    first_name = db_user.first_name
    old_user_id = db_user.id
    old_public_id = db_user.public_id

    await audit.record(
        session,
        action="user.self_reset",
        actor_user_id=old_user_id,
        entity_type="user",
        entity_id=old_user_id,
        payload={"telegram_id": telegram_id, "public_id": old_public_id},
    )

    repo = UserRepository(session)
    await repo.delete_user(db_user)
    await session.commit()

    desired_role = (
        UserRole.ADMIN if settings.is_admin(telegram_id) else UserRole.USER
    )
    await repo.get_or_create(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        role=desired_role,
    )
    await session.commit()

    logger.info("Пользователь tg=%s сбросил данные бота", telegram_id)
    await _edit(
        callback,
        texts.onboarding_legacy_question(),
        keyboards.onboarding_legacy_keyboard(),
    )
    await callback.answer("Данные сброшены")


@router.callback_query(PlanCallback.filter())
async def select_plan(
    callback: CallbackQuery,
    callback_data: PlanCallback,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
    state: FSMContext,
) -> None:
    if callback_data.code == "trial":
        await _activate_trial(callback, session, db_user, settings)
        return

    plan = plans.get_plan(callback_data.code)
    if plan is None:
        await callback.answer("Тариф не найден", show_alert=True)
        return

    payment = await payments.create_request(
        session,
        user_id=db_user.id,
        amount=float(plan.amount_rub),
        period_days=plan.period_days,
    )
    await _edit(
        callback,
        texts.payment_created(payment, settings.payment_details_text),
        keyboards.cancel_payment_keyboard(),
    )
    # Админа уведомляем только после того, как пользователь пришлёт подтверждение.
    await state.set_state(ProofStates.waiting_proof)
    await callback.answer()


async def _cancel_payment(
    session: AsyncSession, db_user: User, state: FSMContext
) -> None:
    """Удаляет неподтверждённую заявку (без приложенного скриншота)."""
    repo = PaymentRepository(session)
    payment = await repo.latest_open_for_user(db_user.id)
    if payment is not None:
        full = await repo.get_by_id_with_relations(payment.id)
        # Удаляем только заявки без приложенного подтверждения: если скриншот
        # уже отправлен, заявка ушла на проверку администратору.
        if full is not None and not full.attachments:
            logger.info(
                "Пользователь tg=%s отменил заявку %s",
                db_user.telegram_id,
                full.payment_code,
            )
            await repo.delete(full)
            await session.commit()
    await state.clear()


async def _activate_trial(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
) -> None:
    logger.info(
        "Пользователь tg=%s (id=%s) запросил пробный период через меню",
        db_user.telegram_id,
        db_user.id,
    )
    result = await billing.grant_trial(
        session,
        user_id=db_user.id,
        updater=build_updater(timeout=float(settings.xui_request_timeout)),
        period_days=settings.trial_period_days,
    )
    if result.already_used:
        text = texts.trial_already_used()
    elif result.no_client:
        text = texts.trial_no_client()
    elif not result.applied:
        text = texts.trial_failed()
    else:
        client = await VpnClientRepository(session).get_for_user(db_user.id)
        text = texts.trial_granted(client, settings.trial_period_days)
    await _edit(callback, text, keyboards.back_keyboard("home"))
    await callback.answer()


async def _attach_and_notify(
    message: Message,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
    state: FSMContext,
    file_type: AttachmentType,
    telegram_file_id: str | None,
    caption: str | None,
) -> None:
    payment = await PaymentRepository(session).latest_open_for_user(db_user.id)
    if payment is None:
        await message.answer(texts.no_open_request())
        return

    await payments.attach_proof(
        session,
        payment_id=payment.id,
        file_type=file_type,
        telegram_file_id=telegram_file_id,
        caption=caption,
    )

    # Карточку заявки с кнопками отправляем при каждом подтверждении оплаты,
    # затем пересылаем само подтверждение (чек/скриншот/сообщение).
    await notify.notify_admins_new_request(
        message.bot, settings, payment, db_user
    )
    await notify.forward_proof_to_admins(
        message.bot,
        settings,
        payment,
        file_type=file_type.value,
        telegram_file_id=telegram_file_id,
        caption=caption,
    )
    await message.answer(
        texts.proof_received(payment.payment_code), parse_mode="HTML"
    )
    await state.clear()


@router.message(F.photo)
async def proof_photo(
    message: Message,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
    state: FSMContext,
) -> None:
    file_id = message.photo[-1].file_id
    await _attach_and_notify(
        message, session, db_user, settings, state,
        AttachmentType.PHOTO, file_id, message.caption,
    )


@router.message(F.document)
async def proof_document(
    message: Message,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
    state: FSMContext,
) -> None:
    file_id = message.document.file_id
    await _attach_and_notify(
        message, session, db_user, settings, state,
        AttachmentType.DOCUMENT, file_id, message.caption,
    )


@router.message(ProofStates.waiting_proof, F.text)
async def proof_text(
    message: Message,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
    state: FSMContext,
) -> None:
    await _attach_and_notify(
        message, session, db_user, settings, state,
        AttachmentType.TEXT, None, message.text,
    )

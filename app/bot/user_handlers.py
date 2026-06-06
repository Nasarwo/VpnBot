from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import keyboards, notify, texts
from app.bot.callbacks import PlanCallback
from app.bot.states import ProofStates
from app.config import Settings
from app.db.enums import AttachmentType
from app.db.models import User
from app.db.repositories import PaymentRepository, VpnClientRepository
from app.services import billing, payments, plans, subscriptions
from app.services.xui_updater import build_updater

router = Router(name="user")


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: User) -> None:
    await message.answer(
        texts.welcome(db_user), reply_markup=keyboards.main_menu()
    )


@router.message(F.text == texts.BTN_MY_ACCESS)
async def show_access(message: Message, session: AsyncSession, db_user: User) -> None:
    client = await VpnClientRepository(session).get_for_user(db_user.id)
    await message.answer(texts.access_status(client, db_user.public_id))


@router.message(F.text == texts.BTN_MY_LINKS)
async def show_links(message: Message, session: AsyncSession, db_user: User) -> None:
    client = await VpnClientRepository(session).get_for_user(db_user.id)
    links = await subscriptions.collect_links(session, client, db_user.public_id)
    await message.answer(texts.links_message(links))


@router.message(F.text == texts.BTN_SUPPORT)
async def show_support(message: Message, settings: Settings, db_user: User) -> None:
    await message.answer(
        texts.support_message(settings.support_contact, db_user.public_id)
    )


@router.message(F.text == texts.BTN_EXTEND)
async def extend(message: Message) -> None:
    await message.answer(texts.choose_plan(), reply_markup=keyboards.plans_keyboard())


@router.message(F.text == texts.BTN_TRIAL)
async def trial(
    message: Message,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
) -> None:
    result = await billing.grant_trial(
        session,
        user_id=db_user.id,
        updater=build_updater(timeout=float(settings.xui_request_timeout)),
        period_days=settings.trial_period_days,
    )
    if result.already_used:
        await message.answer(texts.trial_already_used())
        return
    if result.no_client:
        await message.answer(texts.trial_no_client())
        return
    if not result.applied:
        await message.answer(texts.trial_failed())
        return

    client = await VpnClientRepository(session).get_for_user(db_user.id)
    await message.answer(texts.trial_granted(client, settings.trial_period_days))


@router.callback_query(PlanCallback.filter())
async def select_plan(
    callback: CallbackQuery,
    callback_data: PlanCallback,
    session: AsyncSession,
    db_user: User,
    settings: Settings,
    state: FSMContext,
) -> None:
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
    await callback.message.answer(
        texts.payment_created(payment, settings.payment_details_text)
    )
    # Админа уведомляем только после того, как пользователь пришлёт подтверждение оплаты.
    await state.set_state(ProofStates.waiting_proof)
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
    await message.answer(texts.proof_received(payment.payment_code))
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

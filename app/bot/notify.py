from __future__ import annotations

import logging
from html import escape

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.bot import keyboards, texts
from app.config import Settings
from app.db.models import BindRequest, PaymentRequest, User, VpnClient

logger = logging.getLogger(__name__)


async def notify_admins_new_request(
    bot: Bot, settings: Settings, payment: PaymentRequest, user: User
) -> None:
    card = texts.admin_payment_card(payment, user)
    keyboard = keyboards.admin_payment_keyboard(payment.id)
    for admin_id in settings.admin_telegram_ids:
        try:
            await bot.send_message(
                admin_id, card, reply_markup=keyboard, parse_mode="HTML"
            )
        except TelegramAPIError:
            logger.warning("Не удалось отправить заявку админу %s", admin_id)


async def forward_proof_to_admins(
    bot: Bot,
    settings: Settings,
    payment: PaymentRequest,
    file_type: str,
    telegram_file_id: str | None,
    caption: str | None,
) -> None:
    header = f"Подтверждение по заявке <code>{escape(payment.payment_code)}</code>"
    for admin_id in settings.admin_telegram_ids:
        try:
            if file_type == "photo" and telegram_file_id:
                await bot.send_photo(
                    admin_id, telegram_file_id, caption=header, parse_mode="HTML"
                )
            elif file_type == "document" and telegram_file_id:
                await bot.send_document(
                    admin_id, telegram_file_id, caption=header, parse_mode="HTML"
                )
            else:
                body = f"{header}\n\n{escape(caption or '')}".strip()
                await bot.send_message(admin_id, body, parse_mode="HTML")
        except TelegramAPIError:
            logger.warning("Не удалось переслать подтверждение админу %s", admin_id)


async def notify_user_extended(
    bot: Bot, telegram_id: int, client: VpnClient
) -> None:
    try:
        await bot.send_message(
            telegram_id, texts.access_extended(client), parse_mode="HTML"
        )
    except TelegramAPIError:
        logger.warning("Не удалось уведомить пользователя %s", telegram_id)


async def notify_user_expiry(
    bot: Bot, telegram_id: int, stage: int, expires_at: object
) -> bool:
    """Уведомление пользователя об окончании подписки. True — если доставлено."""
    try:
        await bot.send_message(
            telegram_id, texts.expiry_notice(stage, expires_at), parse_mode="HTML"
        )
        return True
    except TelegramAPIError:
        logger.warning(
            "Не удалось отправить уведомление об окончании пользователю %s",
            telegram_id,
        )
        return False


async def notify_admins_new_bind_request(
    bot: Bot, settings: Settings, req: BindRequest, user: User
) -> None:
    card = texts.admin_bind_card(req, user)
    keyboard = keyboards.admin_bind_keyboard(req.id)
    for admin_id in settings.admin_telegram_ids:
        try:
            await bot.send_message(
                admin_id, card, reply_markup=keyboard, parse_mode="HTML"
            )
        except TelegramAPIError:
            logger.warning("Не удалось отправить заявку на привязку админу %s", admin_id)


async def notify_user_bind_approved(
    bot: Bot, telegram_id: int, public_id: str
) -> None:
    try:
        await bot.send_message(
            telegram_id, texts.bind_request_approved(public_id), parse_mode="HTML"
        )
    except TelegramAPIError:
        logger.warning("Не удалось уведомить пользователя %s о привязке", telegram_id)


async def notify_user_bind_rejected(
    bot: Bot, telegram_id: int, request_code: str
) -> None:
    try:
        await bot.send_message(
            telegram_id, texts.bind_request_rejected(request_code), parse_mode="HTML"
        )
    except TelegramAPIError:
        logger.warning("Не удалось уведомить пользователя %s", telegram_id)


async def notify_admins_bind_failed(
    bot: Bot, settings: Settings, req: BindRequest, user: User
) -> None:
    card = texts.admin_bind_card(req, user)
    if req.last_error:
        card += f"\n\nОшибка: {escape(req.last_error)}"
    keyboard = keyboards.admin_bind_retry_keyboard(req.id)
    for admin_id in settings.admin_telegram_ids:
        try:
            await bot.send_message(
                admin_id,
                f"Не удалось привязать подписку.\n\n{card}",
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except TelegramAPIError:
            logger.warning("Не удалось уведомить админа %s об ошибке привязки", admin_id)


async def notify_user_rejected(
    bot: Bot, telegram_id: int, payment_code: str
) -> None:
    try:
        await bot.send_message(
            telegram_id, texts.payment_rejected(payment_code), parse_mode="HTML"
        )
    except TelegramAPIError:
        logger.warning("Не удалось уведомить пользователя %s", telegram_id)


async def notify_admins_failed(
    bot: Bot, settings: Settings, payment: PaymentRequest, user: User
) -> None:
    card = texts.admin_payment_card(payment, user)
    keyboard = keyboards.admin_retry_keyboard(payment.id)
    for admin_id in settings.admin_telegram_ids:
        try:
            await bot.send_message(
                admin_id,
                f"Не удалось применить продление.\n\n{card}",
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except TelegramAPIError:
            logger.warning("Не удалось уведомить админа %s об ошибке", admin_id)

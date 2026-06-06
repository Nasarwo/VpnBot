from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.bot import keyboards, texts
from app.config import Settings
from app.db.models import PaymentRequest, User, VpnClient

logger = logging.getLogger(__name__)


async def notify_admins_new_request(
    bot: Bot, settings: Settings, payment: PaymentRequest, user: User
) -> None:
    card = texts.admin_payment_card(payment, user)
    keyboard = keyboards.admin_payment_keyboard(payment.id)
    for admin_id in settings.admin_telegram_ids:
        try:
            await bot.send_message(admin_id, card, reply_markup=keyboard)
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
    header = f"Подтверждение по заявке {payment.payment_code}"
    for admin_id in settings.admin_telegram_ids:
        try:
            if file_type == "photo" and telegram_file_id:
                await bot.send_photo(admin_id, telegram_file_id, caption=header)
            elif file_type == "document" and telegram_file_id:
                await bot.send_document(admin_id, telegram_file_id, caption=header)
            else:
                body = f"{header}\n\n{caption or ''}".strip()
                await bot.send_message(admin_id, body)
        except TelegramAPIError:
            logger.warning("Не удалось переслать подтверждение админу %s", admin_id)


async def notify_user_extended(
    bot: Bot, telegram_id: int, client: VpnClient
) -> None:
    try:
        await bot.send_message(telegram_id, texts.access_extended(client))
    except TelegramAPIError:
        logger.warning("Не удалось уведомить пользователя %s", telegram_id)


async def notify_user_rejected(
    bot: Bot, telegram_id: int, payment_code: str
) -> None:
    try:
        await bot.send_message(telegram_id, texts.payment_rejected(payment_code))
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
            )
        except TelegramAPIError:
            logger.warning("Не удалось уведомить админа %s об ошибке", admin_id)

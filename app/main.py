from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.token import TokenValidationError, validate_token

from app.bot.middlewares import DbSessionMiddleware
from app.bot.router import build_root_router
from app.config import Settings, get_settings
from app.db.session import get_sessionmaker
from app.services import antishare
from app.services.ip_provider import build_ip_provider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _token_diagnostics(token: str) -> str:
    """Безопасное описание проблемы с токеном без раскрытия секрета.

    Часть до ':' (числовой ID бота) не является секретом и показывается,
    секретная часть после ':' маскируется.
    """
    has_whitespace = any(ch.isspace() for ch in token)
    left, sep, right = token.partition(":")
    left_is_digits = left.isdigit()
    masked_right = f"{len(right)} симв." if right else "пусто"
    bot_id = left if left_is_digits else f"<не цифры: {left!r}>"
    return (
        f"длина={len(token)}, есть_двоеточие={bool(sep)}, "
        f"пробелы_внутри={has_whitespace}, id_бота={bot_id}, "
        f"секретная_часть={masked_right}"
    )


async def _anti_sharing_poller(settings: Settings) -> None:
    """Фоновый периодический сбор IP-наблюдений из 3x-ui."""
    interval = settings.anti_sharing_poll_minutes * 60
    provider = build_ip_provider(timeout=float(settings.xui_request_timeout))
    sessionmaker = get_sessionmaker()
    while True:
        await asyncio.sleep(interval)
        try:
            async with sessionmaker() as session:
                added = await antishare.collect_all(session, provider)
            logger.info("Антишеринг: собрано наблюдений: %s", added)
        except Exception:  # noqa: BLE001 - фоновая задача не должна падать
            logger.exception("Ошибка фонового сбора IP")


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    # Outer middleware: данные (session, db_user) должны быть доступны фильтрам
    # (например IsAdmin) ещё до выбора обработчика.
    dp.message.outer_middleware(DbSessionMiddleware())
    dp.callback_query.outer_middleware(DbSessionMiddleware())
    dp.include_router(build_root_router())
    return dp


async def run() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise SystemExit(
            "BOT_TOKEN не задан. Укажите токен бота от @BotFather в .env "
            "(переменная BOT_TOKEN) и пересоберите контейнер."
        )
    try:
        validate_token(settings.bot_token)
    except TokenValidationError:
        raise SystemExit(
            "BOT_TOKEN имеет неверный формат. Ожидается значение вида "
            "123456789:AA... без кавычек и пробелов.\n"
            f"Диагностика: {_token_diagnostics(settings.bot_token)}\n"
            "Проверьте .env (частые причины: CRLF/пробел внутри значения, "
            "лишний текст или незаполненный токен)."
        ) from None

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=None),
    )
    dp = build_dispatcher()

    logger.info("Бот запускается (admins=%s)", settings.admin_telegram_ids)

    poller_task: asyncio.Task | None = None
    if settings.anti_sharing_enabled and settings.anti_sharing_poll_minutes > 0:
        poller_task = asyncio.create_task(_anti_sharing_poller(settings))
        logger.info(
            "Антишеринг-мониторинг включён, период сбора: %s мин",
            settings.anti_sharing_poll_minutes,
        )

    try:
        await dp.start_polling(bot)
    finally:
        if poller_task is not None:
            poller_task.cancel()
        await bot.session.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

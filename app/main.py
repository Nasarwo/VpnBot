from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, ErrorEvent, MenuButtonCommands
from aiogram.utils.token import TokenValidationError, validate_token

from app.bot.middlewares import DbSessionMiddleware
from app.bot.router import build_root_router
from app.config import Settings, get_settings
from app.db.session import get_sessionmaker
from app.logging_config import setup_logging
from app.services import antishare, billing, expiry, health, whitelist
from app.services.ip_provider import build_ip_provider
from app.services.subhub_client import trigger_configured_sync
from app.services.web_bridge import delivery_loop, start_bridge
from app.services.xui_updater import build_updater

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


async def _subhub_sync(settings: Settings, reason: str) -> bool:
    """Best-effort запрос SubHub перечитать панели после фоновых изменений."""
    logger.info("SubHub: запрос синхронизации после фоновых изменений (%s)", reason)
    return await trigger_configured_sync(
        settings.subhub_url,
        settings.subhub_admin_token,
        timeout=settings.subhub_timeout_seconds,
    )


async def _server_health_poller(settings: Settings) -> None:
    """Фоновая периодическая проверка доступности серверов 3x-ui.

    Очередь применения whitelist-квот здесь не обслуживается: её ведёт
    ``_whitelist_queue_worker``, который работает и при отключённой проверке.
    """
    interval = settings.server_health_poll_seconds
    timeout = min(float(settings.xui_request_timeout), 10.0)
    updater = build_updater(timeout=float(settings.xui_request_timeout))
    sessionmaker = get_sessionmaker()

    async def subhub_sync(reason: str) -> bool:
        return await _subhub_sync(settings, reason)

    async def pending_applied() -> bool:
        return await subhub_sync("отложенные обновления серверов")

    while True:
        try:
            async with sessionmaker() as session:
                # Возобновлённая после рестарта оплата меняет панели так же, как
                # подтверждение администратором, — SubHub должен их перечитать.
                if await billing.recover_confirmed_payments(session, updater):
                    await subhub_sync("возобновлены оплаты")
                await health.check_servers(
                    session,
                    timeout=timeout,
                    updater=updater,
                    on_updates_applied=pending_applied,
                )
        except Exception:  # noqa: BLE001 - фоновая задача не должна падать
            logger.exception("Ошибка фоновой проверки серверов")
        await asyncio.sleep(interval)


async def _whitelist_queue_worker(settings: Settings) -> None:
    """Очередь применения квот «Обхода белых списков» на панели.

    Единственный обработчик ``whitelist.process_due`` в процессе. Не зависит от
    ``SERVER_HEALTH_POLL_SECONDS`` и сверки расхода: покупка, сохранённая при
    недоступной панели, применяется после её восстановления без команд
    администратора. Повторы по аккаунту, сериализацию по пользователю и
    идемпотентность обеспечивает сама очередь; здесь — только периодический
    запуск и уведомление SubHub после успешного применения.
    """
    interval = settings.whitelist_queue_poll_seconds
    updater = build_updater(timeout=float(settings.xui_request_timeout))
    sessionmaker = get_sessionmaker()
    while True:
        try:
            async with sessionmaker() as session:
                applied = await whitelist.process_due(session, updater)
            if applied:
                await _subhub_sync(settings, "очередь «Обход белых списков»")
        except Exception:  # noqa: BLE001 - фоновая задача не должна падать
            logger.exception("Ошибка фоновой синхронизации «Обход белых списков»")
        await asyncio.sleep(interval)


async def _whitelist_reconcile_poller(settings: Settings) -> None:
    """Фоновая сверка расхода whitelist-услуги: полный обход пачками.

    Работает отдельно от проверки серверов: длительный обход не задерживает
    очередь применения квот. Период — пауза между обходами, а не гарантированное
    время сверки: обход идёт столько, сколько нужно пачкам и паузам.
    """
    interval = settings.whitelist_reconcile_minutes * 60
    updater = build_updater(timeout=float(settings.xui_request_timeout))
    sessionmaker = get_sessionmaker()
    loop = asyncio.get_running_loop()
    while True:
        started = loop.time()
        complete = False
        try:
            async with sessionmaker() as session:
                report = await whitelist.reconcile_cycle(
                    session,
                    updater,
                    batch_size=settings.whitelist_reconcile_batch_size,
                    pause_seconds=settings.whitelist_reconcile_batch_pause_seconds,
                    status=whitelist.RECONCILE_STATUS,
                )
            complete = report.complete
        except Exception as exc:  # noqa: BLE001 - фоновая задача не должна падать
            whitelist.RECONCILE_STATUS.last_run_note = f"ошибка: {type(exc).__name__}"
            logger.exception("Ошибка фоновой сверки расхода «Обход белых списков»")
        await asyncio.sleep(
            whitelist.next_reconcile_delay(
                interval, loop.time() - started, complete=complete
            )
        )


async def _expiry_notify_poller(bot: Bot, settings: Settings) -> None:
    """Фоновая рассылка уведомлений об окончании подписки (день/час/в момент)."""
    interval = settings.expiry_notify_poll_seconds
    sessionmaker = get_sessionmaker()
    while True:
        try:
            async with sessionmaker() as session:
                await expiry.process_expiry_notifications(session, bot)
        except Exception:  # noqa: BLE001 - фоновая задача не должна падать
            logger.exception("Ошибка фоновых уведомлений об окончании подписки")
        await asyncio.sleep(interval)


# Задачи worker'а очереди этого процесса: защита от второго запуска.
_QUEUE_WORKER_TASKS: set[asyncio.Task] = set()


def _queue_worker_alive() -> bool:
    return any(not task.done() for task in _QUEUE_WORKER_TASKS)


def start_background_tasks(bot: Bot, settings: Settings) -> list[asyncio.Task]:
    """Запускает фоновые циклы процесса бота (кроме доставки сайта).

    Одна сборка для обычного запуска рядом с Telegram polling и для
    изолированной приёмки без polling: те же функции, настройки и условия
    включения. ``bot`` нужен только уведомлениям об окончании подписки.
    """
    tasks: list[asyncio.Task] = []
    if settings.anti_sharing_enabled and settings.anti_sharing_poll_minutes > 0:
        tasks.append(asyncio.create_task(_anti_sharing_poller(settings)))
        logger.info(
            "Антишеринг-мониторинг включён, период сбора: %s мин",
            settings.anti_sharing_poll_minutes,
        )
    # Один worker очереди на процесс, независимо от проверки серверов и сверки.
    if _queue_worker_alive():
        logger.warning("Очередь «Обход белых списков» уже обслуживается в этом процессе")
    else:
        worker = asyncio.create_task(_whitelist_queue_worker(settings))
        _QUEUE_WORKER_TASKS.add(worker)
        worker.add_done_callback(_QUEUE_WORKER_TASKS.discard)
        tasks.append(worker)
        logger.info(
            "Очередь «Обход белых списков» включена, период опроса: %s c",
            settings.whitelist_queue_poll_seconds,
        )
    if settings.server_health_poll_seconds > 0:
        tasks.append(asyncio.create_task(_server_health_poller(settings)))
        logger.info(
            "Проверка доступности серверов включена, период: %s c",
            settings.server_health_poll_seconds,
        )
    if settings.whitelist_reconcile_minutes > 0:
        tasks.append(asyncio.create_task(_whitelist_reconcile_poller(settings)))
        logger.info(
            "Сверка расхода «Обход белых списков» включена: пауза между обходами "
            "%s мин, пачка %s, пауза между пачками %s c",
            settings.whitelist_reconcile_minutes,
            settings.whitelist_reconcile_batch_size,
            settings.whitelist_reconcile_batch_pause_seconds,
        )
    if settings.expiry_notify_poll_seconds > 0:
        tasks.append(asyncio.create_task(_expiry_notify_poller(bot, settings)))
        logger.info(
            "Уведомления об окончании подписки включены, период: %s c",
            settings.expiry_notify_poll_seconds,
        )
    return tasks


async def stop_background_tasks(tasks: list[asyncio.Task]) -> None:
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


async def _setup_menu_button(bot: Bot) -> None:
    """Включает кнопку «Меню» у поля ввода с командой /start (возврат в начало)."""
    try:
        await bot.set_my_commands(
            [BotCommand(command="start", description="Главное меню / в начало")]
        )
        await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    except Exception:  # noqa: BLE001 - не критично для запуска бота
        logger.exception("Не удалось настроить кнопку «Меню»")


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    # Outer middleware: данные (session, db_user) должны быть доступны фильтрам
    # (например IsAdmin) ещё до выбора обработчика.
    dp.message.outer_middleware(DbSessionMiddleware())
    dp.callback_query.outer_middleware(DbSessionMiddleware())
    dp.include_router(build_root_router())

    @dp.errors()
    async def _on_error(event: ErrorEvent) -> bool:
        logger.exception(
            "Необработанная ошибка при обработке апдейта: %s", event.exception
        )
        return True

    return dp


async def run() -> None:
    settings = get_settings()
    setup_logging(level=settings.log_level, xui_debug=settings.xui_debug)
    logger.info(
        "Запуск: log_level=%s, xui_debug=%s, db=%s",
        settings.log_level,
        settings.xui_debug,
        settings.database_url.split("://", 1)[0],
    )
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

    async with get_sessionmaker()() as session:
        # Идемпотентно: настройки и начальные пакеты услуги, если их нет.
        await whitelist.ensure_defaults(session)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=None),
    )
    dp = build_dispatcher()

    await _setup_menu_button(bot)

    logger.info("Бот запускается (admins=%s)", settings.admin_telegram_ids)

    background_tasks: list[asyncio.Task] = []
    web_runner = await start_bridge(bot, settings)
    if web_runner:
        background_tasks.append(asyncio.create_task(delivery_loop(bot)))
    background_tasks.extend(start_background_tasks(bot, settings))

    try:
        await dp.start_polling(bot)
    finally:
        await stop_background_tasks(background_tasks)
        if web_runner:
            await web_runner.cleanup()
        await bot.session.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

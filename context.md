# Контекст проекта

## Назначение

Проект `telegram-vpn-billing-bot` - Telegram-бот для продажи и сопровождения VPN-доступа через панели 3x-ui. Пользователь выбирает тариф или пробный доступ, отправляет подтверждение ручного перевода, администратор подтверждает заявку, после чего бот автоматически создает или продлевает клиента в 3x-ui.

Бот не принимает платежи через эквайринг. Вся логика оплаты построена вокруг ручной заявки, вложений с подтверждением и админского подтверждения.

## Технологии

- Python 3.12+
- aiogram 3
- SQLAlchemy 2 async + Alembic
- PostgreSQL в Docker/production, SQLite для локальной разработки и тестов
- httpx для REST-интеграции с 3x-ui
- pydantic-settings для `.env`
- pytest, pytest-asyncio, pytest-httpx
- ruff, mypy

## Запуск

Локально:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
python -m app.main
```

Docker Compose:

```powershell
docker compose up -d --build
```

Контейнер `bot` получает `DATABASE_URL` на PostgreSQL из `docker-compose.yml`; локально по умолчанию используется `sqlite+aiosqlite:///./vpnbot.sqlite3`.

## Конфигурация

Основной конфиг описан в `app/config.py` и читается из `.env`.

Ключевые переменные:

- `BOT_TOKEN` - токен Telegram-бота.
- `ADMIN_TELEGRAM_IDS` - Telegram ID администраторов через запятую.
- `DATABASE_URL` - async SQLAlchemy URL.
- `SECRET_KEY` - ключ для шифрования секретов в БД, прежде всего паролей серверов 3x-ui.
- `PAYMENT_AMOUNT_RUB`, `PAYMENT_PERIOD_DAYS`, `TRIAL_PERIOD_DAYS` - дефолтные параметры оплаты и trial.
- `PAYMENT_DETAILS_TEXT` - реквизиты ручного перевода.
- `SUPPORT_CONTACT` - контакт поддержки.
- `XUI_REQUEST_TIMEOUT` - timeout запросов к 3x-ui.
- `SERVER_HEALTH_POLL_SECONDS` - фоновая проверка доступности панелей.
- `EXPIRY_NOTIFY_POLL_SECONDS` - уведомления об истечении подписки.
- `ANTI_SHARING_*` - настройки мягкого антишеринга по IP-наблюдениям.
- `LOG_LEVEL`, `XUI_DEBUG` - логирование.

## Структура

```text
app/
  main.py                точка входа, polling, фоновые задачи
  config.py              pydantic-settings
  logging_config.py      настройка логов
  crypto.py              Fernet-шифрование секретов
  bot/
    router.py            сборка root router
    user_handlers.py     пользовательский flow
    admin_handlers.py    админский flow и команды
    keyboards.py         inline-клавиатуры
    callbacks.py         CallbackData
    texts.py             тексты сообщений
    middlewares.py       DB session и получение/создание пользователя
    filters.py           IsAdmin
    notify.py            уведомления пользователям и админам
    states.py            FSM-состояния
  db/
    models.py            ORM-модели
    repositories.py      слой доступа к данным
    enums.py             enum-статусы и протоколы
    session.py           async engine/sessionmaker
    types.py             EncryptedString
  services/
    billing.py           подтверждение оплат, trial, ручное продление
    payments.py          создание заявок и вложений
    provisioning.py      создание/синхронизация клиентов в 3x-ui
    xui_client.py        низкоуровневый REST-клиент 3x-ui
    xui_updater.py       реализация PanelUpdater через XuiClient
    panel_updater.py     интерфейс PanelUpdater и mock для тестов
    bind_requests.py     привязка legacy-подписок
    subscriptions.py     ссылки подписки
    subscription_delete.py удаление подписки
    antishare.py         IP-наблюдения и уровни риска
    health.py            проверка доступности серверов
    expiry.py            уведомления об истечении
    broadcast.py         рассылки
    access.py            вычисление эффективного доступа/роли
  migrations/            Alembic
tests/                   unit/integration tests на SQLite и mock/httpx
```

## Доменная модель

Главные таблицы из `app/db/models.py`:

- `users` - Telegram-пользователи, роль, `public_id`, флаг использованного trial и onboarding.
- `vpn_clients` - один VPN-клиент на пользователя, срок доступа, активность, внешний секрет клиента.
- `servers` - панели 3x-ui: URL, логин, зашифрованный пароль, тип сервера, база subscription URL, health status.
- `server_inbounds` - inbound'ы конкретного сервера, куда нужно добавлять клиентов.
- `client_server_mappings` - локальная привязка VPN-клиента к серверу/inbound/client id/email/sub_id.
- `payment_requests` и `payment_attachments` - ручные платежные заявки и подтверждения.
- `bind_requests` - заявки на привязку уже существующей подписки из 3x-ui.
- `ip_observations` - IP-наблюдения для антишеринга.
- `pending_server_updates` - отложенные продления для серверов, которые не удалось обновить при подтверждении платежа.
- `audit_logs` - аудит действий.

Статусы:

- `PaymentStatus`: `created`, `waiting_admin`, `confirmed`, `rejected`, `applied`, `failed`.
- `BindRequestStatus`: `waiting_admin`, `approved`, `rejected`, `failed`.
- `Protocol`: `vmess`, `vless`, `trojan`, `shadowsocks`, `hysteria2`.

## Основные пользовательские сценарии

1. `/start` создает или обновляет пользователя через middleware/repository и присваивает короткий `public_id`.
2. Если пользователь новый, onboarding спрашивает, был ли он клиентом до бота.
3. Новый пользователь может выбрать тариф или trial.
4. При выборе тарифа создается или переиспользуется открытая `PaymentRequest`.
5. Пользователь присылает текст/фото/документ как подтверждение оплаты.
6. Администраторы получают карточку заявки и подтверждают или отклоняют ее.
7. При подтверждении `billing.confirm_payment` фиксирует целевой срок, вызывает provisioning/update панелей и переводит заявку в `applied`.
   Если часть серверов недоступна, доступ продлевается локально и на доступных серверах, а недоступные серверы попадают в `pending_server_updates`.
8. Пользователь получает уведомление и ссылки подключения.

Trial выдается один раз на аккаунт (`User.trial_used`) и не должен расходоваться при ошибке применения к панелям.

## Provisioning в 3x-ui

Сервис `app/services/provisioning.py` отвечает за создание и синхронизацию клиентов:

- `ensure_vpn_client` создает локальный `VpnClient` с UUID-секретом.
- `apply_access` создает или обновляет клиента на всех включенных серверах и включенных inbound'ах.
- `import_inbounds` подтягивает inbound'ы из панели в `server_inbounds`.
- `bind_user_by_public_id` и `bind_existing_client` привязывают существующего клиента панели к пользователю бота.

Для 3x-ui >= 3.2.x используется новый глобальный clients API: один клиент панели с `email/subId = public_id`, привязанный к нескольким inbound'ам. Для старых панелей есть legacy fallback через per-inbound `addClient/updateClient`, где email формируется с суффиксом inbound.

Поддерживаемые протоколы для client payload: `vless`, `vmess`, `trojan`, `shadowsocks`, `hysteria2`.

## Интеграция с 3x-ui

`app/services/xui_client.py`:

- логинится через `/login`;
- поддерживает CSRF `/csrf-token` для новых 3x-ui;
- поддерживает Bearer API token на уровне конструктора, хотя текущий `Server` хранит username/password;
- делает retry для network/timeout и HTTP 502/503/504;
- при 401/403 или redirect на login повторяет login один раз;
- не логирует пароль, cookie и CSRF token;
- умеет list/get inbound, add/update/delete client, global client API, traffic и IP list.

`app/services/xui_updater.py` адаптирует этот клиент к протоколу `PanelUpdater`.

## Админские команды

Команды из `app/bot/admin_handlers.py`:

- `/admin` - админская панель.
- `/pending` - ожидающие заявки.
- `/confirm <id>`, `/reject <id>` - подтверждение/отклонение платежа.
- `/confirmbind <id>`, `/rejectbind <id>` - обработка legacy bind-заявок.
- `/sharing`, `/ipscan` - антишеринг-отчеты и сбор IP.
- `/servers` - список серверов.
- `/renameserver <server_id> <новое название>` - переименовать сервер без удаления.
- `/setsubscriptionurl <server_id> <URL или ->` - изменить или удалить URL подписки.
- `/addserver name|country|panel_url|username|password|[kind]|[subscription_base]` - добавить сервер.
- `/addinbound <server_id> <inbound_id> <protocol> [flow] [method]` - добавить inbound вручную.
- `/delinbound`, `/clearinbounds` - удалить inbound'ы из локальной конфигурации.
- `/inbounds <server_id>`, `/importinbounds <server_id>` - посмотреть/импортировать inbound'ы панели.
- `/provision <telegram_id>` - вручную применить доступ пользователю.
- `/panelclients <server_id>` - посмотреть клиентов панели.
- `/bind <server_id> <email> <telegram_id>` - привязать существующего клиента панели.
- `/active`, `/expired` - списки клиентов.
- `/extend <vpn_client_id> [days]` - ручное продление.
- `/sync <vpn_client_id>` - повторно выставить текущий срок на панелях.

Также админка доступна через inline-кнопки и callback'и.

## Фоновые задачи

Запускаются в `app/main.py`:

- health poller проверяет панели через `health.check_servers`;
- при успешном health-check серверов применяются pending-продления для восстановившихся серверов;
- expiry poller отправляет уведомления за день, за час и при истечении;
- anti-sharing poller собирает IP-наблюдения из 3x-ui.

Все фоновые задачи логируют исключения и не должны падать вместе с polling.

## Антишеринг

`app/services/antishare.py` хранит IP-наблюдения за окна `15m`, `1h`, `24h`, `7d`.

Уровни:

- `ok` - в пределах лимитов;
- `warn` - превышен `DEFAULT_IP_LIMIT` за час или `WARN_THRESHOLD_24H` за сутки;
- `critical` - достигнут `CRITICAL_THRESHOLD_24H`.

Сейчас режим мягкий: мониторинг и отчеты, без обязательной автоблокировки.

## Тарифы

В `app/services/plans.py`:

- `1m` - 30 дней, 175 RUB.
- `6m` - 180 дней, 850 RUB.
- `12m` - 360 дней, 1600 RUB.

Базовая месячная цена для расчета выгоды: 175 RUB.

## Тесты

Тесты находятся в `tests/`. Основные зоны покрытия:

- billing, idempotency, retry failed payments;
- provisioning, bind legacy clients, payloads для разных протоколов;
- XuiClient через pytest-httpx;
- безопасность: экранирование HTML, отсутствие утечек пароля в ошибках, public_id uniqueness;
- permissions/admin filter;
- UI-клавиатуры и UX-тексты;
- trial, expiry notifications, anti-sharing;
- deletion/reset subscription/user.

Запуск:

```powershell
pytest
ruff check .
mypy app
```

## Важные инженерные правила проекта

- Не хранить и не логировать секреты панелей в открытом виде. `Server.password` использует `EncryptedString`.
- `SECRET_KEY` нельзя менять после появления зашифрованных паролей в БД.
- Подтверждение оплаты должно быть идемпотентным: повторный confirm не продлевает второй раз.
- Перед внешними вызовами к панелям платеж фиксирует `target_expires_at`, чтобы retry применял тот же срок.
- Частичные сбои панелей не блокируют продление: failed-серверы ставятся в `pending_server_updates` и догоняются health-check'ом.
- При работе с 3x-ui предпочтительно read-modify-write, чтобы не терять поля клиента.
- Provisioning должен учитывать и новый global clients API, и legacy per-inbound API.
- Trial нельзя считать использованным, если панели не обновились.
- В async SQLAlchemy аккуратно грузить связи через `selectinload`, особенно перед cascade delete.
- Тексты Telegram часто используют HTML parse mode, поэтому пользовательские значения нужно экранировать.

## Локальные артефакты

В корне есть рабочие/локальные файлы, которые не выглядят частью основного приложения: `vpnbot.sqlite3`, `list.json`, `page.html`, `page2.html`, `panel_login.html`, `cj*.txt`, `hs_err_pid*.log`, кэши и `.venv`. При изменениях проекта не стоит трогать их без отдельной причины.

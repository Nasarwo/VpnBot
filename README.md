# Telegram VPN Billing Bot

Telegram-бот для управления подписками на личный сетевой доступ с ручным подтверждением
оплат и автоматическим продлением доступа в панелях 3x-ui.

Бот не принимает платежи через эквайринг. Пользователь создаёт заявку на продление,
переводит деньги вручную по реквизитам и отправляет подтверждение (текст, фото или
документ). Администратор подтверждает оплату одной кнопкой, после чего бот автоматически
продлевает срок доступа во всех связанных панелях 3x-ui и присылает пользователю
актуальные ссылки подключения.

## Возможности

Каждому пользователю при первом обращении присваивается публичный ID (8 символов).
Он показывается пользователю (в приветствии, разделах «Мой доступ» и «Поддержка») и
администратору (в карточке заявки и профиле). Этот ID удобно использовать как
идентификатор клиента (email/sub_id) при заведении inbound и подписки в 3x-ui.

Пользователь:
- запуск бота `/start`;
- просмотр текущего срока доступа («Мой доступ»);
- бесплатный пробный период на 2 дня — один раз на аккаунт («Пробные 2 дня»);
- создание заявки на продление с выбором тарифа («Продлить»):
  - 1 месяц — 175 ₽;
  - 6 месяцев — 850 ₽ (выгода 200 ₽);
  - 1 год — 1600 ₽ (выгода 500 ₽);
- получение реквизитов для ручного перевода;
- отправка подтверждения оплаты: текст, фото или документ;
- получение уведомления после подтверждения;
- получение ссылок подключения («Мои ссылки»);
- обращение в поддержку.

Администратор:
- уведомления о новых заявках с карточкой заявки;
- кнопки «Подтвердить» / «Отклонить» / «История» / «Профиль»;
- идемпотентное подтверждение (повторный клик не продлевает доступ второй раз);
- кнопка «Повторить применение», если часть панелей 3x-ui временно недоступна;
- списки активных и истёкших клиентов (`/active`, `/expired`);
- ручное продление клиента (`/extend <telegram_id> [дней]`);
- синхронизация срока с панелями (`/sync <telegram_id>`).

## Технологический стек

- Python 3.12+
- aiogram 3
- SQLAlchemy 2 (async) + Alembic
- PostgreSQL (production) / SQLite (local/dev)
- httpx (интеграция с 3x-ui)
- pydantic-settings
- pytest, pytest-asyncio, pytest-httpx
- ruff, mypy
- Docker Compose

## Структура проекта

```text
app/
  main.py              точка входа (polling)
  config.py            конфигурация через .env (pydantic-settings)
  bot/
    router.py          сборка роутеров
    keyboards.py       клавиатуры (меню, админские кнопки)
    callbacks.py       CallbackData админских действий
    texts.py           нейтральные тексты сообщений
    states.py          FSM-состояния
    filters.py         фильтр прав (IsAdmin)
    middlewares.py     сессия БД + получение/создание пользователя
    notify.py          уведомления админам и пользователям
    user_handlers.py   пользовательский flow
    admin_handlers.py  админский flow
  db/
    base.py            DeclarativeBase + миксины
    enums.py           перечисления (роли, статусы, протоколы)
    models.py          ORM-модели
    repositories.py    доступ к данным
    session.py         async engine / sessionmaker
  services/
    billing.py         продление, идемпотентность, расчёт срока
    payments.py        заявки и вложения
    subscriptions.py   формирование ссылок подключения
    xui_client.py      изолированный клиент 3x-ui
    xui_updater.py     PanelUpdater поверх XuiClient
    panel_updater.py   интерфейс обновления панелей + mock
    audit.py           запись в audit_logs
  migrations/          Alembic
tests/                 тесты бизнес-логики и XuiClient
docker-compose.yml
Dockerfile
pyproject.toml
.env.example
```

## Конфигурация

Скопируйте `.env.example` в `.env` и заполните значения:

```env
BOT_TOKEN=                # токен бота из @BotFather
ADMIN_TELEGRAM_IDS=       # ID администраторов через запятую: 111111111,222222222
DATABASE_URL=            # см. ниже
PAYMENT_AMOUNT_RUB=175
PAYMENT_PERIOD_DAYS=30
PAYMENT_DETAILS_TEXT=    # реквизиты для перевода (показываются пользователю)
SUPPORT_CONTACT=@support
XUI_REQUEST_TIMEOUT=15
```

`DATABASE_URL`:
- PostgreSQL: `postgresql+asyncpg://vpnbot:vpnbot@db:5432/vpnbot`
- SQLite (dev): `sqlite+aiosqlite:///./vpnbot.sqlite3`

Пароли панелей 3x-ui хранятся в таблице `servers` и никогда не логируются.

## Запуск через Docker Compose

```bash
cp .env.example .env   # заполните BOT_TOKEN и ADMIN_TELEGRAM_IDS
docker compose up -d --build
```

Контейнер `bot` при старте автоматически применяет миграции (`alembic upgrade head`)
и запускает бота. PostgreSQL поднимается в сервисе `db`.

## Локальный запуск (dev)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -e ".[dev]"

# по умолчанию используется SQLite
alembic upgrade head
python -m app.main
```

## Настройка серверов и авто-провижининг

Клиенты создаются автоматически на всех включённых серверах и во всех настроенных
inbound'ах при оплате или активации триала. Inbound'ы на панелях должны быть созданы
заранее — бот только добавляет в них клиентов (`addClient`) и продлевает срок
(`updateClient`).

### Шаг 1. Добавить серверы

Командой администратора:

```text
/addserver name|country|panel_url|username|password|[kind]|[subscription_base]
/addserver Германия|DE|https://de.example:2053|admin|pass|direct|https://de.example:2096/sub/
/addserver Россия|RU|https://ru.example:2053|admin|pass|ru_proxy|https://ru.example:2096/sub/
```

- `kind` — метка типа: `direct` (зарубежный exit) или `ru_proxy` (RU-вход). По умолчанию `direct`.
- `subscription_base` — базовый URL встроенной подписки 3x-ui; полная ссылка = `base + public_id`.

### Шаг 2. Импортировать inbound'ы каждого сервера

`addClient` в 3x-ui требует числовой **id inbound'а из базы панели** (его нет в
xray-конфиге, только порт/tag). Поэтому проще всего импортировать inbound'ы прямо из панели:

```text
/inbounds 1          # показать id — порт — протокол всех inbound'ов панели
/importinbounds 1    # автоматически завести поддерживаемые inbound'ы в БД бота
```

`/importinbounds` сам определяет протокол и для shadowsocks подтягивает `method`.
Поддерживаемые протоколы: `vless`, `vmess`, `trojan`, `shadowsocks`, `hysteria2`
(в т.ч. `hysteria` v2). Неподдерживаемые (dokodemo-door и т.п.) пропускаются.

Можно добавить вручную:

```text
/addinbound <server_id> <inbound_id> <protocol> [flow] [method]
/addinbound 1 7 vless xtls-rprx-vision      # vless + reality с flow
/addinbound 1 8 vless                        # vless + xhttp/grpc/ws (flow пустой)
/addinbound 1 11 shadowsocks "" chacha20-ietf-poly1305
```

- Объект клиента зависит только от протокола; транспорт (reality/xhttp/grpc/ws/tcp) задаётся
  на стороне inbound в панели.
- `flow` (`xtls-rprx-vision`) — только для vless+reality, если этого требует ваш inbound;
  при авто-импорте flow не выставляется (как у большинства ваших клиентов).
- Поля объекта клиента по протоколам: vless `{id, flow?}`, vmess `{id}`,
  trojan `{password}`, shadowsocks `{password, method}`, hysteria2 `{auth}`.

### Как формируется клиент

При оплате/триале бот:

1. гарантирует `vpn_client` пользователя с единым секретом (`external_client_id` — UUID);
2. для каждого сервера и каждого его inbound создаёт/обновляет клиента:
   - `id` (UUID) — для vless/vmess; `password` — для trojan/shadowsocks/hysteria2;
   - `email = <public_id>-<inbound_id>` (уникален в пределах панели);
   - `sub_id = public_id` (общий — чтобы подписка панели собрала все протоколы в одну ссылку);
   - `expiryTime` — рассчитанный срок;
3. сохраняет привязку в `client_server_mappings`.

Подписки выдаются по одной ссылке на сервер: `subscription_base + public_id`
(кнопка «Мои ссылки»). Проверить/перевыпустить доступ вручную: `/provision <telegram_id>`,
посмотреть конфигурацию серверов: `/servers`.

> Примечание: точные поля объекта клиента для `shadowsocks` (2022-шифры) и `hysteria2`
> зависят от версии 3x-ui — проверьте создание на своих панелях и при необходимости
> скорректируйте `app/services/xui_payloads.py`.

## Админ-команды

- `/pending` — список заявок в ожидании проверки (с кодами);
- `/confirm <код>` — подтвердить заявку (например `/confirm PAY-1042`); для заявки в статусе failed повторяет применение;
- `/reject <код>` — отклонить заявку;
- `/active` — список активных клиентов;
- `/expired` — список истёкших клиентов;
- `/extend <telegram_id> [дней]` — ручное продление клиента;
- `/sync <telegram_id>` — повторно выставить текущий срок во всех панелях;
- `/sharing` — список клиентов с повышенной активностью по IP за 24 ч (антишеринг);
- `/sharing <telegram_id>` — детальный отчёт по пользователю (уник. IP за 15м/1ч/24ч/7д);
- `/ipscan` — немедленный сбор IP из 3x-ui и сводка по антишерингу;
- `/servers` — список серверов и их inbound'ов;
- `/addserver name|country|panel_url|username|password|[kind]|[subscription_base]` — добавить сервер;
- `/inbounds <server_id>` — показать inbound'ы панели (id, порт, протокол);
- `/importinbounds <server_id>` — авто-импорт поддерживаемых inbound'ов из панели;
- `/addinbound <server_id> <inbound_id> <protocol> [flow] [method]` — добавить inbound вручную;
- `/provision <telegram_id>` — создать/обновить клиента пользователя на всех серверах.

Действия над заявками можно выполнять двумя способами:
- инлайн-кнопками под карточкой заявки («Подтвердить»/«Отклонить»/«История»/«Профиль»),
  которая приходит администратору после того, как пользователь отправит подтверждение оплаты;
- командами `/confirm <код>` и `/reject <код>` (надёжный способ, если карточка уехала вверх по чату).

## Логика продления

При подтверждении заявки:
1. проверка статуса `waiting_admin`;
2. перевод заявки в `confirmed`;
3. поиск связанного `vpn_client`;
4. расчёт нового срока: если текущий срок активен — `+30 дней` к нему, иначе — `+30 дней`
   от текущего времени;
5. обновление клиента во всех связанных панелях 3x-ui;
6. при успехе — сохранение нового срока, статус `applied`, уведомление пользователя;
7. при ошибке части панелей — статус `failed`, кнопка «Повторить применение».

Подтверждение идемпотентно: повторный клик по уже применённой заявке не продлевает
доступ повторно.

## Антишеринг-мониторинг

Мягкий мониторинг помогает администратору видеть подозрительное использование подписки,
не блокируя пользователей. IP **не** считается точным идентификатором устройства
(мобильная сеть, CG-NAT, смена Wi-Fi и т. п.), поэтому автоматический бан в MVP не используется.

Система отслеживает не «число устройств», а количество **уникальных IP** на клиента/профиль
за окна: 15 минут, 1 час, 24 часа, 7 дней. IP берутся из журнала 3x-ui
(эндпоинт `clientIps`), поэтому в панели должно быть включено логирование IP клиентов.

Статусы по 24-часовому окну:
- `норма` — ниже порогов;
- `внимание` — `unique_24h ≥ WARN_THRESHOLD_24H` или за час уникальных IP больше `DEFAULT_IP_LIMIT`;
- `критично` — `unique_24h ≥ CRITICAL_THRESHOLD_24H`.

Сбор работает в фоне с периодом `ANTI_SHARING_POLL_MINUTES` (0 — отключить фон), наблюдения
старше 7 дней автоматически удаляются. Настройки (см. `.env.example`):

```text
ANTI_SHARING_ENABLED=true
DEVICE_POLICY=soft
DEFAULT_IP_LIMIT=3
WARN_THRESHOLD_24H=5
CRITICAL_THRESHOLD_24H=8
AUTO_BLOCK_ENABLED=false
TRACKING_WINDOW_HOURS=24
ANTI_SHARING_POLL_MINUTES=5
```

## Тестирование и линтинг

```bash
pytest          # тесты бизнес-логики и XuiClient (HTTP мокается)
ruff check .    # линтер
mypy app        # типы (опционально)
```

Реальные панели 3x-ui в тестах не вызываются — HTTP-запросы мокаются через
`pytest-httpx`.

# Graph Report - VpnBot  (2026-10-04)

## Corpus Check
- 122 files · ~70,893 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 17 file(s) not represented in the graph (top: (none) 9, .example 3, .conf 1)

## Summary
- 1740 nodes · 5557 edges · 96 communities (78 shown, 18 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 724 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `412612c0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- provisioning.py
- on_payment_action
- texts.py
- test_legacy_bind.py
- User
- user_handlers.py
- admin_handlers.py
- Settings
- keyboards.py
- Server
- billing.py
- SubHubClient
- MockPanelUpdater
- models.py
- collections_abc
- PanelUpdater
- answer_callback
- main.py
- main.go
- App.vue
- .update_client
- XuiPanelUpdater
- notify.py
- utcnow
- XuiClient
- What You Must Do When Invoked
- Base
- test_xui_client.py
- .__call__
- Protocol
- get_plan
- ._clean_bot_token
- Контекст проекта
- conftest.py
- _activate_trial
- web_bridge.py
- PaymentStatus
- connection_overview
- ._parse_ips
- IsAdmin
- package.json
- Ревью VpnBot — 4 октября 2026
- compilerOptions
- main_test.go
- api
- Контекст проекта
- .auth
- send_broadcast
- delete_user_subscription
- app
- main
- Telegram VPN Billing Bot
- web_preview.mjs
- EncryptedString
- api.ts
- VpnClient
- states.py
- devDependencies
- scripts
- test_review_regressions.py
- Настройка серверов и авто-провижининг
- graphify reference: extra exports and benchmark
- FSMContext
- D VPN — личный кабинет
- dvpn/site
- telegram-vpn-billing-bot
- test_ux.py
- MenuCallback
- test_health_check_server_returns_true_on_success
- reset_bot_confirm_keyboard
- test_health_check_server_returns_false_on_error
- check_servers
- graphify reference: query, path, explain
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- AGENTS.md
- reset_user_bot_state
- .rename
- extraction-spec.md
- menu_nav
- user_operation
- Оставшиеся риски и решения
- ServerRepository
- ._http
- _FakeMessage
- callbacks.py
- .set_subscription_base
- .provision_server

## God Nodes (most connected - your core abstractions)
1. `User` - 216 edges
2. `VpnClient` - 125 edges
3. `Settings` - 97 edges
4. `Server` - 92 edges
5. `MockPanelUpdater` - 73 edges
6. `VpnClientRepository` - 70 edges
7. `XuiClient` - 68 edges
8. `PaymentStatus` - 60 edges
9. `ServerRepository` - 60 edges
10. `PaymentRepository` - 60 edges

## Surprising Connections (you probably didn't know these)
- `Как формируется клиент` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py
- `Логика продления` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py
- `Доменная модель` --references--> `PaymentStatus`  [INFERRED]
  context.md → app/db/enums.py
- `Доменная модель` --references--> `BindRequestStatus`  [INFERRED]
  context.md → app/db/enums.py
- `Доменная модель` --references--> `Protocol`  [INFERRED]
  context.md → app/db/enums.py

## Import Cycles
- None detected.

## Communities (96 total, 18 thin omitted)

### Community 0 - "provisioning.py"
Cohesion: 0.05
Nodes (93): Inbound на панели сервера, в который нужно заводить клиентов. На одном сервере…, ServerInbound, MappingRepository, PanelUpdateError, Exception, Ошибка обновления клиента в панели., ServerUpdateResult, apply_access() (+85 more)

### Community 1 - "on_payment_action"
Cohesion: 0.07
Nodes (35): _edit_panel(), on_payment_action(), callback_query, CallbackQuery, Редактирует сообщение админ-панели, мягко гасит ошибки. parse_mode=None —…, emoji_char(), Возвращает unicode-символ значка (без анимации)., HTML-строка с анимированным значком для вставки в текст сообщения. (+27 more)

### Community 2 - "texts.py"
Cohesion: 0.07
Nodes (41): admin_nav(), ip_scan(), admin_add_server_prompt(), admin_bind_pending(), admin_bind_result(), admin_broadcast_prompt(), admin_confirm_delete(), admin_panel_clients() (+33 more)

### Community 3 - "test_legacy_bind.py"
Cohesion: 0.09
Nodes (39): BindRequestStatus, BindRequest, Заявка на привязку существующей подписки (до внедрения бота)., BindRequestRepository, approve_request(), BindApproveResult, BindRequestError, create_request() (+31 more)

### Community 4 - "User"
Cohesion: 0.11
Nodes (25): User, Удаляет пользователя и связанные записи (каскад в ORM)., Telegram ID всех пользователей, когда-либо запускавших бота., Генерирует короткий уникальный публичный ID пользователя., UserRepository, AsyncSession, test_all_telegram_ids_returns_every_user(), _persist_payment() (+17 more)

### Community 5 - "user_handlers.py"
Cohesion: 0.16
Nodes (30): OnboardingStates, onboarding_legacy_question(), onboarding_send_link_prompt(), Приветствие. Использует HTML-разметку: ID завёрнут в <code> — Telegram копирует…, welcome(), admin_denied(), _attach_and_notify(), cmd_start() (+22 more)

### Community 6 - "admin_handlers.py"
Cohesion: 0.18
Nodes (35): aiogram_fsm_context, add_inbound(), add_server(), admin_delete_subscription_by_client_id(), admin_panel(), admin_rename_server_cancel(), bind_panel_client(), clear_inbounds() (+27 more)

### Community 7 - "Settings"
Cohesion: 0.08
Nodes (46): DbSessionMiddleware, Открывает сессию БД, получает/создаёт пользователя и кладёт их в data., forward_proof_to_admins(), Конфигурация приложения из переменных окружения / .env., Settings, UserRole, has_active_timed_client(), has_client_access() (+38 more)

### Community 8 - "keyboards.py"
Cohesion: 0.15
Nodes (28): AdminCallback, BindCallback, PaymentCallback, Callback админских действий над заявкой на привязку подписки., Навигация по админ-панели (/admin). action: home | servers | server | rename |…, Callback админских действий над заявкой., _adm(), admin_back_keyboard() (+20 more)

### Community 9 - "Server"
Cohesion: 0.11
Nodes (8): ClientServerMapping, Server, MockIpProvider, Mock-провайдер для тестов: возвращает заранее заданные IP по server_id., Реальный провайдер: берёт IP клиента из журнала панели 3x-ui., XuiIpProvider, Удаляет клиента с сервера по сохранённым привязкам., _mapping()

### Community 10 - "billing.py"
Cohesion: 0.12
Nodes (39): Any, AsyncSession, Записывает событие в audit_logs., record(), _apply_panels(), _as_aware(), BillingError, BillingResult (+31 more)

### Community 11 - "SubHubClient"
Cohesion: 0.06
Nodes (51): get_settings(), decrypt(), encrypt(), _fernet(), is_encrypted(), Возвращает Fernet, выведенный из SECRET_KEY, либо None если ключ не задан.…, Шифрует строку. Без SECRET_KEY возвращает значение как есть (dev/тесты)., Расшифровывает строку. Legacy-значения в открытом виде возвращает как есть. (+43 more)

### Community 12 - "MockPanelUpdater"
Cohesion: 0.17
Nodes (27): confirm_payment(), Идемпотентное подтверждение оплаты администратором. Повторный вызов для уже…, MockPanelUpdater, Mock-реализация: ничего не делает либо имитирует сбой нужных серверов., main(), confirm(), AsyncSession, test_confirm_then_notify_user() (+19 more)

### Community 13 - "models.py"
Cohesion: 0.12
Nodes (24): aiogram_exceptions, app_bot, TimestampMixin, AuditLog, AuditRepository, app_services, Serialize access mutations per user, including commits and panel calls., asyncio (+16 more)

### Community 15 - "PanelUpdater"
Cohesion: 0.12
Nodes (21): PendingServerUpdate, PendingServerUpdateRepository, AsyncSession, PanelUpdater, Интерфейс работы с клиентом в панели. Реализуется как mock (для тестов/MVP) и…, apply_pending_for_server(), apply_pending_update(), _apply_to_server() (+13 more)

### Community 16 - "answer_callback"
Cohesion: 0.16
Nodes (15): aiogram_methods, answer(), answer_callback(), edit(), Any, CallbackQuery, Безопасно редактирует сообщение callback'а. ``callback.message`` может быть…, Безопасно отправляет ответ в чат callback'а (если сообщение доступно). (+7 more)

### Community 17 - "main.py"
Cohesion: 0.11
Nodes (23): aiogram, aiogram_client_default, aiogram_fsm_storage_memory, aiogram_utils_token, build_root_router(), Настраивает логирование приложения. - корневой логгер: WARNING (чтобы сторонние…, setup_logging(), _anti_sharing_poller() (+15 more)

### Community 18 - "main.go"
Cohesion: 0.07
Nodes (29): credentials, go_pkg_bytes, go_pkg_context, go_pkg_crypto_hmac, go_pkg_crypto_rand, go_pkg_crypto_sha256, go_pkg_crypto_subtle, go_pkg_crypto_tls (+21 more)

### Community 19 - "App.vue"
Cohesion: 0.07
Nodes (24): authTitles, awaiting, busy, code, comment, config, connection, days (+16 more)

### Community 20 - ".update_client"
Cohesion: 0.14
Nodes (7): Ищет клиента в inbound по uuid, email или subId (стабильные ID)., Совместимый алиас find_client (по uuid/email)., Идентификатор для updateClient/{id}: id для vless/vmess, иначе email., Обновляет клиента, сохраняя все его поля и меняя только нужные. Возвращает…, Устанавливает expiryTime (мс) и включает клиента., Лимит уникальных IP (0 = без лимита). Не считать точным лимитом устройств., Совместимый метод: продление через read-modify-write.

### Community 21 - "XuiPanelUpdater"
Cohesion: 0.19
Nodes (10): Один клиент панели (глобальный по email), привязанный к её inbound'ам.…, ServerProvision, build_client_record(), client_record_body(), Извлекает model.Client из ответа ``clients/get``., Унифицированный объект клиента для нового client-API (3x-ui >= 3.2.x). Один…, _is_missing_client_error(), Старые панели: отдельный клиент в каждом inbound (per-inbound email). (+2 more)

### Community 22 - "notify.py"
Cohesion: 0.29
Nodes (10): notify_admins_bind_failed(), notify_admins_failed(), notify_admins_new_bind_request(), notify_admins_new_request(), notify_user_subscription_deleted(), Bot, admin_bind_card(), admin_payment_card() (+2 more)

### Community 23 - "utcnow"
Cohesion: 0.07
Nodes (65): notify_user_expiry(), Уведомление пользователя об окончании подписки. True — если доставлено., IpObservation, _active_clients(), collect_all(), collect_for_client(), compute_status(), _level_for() (+57 more)

### Community 24 - "XuiClient"
Cohesion: 0.09
Nodes (29): Any, Exception, Response, _quote_path_segment(), Авторизованный запрос: гарантирует login и при истёкшей сессии выполняет…, Берёт CSRF-токен с /csrf-token (3x-ui >= 3.2.x). На старых панелях endpoint…, Базовая ошибка взаимодействия с панелью 3x-ui., Возвращает список inbound'ов панели с их БД-id, портами и протоколами. (+21 more)

### Community 25 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 26 - "Base"
Cohesion: 0.20
Nodes (9): app_db, Base, Базовый класс для всех ORM-моделей., WebSession, WebToken, do_run_migrations(), run_migrations_online(), DeclarativeBase (+1 more)

### Community 27 - "test_xui_client.py"
Cohesion: 0.28
Nodes (23): _client(), _mock_csrf(), HTTPXMock, Регистрирует ответ /csrf-token (3x-ui 3.2.x запрашивает его перед login)., test_bearer_token_skips_login_and_csrf(), test_create_client_record(), test_del_client_quotes_identifier_path_segment(), test_find_client_by_sub_id() (+15 more)

### Community 28 - ".__call__"
Cohesion: 0.19
Nodes (16): _command_name(), _describe_callback(), _describe_event(), _describe_message(), Any, CallbackQuery, Message, TelegramObject (+8 more)

### Community 29 - "Protocol"
Cohesion: 0.11
Nodes (34): Protocol, ProvisionTarget, Описание клиента, которого нужно создать/обновить в конкретном inbound., build_client_object(), client_identifier(), _client_uuid_for_api(), _looks_like_db_id(), merge_client_record_for_update() (+26 more)

### Community 30 - "get_plan"
Cohesion: 0.33
Nodes (5): get_plan(), PaymentPlan, Выгода относительно помесячной оплаты за тот же срок., test_get_plan(), test_plan_amounts_are_fixed_server_side()

### Community 31 - "._clean_bot_token"
Cohesion: 0.33
Nodes (3): Убирает пробелы и обрамляющие кавычки вокруг токена., Разрешает задавать ADMIN_TELEGRAM_IDS как строку '1,2,3' или одно число., field_validator

### Community 32 - "Контекст проекта"
Cohesion: 0.12
Nodes (16): API, Архитектура, Безопасность аутентификации (backend/main.go), Важные инженерные правила, Доменная модель (таблицы веб-части, в БД бота), Запуск, Контекст проекта, Конфигурация (+8 more)

### Community 33 - "conftest.py"
Cohesion: 0.44
Nodes (9): pytest_asyncio, admin(), AsyncSession, datetime, fixture, server(), session(), user() (+1 more)

### Community 34 - "_activate_trial"
Cohesion: 0.29
Nodes (7): trial_already_used(), trial_failed(), trial_no_client(), _activate_trial(), Фоновая периодическая проверка доступности серверов 3x-ui., _server_health_poller(), build_updater()

### Community 35 - "web_bridge.py"
Cohesion: 0.07
Nodes (50): aiohttp, AttachmentType, PaymentAttachment, Durable per-admin Telegram delivery, retried independently of HTTP requests., WebAccount, WebDelivery, WebLinkRequest, get_engine() (+42 more)

### Community 36 - "PaymentStatus"
Cohesion: 0.10
Nodes (25): admin_pending(), PaymentStatus, PaymentRequest, PaymentRepository, Берёт заявку с блокировкой строки (SELECT ... FOR UPDATE). На Postgres…, Удаляет заявку (вместе с вложениями по каскаду)., Последняя успешная (применённая/подтверждённая) оплата пользователя.…, create_request() (+17 more)

### Community 37 - "connection_overview"
Cohesion: 0.33
Nodes (6): connection_overview(), Unified SubHub connection screen with live server availability., server_button_label(), Флаг не добавляется автоматически — он уже в названии сервера., test_connection_overview_shows_server_availability(), test_server_button_label_has_no_autoflag()

### Community 38 - "._parse_ips"
Cohesion: 0.50
Nodes (3): Извлекает IP из вариантов ответа 3x-ui, не сохраняя метаданные лога., test_parse_ips_handles_arbitrary_input(), test_parse_ips_extracts_ip_from_panel_log_objects()

### Community 39 - "IsAdmin"
Cohesion: 0.17
Nodes (12): aiogram_filters, aiogram_types, IsAdmin, TelegramObject, Пропускает событие только если пользователь — администратор., BaseFilter, test_is_admin_filter_accepts_admin(), test_is_admin_filter_rejects_missing_user() (+4 more)

### Community 40 - "package.json"
Cohesion: 0.12
Nodes (14): lucide-vue-next, typescript, vite, @vitejs/plugin-vue, vue, vue-tsc, dependencies, lucide-vue-next (+6 more)

### Community 41 - "Ревью VpnBot — 4 октября 2026"
Cohesion: 0.22
Nodes (8): Исправления в рабочем дереве, Объём и доказательства, Порядок применения в production, Проверки, Разбор PAY-1C3F1344, Ревью VpnBot — 4 октября 2026, Результат, Устройство production

### Community 42 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, esModuleInterop, jsx, lib, module, moduleResolution, resolveJsonModule, skipLibCheck (+4 more)

### Community 43 - "main_test.go"
Cohesion: 0.21
Nodes (11): go_pkg_net_http, go_pkg_net_http_httptest, go_pkg_strings, go_pkg_testing, go_pkg_time, testing.T, canonicalEmail(), TestCodesBoundToAccountAndPurpose() (+3 more)

### Community 44 - "api"
Cohesion: 0.32
Nodes (12): api(), authenticate(), copy(), getConnection(), go(), link(), logout(), pay() (+4 more)

### Community 45 - "Контекст проекта"
Cohesion: 0.13
Nodes (14): Админские команды, Антишеринг, Доменная модель, Запуск, Интеграция с 3x-ui, Контекст проекта, Конфигурация, Локальные артефакты (+6 more)

### Community 46 - ".auth"
Cohesion: 0.53
Nodes (6): net/http.Request, net/http.ResponseWriter, decode(), digest(), fail(), respond()

### Community 47 - "send_broadcast"
Cohesion: 0.25
Nodes (7): BroadcastResult, Bot, Рассылает текстовое сообщение всем пользователям. Сообщение отправляется…, send_broadcast(), FakeBot, test_send_broadcast_counts_sent_and_failed(), test_send_broadcast_empty_list()

### Community 48 - "delete_user_subscription"
Cohesion: 0.21
Nodes (11): _delete_local_subscription(), delete_user_subscription(), AsyncSession, Удаляет VPN-подписку пользователя с панелей и из БД бота. История оплат, заявки…, SubscriptionDeleteResult, _FakeState, AsyncSession, test_admin_delete_subscription_uses_client_id_not_telegram_id() (+3 more)

### Community 49 - "app"
Cohesion: 0.29
Nodes (6): app, config, context.Context, github.com/jackc/pgx/v5/pgxpool.Pool, net/http.Client, pgx.Tx

### Community 50 - "main"
Cohesion: 0.22
Nodes (7): bucket, limiter, net/http.Handler, sync.Mutex, time.Time, env(), main()

### Community 51 - "Telegram VPN Billing Bot"
Cohesion: 0.14
Nodes (13): Telegram VPN Billing Bot, Админ-команды, Антишеринг-мониторинг, Возможности, Граф кода (graphify), Единая подписка SubHub, Запуск через Docker Compose, Конфигурация (+5 more)

### Community 52 - "web_preview.mjs"
Cohesion: 0.29
Nodes (6): ref_node_fs_promises, ref_node_http, ref_node_path, ref_node_url, root, types

### Community 53 - "EncryptedString"
Cohesion: 0.29
Nodes (6): EncryptedString, Any, Прозрачно шифрует значение при записи и расшифровывает при чтении. - Если…, Важные инженерные правила проекта, P1 — пароли панелей не защищены шифрованием приложения, TypeDecorator

### Community 54 - "api.ts"
Cohesion: 0.33
Nodes (4): APIError, Configuration, Plan, Profile

### Community 55 - "VpnClient"
Cohesion: 0.18
Nodes (18): VpnClient, datetime, Клиенты, которым пора слать уведомление об окончании. Берём тех, у кого задан…, Сохраняет результат фоновой проверки доступности сервера., _utcnow(), VpnClientRepository, grant_trial(), Выдаёт бесплатный пробный период один раз на аккаунт. Пробный период… (+10 more)

### Community 56 - "states.py"
Cohesion: 0.50
Nodes (4): aiogram_fsm_state, AdminStates, ProofStates, StatesGroup

### Community 57 - "devDependencies"
Cohesion: 0.40
Nodes (5): devDependencies, typescript, vite, @vitejs/plugin-vue, vue-tsc

### Community 58 - "scripts"
Cohesion: 0.50
Nodes (4): scripts, build, dev, preview

### Community 59 - "test_review_regressions.py"
Cohesion: 0.09
Nodes (24): ProvisionInbound, Inbound сервера, к которому нужно привязать клиента., pytest_httpx, parametrize, ReadOnlyPanel, test_attach_success_without_membership_is_not_provisioning_success(), test_capability_failure_does_not_fall_back_to_legacy_writes(), test_client_read_failure_is_not_misreported_as_missing() (+16 more)

### Community 60 - "Настройка серверов и авто-провижининг"
Cohesion: 0.40
Nodes (5): Как формируется клиент, Настройка серверов и авто-провижининг, Перенос пользователей, существовавших до бота, Шаг 1. Добавить серверы, Шаг 2. Импортировать inbound'ы каждого сервера

### Community 61 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 62 - "FSMContext"
Cohesion: 0.11
Nodes (20): admin_add_server_cancel(), admin_broadcast_cancel(), admin_broadcast_send(), admin_delete_subscription_cancel(), admin_rename_server_name(), admin_subscription_url_cancel(), admin_subscription_url_value(), FSMContext (+12 more)

### Community 63 - "D VPN — личный кабинет"
Cohesion: 0.25
Nodes (7): D VPN — личный кабинет, Архитектура, Запуск вместе с существующим ботом, Локальная разработка, Результаты проверки, Что реализовано, Эксплуатация

### Community 71 - "test_ux.py"
Cohesion: 0.13
Nodes (22): country_flag(), Эмодзи-флаг по ISO2-коду страны (напр. 'SE' -> 🇸🇪). Иначе пусто., _cancel_payment(), _is_active(), Удаляет неподтверждённую заявку (без приложенного скриншота)., Пробный доступен, если им не пользовались и подписку никогда не оформляли., _trial_available(), _DummyState (+14 more)

### Community 72 - "MenuCallback"
Cohesion: 0.15
Nodes (22): MenuCallback, Навигация по inline-меню (редактирование сообщения на месте). action: home |…, custom_emoji_id(), Возвращает custom_emoji_id значка или None, если значок не найден., cancel_payment_keyboard(), connection_keyboard(), One stable SubHub subscription link for every location and protocol., Кнопка «Отмена» под заявкой на оплату — удаляет заявку. (+14 more)

### Community 74 - "reset_bot_confirm_keyboard"
Cohesion: 0.50
Nodes (4): Подтверждение сброса данных пользователя в боте., reset_bot_confirm_keyboard(), _all_buttons(), test_reset_confirm_keyboard()

### Community 76 - "check_servers"
Cohesion: 0.33
Nodes (6): check_server(), check_servers(), AsyncSession, Проверяет доступность панели 3x-ui одного сервера. Успешный login считается…, Проверяет все серверы и сохраняет результат в БД. Возвращает отображение…, Фоновые задачи

### Community 77 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 78 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 79 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 80 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 84 - "reset_user_bot_state"
Cohesion: 0.50
Nodes (4): AsyncSession, Удаляет пользователя и связанные данные только из БД бота. 3x-ui панели не…, reset_user_bot_state(), UserResetResult

### Community 87 - "menu_nav"
Cohesion: 0.12
Nodes (25): _back_button(), _btn(), extend_plans_keyboard(), free_proxies_keyboard(), install_guides_keyboard(), news_channel_keyboard(), _plan_label(), purchase_plans_keyboard() (+17 more)

### Community 88 - "user_operation"
Cohesion: 0.38
Nodes (7): decorate(), wrapped(), user_operation(), check_released(), test_user_operations_serialize_and_release_on_failure(), first(), second()

### Community 89 - "Оставшиеся риски и решения"
Cohesion: 0.29
Nodes (7): P1/P2 — частичный успех внешней операции требует сверки, P1 — административные права зависят от тарифа, P1 — биллинг и панели не образуют одну транзакцию, P2 — мониторинг и производительность, P2 — старые ошибки оплат без ожидающих задач, P2 — эксплуатация и воспроизводимость, Оставшиеся риски и решения

### Community 90 - "ServerRepository"
Cohesion: 0.11
Nodes (16): admin_add_server_line(), _finalize_new_server(), _parse_server_line(), Сохраняет сервер и сразу пытается импортировать его inbound'ы. Так добавленный…, Парсит строку 'name|country|panel_url|username|password|[kind]|[sub]'.…, admin_import_inbounds(), Удаляет сервер вместе с inbound'ами и привязками (каскад). Коллекции грузим…, Удаляет настроенный inbound. Возвращает число удалённых записей. (+8 more)

### Community 92 - "_FakeMessage"
Cohesion: 0.40
Nodes (3): _FakeBot, _FakeMessage, Any

### Community 93 - "callbacks.py"
Cohesion: 0.25
Nodes (8): aiogram_filters_callback_data, OnboardCallback, PlanCallback, Callback выбора тарифа пользователем. code — код тарифа из PLANS (1m/6m/12m)…, Онбординг: был ли пользователь клиентом до внедрения бота., CallbackData, Пользователь по callback может прислать только код тарифа — не цену/срок. Это…, test_plan_callback_carries_only_code()

## Knowledge Gaps
- **147 isolated node(s):** `credentials`, `dvpn/site`, `name`, `version`, `private` (+142 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 588 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `provisioning.py`, `on_payment_action`, `texts.py`, `test_legacy_bind.py`, `user_handlers.py`, `admin_handlers.py`, `Settings`, `billing.py`, `MockPanelUpdater`, `models.py`, `PanelUpdater`, `notify.py`, `utcnow`, `Base`, `conftest.py`, `_activate_trial`, `web_bridge.py`, `PaymentStatus`, `IsAdmin`, `delete_user_subscription`, `VpnClient`, `FSMContext`, `test_ux.py`, `reset_user_bot_state`, `menu_nav`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Why does `Server` connect `Server` to `provisioning.py`, `texts.py`, `test_legacy_bind.py`, `admin_handlers.py`, `keyboards.py`, `SubHubClient`, `MockPanelUpdater`, `models.py`, `PanelUpdater`, `XuiPanelUpdater`, `utcnow`, `XuiClient`, `What You Must Do When Invoked`, `Base`, `conftest.py`, `web_bridge.py`, `connection_overview`, `Контекст проекта`, `EncryptedString`, `VpnClient`, `test_review_regressions.py`, `test_ux.py`, `check_servers`, `.rename`, `ServerRepository`, `.set_subscription_base`, `.provision_server`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Why does `XuiClient` connect `XuiClient` to `provisioning.py`, `admin_handlers.py`, `._parse_ips`, `Settings`, `Server`, `test_review_regressions.py`, `test_xui_client.py`, `check_servers`, `models.py`, `.update_client`, `XuiPanelUpdater`, `._http`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 145 inferred relationships involving `User` (e.g. with `admin_broadcast_send()` and `admin_delete_subscription_by_client_id()`) actually correct?**
  _`User` has 145 INFERRED edges - model-reasoned connections that need verification._
- **Are the 76 inferred relationships involving `VpnClient` (e.g. with `notify_user_extended()` and `access_extended()`) actually correct?**
  _`VpnClient` has 76 INFERRED edges - model-reasoned connections that need verification._
- **Are the 47 inferred relationships involving `Settings` (e.g. with `add_server()` and `admin_add_server_line()`) actually correct?**
  _`Settings` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `Server` (e.g. with `_finalize_new_server()` and `admin_server_keyboard()`) actually correct?**
  _`Server` has 33 INFERRED edges - model-reasoned connections that need verification._
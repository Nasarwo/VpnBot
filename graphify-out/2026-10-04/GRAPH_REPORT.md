# Graph Report - VpnBot  (2026-10-04)

## Corpus Check
- 132 files · ~93,101 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 17 file(s) not represented in the graph (top: (none) 9, .example 3, .conf 1)

## Summary
- 2103 nodes · 7144 edges · 100 communities (86 shown, 14 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 930 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `81e37358`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- provisioning.py
- texts.py
- admin_nav
- test_legacy_bind.py
- test_whitelist.py
- user_handlers.py
- admin_handlers.py
- User
- keyboards.py
- XuiPanelUpdater
- billing.py
- SubHubClient
- PanelUpdater
- models.py
- sqlalchemy
- test_review_regressions.py
- test_whitelist_pg.py
- main.py
- main.go
- App.vue
- config.py
- whitelist.py
- notify.py
- utcnow
- ._parse_json
- What You Must Do When Invoked
- PaymentRequest
- test_xui_client.py
- test_access.py
- test_xui_payloads.py
- whitelist_admin
- Settings
- Контекст проекта
- QuotaClientState
- create_request
- web_bridge.py
- on_payment_action
- test_whitelist_xui.py
- ._api
- Server
- package.json
- Ревью VpnBot — 4 октября 2026
- compilerOptions
- main_test.go
- api
- Контекст проекта
- .auth
- operation_lock.py
- Задание агенту: услуга «Обход белых списков» в VpnBot
- app
- main
- Telegram VPN Billing Bot
- web_preview.mjs
- EncryptedString
- api.ts
- VpnClient
- FakeState
- devDependencies
- Услуга «Обход белых списков» — реализация и порядок внедрения
- test_xui_updater.py
- answer
- graphify reference: extra exports and benchmark
- parametrize
- D VPN — личный кабинет
- dvpn/site
- telegram-vpn-billing-bot
- test_ux.py
- MenuCallback
- PendingRequestExists
- vpn_client
- XuiError
- check_servers
- graphify reference: query, path, explain
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- AGENTS.md
- delete_user_subscription
- Обновление production — 4 октября 2026
- extraction-spec.md
- Настройка серверов и авто-провижининг
- MockPanelUpdater
- Оставшиеся риски и решения
- ServerRepository
- XuiClient
- _FakeMessage
- callbacks.py
- collect_links
- FakeMessage
- panel
- XuiAuthError
- test_attach_success_without_membership_is_not_provisioning_success
- vue

## God Nodes (most connected - your core abstractions)
1. `User` - 236 edges
2. `VpnClient` - 140 edges
3. `Server` - 125 edges
4. `Settings` - 112 edges
5. `MockPanelUpdater` - 91 edges
6. `PaymentRequest` - 79 edges
7. `PaymentStatus` - 78 edges
8. `VpnClientRepository` - 78 edges
9. `XuiClient` - 74 edges
10. `ServerRepository` - 63 edges

## Surprising Connections (you probably didn't know these)
- `Как формируется клиент` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py
- `Логика продления` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py
- `Доменная модель` --references--> `PaymentStatus`  [INFERRED]
  context.md → app/db/enums.py
- `Provisioning в 3x-ui` --references--> `VpnClient`  [INFERRED]
  context.md → app/db/models.py
- `Интеграция с 3x-ui` --references--> `Server`  [INFERRED]
  context.md → app/db/models.py

## Import Cycles
- None detected.

## Communities (100 total, 14 thin omitted)

### Community 0 - "provisioning.py"
Cohesion: 0.06
Nodes (88): MappingRepository, PanelUpdateError, Exception, Ошибка обновления клиента в панели., _apply_to_server(), apply_access(), apply_access_to_server(), bind_existing_client() (+80 more)

### Community 1 - "texts.py"
Cohesion: 0.05
Nodes (59): emoji_char(), Возвращает unicode-символ значка (без анимации)., HTML-строка с анимированным значком для вставки в текст сообщения., tg(), access_extended(), access_update_pending(), admin_add_cancelled(), admin_bind_result() (+51 more)

### Community 2 - "admin_nav"
Cohesion: 0.10
Nodes (26): admin_nav(), _edit_panel(), ip_scan(), list_pending(), CallbackQuery, Редактирует сообщение админ-панели, мягко гасит ошибки. parse_mode=None —…, sharing_report(), admin_add_server_prompt() (+18 more)

### Community 3 - "test_legacy_bind.py"
Cohesion: 0.06
Nodes (43): app_db, BindRequest, Заявка на привязку существующей подписки (до внедрения бота)., BindRequestRepository, AsyncSession, approve_request(), BindApproveResult, BindRequestError (+35 more)

### Community 4 - "test_whitelist.py"
Cohesion: 0.13
Nodes (45): create_traffic_request(), _new_payment_code(), datetime, Заявка на покупку пакета «Обход белых списков». Создаётся только при активной…, whitelist_package_title(), Остатки пользователя; при доступной панели — с актуальной сверкой. Чтение…, user_overview(), _account() (+37 more)

### Community 5 - "user_handlers.py"
Cohesion: 0.11
Nodes (49): aiogram_fsm_context, aiogram_fsm_state, AdminStates, OnboardingStates, ProofStates, onboarding_legacy_question(), onboarding_send_link_prompt(), Приветствие. Использует HTML-разметку: ID завёрнут в <code> — Telegram копирует… (+41 more)

### Community 6 - "admin_handlers.py"
Cohesion: 0.15
Nodes (44): add_inbound(), add_server(), admin_add_server_cancel(), admin_broadcast_cancel(), admin_broadcast_send(), admin_delete_subscription_by_client_id(), admin_delete_subscription_cancel(), admin_panel() (+36 more)

### Community 7 - "User"
Cohesion: 0.06
Nodes (62): IsAdmin, TelegramObject, Пропускает событие только если пользователь — администратор., UserRole, User, Удаляет пользователя и связанные записи (каскад в ORM)., Telegram ID всех пользователей, когда-либо запускавших бота., Генерирует короткий уникальный публичный ID пользователя. (+54 more)

### Community 8 - "keyboards.py"
Cohesion: 0.11
Nodes (52): _adm(), admin_add_server_type_keyboard(), admin_back_keyboard(), admin_bind_keyboard(), admin_bind_retry_keyboard(), admin_confirm_delete_keyboard(), admin_home_keyboard(), admin_payment_keyboard() (+44 more)

### Community 9 - "XuiPanelUpdater"
Cohesion: 0.15
Nodes (12): Один клиент панели (глобальный по email), привязанный к её inbound'ам.…, ServerProvision, build_client_record(), client_record_body(), Извлекает model.Client из ответа ``clients/get``., Унифицированный объект клиента для нового client-API (3x-ui >= 3.2.x).…, _is_missing_client_error(), Старые панели: отдельный клиент в каждом inbound (per-inbound email). (+4 more)

### Community 10 - "billing.py"
Cohesion: 0.14
Nodes (41): _apply_panels(), _as_aware(), BillingError, BillingResult, compute_new_expiry(), _confirm_traffic(), _count_eligible_mappings(), _evaluate_panel_results() (+33 more)

### Community 11 - "SubHubClient"
Cohesion: 0.07
Nodes (26): aiogram_methods, build_happ_import_url(), Resolve the first panel identity known to SubHub. Older bot records can have a…, The panels have not exposed this identity to SubHub yet., The identity exists, but currently has no active nodes., Build a signed HTTPS trampoline for importing a legacy subscription., Small authenticated client for the SubHub admin API. Subscription URLs and…, ResolvedSubscription (+18 more)

### Community 12 - "PanelUpdater"
Cohesion: 0.11
Nodes (47): Any, AsyncSession, Записывает событие в audit_logs., record(), PanelUpdater, Интерфейс работы с клиентом в панели. Реализуется как mock (для тестов/MVP) и…, adjust_balance(), after_access_change() (+39 more)

### Community 13 - "models.py"
Cohesion: 0.11
Nodes (27): aiogram_filters, app_bot, TimestampMixin, BindRequestStatus, Protocol, AuditLog, AuditRepository, app_services (+19 more)

### Community 14 - "sqlalchemy"
Cohesion: 0.07
Nodes (4): alembic, collections_abc, sqlalchemy, sqlalchemy_types

### Community 15 - "test_review_regressions.py"
Cohesion: 0.13
Nodes (26): PendingServerUpdate, Inbound на панели сервера, в который нужно заводить клиентов. На одном сервере…, ServerInbound, PendingServerUpdateRepository, datetime, _utcnow(), apply_pending_for_server(), apply_pending_update() (+18 more)

### Community 16 - "test_whitelist_pg.py"
Cohesion: 0.12
Nodes (30): Base, Базовый класс для всех ORM-моделей., AttachmentType, Пакет покупки трафика «Обход белых списков» (настраивается админом)., TrafficPackage, WebSession, WebToken, attach_proof() (+22 more)

### Community 17 - "main.py"
Cohesion: 0.08
Nodes (35): aiogram, aiogram_client_default, aiogram_fsm_storage_memory, aiogram_types, aiogram_utils_token, DbSessionMiddleware, Открывает сессию БД, получает/создаёт пользователя и кладёт их в data., build_root_router() (+27 more)

### Community 18 - "main.go"
Cohesion: 0.07
Nodes (29): credentials, go_pkg_bytes, go_pkg_context, go_pkg_crypto_hmac, go_pkg_crypto_rand, go_pkg_crypto_sha256, go_pkg_crypto_subtle, go_pkg_crypto_tls (+21 more)

### Community 19 - "App.vue"
Cohesion: 0.07
Nodes (24): authTitles, awaiting, busy, code, comment, config, connection, days (+16 more)

### Community 20 - "config.py"
Cohesion: 0.11
Nodes (31): get_settings(), decrypt(), encrypt(), _fernet(), is_encrypted(), Возвращает Fernet, выведенный из SECRET_KEY, либо None если ключ не задан.…, Шифрует строку. Без SECRET_KEY возвращает значение как есть (dev/тесты)., Расшифровывает строку. Legacy-значения в открытом виде возвращает как есть. (+23 more)

### Community 21 - "whitelist.py"
Cohesion: 0.09
Nodes (33): Единственная строка настроек услуги (id = 1)., Журнал выдач/начислений/корректировок, привязанных к исходной операции., WhitelistConfig, WhitelistLedger, access_state(), AccessState, admin_summary(), AdminSummary (+25 more)

### Community 22 - "notify.py"
Cohesion: 0.16
Nodes (20): aiogram_exceptions, on_bind_action(), callback_query, forward_proof_to_admins(), notify_admins_bind_failed(), notify_admins_new_bind_request(), notify_admins_new_request(), notify_first_purchase_channel() (+12 more)

### Community 23 - "utcnow"
Cohesion: 0.12
Nodes (47): IpObservation, _active_clients(), collect_all(), collect_for_client(), compute_status(), _level_for(), list_all_statuses(), list_flagged() (+39 more)

### Community 24 - "._parse_json"
Cohesion: 0.13
Nodes (13): Any, _quote_path_segment(), Возвращает список inbound'ов панели с их БД-id, портами и протоколами., Ищет клиента в inbound по uuid, email или subId (стабильные ID)., Совместимый алиас find_client (по uuid/email)., Удаляет клиента из inbound., Список всех клиентов панели. На 3x-ui >= 3.2.x берётся из…, Возвращает запись клиента нового API: {"client": {...}, "inboundIds": [...]}.… (+5 more)

### Community 25 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 26 - "PaymentRequest"
Cohesion: 0.13
Nodes (12): PaymentRequest, PaymentRepository, Берёт заявку с блокировкой строки (SELECT ... FOR UPDATE). На Postgres…, Число применённых оплат подписки (покупки трафика не учитываются)., Удаляет заявку (вместе с вложениями по каскаду)., Последняя успешная (применённая/подтверждённая) оплата пользователя.…, cancel_open_request(), _open_request_for_update() (+4 more)

### Community 27 - "test_xui_client.py"
Cohesion: 0.28
Nodes (23): _client(), _mock_csrf(), HTTPXMock, Регистрирует ответ /csrf-token (3x-ui 3.2.x запрашивает его перед login)., test_bearer_token_skips_login_and_csrf(), test_create_client_record(), test_del_client_quotes_identifier_path_segment(), test_find_client_by_sub_id() (+15 more)

### Community 28 - "test_access.py"
Cohesion: 0.12
Nodes (29): _command_name(), _describe_callback(), _describe_event(), _describe_message(), Any, CallbackQuery, Message, TelegramObject (+21 more)

### Community 29 - "test_xui_payloads.py"
Cohesion: 0.11
Nodes (32): build_client_object(), client_identifier(), _client_uuid_for_api(), _looks_like_db_id(), merge_client_record_for_update(), pick_panel_client_secret(), Any, Exception (+24 more)

### Community 30 - "whitelist_admin"
Cohesion: 0.15
Nodes (23): whitelist_admin(), choose_inbound(), ensure_defaults(), get_active_server(), get_config(), list_packages(), process_due(), Запускает услугу и выдаёт её нынешним активным пользователям. Повторный запуск… (+15 more)

### Community 31 - "Settings"
Cohesion: 0.09
Nodes (23): admin_add_server_line(), _finalize_new_server(), _finalize_whitelist_server(), provision_user(), Сохраняет сервер и сразу пытается импортировать его inbound'ы. Так добавленный…, Добавляет сервер услуги и сразу сверяет его inbound'ы. До успешной сверки с…, admin_import_inbounds(), admin_provision_result() (+15 more)

### Community 32 - "Контекст проекта"
Cohesion: 0.13
Nodes (14): Архитектура, Безопасность аутентификации (backend/main.go), Важные инженерные правила, Доменная модель (таблицы веб-части, в БД бота), Запуск, Контекст проекта, Конфигурация, Локальные артефакты (+6 more)

### Community 33 - "QuotaClientState"
Cohesion: 0.12
Nodes (16): Бизнес-учёт трафика пользователя на whitelist-сервере. Остатки…, WhitelistAccount, QuotaClientState, QuotaTarget, Читает клиента и его счётчик трафика (None — клиента нет)., Пакетное чтение клиентов одной сессией панели., Создаёт/обновляет клиента с квотой и проверяет результат чтением., Абсолютное целевое состояние клиента с учётом трафика. ``total_bytes`` —… (+8 more)

### Community 34 - "create_request"
Cohesion: 0.14
Nodes (21): notify_user_extended(), create_request(), Создаёт заявку на продление и переводит её в ожидание проверки админом.…, FakeBot, Any, AsyncSession, test_admin_notified_about_new_request(), test_confirm_then_notify_user() (+13 more)

### Community 35 - "web_bridge.py"
Cohesion: 0.06
Nodes (51): aiohttp, PaymentAttachment, Durable per-admin Telegram delivery, retried independently of HTTP requests., WebAccount, WebDelivery, WebLinkRequest, get_plan(), PaymentPlan (+43 more)

### Community 36 - "on_payment_action"
Cohesion: 0.16
Nodes (20): _after_applied_payment(), on_payment_action(), InlineKeyboardMarkup, Уведомления и SubHub после применения; возвращает итог для администратора.…, _whitelist_home(), notify_admins_failed(), notify_user_traffic_credited(), admin_history() (+12 more)

### Community 37 - "test_whitelist_xui.py"
Cohesion: 0.28
Nodes (17): ProvisionInbound, Inbound сервера, к которому нужно привязать клиента., _auth(), _body(), HTTPXMock, parametrize, HTTP-контракт клиента с квотой на 3x-ui (clients API >= 3.2). Сверено с…, _record() (+9 more)

### Community 38 - "._api"
Cohesion: 0.23
Nodes (5): Response, Авторизованный запрос: гарантирует login и при истёкшей сессии выполняет…, Берёт CSRF-токен с /csrf-token (3x-ui >= 3.2.x). На старых панелях endpoint…, Определяет, есть ли у панели новый client-API /panel/api/clients. В 3x-ui 3.2.x…, Возвращает список IP-адресов клиента из журнала 3x-ui (iplimit log). Требует…

### Community 39 - "Server"
Cohesion: 0.12
Nodes (12): ClientServerMapping, Server, MockIpProvider, Mock-провайдер для тестов: возвращает заранее заданные IP по server_id., Реальный провайдер: берёт IP клиента из журнала панели 3x-ui., XuiIpProvider, Создаёт/обновляет клиента сразу для всех inbound'ов сервера., Удаляет клиента с сервера по сохранённым привязкам. (+4 more)

### Community 40 - "package.json"
Cohesion: 0.12
Nodes (16): lucide-vue-next, typescript, vite, @vitejs/plugin-vue, vue-tsc, dependencies, lucide-vue-next, vue (+8 more)

### Community 41 - "Ревью VpnBot — 4 октября 2026"
Cohesion: 0.25
Nodes (8): Исправления в рабочем дереве, Объём и доказательства, Порядок применения в production, Проверки, Разбор PAY-1C3F1344, Ревью VpnBot — 4 октября 2026, Результат, Устройство production

### Community 42 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, esModuleInterop, jsx, lib, module, moduleResolution, resolveJsonModule, skipLibCheck (+4 more)

### Community 43 - "main_test.go"
Cohesion: 0.21
Nodes (11): go_pkg_net_http, go_pkg_net_http_httptest, go_pkg_strings, go_pkg_testing, go_pkg_time, testing.T, canonicalEmail(), TestCodesBoundToAccountAndPurpose() (+3 more)

### Community 44 - "api"
Cohesion: 0.28
Nodes (13): Пользовательские сценарии, api(), authenticate(), copy(), getConnection(), go(), link(), logout() (+5 more)

### Community 45 - "Контекст проекта"
Cohesion: 0.12
Nodes (15): Админские команды, Антишеринг, Запуск, Интеграция с 3x-ui, Контекст проекта, Конфигурация, Локальные артефакты, Назначение (+7 more)

### Community 46 - ".auth"
Cohesion: 0.53
Nodes (6): net/http.Request, net/http.ResponseWriter, decode(), digest(), fail(), respond()

### Community 47 - "operation_lock.py"
Cohesion: 0.09
Nodes (22): do_run_migrations(), run_migrations_online(), BroadcastResult, Bot, Рассылает текстовое сообщение всем пользователям. Сообщение отправляется…, send_broadcast(), Serialize access mutations per user, including commits and panel calls., decorate() (+14 more)

### Community 48 - "Задание агенту: услуга «Обход белых списков» в VpnBot"
Cohesion: 0.15
Nodes (12): 1. Контекст проекта, 2. Согласованное поведение услуги, 3. Сервер и настройки администратора, 4. Технический контракт учёта трафика, 5. Биллинг, конкуренция и восстановление, 6. Пользовательский интерфейс, 7. Обязательная проверка, 8. Порядок работы и сдача (+4 more)

### Community 49 - "app"
Cohesion: 0.29
Nodes (6): app, config, context.Context, github.com/jackc/pgx/v5/pgxpool.Pool, net/http.Client, pgx.Tx

### Community 50 - "main"
Cohesion: 0.22
Nodes (7): bucket, limiter, net/http.Handler, sync.Mutex, time.Time, env(), main()

### Community 51 - "Telegram VPN Billing Bot"
Cohesion: 0.17
Nodes (12): Telegram VPN Billing Bot, Админ-команды, Антишеринг-мониторинг, Граф кода (graphify), Единая подписка SubHub, Конфигурация, Логика продления, Локальный запуск (dev) (+4 more)

### Community 52 - "web_preview.mjs"
Cohesion: 0.29
Nodes (6): ref_node_fs_promises, ref_node_http, ref_node_path, ref_node_url, root, types

### Community 53 - "EncryptedString"
Cohesion: 0.25
Nodes (7): EncryptedString, Any, Прозрачно шифрует значение при записи и расшифровывает при чтении. - Если…, Важные инженерные правила проекта, P1 — пароли панелей не защищены шифрованием приложения, 8. Проверки, TypeDecorator

### Community 54 - "api.ts"
Cohesion: 0.33
Nodes (4): APIError, Configuration, Plan, Profile

### Community 55 - "VpnClient"
Cohesion: 0.10
Nodes (33): VpnClient, Клиенты, которым пора слать уведомление об окончании. Берём тех, у кого задан…, VpnClientRepository, process_expiry_notifications(), AsyncSession, Bot, Шлёт уведомления «за день / за час / в момент окончания». Каждая стадия…, FakeBot (+25 more)

### Community 56 - "FakeState"
Cohesion: 0.18
Nodes (4): Возможности, FakeMessage, FakeState, Any

### Community 57 - "devDependencies"
Cohesion: 0.40
Nodes (5): devDependencies, typescript, vite, @vitejs/plugin-vue, vue-tsc

### Community 58 - "Услуга «Обход белых списков» — реализация и порядок внедрения"
Cohesion: 0.20
Nodes (8): 1. Что получает пользователь, 2. Проверенный контракт 3x-ui, 3. Модель учёта, 5. Конкуренция и восстановление, 6. Порядок внедрения, 7. Откат, 9. Ограничения и решения, Услуга «Обход белых списков» — реализация и порядок внедрения

### Community 59 - "test_xui_updater.py"
Cohesion: 0.30
Nodes (10): pytest_httpx, test_stale_inbound_is_rejected_before_client_creation(), _mock_auth(), HTTPXMock, _server(), _spec(), test_legacy_provisioning_keeps_one_email_for_every_inbound(), test_provision_server_finds_client_by_sub_id() (+2 more)

### Community 60 - "answer"
Cohesion: 0.40
Nodes (6): answer(), edit(), Any, CallbackQuery, Безопасно редактирует сообщение callback'а. ``callback.message`` может быть…, Безопасно отправляет ответ в чат callback'а (если сообщение доступно).

### Community 61 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 62 - "parametrize"
Cohesion: 0.33
Nodes (6): _validate_subscription_base(), parametrize, test_settings_rejects_dangerous_numeric_values(), test_validate_server_name_rejects_invalid(), test_validate_subscription_base_accepts_url_and_clear_marker(), test_validate_subscription_base_rejects_invalid()

### Community 63 - "D VPN — личный кабинет"
Cohesion: 0.25
Nodes (7): D VPN — личный кабинет, Архитектура, Запуск вместе с существующим ботом, Локальная разработка, Результаты проверки, Что реализовано, Эксплуатация

### Community 71 - "test_ux.py"
Cohesion: 0.11
Nodes (26): _parse_server_line(), Парсит 'name|country|panel_url|username|password|[kind]|[sub]|[purpose]'.…, country_flag(), Эмодзи-флаг по ISO2-коду страны (напр. 'SE' -> 🇸🇪). Иначе пусто., Пробный доступен, если им не пользовались и подписку никогда не оформляли., _trial_available(), test_parse_server_line_accepts_valid(), test_parse_server_line_rejects_invalid() (+18 more)

### Community 72 - "MenuCallback"
Cohesion: 0.12
Nodes (27): MenuCallback, Навигация по inline-меню (редактирование сообщения на месте). action: home |…, custom_emoji_id(), Возвращает custom_emoji_id значка или None, если значок не найден., cancel_payment_keyboard(), connection_keyboard(), free_proxies_keyboard(), Главное меню под приветствием. Зависит от наличия активной подписки. (+19 more)

### Community 73 - "PendingRequestExists"
Cohesion: 0.33
Nodes (5): PaymentRequestError, PendingRequestExists, Exception, Заявку нельзя создать по бизнес-правилам., У пользователя уже есть заявка с отправленной квитанцией.

### Community 74 - "vpn_client"
Cohesion: 0.73
Nodes (6): admin(), AsyncSession, fixture, server(), user(), vpn_client()

### Community 75 - "XuiError"
Cohesion: 0.12
Nodes (13): list_panel_clients(), Возвращает список клиентов, уже существующих на панели сервера., Exception, Базовая ошибка взаимодействия с панелью 3x-ui., Создаёт нового клиента в inbound через addClient., Создаёт глобального клиента и привязывает его к inbound'ам (новый API)., XuiError, parametrize (+5 more)

### Community 76 - "check_servers"
Cohesion: 0.15
Nodes (8): check_server(), check_servers(), AsyncSession, Проверяет доступность панели 3x-ui одного сервера. Успешный login считается…, Проверяет все серверы и сохраняет результат в БД. Возвращает отображение…, Фоновые задачи, test_health_check_server_returns_true_on_success(), test_check_servers_saves_status()

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

### Community 84 - "delete_user_subscription"
Cohesion: 0.50
Nodes (5): _delete_local_subscription(), delete_user_subscription(), AsyncSession, Удаляет VPN-подписку пользователя с панелей и из БД бота. История оплат, заявки…, SubscriptionDeleteResult

### Community 85 - "Обновление production — 4 октября 2026"
Cohesion: 0.25
Nodes (6): PAY-1C3F1344, Внедрено, Дополнительный дефект, обнаруженный при приёмке, Незавершённые операции, Обновление production — 4 октября 2026, Проверки и резервирование

### Community 87 - "Настройка серверов и авто-провижининг"
Cohesion: 0.40
Nodes (5): Как формируется клиент, Настройка серверов и авто-провижининг, Перенос пользователей, существовавших до бота, Шаг 1. Добавить серверы, Шаг 2. Импортировать inbound'ы каждого сервера

### Community 88 - "MockPanelUpdater"
Cohesion: 0.15
Nodes (29): PaymentStatus, confirm_payment(), Идемпотентное подтверждение оплаты администратором. Повторный вызов для уже…, MockPanelUpdater, Mock-реализация: ничего не делает либо имитирует сбой нужных серверов. Для…, main(), confirm(), _make_waiting_payment() (+21 more)

### Community 89 - "Оставшиеся риски и решения"
Cohesion: 0.29
Nodes (7): P1/P2 — частичный успех внешней операции требует сверки, P1 — административные права зависят от тарифа, P1 — биллинг и панели не образуют одну транзакцию, P2 — мониторинг и производительность, P2 — старые ошибки оплат без ожидающих задач, P2 — эксплуатация и воспроизводимость, Оставшиеся риски и решения

### Community 90 - "ServerRepository"
Cohesion: 0.09
Nodes (9): Меняет только имя, сохраняя сервер и все его связи., Меняет URL подписки, не затрагивая связи сервера., Удаляет сервер вместе с inbound'ами и привязками (каскад). Коллекции грузим…, Включённые серверы. По умолчанию — только обычные (безлимитные)., Цели обычного provisioning: whitelist-сервер ведётся отдельно., Удаляет настроенный inbound. Возвращает число удалённых записей., Удаляет все настроенные inbound'ы сервера. Возвращает их число., Сохраняет результат фоновой проверки доступности сервера. (+1 more)

### Community 91 - "XuiClient"
Cohesion: 0.11
Nodes (13): Идентификатор для updateClient/{id}: id для vless/vmess, иначе email., Изолированный REST-клиент панели 3x-ui (MHSanaei/3x-ui). Принципы: - одна…, Обновляет клиента, сохраняя все его поля и меняя только нужные. Возвращает…, Устанавливает expiryTime (мс) и включает клиента., Лимит уникальных IP (0 = без лимита). Не считать точным лимитом устройств., Совместимый метод: продление через read-modify-write., Извлекает IP из вариантов ответа 3x-ui, не сохраняя метаданные лога., XuiClient (+5 more)

### Community 92 - "_FakeMessage"
Cohesion: 0.40
Nodes (3): _FakeBot, _FakeMessage, Any

### Community 93 - "callbacks.py"
Cohesion: 0.14
Nodes (18): aiogram_filters_callback_data, AdminCallback, BindCallback, OnboardCallback, PaymentCallback, PlanCallback, Callback админских действий над заявкой на привязку подписки., Callback выбора тарифа пользователем. code — код тарифа из PLANS (1m/6m/12m)… (+10 more)

### Community 94 - "collect_links"
Cohesion: 0.50
Nodes (4): collect_links(), AsyncSession, Возвращает список (метка, ссылка-подписка) по всем серверам пользователя. Для…, _sub_link()

### Community 95 - "FakeMessage"
Cohesion: 0.40
Nodes (3): FakeMessage, Заменитель Message: запоминает ответы., test_non_admin_admin_command_denied()

### Community 97 - "XuiAuthError"
Cohesion: 0.50
Nodes (4): Ошибка авторизации в панели., XuiAuthError, HTTPXMock, test_login_error_does_not_leak_password()

## Knowledge Gaps
- **165 isolated node(s):** `credentials`, `dvpn/site`, `name`, `version`, `private` (+160 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 695 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `provisioning.py`, `texts.py`, `admin_nav`, `test_legacy_bind.py`, `test_whitelist.py`, `user_handlers.py`, `admin_handlers.py`, `billing.py`, `PanelUpdater`, `models.py`, `test_review_regressions.py`, `test_whitelist_pg.py`, `config.py`, `whitelist.py`, `notify.py`, `utcnow`, `PaymentRequest`, `whitelist_admin`, `Settings`, `QuotaClientState`, `create_request`, `web_bridge.py`, `on_payment_action`, `operation_lock.py`, `VpnClient`, `test_ux.py`, `vpn_client`, `delete_user_subscription`, `MockPanelUpdater`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Why does `Server` connect `Server` to `provisioning.py`, `texts.py`, `test_legacy_bind.py`, `test_whitelist.py`, `admin_handlers.py`, `keyboards.py`, `XuiPanelUpdater`, `PanelUpdater`, `models.py`, `test_review_regressions.py`, `test_whitelist_pg.py`, `main.py`, `config.py`, `whitelist.py`, `utcnow`, `whitelist_admin`, `Settings`, `QuotaClientState`, `web_bridge.py`, `on_payment_action`, `Контекст проекта`, `EncryptedString`, `VpnClient`, `test_xui_updater.py`, `test_ux.py`, `vpn_client`, `XuiError`, `check_servers`, `delete_user_subscription`, `MockPanelUpdater`, `ServerRepository`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Why does `Settings` connect `Settings` to `admin_nav`, `test_whitelist.py`, `user_handlers.py`, `admin_handlers.py`, `User`, `models.py`, `test_review_regressions.py`, `main.py`, `config.py`, `notify.py`, `utcnow`, `test_access.py`, `whitelist_admin`, `create_request`, `web_bridge.py`, `on_payment_action`, `operation_lock.py`, `VpnClient`, `parametrize`, `test_ux.py`, `MockPanelUpdater`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Are the 161 inferred relationships involving `User` (e.g. with `admin_add_server_line()` and `admin_broadcast_send()`) actually correct?**
  _`User` has 161 INFERRED edges - model-reasoned connections that need verification._
- **Are the 87 inferred relationships involving `VpnClient` (e.g. with `notify_user_extended()` and `access_extended()`) actually correct?**
  _`VpnClient` has 87 INFERRED edges - model-reasoned connections that need verification._
- **Are the 48 inferred relationships involving `Server` (e.g. with `_finalize_new_server()` and `_finalize_whitelist_server()`) actually correct?**
  _`Server` has 48 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `Settings` (e.g. with `add_server()` and `admin_add_server_line()`) actually correct?**
  _`Settings` has 54 INFERRED edges - model-reasoned connections that need verification._
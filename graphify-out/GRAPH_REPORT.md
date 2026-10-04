# Graph Report - VpnBot  (2026-10-04)

## Corpus Check
- 123 files · ~71,586 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 17 file(s) not represented in the graph (top: (none) 9, .example 3, .conf 1)

## Summary
- 1747 nodes · 5563 edges · 97 communities (77 shown, 20 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 724 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `412612c0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- MockPanelUpdater
- tg
- texts.py
- test_legacy_bind.py
- UserRepository
- _activate_trial
- admin_handlers.py
- User
- keyboards.py
- Server
- PaymentStatus
- SubHubClient
- provisioning.py
- models.py
- collections_abc
- PendingServerUpdate
- user_handlers.py
- main.py
- main.go
- App.vue
- test_crypto.py
- web_smoke.py
- on_payment_action
- utcnow
- XuiClient
- What You Must Do When Invoked
- config.py
- test_xui_client.py
- .__call__
- test_review_regressions.py
- test_plans.py
- Settings
- Контекст проекта
- bind_user_by_public_id
- process_expiry_notifications
- test_web_bridge.py
- test_access.py
- connection_overview
- find_panel_client
- xui_client.py
- package.json
- Ревью VpnBot — 4 октября 2026
- compilerOptions
- main_test.go
- api
- Контекст проекта
- .auth
- send_broadcast
- import_inbounds
- app
- main
- Telegram VPN Billing Bot
- web_preview.mjs
- EncryptedString
- api.ts
- VpnClient
- test_expiry.py
- devDependencies
- scripts
- test_xui_updater.py
- AsyncSession
- graphify reference: extra exports and benchmark
- _parse_server_line
- D VPN — личный кабинет
- dvpn/site
- telegram-vpn-billing-bot
- test_ux.py
- _all_buttons
- test_health_check_server_returns_true_on_success
- MenuCallback
- test_health_check_server_returns_false_on_error
- check_servers
- graphify reference: query, path, explain
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- AGENTS.md
- ServerInbound
- Обновление production — 4 октября 2026
- extraction-spec.md
- menu_nav
- session
- Оставшиеся риски и решения
- .list_inbounds
- ._http
- _FakeMessage
- test_plan_callback_carries_only_code
- subscriptions.py
- .delete
- .set_status

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
- `Доменная модель` --references--> `PaymentStatus`  [INFERRED]
  context.md → app/db/enums.py
- `Доменная модель` --references--> `BindRequestStatus`  [INFERRED]
  context.md → app/db/enums.py
- `Доменная модель` --references--> `Protocol`  [INFERRED]
  context.md → app/db/enums.py
- `Provisioning в 3x-ui` --references--> `VpnClient`  [INFERRED]
  context.md → app/db/models.py
- `Интеграция с 3x-ui` --references--> `Server`  [INFERRED]
  context.md → app/db/models.py

## Import Cycles
- None detected.

## Communities (97 total, 20 thin omitted)

### Community 0 - "MockPanelUpdater"
Cohesion: 0.15
Nodes (26): MappingRepository, MockPanelUpdater, Mock-реализация: ничего не делает либо имитирует сбой нужных серверов., days_from_now(), _panel_info(), AsyncSession, HTTPXMock, Ссылка содержит subId, а в панели email другой — оба поля сохраняются. (+18 more)

### Community 1 - "tg"
Cohesion: 0.11
Nodes (23): HTML-строка с анимированным значком для вставки в текст сообщения., tg(), notify_user_bind_approved(), notify_user_expiry(), Уведомление пользователя об окончании подписки. True — если доставлено., access_extended(), admin_clients_list(), admin_history() (+15 more)

### Community 2 - "texts.py"
Cohesion: 0.07
Nodes (44): admin_nav(), _edit_panel(), ip_scan(), list_pending(), CallbackQuery, Редактирует сообщение админ-панели, мягко гасит ошибки. parse_mode=None —…, sharing_report(), admin_add_cancelled() (+36 more)

### Community 3 - "test_legacy_bind.py"
Cohesion: 0.08
Nodes (41): on_bind_action(), callback_query, notify_admins_bind_failed(), admin_bind_card(), BindRequestStatus, BindRequest, Заявка на привязку существующей подписки (до внедрения бота)., BindRequestRepository (+33 more)

### Community 4 - "UserRepository"
Cohesion: 0.15
Nodes (10): Удаляет пользователя и связанные записи (каскад в ORM)., Telegram ID всех пользователей, когда-либо запускавших бота., Генерирует короткий уникальный публичный ID пользователя., UserRepository, AsyncSession, test_all_telegram_ids_returns_every_user(), AsyncSession, test_backfills_public_id_for_existing() (+2 more)

### Community 5 - "_activate_trial"
Cohesion: 0.05
Nodes (57): aiogram_fsm_state, aiogram_methods, AdminStates, OnboardingStates, ProofStates, bind_request_received(), bind_request_waiting(), connection_unavailable() (+49 more)

### Community 6 - "admin_handlers.py"
Cohesion: 0.18
Nodes (35): aiogram_fsm_context, add_inbound(), add_server(), admin_add_server_cancel(), admin_add_server_line(), admin_broadcast_cancel(), admin_broadcast_send(), admin_delete_subscription_cancel() (+27 more)

### Community 7 - "User"
Cohesion: 0.07
Nodes (57): aiogram_filters, IsAdmin, TelegramObject, Пропускает событие только если пользователь — администратор., forward_proof_to_admins(), Приветствие. Использует HTML-разметку: ID завёрнут в <code> — Telegram копирует…, welcome(), _send_welcome() (+49 more)

### Community 8 - "keyboards.py"
Cohesion: 0.13
Nodes (32): aiogram_filters_callback_data, AdminCallback, BindCallback, OnboardCallback, PaymentCallback, PlanCallback, Callback админских действий над заявкой на привязку подписки., Callback выбора тарифа пользователем. code — код тарифа из PLANS (1m/6m/12m)… (+24 more)

### Community 9 - "Server"
Cohesion: 0.07
Nodes (24): ClientServerMapping, Server, Меняет только имя, сохраняя сервер и все его связи., MockIpProvider, Mock-провайдер для тестов: возвращает заранее заданные IP по server_id., PanelUpdateError, Exception, Ошибка обновления клиента в панели. (+16 more)

### Community 10 - "PaymentStatus"
Cohesion: 0.05
Nodes (89): PaymentStatus, PaymentRequest, PaymentRepository, Берёт заявку с блокировкой строки (SELECT ... FOR UPDATE). На Postgres…, Удаляет заявку (вместе с вложениями по каскаду)., Последняя успешная (применённая/подтверждённая) оплата пользователя.…, Any, AsyncSession (+81 more)

### Community 11 - "SubHubClient"
Cohesion: 0.09
Nodes (26): build_happ_import_url(), Exception, Base error for the internal SubHub integration., Resolve the first panel identity known to SubHub. Older bot records can have a…, The panels have not exposed this identity to SubHub yet., The identity exists, but currently has no active nodes., Build a signed HTTPS trampoline for importing a legacy subscription., Small authenticated client for the SubHub admin API. Subscription URLs and… (+18 more)

### Community 12 - "provisioning.py"
Cohesion: 0.15
Nodes (26): PanelUpdater, Интерфейс работы с клиентом в панели. Реализуется как mock (для тестов/MVP) и…, apply_access(), apply_access_to_server(), _build_spec(), client_email(), ensure_vpn_client(), _expiry_to_ms() (+18 more)

### Community 13 - "models.py"
Cohesion: 0.11
Nodes (33): Base, Базовый класс для всех ORM-моделей., TimestampMixin, AttachmentType, AuditLog, PaymentAttachment, WebSession, WebToken (+25 more)

### Community 15 - "PendingServerUpdate"
Cohesion: 0.20
Nodes (17): PendingServerUpdate, PendingServerUpdateRepository, apply_pending_for_server(), apply_pending_update(), _apply_to_server(), _as_aware(), _clear_payment_error_if_complete(), enqueue_failed_servers() (+9 more)

### Community 16 - "user_handlers.py"
Cohesion: 0.29
Nodes (8): aiogram, aiogram_exceptions, aiogram_types, app_bot, _needs_onboarding(), Показываем вопрос только новым пользователям без VPN-клиента., html, logging

### Community 17 - "main.py"
Cohesion: 0.09
Nodes (29): aiogram_client_default, aiogram_fsm_storage_memory, aiogram_utils_token, DbSessionMiddleware, Открывает сессию БД, получает/создаёт пользователя и кладёт их в data., build_root_router(), Настраивает логирование приложения. - корневой логгер: WARNING (чтобы сторонние…, setup_logging() (+21 more)

### Community 18 - "main.go"
Cohesion: 0.07
Nodes (29): credentials, go_pkg_bytes, go_pkg_context, go_pkg_crypto_hmac, go_pkg_crypto_rand, go_pkg_crypto_sha256, go_pkg_crypto_subtle, go_pkg_crypto_tls (+21 more)

### Community 19 - "App.vue"
Cohesion: 0.07
Nodes (24): authTitles, awaiting, busy, code, comment, config, connection, days (+16 more)

### Community 20 - "test_crypto.py"
Cohesion: 0.14
Nodes (23): decrypt(), encrypt(), _fernet(), is_encrypted(), Возвращает Fernet, выведенный из SECRET_KEY, либо None если ключ не задан.…, Шифрует строку. Без SECRET_KEY возвращает значение как есть (dev/тесты)., Расшифровывает строку. Legacy-значения в открытом виде возвращает как есть., cryptography_fernet (+15 more)

### Community 21 - "web_smoke.py"
Cohesion: 0.13
Nodes (13): aiohttp, Durable per-admin Telegram delivery, retried independently of HTTP requests., WebDelivery, delivery_loop(), Bot, queue(), contextlib, os (+5 more)

### Community 22 - "on_payment_action"
Cohesion: 0.15
Nodes (19): on_payment_action(), notify_admins_failed(), notify_admins_new_bind_request(), notify_admins_new_request(), notify_first_purchase_channel(), notify_user_bind_rejected(), notify_user_extended(), notify_user_rejected() (+11 more)

### Community 23 - "utcnow"
Cohesion: 0.14
Nodes (42): IpObservation, _active_clients(), collect_all(), collect_for_client(), compute_status(), _level_for(), list_all_statuses(), list_flagged() (+34 more)

### Community 24 - "XuiClient"
Cohesion: 0.07
Nodes (34): Any, Exception, Response, _quote_path_segment(), Авторизованный запрос: гарантирует login и при истёкшей сессии выполняет…, Берёт CSRF-токен с /csrf-token (3x-ui >= 3.2.x). На старых панелях endpoint…, Базовая ошибка взаимодействия с панелью 3x-ui., Возвращает список inbound'ов панели с их БД-id, портами и протоколами. (+26 more)

### Community 25 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 26 - "config.py"
Cohesion: 0.19
Nodes (14): get_settings(), app_db, get_engine(), get_session(), get_sessionmaker(), AsyncSession, do_run_migrations(), run_migrations_online() (+6 more)

### Community 27 - "test_xui_client.py"
Cohesion: 0.28
Nodes (23): _client(), _mock_csrf(), HTTPXMock, Регистрирует ответ /csrf-token (3x-ui 3.2.x запрашивает его перед login)., test_bearer_token_skips_login_and_csrf(), test_create_client_record(), test_del_client_quotes_identifier_path_segment(), test_find_client_by_sub_id() (+15 more)

### Community 28 - ".__call__"
Cohesion: 0.19
Nodes (16): _command_name(), _describe_callback(), _describe_event(), _describe_message(), Any, CallbackQuery, Message, TelegramObject (+8 more)

### Community 29 - "test_review_regressions.py"
Cohesion: 0.10
Nodes (39): Protocol, ProvisionTarget, Описание клиента, которого нужно создать/обновить в конкретном inbound., build_client_object(), client_identifier(), _client_uuid_for_api(), _looks_like_db_id(), merge_client_record_for_update() (+31 more)

### Community 30 - "test_plans.py"
Cohesion: 0.22
Nodes (6): get_plan(), PaymentPlan, Выгода относительно помесячной оплаты за тот же срок., test_get_plan(), test_plan_amounts_are_fixed_server_side(), test_unknown_or_forged_plan_code_rejected()

### Community 31 - "Settings"
Cohesion: 0.13
Nodes (19): admin_delete_subscription_by_client_id(), confirm_bind_cmd(), confirm_cmd(), _get_updater(), provision_user(), admin_provision_result(), Конфигурация приложения из переменных окружения / .env., Убирает пробелы и обрамляющие кавычки вокруг токена. (+11 more)

### Community 32 - "Контекст проекта"
Cohesion: 0.12
Nodes (16): API, Архитектура, Безопасность аутентификации (backend/main.go), Важные инженерные правила, Доменная модель (таблицы веб-части, в БД бота), Запуск, Контекст проекта, Конфигурация (+8 more)

### Community 33 - "bind_user_by_public_id"
Cohesion: 0.20
Nodes (18): bind_existing_client(), bind_user_by_public_id(), BindResult, _ensure_presence_mappings(), _finalize_bound_client(), find_client_presence_on_servers(), _public_id_taken(), AsyncSession (+10 more)

### Community 34 - "process_expiry_notifications"
Cohesion: 0.17
Nodes (13): _as_aware(), process_expiry_notifications(), AsyncSession, Bot, datetime, Стадия уведомления по остатку времени до окончания. 0 — рано, 1 — остался день,…, Шлёт уведомления «за день / за час / в момент окончания». Каждая стадия…, _target_stage() (+5 more)

### Community 35 - "test_web_bridge.py"
Cohesion: 0.16
Nodes (24): WebAccount, WebLinkRequest, decide_link(), has_purchase(), link_callback(), problem(), callback_query, CallbackQuery (+16 more)

### Community 36 - "test_access.py"
Cohesion: 0.44
Nodes (11): has_active_timed_client(), has_client_access(), has_unlimited_bound_client(), resolve_effective_role(), _mapping(), test_access_rejects_missing_client(), test_configured_admin_keeps_admin_role_without_client_access(), test_expired_client_has_no_access_or_auto_admin_role() (+3 more)

### Community 37 - "connection_overview"
Cohesion: 0.33
Nodes (6): connection_overview(), Unified SubHub connection screen with live server availability., server_button_label(), Флаг не добавляется автоматически — он уже в названии сервера., test_connection_overview_shows_server_availability(), test_server_button_label_has_no_autoflag()

### Community 38 - "find_panel_client"
Cohesion: 0.21
Nodes (12): find_panel_client(), _find_panel_client_by_sub_id(), _panel_client_secret(), PanelClientInfo, _pick_secret(), Нормализованные данные существующего клиента панели., Fallback для legacy API: первое непустое строковое значение., Ищет клиента панели по email и нормализует его поля. (+4 more)

### Community 39 - "xui_client.py"
Cohesion: 0.18
Nodes (7): Реальный провайдер: берёт IP клиента из журнала панели 3x-ui., XuiIpProvider, Ошибка авторизации в панели., XuiAuthError, ipaddress, HTTPXMock, test_login_error_does_not_leak_password()

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

### Community 48 - "import_inbounds"
Cohesion: 0.22
Nodes (6): import_inbounds(), Сверяет inbound'ы панели с локальными целями провижининга. Удалённые и…, _ss_method(), ReadOnlyPanel, test_import_network_failure_preserves_targets(), test_import_reconciles_deleted_disabled_and_new_inbounds()

### Community 49 - "app"
Cohesion: 0.29
Nodes (6): app, config, context.Context, github.com/jackc/pgx/v5/pgxpool.Pool, net/http.Client, pgx.Tx

### Community 50 - "main"
Cohesion: 0.22
Nodes (7): bucket, limiter, net/http.Handler, sync.Mutex, time.Time, env(), main()

### Community 51 - "Telegram VPN Billing Bot"
Cohesion: 0.10
Nodes (24): Telegram VPN Billing Bot, Админ-команды, Антишеринг-мониторинг, Возможности, Граф кода (graphify), Единая подписка SubHub, Запуск через Docker Compose, Как формируется клиент (+16 more)

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
Cohesion: 0.11
Nodes (30): _is_active(), VpnClient, datetime, Клиенты, которым пора слать уведомление об окончании. Берём тех, у кого задан…, _utcnow(), VpnClientRepository, _delete_local_subscription(), delete_user_subscription() (+22 more)

### Community 56 - "test_expiry.py"
Cohesion: 0.36
Nodes (7): FakeBot, AsyncSession, После продления (стадия сброшена в 0) уведомления идут заново., test_no_notification_when_far_from_expiry(), test_notifies_day_before_once(), test_progresses_through_stages(), test_stage_resets_allow_new_cycle()

### Community 57 - "devDependencies"
Cohesion: 0.40
Nodes (5): devDependencies, typescript, vite, @vitejs/plugin-vue, vue-tsc

### Community 58 - "scripts"
Cohesion: 0.50
Nodes (4): scripts, build, dev, preview

### Community 59 - "test_xui_updater.py"
Cohesion: 0.18
Nodes (13): ProvisionInbound, Inbound сервера, к которому нужно привязать клиента., pytest_httpx, test_attach_success_without_membership_is_not_provisioning_success(), test_stale_inbound_is_rejected_before_client_creation(), _mock_auth(), HTTPXMock, _server() (+5 more)

### Community 61 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 62 - "_parse_server_line"
Cohesion: 0.15
Nodes (13): _parse_server_line(), Парсит строку 'name|country|panel_url|username|password|[kind]|[sub]'.…, _validate_server_name(), _validate_subscription_base(), parametrize, test_parse_server_line_accepts_valid(), test_parse_server_line_rejects_invalid(), test_settings_rejects_dangerous_numeric_values() (+5 more)

### Community 63 - "D VPN — личный кабинет"
Cohesion: 0.25
Nodes (7): D VPN — личный кабинет, Архитектура, Запуск вместе с существующим ботом, Локальная разработка, Результаты проверки, Что реализовано, Эксплуатация

### Community 71 - "test_ux.py"
Cohesion: 0.13
Nodes (21): country_flag(), purchase_info(), Эмодзи-флаг по ISO2-коду страны (напр. 'SE' -> 🇸🇪). Иначе пусто., Экран «Оформить подписку»: цены и правила. parse_mode='HTML'., Пробный доступен, если им не пользовались и подписку никогда не оформляли., _trial_available(), _DummyState, AsyncSession (+13 more)

### Community 72 - "_all_buttons"
Cohesion: 0.16
Nodes (17): custom_emoji_id(), emoji_char(), Возвращает unicode-символ значка (без анимации)., Возвращает custom_emoji_id значка или None, если значок не найден., connection_keyboard(), One stable SubHub subscription link for every location and protocol., Главное меню под приветствием. Зависит от наличия активной подписки., welcome_menu() (+9 more)

### Community 74 - "MenuCallback"
Cohesion: 0.19
Nodes (13): MenuCallback, Навигация по inline-меню (редактирование сообщения на месте). action: home |…, admin_home_keyboard(), cancel_payment_keyboard(), Подтверждение сброса данных пользователя в боте., Кнопка «Отмена» под заявкой на оплату — удаляет заявку., reset_bot_confirm_keyboard(), test_menu_callback_actions_are_strings() (+5 more)

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

### Community 84 - "ServerInbound"
Cohesion: 0.33
Nodes (6): Inbound на панели сервера, в который нужно заводить клиентов. На одном сервере…, ServerInbound, test_ensure_inbounds_imported_imports_when_missing(), fake_import(), test_disabled_inbounds_are_not_bypassed_by_mapping_retry(), fake_import()

### Community 85 - "Обновление production — 4 октября 2026"
Cohesion: 0.29
Nodes (6): PAY-1C3F1344, Внедрено, Дополнительный дефект, обнаруженный при приёмке, Незавершённые операции, Обновление production — 4 октября 2026, Проверки и резервирование

### Community 87 - "menu_nav"
Cohesion: 0.15
Nodes (22): _back_button(), _btn(), extend_plans_keyboard(), free_proxies_keyboard(), install_guides_keyboard(), news_channel_keyboard(), _plan_label(), purchase_plans_keyboard() (+14 more)

### Community 88 - "session"
Cohesion: 0.33
Nodes (10): decorate(), wrapped(), user_operation(), check_released(), main(), confirm(), session(), test_user_operations_serialize_and_release_on_failure() (+2 more)

### Community 89 - "Оставшиеся риски и решения"
Cohesion: 0.29
Nodes (7): P1/P2 — частичный успех внешней операции требует сверки, P1 — административные права зависят от тарифа, P1 — биллинг и панели не образуют одну транзакцию, P2 — мониторинг и производительность, P2 — старые ошибки оплат без ожидающих задач, P2 — эксплуатация и воспроизводимость, Оставшиеся риски и решения

### Community 92 - "_FakeMessage"
Cohesion: 0.40
Nodes (3): _FakeBot, _FakeMessage, Any

### Community 94 - "subscriptions.py"
Cohesion: 0.50
Nodes (4): collect_links(), AsyncSession, Возвращает список (метка, ссылка-подписка) по всем серверам пользователя. Для…, _sub_link()

## Knowledge Gaps
- **152 isolated node(s):** `credentials`, `dvpn/site`, `name`, `version`, `private` (+147 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 594 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `MockPanelUpdater`, `tg`, `texts.py`, `test_legacy_bind.py`, `UserRepository`, `_activate_trial`, `admin_handlers.py`, `PaymentStatus`, `provisioning.py`, `models.py`, `PendingServerUpdate`, `user_handlers.py`, `web_smoke.py`, `on_payment_action`, `utcnow`, `test_plans.py`, `Settings`, `bind_user_by_public_id`, `test_web_bridge.py`, `find_panel_client`, `Telegram VPN Billing Bot`, `VpnClient`, `test_expiry.py`, `test_ux.py`, `menu_nav`, `session`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Why does `Server` connect `Server` to `MockPanelUpdater`, `texts.py`, `test_legacy_bind.py`, `admin_handlers.py`, `keyboards.py`, `PaymentStatus`, `provisioning.py`, `models.py`, `PendingServerUpdate`, `test_crypto.py`, `web_smoke.py`, `utcnow`, `What You Must Do When Invoked`, `bind_user_by_public_id`, `test_web_bridge.py`, `connection_overview`, `find_panel_client`, `xui_client.py`, `Контекст проекта`, `import_inbounds`, `Telegram VPN Billing Bot`, `EncryptedString`, `VpnClient`, `test_xui_updater.py`, `_parse_server_line`, `test_ux.py`, `check_servers`, `ServerInbound`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Why does `Settings` connect `Settings` to `texts.py`, `test_legacy_bind.py`, `_activate_trial`, `admin_handlers.py`, `User`, `models.py`, `user_handlers.py`, `main.py`, `test_crypto.py`, `web_smoke.py`, `on_payment_action`, `utcnow`, `config.py`, `test_review_regressions.py`, `test_web_bridge.py`, `test_access.py`, `VpnClient`, `_parse_server_line`, `test_ux.py`, `menu_nav`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Are the 145 inferred relationships involving `User` (e.g. with `admin_broadcast_send()` and `admin_delete_subscription_by_client_id()`) actually correct?**
  _`User` has 145 INFERRED edges - model-reasoned connections that need verification._
- **Are the 76 inferred relationships involving `VpnClient` (e.g. with `notify_user_extended()` and `access_extended()`) actually correct?**
  _`VpnClient` has 76 INFERRED edges - model-reasoned connections that need verification._
- **Are the 47 inferred relationships involving `Settings` (e.g. with `add_server()` and `admin_add_server_line()`) actually correct?**
  _`Settings` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `Server` (e.g. with `_finalize_new_server()` and `admin_server_keyboard()`) actually correct?**
  _`Server` has 33 INFERRED edges - model-reasoned connections that need verification._
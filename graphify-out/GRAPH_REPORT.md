# Graph Report - VpnBot  (2026-10-05)

## Corpus Check
- 156 files · ~141,588 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 17 file(s) not represented in the graph (top: (none) 9, .example 3, .conf 1)

## Summary
- 2662 nodes · 9412 edges · 125 communities (102 shown, 23 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1248 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6e82f662`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- provisioning.py
- test_provisioning.py
- whitelist.py
- repositories.py
- MockPanelUpdater
- user_handlers.py
- admin_handlers.py
- import_inbounds
- keyboards.py
- test_whitelist_reconcile.py
- billing.py
- test_subhub_trigger.py
- _btn
- models.py
- collections_abc
- ServerInbound
- test_whitelist_pg.py
- test_payment_kind_conflict.py
- main.go
- App.vue
- test_crypto.py
- main.py
- create_request
- antishare.py
- XuiClient
- ._clean_bot_token
- test_whitelist_bot.py
- test_broadcast.py
- .__call__
- Protocol
- reconcile_cycle
- User
- Контекст проекта
- XuiPanelUpdater
- PaymentStatus
- web_bridge.py
- tg
- test_whitelist_xui.py
- Server
- PaymentRequest
- package.json
- whitelist_e2e.py
- compilerOptions
- main_test.go
- api
- Контекст проекта
- .auth
- select_plan
- Задание агенту: услуга «Обход белых списков» в VpnBot
- app
- main
- test_antishare.py
- web_preview.mjs
- test_whitelist_inbound_compat.py
- AsyncSession
- What You Must Do When Invoked
- test_security.py
- record
- VpnClientRepository
- panel_updater.py
- whitelist_migration_check.py
- sync_inventory
- ref_node_fs_promises
- D VPN — личный кабинет
- texts.py
- test_xui_updater.py
- test_review_regressions.py
- test_set_volume_is_shown_as_entered
- dvpn/site
- telegram-vpn-billing-bot
- whitelist_admin
- _all_buttons
- Настройка серверов и авто-провижининг
- VpnClient
- test_all_inline_buttons_have_color_style
- notify.py
- AsyncSession
- whitelist_background_e2e.py
- MenuCallback
- IsAdmin
- EncryptedString
- test_subscription_delete.py
- AGENTS.md
- api.ts
- xui_client.py
- create_traffic_request
- UserRepository
- Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026
- _utcnow
- graphify reference: extra exports and benchmark
- FakeBot
- AdminCallback
- Протокол: R46 без принудительной синхронизации, фоновые циклы бота — 5 октября 2026
- utcnow
- Q: собери контекст проекта
- test_health_check_server_returns_true_on_success
- subscriptions.py
- pytest
- graphify reference: query, path, explain
- conftest.py
- .get_or_create
- test_health_check_server_returns_false_on_error
- devDependencies
- active_user
- whitelist_e2e_2026-10-05.md
- TelegramMock
- ServerRepository
- test_ux.py
- stack.sh
- whitelist_migration_2026-10-05.md
- scripts
- test_xui_client.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- ._http
- ReconcileOutcome
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- extraction-spec.md

## God Nodes (most connected - your core abstractions)
1. `User` - 268 edges
2. `VpnClient` - 146 edges
3. `Server` - 135 edges
4. `Settings` - 133 edges
5. `MockPanelUpdater` - 121 edges
6. `PaymentRequest` - 108 edges
7. `PaymentStatus` - 95 edges
8. `VpnClientRepository` - 86 edges
9. `XuiClient` - 77 edges
10. `Bot` - 69 edges

## Surprising Connections (you probably didn't know these)
- `6. Реальные 3x-ui и SubHub` --references--> `recover_confirmed_payments()`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → app/services/billing.py
- `Пользовательские сценарии` --references--> `decide_link()`  [INFERRED]
  VPNSite/context.md → app/services/web_bridge.py
- `Как формируется клиент` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py
- `Логика продления` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py
- `3.2. Купленный трафик` --references--> `on_payment_action()`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → app/bot/admin_handlers.py

## Import Cycles
- None detected.

## Communities (125 total, 23 thin omitted)

### Community 0 - "provisioning.py"
Cohesion: 0.12
Nodes (35): ProvisionInbound, Inbound сервера, к которому нужно привязать клиента., apply_access(), apply_access_to_server(), bind_existing_client(), BindResult, _build_spec(), client_email() (+27 more)

### Community 1 - "test_provisioning.py"
Cohesion: 0.10
Nodes (37): bind_user_by_public_id(), ensure_inbounds_imported(), ensure_vpn_client(), find_client_presence_on_servers(), has_targets(), Импортирует inbound'ы для включённых серверов, у которых их ещё нет. Нужно для…, Клиент найден на конкретном сервере., Ищет клиента по email или subId на всех включённых серверах. (+29 more)

### Community 2 - "whitelist.py"
Cohesion: 0.09
Nodes (47): Бизнес-учёт трафика пользователя на whitelist-сервере. Остатки…, Журнал выдач/начислений/корректировок, привязанных к исходной операции. Выдача…, WhitelistAccount, WhitelistLedger, QuotaClientState, Прочитанное с панели состояние клиента и его счётчика трафика., AccessState, admin_summary() (+39 more)

### Community 3 - "repositories.py"
Cohesion: 0.08
Nodes (41): BindRequestStatus, BindRequest, Заявка на привязку существующей подписки (до внедрения бота)., BindRequestRepository, approve_request(), BindApproveResult, BindRequestError, create_request() (+33 more)

### Community 4 - "MockPanelUpdater"
Cohesion: 0.06
Nodes (112): admin_payment_card(), payment_status_label(), MockPanelUpdater, datetime, Mock-реализация: ничего не делает либо имитирует сбой нужных серверов. Для…, AwaitingCredit, list_open_events(), process_due() (+104 more)

### Community 5 - "user_handlers.py"
Cohesion: 0.15
Nodes (33): aiogram_fsm_context, OnboardingStates, connection_unavailable(), onboarding_legacy_question(), onboarding_send_link_prompt(), Приветствие. Использует HTML-разметку: ID завёрнут в <code> — Telegram копирует…, welcome(), admin_denied() (+25 more)

### Community 6 - "admin_handlers.py"
Cohesion: 0.11
Nodes (63): add_inbound(), add_server(), admin_add_server_cancel(), admin_add_server_line(), admin_broadcast_cancel(), admin_broadcast_send(), admin_delete_subscription_by_client_id(), admin_delete_subscription_cancel() (+55 more)

### Community 7 - "import_inbounds"
Cohesion: 0.24
Nodes (11): fetch_inbounds(), import_inbounds(), Any, Сверяет inbound'ы панели с локальными целями провижининга. Удалённые и…, Читает список inbound'ов панели (``inbounds/list``) как есть., Сверка реестра с уже прочитанным списком (см. :func:`import_inbounds`)., reconcile_inbounds(), _ss_method() (+3 more)

### Community 8 - "keyboards.py"
Cohesion: 0.20
Nodes (22): _adm(), admin_add_server_type_keyboard(), admin_back_keyboard(), admin_confirm_delete_keyboard(), admin_servers_keyboard(), admin_whitelist_back_keyboard(), admin_whitelist_keyboard(), admin_whitelist_package_keyboard() (+14 more)

### Community 9 - "test_whitelist_reconcile.py"
Cohesion: 0.07
Nodes (45): Состояние и наблюдаемость фоновой сверки (хранится в памяти процесса).…, Сколько прошло с завершения последнего обхода без ошибок., Верхняя граница возраста данных учёта после последнего чистого обхода. Учёт мог…, Фоновая сверка расхода: обходит все учёты пачками по ``limit``. Возвращает…, reconcile_usage(), ReconcileStatus, _add_account(), _cycle() (+37 more)

### Community 10 - "billing.py"
Cohesion: 0.15
Nodes (34): _apply_panels(), _as_aware(), BillingError, BillingResult, compute_new_expiry(), _confirm_traffic(), _count_eligible_mappings(), _evaluate_panel_results() (+26 more)

### Community 11 - "test_subhub_trigger.py"
Cohesion: 0.06
Nodes (41): aiogram_filters, build_happ_import_url(), Exception, Resolve the first panel identity known to SubHub. Older bot records can have a…, Base error for the internal SubHub integration., The panels have not exposed this identity to SubHub yet., The identity exists, but currently has no active nodes., Build a signed HTTPS trampoline for importing a legacy subscription. (+33 more)

### Community 12 - "_btn"
Cohesion: 0.14
Nodes (21): _back_button(), _btn(), extend_plans_keyboard(), free_proxies_keyboard(), install_guides_keyboard(), news_channel_keyboard(), _plan_label(), purchase_plans_keyboard() (+13 more)

### Community 13 - "models.py"
Cohesion: 0.08
Nodes (45): get_settings(), app_db, Base, Базовый класс для всех ORM-моделей., TimestampMixin, AuditLog, WebSession, WebToken (+37 more)

### Community 15 - "ServerInbound"
Cohesion: 0.15
Nodes (24): PendingServerUpdate, Inbound на панели сервера, в который нужно заводить клиентов. На одном сервере…, ServerInbound, PendingServerUpdateRepository, apply_pending_for_server(), apply_pending_update(), _apply_to_server(), _as_aware() (+16 more)

### Community 16 - "test_whitelist_pg.py"
Cohesion: 0.06
Nodes (63): decorate(), wrapped(), user_operation(), get_account(), dict, 4. Автоматические тесты, 1. Что получает пользователь, 5. Конкуренция и восстановление (+55 more)

### Community 17 - "test_payment_kind_conflict.py"
Cohesion: 0.25
Nodes (20): aiogram_fsm_state, PlanCallback, Callback выбора тарифа пользователем. code — код тарифа из PLANS (1m/6m/12m)…, ProofStates, _open_count(), _package(), D-1: заявку с отправленной квитанцией нельзя превратить в заявку другого вида., _snapshot() (+12 more)

### Community 18 - "main.go"
Cohesion: 0.07
Nodes (29): credentials, go_pkg_bytes, go_pkg_context, go_pkg_crypto_hmac, go_pkg_crypto_rand, go_pkg_crypto_sha256, go_pkg_crypto_subtle, go_pkg_crypto_tls (+21 more)

### Community 19 - "App.vue"
Cohesion: 0.07
Nodes (24): authTitles, awaiting, busy, code, comment, config, connection, days (+16 more)

### Community 20 - "test_crypto.py"
Cohesion: 0.15
Nodes (21): decrypt(), encrypt(), _fernet(), is_encrypted(), Возвращает Fernet, выведенный из SECRET_KEY, либо None если ключ не задан.…, Шифрует строку. Без SECRET_KEY возвращает значение как есть (dev/тесты)., Расшифровывает строку. Legacy-значения в открытом виде возвращает как есть., cryptography_fernet (+13 more)

### Community 21 - "main.py"
Cohesion: 0.06
Nodes (47): aiogram, aiogram_client_default, aiogram_fsm_storage_memory, aiogram_types, aiogram_utils_token, app_bot, _command_name(), DbSessionMiddleware (+39 more)

### Community 22 - "create_request"
Cohesion: 0.18
Nodes (18): AttachmentType, attach_proof(), cancel_open_request(), create_request(), _open_request_for_update(), AsyncSession, Удаляет открытую заявку без квитанции; возвращает её код. Удаление условное:…, Прикрепляет подтверждение оплаты (текст/фото/документ) к заявке. (+10 more)

### Community 23 - "antishare.py"
Cohesion: 0.23
Nodes (22): IpObservation, _active_clients(), collect_all(), collect_for_client(), compute_status(), _level_for(), list_all_statuses(), list_flagged() (+14 more)

### Community 24 - "XuiClient"
Cohesion: 0.07
Nodes (34): Any, Exception, Response, _quote_path_segment(), Авторизованный запрос: гарантирует login и при истёкшей сессии выполняет…, Берёт CSRF-токен с /csrf-token (3x-ui >= 3.2.x). На старых панелях endpoint…, Базовая ошибка взаимодействия с панелью 3x-ui., Возвращает список inbound'ов панели с их БД-id, портами и протоколами. (+26 more)

### Community 25 - "._clean_bot_token"
Cohesion: 0.33
Nodes (3): Убирает пробелы и обрамляющие кавычки вокруг токена., Разрешает задавать ADMIN_TELEGRAM_IDS как строку '1,2,3' или одно число., field_validator

### Community 26 - "test_whitelist_bot.py"
Cohesion: 0.13
Nodes (19): Пользовательский раздел «Обход белых списков». action: home | refresh | buy…, WhitelistCallback, Step 7d - MCP server (only if --mcp flag), 8. Проверки, Возможности, FakeCallback, FakeMessage, FakeState (+11 more)

### Community 27 - "test_broadcast.py"
Cohesion: 0.19
Nodes (10): BroadcastResult, Рассылает текстовое сообщение всем пользователям. Сообщение отправляется…, send_broadcast(), FakeBot, AsyncSession, Текст рассылки шлётся без parse_mode — произвольный текст админа не должен…, test_all_telegram_ids_returns_every_user(), test_broadcast_text_is_plain_no_parse_mode() (+2 more)

### Community 28 - ".__call__"
Cohesion: 0.25
Nodes (13): _describe_callback(), _describe_event(), Any, CallbackQuery, TelegramObject, Chat, _private_chat(), test_describe_addserver_redacts_secrets() (+5 more)

### Community 29 - "Protocol"
Cohesion: 0.12
Nodes (32): Protocol, build_client_object(), client_identifier(), _client_uuid_for_api(), _looks_like_db_id(), merge_client_record_for_update(), pick_panel_client_secret(), Any (+24 more)

### Community 30 - "reconcile_cycle"
Cohesion: 0.17
Nodes (12): _BatchResult, _finish_reconcile(), Итог обхода учётов (накапливается между запусками, если обход прерывали).…, Следующая пачка учётов: стабильный курсор по id, а не по изменяемой метке., Читает пачку одной сессией панели и сверяет учёты по одному. Сбой одного учёта…, Один повторный проход по учётам, изменившимся между чтением и сверкой., Полный обход учётов whitelist-сервера ограниченными пачками. Пачки берутся по…, _reconcile_batch() (+4 more)

### Community 31 - "User"
Cohesion: 0.13
Nodes (12): Админ-раздел услуги «Обход белых списков». action: home | sync | choose (value…, WhitelistAdminCallback, notify_admins_bind_failed(), notify_admins_failed(), notify_admins_new_bind_request(), admin_bind_card(), User, Удаляет пользователя и связанные записи (каскад в ORM). (+4 more)

### Community 32 - "Контекст проекта"
Cohesion: 0.12
Nodes (15): Архитектура, Безопасность аутентификации (backend/main.go), Важные инженерные правила, Доменная модель (таблицы веб-части, в БД бота), Запуск, Контекст проекта, Конфигурация, Локальные артефакты (+7 more)

### Community 33 - "XuiPanelUpdater"
Cohesion: 0.15
Nodes (14): Один клиент панели (глобальный по email), привязанный к её inbound'ам.…, ServerProvision, build_client_record(), client_record_body(), Извлекает model.Client из ответа ``clients/get``., Унифицированный объект клиента для нового client-API (3x-ui >= 3.2.x).…, _is_missing_client_error(), Старые панели: отдельный клиент в каждом inbound (per-inbound email). (+6 more)

### Community 34 - "PaymentStatus"
Cohesion: 0.26
Nodes (20): PaymentStatus, confirm_payment(), Идемпотентное подтверждение оплаты администратором. Повторный вызов для уже…, _make_waiting_payment(), AsyncSession, test_confirm_applies_available_servers_and_queues_unavailable(), test_confirm_no_client_marks_failed(), test_confirm_payment_extends_expired() (+12 more)

### Community 35 - "web_bridge.py"
Cohesion: 0.07
Nodes (46): aiohttp, PaymentAttachment, Durable per-admin Telegram delivery, retried independently of HTTP requests., WebAccount, WebDelivery, WebLinkRequest, get_plan(), PaymentPlan (+38 more)

### Community 36 - "tg"
Cohesion: 0.10
Nodes (26): HTML-строка с анимированным значком для вставки в текст сообщения., tg(), access_extended(), access_update_pending(), admin_clients_list(), admin_whitelist_rollout_plan(), bind_request_approved(), connection_preparing() (+18 more)

### Community 37 - "test_whitelist_xui.py"
Cohesion: 0.29
Nodes (20): QuotaTarget, Абсолютное целевое состояние клиента с учётом трафика. ``total_bytes`` —…, 3.5. Учёт трафика и интеграция 3x-ui, _auth(), _body(), HTTPXMock, parametrize, HTTP-контракт клиента с квотой на 3x-ui (clients API >= 3.2). Сверено с… (+12 more)

### Community 38 - "Server"
Cohesion: 0.06
Nodes (40): connection_overview(), Unified SubHub connection screen with live server availability., server_button_label(), Server, Меняет только имя, сохраняя сервер и все его связи., Меняет URL подписки, не затрагивая связи сервера., check_server(), check_servers() (+32 more)

### Community 39 - "PaymentRequest"
Cohesion: 0.13
Nodes (11): PaymentRequest, PaymentRepository, Берёт заявку с блокировкой строки (SELECT ... FOR UPDATE). На Postgres…, Число применённых оплат подписки (покупки трафика не учитываются)., Удаляет заявку (вместе с вложениями по каскаду)., Последняя успешная (применённая/подтверждённая) оплата пользователя.…, _make_waiting(), AsyncSession (+3 more)

### Community 40 - "package.json"
Cohesion: 0.12
Nodes (14): lucide-vue-next, typescript, vite, @vitejs/plugin-vue, vue, vue-tsc, dependencies, lucide-vue-next (+6 more)

### Community 41 - "whitelist_e2e.py"
Cohesion: 0.05
Nodes (52): admin_servers(), Пакет покупки трафика «Обход белых списков» (настраивается админом)., TrafficPackage, whitelist_package_title(), argparse, 14. Исправление D-2: SubHub собирается без ручной установки greenlet (результаты от 2026-10-05, после приёмки), json, import_control_inbound() (+44 more)

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
Cohesion: 0.15
Nodes (12): Админские команды, Антишеринг, Доменная модель, Контекст проекта, Конфигурация, Локальные артефакты, Назначение, Основные пользовательские сценарии (+4 more)

### Community 46 - ".auth"
Cohesion: 0.53
Nodes (6): net/http.Request, net/http.ResponseWriter, decode(), digest(), fail(), respond()

### Community 47 - "select_plan"
Cohesion: 0.32
Nodes (13): answer_callback(), Отвечает на callback и игнорирует протухшие query-id после сетевых лагов., _activate_trial(), _edit(), callback_query, CallbackQuery, Редактирует текущее сообщение (без спама в чат). При сбое — отправляет новое., Прежняя заявка с квитанцией на проверке: новой не создаём, квитанций не ждём. (+5 more)

### Community 48 - "Задание агенту: услуга «Обход белых списков» в VpnBot"
Cohesion: 0.15
Nodes (12): 1. Контекст проекта, 2. Согласованное поведение услуги, 3. Сервер и настройки администратора, 4. Технический контракт учёта трафика, 5. Биллинг, конкуренция и восстановление, 6. Пользовательский интерфейс, 7. Обязательная проверка, 8. Порядок работы и сдача (+4 more)

### Community 49 - "app"
Cohesion: 0.29
Nodes (6): app, config, context.Context, github.com/jackc/pgx/v5/pgxpool.Pool, net/http.Client, pgx.Tx

### Community 50 - "main"
Cohesion: 0.22
Nodes (7): bucket, limiter, net/http.Handler, sync.Mutex, time.Time, env(), main()

### Community 51 - "test_antishare.py"
Cohesion: 0.27
Nodes (17): Сохраняет наблюдения IP. Возвращает число добавленных записей., record_ips(), MockIpProvider, Mock-провайдер для тестов: возвращает заранее заданные IP по server_id., _ips(), AsyncSession, _settings(), test_collect_for_client() (+9 more)

### Community 52 - "web_preview.mjs"
Cohesion: 0.29
Nodes (6): ref_node_fs, ref_node_http, ref_node_path, ref_node_url, root, types

### Community 53 - "test_whitelist_inbound_compat.py"
Cohesion: 0.15
Nodes (33): build_provision_spec(), get_active_server(), Включённый whitelist-сервер (не более одного по уникальному индексу)., server_ready(), target_inbound(), cryptography_hazmat_primitives, cryptography_hazmat_primitives_asymmetric_x25519, skipif (+25 more)

### Community 54 - "AsyncSession"
Cohesion: 0.11
Nodes (48): serialized_access(), access_state(), adjust_balance(), after_access_change(), _aware(), classify_origin(), confirm_traffic_payment(), _detect_external_disable() (+40 more)

### Community 55 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 56 - "test_security.py"
Cohesion: 0.05
Nodes (61): _parse_server_line(), Парсит 'name|country|panel_url|username|password|[kind]|[sub]|[purpose]'.…, forward_proof_to_admins(), UserRole, enum, pytest_httpx, FakeMessage, _make_payment() (+53 more)

### Community 57 - "record"
Cohesion: 0.11
Nodes (22): Единственная строка настроек услуги (id = 1)., WhitelistConfig, Any, AsyncSession, Записывает событие в audit_logs., record(), ensure_defaults(), get_config() (+14 more)

### Community 58 - "VpnClientRepository"
Cohesion: 0.27
Nodes (13): VpnClientRepository, grant_trial(), Выдаёт бесплатный пробный период один раз на аккаунт. Пробный период…, TrialResult, AsyncSession, Регресс: сервер добавлен, но inbound'ы не импортированы. Ранее триал отвечал…, test_grant_trial_success(), test_trial_auto_imports_inbounds_when_servers_added() (+5 more)

### Community 59 - "panel_updater.py"
Cohesion: 0.20
Nodes (11): ClientServerMapping, MappingRepository, ProvisionTarget, Описание клиента, которого нужно создать/обновить в конкретном inbound., ServerUpdateResult, _delete_local_subscription(), delete_user_subscription(), AsyncSession (+3 more)

### Community 60 - "whitelist_migration_check.py"
Cohesion: 0.25
Nodes (20): asyncpg, alembic(), check(), docker(), downgrade_cycle(), dsn(), ensure_defaults_idempotent(), main() (+12 more)

### Community 61 - "sync_inventory"
Cohesion: 0.15
Nodes (23): choose_inbound(), check_inbound(), _check_vless_reality(), describe(), _foreign_flows(), InboundCompat, _json(), _public_key_available() (+15 more)

### Community 63 - "D VPN — личный кабинет"
Cohesion: 0.25
Nodes (7): D VPN — личный кабинет, Архитектура, Запуск вместе с существующим ботом, Локальная разработка, Результаты проверки, Что реализовано, Эксплуатация

### Community 64 - "texts.py"
Cohesion: 0.06
Nodes (50): admin_nav(), _finalize_new_server(), _finalize_whitelist_server(), Сохраняет сервер и сразу пытается импортировать его inbound'ы. Так добавленный…, Добавляет сервер услуги и сразу сверяет его inbound'ы. До успешной сверки с…, admin_add_server_prompt(), admin_bind_pending(), admin_bind_result() (+42 more)

### Community 65 - "test_xui_updater.py"
Cohesion: 0.23
Nodes (8): test_attach_success_without_membership_is_not_provisioning_success(), _mock_auth(), HTTPXMock, _spec(), test_legacy_provisioning_keeps_one_email_for_every_inbound(), test_provision_server_finds_client_by_sub_id(), test_provision_server_new_api_creates(), test_provision_server_new_api_updates_existing()

### Community 66 - "test_review_regressions.py"
Cohesion: 0.20
Nodes (9): parametrize, ReadOnlyPanel, test_capability_failure_does_not_fall_back_to_legacy_writes(), test_client_read_failure_is_not_misreported_as_missing(), test_import_network_failure_preserves_targets(), test_import_reconciles_deleted_disabled_and_new_inbounds(), test_malformed_inbounds_is_not_treated_as_empty_panel(), test_stale_inbound_is_rejected_before_client_creation() (+1 more)

### Community 67 - "test_set_volume_is_shown_as_entered"
Cohesion: 0.11
Nodes (35): _parse_gb(), notify_user_traffic_credited(), admin_history(), admin_pending(), admin_whitelist_home(), admin_whitelist_packages(), admin_whitelist_user(), fmt_gb() (+27 more)

### Community 71 - "whitelist_admin"
Cohesion: 0.19
Nodes (13): _edit_panel(), on_payment_action(), callback_query, CallbackQuery, InlineKeyboardMarkup, Редактирует сообщение админ-панели, мягко гасит ошибки. parse_mode=None —…, whitelist_admin(), _whitelist_home() (+5 more)

### Community 72 - "_all_buttons"
Cohesion: 0.18
Nodes (18): custom_emoji_id(), Возвращает custom_emoji_id значка или None, если значок не найден., admin_home_keyboard(), connection_keyboard(), Главное меню под приветствием. Зависит от наличия активной подписки., One stable SubHub subscription link for every location and protocol., welcome_menu(), _all_buttons() (+10 more)

### Community 73 - "Настройка серверов и авто-провижининг"
Cohesion: 0.33
Nodes (6): Как формируется клиент, Настройка серверов и авто-провижининг, Перенос пользователей, существовавших до бота, Шаг 1. Добавить серверы, Шаг 2. Импортировать inbound'ы каждого сервера, hysteria()

### Community 74 - "VpnClient"
Cohesion: 0.34
Nodes (16): _is_active(), VpnClient, has_active_timed_client(), has_client_access(), has_unlimited_bound_client(), resolve_effective_role(), _mapping(), test_access_rejects_missing_client() (+8 more)

### Community 75 - "test_all_inline_buttons_have_color_style"
Cohesion: 0.19
Nodes (14): BindCallback, OnboardCallback, PaymentCallback, Callback админских действий над заявкой на привязку подписки., Онбординг: был ли пользователь клиентом до внедрения бота., Callback админских действий над заявкой., admin_bind_keyboard(), admin_bind_retry_keyboard() (+6 more)

### Community 76 - "notify.py"
Cohesion: 0.10
Nodes (24): notify_admins_new_request(), notify_first_purchase_channel(), notify_user_bind_approved(), notify_user_bind_rejected(), notify_user_expiry(), notify_user_extended(), notify_user_rejected(), notify_user_subscription_deleted() (+16 more)

### Community 78 - "whitelist_background_e2e.py"
Cohesion: 0.07
Nodes (42): BaseException, 15. Лимит трафика 3x-ui → SubHub: единица `totalGB` и источник расхода (результаты от 2026-10-05, после приёмки), 2. Проверенный контракт 3x-ui, Acts, _async(), describe(), DiesOnFirstChange, die() (+34 more)

### Community 79 - "MenuCallback"
Cohesion: 0.24
Nodes (10): aiogram_filters_callback_data, MenuCallback, Навигация по inline-меню (редактирование сообщения на месте). action: home |…, cancel_payment_keyboard(), Подтверждение сброса данных пользователя в боте., Кнопка «Отмена» под заявкой на оплату — удаляет заявку., reset_bot_confirm_keyboard(), _all_buttons() (+2 more)

### Community 80 - "IsAdmin"
Cohesion: 0.21
Nodes (10): IsAdmin, TelegramObject, Пропускает событие только если пользователь — администратор., BaseFilter, test_is_admin_filter_accepts_admin(), test_is_admin_filter_rejects_missing_user(), test_is_admin_filter_rejects_regular_user(), test_settings_is_admin() (+2 more)

### Community 81 - "EncryptedString"
Cohesion: 0.06
Nodes (28): EncryptedString, Any, Прозрачно шифрует значение при записи и расшифровывает при чтении. - Если…, Важные инженерные правила проекта, PAY-1C3F1344, Внедрено, Дополнительный дефект, обнаруженный при приёмке, Незавершённые операции (+20 more)

### Community 82 - "test_subscription_delete.py"
Cohesion: 0.23
Nodes (9): _FakeBot, _FakeMessage, _FakeState, Any, AsyncSession, test_admin_delete_subscription_uses_client_id_not_telegram_id(), test_delete_subscription_keeps_local_client_on_panel_failure(), test_delete_subscription_removes_panel_and_local_client() (+1 more)

### Community 84 - "api.ts"
Cohesion: 0.33
Nodes (4): APIError, Configuration, Plan, Profile

### Community 85 - "xui_client.py"
Cohesion: 0.18
Nodes (8): build_ip_provider(), Реальный провайдер: берёт IP клиента из журнала панели 3x-ui., XuiIpProvider, Ошибка авторизации в панели., XuiAuthError, ipaddress, HTTPXMock, test_login_error_does_not_leak_password()

### Community 86 - "create_traffic_request"
Cohesion: 0.22
Nodes (10): create_traffic_request(), _new_payment_code(), PaymentRequestError, PendingRequestExists, datetime, Exception, Заявка на покупку пакета «Обход белых списков». Создаётся только при активной…, Заявку нельзя создать по бизнес-правилам. (+2 more)

### Community 87 - "UserRepository"
Cohesion: 0.36
Nodes (6): Telegram ID всех пользователей, когда-либо запускавших бота., UserRepository, AsyncSession, test_backfills_public_id_for_existing(), test_get_or_create_assigns_public_id(), test_public_id_is_stable_and_unique()

### Community 88 - "Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026"
Cohesion: 0.50
Nodes (3): Прогон до исправления (SubHub `d9a2c80` + незакоммиченные правки, не относящиеся к задаче), Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026, Финальный прогон после исправления

### Community 89 - "_utcnow"
Cohesion: 0.25
Nodes (4): datetime, Клиенты, которым пора слать уведомление об окончании. Берём тех, у кого задан…, Сохраняет результат фоновой проверки доступности сервера., _utcnow()

### Community 90 - "graphify reference: extra exports and benchmark"
Cohesion: 0.25
Nodes (7): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 92 - "AdminCallback"
Cohesion: 0.40
Nodes (5): AdminCallback, Навигация по админ-панели (/admin). action: home | servers | server | rename |…, admin_server_keyboard(), Управление конкретным сервером., test_admin_server_keyboard_toggle_label()

### Community 93 - "Протокол: R46 без принудительной синхронизации, фоновые циклы бота — 5 октября 2026"
Cohesion: 0.40
Nodes (4): Прогон 1 — до исправлений (бот и SubHub без изменений этой задачи), Прогон 2 — SubHub исправлен (D-6), бот: исправлен D-5, исправления D-7 и D-8 временно сняты, Прогон 3 — финальный, все исправления, Протокол: R46 без принудительной синхронизации, фоновые циклы бота — 5 октября 2026

### Community 94 - "utcnow"
Cohesion: 0.15
Nodes (21): _as_aware(), process_expiry_notifications(), AsyncSession, datetime, Стадия уведомления по остатку времени до окончания. 0 — рано, 1 — остался день,…, Шлёт уведомления «за день / за час / в момент окончания». Каждая стадия…, _target_stage(), utcnow() (+13 more)

### Community 95 - "Q: собери контекст проекта"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: собери контекст проекта, Source Nodes

### Community 97 - "subscriptions.py"
Cohesion: 0.50
Nodes (4): collect_links(), AsyncSession, Возвращает список (метка, ссылка-подписка) по всем серверам пользователя. Для…, _sub_link()

### Community 98 - "pytest"
Cohesion: 0.15
Nodes (15): aiogram_exceptions, aiogram_methods, answer(), edit(), Any, CallbackQuery, Безопасно редактирует сообщение callback'а. ``callback.message`` может быть…, Безопасно отправляет ответ в чат callback'а (если сообщение доступно). (+7 more)

### Community 99 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 100 - "conftest.py"
Cohesion: 0.47
Nodes (8): pytest_asyncio, admin(), AsyncSession, datetime, fixture, server(), user(), vpn_client()

### Community 103 - "devDependencies"
Cohesion: 0.40
Nodes (5): devDependencies, typescript, vite, @vitejs/plugin-vue, vue-tsc

### Community 104 - "active_user"
Cohesion: 0.50
Nodes (4): active_user(), panel(), fixture, Пользователь с оплаченной подпиской: покупка трафика доступна.

### Community 107 - "ServerRepository"
Cohesion: 0.14
Nodes (6): Удаляет сервер вместе с inbound'ами и привязками (каскад). Коллекции грузим…, Включённые серверы. По умолчанию — только обычные (безлимитные)., Цели обычного provisioning: whitelist-сервер ведётся отдельно., Удаляет настроенный inbound. Возвращает число удалённых записей., Удаляет все настроенные inbound'ы сервера. Возвращает их число., ServerRepository

### Community 108 - "test_ux.py"
Cohesion: 0.12
Nodes (21): emoji_char(), Возвращает unicode-символ значка (без анимации)., country_flag(), Эмодзи-флаг по ISO2-коду страны (напр. 'SE' -> 🇸🇪). Иначе пусто., Пробный доступен, если им не пользовались и подписку никогда не оформляли., _trial_available(), _DummyState, AsyncSession (+13 more)

### Community 109 - "stack.sh"
Cohesion: 0.57
Nodes (5): running(), stack.sh script, start_panel(), start_subhub(), subhub_config()

### Community 111 - "scripts"
Cohesion: 0.50
Nodes (4): scripts, build, dev, preview

### Community 112 - "test_xui_client.py"
Cohesion: 0.28
Nodes (23): _client(), _mock_csrf(), HTTPXMock, Регистрирует ответ /csrf-token (3x-ui 3.2.x запрашивает его перед login)., test_bearer_token_skips_login_and_csrf(), test_create_client_record(), test_del_client_quotes_identifier_path_segment(), test_find_client_by_sub_id() (+15 more)

### Community 113 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 114 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 115 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **174 isolated node(s):** `credentials`, `dvpn/site`, `name`, `version`, `private` (+169 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 855 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `provisioning.py`, `test_provisioning.py`, `whitelist.py`, `repositories.py`, `MockPanelUpdater`, `user_handlers.py`, `admin_handlers.py`, `test_whitelist_reconcile.py`, `billing.py`, `models.py`, `ServerInbound`, `test_whitelist_pg.py`, `create_request`, `test_broadcast.py`, `PaymentStatus`, `web_bridge.py`, `PaymentRequest`, `whitelist_e2e.py`, `select_plan`, `test_antishare.py`, `AsyncSession`, `test_security.py`, `VpnClientRepository`, `panel_updater.py`, `texts.py`, `test_set_volume_is_shown_as_entered`, `whitelist_admin`, `VpnClient`, `notify.py`, `whitelist_background_e2e.py`, `MenuCallback`, `IsAdmin`, `test_subscription_delete.py`, `create_traffic_request`, `UserRepository`, `utcnow`, `conftest.py`, `.get_or_create`, `test_ux.py`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._
- **Why does `Server` connect `Server` to `provisioning.py`, `test_provisioning.py`, `whitelist.py`, `repositories.py`, `MockPanelUpdater`, `admin_handlers.py`, `import_inbounds`, `keyboards.py`, `test_whitelist_reconcile.py`, `models.py`, `ServerInbound`, `test_whitelist_pg.py`, `test_crypto.py`, `antishare.py`, `test_whitelist_bot.py`, `reconcile_cycle`, `XuiPanelUpdater`, `PaymentStatus`, `web_bridge.py`, `test_whitelist_xui.py`, `test_antishare.py`, `test_whitelist_inbound_compat.py`, `What You Must Do When Invoked`, `test_security.py`, `VpnClientRepository`, `panel_updater.py`, `sync_inventory`, `texts.py`, `test_xui_updater.py`, `whitelist_admin`, `test_all_inline_buttons_have_color_style`, `EncryptedString`, `xui_client.py`, `AdminCallback`, `conftest.py`, `ServerRepository`, `test_ux.py`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `Settings` connect `admin_handlers.py` to `MockPanelUpdater`, `user_handlers.py`, `test_subhub_trigger.py`, `models.py`, `test_payment_kind_conflict.py`, `test_crypto.py`, `main.py`, `antishare.py`, `._clean_bot_token`, `test_whitelist_bot.py`, `test_broadcast.py`, `User`, `web_bridge.py`, `whitelist_e2e.py`, `select_plan`, `test_antishare.py`, `test_whitelist_inbound_compat.py`, `test_security.py`, `texts.py`, `test_review_regressions.py`, `whitelist_admin`, `VpnClient`, `notify.py`, `IsAdmin`, `test_subscription_delete.py`, `test_ux.py`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 167 inferred relationships involving `User` (e.g. with `admin_add_server_line()` and `admin_broadcast_send()`) actually correct?**
  _`User` has 167 INFERRED edges - model-reasoned connections that need verification._
- **Are the 90 inferred relationships involving `VpnClient` (e.g. with `notify_user_extended()` and `access_extended()`) actually correct?**
  _`VpnClient` has 90 INFERRED edges - model-reasoned connections that need verification._
- **Are the 52 inferred relationships involving `Server` (e.g. with `_finalize_new_server()` and `_finalize_whitelist_server()`) actually correct?**
  _`Server` has 52 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `Settings` (e.g. with `add_server()` and `admin_add_server_line()`) actually correct?**
  _`Settings` has 59 INFERRED edges - model-reasoned connections that need verification._
# Graph Report - VpnBot  (2026-10-05)

## Corpus Check
- 135 files · ~101,493 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 17 file(s) not represented in the graph (top: (none) 9, .example 3, .conf 1)

## Summary
- 2198 nodes · 7657 edges · 113 communities (96 shown, 17 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 976 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `81e37358`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- provisioning.py
- texts.py
- WhitelistLedger
- notify.py
- test_whitelist.py
- user_handlers.py
- admin_handlers.py
- admin_rename_server_name
- keyboards.py
- XuiPanelUpdater
- billing.py
- SubHubClient
- test_provisioning.py
- repositories.py
- alembic
- pending_updates.py
- test_whitelist_pg.py
- main.py
- main.go
- App.vue
- config.py
- AsyncSession
- admin_nav
- utcnow
- XuiError
- What You Must Do When Invoked
- User
- test_xui_client.py
- middlewares.py
- Protocol
- record
- ._clean_bot_token
- Контекст проекта
- IsAdmin
- MockPanelUpdater
- web_smoke.py
- ServerRepository
- test_whitelist_xui.py
- PanelUpdater
- test_whitelist_payment_status.py
- package.json
- Ревью VpnBot — 4 октября 2026
- compilerOptions
- main_test.go
- api
- Контекст проекта
- .auth
- test_broadcast.py
- Задание агенту: услуга «Обход белых списков» в VpnBot
- app
- main
- Telegram VPN Billing Bot
- web_preview.mjs
- EncryptedString
- api.ts
- VpnClient
- test_security.py
- test_notify_swallows_telegram_api_errors
- Услуга «Обход белых списков» — реализация и порядок внедрения
- user_overview
- QuotaClientState
- graphify reference: extra exports and benchmark
- ._api
- D VPN — личный кабинет
- dvpn/site
- telegram-vpn-billing-bot
- test_xui_updater.py
- test_ux.py
- test_reset_confirm_keyboard
- web_bridge.py
- test_health_check_server_returns_false_on_error
- UserRole
- graphify reference: query, path, explain
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- AGENTS.md
- bind_user_by_public_id
- Обновление production — 4 октября 2026
- extraction-spec.md
- vpn_client
- PaymentRequest
- Оставшиеся риски и решения
- Server
- PanelUpdateError
- test_subscription_delete.py
- test_whitelist_bot.py
- ServerInbound
- whitelist.py
- panel
- callbacks.py
- test_ui.py
- FSMContext
- models.py
- _whitelist_home
- check_servers
- devDependencies
- XuiClient
- test_payment_requests.py
- reconcile_usage
- FakeMessage
- xui_client.py
- test_payment_code_wrapped_in_code_tag
- test_create_request_with_plan
- test_broadcast_text_is_plain_no_parse_mode
- provision_server

## God Nodes (most connected - your core abstractions)
1. `User` - 237 edges
2. `VpnClient` - 140 edges
3. `Server` - 125 edges
4. `Settings` - 119 edges
5. `MockPanelUpdater` - 106 edges
6. `PaymentRequest` - 84 edges
7. `PaymentStatus` - 81 edges
8. `VpnClientRepository` - 78 edges
9. `XuiClient` - 74 edges
10. `ServerRepository` - 63 edges

## Surprising Connections (you probably didn't know these)
- `Логика продления` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py
- `Step 7d - MCP server (only if --mcp flag)` --references--> `command()`  [INFERRED]
  .codex/skills/graphify/references/exports.md → tests/test_whitelist_bot.py
- `3. Модель учёта` --references--> `payment_status_label()`  [INFERRED]
  docs/WHITELIST_SERVICE.md → app/bot/texts.py
- `Доменная модель` --references--> `PaymentStatus`  [INFERRED]
  context.md → app/db/enums.py
- `Доменная модель` --references--> `BindRequestStatus`  [INFERRED]
  context.md → app/db/enums.py

## Import Cycles
- None detected.

## Communities (113 total, 17 thin omitted)

### Community 0 - "provisioning.py"
Cohesion: 0.15
Nodes (27): ServerUpdateResult, apply_access(), apply_access_to_server(), build_provision_spec(), _build_spec(), client_email(), client_identity(), ensure_vpn_client() (+19 more)

### Community 1 - "texts.py"
Cohesion: 0.05
Nodes (62): HTML-строка с анимированным значком для вставки в текст сообщения., tg(), notify_user_traffic_credited(), access_extended(), access_update_pending(), admin_bind_result(), admin_broadcast_result(), admin_clients_list() (+54 more)

### Community 2 - "WhitelistLedger"
Cohesion: 0.11
Nodes (32): Бизнес-учёт трафика пользователя на whitelist-сервере. Остатки…, Журнал выдач/начислений/корректировок, привязанных к исходной операции. Выдача…, WhitelistAccount, WhitelistLedger, AccessState, _append_note(), _applied_target(), apply_event() (+24 more)

### Community 3 - "notify.py"
Cohesion: 0.05
Nodes (59): confirm_bind_cmd(), on_bind_action(), forward_proof_to_admins(), notify_admins_bind_failed(), notify_admins_failed(), notify_admins_new_bind_request(), notify_admins_new_request(), notify_first_purchase_channel() (+51 more)

### Community 4 - "test_whitelist.py"
Cohesion: 0.12
Nodes (61): list_open_events(), process_due(), Фоновая очередь: применяет несинхронизированные состояния с backoff., Неприменённые события учёта пользователя в порядке возникновения., _account(), _ago(), _baseline(), _buy() (+53 more)

### Community 5 - "user_handlers.py"
Cohesion: 0.10
Nodes (51): aiogram_exceptions, aiogram_filters, aiogram_fsm_context, aiogram_fsm_state, aiogram_types, back_keyboard(), Клавиатура с единственной кнопкой «Назад» на указанный экран., AdminStates (+43 more)

### Community 6 - "admin_handlers.py"
Cohesion: 0.17
Nodes (40): add_inbound(), add_server(), admin_broadcast_send(), admin_delete_subscription_by_client_id(), admin_panel(), _after_applied_payment(), bind_panel_client(), clear_inbounds() (+32 more)

### Community 7 - "admin_rename_server_name"
Cohesion: 0.13
Nodes (16): admin_rename_server_name(), admin_subscription_url_value(), _parse_server_line(), Парсит 'name|country|panel_url|username|password|[kind]|[sub]|[purpose]'.…, _validate_server_name(), _validate_subscription_base(), admin_server_detail(), server_purpose_label() (+8 more)

### Community 8 - "keyboards.py"
Cohesion: 0.11
Nodes (53): _adm(), admin_add_server_type_keyboard(), admin_back_keyboard(), admin_bind_keyboard(), admin_bind_retry_keyboard(), admin_confirm_delete_keyboard(), admin_home_keyboard(), admin_payment_keyboard() (+45 more)

### Community 9 - "XuiPanelUpdater"
Cohesion: 0.15
Nodes (14): Один клиент панели (глобальный по email), привязанный к её inbound'ам.…, ServerProvision, build_client_record(), client_record_body(), Извлекает model.Client из ответа ``clients/get``., Унифицированный объект клиента для нового client-API (3x-ui >= 3.2.x).…, _is_missing_client_error(), Старые панели: отдельный клиент в каждом inbound (per-inbound email). (+6 more)

### Community 10 - "billing.py"
Cohesion: 0.19
Nodes (24): _apply_panels(), _as_aware(), BillingResult, compute_new_expiry(), _confirm_traffic(), _count_eligible_mappings(), _evaluate_panel_results(), expiry_to_ms() (+16 more)

### Community 11 - "SubHubClient"
Cohesion: 0.10
Nodes (23): build_happ_import_url(), Exception, Base error for the internal SubHub integration., Resolve the first panel identity known to SubHub. Older bot records can have a…, The panels have not exposed this identity to SubHub yet., The identity exists, but currently has no active nodes., Build a signed HTTPS trampoline for importing a legacy subscription., Small authenticated client for the SubHub admin API. Subscription URLs and… (+15 more)

### Community 12 - "test_provisioning.py"
Cohesion: 0.15
Nodes (24): MappingRepository, days_from_now(), _panel_info(), AsyncSession, HTTPXMock, Ссылка содержит subId, а в панели email другой — оба поля сохраняются., _server_with_inbounds(), test_apply_access_creates_clients_and_mappings() (+16 more)

### Community 13 - "repositories.py"
Cohesion: 0.11
Nodes (18): AuditLog, AuditRepository, app_services, ProvisionTarget, Описание клиента, которого нужно создать/обновить в конкретном inbound., collect_links(), AsyncSession, Возвращает список (метка, ссылка-подписка) по всем серверам пользователя. Для… (+10 more)

### Community 15 - "pending_updates.py"
Cohesion: 0.29
Nodes (14): PendingServerUpdate, PendingServerUpdateRepository, apply_pending_for_server(), apply_pending_update(), _apply_to_server(), _as_aware(), _clear_payment_error_if_complete(), enqueue_failed_servers() (+6 more)

### Community 16 - "test_whitelist_pg.py"
Cohesion: 0.15
Nodes (26): AttachmentType, attach_proof(), Прикрепляет подтверждение оплаты (текст/фото/документ) к заявке., dict, str, session(), _confirm(), _NoLocalLocks (+18 more)

### Community 17 - "main.py"
Cohesion: 0.12
Nodes (22): aiogram, aiogram_client_default, aiogram_fsm_storage_memory, aiogram_utils_token, build_root_router(), Настраивает логирование приложения. - корневой логгер: WARNING (чтобы сторонние…, setup_logging(), _anti_sharing_poller() (+14 more)

### Community 18 - "main.go"
Cohesion: 0.07
Nodes (29): credentials, go_pkg_bytes, go_pkg_context, go_pkg_crypto_hmac, go_pkg_crypto_rand, go_pkg_crypto_sha256, go_pkg_crypto_subtle, go_pkg_crypto_tls (+21 more)

### Community 19 - "App.vue"
Cohesion: 0.07
Nodes (24): authTitles, awaiting, busy, code, comment, config, connection, days (+16 more)

### Community 20 - "config.py"
Cohesion: 0.11
Nodes (33): get_settings(), decrypt(), encrypt(), _fernet(), is_encrypted(), Возвращает Fernet, выведенный из SECRET_KEY, либо None если ключ не задан.…, Шифрует строку. Без SECRET_KEY возвращает значение как есть (dev/тесты)., Расшифровывает строку. Legacy-значения в открытом виде возвращает как есть. (+25 more)

### Community 21 - "AsyncSession"
Cohesion: 0.19
Nodes (26): access_state(), _aware(), classify_origin(), confirm_traffic_payment(), forget_panel_client(), grant_for_subscription_payment(), grant_for_trial(), _ledger_exists() (+18 more)

### Community 22 - "admin_nav"
Cohesion: 0.09
Nodes (24): admin_nav(), _edit_panel(), list_pending(), callback_query, CallbackQuery, Редактирует сообщение админ-панели, мягко гасит ошибки. parse_mode=None —…, admin_add_server_prompt(), admin_bind_pending() (+16 more)

### Community 23 - "utcnow"
Cohesion: 0.16
Nodes (39): IpObservation, _active_clients(), collect_all(), collect_for_client(), compute_status(), _level_for(), list_all_statuses(), list_flagged() (+31 more)

### Community 24 - "XuiError"
Cohesion: 0.11
Nodes (19): Any, Exception, _quote_path_segment(), Базовая ошибка взаимодействия с панелью 3x-ui., Возвращает список inbound'ов панели с их БД-id, портами и протоколами., Ищет клиента в inbound по uuid, email или subId (стабильные ID)., Совместимый алиас find_client (по uuid/email)., Удаляет клиента из inbound. (+11 more)

### Community 25 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 26 - "User"
Cohesion: 0.12
Nodes (27): User, Удаляет пользователя и связанные записи (каскад в ORM)., Telegram ID всех пользователей, когда-либо запускавших бота., Генерирует короткий уникальный публичный ID пользователя., UserRepository, grant_trial(), Выдаёт бесплатный пробный период один раз на аккаунт. Пробный период…, TrialResult (+19 more)

### Community 27 - "test_xui_client.py"
Cohesion: 0.28
Nodes (23): _client(), _mock_csrf(), HTTPXMock, Регистрирует ответ /csrf-token (3x-ui 3.2.x запрашивает его перед login)., test_bearer_token_skips_login_and_csrf(), test_create_client_record(), test_del_client_quotes_identifier_path_segment(), test_find_client_by_sub_id() (+15 more)

### Community 28 - "middlewares.py"
Cohesion: 0.16
Nodes (19): _command_name(), DbSessionMiddleware, _describe_callback(), _describe_event(), _describe_message(), Any, CallbackQuery, Message (+11 more)

### Community 29 - "Protocol"
Cohesion: 0.11
Nodes (37): Protocol, build_client_object(), client_identifier(), _client_uuid_for_api(), _looks_like_db_id(), merge_client_record_for_update(), pick_panel_client_secret(), Any (+29 more)

### Community 30 - "record"
Cohesion: 0.13
Nodes (18): Единственная строка настроек услуги (id = 1)., WhitelistConfig, Any, AsyncSession, Записывает событие в audit_logs., record(), choose_inbound(), InventoryResult (+10 more)

### Community 31 - "._clean_bot_token"
Cohesion: 0.33
Nodes (3): Убирает пробелы и обрамляющие кавычки вокруг токена., Разрешает задавать ADMIN_TELEGRAM_IDS как строку '1,2,3' или одно число., field_validator

### Community 32 - "Контекст проекта"
Cohesion: 0.10
Nodes (18): Запуск, Запуск через Docker Compose, API, Архитектура, Безопасность аутентификации (backend/main.go), Важные инженерные правила, Доменная модель (таблицы веб-части, в БД бота), Запуск (+10 more)

### Community 33 - "IsAdmin"
Cohesion: 0.21
Nodes (10): IsAdmin, TelegramObject, Пропускает событие только если пользователь — администратор., BaseFilter, test_is_admin_filter_accepts_admin(), test_is_admin_filter_rejects_missing_user(), test_is_admin_filter_rejects_regular_user(), test_settings_is_admin() (+2 more)

### Community 34 - "MockPanelUpdater"
Cohesion: 0.09
Nodes (36): PaymentStatus, BillingError, confirm_payment(), Exception, Ошибка бизнес-логики продления., Идемпотентное подтверждение оплаты администратором. Повторный вызов для уже…, Повторяет сбойную или прерванную после фиксации target заявку., Отклонение заявки администратором. Сериализуется с подтверждением: отклонение… (+28 more)

### Community 35 - "web_smoke.py"
Cohesion: 0.11
Nodes (25): aiohttp, WebAccount, WebLinkRequest, decide_link(), link_callback(), callback_query, CallbackQuery, base64 (+17 more)

### Community 36 - "ServerRepository"
Cohesion: 0.14
Nodes (12): admin_add_server_line(), _finalize_new_server(), _finalize_whitelist_server(), Сохраняет сервер и сразу пытается импортировать его inbound'ы. Так добавленный…, Добавляет сервер услуги и сразу сверяет его inbound'ы. До успешной сверки с…, admin_import_inbounds(), admin_whitelist_inventory(), Удаляет сервер вместе с inbound'ами и привязками (каскад). Коллекции грузим… (+4 more)

### Community 37 - "test_whitelist_xui.py"
Cohesion: 0.26
Nodes (21): ProvisionInbound, QuotaTarget, Inbound сервера, к которому нужно привязать клиента., Абсолютное целевое состояние клиента с учётом трафика. ``total_bytes`` —…, _auth(), _body(), HTTPXMock, parametrize (+13 more)

### Community 38 - "PanelUpdater"
Cohesion: 0.15
Nodes (24): Повторно выставляет текущий срок доступа клиента во всех панелях., sync_client(), serialized_access(), PanelUpdater, Интерфейс работы с клиентом в панели. Реализуется как mock (для тестов/MVP) и…, _delete_local_subscription(), delete_user_subscription(), AsyncSession (+16 more)

### Community 39 - "test_whitelist_payment_status.py"
Cohesion: 0.18
Nodes (27): on_payment_action(), admin_history(), admin_payment_card(), payment_status_label(), test_deferred_payment_notification_does_not_claim_full_access(), _down(), _fresh(), _is_waiting() (+19 more)

### Community 40 - "package.json"
Cohesion: 0.10
Nodes (18): lucide-vue-next, typescript, vite, @vitejs/plugin-vue, vue, vue-tsc, dependencies, lucide-vue-next (+10 more)

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
Cohesion: 0.32
Nodes (12): api(), authenticate(), copy(), getConnection(), go(), link(), logout(), pay() (+4 more)

### Community 45 - "Контекст проекта"
Cohesion: 0.14
Nodes (13): Админские команды, Антишеринг, Доменная модель, Интеграция с 3x-ui, Контекст проекта, Конфигурация, Локальные артефакты, Назначение (+5 more)

### Community 46 - ".auth"
Cohesion: 0.53
Nodes (6): net/http.Request, net/http.ResponseWriter, decode(), digest(), fail(), respond()

### Community 47 - "test_broadcast.py"
Cohesion: 0.27
Nodes (7): BroadcastResult, Bot, Рассылает текстовое сообщение всем пользователям. Сообщение отправляется…, send_broadcast(), FakeBot, test_send_broadcast_counts_sent_and_failed(), test_send_broadcast_empty_list()

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
Cohesion: 0.11
Nodes (35): app_bot, VpnClient, datetime, Клиенты, которым пора слать уведомление об окончании. Берём тех, у кого задан…, _utcnow(), VpnClientRepository, _as_aware(), process_expiry_notifications() (+27 more)

### Community 56 - "test_security.py"
Cohesion: 0.09
Nodes (32): _make_waiting(), _persist_payment(), AsyncSession, Тесты безопасности и устойчивости приложения. Покрывают ключевые свойства…, Порядок важен: для не-админа /admin проскакивает админ-роутер (фильтр IsAdmin…, Пользователь по callback может прислать только код тарифа — не цену/срок. Это…, Повторное создание заявки не плодит дубликаты (анти-спам / целостность)., Нельзя «откатить» уже применённую заявку отклонением. (+24 more)

### Community 57 - "test_notify_swallows_telegram_api_errors"
Cohesion: 0.15
Nodes (11): FakeBot, _make_payment(), Минимальный заменитель aiogram.Bot для проверки notify-функций., Подпись к чеку полностью контролируется пользователем и уходит админу с…, Для фото/документа подпись пользователя НЕ используется как caption —…, Сбой отправки одному админу не должен ронять обработку апдейта., test_admin_payment_card_escapes_username_and_error(), test_admin_pending_escapes_username() (+3 more)

### Community 58 - "Услуга «Обход белых списков» — реализация и порядок внедрения"
Cohesion: 0.20
Nodes (8): 1. Что получает пользователь, 2. Проверенный контракт 3x-ui, 5. Конкуренция и восстановление, 6. Порядок внедрения, 7. Откат, 9. Ограничения и решения, Восстановление после недоступной статистики, Услуга «Обход белых списков» — реализация и порядок внедрения

### Community 59 - "user_overview"
Cohesion: 0.14
Nodes (22): whitelist_admin(), answer(), edit(), Any, CallbackQuery, Безопасно редактирует сообщение callback'а. ``callback.message`` может быть…, Безопасно отправляет ответ в чат callback'а (если сообщение доступно)., get_active_server() (+14 more)

### Community 60 - "QuotaClientState"
Cohesion: 0.15
Nodes (18): QuotaClientState, Читает клиента и его счётчик трафика (None — клиента нет)., Прочитанное с панели состояние клиента и его счётчика трафика., _consistent_anchor(), _Context, _last_online(), _lose_baseline(), _push() (+10 more)

### Community 61 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 62 - "._api"
Cohesion: 0.22
Nodes (6): Response, Авторизованный запрос: гарантирует login и при истёкшей сессии выполняет…, Берёт CSRF-токен с /csrf-token (3x-ui >= 3.2.x). На старых панелях endpoint…, Ошибка авторизации в панели., Создаёт нового клиента в inbound через addClient., XuiAuthError

### Community 63 - "D VPN — личный кабинет"
Cohesion: 0.25
Nodes (7): D VPN — личный кабинет, Архитектура, Запуск вместе с существующим ботом, Локальная разработка, Результаты проверки, Что реализовано, Эксплуатация

### Community 71 - "test_xui_updater.py"
Cohesion: 0.21
Nodes (9): pytest_httpx, test_attach_success_without_membership_is_not_provisioning_success(), _mock_auth(), HTTPXMock, _spec(), test_legacy_provisioning_keeps_one_email_for_every_inbound(), test_provision_server_finds_client_by_sub_id(), test_provision_server_new_api_creates() (+1 more)

### Community 72 - "test_ux.py"
Cohesion: 0.08
Nodes (44): MenuCallback, Навигация по inline-меню (редактирование сообщения на месте). action: home |…, custom_emoji_id(), emoji_char(), Возвращает unicode-символ значка (без анимации)., Возвращает custom_emoji_id значка или None, если значок не найден., cancel_payment_keyboard(), connection_keyboard() (+36 more)

### Community 74 - "web_bridge.py"
Cohesion: 0.10
Nodes (30): PaymentAttachment, Durable per-admin Telegram delivery, retried independently of HTTP requests., WebDelivery, Фоновая периодическая проверка доступности серверов 3x-ui., _server_health_poller(), subhub_sync(), get_plan(), PaymentPlan (+22 more)

### Community 76 - "UserRole"
Cohesion: 0.27
Nodes (18): _is_active(), UserRole, has_active_timed_client(), has_client_access(), has_unlimited_bound_client(), resolve_effective_role(), _mapping(), test_access_rejects_missing_client() (+10 more)

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

### Community 84 - "bind_user_by_public_id"
Cohesion: 0.20
Nodes (18): bind_existing_client(), bind_user_by_public_id(), BindResult, _ensure_presence_mappings(), _finalize_bound_client(), find_client_presence_on_servers(), _public_id_taken(), AsyncSession (+10 more)

### Community 85 - "Обновление production — 4 октября 2026"
Cohesion: 0.25
Nodes (6): PAY-1C3F1344, Внедрено, Дополнительный дефект, обнаруженный при приёмке, Незавершённые операции, Обновление production — 4 октября 2026, Проверки и резервирование

### Community 87 - "vpn_client"
Cohesion: 0.29
Nodes (11): Как формируется клиент, Настройка серверов и авто-провижининг, Перенос пользователей, существовавших до бота, Шаг 1. Добавить серверы, Шаг 2. Импортировать inbound'ы каждого сервера, admin(), AsyncSession, fixture (+3 more)

### Community 88 - "PaymentRequest"
Cohesion: 0.09
Nodes (24): PaymentRequest, Пакет покупки трафика «Обход белых списков» (настраивается админом)., TrafficPackage, PaymentRepository, Берёт заявку с блокировкой строки (SELECT ... FOR UPDATE). На Postgres…, Число применённых оплат подписки (покупки трафика не учитываются)., Удаляет заявку (вместе с вложениями по каскаду)., Последняя успешная (применённая/подтверждённая) оплата пользователя.… (+16 more)

### Community 89 - "Оставшиеся риски и решения"
Cohesion: 0.29
Nodes (7): P1/P2 — частичный успех внешней операции требует сверки, P1 — административные права зависят от тарифа, P1 — биллинг и панели не образуют одну транзакцию, P2 — мониторинг и производительность, P2 — старые ошибки оплат без ожидающих задач, P2 — эксплуатация и воспроизводимость, Оставшиеся риски и решения

### Community 90 - "Server"
Cohesion: 0.06
Nodes (20): connection_overview(), Unified SubHub connection screen with live server availability., server_button_label(), ClientServerMapping, Server, Включённые серверы. По умолчанию — только обычные (безлимитные)., Цели обычного provisioning: whitelist-сервер ведётся отдельно., MockIpProvider (+12 more)

### Community 91 - "PanelUpdateError"
Cohesion: 0.15
Nodes (16): PanelUpdateError, Exception, Ошибка обновления клиента в панели., Пакетное чтение клиентов одной сессией панели., find_panel_client(), _find_panel_client_by_sub_id(), list_panel_clients(), _panel_client_secret() (+8 more)

### Community 92 - "test_subscription_delete.py"
Cohesion: 0.23
Nodes (9): _FakeBot, _FakeMessage, _FakeState, Any, AsyncSession, test_admin_delete_subscription_uses_client_id_not_telegram_id(), test_delete_subscription_keeps_local_client_on_panel_failure(), test_delete_subscription_removes_panel_and_local_client() (+1 more)

### Community 93 - "test_whitelist_bot.py"
Cohesion: 0.14
Nodes (17): Пользовательский раздел «Обход белых списков». action: home | refresh | buy…, WhitelistCallback, Возможности, FakeCallback, FakeMessage, FakeState, Any, Сценарии Telegram-бота услуги «Обход белых списков» (пользователь и админ). (+9 more)

### Community 94 - "ServerInbound"
Cohesion: 0.13
Nodes (14): Inbound на панели сервера, в который нужно заводить клиентов. На одном сервере…, ServerInbound, ensure_inbounds_imported(), has_targets(), import_inbounds(), Сверяет inbound'ы панели с локальными целями провижининга. Удалённые и…, Импортирует inbound'ы для включённых серверов, у которых их ещё нет. Нужно для…, Есть ли хотя бы один включённый сервер с включённым inbound для провижининга. (+6 more)

### Community 95 - "whitelist.py"
Cohesion: 0.18
Nodes (12): admin_summary(), AdminSummary, AwaitingCredit, _detect_external_disable(), gib_to_bytes(), _ms(), PurchaseResult, Decimal (+4 more)

### Community 97 - "callbacks.py"
Cohesion: 0.18
Nodes (14): aiogram_filters_callback_data, AdminCallback, BindCallback, OnboardCallback, PaymentCallback, PlanCallback, Callback админских действий над заявкой на привязку подписки., Callback выбора тарифа пользователем. code — код тарифа из PLANS (1m/6m/12m)… (+6 more)

### Community 98 - "test_ui.py"
Cohesion: 0.29
Nodes (7): aiogram_methods, TelegramBadRequest, _bad_request(), _Callback, Exception, test_answer_callback_ignores_expired_query_id(), test_answer_callback_reraises_other_bad_request()

### Community 99 - "FSMContext"
Cohesion: 0.22
Nodes (9): admin_add_server_cancel(), admin_broadcast_cancel(), admin_delete_subscription_cancel(), admin_rename_server_cancel(), admin_subscription_url_cancel(), FSMContext, whitelist_value_cancel(), admin_add_cancelled() (+1 more)

### Community 100 - "models.py"
Cohesion: 0.09
Nodes (30): app_db, Base, Базовый класс для всех ORM-моделей., TimestampMixin, WebSession, WebToken, do_run_migrations(), run_migrations_online() (+22 more)

### Community 101 - "_whitelist_home"
Cohesion: 0.29
Nodes (7): _parse_gb(), _parse_price(), Decimal, InlineKeyboardMarkup, _whitelist_home(), whitelist_value_input(), admin_whitelist_home()

### Community 102 - "check_servers"
Cohesion: 0.18
Nodes (7): check_server(), check_servers(), AsyncSession, Проверяет доступность панели 3x-ui одного сервера. Успешный login считается…, Проверяет все серверы и сохраняет результат в БД. Возвращает отображение…, Фоновые задачи, test_health_check_server_returns_true_on_success()

### Community 103 - "devDependencies"
Cohesion: 0.40
Nodes (5): devDependencies, typescript, vite, @vitejs/plugin-vue, vue-tsc

### Community 104 - "XuiClient"
Cohesion: 0.08
Nodes (19): Идентификатор для updateClient/{id}: id для vless/vmess, иначе email., Изолированный REST-клиент панели 3x-ui (MHSanaei/3x-ui). Принципы: - одна…, Обновляет клиента, сохраняя все его поля и меняя только нужные. Возвращает…, Устанавливает expiryTime (мс) и включает клиента., Лимит уникальных IP (0 = без лимита). Не считать точным лимитом устройств., Совместимый метод: продление через read-modify-write., Возвращает список IP-адресов клиента из журнала 3x-ui (iplimit log). Требует…, Извлекает IP из вариантов ответа 3x-ui, не сохраняя метаданные лога. (+11 more)

### Community 105 - "test_payment_requests.py"
Cohesion: 0.48
Nodes (6): AsyncSession, test_attach_proof_creates_attachment(), test_create_request_reuses_open_request(), test_create_request_sets_waiting_admin(), test_get_by_code_and_list_waiting(), test_payment_code_increments()

### Community 106 - "reconcile_usage"
Cohesion: 0.40
Nodes (5): ensure_defaults(), Фоновая сверка расхода: обновляет остатки и обнаруживает сброс счётчика.…, Идемпотентная инициализация: настройки и начальные пакеты., reconcile_usage(), 4. Точки интеграции

### Community 107 - "FakeMessage"
Cohesion: 0.40
Nodes (3): FakeMessage, Заменитель Message: запоминает ответы., test_non_admin_admin_command_denied()

### Community 108 - "xui_client.py"
Cohesion: 0.50
Nodes (3): ipaddress, json, urllib_parse

### Community 109 - "test_payment_code_wrapped_in_code_tag"
Cohesion: 0.67
Nodes (3): payment_rejected(), proof_received(), test_payment_code_wrapped_in_code_tag()

### Community 110 - "test_create_request_with_plan"
Cohesion: 0.67
Nodes (3): AsyncSession, test_changing_plan_updates_open_request(), test_create_request_with_plan()

## Knowledge Gaps
- **164 isolated node(s):** `credentials`, `dvpn/site`, `name`, `version`, `private` (+159 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 722 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `provisioning.py`, `texts.py`, `WhitelistLedger`, `notify.py`, `test_whitelist.py`, `user_handlers.py`, `admin_handlers.py`, `admin_rename_server_name`, `billing.py`, `test_provisioning.py`, `repositories.py`, `pending_updates.py`, `test_whitelist_pg.py`, `AsyncSession`, `admin_nav`, `utcnow`, `IsAdmin`, `MockPanelUpdater`, `web_smoke.py`, `ServerRepository`, `PanelUpdater`, `test_whitelist_payment_status.py`, `test_broadcast.py`, `VpnClient`, `test_security.py`, `test_notify_swallows_telegram_api_errors`, `user_overview`, `QuotaClientState`, `test_ux.py`, `web_bridge.py`, `UserRole`, `bind_user_by_public_id`, `vpn_client`, `PaymentRequest`, `test_subscription_delete.py`, `whitelist.py`, `models.py`, `_whitelist_home`, `test_payment_requests.py`, `test_create_request_with_plan`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Why does `Server` connect `Server` to `provisioning.py`, `texts.py`, `notify.py`, `test_whitelist.py`, `admin_handlers.py`, `admin_rename_server_name`, `keyboards.py`, `XuiPanelUpdater`, `test_provisioning.py`, `repositories.py`, `pending_updates.py`, `test_whitelist_pg.py`, `config.py`, `utcnow`, `What You Must Do When Invoked`, `User`, `record`, `MockPanelUpdater`, `web_smoke.py`, `ServerRepository`, `test_whitelist_xui.py`, `PanelUpdater`, `test_whitelist_payment_status.py`, `Контекст проекта`, `EncryptedString`, `VpnClient`, `user_overview`, `QuotaClientState`, `test_xui_updater.py`, `test_ux.py`, `web_bridge.py`, `bind_user_by_public_id`, `vpn_client`, `PanelUpdateError`, `test_whitelist_bot.py`, `ServerInbound`, `whitelist.py`, `models.py`, `_whitelist_home`, `check_servers`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `Settings` connect `admin_handlers.py` to `notify.py`, `test_whitelist.py`, `user_handlers.py`, `admin_rename_server_name`, `repositories.py`, `main.py`, `config.py`, `admin_nav`, `utcnow`, `middlewares.py`, `Protocol`, `._clean_bot_token`, `IsAdmin`, `MockPanelUpdater`, `web_smoke.py`, `ServerRepository`, `test_whitelist_payment_status.py`, `test_broadcast.py`, `test_security.py`, `test_notify_swallows_telegram_api_errors`, `user_overview`, `test_ux.py`, `web_bridge.py`, `UserRole`, `test_subscription_delete.py`, `test_whitelist_bot.py`, `test_broadcast_text_is_plain_no_parse_mode`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 162 inferred relationships involving `User` (e.g. with `admin_add_server_line()` and `admin_broadcast_send()`) actually correct?**
  _`User` has 162 INFERRED edges - model-reasoned connections that need verification._
- **Are the 87 inferred relationships involving `VpnClient` (e.g. with `notify_user_extended()` and `access_extended()`) actually correct?**
  _`VpnClient` has 87 INFERRED edges - model-reasoned connections that need verification._
- **Are the 47 inferred relationships involving `Server` (e.g. with `_finalize_new_server()` and `_finalize_whitelist_server()`) actually correct?**
  _`Server` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Are the 55 inferred relationships involving `Settings` (e.g. with `add_server()` and `admin_add_server_line()`) actually correct?**
  _`Settings` has 55 INFERRED edges - model-reasoned connections that need verification._
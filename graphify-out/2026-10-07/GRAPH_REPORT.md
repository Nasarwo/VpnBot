# Graph Report - VpnBot  (2026-10-07)

## Corpus Check
- 182 files · ~192,750 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 9, .example 3, .conf 1)

## Summary
- 3338 nodes · 12385 edges · 146 communities (116 shown, 30 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1631 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `520d65e2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_whitelist_retarget.py
- test_provisioning.py
- whitelist.py
- test_legacy_bind.py
- test_whitelist.py
- user_handlers.py
- admin_handlers.py
- Protocol
- keyboards.py
- test_whitelist_reconcile.py
- billing.py
- SubHubClient
- _trial_available
- VpnClientRepository
- alembic
- pending_updates.py
- WhitelistLedger
- LocalSubHub
- main.go
- App.vue
- get_sessionmaker
- whitelist_e2e.py
- WhitelistAccount
- ClientServerMapping
- XuiClient
- test_trial_grants_migration.py
- xui_updater.py
- send_broadcast
- AsyncSession
- test_whitelist_inbound_compat.py
- xui_traffic_d3.py
- test_whitelist_bot.py
- Контекст проекта
- PanelUpdateError
- test_trial_paid_reset.py
- web_bridge.py
- test_whitelist_queue_worker.py
- XuiPanelUpdater
- Server
- test_whitelist_payment_status.py
- package.json
- scenario
- compilerOptions
- main_test.go
- api
- Ревью VpnBot — 4 октября 2026
- .auth
- test_renewal_recovery_worker.py
- Задание агенту: услуга «Обход белых списков» в VpnBot
- app
- main
- Panel
- web_preview.mjs
- UserRepository
- _pay
- What You Must Do When Invoked
- VpnClient
- sync_inventory
- PanelUpdater
- Telegram VPN Billing Bot
- whitelist_migration_check.py
- collections_abc
- Report
- D VPN — личный кабинет
- PaymentRequest
- ServerInbound
- placement_progress
- create_request
- dvpn/site
- telegram-vpn-billing-bot
- MockPanelUpdater
- ServerProvision
- graphify reference: extra exports and benchmark
- grant_trial
- test_subscription_purchases_migration.py
- Контекст проекта
- session
- whitelist_background_e2e.py
- .failed
- apply_access
- models.py
- _server_health_poller
- AGENTS.md
- delete_user_subscription
- User
- test_user_reset_pg.py
- run_rollout
- Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026
- test_trial_reset.py
- DiesOnFirstChange
- parametrize
- Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026
- provisioning.py
- Production deployment — 2026-10-06
- Q: собери контекст проекта
- test_health_check_server_returns_false_on_error
- run_once
- PendingServerUpdate
- graphify reference: query, path, explain
- EncryptedString
- Any
- menu_nav
- Услуга «Обход белых списков» — реализация и порядок внедрения
- ._clean_bot_token
- whitelist_e2e_2026-10-05.md
- Ids
- reconcile_cycle
- Настройка серверов и авто-провижининг
- stack.sh
- whitelist_migration_2026-10-05.md
- scripts
- test_xui_client.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- _whitelist_queue_worker
- api.ts
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- admin_nav
- _Crash
- extraction-spec.md
- env.py
- Протокол: R46 без принудительной синхронизации, фоновые циклы бота — 5 октября 2026
- _Crash
- test_ux.py
- test_verdicts_agree_with_subhub_link_builder
- test_health_check_server_returns_true_on_success
- panel
- _PoisonedPanel
- AuditLog
- _FakeBot
- _HangingPanel
- AwaitingCredit
- vue
- test_site_trial_race_with_payment_maps_to_conflict
- ref_node_fs_promises

## God Nodes (most connected - your core abstractions)
1. `User` - 315 edges
2. `MockPanelUpdater` - 214 edges
3. `VpnClient` - 163 edges
4. `Server` - 153 edges
5. `Settings` - 150 edges
6. `PaymentRequest` - 138 edges
7. `PaymentStatus` - 125 edges
8. `_pay()` - 110 edges
9. `VpnClientRepository` - 86 edges
10. `XuiClient` - 82 edges

## Surprising Connections (you probably didn't know these)
- `P1 — пароли панелей не защищены шифрованием приложения` --references--> `EncryptedString`  [INFERRED]
  docs/REVIEW_2026-10-04.md → app/db/types.py
- `6. Реальные 3x-ui и SubHub` --references--> `recover_confirmed_payments()`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → app/services/billing.py
- `Фоновые задачи` --references--> `check_servers()`  [INFERRED]
  context.md → app/services/health.py
- `Смена целевого inbound и перенос клиентов (2026-10-06)` --references--> `_push()`  [INFERRED]
  docs/WHITELIST_SERVICE.md → app/services/whitelist.py
- `Как формируется клиент` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py

## Import Cycles
- None detected.

## Communities (146 total, 30 thin omitted)

### Community 0 - "test_whitelist_retarget.py"
Cohesion: 0.16
Nodes (49): get_active_server(), process_due(), Фоновая очередь: применяет несинхронизированные состояния с backoff. Кроме…, Включённый whitelist-сервер (не более одного по уникальному индексу)., _add_candidate(), _available(), test_claim_command_releases_legacy_attachment(), test_whitelist_check_reports_actual_placement() (+41 more)

### Community 1 - "test_provisioning.py"
Cohesion: 0.14
Nodes (21): ensure_inbounds_imported(), Импортирует inbound'ы для включённых серверов, у которых их ещё нет. Нужно для…, _panel_info(), AsyncSession, HTTPXMock, Ссылка содержит subId, а в панели email другой — оба поля сохраняются., _server_with_inbounds(), test_bind_existing_client() (+13 more)

### Community 2 - "whitelist.py"
Cohesion: 0.08
Nodes (60): QuotaClientState, Прочитанное с панели состояние клиента и его счётчика трафика., access_state(), AccessState, _applied_target(), _apply_quota(), apply_usage(), _aware() (+52 more)

### Community 3 - "test_legacy_bind.py"
Cohesion: 0.06
Nodes (44): bind_request_received(), connection_unavailable(), onboarding_invalid_link(), onboard_legacy_link(), BindRequest, Заявка на привязку существующей подписки (до внедрения бота)., BindRequestRepository, AsyncSession (+36 more)

### Community 4 - "test_whitelist.py"
Cohesion: 0.08
Nodes (75): list_open_events(), Применяет состояние учёта пользователя на whitelist-панели., Фоновая сверка расхода: обходит все учёты пачками по ``limit``. Возвращает…, Остатки пользователя; при доступной панели — с актуальной сверкой. Чтение…, Неприменённые события учёта пользователя в порядке возникновения., reconcile_usage(), sync_user(), user_overview() (+67 more)

### Community 5 - "user_handlers.py"
Cohesion: 0.08
Nodes (50): aiogram_exceptions, aiogram_fsm_state, aiogram_methods, OnboardingStates, bind_request_waiting(), no_open_request(), onboarding_legacy_question(), onboarding_send_link_prompt() (+42 more)

### Community 6 - "admin_handlers.py"
Cohesion: 0.10
Nodes (61): aiogram_fsm_context, add_inbound(), add_server(), admin_add_server_cancel(), admin_broadcast_cancel(), admin_broadcast_send(), admin_delete_subscription_by_client_id(), admin_delete_subscription_cancel() (+53 more)

### Community 7 - "Protocol"
Cohesion: 0.11
Nodes (34): Protocol, ProvisionTarget, Описание клиента, которого нужно создать/обновить в конкретном inbound., build_client_object(), client_identifier(), _client_uuid_for_api(), _looks_like_db_id(), pick_panel_client_secret() (+26 more)

### Community 8 - "keyboards.py"
Cohesion: 0.11
Nodes (55): BindCallback, Callback админских действий над заявкой на привязку подписки., _adm(), admin_add_server_type_keyboard(), admin_back_keyboard(), admin_bind_keyboard(), admin_bind_retry_keyboard(), admin_confirm_delete_keyboard() (+47 more)

### Community 9 - "test_whitelist_reconcile.py"
Cohesion: 0.06
Nodes (61): _fmt_span(), Состояние фоновой сверки расхода для админ-раздела (по данным процесса). «Обход…, _reconcile_gaps(), reconcile_status_lines(), timedelta, Состояние и наблюдаемость фоновой сверки (хранится в памяти процесса).…, Сколько прошло с завершения последнего обхода (в т. ч. с пропусками)., Верхняя граница возраста данных *сверенных* учётов последнего обхода. (+53 more)

### Community 10 - "billing.py"
Cohesion: 0.13
Nodes (38): Any, AsyncSession, Записывает событие в audit_logs., record(), _apply_panels(), BillingError, BillingResult, compute_new_expiry() (+30 more)

### Community 11 - "SubHubClient"
Cohesion: 0.07
Nodes (32): main(), build_happ_import_url(), Exception, Resolve the first panel identity known to SubHub. Older bot records can have a…, Base error for the internal SubHub integration., The panels have not exposed this identity to SubHub yet., The identity exists, but currently has no active nodes., Build a signed HTTPS trampoline for importing a legacy subscription. (+24 more)

### Community 12 - "_trial_available"
Cohesion: 0.19
Nodes (16): trial_subscription_purchased(), Пробный доступен, если им не пользовались и подписку никогда не оформляли., _trial_available(), _old_trial_button(), parametrize, Клиент удалён, а оплата осталась: бот, сервис и сайт отказывают одинаково., Всё, что trial не должен менять после отказа., Нажатие trial в старом сообщении, когда кнопка уже скрыта в новом меню. (+8 more)

### Community 13 - "VpnClientRepository"
Cohesion: 0.13
Nodes (19): datetime, Клиенты, которым пора слать уведомление об окончании. Берём тех, у кого задан…, _utcnow(), VpnClientRepository, _as_aware(), process_expiry_notifications(), AsyncSession, datetime (+11 more)

### Community 15 - "pending_updates.py"
Cohesion: 0.26
Nodes (18): apply_pending_for_server(), apply_pending_update(), _apply_to_server(), _as_aware(), _clear_payment_error_if_complete(), close_for_server(), _defer_after_error(), _expiry_to_ms() (+10 more)

### Community 16 - "WhitelistLedger"
Cohesion: 0.09
Nodes (36): Привязка клиента whitelist-панели к inbound'у, созданная самой услугой. Строка…, Журнал выдач/начислений/корректировок, привязанных к исходной операции. Выдача…, WhitelistLedger, WhitelistPlacement, get_account(), _record_ledger(), 4. Автоматические тесты, _ledger() (+28 more)

### Community 17 - "LocalSubHub"
Cohesion: 0.11
Nodes (16): StreamReader, StreamWriter, _command(), LocalSubHub, _Maker, _paid(), parametrize, HTTP-сервер вместо SubHub: ``accept`` — 202 и запись, ``drop`` — разрыв без… (+8 more)

### Community 18 - "main.go"
Cohesion: 0.07
Nodes (29): credentials, go_pkg_bytes, go_pkg_context, go_pkg_crypto_hmac, go_pkg_crypto_rand, go_pkg_crypto_sha256, go_pkg_crypto_subtle, go_pkg_crypto_tls (+21 more)

### Community 19 - "App.vue"
Cohesion: 0.07
Nodes (24): authTitles, awaiting, busy, code, comment, config, connection, days (+16 more)

### Community 20 - "get_sessionmaker"
Cohesion: 0.06
Nodes (54): _command_name(), _describe_callback(), _describe_event(), _describe_message(), Any, CallbackQuery, Message, TelegramObject (+46 more)

### Community 21 - "whitelist_e2e.py"
Cohesion: 0.09
Nodes (30): aiogram, aiogram_client_default, aiogram_fsm_storage_memory, aiogram_types, aiogram_utils_token, DbSessionMiddleware, Открывает сессию БД, получает/создаёт пользователя и кладёт их в data., build_root_router() (+22 more)

### Community 22 - "WhitelistAccount"
Cohesion: 0.10
Nodes (25): Base, Базовый класс для всех ORM-моделей., Бизнес-учёт трафика пользователя на whitelist-сервере. Остатки…, WebSession, WebToken, WhitelistAccount, apply_event(), compute_target() (+17 more)

### Community 23 - "ClientServerMapping"
Cohesion: 0.07
Nodes (62): ip_scan(), sharing_report(), items: список кортежей (VpnClient, SharingStatus)., Полный краткий отчёт по IP-наблюдениям всех VPN-клиентов., sharing_all(), sharing_detail(), sharing_disabled(), sharing_level_label() (+54 more)

### Community 24 - "XuiClient"
Cohesion: 0.06
Nodes (40): Реальный провайдер: берёт IP клиента из журнала панели 3x-ui., XuiIpProvider, Any, Exception, Response, _quote_path_segment(), Авторизованный запрос: гарантирует login и при истёкшей сессии выполняет…, Берёт CSRF-токен с /csrf-token (3x-ui >= 3.2.x). На старых панелях endpoint… (+32 more)

### Community 25 - "test_trial_grants_migration.py"
Cohesion: 0.19
Nodes (17): alembic_config, _audit(), _expected(), _naive_utc(), datetime, parametrize, Миграция ``trial_grants`` переносит существующие факты использования trial.…, PostgreSQL: удаление пользователя обнуляет actor_user_id (ON DELETE SET NULL). (+9 more)

### Community 26 - "xui_updater.py"
Cohesion: 0.11
Nodes (20): build_client_record(), client_record_body(), merge_client_record_for_update(), Извлекает model.Client из ответа ``clients/get``., Тело ``clients/update``: сохраняет секреты панели, меняет срок и enable. Поля…, Унифицированный объект клиента для нового client-API (3x-ui >= 3.2.x).…, _client_flows(), _inbound_client_flow() (+12 more)

### Community 27 - "send_broadcast"
Cohesion: 0.29
Nodes (6): BroadcastResult, Рассылает текстовое сообщение всем пользователям. Сообщение отправляется…, send_broadcast(), FakeBot, test_send_broadcast_counts_sent_and_failed(), test_send_broadcast_empty_list()

### Community 28 - "AsyncSession"
Cohesion: 0.10
Nodes (36): Единственная строка настроек услуги (id = 1)., WhitelistConfig, classify_origin(), confirm_traffic_payment(), ensure_defaults(), get_config(), grant_for_subscription_payment(), grant_for_trial() (+28 more)

### Community 29 - "test_whitelist_inbound_compat.py"
Cohesion: 0.19
Nodes (26): build_provision_spec(), server_ready(), target_inbound(), cryptography_hazmat_primitives, cryptography_hazmat_primitives_asymmetric_x25519, _assert_no_secrets(), parametrize, Совместимость целевого inbound услуги с форматом ссылок SubHub. Импорт inbound… (+18 more)

### Community 30 - "xui_traffic_d3.py"
Cohesion: 0.10
Nodes (47): 15. Лимит трафика 3x-ui → SubHub: единица `totalGB` и источник расхода (результаты от 2026-10-05, после приёмки), 2. Проверенный контракт 3x-ui, Число строк и хэш упорядоченного содержимого прежних столбцов., snapshot(), accounted(), add_client(), container_started(), delta() (+39 more)

### Community 31 - "test_whitelist_bot.py"
Cohesion: 0.11
Nodes (46): aiogram_filters_callback_data, AdminCallback, OnboardCallback, PaymentCallback, PlanCallback, Callback выбора тарифа пользователем. code — код тарифа из PLANS (1m/6m/12m)…, Онбординг: был ли пользователь клиентом до внедрения бота., Навигация по админ-панели (/admin). action: home | servers | server | rename |… (+38 more)

### Community 32 - "Контекст проекта"
Cohesion: 0.13
Nodes (14): Архитектура, Безопасность аутентификации (backend/main.go), Важные инженерные правила, Доменная модель (таблицы веб-части, в БД бота), Запуск, Контекст проекта, Конфигурация, Локальные артефакты (+6 more)

### Community 33 - "PanelUpdateError"
Cohesion: 0.14
Nodes (9): effective_flow(), PanelUpdateError, Exception, Ошибка обновления клиента в панели., flow, который 3x-ui копирует при attach: первый непустой по id inbound'а., list_panel_clients(), Возвращает список клиентов, уже существующих на панели сервера., LostDetachResponse (+1 more)

### Community 34 - "test_trial_paid_reset.py"
Cohesion: 0.14
Nodes (29): Первая применённая оплата подписки Telegram-аккаунта. Закрывает trial так же,…, SubscriptionPurchase, Подписку уже оформляли этот пользователь или его Telegram ID. Оформлена — есть…, subscription_already_purchased(), _assert_failed_not_recorded(), _paid_and_reset(), _purchases(), parametrize (+21 more)

### Community 35 - "web_bridge.py"
Cohesion: 0.07
Nodes (46): aiohttp, AttachmentType, str, PaymentAttachment, Durable per-admin Telegram delivery, retried independently of HTTP requests., WebAccount, WebDelivery, WebLinkRequest (+38 more)

### Community 36 - "test_whitelist_queue_worker.py"
Cohesion: 0.16
Nodes (32): Any, Запускает worker, если такой ещё не работает в этом процессе., Запускает фоновые циклы процесса бота (кроме доставки сайта). Одна сборка для…, start_background_tasks(), _start_exclusive(), stop_background_tasks(), Task, test_worker_survives_cycle_failures() (+24 more)

### Community 37 - "XuiPanelUpdater"
Cohesion: 0.20
Nodes (37): QuotaTarget, Абсолютное целевое состояние клиента с учётом трафика. ``total_bytes`` —…, Реализация PanelUpdater поверх XuiClient. На каждый сервер создаётся отдельный…, XuiPanelUpdater, 3.5. Учёт трафика и интеграция 3x-ui, test_stale_inbound_is_rejected_before_client_creation(), _apply_existing(), _auth() (+29 more)

### Community 38 - "Server"
Cohesion: 0.05
Nodes (42): admin_add_server_line(), _finalize_new_server(), _finalize_whitelist_server(), _parse_server_line(), Сохраняет сервер и сразу пытается импортировать его inbound'ы. Так добавленный…, Добавляет сервер услуги и сразу сверяет его inbound'ы. До успешной сверки с…, Парсит 'name|country|panel_url|username|password|[kind]|[sub]|[purpose]'.…, server_button_label() (+34 more)

### Community 39 - "test_whitelist_payment_status.py"
Cohesion: 0.27
Nodes (20): _buy(), _down(), _fresh(), _is_waiting(), _queue(), Статус заявки на покупку трафика следует за фактическим применением начисления., Запись квоты прошла, но расход не сверен: начисление ещё не учтено., Применена версия между двумя заявками: ожидание снимается только с ранней. (+12 more)

### Community 40 - "package.json"
Cohesion: 0.11
Nodes (17): lucide-vue-next, typescript, vite, @vitejs/plugin-vue, vue-tsc, dependencies, lucide-vue-next, vue (+9 more)

### Community 41 - "scenario"
Cohesion: 0.11
Nodes (17): _disabled(), gb(), load_env(), main(), ms(), _package(), _panel_up(), datetime (+9 more)

### Community 42 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, esModuleInterop, jsx, lib, module, moduleResolution, resolveJsonModule, skipLibCheck (+4 more)

### Community 43 - "main_test.go"
Cohesion: 0.21
Nodes (11): go_pkg_net_http, go_pkg_net_http_httptest, go_pkg_strings, go_pkg_testing, go_pkg_time, testing.T, canonicalEmail(), TestCodesBoundToAccountAndPurpose() (+3 more)

### Community 44 - "api"
Cohesion: 0.32
Nodes (12): api(), authenticate(), copy(), getConnection(), go(), link(), logout(), pay() (+4 more)

### Community 45 - "Ревью VpnBot — 4 октября 2026"
Cohesion: 0.08
Nodes (22): PAY-1C3F1344, Внедрено, Дополнительный дефект, обнаруженный при приёмке, Незавершённые операции, Обновление production — 4 октября 2026, Проверки и резервирование, P1/P2 — частичный успех внешней операции требует сверки, P1 — административные права зависят от тарифа (+14 more)

### Community 46 - ".auth"
Cohesion: 0.53
Nodes (6): net/http.Request, net/http.ResponseWriter, decode(), digest(), fail(), respond()

### Community 47 - "test_renewal_recovery_worker.py"
Cohesion: 0.16
Nodes (40): _as_aware(), expiry_to_ms(), Гарантирует timezone-aware datetime (SQLite возвращает naive)., Конвертирует дату в миллисекунды Unix-времени (формат 3x-ui expiryTime)., _audit_count(), _crash_during_confirmation(), _expiry_calls(), _fresh() (+32 more)

### Community 48 - "Задание агенту: услуга «Обход белых списков» в VpnBot"
Cohesion: 0.15
Nodes (12): 1. Контекст проекта, 2. Согласованное поведение услуги, 3. Сервер и настройки администратора, 4. Технический контракт учёта трафика, 5. Биллинг, конкуренция и восстановление, 6. Пользовательский интерфейс, 7. Обязательная проверка, 8. Порядок работы и сдача (+4 more)

### Community 49 - "app"
Cohesion: 0.29
Nodes (6): app, config, context.Context, github.com/jackc/pgx/v5/pgxpool.Pool, net/http.Client, pgx.Tx

### Community 50 - "main"
Cohesion: 0.22
Nodes (7): bucket, limiter, net/http.Handler, sync.Mutex, time.Time, env(), main()

### Community 51 - "Panel"
Cohesion: 0.07
Nodes (31): admin_servers(), import_control_inbound(), main(), panel_view(), Any, Path, Квота трафика 3x-ui → SubHub на реальной панели, без маскирующего…, Расход, не менявшийся между двумя чтениями с интервалом 12 с. (+23 more)

### Community 52 - "web_preview.mjs"
Cohesion: 0.29
Nodes (6): ref_node_fs, ref_node_http, ref_node_path, ref_node_url, root, types

### Community 53 - "UserRepository"
Cohesion: 0.20
Nodes (8): Удаляет пользователя и связанные записи (каскад в ORM)., Telegram ID всех пользователей, когда-либо запускавших бота., Генерирует короткий уникальный публичный ID пользователя., UserRepository, AsyncSession, test_backfills_public_id_for_existing(), test_get_or_create_assigns_public_id(), test_public_id_is_stable_and_unique()

### Community 54 - "_pay"
Cohesion: 0.11
Nodes (29): 3.2. Купленный трафик, 3.3. Ограничения доступа, 3.6. Биллинг, конкуренция, восстановление, 3.7. Интерфейс, миграции, устройство, 3. Матрица требований и доказательств, ops, _package(), _pay() (+21 more)

### Community 55 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 56 - "VpnClient"
Cohesion: 0.05
Nodes (80): forward_proof_to_admins(), _is_active(), Конфигурация приложения из переменных окружения / .env., Settings, PaymentStatus, UserRole, VpnClient, has_active_timed_client() (+72 more)

### Community 57 - "sync_inventory"
Cohesion: 0.11
Nodes (30): choose_inbound(), claim_inbound(), check_inbound(), _check_vless_reality(), describe(), _foreign_flows(), InboundCompat, _json() (+22 more)

### Community 58 - "PanelUpdater"
Cohesion: 0.12
Nodes (22): PanelUpdater, Интерфейс работы с клиентом в панели. Реализуется как mock (для тестов/MVP) и…, Читает клиента и его счётчик трафика (None — клиента нет)., Пакетное чтение клиентов одной сессией панели., Создаёт/обновляет клиента с квотой и проверяет результат чтением.…, Снимает привязки клиента к ``inbound_ids`` (счётчик сохраняется). Проверяет…, adjust_balance(), after_access_change() (+14 more)

### Community 59 - "Telegram VPN Billing Bot"
Cohesion: 0.13
Nodes (14): Запуск, Telegram VPN Billing Bot, Админ-команды, Антишеринг-мониторинг, Граф кода (graphify), Единая подписка SubHub, Запуск через Docker Compose, Конфигурация (+6 more)

### Community 60 - "whitelist_migration_check.py"
Cohesion: 0.26
Nodes (18): hashlib, alembic(), check(), docker(), downgrade_cycle(), dsn(), ensure_defaults_idempotent(), main() (+10 more)

### Community 62 - "Report"
Cohesion: 0.25
Nodes (4): Any, Конфигурация xray-клиента: SOCKS 127.0.0.1:10808 → VLESS по ссылке., Report, xray_client_config()

### Community 63 - "D VPN — личный кабинет"
Cohesion: 0.25
Nodes (7): D VPN — личный кабинет, Архитектура, Запуск вместе с существующим ботом, Локальная разработка, Результаты проверки, Что реализовано, Эксплуатация

### Community 64 - "PaymentRequest"
Cohesion: 0.06
Nodes (79): _after_applied_payment(), on_payment_action(), Уведомления и SubHub после применения; возвращает итог для администратора.…, notify_admins_failed(), notify_admins_new_request(), notify_first_purchase_channel(), notify_user_expiry(), notify_user_extended() (+71 more)

### Community 65 - "ServerInbound"
Cohesion: 0.11
Nodes (16): Inbound на панели сервера, в который нужно заводить клиентов. На одном сервере…, ServerInbound, fetch_inbounds(), import_inbounds(), Any, Сверяет inbound'ы панели с локальными целями провижининга. Удалённые и…, Читает список inbound'ов панели (``inbounds/list``) как есть., Сверка реестра с уже прочитанным списком (см. :func:`import_inbounds`). (+8 more)

### Community 66 - "placement_progress"
Cohesion: 0.12
Nodes (15): admin_summary(), AdminSummary, placement_drift(), placement_progress(), PlacementProgress, Привязки услуги к прежним целям на этом сервере (снимаются после переноса)., Учёт с клиентом на панели, размещение которого не подтверждено для цели.…, Расхождение прочитанного размещения клиента с целью сервера; None — совпадает.… (+7 more)

### Community 67 - "create_request"
Cohesion: 0.07
Nodes (38): cancel_open_request(), create_request(), create_traffic_request(), _new_payment_code(), _open_request_for_update(), PaymentRequestError, PendingRequestExists, AsyncSession (+30 more)

### Community 71 - "MockPanelUpdater"
Cohesion: 0.09
Nodes (31): PaymentRepository, Берёт заявку с блокировкой строки (SELECT ... FOR UPDATE). На Postgres…, Число применённых оплат подписки (покупки трафика не учитываются)., Удаляет заявку (вместе с вложениями по каскаду)., Последняя успешная (применённая/подтверждённая) оплата пользователя.…, confirm_payment(), Идемпотентное подтверждение оплаты администратором. Повторный вызов для уже…, MockPanelUpdater (+23 more)

### Community 72 - "ServerProvision"
Cohesion: 0.12
Nodes (16): ProvisionInbound, Создаёт/обновляет клиента сразу для всех inbound'ов сервера., Inbound сервера, к которому нужно привязать клиента., Один клиент панели (глобальный по email), привязанный к её inbound'ам.…, ServerProvision, Старые панели: отдельный клиент в каждом inbound (per-inbound email)., json, pytest_httpx (+8 more)

### Community 73 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 74 - "grant_trial"
Cohesion: 0.15
Nodes (22): Оформлялась ли подписка: есть принятая оплата подписки (не трафика). Принятая —…, grant_trial(), Пробный период уже выдавался этому пользователю или его Telegram ID.…, Единое правило допуска trial: он не использован и подписку ещё не оформляли.…, Выдаёт бесплатный пробный период один раз на Telegram-аккаунт и до первой…, trial_already_used(), trial_available(), TrialResult (+14 more)

### Community 75 - "test_subscription_purchases_migration.py"
Cohesion: 0.20
Nodes (15): Config, _at(), _expected(), _payment(), datetime, parametrize, Миграция ``subscription_purchases`` переносит сохранившиеся оплаты подписки.…, timestamptz: явный UTC, независимо от часового пояса сервера. (+7 more)

### Community 76 - "Контекст проекта"
Cohesion: 0.14
Nodes (13): Админские команды, Антишеринг, Интеграция с 3x-ui, Контекст проекта, Конфигурация, Локальные артефакты, Назначение, Основные пользовательские сценарии (+5 more)

### Community 77 - "session"
Cohesion: 0.18
Nodes (13): fake_check_server(), _wire(), _maker(), _maker_for(), async_sessionmaker, AsyncSession, fixture, Подменяет фоновые циклы метками: видно, какие из них запустил… (+5 more)

### Community 78 - "whitelist_background_e2e.py"
Cohesion: 0.07
Nodes (45): app_db, Настраивает логирование приложения. - корневой логгер: WARNING (чтобы сторонние…, setup_logging(), argparse, asyncpg, ops_acceptance, Acts, _async() (+37 more)

### Community 79 - ".failed"
Cohesion: 0.18
Nodes (11): timedelta, Backoff повтора после ``attempts`` неудачных попыток: 1 мин → 1 ч., retry_delay(), Каждый существующий учёт сверен: ни ошибок, ни пропусков., Доменная модель, Проверки и ограничения, Ревью проекта — 7 октября 2026, Логика продления (+3 more)

### Community 80 - "apply_access"
Cohesion: 0.19
Nodes (21): MappingRepository, apply_access(), apply_access_to_server(), _build_spec(), client_email(), client_identity(), ensure_vpn_client(), _new_secret() (+13 more)

### Community 81 - "models.py"
Cohesion: 0.12
Nodes (33): app_bot, TimestampMixin, BindRequestStatus, app_services, Serialize access mutations per user, including commits and panel calls., Восстановление обычных VPN-продлений после сбоев панелей и рестартов. Один…, delete_for_self_reset(), find_reset_blocker() (+25 more)

### Community 82 - "_server_health_poller"
Cohesion: 0.15
Nodes (9): Фоновая сверка расхода whitelist-услуги: полный обход пачками. Работает…, Фоновая периодическая проверка доступности серверов 3x-ui. Только сохраняет…, _server_health_poller(), _whitelist_reconcile_poller(), next_reconcile_delay(), Пауза до следующего запуска обхода. Прерванный обход (панель недоступна)…, 17. Очередь применения не зависит от проверки здоровья серверов (2026-10-06), Очередь обслуживает только worker: при включённом health polling обработки нет… (+1 more)

### Community 84 - "delete_user_subscription"
Cohesion: 0.31
Nodes (9): _delete_local_subscription(), delete_user_subscription(), AsyncSession, Удаляет VPN-подписку пользователя с панелей и из БД бота. История оплат, заявки…, SubscriptionDeleteResult, AsyncSession, test_delete_subscription_keeps_local_client_on_panel_failure(), test_delete_subscription_removes_panel_and_local_client() (+1 more)

### Community 85 - "User"
Cohesion: 0.08
Nodes (26): aiogram_filters, Админ-раздел услуги «Обход белых списков». action: home | sync | choose (value…, WhitelistAdminCallback, IsAdmin, TelegramObject, Пропускает событие только если пользователь — администратор., notify_admins_new_bind_request(), User (+18 more)

### Community 86 - "test_user_reset_pg.py"
Cohesion: 0.11
Nodes (38): str, Почему самостоятельный сброс потерял бы оплату, начисление или заявку., ResetBlock, sqlalchemy_exc, _counts(), _fresh_id(), parametrize, Оплата подписки, сброс бота и trial конкурентно на PostgreSQL. Запуск:… (+30 more)

### Community 87 - "run_rollout"
Cohesion: 0.25
Nodes (9): Запускает услугу и выдаёт её нынешним активным пользователям. Повторный запуск…, run_rollout(), 3.4. Сервер, импорт, выдача, администрирование, 8. Проверки, parametrize, test_origin_of_current_access(), test_rollout_handles_ambiguous_users_by_admin_choice(), test_first_import_failure_then_retry_and_single_target() (+1 more)

### Community 88 - "Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026"
Cohesion: 0.50
Nodes (3): Прогон до исправления (SubHub `d9a2c80` + незакоммиченные правки, не относящиеся к задаче), Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026, Финальный прогон после исправления

### Community 89 - "test_trial_reset.py"
Cohesion: 0.09
Nodes (39): Почему сброс бота сейчас невозможен (короткий alert Telegram)., reset_blocked(), Пробный период, выданный Telegram-аккаунту. Хранится по Telegram ID отдельно от…, TrialGrant, session(), bridge(), call(), _file_db() (+31 more)

### Community 90 - "DiesOnFirstChange"
Cohesion: 0.25
Nodes (7): BaseException, DiesOnFirstChange, die(), ProcessKilled, Any, Имитация гибели процесса: не перехватывается ``except Exception`` кода бота., Настоящий updater, у которого первое изменение панели «убивает процесс».

### Community 91 - "parametrize"
Cohesion: 0.33
Nodes (6): _validate_server_name(), parametrize, test_parse_server_line_rejects_invalid(), test_validate_server_name_rejects_invalid(), test_validate_server_name_trims_valid_name(), test_validate_subscription_base_rejects_invalid()

### Community 92 - "Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026"
Cohesion: 0.33
Nodes (5): 1. 3x-ui v3.9.0 (`ghcr.io/mhsanaei/3x-ui:v3.9.0`), финальный прогон — 25 OK, 5 FAIL, 2. 3x-ui v3.9.0, повтор S6, S6b, S7 с исправленным расчётом — 5 OK, 0 FAIL, 3. 3x-ui v3.5.0 (`ghcr.io/mhsanaei/3x-ui:v3.5.0`, Xray 26.7.11) — 5 OK, 9 FAIL, 4. Первый (предварительный) прогон на v3.9.0 — 24 OK, 6 FAIL, Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026

### Community 93 - "provisioning.py"
Cohesion: 0.10
Nodes (40): ServerUpdateResult, bind_existing_client(), bind_user_by_public_id(), BindResult, _ensure_presence_mappings(), _expiry_to_ms(), _finalize_bound_client(), find_client_presence_on_servers() (+32 more)

### Community 94 - "Production deployment — 2026-10-06"
Cohesion: 0.33
Nodes (5): Backups and rollback, Checks after deployment, Deployment incidents and limits, Production deployment — 2026-10-06, Release

### Community 95 - "Q: собери контекст проекта"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: собери контекст проекта, Source Nodes

### Community 97 - "run_once"
Cohesion: 0.20
Nodes (7): Backoff повторов в памяти процесса для записей без поля ``next_retry_at``.…, RetryBackoff, AsyncSession, Панели изменены и изменения зафиксированы в БД — нужен SubHub sync., Один проход восстановления; ошибка одного шага не отменяет другой. Сначала…, RecoveryReport, run_once()

### Community 98 - "PendingServerUpdate"
Cohesion: 0.21
Nodes (10): PendingServerUpdate, PendingServerUpdateRepository, Ожидающие обновления, у которых истёк backoff, по всем серверам. Записи…, enqueue_failed_servers(), test_disabled_inbounds_are_not_bypassed_by_mapping_retry(), test_disabled_server_is_not_reenabled_by_pending_payment(), test_failed_queue_items_back_off_until_next_retry(), test_pending_reconciles_memberships_and_never_shortens_newer_expiry() (+2 more)

### Community 99 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 100 - "EncryptedString"
Cohesion: 0.29
Nodes (6): EncryptedString, Any, Прозрачно шифрует значение при записи и расшифровывает при чтении. - Если…, Важные инженерные правила проекта, 5. Миграции и резервная копия (PostgreSQL 16.15), TypeDecorator

### Community 102 - "menu_nav"
Cohesion: 0.10
Nodes (25): HTML-строка с анимированным значком для вставки в текст сообщения., tg(), notify_user_bind_approved(), access_extended(), admin_panel_home(), bind_request_approved(), connection_overview(), connection_preparing() (+17 more)

### Community 103 - "Услуга «Обход белых списков» — реализация и порядок внедрения"
Cohesion: 0.33
Nodes (4): 1. Что получает пользователь, 6. Порядок внедрения, 7. Откат, Услуга «Обход белых списков» — реализация и порядок внедрения

### Community 104 - "._clean_bot_token"
Cohesion: 0.33
Nodes (3): Разрешает задавать ADMIN_TELEGRAM_IDS как строку '1,2,3' или одно число., Убирает пробелы и обрамляющие кавычки вокруг токена., field_validator

### Community 106 - "Ids"
Cohesion: 0.33
Nodes (5): Ids, fixture, Идентификаторы фикстур: объекты сессии теста истекают после rollback., started(), fake()

### Community 107 - "reconcile_cycle"
Cohesion: 0.08
Nodes (25): problem(), Response, errors(), _BatchResult, _finish_reconcile(), Итог обхода учётов (накапливается между запусками, если обход прерывали).…, Учёты, чьё состояние этим обходом не подтверждено. Удалённые (``skipped_gone``)…, Следующая пачка учётов: стабильный курсор по id, а не по изменяемой метке. (+17 more)

### Community 108 - "Настройка серверов и авто-провижининг"
Cohesion: 0.33
Nodes (6): Как формируется клиент, Настройка серверов и авто-провижининг, Перенос пользователей, существовавших до бота, Шаг 1. Добавить серверы, Шаг 2. Импортировать inbound'ы каждого сервера, hysteria()

### Community 109 - "stack.sh"
Cohesion: 0.57
Nodes (5): running(), stack.sh script, start_panel(), start_subhub(), subhub_config()

### Community 111 - "scripts"
Cohesion: 0.50
Nodes (4): scripts, build, dev, preview

### Community 112 - "test_xui_client.py"
Cohesion: 0.22
Nodes (27): Ошибка авторизации в панели., XuiAuthError, HTTPXMock, test_login_error_does_not_leak_password(), _client(), _mock_csrf(), HTTPXMock, Регистрирует ответ /csrf-token (3x-ui 3.2.x запрашивает его перед login). (+19 more)

### Community 113 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 114 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 115 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.40
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 116 - "_whitelist_queue_worker"
Cohesion: 0.10
Nodes (22): Очередь применения квот «Обхода белых списков» на панели. Единственный…, _whitelist_queue_worker(), decorate(), wrapped(), user_operation(), D-3: потеря учёта подтверждена на штатном образе, Версии и изоляция, Вывод (+14 more)

### Community 117 - "api.ts"
Cohesion: 0.33
Nodes (4): APIError, Configuration, Plan, Profile

### Community 120 - "admin_nav"
Cohesion: 0.07
Nodes (36): admin_nav(), _edit_panel(), on_bind_action(), callback_query, CallbackQuery, InlineKeyboardMarkup, Редактирует сообщение админ-панели, мягко гасит ошибки. parse_mode=None —…, whitelist_admin() (+28 more)

### Community 121 - "_Crash"
Cohesion: 0.40
Nodes (4): _Crash, _CrashingPanel, Exception, Процесс «умер» посреди обращения к панели (не ошибка панели).

### Community 127 - "env.py"
Cohesion: 0.50
Nodes (3): do_run_migrations(), run_migrations_online(), sqlalchemy_pool

### Community 128 - "Протокол: R46 без принудительной синхронизации, фоновые циклы бота — 5 октября 2026"
Cohesion: 0.40
Nodes (4): Прогон 1 — до исправлений (бот и SubHub без изменений этой задачи), Прогон 2 — SubHub исправлен (D-6), бот: исправлен D-5, исправления D-7 и D-8 временно сняты, Прогон 3 — финальный, все исправления, Протокол: R46 без принудительной синхронизации, фоновые циклы бота — 5 октября 2026

### Community 129 - "_Crash"
Cohesion: 0.40
Nodes (3): RuntimeError, _Crash, Процесс завершился после запроса к панели, до commit.

### Community 130 - "test_ux.py"
Cohesion: 0.09
Nodes (39): MenuCallback, Навигация по inline-меню (редактирование сообщения на месте). action: home |…, custom_emoji_id(), emoji_char(), Возвращает unicode-символ значка (без анимации)., Возвращает custom_emoji_id значка или None, если значок не найден., connection_keyboard(), Главное меню под приветствием. Зависит от наличия активной подписки. (+31 more)

### Community 131 - "test_verdicts_agree_with_subhub_link_builder"
Cohesion: 0.40
Nodes (5): skipif, Path, Проверка против исходников SubHub (не рабочего экземпляра и его config.yaml)., _subhub_runner(), test_verdicts_agree_with_subhub_link_builder()

### Community 142 - "AwaitingCredit"
Cohesion: 0.67
Nodes (3): AwaitingCredit, Сохранённое начисление, ещё не сверенное с расходом., test_disabled_server_is_not_touched()

## Knowledge Gaps
- **187 isolated node(s):** `credentials`, `dvpn/site`, `name`, `version`, `private` (+182 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1080 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Server` connect `Server` to `test_whitelist_retarget.py`, `test_provisioning.py`, `whitelist.py`, `test_legacy_bind.py`, `test_ux.py`, `test_whitelist.py`, `admin_handlers.py`, `keyboards.py`, `test_whitelist_reconcile.py`, `pending_updates.py`, `WhitelistLedger`, `get_sessionmaker`, `whitelist_e2e.py`, `WhitelistAccount`, `ClientServerMapping`, `XuiClient`, `xui_updater.py`, `AsyncSession`, `test_whitelist_inbound_compat.py`, `test_whitelist_bot.py`, `PanelUpdateError`, `web_bridge.py`, `XuiPanelUpdater`, `test_renewal_recovery_worker.py`, `sync_inventory`, `PanelUpdater`, `PaymentRequest`, `ServerInbound`, `placement_progress`, `MockPanelUpdater`, `ServerProvision`, `grant_trial`, `Контекст проекта`, `apply_access`, `models.py`, `delete_user_subscription`, `test_user_reset_pg.py`, `run_rollout`, `test_trial_reset.py`, `provisioning.py`, `PendingServerUpdate`, `EncryptedString`, `menu_nav`, `reconcile_cycle`, `admin_nav`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `User` connect `User` to `test_provisioning.py`, `test_ux.py`, `test_legacy_bind.py`, `whitelist.py`, `user_handlers.py`, `admin_handlers.py`, `test_whitelist.py`, `test_whitelist_reconcile.py`, `billing.py`, `_trial_available`, `VpnClientRepository`, `pending_updates.py`, `WhitelistLedger`, `get_sessionmaker`, `whitelist_e2e.py`, `WhitelistAccount`, `ClientServerMapping`, `test_trial_grants_migration.py`, `AsyncSession`, `test_whitelist_bot.py`, `test_trial_paid_reset.py`, `web_bridge.py`, `Server`, `scenario`, `test_renewal_recovery_worker.py`, `UserRepository`, `_pay`, `VpnClient`, `PaymentRequest`, `create_request`, `MockPanelUpdater`, `grant_trial`, `test_subscription_purchases_migration.py`, `whitelist_background_e2e.py`, `apply_access`, `models.py`, `delete_user_subscription`, `test_user_reset_pg.py`, `test_trial_reset.py`, `provisioning.py`, `menu_nav`, `admin_nav`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `MockPanelUpdater` connect `MockPanelUpdater` to `test_whitelist_retarget.py`, `test_provisioning.py`, `test_legacy_bind.py`, `test_whitelist.py`, `panel`, `_PoisonedPanel`, `test_whitelist_reconcile.py`, `SubHubClient`, `_trial_available`, `_HangingPanel`, `test_site_trial_race_with_payment_maps_to_conflict`, `LocalSubHub`, `WhitelistLedger`, `ClientServerMapping`, `test_whitelist_inbound_compat.py`, `test_whitelist_bot.py`, `PanelUpdateError`, `test_trial_paid_reset.py`, `web_bridge.py`, `test_whitelist_queue_worker.py`, `Server`, `test_whitelist_payment_status.py`, `test_renewal_recovery_worker.py`, `_pay`, `VpnClient`, `sync_inventory`, `PanelUpdater`, `PaymentRequest`, `create_request`, `grant_trial`, `apply_access`, `models.py`, `_server_health_poller`, `delete_user_subscription`, `test_user_reset_pg.py`, `run_rollout`, `test_trial_reset.py`, `provisioning.py`, `PendingServerUpdate`, `reconcile_cycle`, `_whitelist_queue_worker`, `_Crash`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 198 inferred relationships involving `User` (e.g. with `add_inbound()` and `admin_add_server_line()`) actually correct?**
  _`User` has 198 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `MockPanelUpdater` (e.g. with `ClientServerMapping` and `Server`) actually correct?**
  _`MockPanelUpdater` has 29 INFERRED edges - model-reasoned connections that need verification._
- **Are the 100 inferred relationships involving `VpnClient` (e.g. with `notify_user_extended()` and `access_extended()`) actually correct?**
  _`VpnClient` has 100 INFERRED edges - model-reasoned connections that need verification._
- **Are the 61 inferred relationships involving `Server` (e.g. with `_finalize_new_server()` and `_finalize_whitelist_server()`) actually correct?**
  _`Server` has 61 INFERRED edges - model-reasoned connections that need verification._
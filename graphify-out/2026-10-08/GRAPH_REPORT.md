# Graph Report - VpnBot  (2026-10-08)

## Corpus Check
- 216 files · ~228,059 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 23 file(s) not represented in the graph (top: (none) 9, .example 3, .patch 3)

## Summary
- 3541 nodes · 13159 edges · 170 communities (135 shown, 35 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1731 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6510d9e0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_whitelist_retarget.py
- test_provisioning.py
- WhitelistLedger
- BindRequestRepository
- test_whitelist.py
- menu_nav
- admin_handlers.py
- Protocol
- keyboards.py
- ReconcileStatus
- _extend_and_finalize
- test_trial_failed_payment.py
- trial_available
- test_renewal_recovery_pg.py
- alembic
- PendingServerUpdate
- test_whitelist_pg.py
- test_whitelist_epoch.py
- main.go
- App.vue
- test_crypto.py
- main.py
- release_applied_credits
- antishare.py
- XuiClient
- test_trial_grants_migration.py
- XuiPanelUpdater
- .down
- ClientServerMapping
- ServerInbound
- xui_traffic_d3.py
- Bot
- Контекст проекта
- PanelUpdateError
- _trial_available
- web_bridge.py
- test_whitelist_queue_worker.py
- test_whitelist_xui.py
- Server
- test_whitelist_payment_status.py
- package.json
- ResetBlock
- compilerOptions
- main_test.go
- api
- EncryptedString
- .auth
- test_renewal_recovery_worker.py
- Задание агенту: услуга «Обход белых списков» в VpnBot
- app
- main
- scenario
- web_preview.mjs
- UserRepository
- _describe_event
- What You Must Do When Invoked
- Settings
- sync_inventory
- PanelUpdater
- Telegram VPN Billing Bot
- whitelist_migration_check.py
- Report
- D VPN — личный кабинет
- texts.py
- Panel
- whitelist.py
- get_account
- dvpn/site
- telegram-vpn-billing-bot
- PaymentRequest
- test_xui_updater.py
- graphify reference: extra exports and benchmark
- test_expiry.py
- test_subscription_purchases_migration.py
- Контекст проекта
- session
- _phases
- User
- test_first_import_failure_then_retry_and_single_target
- send_broadcast
- timedelta
- AGENTS.md
- VpnClient
- MockPanelUpdater
- test_user_reset_pg.py
- test_failed_busy_retry_is_not_successful_cycle
- Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026
- models.py
- LocalSubHub
- utcnow
- Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026
- QuotaClientState
- Production deployment — 2026-10-06
- Q: собери контекст проекта
- test_whitelist_reconcile.py
- Приёмка услуги «Обход белых списков» — 5 октября 2026
- RecordingPanel
- graphify reference: query, path, explain
- placement_progress
- test_ui.py
- test_whitelist_retarget_pg.py
- Повторное ревью — 6 октября 2026
- .panel_changes
- whitelist_e2e_2026-10-05.md
- Ids
- reconcile_cycle
- session
- stack.sh
- whitelist_migration_2026-10-05.md
- scripts
- test_xui_client.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- user_operation
- check_server
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- admin_nav
- _CrashingPanel
- extraction-spec.md
- whitelist_e2e.py
- DiesOnFirstChange
- _Crash
- Повторная приёмка whitelist — 6 октября 2026
- e3f4a5b6c7d8_subscription_purchases.py
- _alembic
- Обновление whitelist-панели — 6 октября 2026
- Проверка исправленной 3x-ui — 6 октября 2026
- _PoisonedPanel
- _reconciled
- Динамические названия whitelist — 6 октября 2026
- _HangingPanel
- vue
- FakeBot
- _server_health_poller
- Обновление production — 4 октября 2026
- Ревью VpnBot — 4 октября 2026
- find_reset_blocker
- Оставшиеся риски и решения
- Приёмка на Android / Happ 4.6.0
- Ограниченное подключение whitelist к production — 6 октября 2026
- test_poller_uses_settings_global_status_and_adaptive_delay
- ref_node_fs_promises
- api.ts
- Финальное сохранение расхода 3x-ui — 6 октября 2026
- AuditLog
- Включение whitelist для действующих пользователей — 6 октября 2026
- pg
- Настройка серверов и авто-провижининг
- cycles
- _FakeMessage
- active_user
- GatedPanel
- Handler

## God Nodes (most connected - your core abstractions)
1. `User` - 322 edges
2. `MockPanelUpdater` - 244 edges
3. `VpnClient` - 173 edges
4. `Server` - 161 edges
5. `Settings` - 154 edges
6. `PaymentRequest` - 150 edges
7. `PaymentStatus` - 145 edges
8. `_pay()` - 110 edges
9. `VpnClientRepository` - 86 edges
10. `XuiClient` - 83 edges

## Surprising Connections (you probably didn't know these)
- `Изменения` --references--> `EncryptedString`  [INFERRED]
  docs/acceptance/whitelist_integration_2026-10-06.md → app/db/types.py
- `P1 — пароли панелей не защищены шифрованием приложения` --references--> `EncryptedString`  [INFERRED]
  docs/REVIEW_2026-10-04.md → app/db/types.py
- `Смена целевого inbound и перенос клиентов (2026-10-06)` --references--> `_push()`  [INFERRED]
  docs/WHITELIST_SERVICE.md → app/services/whitelist.py
- `Как формируется клиент` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py
- `3.4. Сервер, импорт, выдача, администрирование` --references--> `rollout()`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → tests/test_whitelist_acceptance_pg.py

## Import Cycles
- None detected.

## Communities (170 total, 35 thin omitted)

### Community 0 - "test_whitelist_retarget.py"
Cohesion: 0.13
Nodes (57): choose_inbound(), get_active_server(), process_due(), Фоновая очередь: применяет несинхронизированные состояния с backoff. Кроме…, Включённый whitelist-сервер (не более одного по уникальному индексу)., Делает выбранный inbound единственной целью whitelist-сервера. Готовность…, P1: смена целевого inbound не переносит существующих пользователей, 19. Перенос клиентов при смене целевого inbound (2026-10-06, P1 ревью) (+49 more)

### Community 1 - "test_provisioning.py"
Cohesion: 0.06
Nodes (71): MappingRepository, apply_access(), apply_access_to_server(), bind_existing_client(), bind_user_by_public_id(), BindResult, client_email(), client_identity() (+63 more)

### Community 2 - "WhitelistLedger"
Cohesion: 0.11
Nodes (28): Бизнес-учёт трафика пользователя на whitelist-сервере. Остатки…, Журнал выдач/начислений/корректировок, привязанных к исходной операции. Выдача…, WhitelistAccount, WhitelistLedger, apply_event(), _consistent_anchor(), is_open(), confirmed_snapshots() (+20 more)

### Community 3 - "BindRequestRepository"
Cohesion: 0.07
Nodes (30): BindRequest, Заявка на привязку существующей подписки (до внедрения бота)., BindRequestRepository, AsyncSession, Меняет только имя, сохраняя сервер и все его связи., Меняет URL подписки, не затрагивая связи сервера., approve_request(), BindApproveResult (+22 more)

### Community 4 - "test_whitelist.py"
Cohesion: 0.08
Nodes (81): AwaitingCredit, list_open_events(), Фоновая сверка расхода: обходит все учёты пачками по ``limit``. Возвращает…, Сохранённое начисление, ещё не сверенное с расходом., Остатки пользователя; при доступной панели — с актуальной сверкой. Чтение…, Неприменённые события учёта пользователя в порядке возникновения., reconcile_usage(), user_overview() (+73 more)

### Community 5 - "menu_nav"
Cohesion: 0.08
Nodes (51): admin_panel_home(), bind_request_received(), bind_request_waiting(), connection_preparing(), connection_unavailable(), free_proxies_intro(), install_guides_intro(), news_channel_prompt() (+43 more)

### Community 6 - "admin_handlers.py"
Cohesion: 0.09
Nodes (69): aiogram_fsm_context, add_inbound(), add_server(), admin_add_server_cancel(), admin_add_server_line(), admin_broadcast_cancel(), admin_broadcast_send(), admin_delete_subscription_by_client_id() (+61 more)

### Community 7 - "Protocol"
Cohesion: 0.11
Nodes (34): Protocol, ProvisionTarget, Описание клиента, которого нужно создать/обновить в конкретном inbound., build_client_object(), client_identifier(), _client_uuid_for_api(), _looks_like_db_id(), merge_client_record_for_update() (+26 more)

### Community 8 - "keyboards.py"
Cohesion: 0.09
Nodes (61): BindCallback, MenuCallback, Callback админских действий над заявкой на привязку подписки., Навигация по inline-меню (редактирование сообщения на месте). action: home |…, _adm(), admin_add_server_type_keyboard(), admin_back_keyboard(), admin_bind_keyboard() (+53 more)

### Community 9 - "ReconcileStatus"
Cohesion: 0.20
Nodes (21): Состояние и наблюдаемость фоновой сверки (хранится в памяти процесса).…, ReconcileStatus, _add_account(), _cycle(), _email(), _populate(), Прямой вызов повтора: полностью нечитаемая пачка — ошибки, а не пропуск., test_account_that_stays_busy_is_reported_as_skipped() (+13 more)

### Community 10 - "_extend_and_finalize"
Cohesion: 0.12
Nodes (32): _apply_panels(), BillingError, BillingResult, compute_new_expiry(), _confirm_traffic(), _count_eligible_mappings(), _evaluate_panel_results(), _extend_and_finalize() (+24 more)

### Community 11 - "test_trial_failed_payment.py"
Cohesion: 0.12
Nodes (31): Пробный период, выданный Telegram-аккаунту. Хранится по Telegram ID отдельно от…, TrialGrant, Подписку уже оформляли этот пользователь или его Telegram ID. Оформлена — есть…, subscription_already_purchased(), _accepted_failed(), _legacy_client(), _purchases(), parametrize (+23 more)

### Community 12 - "trial_available"
Cohesion: 0.15
Nodes (20): accepted_subscription_clause(), Условие SQL: заявка — принятая администратором оплата подписки. Принятие…, Оформлялась ли подписка: есть принятая оплата подписки (не трафика). Принятая…, Пробный период уже выдавался этому пользователю или его Telegram ID.…, Единое правило допуска trial: он не использован и подписку ещё не оформляли.…, trial_already_used(), trial_available(), Каждый существующий учёт сверен: ни ошибок, ни пропусков. (+12 more)

### Community 13 - "test_renewal_recovery_pg.py"
Cohesion: 0.14
Nodes (51): _advisory(), _audit(), _client_expiry(), _confirm(), _crash_during_confirmation(), Env, _expiry_calls(), _idle_in_transaction() (+43 more)

### Community 15 - "PendingServerUpdate"
Cohesion: 0.09
Nodes (36): PendingServerUpdate, PendingServerUpdateRepository, Ожидающие обновления, у которых истёк backoff, по всем серверам. Записи…, Any, Запускает worker, если такой ещё не работает в этом процессе., _start_exclusive(), apply_pending_for_server(), apply_pending_update() (+28 more)

### Community 16 - "test_whitelist_pg.py"
Cohesion: 0.22
Nodes (15): AttachmentType, attach_proof(), Прикрепляет подтверждение оплаты (текст/фото/документ) к заявке., test_bot_cannot_change_submitted_web_payment(), _confirm(), Конкуренция операций услуги на PostgreSQL (SQLite не доказывает блокировки).…, Сбой статистики: параллельные продление, покупка, очередь и сверка., _state() (+7 more)

### Community 17 - "test_whitelist_epoch.py"
Cohesion: 0.13
Nodes (22): Применяет состояние учёта пользователя на whitelist-панели., sync_user(), _available(), parametrize, Смена эпохи счётчика whitelist-панели при неприменённых событиях учёта. Внешний…, Пересоздание клиента: значение не уменьшилось, сменилась строка статистики., Сброс обнаруживается по последнему прочитанному значению, а не только по…, Строка до миграции f3a4b5c6d7e8: последнее чтение есть только в границах… (+14 more)

### Community 18 - "main.go"
Cohesion: 0.07
Nodes (29): credentials, go_pkg_bytes, go_pkg_context, go_pkg_crypto_hmac, go_pkg_crypto_rand, go_pkg_crypto_sha256, go_pkg_crypto_subtle, go_pkg_crypto_tls (+21 more)

### Community 19 - "App.vue"
Cohesion: 0.07
Nodes (24): authTitles, awaiting, busy, code, comment, config, connection, days (+16 more)

### Community 20 - "test_crypto.py"
Cohesion: 0.14
Nodes (24): decrypt(), encrypt(), _fernet(), is_encrypted(), Возвращает Fernet, выведенный из SECRET_KEY, либо None если ключ не задан.…, Шифрует строку. Без SECRET_KEY возвращает значение как есть (dev/тесты)., Расшифровывает строку. Legacy-значения в открытом виде возвращает как есть., cryptography_fernet (+16 more)

### Community 21 - "main.py"
Cohesion: 0.06
Nodes (54): aiogram_client_default, aiogram_fsm_storage_memory, aiogram_types, aiogram_utils_token, DbSessionMiddleware, Any, Открывает сессию БД, получает/создаёт пользователя и кладёт их в data., build_root_router() (+46 more)

### Community 22 - "release_applied_credits"
Cohesion: 0.22
Nodes (9): Снимает ожидание с заявок, начисление которых уже применено на панели (без…, release_applied_credits(), 1. Что получает пользователь, 3. Модель учёта, 6. Порядок внедрения, 7. Откат, 8. Проверки, Смена целевого inbound и перенос клиентов (2026-10-06) (+1 more)

### Community 23 - "antishare.py"
Cohesion: 0.26
Nodes (20): IpObservation, _active_clients(), collect_all(), collect_for_client(), compute_status(), _level_for(), list_all_statuses(), list_flagged() (+12 more)

### Community 24 - "XuiClient"
Cohesion: 0.06
Nodes (45): Реальный провайдер: берёт IP клиента из журнала панели 3x-ui., XuiIpProvider, Any, Exception, Response, _quote_path_segment(), Авторизованный запрос: гарантирует login и при истёкшей сессии выполняет…, Берёт CSRF-токен с /csrf-token (3x-ui >= 3.2.x). На старых панелях endpoint… (+37 more)

### Community 25 - "test_trial_grants_migration.py"
Cohesion: 0.21
Nodes (15): _execute(), _expected(), _naive_utc(), datetime, parametrize, Миграция ``trial_grants`` переносит существующие факты использования trial.…, PostgreSQL: удаление пользователя обнуляет actor_user_id (ON DELETE SET NULL)., SQLite возвращает строку без пояса, PostgreSQL — datetime с поясом. (+7 more)

### Community 26 - "XuiPanelUpdater"
Cohesion: 0.12
Nodes (19): Один клиент панели (глобальный по email), привязанный к её inbound'ам.…, ServerProvision, client_record_body(), Извлекает model.Client из ответа ``clients/get``., _client_flows(), _inbound_client_flow(), _is_missing_client_error(), _other_flow() (+11 more)

### Community 28 - "ClientServerMapping"
Cohesion: 0.10
Nodes (12): ClientServerMapping, IpProvider, MockIpProvider, Источник списка IP-адресов клиента (для антишеринг-мониторинга)., Mock-провайдер для тестов: возвращает заранее заданные IP по server_id., Удаляет клиента с сервера по сохранённым привязкам., Удаляет пользователя и связанные данные только из БД бота. 3x-ui панели не…, reset_user_bot_state() (+4 more)

### Community 29 - "ServerInbound"
Cohesion: 0.14
Nodes (33): Inbound на панели сервера, в который нужно заводить клиентов. На одном сервере…, ServerInbound, build_provision_spec(), server_ready(), target_inbound(), cryptography_hazmat_primitives, cryptography_hazmat_primitives_asymmetric_x25519, Совместимость inbound с SubHub (2026-10-05) (+25 more)

### Community 30 - "xui_traffic_d3.py"
Cohesion: 0.12
Nodes (39): accounted(), add_client(), container_started(), delta(), _disable_case(), Lab, m1_planned_restart(), set_inbound() (+31 more)

### Community 31 - "Bot"
Cohesion: 0.05
Nodes (64): aiogram_filters, aiogram_filters_callback_data, aiogram_fsm_state, AdminCallback, OnboardCallback, PaymentCallback, PlanCallback, Callback выбора тарифа пользователем. code — код тарифа из PLANS (1m/6m/12m)… (+56 more)

### Community 32 - "Контекст проекта"
Cohesion: 0.13
Nodes (14): Архитектура, Безопасность аутентификации (backend/main.go), Важные инженерные правила, Доменная модель (таблицы веб-части, в БД бота), Запуск, Контекст проекта, Конфигурация, Локальные артефакты (+6 more)

### Community 33 - "PanelUpdateError"
Cohesion: 0.06
Nodes (27): effective_flow(), PanelUpdateError, Exception, Ошибка обновления клиента в панели., flow, который 3x-ui копирует при attach: первый непустой по id inbound'а., fetch_inbounds(), find_panel_client(), _find_panel_client_by_sub_id() (+19 more)

### Community 34 - "_trial_available"
Cohesion: 0.10
Nodes (41): trial_subscription_purchased(), Пробный доступен, если им не пользовались и подписку никогда не оформляли., _trial_available(), _paid_and_reset(), _purchases(), Доступ без оплаты подписки (привязанная подписка) и покупка трафика., Оплата подписки без trial → настоящий обработчик сброса → новый User., test_first_payment_is_kept_on_later_payments() (+33 more)

### Community 35 - "web_bridge.py"
Cohesion: 0.06
Nodes (49): aiohttp, notify_user_rejected(), PaymentAttachment, Durable per-admin Telegram delivery, retried independently of HTTP requests., WebAccount, WebDelivery, WebLinkRequest, get_plan() (+41 more)

### Community 36 - "test_whitelist_queue_worker.py"
Cohesion: 0.12
Nodes (25): pytest_asyncio, _expire(), _purchase_while_panel_down(), fixture, Очередь применения whitelist-квот не зависит от проверки здоровья серверов.…, Ждёт, пока worker зафиксирует применение в БД (на панели оно видно раньше…, Подменяет фоновые циклы метками: видно, какие из них запустил…, Завершение не зависает на зависшем запросе панели: задача отменяется. (+17 more)

### Community 37 - "test_whitelist_xui.py"
Cohesion: 0.21
Nodes (34): QuotaTarget, Абсолютное целевое состояние клиента с учётом трафика. ``total_bytes`` —…, 3.5. Учёт трафика и интеграция 3x-ui, _apply_existing(), _auth(), _body(), _inbound(), HTTPXMock (+26 more)

### Community 38 - "Server"
Cohesion: 0.05
Nodes (58): _parse_server_line(), Парсит 'name|country|panel_url|username|password|[kind]|[sub]|[purpose]'.…, custom_emoji_id(), emoji_char(), Возвращает unicode-символ значка (без анимации)., Возвращает custom_emoji_id значка или None, если значок не найден., connection_keyboard(), Главное меню под приветствием. Зависит от наличия активной подписки. (+50 more)

### Community 39 - "test_whitelist_payment_status.py"
Cohesion: 0.29
Nodes (21): _purchase_during_outage(), _buy(), _down(), _fresh(), _is_waiting(), _queue(), Статус заявки на покупку трафика следует за фактическим применением начисления., Запись квоты прошла, но расход не сверен: начисление ещё не учтено. (+13 more)

### Community 40 - "package.json"
Cohesion: 0.11
Nodes (17): lucide-vue-next, typescript, vite, @vitejs/plugin-vue, vue-tsc, dependencies, lucide-vue-next, vue (+9 more)

### Community 41 - "ResetBlock"
Cohesion: 0.20
Nodes (16): Почему сброс бота сейчас невозможен (короткий alert Telegram)., reset_blocked(), str, Почему самостоятельный сброс потерял бы оплату, начисление или заявку., ResetBlock, _assert_purchase_kept(), parametrize, test_concurrent_purchase_confirmation_and_reset_keep_purchase() (+8 more)

### Community 42 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, esModuleInterop, jsx, lib, module, moduleResolution, resolveJsonModule, skipLibCheck (+4 more)

### Community 43 - "main_test.go"
Cohesion: 0.21
Nodes (11): go_pkg_net_http, go_pkg_net_http_httptest, go_pkg_strings, go_pkg_testing, go_pkg_time, testing.T, canonicalEmail(), TestCodesBoundToAccountAndPurpose() (+3 more)

### Community 44 - "api"
Cohesion: 0.32
Nodes (12): api(), authenticate(), copy(), getConnection(), go(), link(), logout(), pay() (+4 more)

### Community 45 - "EncryptedString"
Cohesion: 0.25
Nodes (7): EncryptedString, Any, Прозрачно шифрует значение при записи и расшифровывает при чтении. - Если…, Важные инженерные правила проекта, Выполненные проверки, 5. Миграции и резервная копия (PostgreSQL 16.15), TypeDecorator

### Community 46 - ".auth"
Cohesion: 0.53
Nodes (6): net/http.Request, net/http.ResponseWriter, decode(), digest(), fail(), respond()

### Community 47 - "test_renewal_recovery_worker.py"
Cohesion: 0.14
Nodes (48): Запускает фоновые циклы процесса бота (кроме доставки сайта). Одна сборка для…, start_background_tasks(), stop_background_tasks(), _as_aware(), expiry_to_ms(), Гарантирует timezone-aware datetime (SQLite возвращает naive)., Конвертирует дату в миллисекунды Unix-времени (формат 3x-ui expiryTime)., Task (+40 more)

### Community 48 - "Задание агенту: услуга «Обход белых списков» в VpnBot"
Cohesion: 0.15
Nodes (12): 1. Контекст проекта, 2. Согласованное поведение услуги, 3. Сервер и настройки администратора, 4. Технический контракт учёта трафика, 5. Биллинг, конкуренция и восстановление, 6. Пользовательский интерфейс, 7. Обязательная проверка, 8. Порядок работы и сдача (+4 more)

### Community 49 - "app"
Cohesion: 0.29
Nodes (6): app, config, context.Context, github.com/jackc/pgx/v5/pgxpool.Pool, net/http.Client, pgx.Tx

### Community 50 - "main"
Cohesion: 0.22
Nodes (7): bucket, limiter, net/http.Handler, sync.Mutex, time.Time, env(), main()

### Community 51 - "scenario"
Cohesion: 0.07
Nodes (40): docker(), prepare(), Path, import_control_inbound(), main(), panel_view(), Any, Path (+32 more)

### Community 52 - "web_preview.mjs"
Cohesion: 0.29
Nodes (6): ref_node_fs, ref_node_http, ref_node_path, ref_node_url, root, types

### Community 53 - "UserRepository"
Cohesion: 0.16
Nodes (9): Удаляет пользователя и связанные записи (каскад в ORM)., Telegram ID всех пользователей, когда-либо запускавших бота., Генерирует короткий уникальный публичный ID пользователя., UserRepository, test_generated_public_id_is_unique_and_hex(), AsyncSession, test_backfills_public_id_for_existing(), test_get_or_create_assigns_public_id() (+1 more)

### Community 54 - "_describe_event"
Cohesion: 0.22
Nodes (15): _command_name(), _describe_callback(), _describe_event(), _describe_message(), CallbackQuery, Message, TelegramObject, Chat (+7 more)

### Community 55 - "What You Must Do When Invoked"
Cohesion: 0.07
Nodes (25): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+17 more)

### Community 56 - "Settings"
Cohesion: 0.05
Nodes (67): IsAdmin, Пропускает событие только если пользователь — администратор., forward_proof_to_admins(), admin_denied(), Разрешает задавать ADMIN_TELEGRAM_IDS как строку '1,2,3' или одно число., Конфигурация приложения из переменных окружения / .env., Убирает пробелы и обрамляющие кавычки вокруг токена., Settings (+59 more)

### Community 57 - "sync_inventory"
Cohesion: 0.10
Nodes (30): Сверка реестра с уже прочитанным списком (см. :func:`import_inbounds`)., reconcile_inbounds(), _ss_method(), check_inbound(), _check_vless_reality(), describe(), _foreign_flows(), InboundCompat (+22 more)

### Community 58 - "PanelUpdater"
Cohesion: 0.08
Nodes (57): Any, AsyncSession, Записывает событие в audit_logs., record(), Повторно выставляет текущий срок доступа клиента во всех панелях., sync_client(), serialized_access(), PanelUpdater (+49 more)

### Community 59 - "Telegram VPN Billing Bot"
Cohesion: 0.13
Nodes (14): Запуск, Telegram VPN Billing Bot, Админ-команды, Антишеринг-мониторинг, Граф кода (graphify), Единая подписка SubHub, Запуск через Docker Compose, Конфигурация (+6 more)

### Community 60 - "whitelist_migration_check.py"
Cohesion: 0.20
Nodes (23): alembic_config, alembic_script, Единственная строка настроек услуги (id = 1)., WhitelistConfig, alembic(), check(), docker(), downgrade_cycle() (+15 more)

### Community 62 - "Report"
Cohesion: 0.25
Nodes (4): Any, Конфигурация xray-клиента: SOCKS 127.0.0.1:10808 → VLESS по ссылке., Report, xray_client_config()

### Community 63 - "D VPN — личный кабинет"
Cohesion: 0.25
Nodes (7): D VPN — личный кабинет, Архитектура, Запуск вместе с существующим ботом, Локальная разработка, Результаты проверки, Что реализовано, Эксплуатация

### Community 64 - "texts.py"
Cohesion: 0.04
Nodes (94): HTML-строка с анимированным значком для вставки в текст сообщения., tg(), notify_first_purchase_channel(), notify_user_bind_approved(), notify_user_extended(), notify_user_subscription_deleted(), notify_user_traffic_credited(), access_extended() (+86 more)

### Community 65 - "Panel"
Cohesion: 0.08
Nodes (15): admin_servers(), build_client_record(), Унифицированный объект клиента для нового client-API (3x-ui >= 3.2.x).…, 14. Исправление D-2: SubHub собирается без ручной установки greenlet (результаты от 2026-10-05, после приёмки), Panel, Прямой доступ к тестовой панели — для проверок и действий «вручную в панели»., Разрешает трафик к частной подсети стенда — только на тестовых панелях.…, VLESS + REALITY (TCP), как у рабочих серверов; цель — локальный TLS 1.3. (+7 more)

### Community 66 - "whitelist.py"
Cohesion: 0.09
Nodes (50): Привязка клиента whitelist-панели к inbound'у, созданная самой услугой. Строка…, WhitelistPlacement, access_state(), AccessState, _applied_target(), apply_usage(), _aware(), classify_origin() (+42 more)

### Community 67 - "get_account"
Cohesion: 0.15
Nodes (11): get_account(), 4. Автоматические тесты, _ledger(), Приёмка: гонки услуги на PostgreSQL, не покрытые test_whitelist_pg. Те же…, test_admin_block_is_not_lost_to_queue_reads_or_reconcile(), test_concurrent_rollouts_grant_once_and_keep_purchase(), rollout(), test_purchase_confirmed_after_expiry_races_queue_without_enabling() (+3 more)

### Community 71 - "PaymentRequest"
Cohesion: 0.08
Nodes (24): PaymentRequest, Берёт заявку с блокировкой строки (SELECT ... FOR UPDATE). На Postgres…, Удаляет заявку (вместе с вложениями по каскаду)., Последняя успешная (применённая/подтверждённая) оплата пользователя.…, cancel_open_request(), create_traffic_request(), _new_payment_code(), _open_request_for_update() (+16 more)

### Community 72 - "test_xui_updater.py"
Cohesion: 0.17
Nodes (12): ProvisionInbound, Inbound сервера, к которому нужно привязать клиента., _build_spec(), pytest_httpx, test_attach_success_without_membership_is_not_provisioning_success(), _mock_auth(), HTTPXMock, _spec() (+4 more)

### Community 73 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 74 - "test_expiry.py"
Cohesion: 0.17
Nodes (17): _as_aware(), process_expiry_notifications(), AsyncSession, datetime, Стадия уведомления по остатку времени до окончания. 0 — рано, 1 — остался день,…, Шлёт уведомления «за день / за час / в момент окончания». Каждая стадия…, _target_stage(), FakeBot (+9 more)

### Community 75 - "test_subscription_purchases_migration.py"
Cohesion: 0.23
Nodes (14): _at(), _expected(), _payment(), datetime, parametrize, Миграция ``subscription_purchases`` переносит сохранившиеся оплаты подписки.…, timestamptz: явный UTC, независимо от часового пояса сервера., _seed() (+6 more)

### Community 76 - "Контекст проекта"
Cohesion: 0.15
Nodes (12): Админские команды, Антишеринг, Интеграция с 3x-ui, Контекст проекта, Конфигурация, Локальные артефакты, Назначение, Основные пользовательские сценарии (+4 more)

### Community 77 - "session"
Cohesion: 0.31
Nodes (9): fake_check_server(), _wire(), _maker(), _maker_for(), async_sessionmaker, AsyncSession, БД в файле с отдельными соединениями у теста и у фонового worker'а. Общее…, session() (+1 more)

### Community 78 - "_phases"
Cohesion: 0.08
Nodes (33): Acts, _async(), describe(), docker(), expect_poll(), expect_trigger(), _forbid_sync(), from_source() (+25 more)

### Community 79 - "User"
Cohesion: 0.08
Nodes (67): TelegramObject, notify_admins_new_request(), PaymentStatus, User, PaymentRepository, Число применённых оплат подписки (покупки трафика не учитываются)., confirm_payment(), Идемпотентное подтверждение оплаты администратором. Повторный вызов для уже… (+59 more)

### Community 80 - "test_first_import_failure_then_retry_and_single_target"
Cohesion: 0.33
Nodes (7): 3.4. Сервер, импорт, выдача, администрирование, _payment(), parametrize, test_origin_of_current_access(), test_rollout_handles_ambiguous_users_by_admin_choice(), test_first_import_failure_then_retry_and_single_target(), test_second_enabled_whitelist_server_is_rejected()

### Community 81 - "send_broadcast"
Cohesion: 0.29
Nodes (6): BroadcastResult, Рассылает текстовое сообщение всем пользователям. Сообщение отправляется…, send_broadcast(), FakeBot, test_send_broadcast_counts_sent_and_failed(), test_send_broadcast_empty_list()

### Community 82 - "timedelta"
Cohesion: 0.22
Nodes (5): timedelta, Сколько прошло с завершения последнего обхода (в т. ч. с пропусками)., Верхняя граница возраста данных *сверенных* учётов последнего обхода., Сколько прошло с завершения последнего полностью подтверждённого обхода., Верхняя граница возраста данных всех учётов после последнего подтверждённого…

### Community 84 - "VpnClient"
Cohesion: 0.11
Nodes (15): _is_active(), VpnClient, datetime, Клиенты, которым пора слать уведомление об окончании. Берём тех, у кого задан…, Сохраняет результат фоновой проверки доступности сервера., _utcnow(), _delete_local_subscription(), AsyncSession (+7 more)

### Community 85 - "MockPanelUpdater"
Cohesion: 0.11
Nodes (26): grant_trial(), Выдаёт бесплатный пробный период один раз на Telegram-аккаунт и до первой…, MockPanelUpdater, datetime, Mock-реализация: ничего не делает либо имитирует сбой нужных серверов. Для…, Inbound удалён на панели: его привязки исчезают у всех клиентов., main(), confirm() (+18 more)

### Community 86 - "test_user_reset_pg.py"
Cohesion: 0.13
Nodes (31): _counts(), _fresh_id(), parametrize, Оплата подписки, сброс бота и trial конкурентно на PostgreSQL. Запуск:…, Trial до оплаты разрешён; после оплаты и сброса trial закрыт в обоих порядках., Две заявки одного пользователя подтверждаются параллельно: одна запись., test_concurrent_confirmations_record_one_purchase(), test_parallel_trials_after_paid_reset_are_all_refused() (+23 more)

### Community 87 - "test_failed_busy_retry_is_not_successful_cycle"
Cohesion: 0.22
Nodes (10): P2: неудачный повтор чтения объявляется успешной сверкой, P2: отключение health polling отключает восстановление очереди, Standards / корректность, _busy_on_first_read(), Учёты, изменившиеся между чтением и сверкой: BUSY только при первом чтении., test_failed_busy_retry_is_not_successful_cycle(), test_next_clean_traversal_recovers_and_old_confirmation_survives_gap(), test_partly_failed_busy_retry_counts_each_account_once() (+2 more)

### Community 88 - "Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026"
Cohesion: 0.50
Nodes (3): Прогон до исправления (SubHub `d9a2c80` + незакоммиченные правки, не относящиеся к задаче), Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026, Финальный прогон после исправления

### Community 89 - "models.py"
Cohesion: 0.07
Nodes (68): aiogram, aiogram_exceptions, alembic_autogenerate, alembic_migration, app_bot, Base, Базовый класс для всех ORM-моделей., TimestampMixin (+60 more)

### Community 90 - "LocalSubHub"
Cohesion: 0.05
Nodes (37): build_happ_import_url(), Exception, Resolve the first panel identity known to SubHub. Older bot records can have a…, Base error for the internal SubHub integration., The panels have not exposed this identity to SubHub yet., The identity exists, but currently has no active nodes., Build a signed HTTPS trampoline for importing a legacy subscription., Small authenticated client for the SubHub admin API. Subscription URLs and… (+29 more)

### Community 91 - "utcnow"
Cohesion: 0.40
Nodes (16): Сохраняет наблюдения IP. Возвращает число добавленных записей., record_ips(), utcnow(), _ips(), AsyncSession, _settings(), test_collect_for_client(), test_list_all_statuses_includes_client_without_observations() (+8 more)

### Community 92 - "Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026"
Cohesion: 0.33
Nodes (5): 1. 3x-ui v3.9.0 (`ghcr.io/mhsanaei/3x-ui:v3.9.0`), финальный прогон — 25 OK, 5 FAIL, 2. 3x-ui v3.9.0, повтор S6, S6b, S7 с исправленным расчётом — 5 OK, 0 FAIL, 3. 3x-ui v3.5.0 (`ghcr.io/mhsanaei/3x-ui:v3.5.0`, Xray 26.7.11) — 5 OK, 9 FAIL, 4. Первый (предварительный) прогон на v3.9.0 — 24 OK, 6 FAIL, Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026

### Community 93 - "QuotaClientState"
Cohesion: 0.10
Nodes (24): QuotaClientState, Читает клиента и его счётчик трафика (None — клиента нет)., Пакетное чтение клиентов одной сессией панели., Создаёт/обновляет клиента с квотой и проверяет результат чтением.…, Снимает привязки клиента к ``inbound_ids`` (счётчик сохраняется). Проверяет…, Прочитанное с панели состояние клиента и его счётчика трафика., _apply_quota(), _Context (+16 more)

### Community 94 - "Production deployment — 2026-10-06"
Cohesion: 0.33
Nodes (5): Backups and rollback, Checks after deployment, Deployment incidents and limits, Production deployment — 2026-10-06, Release

### Community 95 - "Q: собери контекст проекта"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: собери контекст проекта, Source Nodes

### Community 96 - "test_whitelist_reconcile.py"
Cohesion: 0.23
Nodes (10): _fmt_span(), Состояние фоновой сверки расхода для админ-раздела (по данным процесса). «Обход…, _reconcile_gaps(), reconcile_status_lines(), Фоновая сверка расхода whitelist-услуги: полный обход аккаунтов пачками., test_accounts_without_panel_client_are_skipped_not_repeated(), test_reconcile_text_describes_age_and_abort(), test_reconcile_text_does_not_promise_freshness_for_unconfirmed_accounts() (+2 more)

### Community 97 - "Приёмка услуги «Обход белых списков» — 5 октября 2026"
Cohesion: 0.07
Nodes (27): Возобновляет подтверждения, прерванные после фиксации целевого срока. Заявка…, recover_confirmed_payments(), Backoff повторов в памяти процесса для записей без поля ``next_retry_at``.…, RetryBackoff, AsyncSession, Панели изменены и изменения зафиксированы в БД — нужен SubHub sync., Один проход восстановления; ошибка одного шага не отменяет другой. Сначала…, RecoveryReport (+19 more)

### Community 98 - "RecordingPanel"
Cohesion: 0.17
Nodes (8): panel(), fixture, Панель с журналом пакетных чтений и точками вмешательства в обход., RecordingPanel, service_on(), _Sleeps, mutate(), wl_server()

### Community 99 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 100 - "placement_progress"
Cohesion: 0.17
Nodes (9): admin_summary(), AdminSummary, placement_progress(), PlacementProgress, Учёт с клиентом на панели, размещение которого не подтверждено для цели.…, Перенос клиентов на текущую цель whitelist-сервера. Учитываются учёты с…, Прогресс переноса на текущую цель; None — сервер услуги без единой цели., _unplaced() (+1 more)

### Community 101 - "test_ui.py"
Cohesion: 0.29
Nodes (7): aiogram_methods, TelegramBadRequest, _bad_request(), _Callback, Exception, test_answer_callback_ignores_expired_query_id(), test_answer_callback_reraises_other_bad_request()

### Community 102 - "test_whitelist_retarget_pg.py"
Cohesion: 0.36
Nodes (9): _placement(), _queue(), Перенос на новую цель при конкурентных покупке, продлении, очереди и сверке…, _reconcile(), _retarget(), SlowMovePanel, test_concurrent_queues_during_retarget_converge_on_latest_target(), retarget_to_nine() (+1 more)

### Community 103 - "Повторное ревью — 6 октября 2026"
Cohesion: 0.40
Nodes (4): Spec, Выполненные проверки, Повторное ревью — 6 октября 2026, Что подтверждено и что остаётся перед внедрением

### Community 106 - "Ids"
Cohesion: 0.33
Nodes (5): Ids, fixture, Идентификаторы фикстур: объекты сессии теста истекают после rollback., started(), fake()

### Community 107 - "reconcile_cycle"
Cohesion: 0.14
Nodes (13): _BatchResult, _finish_reconcile(), Итог обхода учётов (накапливается между запусками, если обход прерывали).…, Учёты, чьё состояние этим обходом не подтверждено. Удалённые (``skipped_gone``)…, Следующая пачка учётов: стабильный курсор по id, а не по изменяемой метке., Читает пачку одной сессией панели и сверяет учёты по одному. Сбой одного учёта…, Один повторный проход по учётам, изменившимся между чтением и сверкой., Полный обход учётов whitelist-сервера ограниченными пачками. Пачки берутся по… (+5 more)

### Community 108 - "session"
Cohesion: 0.20
Nodes (17): admin(), AsyncSession, fixture, server(), session(), user(), vpn_client(), confirm() (+9 more)

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
Cohesion: 0.40
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 116 - "user_operation"
Cohesion: 0.21
Nodes (13): decorate(), wrapped(), user_operation(), 5. Конкуренция и восстановление, Восстановление после недоступной статистики, Синхронизация подписки SubHub: быстрый триггер и резервный опрос (2026-10-05), Фоновая сверка расхода: обход, гарантии, ограничения, check_released() (+5 more)

### Community 117 - "check_server"
Cohesion: 0.17
Nodes (5): check_server(), Проверяет доступность панели 3x-ui одного сервера. Успешный login считается…, test_health_check_server_returns_false_on_error(), login(), test_health_check_server_returns_true_on_success()

### Community 120 - "admin_nav"
Cohesion: 0.08
Nodes (37): admin_nav(), _edit_panel(), _finalize_whitelist_server(), on_bind_action(), on_payment_action(), callback_query, CallbackQuery, Добавляет сервер услуги и сразу сверяет его inbound'ы. До успешной сверки с… (+29 more)

### Community 121 - "_CrashingPanel"
Cohesion: 0.40
Nodes (4): _Crash, _CrashingPanel, Exception, Процесс «умер» посреди обращения к панели (не ошибка панели).

### Community 127 - "whitelist_e2e.py"
Cohesion: 0.10
Nodes (30): app_db, argparse, asyncio, asyncpg, base64, contextlib, hashlib, http_server (+22 more)

### Community 128 - "DiesOnFirstChange"
Cohesion: 0.25
Nodes (7): BaseException, DiesOnFirstChange, die(), ProcessKilled, Any, Имитация гибели процесса: не перехватывается ``except Exception`` кода бота., Настоящий updater, у которого первое изменение панели «убивает процесс».

### Community 129 - "_Crash"
Cohesion: 0.40
Nodes (3): RuntimeError, _Crash, Процесс завершился после запроса к панели, до commit.

### Community 130 - "Повторная приёмка whitelist — 6 октября 2026"
Cohesion: 0.22
Nodes (7): D-3: потеря учёта подтверждена на штатном образе, Версии и изоляция, Вывод, Изменения средств приёмки, Ограничения, Повторная приёмка whitelist — 6 октября 2026, Следующий шаг

### Community 132 - "_alembic"
Cohesion: 0.28
Nodes (7): Config, pg_only, _reset_schema(), test_empty_postgresql_migrates_to_head_matching_models(), test_pre_fix_postgresql_upgrades_and_recovery_worker_runs(), test_github_schema_upgrades_without_model_drift_or_data_loss(), _alembic()

### Community 133 - "Обновление whitelist-панели — 6 октября 2026"
Cohesion: 0.22
Nodes (8): DNS и TLS, Границы проверки, Итоговая удалённая приёмка, Обновление whitelist-панели — 6 октября 2026, Остановка systemd, Первая удалённая приёмка, Развёртывание, Резервная копия и откат

### Community 134 - "Проверка исправленной 3x-ui — 6 октября 2026"
Cohesion: 0.22
Nodes (8): Как повторить, Неуспешные промежуточные прогоны, Область проверки, Ограничения учёта и отключения, Проверка исправленной 3x-ui — 6 октября 2026, Проверки, Сборка и патч, Следующий этап

### Community 136 - "_reconciled"
Cohesion: 0.22
Nodes (9): _free(), Аккаунты без клиента на панели не обновляют метку и не должны занимать пачку., _reconciled(), test_exception_while_reconciling_one_account_does_not_stop_others(), flaky(), test_more_than_one_batch_is_reconciled_in_one_pass(), test_recovered_panel_after_transient_batch_failure_continues(), one_bad_batch() (+1 more)

### Community 140 - "Динамические названия whitelist — 6 октября 2026"
Cohesion: 0.25
Nodes (5): Динамические названия whitelist — 6 октября 2026, Контракт и обновление, Реализация, Резервные копии и откат, Удалённая приёмка

### Community 145 - "FakeBot"
Cohesion: 0.32
Nodes (4): 2. Стенд, async_sessionmaker, FakeBot, Any

### Community 147 - "_server_health_poller"
Cohesion: 0.29
Nodes (7): Фоновая периодическая проверка доступности серверов 3x-ui. Только сохраняет…, _server_health_poller(), check_servers(), AsyncSession, Проверяет все серверы и сохраняет результат в БД. Только наблюдение: отложенные…, Фоновые задачи, 17. Очередь применения не зависит от проверки здоровья серверов (2026-10-06)

### Community 148 - "Обновление production — 4 октября 2026"
Cohesion: 0.25
Nodes (6): PAY-1C3F1344, Внедрено, Дополнительный дефект, обнаруженный при приёмке, Незавершённые операции, Обновление production — 4 октября 2026, Проверки и резервирование

### Community 149 - "Ревью VpnBot — 4 октября 2026"
Cohesion: 0.25
Nodes (8): Исправления в рабочем дереве, Объём и доказательства, Порядок применения в production, Проверки, Разбор PAY-1C3F1344, Ревью VpnBot — 4 октября 2026, Результат, Устройство production

### Community 150 - "find_reset_blocker"
Cohesion: 0.33
Nodes (6): delete_for_self_reset(), find_reset_blocker(), AsyncSession, Удаляет пользователя по его запросу, если это не теряет оплат и заявок.…, Финансовое обязательство или заявка, которые удалил бы сброс; None — нет.…, SelfResetOutcome

### Community 151 - "Оставшиеся риски и решения"
Cohesion: 0.22
Nodes (8): P1/P2 — частичный успех внешней операции требует сверки, P1 — административные права зависят от тарифа, P1 — биллинг и панели не образуют одну транзакцию, P1 — пароли панелей не защищены шифрованием приложения, P2 — мониторинг и производительность, P2 — старые ошибки оплат без ожидающих задач, P2 — эксплуатация и воспроизводимость, Оставшиеся риски и решения

### Community 152 - "Приёмка на Android / Happ 4.6.0"
Cohesion: 0.29
Nodes (6): Подготовленный Wi-Fi стенд, Приёмка на Android / Happ 4.6.0, Протокол, Сверка после подтверждения пользователя, Условия начала, Шаги

### Community 153 - "Ограниченное подключение whitelist к production — 6 октября 2026"
Cohesion: 0.29
Nodes (6): Изменения, Инциденты подготовки, Ограниченное подключение whitelist к production — 6 октября 2026, Проверки, Резервные копии и откат, Состояние

### Community 156 - "api.ts"
Cohesion: 0.33
Nodes (4): APIError, Configuration, Plan, Profile

### Community 157 - "Финальное сохранение расхода 3x-ui — 6 октября 2026"
Cohesion: 0.33
Nodes (5): Границы гарантии, Изменения, Проверки и исторические результаты, Статус, Финальное сохранение расхода 3x-ui — 6 октября 2026

### Community 158 - "AuditLog"
Cohesion: 0.50
Nodes (3): AuditLog, AuditRepository, fresh_client()

### Community 159 - "Включение whitelist для действующих пользователей — 6 октября 2026"
Cohesion: 0.40
Nodes (4): Включение whitelist для действующих пользователей — 6 октября 2026, Особенность существующей идентичности, Резервные копии и ограничения отката, Результат

### Community 160 - "pg"
Cohesion: 0.33
Nodes (5): dict, _NoLocalLocks, pg(), fixture, Каждый вызов получает новый asyncio.Lock — как в отдельном процессе.

### Community 161 - "Настройка серверов и авто-провижининг"
Cohesion: 0.40
Nodes (5): Как формируется клиент, Настройка серверов и авто-провижининг, Перенос пользователей, существовавших до бота, Шаг 1. Добавить серверы, Шаг 2. Импортировать inbound'ы каждого сервера

### Community 163 - "_FakeMessage"
Cohesion: 0.40
Nodes (3): _FakeBot, _FakeMessage, Any

### Community 164 - "active_user"
Cohesion: 0.50
Nodes (4): active_user(), panel(), fixture, Пользователь с оплаченной подпиской: покупка трафика доступна.

## Knowledge Gaps
- **226 isolated node(s):** `credentials`, `dvpn/site`, `name`, `version`, `private` (+221 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1168 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **35 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `test_provisioning.py`, `WhitelistLedger`, `BindRequestRepository`, `test_whitelist.py`, `menu_nav`, `admin_handlers.py`, `ReconcileStatus`, `_extend_and_finalize`, `test_trial_failed_payment.py`, `trial_available`, `test_renewal_recovery_pg.py`, `PendingServerUpdate`, `test_whitelist_pg.py`, `main.py`, `find_reset_blocker`, `test_trial_grants_migration.py`, `ClientServerMapping`, `Bot`, `pg`, `PanelUpdateError`, `_trial_available`, `web_bridge.py`, `Server`, `ResetBlock`, `test_renewal_recovery_worker.py`, `scenario`, `UserRepository`, `Settings`, `PanelUpdater`, `texts.py`, `whitelist.py`, `get_account`, `PaymentRequest`, `test_expiry.py`, `test_subscription_purchases_migration.py`, `_phases`, `MockPanelUpdater`, `test_user_reset_pg.py`, `models.py`, `utcnow`, `QuotaClientState`, `test_whitelist_reconcile.py`, `session`, `admin_nav`, `whitelist_e2e.py`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Why does `Server` connect `Server` to `test_whitelist_retarget.py`, `test_provisioning.py`, `BindRequestRepository`, `test_whitelist.py`, `admin_handlers.py`, `keyboards.py`, `ReconcileStatus`, `test_trial_failed_payment.py`, `test_renewal_recovery_pg.py`, `PendingServerUpdate`, `test_whitelist_pg.py`, `test_whitelist_epoch.py`, `test_crypto.py`, `main.py`, `XuiClient`, `XuiPanelUpdater`, `ClientServerMapping`, `ServerInbound`, `Bot`, `pg`, `PanelUpdateError`, `web_bridge.py`, `test_whitelist_xui.py`, `EncryptedString`, `test_renewal_recovery_worker.py`, `What You Must Do When Invoked`, `sync_inventory`, `PanelUpdater`, `texts.py`, `whitelist.py`, `PaymentRequest`, `test_xui_updater.py`, `Контекст проекта`, `User`, `test_first_import_failure_then_retry_and_single_target`, `MockPanelUpdater`, `test_user_reset_pg.py`, `models.py`, `utcnow`, `QuotaClientState`, `test_whitelist_reconcile.py`, `RecordingPanel`, `placement_progress`, `reconcile_cycle`, `session`, `check_server`, `admin_nav`, `whitelist_e2e.py`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `XuiClient` connect `XuiClient` to `PanelUpdateError`, `Panel`, `test_whitelist_xui.py`, `admin_handlers.py`, `test_xui_client.py`, `main.py`, `check_server`, `Settings`, `models.py`, `XuiPanelUpdater`, `xui_traffic_d3.py`, `whitelist_e2e.py`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Are the 200 inferred relationships involving `User` (e.g. with `add_inbound()` and `admin_add_server_line()`) actually correct?**
  _`User` has 200 INFERRED edges - model-reasoned connections that need verification._
- **Are the 37 inferred relationships involving `MockPanelUpdater` (e.g. with `ClientServerMapping` and `Server`) actually correct?**
  _`MockPanelUpdater` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 103 inferred relationships involving `VpnClient` (e.g. with `notify_user_extended()` and `access_extended()`) actually correct?**
  _`VpnClient` has 103 INFERRED edges - model-reasoned connections that need verification._
- **Are the 63 inferred relationships involving `Server` (e.g. with `_finalize_new_server()` and `_finalize_whitelist_server()`) actually correct?**
  _`Server` has 63 INFERRED edges - model-reasoned connections that need verification._
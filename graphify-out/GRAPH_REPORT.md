# Graph Report - VpnBot  (2026-10-08)

## Corpus Check
- 216 files · ~228,379 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 23 file(s) not represented in the graph (top: (none) 9, .example 3, .patch 3)

## Summary
- 3543 nodes · 13167 edges · 160 communities (125 shown, 35 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1733 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6510d9e0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- _pay
- provisioning.py
- WhitelistLedger
- test_subhub_trigger.py
- test_whitelist.py
- whitelist_menu
- admin_handlers.py
- test_xui_payloads.py
- keyboards.py
- test_whitelist_reconcile.py
- billing.py
- PaymentRequest
- _reset_bot_user
- test_renewal_recovery_pg.py
- alembic
- P2: отключение health polling останавливает восстановление обычных продлений
- FakeCallback
- _wl_state
- main.go
- App.vue
- test_crypto.py
- user_handlers.py
- _push
- utcnow
- XuiClient
- test_trial_grants_migration.py
- XuiPanelUpdater
- xray_binary
- Server
- test_whitelist_inbound_compat.py
- xui_traffic_d3.py
- Bot
- Контекст проекта
- test_payment_kind_conflict.py
- test_user_reset.py
- test_web_bridge.py
- test_whitelist_queue_worker.py
- test_whitelist_xui.py
- test_ux.py
- test_whitelist_payment_status.py
- package.json
- get_account
- compilerOptions
- main_test.go
- api
- EncryptedString
- .auth
- test_renewal_recovery_worker.py
- Задание агенту: услуга «Обход белых списков» в VpnBot
- app
- main
- subhub_quota_e2e.py
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
- test_admin_block_is_not_lost_to_queue_reads_or_reconcile
- dvpn/site
- telegram-vpn-billing-bot
- create_request
- test_xui_updater.py
- graphify reference: extra exports and benchmark
- test_admin_confirm.py
- test_subscription_purchases_migration.py
- Контекст проекта
- session
- _phases
- User
- 3.2. Купленный трафик
- dataclasses
- gib_to_bytes
- AGENTS.md
- ServerRepository
- FakeMessage
- test_whitelist_pg.py
- test_github_schema_upgrades_without_model_drift_or_data_loss
- Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026
- models.py
- SubHubClient
- panel
- Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026
- devDependencies
- Production deployment — 2026-10-06
- Q: собери контекст проекта
- TelegramMock
- recover_confirmed_payments
- graphify reference: query, path, explain
- test_ui.py
- Meter
- whitelist_e2e_2026-10-05.md
- Ids
- reconcile_cycle
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
- Protocol
- Обновление whitelist-панели — 6 октября 2026
- Проверка исправленной 3x-ui — 6 октября 2026
- _PoisonedPanel
- link_callback
- Услуга «Обход белых списков» — реализация и порядок внедрения
- _HangingPanel
- Приёмка услуги «Обход белых списков» — 5 октября 2026
- check_servers
- Обновление production — 4 октября 2026
- Ревью VpnBot — 4 октября 2026
- Оставшиеся риски и решения
- Приёмка на Android / Happ 4.6.0
- Ограниченное подключение whitelist к production — 6 октября 2026
- ref_node_fs_promises
- Финальное сохранение расхода 3x-ui — 6 октября 2026
- AuditLog
- Включение whitelist для действующих пользователей — 6 октября 2026
- _NoLocalLocks
- cycles
- _FakeBot
- active_user
- GatedPanel

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
- `6. Реальные 3x-ui и SubHub` --references--> `recover_confirmed_payments()`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → app/services/billing.py
- `Как формируется клиент` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py
- `16. R46 без принудительной синхронизации и фоновые циклы бота (результаты от 2026-10-05, после приёмки)` --references--> `_after_applied_payment()`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → app/bot/admin_handlers.py

## Import Cycles
- None detected.

## Communities (160 total, 35 thin omitted)

### Community 0 - "_pay"
Cohesion: 0.12
Nodes (61): choose_inbound(), process_due(), Фоновая очередь: применяет несинхронизированные состояния с backoff. Кроме…, Делает выбранный inbound единственной целью whitelist-сервера. Готовность…, P1: смена целевого inbound не переносит существующих пользователей, 19. Перенос клиентов при смене целевого inbound (2026-10-06, P1 ревью), ops, _pay() (+53 more)

### Community 1 - "provisioning.py"
Cohesion: 0.05
Nodes (90): MappingRepository, PanelUpdateError, Exception, Ошибка обновления клиента в панели., ServerUpdateResult, apply_access(), apply_access_to_server(), bind_existing_client() (+82 more)

### Community 2 - "WhitelistLedger"
Cohesion: 0.07
Nodes (49): Бизнес-учёт трафика пользователя на whitelist-сервере. Остатки…, Журнал выдач/начислений/корректировок, привязанных к исходной операции. Выдача…, WhitelistAccount, WhitelistLedger, QuotaClientState, Читает клиента и его счётчик трафика (None — клиента нет)., Пакетное чтение клиентов одной сессией панели., Снимает привязки клиента к ``inbound_ids`` (счётчик сохраняется). Проверяет… (+41 more)

### Community 3 - "test_subhub_trigger.py"
Cohesion: 0.10
Nodes (23): aiogram_filters, Best-effort запрос SubHub перечитать панели после фоновых изменений., _subhub_sync(), Best-effort notification after a successful panel mutation., trigger_configured_sync(), StreamReader, StreamWriter, _command() (+15 more)

### Community 4 - "test_whitelist.py"
Cohesion: 0.11
Nodes (51): AwaitingCredit, list_open_events(), Сохранённое начисление, ещё не сверенное с расходом., Остатки пользователя; при доступной панели — с актуальной сверкой. Чтение…, Неприменённые события учёта пользователя в порядке возникновения., user_overview(), 3.1. Бесплатный пакет и доступ, _account() (+43 more)

### Community 5 - "whitelist_menu"
Cohesion: 0.13
Nodes (31): bind_request_waiting(), no_open_request(), onboarding_send_link_prompt(), Приветствие. Использует HTML-разметку: ID завёрнут в <code> — Telegram копирует…, welcome(), _attach_and_notify(), cmd_start(), _edit() (+23 more)

### Community 6 - "admin_handlers.py"
Cohesion: 0.08
Nodes (71): aiogram_fsm_context, add_inbound(), add_server(), admin_add_server_cancel(), admin_add_server_line(), admin_broadcast_cancel(), admin_broadcast_send(), admin_delete_subscription_by_client_id() (+63 more)

### Community 7 - "test_xui_payloads.py"
Cohesion: 0.09
Nodes (35): build_client_object(), client_identifier(), _client_uuid_for_api(), _looks_like_db_id(), merge_client_record_for_update(), pick_panel_client_secret(), Any, Exception (+27 more)

### Community 8 - "keyboards.py"
Cohesion: 0.10
Nodes (57): BindCallback, Callback админских действий над заявкой на привязку подписки., _adm(), admin_add_server_type_keyboard(), admin_back_keyboard(), admin_bind_keyboard(), admin_bind_retry_keyboard(), admin_confirm_delete_keyboard() (+49 more)

### Community 9 - "test_whitelist_reconcile.py"
Cohesion: 0.06
Nodes (61): _fmt_span(), Состояние фоновой сверки расхода для админ-раздела (по данным процесса). «Обход…, _reconcile_gaps(), reconcile_status_lines(), timedelta, Состояние и наблюдаемость фоновой сверки (хранится в памяти процесса).…, Сколько прошло с завершения последнего обхода (в т. ч. с пропусками)., Верхняя граница возраста данных *сверенных* учётов последнего обхода. (+53 more)

### Community 10 - "billing.py"
Cohesion: 0.13
Nodes (43): _apply_panels(), _as_aware(), BillingError, BillingResult, compute_new_expiry(), confirm_payment(), _confirm_traffic(), _count_eligible_mappings() (+35 more)

### Community 11 - "PaymentRequest"
Cohesion: 0.12
Nodes (14): PaymentRequest, PaymentRepository, Берёт заявку с блокировкой строки (SELECT ... FOR UPDATE). На Postgres…, Число применённых оплат подписки (покупки трафика не учитываются)., Удаляет заявку (вместе с вложениями по каскаду)., Последняя успешная (применённая/подтверждённая) оплата пользователя.…, AsyncSession, test_attach_proof_creates_attachment() (+6 more)

### Community 12 - "_reset_bot_user"
Cohesion: 0.12
Nodes (24): onboarding_legacy_question(), Удаляет данные пользователя в боте и показывает онбординг заново. Сброс не…, _reset_bot_user(), accepted_subscription_clause(), Условие SQL: заявка — принятая администратором оплата подписки. Принятие…, Оформлялась ли подписка: есть принятая оплата подписки (не трафика). Принятая…, Пробный период уже выдавался этому пользователю или его Telegram ID.…, trial_already_used() (+16 more)

### Community 13 - "test_renewal_recovery_pg.py"
Cohesion: 0.15
Nodes (50): _advisory(), _audit(), _client_expiry(), _confirm(), _crash_during_confirmation(), Env, _expiry_calls(), _idle_in_transaction() (+42 more)

### Community 15 - "P2: отключение health polling останавливает восстановление обычных продлений"
Cohesion: 0.17
Nodes (20): apply_pending_for_server(), apply_pending_update(), _clear_payment_error_if_complete(), close_for_server(), _defer_after_error(), PendingApplyResult, process_due(), AsyncSession (+12 more)

### Community 16 - "FakeCallback"
Cohesion: 0.16
Nodes (12): Пользовательский раздел «Обход белых списков». action: home | refresh | buy…, WhitelistCallback, FakeCallback, FakeState, Any, test_expired_user_gets_clear_explanation(), test_outage_payment_is_shown_as_awaiting_and_admin_resolves(), user_screen() (+4 more)

### Community 17 - "_wl_state"
Cohesion: 0.17
Nodes (30): Применяет состояние учёта пользователя на whitelist-панели., Фоновая сверка расхода: обходит все учёты пачками по ``limit``. Возвращает…, reconcile_usage(), sync_user(), _available(), parametrize, Смена эпохи счётчика whitelist-панели при неприменённых событиях учёта. Внешний…, Пересоздание клиента: значение не уменьшилось, сменилась строка статистики. (+22 more)

### Community 18 - "main.go"
Cohesion: 0.07
Nodes (29): credentials, go_pkg_bytes, go_pkg_context, go_pkg_crypto_hmac, go_pkg_crypto_rand, go_pkg_crypto_sha256, go_pkg_crypto_subtle, go_pkg_crypto_tls (+21 more)

### Community 19 - "App.vue"
Cohesion: 0.07
Nodes (28): APIError, Configuration, Plan, Profile, authTitles, awaiting, busy, code (+20 more)

### Community 20 - "test_crypto.py"
Cohesion: 0.13
Nodes (25): decrypt(), encrypt(), _fernet(), is_encrypted(), Возвращает Fernet, выведенный из SECRET_KEY, либо None если ключ не задан.…, Шифрует строку. Без SECRET_KEY возвращает значение как есть (dev/тесты)., Расшифровывает строку. Legacy-значения в открытом виде возвращает как есть., base64 (+17 more)

### Community 21 - "user_handlers.py"
Cohesion: 0.05
Nodes (79): aiogram, aiogram_client_default, aiogram_exceptions, aiogram_fsm_storage_memory, aiogram_types, aiogram_utils_token, app_bot, _command_name() (+71 more)

### Community 22 - "_push"
Cohesion: 0.18
Nodes (15): Привязка клиента whitelist-панели к inbound'у, созданная самой услугой. Строка…, WhitelistPlacement, _confirm_attach(), _defer(), _find_placement(), _Link, _push(), Повтор через backoff 1 мин → 1 ч; ошибка сохраняется для администратора. (+7 more)

### Community 23 - "utcnow"
Cohesion: 0.16
Nodes (39): IpObservation, _active_clients(), collect_all(), collect_for_client(), compute_status(), _level_for(), list_all_statuses(), list_flagged() (+31 more)

### Community 24 - "XuiClient"
Cohesion: 0.06
Nodes (41): list_panel_clients(), Возвращает список клиентов, уже существующих на панели сервера., Any, Exception, Response, _quote_path_segment(), Авторизованный запрос: гарантирует login и при истёкшей сессии выполняет…, Берёт CSRF-токен с /csrf-token (3x-ui >= 3.2.x). На старых панелях endpoint… (+33 more)

### Community 25 - "test_trial_grants_migration.py"
Cohesion: 0.18
Nodes (17): alembic_config, Config, _alembic(), _expected(), _naive_utc(), datetime, parametrize, Миграция ``trial_grants`` переносит существующие факты использования trial.… (+9 more)

### Community 26 - "XuiPanelUpdater"
Cohesion: 0.10
Nodes (21): Создаёт/обновляет клиента сразу для всех inbound'ов сервера., Создаёт/обновляет клиента с квотой и проверяет результат чтением.…, Один клиент панели (глобальный по email), привязанный к её inbound'ам.…, ServerProvision, client_record_body(), Извлекает model.Client из ответа ``clients/get``., _client_flows(), _inbound_client_flow() (+13 more)

### Community 27 - "xray_binary"
Cohesion: 0.20
Nodes (7): 15. Лимит трафика 3x-ui → SubHub: единица `totalGB` и источник расхода (результаты от 2026-10-05, после приёмки), 2. Проверенный контракт 3x-ui, Use the binary packaged for the container image's architecture., up+down из счётчиков самого Xray панели (statsquery), минуя учёт панели.…, xray_binary(), main(), sh()

### Community 28 - "Server"
Cohesion: 0.09
Nodes (19): ClientServerMapping, Server, IpProvider, MockIpProvider, Источник списка IP-адресов клиента (для антишеринг-мониторинга)., Mock-провайдер для тестов: возвращает заранее заданные IP по server_id., Реальный провайдер: берёт IP клиента из журнала панели 3x-ui., XuiIpProvider (+11 more)

### Community 29 - "test_whitelist_inbound_compat.py"
Cohesion: 0.16
Nodes (32): build_provision_spec(), get_active_server(), Включённый whitelist-сервер (не более одного по уникальному индексу)., server_ready(), target_inbound(), cryptography_hazmat_primitives, cryptography_hazmat_primitives_asymmetric_x25519, Совместимость inbound с SubHub (2026-10-05) (+24 more)

### Community 30 - "xui_traffic_d3.py"
Cohesion: 0.18
Nodes (33): Конфигурация xray-клиента: SOCKS 127.0.0.1:10808 → VLESS по ссылке., xray_client_config(), accounted(), add_client(), container_started(), delta(), _disable_case(), Lab (+25 more)

### Community 31 - "Bot"
Cohesion: 0.08
Nodes (25): aiogram_filters_callback_data, AdminCallback, OnboardCallback, PaymentCallback, Онбординг: был ли пользователь клиентом до внедрения бота., Навигация по админ-панели (/admin). action: home | servers | server | rename |…, Админ-раздел услуги «Обход белых списков». action: home | sync | choose (value…, Callback админских действий над заявкой. (+17 more)

### Community 32 - "Контекст проекта"
Cohesion: 0.13
Nodes (14): Архитектура, Безопасность аутентификации (backend/main.go), Важные инженерные правила, Доменная модель (таблицы веб-части, в БД бота), Запуск, Контекст проекта, Конфигурация, Локальные артефакты (+6 more)

### Community 33 - "test_payment_kind_conflict.py"
Cohesion: 0.37
Nodes (14): _open_count(), _package(), D-1: заявку с отправленной квитанцией нельзя превратить в заявку другого вида., _snapshot(), _subscription_with_proof(), test_conflicted_subscription_request_extends_once_and_adds_no_traffic(), test_kind_switch_without_proof_still_converts_single_request(), test_same_kind_repeat_returns_pending_request_unchanged() (+6 more)

### Community 34 - "test_user_reset.py"
Cohesion: 0.04
Nodes (118): aiohttp, Почему сброс бота сейчас невозможен (короткий alert Telegram)., reset_blocked(), trial_subscription_purchased(), Пробный доступен, если им не пользовались и подписку никогда не оформляли., _trial_available(), Пробный период, выданный Telegram-аккаунту. Хранится по Telegram ID отдельно от…, TrialGrant (+110 more)

### Community 35 - "test_web_bridge.py"
Cohesion: 0.17
Nodes (19): WebAccount, WebLinkRequest, decide_link(), Оплата принята между проверкой моста и grant_trial: ответ 409, не 503., test_site_trial_race_with_payment_maps_to_conflict(), Привязка сайта в окне сброса не одобряется к удалённому пользователю., test_web_link_approval_during_reset_is_serialized(), link_and_approve() (+11 more)

### Community 36 - "test_whitelist_queue_worker.py"
Cohesion: 0.11
Nodes (38): Any, Очередь применения квот «Обхода белых списков» на панели. Единственный…, Запускает worker, если такой ещё не работает в этом процессе., Запускает фоновые циклы процесса бота (кроме доставки сайта). Одна сборка для…, start_background_tasks(), _start_exclusive(), stop_background_tasks(), _whitelist_queue_worker() (+30 more)

### Community 37 - "test_whitelist_xui.py"
Cohesion: 0.21
Nodes (34): QuotaTarget, Абсолютное целевое состояние клиента с учётом трафика. ``total_bytes`` —…, 3.5. Учёт трафика и интеграция 3x-ui, _apply_existing(), _auth(), _body(), _inbound(), HTTPXMock (+26 more)

### Community 38 - "test_ux.py"
Cohesion: 0.07
Nodes (51): _parse_server_line(), Парсит 'name|country|panel_url|username|password|[kind]|[sub]|[purpose]'.…, MenuCallback, Навигация по inline-меню (редактирование сообщения на месте). action: home |…, custom_emoji_id(), emoji_char(), Возвращает unicode-символ значка (без анимации)., Возвращает custom_emoji_id значка или None, если значок не найден. (+43 more)

### Community 39 - "test_whitelist_payment_status.py"
Cohesion: 0.27
Nodes (20): _buy(), _down(), _fresh(), _is_waiting(), _queue(), Статус заявки на покупку трафика следует за фактическим применением начисления., Запись квоты прошла, но расход не сверен: начисление ещё не учтено., Применена версия между двумя заявками: ожидание снимается только с ранней. (+12 more)

### Community 40 - "package.json"
Cohesion: 0.12
Nodes (14): lucide-vue-next, typescript, vite, @vitejs/plugin-vue, vue, vue-tsc, dependencies, lucide-vue-next (+6 more)

### Community 41 - "get_account"
Cohesion: 0.21
Nodes (13): aiogram_fsm_state, PlanCallback, Callback выбора тарифа пользователем. code — код тарифа из PLANS (1m/6m/12m)…, OnboardingStates, ProofStates, select_plan(), get_account(), StatesGroup (+5 more)

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
Cohesion: 0.29
Nodes (6): EncryptedString, Any, Прозрачно шифрует значение при записи и расшифровывает при чтении. - Если…, Важные инженерные правила проекта, 5. Миграции и резервная копия (PostgreSQL 16.15), TypeDecorator

### Community 46 - ".auth"
Cohesion: 0.53
Nodes (6): net/http.Request, net/http.ResponseWriter, decode(), digest(), fail(), respond()

### Community 47 - "test_renewal_recovery_worker.py"
Cohesion: 0.15
Nodes (39): expiry_to_ms(), Конвертирует дату в миллисекунды Unix-времени (формат 3x-ui expiryTime)., _audit_count(), _crash_during_confirmation(), _expiry_calls(), _fresh(), _pay_during_outage(), _pending() (+31 more)

### Community 48 - "Задание агенту: услуга «Обход белых списков» в VpnBot"
Cohesion: 0.15
Nodes (12): 1. Контекст проекта, 2. Согласованное поведение услуги, 3. Сервер и настройки администратора, 4. Технический контракт учёта трафика, 5. Биллинг, конкуренция и восстановление, 6. Пользовательский интерфейс, 7. Обязательная проверка, 8. Порядок работы и сдача (+4 more)

### Community 49 - "app"
Cohesion: 0.29
Nodes (6): app, config, context.Context, github.com/jackc/pgx/v5/pgxpool.Pool, net/http.Client, pgx.Tx

### Community 50 - "main"
Cohesion: 0.22
Nodes (7): bucket, limiter, net/http.Handler, sync.Mutex, time.Time, env(), main()

### Community 51 - "subhub_quota_e2e.py"
Cohesion: 0.11
Nodes (21): import_control_inbound(), main(), panel_view(), Any, Path, Квота трафика 3x-ui → SubHub на реальной панели, без маскирующего…, Расход, не менявшийся между двумя чтениями с интервалом 12 с., Что SubHub получает из ``inbounds/list`` для клиента: settings и clientStats. (+13 more)

### Community 52 - "web_preview.mjs"
Cohesion: 0.29
Nodes (6): ref_node_fs, ref_node_http, ref_node_path, ref_node_url, root, types

### Community 53 - "UserRepository"
Cohesion: 0.10
Nodes (10): AsyncSession, Удаляет пользователя и связанные записи (каскад в ORM)., Telegram ID всех пользователей, когда-либо запускавших бота., Генерирует короткий уникальный публичный ID пользователя., UserRepository, test_generated_public_id_is_unique_and_hex(), AsyncSession, test_backfills_public_id_for_existing() (+2 more)

### Community 54 - "_describe_event"
Cohesion: 0.33
Nodes (11): _describe_callback(), _describe_event(), CallbackQuery, Chat, _private_chat(), test_describe_addserver_redacts_secrets(), test_describe_callback_shows_action_only(), test_describe_command_without_args_shows_name() (+3 more)

### Community 55 - "What You Must Do When Invoked"
Cohesion: 0.07
Nodes (25): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+17 more)

### Community 56 - "Settings"
Cohesion: 0.06
Nodes (64): IsAdmin, TelegramObject, Пропускает событие только если пользователь — администратор., forward_proof_to_admins(), notify_admins_new_request(), Разрешает задавать ADMIN_TELEGRAM_IDS как строку '1,2,3' или одно число., Конфигурация приложения из переменных окружения / .env., Убирает пробелы и обрамляющие кавычки вокруг токена. (+56 more)

### Community 57 - "sync_inventory"
Cohesion: 0.10
Nodes (32): fetch_inbounds(), Any, Read inventory and external Hosts needed for whitelist XHTTP links., Сверка реестра с уже прочитанным списком (см. :func:`import_inbounds`)., reconcile_inbounds(), _ss_method(), check_inbound(), _check_vless_reality() (+24 more)

### Community 58 - "PanelUpdater"
Cohesion: 0.10
Nodes (53): Any, AsyncSession, Записывает событие в audit_logs., record(), PanelUpdater, Интерфейс работы с клиентом в панели. Реализуется как mock (для тестов/MVP) и…, adjust_balance(), claim_inbound() (+45 more)

### Community 59 - "Telegram VPN Billing Bot"
Cohesion: 0.13
Nodes (15): Telegram VPN Billing Bot, Админ-команды, Антишеринг-мониторинг, Граф кода (graphify), Единая подписка SubHub, Как формируется клиент, Конфигурация, Локальный запуск (dev) (+7 more)

### Community 60 - "whitelist_migration_check.py"
Cohesion: 0.22
Nodes (22): alembic_script, Единственная строка настроек услуги (id = 1)., WhitelistConfig, alembic(), check(), docker(), downgrade_cycle(), dsn() (+14 more)

### Community 63 - "D VPN — личный кабинет"
Cohesion: 0.25
Nodes (7): D VPN — личный кабинет, Архитектура, Запуск вместе с существующим ботом, Локальная разработка, Результаты проверки, Что реализовано, Эксплуатация

### Community 64 - "texts.py"
Cohesion: 0.04
Nodes (96): HTML-строка с анимированным значком для вставки в текст сообщения., tg(), notify_admins_failed(), notify_first_purchase_channel(), notify_user_bind_approved(), notify_user_extended(), notify_user_traffic_credited(), access_extended() (+88 more)

### Community 65 - "Panel"
Cohesion: 0.09
Nodes (15): admin_servers(), 14. Исправление D-2: SubHub собирается без ручной установки greenlet (результаты от 2026-10-05, после приёмки), Panel, Прямой доступ к тестовой панели — для проверок и действий «вручную в панели»., Разрешает трафик к частной подсети стенда — только на тестовых панелях.…, VLESS + REALITY (TCP), как у рабочих серверов; цель — локальный TLS 1.3., {'body': тело клиента, 'inboundIds': [...], 'traffic': client_traffics|None}., Изменение клиента «вручную в панели» (тот же API, что у веб-интерфейса). (+7 more)

### Community 66 - "whitelist.py"
Cohesion: 0.06
Nodes (45): access_state(), AccessState, admin_summary(), AdminSummary, _applied_target(), _aware(), _clear_placement(), _detect_external_disable() (+37 more)

### Community 71 - "create_request"
Cohesion: 0.12
Nodes (24): cancel_open_request(), create_request(), create_traffic_request(), _new_payment_code(), _open_request_for_update(), PaymentRequestError, PendingRequestExists, AsyncSession (+16 more)

### Community 72 - "test_xui_updater.py"
Cohesion: 0.12
Nodes (13): ProvisionInbound, Inbound сервера, к которому нужно привязать клиента., pytest_httpx, ReadOnlyPanel, test_attach_success_without_membership_is_not_provisioning_success(), test_stale_inbound_is_rejected_before_client_creation(), _mock_auth(), HTTPXMock (+5 more)

### Community 73 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 74 - "test_admin_confirm.py"
Cohesion: 0.09
Nodes (24): notify_user_expiry(), notify_user_rejected(), Уведомление пользователя об окончании подписки. True — если доставлено., _as_aware(), process_expiry_notifications(), AsyncSession, datetime, Стадия уведомления по остатку времени до окончания. 0 — рано, 1 — остался день,… (+16 more)

### Community 75 - "test_subscription_purchases_migration.py"
Cohesion: 0.21
Nodes (15): _at(), _expected(), _payment(), datetime, parametrize, Миграция ``subscription_purchases`` переносит сохранившиеся оплаты подписки.…, timestamptz: явный UTC, независимо от часового пояса сервера., _seed() (+7 more)

### Community 76 - "Контекст проекта"
Cohesion: 0.15
Nodes (12): Админские команды, Антишеринг, Интеграция с 3x-ui, Контекст проекта, Конфигурация, Локальные артефакты, Назначение, Основные пользовательские сценарии (+4 more)

### Community 77 - "session"
Cohesion: 0.18
Nodes (13): fake_check_server(), _wire(), _maker(), _maker_for(), async_sessionmaker, AsyncSession, fixture, Подменяет фоновые циклы метками: видно, какие из них запустил… (+5 more)

### Community 78 - "_phases"
Cohesion: 0.08
Nodes (32): Acts, _async(), describe(), docker(), expect_poll(), expect_trigger(), _forbid_sync(), from_source() (+24 more)

### Community 79 - "User"
Cohesion: 0.08
Nodes (69): PaymentStatus, User, VpnClient, datetime, Клиенты, которым пора слать уведомление об окончании. Берём тех, у кого задан…, _utcnow(), VpnClientRepository, MockPanelUpdater (+61 more)

### Community 80 - "3.2. Купленный трафик"
Cohesion: 0.11
Nodes (24): 3.2. Купленный трафик, 3.3. Ограничения доступа, 3.4. Сервер, импорт, выдача, администрирование, 3.6. Биллинг, конкуренция, восстановление, 3.7. Интерфейс, миграции, устройство, 3. Матрица требований и доказательств, rollout(), parametrize (+16 more)

### Community 81 - "dataclasses"
Cohesion: 0.18
Nodes (11): BroadcastResult, Рассылает текстовое сообщение всем пользователям. Сообщение отправляется…, send_broadcast(), dataclasses, FakeBot, AsyncSession, Текст рассылки шлётся без parse_mode — произвольный текст админа не должен…, test_all_telegram_ids_returns_every_user() (+3 more)

### Community 82 - "gib_to_bytes"
Cohesion: 0.31
Nodes (9): whitelist_package_title(), gib_to_bytes(), Заданный объём в ГБ (без единицы, точка): так, как он вводился. Байты при вводе…, set_volume_gib_text(), 12. Исправление D-4 (результаты от 2026-10-05, после приёмки), parametrize, test_accounting_stays_integer_truncated_bytes(), test_package_title_snapshot_for_new_requests_matches_display() (+1 more)

### Community 84 - "ServerRepository"
Cohesion: 0.08
Nodes (13): Меняет только имя, сохраняя сервер и все его связи., Меняет URL подписки, не затрагивая связи сервера., Удаляет сервер вместе с inbound'ами и привязками (каскад). Коллекции грузим…, Включённые серверы. По умолчанию — только обычные (безлимитные)., Цели обычного provisioning: whitelist-сервер ведётся отдельно., Удаляет настроенный inbound. Возвращает число удалённых записей., Удаляет все настроенные inbound'ы сервера. Возвращает их число., Сохраняет результат фоновой проверки доступности сервера. (+5 more)

### Community 85 - "FakeMessage"
Cohesion: 0.33
Nodes (4): admin_denied(), FakeMessage, Заменитель Message: запоминает ответы., test_non_admin_admin_command_denied()

### Community 86 - "test_whitelist_pg.py"
Cohesion: 0.06
Nodes (68): Пакет покупки трафика «Обход белых списков» (настраивается админом)., Первая применённая оплата подписки Telegram-аккаунта. Закрывает trial так же,…, SubscriptionPurchase, TrafficPackage, attach_proof(), Прикрепляет подтверждение оплаты (текст/фото/документ) к заявке., pytest, sqlalchemy_exc (+60 more)

### Community 87 - "test_github_schema_upgrades_without_model_drift_or_data_loss"
Cohesion: 0.33
Nodes (3): parametrize, _schema(), test_github_schema_upgrades_without_model_drift_or_data_loss()

### Community 88 - "Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026"
Cohesion: 0.50
Nodes (3): Прогон до исправления (SubHub `d9a2c80` + незакоммиченные правки, не относящиеся к задаче), Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026, Финальный прогон после исправления

### Community 89 - "models.py"
Cohesion: 0.06
Nodes (57): TimestampMixin, AttachmentType, BindRequestStatus, str, BindRequest, PaymentAttachment, Заявка на привязку существующей подписки (до внедрения бота)., BindRequestRepository (+49 more)

### Community 90 - "SubHubClient"
Cohesion: 0.07
Nodes (35): onboard_legacy_link(), Фоновая периодическая проверка доступности серверов 3x-ui. Только сохраняет…, _server_health_poller(), build_happ_import_url(), Exception, Resolve the first panel identity known to SubHub. Older bot records can have a…, Base error for the internal SubHub integration., The panels have not exposed this identity to SubHub yet. (+27 more)

### Community 92 - "Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026"
Cohesion: 0.33
Nodes (5): 1. 3x-ui v3.9.0 (`ghcr.io/mhsanaei/3x-ui:v3.9.0`), финальный прогон — 25 OK, 5 FAIL, 2. 3x-ui v3.9.0, повтор S6, S6b, S7 с исправленным расчётом — 5 OK, 0 FAIL, 3. 3x-ui v3.5.0 (`ghcr.io/mhsanaei/3x-ui:v3.5.0`, Xray 26.7.11) — 5 OK, 9 FAIL, 4. Первый (предварительный) прогон на v3.9.0 — 24 OK, 6 FAIL, Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026

### Community 93 - "devDependencies"
Cohesion: 0.40
Nodes (5): devDependencies, typescript, vite, @vitejs/plugin-vue, vue-tsc

### Community 94 - "Production deployment — 2026-10-06"
Cohesion: 0.33
Nodes (5): Backups and rollback, Checks after deployment, Deployment incidents and limits, Production deployment — 2026-10-06, Release

### Community 95 - "Q: собери контекст проекта"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: собери контекст проекта, Source Nodes

### Community 97 - "recover_confirmed_payments"
Cohesion: 0.12
Nodes (14): Возобновляет подтверждения, прерванные после фиксации целевого срока. Заявка…, recover_confirmed_payments(), Backoff повторов в памяти процесса для записей без поля ``next_retry_at``.…, RetryBackoff, AsyncSession, Панели изменены и изменения зафиксированы в БД — нужен SubHub sync., Один проход восстановления; ошибка одного шага не отменяет другой. Сначала…, RecoveryReport (+6 more)

### Community 99 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 101 - "test_ui.py"
Cohesion: 0.29
Nodes (7): aiogram_methods, TelegramBadRequest, _bad_request(), _Callback, Exception, test_answer_callback_ignores_expired_query_id(), test_answer_callback_reraises_other_bad_request()

### Community 104 - "Meter"
Cohesion: 0.22
Nodes (4): Meter, Any, Временной ряд каждые 0,5 с: PID Xray, счётчики Xray и панели по email., Моменты изменения учёта панели — это моменты опросов задачи трафика.

### Community 106 - "Ids"
Cohesion: 0.33
Nodes (5): Ids, fixture, Идентификаторы фикстур: объекты сессии теста истекают после rollback., started(), fake()

### Community 107 - "reconcile_cycle"
Cohesion: 0.09
Nodes (23): _BatchResult, _finish_reconcile(), Итог обхода учётов (накапливается между запусками, если обход прерывали).…, Учёты, чьё состояние этим обходом не подтверждено. Удалённые (``skipped_gone``)…, Следующая пачка учётов: стабильный курсор по id, а не по изменяемой метке., Читает пачку одной сессией панели и сверяет учёты по одному. Сбой одного учёта…, Один повторный проход по учётам, изменившимся между чтением и сверкой., Полный обход учётов whitelist-сервера ограниченными пачками. Пачки берутся по… (+15 more)

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
Cohesion: 0.31
Nodes (9): decorate(), wrapped(), user_operation(), 5. Конкуренция и восстановление, Восстановление после недоступной статистики, Фоновая сверка расхода: обход, гарантии, ограничения, test_user_operations_serialize_and_release_on_failure(), first() (+1 more)

### Community 117 - "check_server"
Cohesion: 0.17
Nodes (5): check_server(), Проверяет доступность панели 3x-ui одного сервера. Успешный login считается…, test_health_check_server_returns_false_on_error(), login(), test_health_check_server_returns_true_on_success()

### Community 120 - "admin_nav"
Cohesion: 0.07
Nodes (41): admin_nav(), _edit_panel(), _finalize_whitelist_server(), on_bind_action(), on_payment_action(), callback_query, CallbackQuery, Добавляет сервер услуги и сразу сверяет его inbound'ы. До успешной сверки с… (+33 more)

### Community 121 - "_CrashingPanel"
Cohesion: 0.40
Nodes (4): _Crash, _CrashingPanel, Exception, Процесс «умер» посреди обращения к панели (не ошибка панели).

### Community 127 - "whitelist_e2e.py"
Cohesion: 0.05
Nodes (53): app_db, do_run_migrations(), run_migrations_online(), build_client_record(), Унифицированный объект клиента для нового client-API (3x-ui >= 3.2.x).…, argparse, asyncio, asyncpg (+45 more)

### Community 128 - "DiesOnFirstChange"
Cohesion: 0.25
Nodes (7): BaseException, DiesOnFirstChange, die(), ProcessKilled, Any, Имитация гибели процесса: не перехватывается ``except Exception`` кода бота., Настоящий updater, у которого первое изменение панели «убивает процесс».

### Community 129 - "_Crash"
Cohesion: 0.40
Nodes (3): RuntimeError, _Crash, Процесс завершился после запроса к панели, до commit.

### Community 130 - "Повторная приёмка whitelist — 6 октября 2026"
Cohesion: 0.20
Nodes (8): D-3: потеря учёта подтверждена на штатном образе, Версии и изоляция, Вывод, Выполненные проверки, Изменения средств приёмки, Ограничения, Повторная приёмка whitelist — 6 октября 2026, Следующий шаг

### Community 132 - "Protocol"
Cohesion: 0.07
Nodes (45): alembic_autogenerate, alembic_migration, Base, Базовый класс для всех ORM-моделей., Protocol, PendingServerUpdate, Inbound на панели сервера, в который нужно заводить клиентов. На одном сервере…, ServerInbound (+37 more)

### Community 133 - "Обновление whitelist-панели — 6 октября 2026"
Cohesion: 0.22
Nodes (8): DNS и TLS, Границы проверки, Итоговая удалённая приёмка, Обновление whitelist-панели — 6 октября 2026, Остановка systemd, Первая удалённая приёмка, Развёртывание, Резервная копия и откат

### Community 134 - "Проверка исправленной 3x-ui — 6 октября 2026"
Cohesion: 0.22
Nodes (8): Как повторить, Неуспешные промежуточные прогоны, Область проверки, Ограничения учёта и отключения, Проверка исправленной 3x-ui — 6 октября 2026, Проверки, Сборка и патч, Следующий этап

### Community 136 - "link_callback"
Cohesion: 0.67
Nodes (3): link_callback(), callback_query, CallbackQuery

### Community 140 - "Услуга «Обход белых списков» — реализация и порядок внедрения"
Cohesion: 0.17
Nodes (9): Динамические названия whitelist — 6 октября 2026, Контракт и обновление, Реализация, Резервные копии и откат, Удалённая приёмка, 1. Что получает пользователь, 6. Порядок внедрения, 7. Откат (+1 more)

### Community 145 - "Приёмка услуги «Обход белых списков» — 5 октября 2026"
Cohesion: 0.17
Nodes (12): 10. Заключение, 1. Итог, 20. Повторная приёмка на реальных панелях (2026-10-06), 21. Исправленная 3x-ui и подготовка Happ — 6 октября 2026, 22. Финальное сохранение расхода — локальные тесты пропущены, 23. Обновление рабочей whitelist-панели — 6 октября 2026, 24. Подключение и массовое включение — 6 октября 2026, 25. Динамические названия — 6 октября 2026 (+4 more)

### Community 147 - "check_servers"
Cohesion: 0.50
Nodes (4): check_servers(), AsyncSession, Проверяет все серверы и сохраняет результат в БД. Только наблюдение: отложенные…, Фоновые задачи

### Community 148 - "Обновление production — 4 октября 2026"
Cohesion: 0.25
Nodes (6): PAY-1C3F1344, Внедрено, Дополнительный дефект, обнаруженный при приёмке, Незавершённые операции, Обновление production — 4 октября 2026, Проверки и резервирование

### Community 149 - "Ревью VpnBot — 4 октября 2026"
Cohesion: 0.25
Nodes (8): Исправления в рабочем дереве, Объём и доказательства, Порядок применения в production, Проверки, Разбор PAY-1C3F1344, Ревью VpnBot — 4 октября 2026, Результат, Устройство production

### Community 151 - "Оставшиеся риски и решения"
Cohesion: 0.22
Nodes (8): P1/P2 — частичный успех внешней операции требует сверки, P1 — административные права зависят от тарифа, P1 — биллинг и панели не образуют одну транзакцию, P1 — пароли панелей не защищены шифрованием приложения, P2 — мониторинг и производительность, P2 — старые ошибки оплат без ожидающих задач, P2 — эксплуатация и воспроизводимость, Оставшиеся риски и решения

### Community 152 - "Приёмка на Android / Happ 4.6.0"
Cohesion: 0.29
Nodes (6): Подготовленный Wi-Fi стенд, Приёмка на Android / Happ 4.6.0, Протокол, Сверка после подтверждения пользователя, Условия начала, Шаги

### Community 153 - "Ограниченное подключение whitelist к production — 6 октября 2026"
Cohesion: 0.29
Nodes (6): Изменения, Инциденты подготовки, Ограниченное подключение whitelist к production — 6 октября 2026, Проверки, Резервные копии и откат, Состояние

### Community 157 - "Финальное сохранение расхода 3x-ui — 6 октября 2026"
Cohesion: 0.33
Nodes (5): Границы гарантии, Изменения, Проверки и исторические результаты, Статус, Финальное сохранение расхода 3x-ui — 6 октября 2026

### Community 158 - "AuditLog"
Cohesion: 0.50
Nodes (3): AuditLog, AuditRepository, fresh_client()

### Community 159 - "Включение whitelist для действующих пользователей — 6 октября 2026"
Cohesion: 0.40
Nodes (4): Включение whitelist для действующих пользователей — 6 октября 2026, Особенность существующей идентичности, Резервные копии и ограничения отката, Результат

### Community 160 - "_NoLocalLocks"
Cohesion: 0.50
Nodes (3): dict, _NoLocalLocks, Каждый вызов получает новый asyncio.Lock — как в отдельном процессе.

### Community 162 - "cycles"
Cohesion: 0.50
Nodes (3): cycles(), fixture, Счётчик завершённых проходов worker'а — явная точка синхронизации.

### Community 164 - "active_user"
Cohesion: 0.50
Nodes (4): active_user(), panel(), fixture, Пользователь с оплаченной подпиской: покупка трафика доступна.

## Knowledge Gaps
- **226 isolated node(s):** `credentials`, `dvpn/site`, `name`, `version`, `private` (+221 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1169 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **35 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `_pay`, `provisioning.py`, `WhitelistLedger`, `Protocol`, `whitelist_menu`, `admin_handlers.py`, `test_whitelist.py`, `link_callback`, `test_whitelist_reconcile.py`, `billing.py`, `PaymentRequest`, `_reset_bot_user`, `test_renewal_recovery_pg.py`, `user_handlers.py`, `utcnow`, `test_trial_grants_migration.py`, `Server`, `Bot`, `test_user_reset.py`, `test_web_bridge.py`, `test_ux.py`, `get_account`, `test_renewal_recovery_worker.py`, `UserRepository`, `Settings`, `PanelUpdater`, `texts.py`, `whitelist.py`, `create_request`, `test_admin_confirm.py`, `test_subscription_purchases_migration.py`, `_phases`, `dataclasses`, `test_whitelist_pg.py`, `models.py`, `SubHubClient`, `admin_nav`, `whitelist_e2e.py`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Why does `Server` connect `Server` to `_pay`, `provisioning.py`, `WhitelistLedger`, `Protocol`, `test_whitelist.py`, `admin_handlers.py`, `keyboards.py`, `test_whitelist_reconcile.py`, `test_renewal_recovery_pg.py`, `_wl_state`, `test_crypto.py`, `user_handlers.py`, `utcnow`, `XuiClient`, `XuiPanelUpdater`, `test_whitelist_inbound_compat.py`, `Bot`, `test_user_reset.py`, `test_web_bridge.py`, `test_whitelist_xui.py`, `test_ux.py`, `EncryptedString`, `test_renewal_recovery_worker.py`, `What You Must Do When Invoked`, `sync_inventory`, `PanelUpdater`, `texts.py`, `whitelist.py`, `test_xui_updater.py`, `Контекст проекта`, `User`, `3.2. Купленный трафик`, `ServerRepository`, `test_whitelist_pg.py`, `models.py`, `reconcile_cycle`, `check_server`, `admin_nav`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `XuiClient` connect `XuiClient` to `provisioning.py`, `Panel`, `Protocol`, `test_whitelist_xui.py`, `admin_handlers.py`, `test_xui_payloads.py`, `Meter`, `test_xui_client.py`, `check_server`, `user_handlers.py`, `Settings`, `sync_inventory`, `XuiPanelUpdater`, `Server`, `xui_traffic_d3.py`, `whitelist_e2e.py`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 200 inferred relationships involving `User` (e.g. with `add_inbound()` and `admin_add_server_line()`) actually correct?**
  _`User` has 200 INFERRED edges - model-reasoned connections that need verification._
- **Are the 37 inferred relationships involving `MockPanelUpdater` (e.g. with `ClientServerMapping` and `Server`) actually correct?**
  _`MockPanelUpdater` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 103 inferred relationships involving `VpnClient` (e.g. with `notify_user_extended()` and `access_extended()`) actually correct?**
  _`VpnClient` has 103 INFERRED edges - model-reasoned connections that need verification._
- **Are the 63 inferred relationships involving `Server` (e.g. with `_finalize_new_server()` and `_finalize_whitelist_server()`) actually correct?**
  _`Server` has 63 INFERRED edges - model-reasoned connections that need verification._
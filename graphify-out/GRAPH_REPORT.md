# Graph Report - VpnBot  (2026-10-06)

## Corpus Check
- 165 files · ~175,759 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 9, .example 3, .conf 1)

## Summary
- 3021 nodes · 10930 edges · 137 communities (116 shown, 21 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1399 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `abeb5aaa`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- _pay
- test_provisioning.py
- datetime
- bind_requests.py
- test_whitelist.py
- user_handlers.py
- admin_handlers.py
- ReadOnlyPanel
- keyboards.py
- test_whitelist_reconcile.py
- billing.py
- test_subhub_trigger.py
- .confirmed
- VpnClientRepository
- collections_abc
- test_review_regressions.py
- test_whitelist_pg.py
- test_whitelist_bot.py
- main.go
- App.vue
- test_crypto.py
- main.py
- PaymentRequest
- utcnow
- XuiClient
- Settings
- XuiPanelUpdater
- test_broadcast.py
- _describe_event
- Protocol
- xui_traffic_d3.py
- User
- Контекст проекта
- Server
- MockPanelUpdater
- web_bridge.py
- test_whitelist_queue_worker.py
- test_whitelist_xui.py
- test_ux.py
- test_whitelist_payment_status.py
- package.json
- whitelist_e2e.py
- compilerOptions
- main_test.go
- api
- Контекст проекта
- .auth
- Panel
- Задание агенту: услуга «Обход белых списков» в VpnBot
- app
- main
- deployment_check.py
- web_preview.mjs
- ServerInbound
- _wl_state
- What You Must Do When Invoked
- test_security.py
- whitelist.py
- UserRepository
- find_panel_client
- whitelist_migration_check.py
- Telegram VPN Billing Bot
- Report
- D VPN — личный кабинет
- test_set_volume_is_shown_as_entered
- whitelist_background_e2e.py
- _push
- Приёмка услуги «Обход белых списков» — 5 октября 2026
- dvpn/site
- telegram-vpn-billing-bot
- Any
- AsyncSession
- MenuCallback
- VpnClient
- Meter
- 4. Точки интеграции
- test_xui_updater.py
- _phases
- WhitelistAccount
- IsAdmin
- models.py
- test_subscription_delete.py
- AGENTS.md
- api.ts
- FakeBot
- test_purchase_or_renewal_during_batch_read_is_not_overwritten_by_stale_reading
- EncryptedString
- Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026
- DiesOnFirstChange
- PanelUpdater
- WhitelistLedger
- Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026
- provisioning.py
- pytest
- Q: собери контекст проекта
- check_servers
- repositories.py
- SubHubClient
- graphify reference: query, path, explain
- conftest.py
- whitelist_admin
- texts.py
- wl_server
- Обновление production — 4 октября 2026
- whitelist_e2e_2026-10-05.md
- vue
- .list_inbounds
- _parse_server_line
- stack.sh
- whitelist_migration_2026-10-05.md
- scripts
- test_xui_client.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- ref_node_fs
- Ревью VpnBot — 4 октября 2026
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- Оставшиеся риски и решения
- test_plans.py
- extraction-spec.md
- ensure_inbounds_imported
- delete_user_subscription
- Протокол: R46 без принудительной синхронизации, фоновые циклы бота — 5 октября 2026
- _Crash
- .bot
- Настройка серверов и авто-провижининг
- country_flag
- provision_server
- sh
- test_plan_callback_carries_only_code

## God Nodes (most connected - your core abstractions)
1. `User` - 272 edges
2. `MockPanelUpdater` - 153 edges
3. `VpnClient` - 151 edges
4. `Server` - 145 edges
5. `Settings` - 137 edges
6. `PaymentRequest` - 112 edges
7. `PaymentStatus` - 99 edges
8. `_pay()` - 93 edges
9. `VpnClientRepository` - 86 edges
10. `XuiClient` - 82 edges

## Surprising Connections (you probably didn't know these)
- `6. Реальные 3x-ui и SubHub` --references--> `recover_confirmed_payments()`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → app/services/billing.py
- `Смена целевого inbound и перенос клиентов (2026-10-06)` --references--> `_push()`  [INFERRED]
  docs/WHITELIST_SERVICE.md → app/services/whitelist.py
- `Как формируется клиент` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py
- `16. R46 без принудительной синхронизации и фоновые циклы бота (результаты от 2026-10-05, после приёмки)` --references--> `_after_applied_payment()`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → app/bot/admin_handlers.py
- `3.2. Купленный трафик` --references--> `on_payment_action()`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → app/bot/admin_handlers.py

## Import Cycles
- None detected.

## Communities (137 total, 21 thin omitted)

### Community 0 - "_pay"
Cohesion: 0.13
Nodes (58): get_active_server(), process_due(), Фоновая очередь: применяет несинхронизированные состояния с backoff. Кроме…, Включённый whitelist-сервер (не более одного по уникальному индексу)., ops, _pay(), _add_candidate(), _available() (+50 more)

### Community 1 - "test_provisioning.py"
Cohesion: 0.15
Nodes (26): MappingRepository, ensure_vpn_client(), Возвращает VPN-клиента пользователя, создавая его при отсутствии., days_from_now(), _panel_info(), AsyncSession, HTTPXMock, Ссылка содержит subId, а в панели email другой — оба поля сохраняются. (+18 more)

### Community 2 - "datetime"
Cohesion: 0.13
Nodes (30): Единственная строка настроек услуги (id = 1)., WhitelistConfig, access_state(), _aware(), classify_origin(), confirm_traffic_payment(), _detect_external_disable(), get_config() (+22 more)

### Community 3 - "bind_requests.py"
Cohesion: 0.06
Nodes (41): BindRequestStatus, BindRequest, Заявка на привязку существующей подписки (до внедрения бота)., BindRequestRepository, AsyncSession, Меняет только имя, сохраняя сервер и все его связи., Меняет URL подписки, не затрагивая связи сервера., approve_request() (+33 more)

### Community 4 - "test_whitelist.py"
Cohesion: 0.09
Nodes (64): AwaitingCredit, list_open_events(), Фоновая сверка расхода: обходит все учёты пачками по ``limit``. Возвращает…, Сохранённое начисление, ещё не сверенное с расходом., Остатки пользователя; при доступной панели — с актуальной сверкой. Чтение…, Неприменённые события учёта пользователя в порядке возникновения., reconcile_usage(), user_overview() (+56 more)

### Community 5 - "user_handlers.py"
Cohesion: 0.08
Nodes (63): aiogram_fsm_context, aiogram_fsm_state, AdminStates, OnboardingStates, ProofStates, bind_request_received(), bind_request_waiting(), connection_preparing() (+55 more)

### Community 6 - "admin_handlers.py"
Cohesion: 0.10
Nodes (60): add_inbound(), add_server(), admin_add_server_cancel(), admin_add_server_line(), admin_broadcast_cancel(), admin_broadcast_send(), admin_delete_subscription_by_client_id(), admin_delete_subscription_cancel() (+52 more)

### Community 7 - "ReadOnlyPanel"
Cohesion: 0.25
Nodes (4): ReadOnlyPanel, test_import_network_failure_preserves_targets(), test_import_reconciles_deleted_disabled_and_new_inbounds(), test_stale_inbound_is_rejected_before_client_creation()

### Community 8 - "keyboards.py"
Cohesion: 0.11
Nodes (54): _adm(), admin_add_server_type_keyboard(), admin_back_keyboard(), admin_bind_keyboard(), admin_bind_retry_keyboard(), admin_confirm_delete_keyboard(), admin_home_keyboard(), admin_payment_keyboard() (+46 more)

### Community 9 - "test_whitelist_reconcile.py"
Cohesion: 0.06
Nodes (65): Состояние фоновой сверки расхода для админ-раздела (по данным процесса). «Обход…, reconcile_status_lines(), Состояние и наблюдаемость фоновой сверки (хранится в памяти процесса).…, Сколько прошло с завершения последнего обхода (в т. ч. с пропусками)., Верхняя граница возраста данных *сверенных* учётов последнего обхода., Сколько прошло с завершения последнего полностью подтверждённого обхода., Верхняя граница возраста данных всех учётов после последнего подтверждённого…, ReconcileStatus (+57 more)

### Community 10 - "billing.py"
Cohesion: 0.12
Nodes (44): Any, AsyncSession, Записывает событие в audit_logs., record(), _apply_panels(), _as_aware(), BillingError, BillingResult (+36 more)

### Community 11 - "test_subhub_trigger.py"
Cohesion: 0.08
Nodes (30): aiogram_filters, graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag) (+22 more)

### Community 12 - ".confirmed"
Cohesion: 0.40
Nodes (4): Каждый существующий учёт сверен: ни ошибок, ни пропусков., Доменная модель, Логика продления, Пользовательские сценарии

### Community 13 - "VpnClientRepository"
Cohesion: 0.10
Nodes (23): Any, TelegramObject, notify_user_expiry(), Уведомление пользователя об окончании подписки. True — если доставлено., datetime, Клиенты, которым пора слать уведомление об окончании. Берём тех, у кого задан…, _utcnow(), VpnClientRepository (+15 more)

### Community 15 - "test_review_regressions.py"
Cohesion: 0.25
Nodes (17): PendingServerUpdate, PendingServerUpdateRepository, apply_pending_for_server(), apply_pending_update(), _apply_to_server(), _as_aware(), _clear_payment_error_if_complete(), enqueue_failed_servers() (+9 more)

### Community 16 - "test_whitelist_pg.py"
Cohesion: 0.10
Nodes (30): 4. Автоматические тесты, _ledger(), Приёмка: гонки услуги на PostgreSQL, не покрытые test_whitelist_pg. Те же…, test_admin_block_is_not_lost_to_queue_reads_or_reconcile(), test_concurrent_rollouts_grant_once_and_keep_purchase(), test_purchase_confirmed_after_expiry_races_queue_without_enabling(), test_trial_double_click_grants_three_gb_once(), _confirm() (+22 more)

### Community 17 - "test_whitelist_bot.py"
Cohesion: 0.13
Nodes (36): aiogram_filters_callback_data, PaymentCallback, PlanCallback, Callback выбора тарифа пользователем. code — код тарифа из PLANS (1m/6m/12m)…, Пользовательский раздел «Обход белых списков». action: home | refresh | buy…, Callback админских действий над заявкой., WhitelistCallback, create_traffic_request() (+28 more)

### Community 18 - "main.go"
Cohesion: 0.07
Nodes (29): credentials, go_pkg_bytes, go_pkg_context, go_pkg_crypto_hmac, go_pkg_crypto_rand, go_pkg_crypto_sha256, go_pkg_crypto_subtle, go_pkg_crypto_tls (+21 more)

### Community 19 - "App.vue"
Cohesion: 0.07
Nodes (24): authTitles, awaiting, busy, code, comment, config, connection, days (+16 more)

### Community 20 - "test_crypto.py"
Cohesion: 0.14
Nodes (23): decrypt(), encrypt(), _fernet(), is_encrypted(), Возвращает Fernet, выведенный из SECRET_KEY, либо None если ключ не задан.…, Шифрует строку. Без SECRET_KEY возвращает значение как есть (dev/тесты)., Расшифровывает строку. Legacy-значения в открытом виде возвращает как есть., cryptography_fernet (+15 more)

### Community 21 - "main.py"
Cohesion: 0.07
Nodes (41): aiogram, aiogram_client_default, aiogram_fsm_storage_memory, aiogram_utils_token, app_bot, _command_name(), DbSessionMiddleware, _describe_message() (+33 more)

### Community 22 - "PaymentRequest"
Cohesion: 0.10
Nodes (25): AttachmentType, PaymentRequest, PaymentRepository, Берёт заявку с блокировкой строки (SELECT ... FOR UPDATE). На Postgres…, Число применённых оплат подписки (покупки трафика не учитываются)., Удаляет заявку (вместе с вложениями по каскаду)., Последняя успешная (применённая/подтверждённая) оплата пользователя.…, attach_proof() (+17 more)

### Community 23 - "utcnow"
Cohesion: 0.17
Nodes (38): IpObservation, _active_clients(), collect_all(), collect_for_client(), compute_status(), _level_for(), list_all_statuses(), list_flagged() (+30 more)

### Community 24 - "XuiClient"
Cohesion: 0.06
Nodes (40): Any, Exception, Response, _quote_path_segment(), Авторизованный запрос: гарантирует login и при истёкшей сессии выполняет…, Берёт CSRF-токен с /csrf-token (3x-ui >= 3.2.x). На старых панелях endpoint…, Базовая ошибка взаимодействия с панелью 3x-ui., Возвращает список inbound'ов панели с их БД-id, портами и протоколами. (+32 more)

### Community 25 - "Settings"
Cohesion: 0.06
Nodes (41): on_bind_action(), on_payment_action(), provision_user(), callback_query, notify_admins_bind_failed(), notify_admins_failed(), notify_admins_new_bind_request(), notify_admins_new_request() (+33 more)

### Community 26 - "XuiPanelUpdater"
Cohesion: 0.10
Nodes (22): QuotaClientState, Создаёт/обновляет клиента с квотой и проверяет результат чтением.…, Один клиент панели (глобальный по email), привязанный к её inbound'ам.…, Прочитанное с панели состояние клиента и его счётчика трафика., ServerProvision, client_record_body(), Извлекает model.Client из ответа ``clients/get``., _client_flows() (+14 more)

### Community 27 - "test_broadcast.py"
Cohesion: 0.31
Nodes (6): BroadcastResult, Рассылает текстовое сообщение всем пользователям. Сообщение отправляется…, send_broadcast(), FakeBot, test_send_broadcast_counts_sent_and_failed(), test_send_broadcast_empty_list()

### Community 28 - "_describe_event"
Cohesion: 0.33
Nodes (11): _describe_callback(), _describe_event(), CallbackQuery, Chat, _private_chat(), test_describe_addserver_redacts_secrets(), test_describe_callback_shows_action_only(), test_describe_command_without_args_shows_name() (+3 more)

### Community 29 - "Protocol"
Cohesion: 0.11
Nodes (36): Protocol, ProvisionTarget, Описание клиента, которого нужно создать/обновить в конкретном inbound., build_client_object(), client_identifier(), _client_uuid_for_api(), _looks_like_db_id(), merge_client_record_for_update() (+28 more)

### Community 30 - "xui_traffic_d3.py"
Cohesion: 0.20
Nodes (31): Конфигурация xray-клиента: SOCKS 127.0.0.1:10808 → VLESS по ссылке., xray_client_config(), accounted(), add_client(), container_started(), delta(), _disable_case(), Lab (+23 more)

### Community 31 - "User"
Cohesion: 0.16
Nodes (9): User, _expiry_notify_poller(), Фоновая рассылка уведомлений об окончании подписки (день/час/в момент)., Bot, Обработчики бота с сессией на каждое обновление, как у middleware., Пользователь создаёт заявку на подписку и присылает квитанцию., Сдвиг срока в БД вместо ожидания реального окончания (минуты, а не дни)., test_admin_pending_has_no_raw_angle_brackets() (+1 more)

### Community 32 - "Контекст проекта"
Cohesion: 0.13
Nodes (14): Архитектура, Безопасность аутентификации (backend/main.go), Важные инженерные правила, Доменная модель (таблицы веб-части, в БД бота), Запуск, Контекст проекта, Конфигурация, Локальные артефакты (+6 more)

### Community 33 - "Server"
Cohesion: 0.05
Nodes (30): connection_overview(), Unified SubHub connection screen with live server availability., server_button_label(), ClientServerMapping, Server, MockIpProvider, Mock-провайдер для тестов: возвращает заранее заданные IP по server_id., Реальный провайдер: берёт IP клиента из журнала панели 3x-ui. (+22 more)

### Community 34 - "MockPanelUpdater"
Cohesion: 0.13
Nodes (35): PaymentStatus, confirm_payment(), Идемпотентное подтверждение оплаты администратором. Повторный вызов для уже…, MockPanelUpdater, Mock-реализация: ничего не делает либо имитирует сбой нужных серверов. Для…, Inbound удалён на панели: его привязки исчезают у всех клиентов., main(), confirm() (+27 more)

### Community 35 - "web_bridge.py"
Cohesion: 0.08
Nodes (39): aiogram_types, aiohttp, PaymentAttachment, WebAccount, WebLinkRequest, get_plan(), PaymentPlan, Выгода относительно помесячной оплаты за тот же срок. (+31 more)

### Community 36 - "test_whitelist_queue_worker.py"
Cohesion: 0.05
Nodes (60): _queue_worker_alive(), Очередь применения квот «Обхода белых списков» на панели. Единственный…, Фоновая сверка расхода whitelist-услуги: полный обход пачками. Работает…, Запускает фоновые циклы процесса бота (кроме доставки сайта). Одна сборка для…, Фоновая периодическая проверка доступности серверов 3x-ui. Очередь применения…, _server_health_poller(), pending_applied(), subhub_sync() (+52 more)

### Community 37 - "test_whitelist_xui.py"
Cohesion: 0.21
Nodes (34): QuotaTarget, Абсолютное целевое состояние клиента с учётом трафика. ``total_bytes`` —…, 3.5. Учёт трафика и интеграция 3x-ui, _apply_existing(), _auth(), _body(), _inbound(), HTTPXMock (+26 more)

### Community 38 - "test_ux.py"
Cohesion: 0.09
Nodes (38): AdminCallback, Навигация по админ-панели (/admin). action: home | servers | server | rename |…, custom_emoji_id(), emoji_char(), Возвращает unicode-символ значка (без анимации)., Возвращает custom_emoji_id значка или None, если значок не найден., Главное меню под приветствием. Зависит от наличия активной подписки., welcome_menu() (+30 more)

### Community 39 - "test_whitelist_payment_status.py"
Cohesion: 0.21
Nodes (26): admin_history(), admin_payment_card(), admin_whitelist_home(), fmt_money(), payment_status_label(), _buy(), _down(), _fresh() (+18 more)

### Community 40 - "package.json"
Cohesion: 0.11
Nodes (17): lucide-vue-next, typescript, vite, @vitejs/plugin-vue, vue-tsc, dependencies, lucide-vue-next, vue (+9 more)

### Community 41 - "whitelist_e2e.py"
Cohesion: 0.07
Nodes (41): build_updater(), argparse, import_control_inbound(), main(), panel_view(), Any, Path, Квота трафика 3x-ui → SubHub на реальной панели, без маскирующего… (+33 more)

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
Nodes (12): Админские команды, Антишеринг, Интеграция с 3x-ui, Контекст проекта, Конфигурация, Локальные артефакты, Назначение, Основные пользовательские сценарии (+4 more)

### Community 46 - ".auth"
Cohesion: 0.53
Nodes (6): net/http.Request, net/http.ResponseWriter, decode(), digest(), fail(), respond()

### Community 47 - "Panel"
Cohesion: 0.11
Nodes (9): admin_servers(), Panel, Прямой доступ к тестовой панели — для проверок и действий «вручную в панели»., Разрешает трафик к частной подсети стенда — только на тестовых панелях.…, VLESS + REALITY (TCP), как у рабочих серверов; цель — локальный TLS 1.3., {'body': тело клиента, 'inboundIds': [...], 'traffic': client_traffics|None}., Изменение клиента «вручную в панели» (тот же API, что у веб-интерфейса)., up+down из счётчиков самого Xray панели (statsquery), минуя учёт панели.… (+1 more)

### Community 48 - "Задание агенту: услуга «Обход белых списков» в VpnBot"
Cohesion: 0.15
Nodes (12): 1. Контекст проекта, 2. Согласованное поведение услуги, 3. Сервер и настройки администратора, 4. Технический контракт учёта трафика, 5. Биллинг, конкуренция и восстановление, 6. Пользовательский интерфейс, 7. Обязательная проверка, 8. Порядок работы и сдача (+4 more)

### Community 49 - "app"
Cohesion: 0.29
Nodes (6): app, config, context.Context, github.com/jackc/pgx/v5/pgxpool.Pool, net/http.Client, pgx.Tx

### Community 50 - "main"
Cohesion: 0.22
Nodes (7): bucket, limiter, net/http.Handler, sync.Mutex, time.Time, env(), main()

### Community 51 - "deployment_check.py"
Cohesion: 0.25
Nodes (9): Serialize access mutations per user, including commits and panel calls., user_operation(), inspect, check_released(), Run against a restored scratch database only; never calls real panel APIs., test_user_operations_serialize_and_release_on_failure(), first(), second() (+1 more)

### Community 52 - "web_preview.mjs"
Cohesion: 0.29
Nodes (6): ref_node_fs_promises, ref_node_http, ref_node_path, ref_node_url, root, types

### Community 53 - "ServerInbound"
Cohesion: 0.07
Nodes (63): Inbound на панели сервера, в который нужно заводить клиентов. На одном сервере…, ServerInbound, build_provision_spec(), choose_inbound(), check_inbound(), _check_vless_reality(), describe(), _foreign_flows() (+55 more)

### Community 54 - "_wl_state"
Cohesion: 0.20
Nodes (25): Применяет состояние учёта пользователя на whitelist-панели., sync_user(), _available(), Смена эпохи счётчика whitelist-панели при неприменённых событиях учёта. Внешний…, Пересоздание клиента: значение не уменьшилось, сменилась строка статистики., Сброс обнаруживается по последнему прочитанному значению, а не только по…, Строка до миграции f3a4b5c6d7e8: последнее чтение есть только в границах…, Операция взяла время до пакетного чтения, а счётчик прочитала после него. (+17 more)

### Community 55 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 56 - "test_security.py"
Cohesion: 0.06
Nodes (49): forward_proof_to_admins(), UserRole, FakeBot, FakeMessage, _make_payment(), _make_waiting(), _persist_payment(), AsyncSession (+41 more)

### Community 57 - "whitelist.py"
Cohesion: 0.11
Nodes (21): admin_summary(), AdminSummary, _applied_target(), _last_online(), PurchaseResult, Decimal, Exception, Услуга «Обход белых списков»: учёт трафика и квота на whitelist-сервере. Модель… (+13 more)

### Community 58 - "UserRepository"
Cohesion: 0.11
Nodes (20): Удаляет пользователя и связанные записи (каскад в ORM)., Telegram ID всех пользователей, когда-либо запускавших бота., Генерирует короткий уникальный публичный ID пользователя., UserRepository, AsyncSession, test_all_telegram_ids_returns_every_user(), test_generated_public_id_is_unique_and_hex(), AsyncSession (+12 more)

### Community 59 - "find_panel_client"
Cohesion: 0.29
Nodes (8): find_panel_client(), _panel_client_secret(), PanelClientInfo, _pick_secret(), Нормализованные данные существующего клиента панели., Fallback для legacy API: первое непустое строковое значение., Ищет клиента панели по email и нормализует его поля., fake_find()

### Community 60 - "whitelist_migration_check.py"
Cohesion: 0.27
Nodes (19): alembic(), check(), docker(), downgrade_cycle(), dsn(), ensure_defaults_idempotent(), main(), plain() (+11 more)

### Community 61 - "Telegram VPN Billing Bot"
Cohesion: 0.13
Nodes (12): Telegram VPN Billing Bot, Админ-команды, Антишеринг-мониторинг, Возможности, Граф кода (graphify), Единая подписка SubHub, Конфигурация, Локальный запуск (dev) (+4 more)

### Community 63 - "D VPN — личный кабинет"
Cohesion: 0.25
Nodes (7): D VPN — личный кабинет, Архитектура, Запуск вместе с существующим ботом, Локальная разработка, Результаты проверки, Что реализовано, Эксплуатация

### Community 64 - "test_set_volume_is_shown_as_entered"
Cohesion: 0.07
Nodes (51): _after_applied_payment(), _parse_gb(), Уведомления и SubHub после применения; возвращает итог для администратора.…, HTML-строка с анимированным значком для вставки в текст сообщения., tg(), notify_user_traffic_credited(), access_extended(), admin_clients_list() (+43 more)

### Community 65 - "whitelist_background_e2e.py"
Cohesion: 0.13
Nodes (20): app_db, Настраивает логирование приложения. - корневой логгер: WARNING (чтобы сторонние…, setup_logging(), do_run_migrations(), run_migrations_online(), build_client_record(), Унифицированный объект клиента для нового client-API (3x-ui >= 3.2.x).…, asyncio (+12 more)

### Community 66 - "_push"
Cohesion: 0.11
Nodes (24): Привязка клиента whitelist-панели к inbound'у, созданная самой услугой. Строка…, WhitelistPlacement, _confirm_attach(), _find_placement(), _Link, placement_drift(), placement_progress(), PlacementProgress (+16 more)

### Community 67 - "Приёмка услуги «Обход белых списков» — 5 октября 2026"
Cohesion: 0.13
Nodes (13): PaymentRequestError, PendingRequestExists, Exception, Заявку нельзя создать по бизнес-правилам., У пользователя уже есть заявка с отправленной квитанцией., 10. Заключение, 14. Исправление D-2: SubHub собирается без ручной установки greenlet (результаты от 2026-10-05, после приёмки), 19. Перенос клиентов при смене целевого inbound (2026-10-06, P1 ревью) (+5 more)

### Community 72 - "AsyncSession"
Cohesion: 0.18
Nodes (22): adjust_balance(), after_access_change(), _clear_placement(), forget_panel_client(), get_account(), _list_placements(), mark_dirty(), AsyncSession (+14 more)

### Community 73 - "MenuCallback"
Cohesion: 0.15
Nodes (14): BindCallback, MenuCallback, OnboardCallback, Callback админских действий над заявкой на привязку подписки., Навигация по inline-меню (редактирование сообщения на месте). action: home |…, Онбординг: был ли пользователь клиентом до внедрения бота., Админ-раздел услуги «Обход белых списков». action: home | sync | choose (value…, WhitelistAdminCallback (+6 more)

### Community 74 - "VpnClient"
Cohesion: 0.22
Nodes (21): admin_profile(), _is_active(), _needs_onboarding(), Показываем вопрос только новым пользователям без VPN-клиента., VpnClient, has_active_timed_client(), has_client_access(), has_unlimited_bound_client() (+13 more)

### Community 75 - "Meter"
Cohesion: 0.22
Nodes (4): Meter, Any, Временной ряд каждые 0,5 с: PID Xray, счётчики Xray и панели по email., Моменты изменения учёта панели — это моменты опросов задачи трафика.

### Community 76 - "4. Точки интеграции"
Cohesion: 0.18
Nodes (11): claim_inbound(), ensure_defaults(), Администратор признаёт привязки клиентов услуги к inbound'у привязками услуги.…, Идемпотентная инициализация: настройки и начальные пакеты., 1. Что получает пользователь, 3. Модель учёта, 4. Точки интеграции, 6. Порядок внедрения (+3 more)

### Community 77 - "test_xui_updater.py"
Cohesion: 0.18
Nodes (11): ProvisionInbound, Inbound сервера, к которому нужно привязать клиента., pytest_httpx, test_attach_success_without_membership_is_not_provisioning_success(), _mock_auth(), HTTPXMock, _spec(), test_legacy_provisioning_keeps_one_email_for_every_inbound() (+3 more)

### Community 78 - "_phases"
Cohesion: 0.08
Nodes (32): Acts, _async(), describe(), docker(), expect_poll(), expect_trigger(), _forbid_sync(), from_source() (+24 more)

### Community 79 - "WhitelistAccount"
Cohesion: 0.18
Nodes (14): Бизнес-учёт трафика пользователя на whitelist-сервере. Остатки…, WhitelistAccount, AccessState, compute_target(), _defer(), quota_room(), Повтор через backoff 1 мин → 1 ч; ошибка сохраняется для администратора., Гарантированный объём квоты сверх контрольной точки. Остатки с неприменёнными… (+6 more)

### Community 80 - "IsAdmin"
Cohesion: 0.21
Nodes (10): IsAdmin, TelegramObject, Пропускает событие только если пользователь — администратор., BaseFilter, test_is_admin_filter_accepts_admin(), test_is_admin_filter_rejects_missing_user(), test_is_admin_filter_rejects_regular_user(), test_settings_is_admin() (+2 more)

### Community 81 - "models.py"
Cohesion: 0.11
Nodes (23): Base, Базовый класс для всех ORM-моделей., TimestampMixin, Durable per-admin Telegram delivery, retried independently of HTTP requests., Пакет покупки трафика «Обход белых списков» (настраивается админом)., TrafficPackage, WebDelivery, WebSession (+15 more)

### Community 82 - "test_subscription_delete.py"
Cohesion: 0.23
Nodes (9): _FakeBot, _FakeMessage, _FakeState, Any, AsyncSession, test_admin_delete_subscription_uses_client_id_not_telegram_id(), test_delete_subscription_keeps_local_client_on_panel_failure(), test_delete_subscription_removes_panel_and_local_client() (+1 more)

### Community 84 - "api.ts"
Cohesion: 0.33
Nodes (4): APIError, Configuration, Plan, Profile

### Community 85 - "FakeBot"
Cohesion: 0.22
Nodes (7): 2. Стенд, async_sessionmaker, FakeBot, Any, test_reject_then_notify_user(), test_expiry_after_downtime_sends_only_current_notice(), test_failed_expiry_notice_is_retried()

### Community 86 - "test_purchase_or_renewal_during_batch_read_is_not_overwritten_by_stale_reading"
Cohesion: 0.20
Nodes (10): 3.3. Ограничения доступа, 3.6. Биллинг, конкуренция, восстановление, 3.7. Интерфейс, миграции, устройство, 3. Матрица требований и доказательств, parametrize, test_purchase_or_renewal_during_batch_read_is_not_overwritten_by_stale_reading(), concurrent_operation(), test_exhaustion_disables_only_whitelist_config_and_purchase_resumes() (+2 more)

### Community 87 - "EncryptedString"
Cohesion: 0.25
Nodes (7): EncryptedString, Any, Прозрачно шифрует значение при записи и расшифровывает при чтении. - Если…, Важные инженерные правила проекта, P1 — пароли панелей не защищены шифрованием приложения, 5. Миграции и резервная копия (PostgreSQL 16.15), TypeDecorator

### Community 88 - "Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026"
Cohesion: 0.50
Nodes (3): Прогон до исправления (SubHub `d9a2c80` + незакоммиченные правки, не относящиеся к задаче), Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026, Финальный прогон после исправления

### Community 89 - "DiesOnFirstChange"
Cohesion: 0.25
Nodes (7): BaseException, DiesOnFirstChange, die(), ProcessKilled, Any, Имитация гибели процесса: не перехватывается ``except Exception`` кода бота., Настоящий updater, у которого первое изменение панели «убивает процесс».

### Community 90 - "PanelUpdater"
Cohesion: 0.10
Nodes (20): PanelUpdater, Интерфейс работы с клиентом в панели. Реализуется как mock (для тестов/MVP) и…, _apply_quota(), _BatchResult, _finish_reconcile(), Читает клиента whitelist-панели; (None, ошибка) при недоступности., Сверка прочитанного после записи и, если квота изменилась, повторная запись.…, Итог обхода учётов (накапливается между запусками, если обход прерывали).… (+12 more)

### Community 91 - "WhitelistLedger"
Cohesion: 0.11
Nodes (33): Журнал выдач/начислений/корректировок, привязанных к исходной операции. Выдача…, WhitelistLedger, _append_note(), apply_event(), apply_usage(), _consistent_anchor(), _Context, _infer_anchor() (+25 more)

### Community 92 - "Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026"
Cohesion: 0.33
Nodes (5): 1. 3x-ui v3.9.0 (`ghcr.io/mhsanaei/3x-ui:v3.9.0`), финальный прогон — 25 OK, 5 FAIL, 2. 3x-ui v3.9.0, повтор S6, S6b, S7 с исправленным расчётом — 5 OK, 0 FAIL, 3. 3x-ui v3.5.0 (`ghcr.io/mhsanaei/3x-ui:v3.5.0`, Xray 26.7.11) — 5 OK, 9 FAIL, 4. Первый (предварительный) прогон на v3.9.0 — 24 OK, 6 FAIL, Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026

### Community 93 - "provisioning.py"
Cohesion: 0.10
Nodes (45): ServerUpdateResult, apply_access(), apply_access_to_server(), bind_existing_client(), bind_user_by_public_id(), BindResult, _build_spec(), client_email() (+37 more)

### Community 94 - "pytest"
Cohesion: 0.25
Nodes (8): 3.4. Сервер, импорт, выдача, администрирование, pytest, _payment(), rollout(), parametrize, Приёмка: происхождение текущего доступа при выдаче услуги нынешним…, test_origin_of_current_access(), test_second_enabled_whitelist_server_is_rejected()

### Community 95 - "Q: собери контекст проекта"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: собери контекст проекта, Source Nodes

### Community 96 - "check_servers"
Cohesion: 0.12
Nodes (9): check_server(), check_servers(), AsyncSession, Проверяет доступность панели 3x-ui одного сервера. Успешный login считается…, Проверяет все серверы и сохраняет результат в БД. Возвращает отображение…, Фоновые задачи, test_health_check_server_returns_false_on_error(), login() (+1 more)

### Community 97 - "repositories.py"
Cohesion: 0.16
Nodes (14): AuditLog, AuditRepository, app_services, datetime, collect_links(), AsyncSession, Возвращает список (метка, ссылка-подписка) по всем серверам пользователя. Для…, _sub_link() (+6 more)

### Community 98 - "SubHubClient"
Cohesion: 0.10
Nodes (22): build_happ_import_url(), Exception, Resolve the first panel identity known to SubHub. Older bot records can have a…, Base error for the internal SubHub integration., The panels have not exposed this identity to SubHub yet., The identity exists, but currently has no active nodes., Build a signed HTTPS trampoline for importing a legacy subscription., Small authenticated client for the SubHub admin API. Subscription URLs and… (+14 more)

### Community 99 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 100 - "conftest.py"
Cohesion: 0.44
Nodes (9): pytest_asyncio, admin(), AsyncSession, datetime, fixture, server(), session(), user() (+1 more)

### Community 101 - "whitelist_admin"
Cohesion: 0.11
Nodes (22): aiogram_exceptions, aiogram_methods, _edit_panel(), CallbackQuery, InlineKeyboardMarkup, Редактирует сообщение админ-панели, мягко гасит ошибки. parse_mode=None —…, whitelist_admin(), _whitelist_home() (+14 more)

### Community 102 - "texts.py"
Cohesion: 0.07
Nodes (41): admin_nav(), _finalize_whitelist_server(), ip_scan(), Добавляет сервер услуги и сразу сверяет его inbound'ы. До успешной сверки с…, sharing_report(), admin_add_cancelled(), admin_add_server_prompt(), admin_bind_pending() (+33 more)

### Community 103 - "wl_server"
Cohesion: 0.22
Nodes (5): panel(), fixture, service_on(), std_target(), wl_server()

### Community 104 - "Обновление production — 4 октября 2026"
Cohesion: 0.25
Nodes (6): PAY-1C3F1344, Внедрено, Дополнительный дефект, обнаруженный при приёмке, Незавершённые операции, Обновление production — 4 октября 2026, Проверки и резервирование

### Community 108 - "_parse_server_line"
Cohesion: 0.20
Nodes (10): _parse_server_line(), Парсит 'name|country|panel_url|username|password|[kind]|[sub]|[purpose]'.…, parametrize, test_parse_server_line_accepts_valid(), test_parse_server_line_rejects_invalid(), test_settings_rejects_dangerous_numeric_values(), test_unknown_or_forged_plan_code_rejected(), test_validate_server_name_rejects_invalid() (+2 more)

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

### Community 117 - "Ревью VpnBot — 4 октября 2026"
Cohesion: 0.25
Nodes (8): Исправления в рабочем дереве, Объём и доказательства, Порядок применения в production, Проверки, Разбор PAY-1C3F1344, Ревью VpnBot — 4 октября 2026, Результат, Устройство production

### Community 120 - "Оставшиеся риски и решения"
Cohesion: 0.29
Nodes (7): P1/P2 — частичный успех внешней операции требует сверки, P1 — административные права зависят от тарифа, P1 — биллинг и панели не образуют одну транзакцию, P2 — мониторинг и производительность, P2 — старые ошибки оплат без ожидающих задач, P2 — эксплуатация и воспроизводимость, Оставшиеся риски и решения

### Community 121 - "test_plans.py"
Cohesion: 0.33
Nodes (4): AsyncSession, test_changing_plan_updates_open_request(), test_create_request_with_plan(), test_get_plan()

### Community 127 - "ensure_inbounds_imported"
Cohesion: 0.40
Nodes (5): ensure_inbounds_imported(), has_targets(), Импортирует inbound'ы для включённых серверов, у которых их ещё нет. Нужно для…, Есть ли хотя бы один включённый сервер с включённым inbound для провижининга., test_ensure_inbounds_imported_imports_when_missing()

### Community 128 - "delete_user_subscription"
Cohesion: 0.50
Nodes (5): _delete_local_subscription(), delete_user_subscription(), AsyncSession, Удаляет VPN-подписку пользователя с панелей и из БД бота. История оплат, заявки…, SubscriptionDeleteResult

### Community 129 - "Протокол: R46 без принудительной синхронизации, фоновые циклы бота — 5 октября 2026"
Cohesion: 0.40
Nodes (4): Прогон 1 — до исправлений (бот и SubHub без изменений этой задачи), Прогон 2 — SubHub исправлен (D-6), бот: исправлен D-5, исправления D-7 и D-8 временно сняты, Прогон 3 — финальный, все исправления, Протокол: R46 без принудительной синхронизации, фоновые циклы бота — 5 октября 2026

### Community 130 - "_Crash"
Cohesion: 0.40
Nodes (3): RuntimeError, _Crash, Процесс завершился после запроса к панели, до commit.

### Community 131 - ".bot"
Cohesion: 0.50
Nodes (3): Запуск, Запуск через Docker Compose, API

### Community 132 - "Настройка серверов и авто-провижининг"
Cohesion: 0.50
Nodes (4): Как формируется клиент, Настройка серверов и авто-провижининг, Перенос пользователей, существовавших до бота, Шаг 1. Добавить серверы

### Community 133 - "country_flag"
Cohesion: 0.67
Nodes (3): country_flag(), Эмодзи-флаг по ISO2-коду страны (напр. 'SE' -> 🇸🇪). Иначе пусто., test_country_flag()

### Community 135 - "sh"
Cohesion: 0.13
Nodes (12): 15. Лимит трафика 3x-ui → SubHub: единица `totalGB` и источник расхода (результаты от 2026-10-05, после приёмки), 2. Проверенный контракт 3x-ui, set_inbound(), main(), panel_call(), Новый контейнер панели: учётные данные, шаблон для частной сети, inbound., docker stop/start: новый процесс панели и новый процесс Xray., PID Xray, его возраст (с) и счётчики пользователей Xray (up+down по email). (+4 more)

## Knowledge Gaps
- **178 isolated node(s):** `credentials`, `dvpn/site`, `name`, `version`, `private` (+173 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 972 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `delete_user_subscription`, `test_provisioning.py`, `datetime`, `bind_requests.py`, `test_whitelist.py`, `user_handlers.py`, `admin_handlers.py`, `_pay`, `test_whitelist_reconcile.py`, `billing.py`, `VpnClientRepository`, `test_review_regressions.py`, `test_whitelist_pg.py`, `test_whitelist_bot.py`, `main.py`, `PaymentRequest`, `utcnow`, `Settings`, `test_broadcast.py`, `MockPanelUpdater`, `web_bridge.py`, `test_ux.py`, `test_whitelist_payment_status.py`, `whitelist_e2e.py`, `deployment_check.py`, `test_security.py`, `whitelist.py`, `UserRepository`, `test_set_volume_is_shown_as_entered`, `whitelist_background_e2e.py`, `VpnClient`, `_phases`, `WhitelistAccount`, `IsAdmin`, `models.py`, `test_subscription_delete.py`, `FakeBot`, `WhitelistLedger`, `provisioning.py`, `repositories.py`, `conftest.py`, `whitelist_admin`, `texts.py`, `test_plans.py`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `Server` connect `Server` to `delete_user_subscription`, `_pay`, `test_provisioning.py`, `bind_requests.py`, `test_whitelist.py`, `admin_handlers.py`, `keyboards.py`, `test_whitelist_reconcile.py`, `test_review_regressions.py`, `test_whitelist_pg.py`, `test_whitelist_bot.py`, `test_crypto.py`, `utcnow`, `Settings`, `XuiPanelUpdater`, `MockPanelUpdater`, `web_bridge.py`, `test_whitelist_xui.py`, `test_ux.py`, `Контекст проекта`, `ServerInbound`, `_wl_state`, `What You Must Do When Invoked`, `whitelist.py`, `UserRepository`, `find_panel_client`, `whitelist_background_e2e.py`, `_push`, `test_xui_updater.py`, `models.py`, `EncryptedString`, `PanelUpdater`, `WhitelistLedger`, `provisioning.py`, `pytest`, `check_servers`, `repositories.py`, `conftest.py`, `whitelist_admin`, `texts.py`, `wl_server`, `_parse_server_line`, `ensure_inbounds_imported`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Why does `Settings` connect `Settings` to `test_whitelist.py`, `user_handlers.py`, `admin_handlers.py`, `test_subhub_trigger.py`, `test_review_regressions.py`, `test_whitelist_bot.py`, `test_crypto.py`, `main.py`, `utcnow`, `test_broadcast.py`, `User`, `web_bridge.py`, `test_whitelist_queue_worker.py`, `test_ux.py`, `test_whitelist_payment_status.py`, `whitelist_e2e.py`, `ServerInbound`, `test_security.py`, `test_set_volume_is_shown_as_entered`, `VpnClient`, `IsAdmin`, `test_subscription_delete.py`, `FakeBot`, `repositories.py`, `whitelist_admin`, `texts.py`, `_parse_server_line`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 171 inferred relationships involving `User` (e.g. with `add_inbound()` and `admin_add_server_line()`) actually correct?**
  _`User` has 171 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `MockPanelUpdater` (e.g. with `ClientServerMapping` and `Server`) actually correct?**
  _`MockPanelUpdater` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 92 inferred relationships involving `VpnClient` (e.g. with `notify_user_extended()` and `access_extended()`) actually correct?**
  _`VpnClient` has 92 INFERRED edges - model-reasoned connections that need verification._
- **Are the 57 inferred relationships involving `Server` (e.g. with `_finalize_new_server()` and `_finalize_whitelist_server()`) actually correct?**
  _`Server` has 57 INFERRED edges - model-reasoned connections that need verification._
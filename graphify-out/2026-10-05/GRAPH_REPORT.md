# Graph Report - VpnBot  (2026-10-05)

## Corpus Check
- 153 files · ~133,995 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 17 file(s) not represented in the graph (top: (none) 9, .example 3, .conf 1)

## Summary
- 2559 nodes · 9048 edges · 118 communities (99 shown, 19 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1213 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6e82f662`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- provisioning.py
- test_provisioning.py
- whitelist.py
- test_legacy_bind.py
- MockPanelUpdater
- user_handlers.py
- admin_handlers.py
- import_inbounds
- keyboards.py
- test_whitelist_reconcile.py
- PaymentRequest
- SubHubClient
- menu_nav
- models.py
- collections_abc
- pending_updates.py
- test_whitelist_pg.py
- test_payment_kind_conflict.py
- main.go
- App.vue
- config.py
- main.py
- create_request
- utcnow
- XuiClient
- Settings
- FakeState
- operation_lock.py
- middlewares.py
- Protocol
- reconcile_cycle
- User
- Контекст проекта
- whitelist_e2e.py
- PaymentStatus
- web_bridge.py
- bind_existing_client
- XuiPanelUpdater
- Server
- Panel
- package.json
- subhub_quota_e2e.py
- compilerOptions
- main_test.go
- api
- Контекст проекта
- .auth
- select_plan
- Задание агенту: услуга «Обход белых списков» в VpnBot
- app
- main
- Telegram VPN Billing Bot
- web_preview.mjs
- test_whitelist_inbound_compat.py
- AsyncSession
- What You Must Do When Invoked
- test_security.py
- PanelUpdater
- UserRepository
- onboard_legacy_link
- whitelist_migration_check.py
- sync_inventory
- ref_node_fs_promises
- D VPN — личный кабинет
- admin_nav
- ServerInbound
- test_plans.py
- texts.py
- dvpn/site
- telegram-vpn-billing-bot
- fmt_gb
- MenuCallback
- Настройка серверов и авто-провижининг
- VpnClient
- test_all_inline_buttons_have_color_style
- FakeBot
- AsyncSession
- Услуга «Обход белых списков» — реализация и порядок внедрения
- connection_overview
- SubHub
- EncryptedString
- _FakeMessage
- AGENTS.md
- api.ts
- _parse_server_line
- Обновление production — 4 октября 2026
- Ревью VpnBot — 4 октября 2026
- Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026
- Приёмка услуги «Обход белых списков» — 5 октября 2026
- emoji.py
- vue
- VpnClientRepository
- Q: собери контекст проекта
- Оставшиеся риски и решения
- subscriptions.py
- answer_callback
- graphify reference: query, path, explain
- conftest.py
- check_server
- devDependencies
- whitelist_e2e_2026-10-05.md
- .list_inbounds
- test_ux.py
- stack.sh
- whitelist_migration_2026-10-05.md
- test_xui_client.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- check_servers
- extraction-spec.md

## God Nodes (most connected - your core abstractions)
1. `User` - 266 edges
2. `VpnClient` - 146 edges
3. `Server` - 135 edges
4. `Settings` - 128 edges
5. `MockPanelUpdater` - 114 edges
6. `PaymentRequest` - 103 edges
7. `PaymentStatus` - 91 edges
8. `VpnClientRepository` - 86 edges
9. `XuiClient` - 77 edges
10. `PanelUpdater` - 66 edges

## Surprising Connections (you probably didn't know these)
- `6. Реальные 3x-ui и SubHub` --references--> `recover_confirmed_payments()`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → app/services/billing.py
- `Как формируется клиент` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py
- `Логика продления` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py
- `3.2. Купленный трафик` --references--> `on_payment_action()`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → app/bot/admin_handlers.py
- `3.4. Сервер, импорт, выдача, администрирование` --references--> `IsAdmin`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → app/bot/filters.py

## Import Cycles
- None detected.

## Communities (118 total, 19 thin omitted)

### Community 0 - "provisioning.py"
Cohesion: 0.13
Nodes (34): ServerUpdateResult, apply_access(), apply_access_to_server(), BindResult, _build_spec(), client_email(), client_identity(), _ensure_presence_mappings() (+26 more)

### Community 1 - "test_provisioning.py"
Cohesion: 0.13
Nodes (28): MappingRepository, bind_user_by_public_id(), Клиент найден на конкретном сервере., Привязывает пользователя по ID из ссылки-подписки. Ищет клиента на всех…, ServerClientPresence, days_from_now(), _panel_info(), AsyncSession (+20 more)

### Community 2 - "whitelist.py"
Cohesion: 0.08
Nodes (51): Бизнес-учёт трафика пользователя на whitelist-сервере. Остатки…, Журнал выдач/начислений/корректировок, привязанных к исходной операции. Выдача…, WhitelistAccount, WhitelistLedger, AccessState, adjust_balance(), admin_summary(), AdminSummary (+43 more)

### Community 3 - "test_legacy_bind.py"
Cohesion: 0.09
Nodes (30): BindRequest, Заявка на привязку существующей подписки (до внедрения бота)., BindRequestRepository, Меняет только имя, сохраняя сервер и все его связи., Меняет URL подписки, не затрагивая связи сервера., approve_request(), BindApproveResult, BindRequestError (+22 more)

### Community 4 - "MockPanelUpdater"
Cohesion: 0.05
Nodes (123): confirm_payment(), Идемпотентное подтверждение оплаты администратором. Повторный вызов для уже…, MockPanelUpdater, datetime, Mock-реализация: ничего не делает либо имитирует сбой нужных серверов. Для…, create_traffic_request(), Заявка на покупку пакета «Обход белых списков». Создаётся только при активной…, AwaitingCredit (+115 more)

### Community 5 - "user_handlers.py"
Cohesion: 0.14
Nodes (32): aiogram_fsm_context, aiogram_fsm_state, OnboardingStates, bind_request_waiting(), no_open_request(), onboarding_legacy_question(), onboarding_send_link_prompt(), admin_denied() (+24 more)

### Community 6 - "admin_handlers.py"
Cohesion: 0.11
Nodes (53): add_inbound(), add_server(), admin_add_server_cancel(), admin_add_server_line(), admin_broadcast_cancel(), admin_broadcast_send(), admin_delete_subscription_by_client_id(), admin_delete_subscription_cancel() (+45 more)

### Community 7 - "import_inbounds"
Cohesion: 0.24
Nodes (12): ensure_inbounds_imported(), fetch_inbounds(), import_inbounds(), Any, Сверяет inbound'ы панели с локальными целями провижининга. Удалённые и…, Читает список inbound'ов панели (``inbounds/list``) как есть., Сверка реестра с уже прочитанным списком (см. :func:`import_inbounds`)., Импортирует inbound'ы для включённых серверов, у которых их ещё нет. Нужно для… (+4 more)

### Community 8 - "keyboards.py"
Cohesion: 0.20
Nodes (23): Админ-раздел услуги «Обход белых списков». action: home | sync | choose (value…, WhitelistAdminCallback, _adm(), admin_add_server_type_keyboard(), admin_back_keyboard(), admin_confirm_delete_keyboard(), admin_home_keyboard(), admin_servers_keyboard() (+15 more)

### Community 9 - "test_whitelist_reconcile.py"
Cohesion: 0.07
Nodes (41): Состояние и наблюдаемость фоновой сверки (хранится в памяти процесса).…, Сколько прошло с завершения последнего обхода без ошибок., Верхняя граница возраста данных учёта после последнего чистого обхода. Учёт мог…, Фоновая сверка расхода: обходит все учёты пачками по ``limit``. Возвращает…, reconcile_usage(), ReconcileStatus, _add_account(), _cycle() (+33 more)

### Community 10 - "PaymentRequest"
Cohesion: 0.06
Nodes (66): PaymentRequest, PaymentRepository, Берёт заявку с блокировкой строки (SELECT ... FOR UPDATE). На Postgres…, Число применённых оплат подписки (покупки трафика не учитываются)., Удаляет заявку (вместе с вложениями по каскаду)., Последняя успешная (применённая/подтверждённая) оплата пользователя.…, _apply_panels(), _as_aware() (+58 more)

### Community 11 - "SubHubClient"
Cohesion: 0.10
Nodes (24): build_happ_import_url(), Exception, Base error for the internal SubHub integration., Resolve the first panel identity known to SubHub. Older bot records can have a…, The panels have not exposed this identity to SubHub yet., The identity exists, but currently has no active nodes., Build a signed HTTPS trampoline for importing a legacy subscription., Small authenticated client for the SubHub admin API. Subscription URLs and… (+16 more)

### Community 12 - "menu_nav"
Cohesion: 0.14
Nodes (24): _back_button(), back_keyboard(), _btn(), extend_plans_keyboard(), free_proxies_keyboard(), install_guides_keyboard(), news_channel_keyboard(), _plan_label() (+16 more)

### Community 13 - "models.py"
Cohesion: 0.10
Nodes (35): app_bot, Base, Базовый класс для всех ORM-моделей., TimestampMixin, BindRequestStatus, AuditLog, PaymentAttachment, WebSession (+27 more)

### Community 15 - "pending_updates.py"
Cohesion: 0.25
Nodes (15): PendingServerUpdate, PendingServerUpdateRepository, apply_pending_for_server(), apply_pending_update(), _apply_to_server(), _as_aware(), _clear_payment_error_if_complete(), enqueue_failed_servers() (+7 more)

### Community 16 - "test_whitelist_pg.py"
Cohesion: 0.08
Nodes (49): Пакет покупки трафика «Обход белых списков» (настраивается админом)., TrafficPackage, attach_proof(), Прикрепляет подтверждение оплаты (текст/фото/документ) к заявке., graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag) (+41 more)

### Community 17 - "test_payment_kind_conflict.py"
Cohesion: 0.26
Nodes (21): PlanCallback, Callback выбора тарифа пользователем. code — код тарифа из PLANS (1m/6m/12m)…, _open_count(), _package(), D-1: заявку с отправленной квитанцией нельзя превратить в заявку другого вида., _snapshot(), _subscription_with_proof(), test_conflicted_subscription_request_extends_once_and_adds_no_traffic() (+13 more)

### Community 18 - "main.go"
Cohesion: 0.07
Nodes (29): credentials, go_pkg_bytes, go_pkg_context, go_pkg_crypto_hmac, go_pkg_crypto_rand, go_pkg_crypto_sha256, go_pkg_crypto_subtle, go_pkg_crypto_tls (+21 more)

### Community 19 - "App.vue"
Cohesion: 0.07
Nodes (24): authTitles, awaiting, busy, code, comment, config, connection, days (+16 more)

### Community 20 - "config.py"
Cohesion: 0.11
Nodes (35): get_settings(), decrypt(), encrypt(), _fernet(), is_encrypted(), Возвращает Fernet, выведенный из SECRET_KEY, либо None если ключ не задан.…, Шифрует строку. Без SECRET_KEY возвращает значение как есть (dev/тесты)., Расшифровывает строку. Legacy-значения в открытом виде возвращает как есть. (+27 more)

### Community 21 - "main.py"
Cohesion: 0.09
Nodes (27): aiogram, aiogram_client_default, aiogram_fsm_storage_memory, aiogram_utils_token, build_root_router(), Настраивает логирование приложения. - корневой логгер: WARNING (чтобы сторонние…, setup_logging(), _anti_sharing_poller() (+19 more)

### Community 22 - "create_request"
Cohesion: 0.13
Nodes (19): create_request(), _new_payment_code(), PaymentRequestError, PendingRequestExists, Exception, Заявку нельзя создать по бизнес-правилам., У пользователя уже есть заявка с отправленной квитанцией., Создаёт заявку на продление и переводит её в ожидание проверки админом.… (+11 more)

### Community 23 - "utcnow"
Cohesion: 0.17
Nodes (38): IpObservation, _active_clients(), collect_all(), collect_for_client(), compute_status(), _level_for(), list_all_statuses(), list_flagged() (+30 more)

### Community 24 - "XuiClient"
Cohesion: 0.07
Nodes (36): Any, Exception, Response, _quote_path_segment(), Авторизованный запрос: гарантирует login и при истёкшей сессии выполняет…, Берёт CSRF-токен с /csrf-token (3x-ui >= 3.2.x). На старых панелях endpoint…, Базовая ошибка взаимодействия с панелью 3x-ui., Возвращает список inbound'ов панели с их БД-id, портами и протоколами. (+28 more)

### Community 25 - "Settings"
Cohesion: 0.09
Nodes (29): confirm_bind_cmd(), on_bind_action(), provision_user(), callback_query, notify_admins_bind_failed(), notify_admins_new_bind_request(), notify_user_bind_approved(), notify_user_bind_rejected() (+21 more)

### Community 26 - "FakeState"
Cohesion: 0.15
Nodes (10): Пользовательский раздел «Обход белых списков». action: home | refresh | buy…, WhitelistCallback, FakeState, Any, test_expired_user_gets_clear_explanation(), test_outage_payment_is_shown_as_awaiting_and_admin_resolves(), user_screen(), test_user_sees_balances_and_buys_package() (+2 more)

### Community 27 - "operation_lock.py"
Cohesion: 0.11
Nodes (16): app_db, do_run_migrations(), run_migrations_online(), BroadcastResult, Рассылает текстовое сообщение всем пользователям. Сообщение отправляется…, send_broadcast(), Serialize access mutations per user, including commits and panel calls., asyncio (+8 more)

### Community 28 - "middlewares.py"
Cohesion: 0.16
Nodes (20): aiogram_types, _command_name(), DbSessionMiddleware, _describe_callback(), _describe_event(), _describe_message(), Any, CallbackQuery (+12 more)

### Community 29 - "Protocol"
Cohesion: 0.07
Nodes (42): Protocol, build_client_object(), client_identifier(), _client_uuid_for_api(), _looks_like_db_id(), merge_client_record_for_update(), pick_panel_client_secret(), Any (+34 more)

### Community 30 - "reconcile_cycle"
Cohesion: 0.17
Nodes (12): _BatchResult, _finish_reconcile(), Итог обхода учётов (накапливается между запусками, если обход прерывали).…, Следующая пачка учётов: стабильный курсор по id, а не по изменяемой метке., Читает пачку одной сессией панели и сверяет учёты по одному. Сбой одного учёта…, Один повторный проход по учётам, изменившимся между чтением и сверкой., Полный обход учётов whitelist-сервера ограниченными пачками. Пачки берутся по…, _reconcile_batch() (+4 more)

### Community 31 - "User"
Cohesion: 0.16
Nodes (9): notify_admins_new_request(), User, _expiry_notify_poller(), Фоновая рассылка уведомлений об окончании подписки (день/час/в момент)., Bot, Обработчики бота с сессией на каждое обновление, как у middleware., Пользователь создаёт заявку на подписку и присылает квитанцию., Сдвиг срока в БД вместо ожидания реального окончания (минуты, а не дни). (+1 more)

### Community 32 - "Контекст проекта"
Cohesion: 0.13
Nodes (14): Архитектура, Безопасность аутентификации (backend/main.go), Важные инженерные правила, Доменная модель (таблицы веб-части, в БД бота), Запуск, Контекст проекта, Конфигурация, Локальные артефакты (+6 more)

### Community 33 - "whitelist_e2e.py"
Cohesion: 0.16
Nodes (17): asyncpg, _disabled(), gb(), link_for(), load_env(), main(), ms(), _package() (+9 more)

### Community 34 - "PaymentStatus"
Cohesion: 0.29
Nodes (17): PaymentStatus, _make_waiting_payment(), AsyncSession, test_compute_new_expiry_active(), test_compute_new_expiry_expired(), test_compute_new_expiry_none(), test_confirm_applies_available_servers_and_queues_unavailable(), test_confirm_no_client_marks_failed() (+9 more)

### Community 35 - "web_bridge.py"
Cohesion: 0.10
Nodes (36): aiohttp, Durable per-admin Telegram delivery, retried independently of HTTP requests., WebAccount, WebDelivery, WebLinkRequest, decide_link(), delivery_loop(), has_purchase() (+28 more)

### Community 36 - "bind_existing_client"
Cohesion: 0.17
Nodes (16): bind_existing_client(), find_client_presence_on_servers(), find_panel_client(), _find_panel_client_by_sub_id(), _panel_client_secret(), PanelClientInfo, _pick_secret(), Нормализованные данные существующего клиента панели. (+8 more)

### Community 37 - "XuiPanelUpdater"
Cohesion: 0.12
Nodes (37): ProvisionInbound, QuotaTarget, Создаёт/обновляет клиента с квотой и проверяет результат чтением., Inbound сервера, к которому нужно привязать клиента., Один клиент панели (глобальный по email), привязанный к её inbound'ам.…, Абсолютное целевое состояние клиента с учётом трафика. ``total_bytes`` —…, ServerProvision, Реализация PanelUpdater поверх XuiClient. На каждый сервер создаётся отдельный… (+29 more)

### Community 38 - "Server"
Cohesion: 0.06
Nodes (30): ClientServerMapping, Server, Включённые серверы. По умолчанию — только обычные (безлимитные)., Цели обычного provisioning: whitelist-сервер ведётся отдельно., MockIpProvider, Mock-провайдер для тестов: возвращает заранее заданные IP по server_id., Реальный провайдер: берёт IP клиента из журнала панели 3x-ui., XuiIpProvider (+22 more)

### Community 39 - "Panel"
Cohesion: 0.14
Nodes (7): admin_servers(), Panel, Прямой доступ к тестовой панели — для проверок и действий «вручную в панели»., Разрешает трафик к частной подсети стенда — только на тестовых панелях.…, VLESS + REALITY (TCP), как у рабочих серверов; цель — локальный TLS 1.3., {'body': тело клиента, 'inboundIds': [...], 'traffic': client_traffics|None}., Изменение клиента «вручную в панели» (тот же API, что у веб-интерфейса).

### Community 40 - "package.json"
Cohesion: 0.12
Nodes (16): lucide-vue-next, typescript, vite, @vitejs/plugin-vue, vue-tsc, dependencies, lucide-vue-next, vue (+8 more)

### Community 41 - "subhub_quota_e2e.py"
Cohesion: 0.12
Nodes (22): argparse, import_control_inbound(), main(), panel_view(), Any, Path, Квота трафика 3x-ui → SubHub на реальной панели, без маскирующего…, Расход, не менявшийся между двумя чтениями с интервалом 12 с. (+14 more)

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
Cohesion: 0.14
Nodes (13): Админские команды, Антишеринг, Доменная модель, Интеграция с 3x-ui, Контекст проекта, Конфигурация, Локальные артефакты, Назначение (+5 more)

### Community 46 - ".auth"
Cohesion: 0.53
Nodes (6): net/http.Request, net/http.ResponseWriter, decode(), digest(), fail(), respond()

### Community 47 - "select_plan"
Cohesion: 0.30
Nodes (12): ProofStates, _edit(), callback_query, CallbackQuery, Редактирует текущее сообщение (без спама в чат). При сбое — отправляет новое., Прежняя заявка с квитанцией на проверке: новой не создаём, квитанций не ждём., _refuse_pending_request(), select_plan() (+4 more)

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
Cohesion: 0.14
Nodes (13): Telegram VPN Billing Bot, Админ-команды, Антишеринг-мониторинг, Возможности, Граф кода (graphify), Единая подписка SubHub, Конфигурация, Логика продления (+5 more)

### Community 52 - "web_preview.mjs"
Cohesion: 0.29
Nodes (6): ref_node_fs, ref_node_http, ref_node_path, ref_node_url, root, types

### Community 53 - "test_whitelist_inbound_compat.py"
Cohesion: 0.16
Nodes (34): build_provision_spec(), get_active_server(), Включённый whitelist-сервер (не более одного по уникальному индексу)., server_ready(), target_inbound(), cryptography_hazmat_primitives, cryptography_hazmat_primitives_asymmetric_x25519, 3.4. Сервер, импорт, выдача, администрирование (+26 more)

### Community 54 - "AsyncSession"
Cohesion: 0.12
Nodes (39): Единственная строка настроек услуги (id = 1)., WhitelistConfig, access_state(), classify_origin(), confirm_traffic_payment(), _consistent_anchor(), _Context, ensure_defaults() (+31 more)

### Community 55 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 56 - "test_security.py"
Cohesion: 0.05
Nodes (53): aiogram_filters, IsAdmin, TelegramObject, Пропускает событие только если пользователь — администратор., forward_proof_to_admins(), Приветствие. Использует HTML-разметку: ID завёрнут в <code> — Telegram копирует…, welcome(), UserRole (+45 more)

### Community 57 - "PanelUpdater"
Cohesion: 0.09
Nodes (34): Any, AsyncSession, Записывает событие в audit_logs., record(), PanelUpdater, Интерфейс работы с клиентом в панели. Реализуется как mock (для тестов/MVP) и…, after_access_change(), get_account() (+26 more)

### Community 58 - "UserRepository"
Cohesion: 0.09
Nodes (24): Удаляет пользователя и связанные записи (каскад в ORM)., Telegram ID всех пользователей, когда-либо запускавших бота., Генерирует короткий уникальный публичный ID пользователя., UserRepository, AsyncSession, test_all_telegram_ids_returns_every_user(), AsyncSession, Регресс: сервер добавлен, но inbound'ы не импортированы. Ранее триал отвечал… (+16 more)

### Community 59 - "onboard_legacy_link"
Cohesion: 0.22
Nodes (10): bind_request_received(), onboarding_invalid_link(), onboard_legacy_link(), _is_valid_public_id(), parse_subhub_subscription_token(), parse_subscription_public_id(), Извлекает ID подписки из последнего сегмента URL. Примеры: -…, Extract a secret token only from a SubHub /connection[/raw]/ URL. (+2 more)

### Community 60 - "whitelist_migration_check.py"
Cohesion: 0.27
Nodes (19): alembic(), check(), docker(), downgrade_cycle(), dsn(), ensure_defaults_idempotent(), main(), plain() (+11 more)

### Community 61 - "sync_inventory"
Cohesion: 0.11
Nodes (28): choose_inbound(), check_inbound(), _check_vless_reality(), describe(), _foreign_flows(), InboundCompat, _json(), _public_key_available() (+20 more)

### Community 63 - "D VPN — личный кабинет"
Cohesion: 0.25
Nodes (7): D VPN — личный кабинет, Архитектура, Запуск вместе с существующим ботом, Локальная разработка, Результаты проверки, Что реализовано, Эксплуатация

### Community 64 - "admin_nav"
Cohesion: 0.08
Nodes (32): admin_nav(), _edit_panel(), _finalize_whitelist_server(), CallbackQuery, InlineKeyboardMarkup, Добавляет сервер услуги и сразу сверяет его inbound'ы. До успешной сверки с…, Редактирует сообщение админ-панели, мягко гасит ошибки. parse_mode=None —…, sharing_report() (+24 more)

### Community 65 - "ServerInbound"
Cohesion: 0.20
Nodes (11): Inbound на панели сервера, в который нужно заводить клиентов. На одном сервере…, ServerInbound, test_ensure_inbounds_imported_imports_when_missing(), fake_import(), test_pending_reconciles_memberships_and_never_shortens_newer_expiry(), provision_server(), test_provisioning_carries_telegram_identity(), provision_server() (+3 more)

### Community 66 - "test_plans.py"
Cohesion: 0.19
Nodes (9): get_plan(), PaymentPlan, Выгода относительно помесячной оплаты за тот же срок., AsyncSession, test_changing_plan_updates_open_request(), test_create_request_with_plan(), test_get_plan(), test_plan_amounts_are_fixed_server_side() (+1 more)

### Community 67 - "texts.py"
Cohesion: 0.05
Nodes (80): _after_applied_payment(), on_payment_action(), Уведомления и SubHub после применения; возвращает итог для администратора.…, HTML-строка с анимированным значком для вставки в текст сообщения., tg(), notify_admins_failed(), notify_first_purchase_channel(), notify_user_extended() (+72 more)

### Community 71 - "fmt_gb"
Cohesion: 0.21
Nodes (14): _parse_gb(), fmt_gb(), Остаток или расход в ГБ (1 ГБ = 1024³ байт), округлённый вниз: лишнего не…, whitelist_package_title(), gib_to_bytes(), Заданный объём в ГБ (без единицы, точка): так, как он вводился. Байты при вводе…, set_volume_gib_text(), 12. Исправление D-4 (результаты от 2026-10-05, после приёмки) (+6 more)

### Community 72 - "MenuCallback"
Cohesion: 0.20
Nodes (18): MenuCallback, Навигация по inline-меню (редактирование сообщения на месте). action: home |…, custom_emoji_id(), Возвращает custom_emoji_id значка или None, если значок не найден., cancel_payment_keyboard(), Главное меню под приветствием. Зависит от наличия активной подписки., Кнопка «Отмена» под заявкой на оплату — удаляет заявку., welcome_menu() (+10 more)

### Community 73 - "Настройка серверов и авто-провижининг"
Cohesion: 0.33
Nodes (6): Как формируется клиент, Настройка серверов и авто-провижининг, Перенос пользователей, существовавших до бота, Шаг 1. Добавить серверы, Шаг 2. Импортировать inbound'ы каждого сервера, hysteria()

### Community 74 - "VpnClient"
Cohesion: 0.34
Nodes (16): _is_active(), VpnClient, has_active_timed_client(), has_client_access(), has_unlimited_bound_client(), resolve_effective_role(), _mapping(), test_access_rejects_missing_client() (+8 more)

### Community 75 - "test_all_inline_buttons_have_color_style"
Cohesion: 0.13
Nodes (21): aiogram_filters_callback_data, AdminCallback, BindCallback, OnboardCallback, PaymentCallback, Callback админских действий над заявкой на привязку подписки., Онбординг: был ли пользователь клиентом до внедрения бота., Навигация по админ-панели (/admin). action: home | servers | server | rename |… (+13 more)

### Community 76 - "FakeBot"
Cohesion: 0.15
Nodes (10): Запуск, 2. Стенд, async_sessionmaker, Запуск через Docker Compose, FakeBot, Any, test_reject_then_notify_user(), test_expiry_after_downtime_sends_only_current_notice() (+2 more)

### Community 78 - "Услуга «Обход белых списков» — реализация и порядок внедрения"
Cohesion: 0.29
Nodes (5): 1. Что получает пользователь, 2. Проверенный контракт 3x-ui, 6. Порядок внедрения, 7. Откат, Услуга «Обход белых списков» — реализация и порядок внедрения

### Community 79 - "connection_overview"
Cohesion: 0.33
Nodes (6): connection_overview(), Unified SubHub connection screen with live server availability., server_button_label(), Флаг не добавляется автоматически — он уже в названии сервера., test_connection_overview_shows_server_availability(), test_server_button_label_has_no_autoflag()

### Community 80 - "SubHub"
Cohesion: 0.18
Nodes (4): Any, Полная синхронизация с ожиданием её завершения., Report, SubHub

### Community 81 - "EncryptedString"
Cohesion: 0.25
Nodes (7): EncryptedString, Any, Прозрачно шифрует значение при записи и расшифровывает при чтении. - Если…, Важные инженерные правила проекта, P1 — пароли панелей не защищены шифрованием приложения, 5. Миграции и резервная копия (PostgreSQL 16.15), TypeDecorator

### Community 82 - "_FakeMessage"
Cohesion: 0.40
Nodes (3): _FakeBot, _FakeMessage, Any

### Community 84 - "api.ts"
Cohesion: 0.33
Nodes (4): APIError, Configuration, Plan, Profile

### Community 85 - "_parse_server_line"
Cohesion: 0.22
Nodes (9): _parse_server_line(), Парсит 'name|country|panel_url|username|password|[kind]|[sub]|[purpose]'.…, parametrize, test_parse_server_line_accepts_valid(), test_parse_server_line_rejects_invalid(), test_settings_rejects_dangerous_numeric_values(), test_validate_server_name_rejects_invalid(), test_validate_subscription_base_rejects_invalid() (+1 more)

### Community 86 - "Обновление production — 4 октября 2026"
Cohesion: 0.25
Nodes (6): PAY-1C3F1344, Внедрено, Дополнительный дефект, обнаруженный при приёмке, Незавершённые операции, Обновление production — 4 октября 2026, Проверки и резервирование

### Community 87 - "Ревью VpnBot — 4 октября 2026"
Cohesion: 0.25
Nodes (8): Исправления в рабочем дереве, Объём и доказательства, Порядок применения в production, Проверки, Разбор PAY-1C3F1344, Ревью VpnBot — 4 октября 2026, Результат, Устройство production

### Community 88 - "Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026"
Cohesion: 0.50
Nodes (3): Прогон до исправления (SubHub `d9a2c80` + незакоммиченные правки, не относящиеся к задаче), Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026, Финальный прогон после исправления

### Community 89 - "Приёмка услуги «Обход белых списков» — 5 октября 2026"
Cohesion: 0.22
Nodes (8): 10. Заключение, 14. Исправление D-2: SubHub собирается без ручной установки greenlet (результаты от 2026-10-05, после приёмки), 15. Лимит трафика 3x-ui → SubHub: единица `totalGB` и источник расхода (результаты от 2026-10-05, после приёмки), 1. Итог, 6. Реальные 3x-ui и SubHub, 7. Happ — не выполнено, 9. Что не проверялось, Приёмка услуги «Обход белых списков» — 5 октября 2026

### Community 94 - "VpnClientRepository"
Cohesion: 0.09
Nodes (29): datetime, Клиенты, которым пора слать уведомление об окончании. Берём тех, у кого задан…, _utcnow(), VpnClientRepository, _as_aware(), process_expiry_notifications(), AsyncSession, datetime (+21 more)

### Community 95 - "Q: собери контекст проекта"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: собери контекст проекта, Source Nodes

### Community 96 - "Оставшиеся риски и решения"
Cohesion: 0.29
Nodes (7): P1/P2 — частичный успех внешней операции требует сверки, P1 — административные права зависят от тарифа, P1 — биллинг и панели не образуют одну транзакцию, P2 — мониторинг и производительность, P2 — старые ошибки оплат без ожидающих задач, P2 — эксплуатация и воспроизводимость, Оставшиеся риски и решения

### Community 97 - "subscriptions.py"
Cohesion: 0.50
Nodes (4): collect_links(), AsyncSession, Возвращает список (метка, ссылка-подписка) по всем серверам пользователя. Для…, _sub_link()

### Community 98 - "answer_callback"
Cohesion: 0.16
Nodes (16): aiogram_exceptions, aiogram_methods, answer(), answer_callback(), edit(), Any, CallbackQuery, Безопасно редактирует сообщение callback'а. ``callback.message`` может быть… (+8 more)

### Community 99 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 100 - "conftest.py"
Cohesion: 0.47
Nodes (8): pytest_asyncio, admin(), AsyncSession, datetime, fixture, server(), user(), vpn_client()

### Community 102 - "check_server"
Cohesion: 0.17
Nodes (5): check_server(), Проверяет доступность панели 3x-ui одного сервера. Успешный login считается…, test_health_check_server_returns_false_on_error(), login(), test_health_check_server_returns_true_on_success()

### Community 103 - "devDependencies"
Cohesion: 0.40
Nodes (5): devDependencies, typescript, vite, @vitejs/plugin-vue, vue-tsc

### Community 108 - "test_ux.py"
Cohesion: 0.10
Nodes (26): connection_keyboard(), One stable SubHub subscription link for every location and protocol., country_flag(), purchase_info(), Эмодзи-флаг по ISO2-коду страны (напр. 'SE' -> 🇸🇪). Иначе пусто., Экран «Оформить подписку»: цены и правила. parse_mode='HTML'., Пробный доступен, если им не пользовались и подписку никогда не оформляли., _trial_available() (+18 more)

### Community 109 - "stack.sh"
Cohesion: 0.70
Nodes (3): running(), stack.sh script, start_panel()

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
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 120 - "check_servers"
Cohesion: 0.50
Nodes (4): check_servers(), AsyncSession, Проверяет все серверы и сохраняет результат в БД. Возвращает отображение…, Фоновые задачи

## Knowledge Gaps
- **174 isolated node(s):** `credentials`, `dvpn/site`, `name`, `version`, `private` (+169 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 822 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `provisioning.py`, `test_provisioning.py`, `whitelist.py`, `test_legacy_bind.py`, `MockPanelUpdater`, `user_handlers.py`, `admin_handlers.py`, `test_whitelist_reconcile.py`, `PaymentRequest`, `menu_nav`, `models.py`, `pending_updates.py`, `test_whitelist_pg.py`, `config.py`, `create_request`, `utcnow`, `Settings`, `operation_lock.py`, `whitelist_e2e.py`, `PaymentStatus`, `web_bridge.py`, `bind_existing_client`, `select_plan`, `AsyncSession`, `test_security.py`, `UserRepository`, `onboard_legacy_link`, `admin_nav`, `test_plans.py`, `texts.py`, `VpnClient`, `FakeBot`, `VpnClientRepository`, `conftest.py`, `test_ux.py`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Why does `Server` connect `Server` to `provisioning.py`, `test_provisioning.py`, `whitelist.py`, `test_legacy_bind.py`, `MockPanelUpdater`, `admin_handlers.py`, `import_inbounds`, `keyboards.py`, `test_whitelist_reconcile.py`, `models.py`, `pending_updates.py`, `test_whitelist_pg.py`, `config.py`, `utcnow`, `Protocol`, `reconcile_cycle`, `PaymentStatus`, `web_bridge.py`, `bind_existing_client`, `XuiPanelUpdater`, `Контекст проекта`, `test_whitelist_inbound_compat.py`, `AsyncSession`, `What You Must Do When Invoked`, `PanelUpdater`, `UserRepository`, `sync_inventory`, `admin_nav`, `ServerInbound`, `texts.py`, `test_all_inline_buttons_have_color_style`, `connection_overview`, `EncryptedString`, `_parse_server_line`, `VpnClientRepository`, `conftest.py`, `check_server`, `test_ux.py`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **Why does `VpnClient` connect `VpnClient` to `provisioning.py`, `whitelist.py`, `MockPanelUpdater`, `user_handlers.py`, `admin_handlers.py`, `PaymentRequest`, `models.py`, `pending_updates.py`, `test_whitelist_pg.py`, `config.py`, `utcnow`, `Settings`, `operation_lock.py`, `User`, `whitelist_e2e.py`, `PaymentStatus`, `web_bridge.py`, `AsyncSession`, `test_security.py`, `PanelUpdater`, `UserRepository`, `texts.py`, `VpnClientRepository`, `subscriptions.py`, `conftest.py`, `test_ux.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 166 inferred relationships involving `User` (e.g. with `admin_add_server_line()` and `admin_broadcast_send()`) actually correct?**
  _`User` has 166 INFERRED edges - model-reasoned connections that need verification._
- **Are the 90 inferred relationships involving `VpnClient` (e.g. with `notify_user_extended()` and `access_extended()`) actually correct?**
  _`VpnClient` has 90 INFERRED edges - model-reasoned connections that need verification._
- **Are the 52 inferred relationships involving `Server` (e.g. with `_finalize_new_server()` and `_finalize_whitelist_server()`) actually correct?**
  _`Server` has 52 INFERRED edges - model-reasoned connections that need verification._
- **Are the 57 inferred relationships involving `Settings` (e.g. with `add_server()` and `admin_add_server_line()`) actually correct?**
  _`Settings` has 57 INFERRED edges - model-reasoned connections that need verification._
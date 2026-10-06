# Graph Report - VpnBot  (2026-10-06)

## Corpus Check
- 162 files · ~162,032 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 9, .example 3, .conf 1)

## Summary
- 2873 nodes · 10175 edges · 131 communities (110 shown, 21 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1332 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `abeb5aaa`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- XuiClient
- test_provisioning.py
- whitelist.py
- test_legacy_bind.py
- test_whitelist.py
- menu_nav
- admin_handlers.py
- ServerInbound
- keyboards.py
- test_whitelist_reconcile.py
- billing.py
- LocalSubHub
- _whitelist_reconcile_poller
- test_expiry.py
- sqlalchemy
- PendingServerUpdate
- test_whitelist_pg.py
- test_payment_kind_conflict.py
- main.go
- App.vue
- test_crypto.py
- whitelist_e2e.py
- PaymentRequest
- utcnow
- ._api
- Settings
- test_all_inline_buttons_have_color_style
- broadcast.py
- _describe_event
- Protocol
- xui_traffic_d3.py
- User
- Контекст проекта
- Server
- VpnClientRepository
- Base
- test_whitelist_queue_worker.py
- XuiPanelUpdater
- _all_buttons
- MockPanelUpdater
- package.json
- scenario
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
- test_whitelist_inbound_compat.py
- test_whitelist_epoch.py
- What You Must Do When Invoked
- test_security.py
- run_rollout
- UserRepository
- PanelUpdateError
- whitelist_migration_check.py
- Telegram VPN Billing Bot
- Report
- D VPN — личный кабинет
- texts.py
- XuiError
- session
- Приёмка услуги «Обход белых списков» — 5 октября 2026
- dvpn/site
- telegram-vpn-billing-bot
- FakeCallback
- test_health_poller_triggers_subhub_after_recovering_payment
- MenuCallback
- VpnClient
- panel_call
- 4. Точки интеграции
- on_bind_action
- _phases
- purchase_plans_keyboard
- admin_server_detail
- pg
- _FakeMessage
- AGENTS.md
- api.ts
- .set_status
- subscriptions.py
- PaymentCallback
- Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026
- XuiAuthError
- reconcile_cycle
- resolve_uncertain
- Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026
- provisioning.py
- active_user
- Q: собери контекст проекта
- check_servers
- models.py
- SubHubClient
- graphify reference: query, path, explain
- conftest.py
- whitelist_admin
- admin_nav
- _PoisonedPanel
- TelegramMock
- whitelist_e2e_2026-10-05.md
- vue
- .list_inbounds
- test_ux.py
- stack.sh
- whitelist_migration_2026-10-05.md
- scripts
- test_xui_client.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- ref_node_fs
- admin_servers_keyboard
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- test_ui.py
- install_guides_keyboard
- extraction-spec.md
- .delete
- .panel_changes
- _server_health_poller
- sh

## God Nodes (most connected - your core abstractions)
1. `User` - 268 edges
2. `VpnClient` - 148 edges
3. `MockPanelUpdater` - 138 edges
4. `Settings` - 137 edges
5. `Server` - 137 edges
6. `PaymentRequest` - 110 edges
7. `PaymentStatus` - 97 edges
8. `VpnClientRepository` - 86 edges
9. `XuiClient` - 80 edges
10. `Bot` - 69 edges

## Surprising Connections (you probably didn't know these)
- `6. Реальные 3x-ui и SubHub` --references--> `recover_confirmed_payments()`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → app/services/billing.py
- `Как формируется клиент` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py
- `16. R46 без принудительной синхронизации и фоновые циклы бота (результаты от 2026-10-05, после приёмки)` --references--> `_after_applied_payment()`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → app/bot/admin_handlers.py
- `3.2. Купленный трафик` --references--> `on_payment_action()`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → app/bot/admin_handlers.py
- `3.4. Сервер, импорт, выдача, администрирование` --references--> `IsAdmin`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → app/bot/filters.py

## Import Cycles
- None detected.

## Communities (131 total, 21 thin omitted)

### Community 0 - "XuiClient"
Cohesion: 0.10
Nodes (14): Идентификатор для updateClient/{id}: id для vless/vmess, иначе email., Изолированный REST-клиент панели 3x-ui (MHSanaei/3x-ui). Принципы: - одна…, Обновляет клиента, сохраняя все его поля и меняя только нужные. Возвращает…, Устанавливает expiryTime (мс) и включает клиента., Лимит уникальных IP (0 = без лимита). Не считать точным лимитом устройств., Совместимый метод: продление через read-modify-write., Определяет, есть ли у панели новый client-API /panel/api/clients. В 3x-ui 3.2.x…, Возвращает список IP-адресов клиента из журнала 3x-ui (iplimit log). Требует… (+6 more)

### Community 1 - "test_provisioning.py"
Cohesion: 0.14
Nodes (28): MappingRepository, ensure_vpn_client(), Клиент найден на конкретном сервере., Возвращает VPN-клиента пользователя, создавая его при отсутствии., ServerClientPresence, days_from_now(), _panel_info(), AsyncSession (+20 more)

### Community 2 - "whitelist.py"
Cohesion: 0.06
Nodes (99): Бизнес-учёт трафика пользователя на whitelist-сервере. Остатки…, Журнал выдач/начислений/корректировок, привязанных к исходной операции. Выдача…, WhitelistAccount, WhitelistLedger, PanelUpdater, QuotaClientState, Интерфейс работы с клиентом в панели. Реализуется как mock (для тестов/MVP) и…, Читает клиента и его счётчик трафика (None — клиента нет). (+91 more)

### Community 3 - "test_legacy_bind.py"
Cohesion: 0.07
Nodes (45): notify_admins_new_bind_request(), bind_request_received(), onboarding_invalid_link(), onboard_legacy_link(), BindRequest, Заявка на привязку существующей подписки (до внедрения бота)., BindRequestRepository, Меняет только имя, сохраняя сервер и все его связи. (+37 more)

### Community 4 - "test_whitelist.py"
Cohesion: 0.09
Nodes (70): create_traffic_request(), datetime, Заявка на покупку пакета «Обход белых списков». Создаётся только при активной…, AwaitingCredit, list_open_events(), Сохранённое начисление, ещё не сверенное с расходом., Остатки пользователя; при доступной панели — с актуальной сверкой. Чтение…, Неприменённые события учёта пользователя в порядке возникновения. (+62 more)

### Community 5 - "menu_nav"
Cohesion: 0.10
Nodes (43): admin_panel_home(), bind_request_waiting(), free_proxies_intro(), install_guides_intro(), news_channel_prompt(), no_open_request(), onboarding_legacy_question(), onboarding_send_link_prompt() (+35 more)

### Community 6 - "admin_handlers.py"
Cohesion: 0.13
Nodes (55): aiogram_fsm_context, add_inbound(), add_server(), admin_add_server_cancel(), admin_add_server_line(), admin_broadcast_cancel(), admin_broadcast_send(), admin_delete_subscription_by_client_id() (+47 more)

### Community 7 - "ServerInbound"
Cohesion: 0.09
Nodes (25): Inbound на панели сервера, в который нужно заводить клиентов. На одном сервере…, ServerInbound, ensure_inbounds_imported(), fetch_inbounds(), import_inbounds(), Any, Сверяет inbound'ы панели с локальными целями провижининга. Удалённые и…, Читает список inbound'ов панели (``inbounds/list``) как есть. (+17 more)

### Community 8 - "keyboards.py"
Cohesion: 0.17
Nodes (32): _adm(), admin_add_server_type_keyboard(), admin_back_keyboard(), admin_confirm_delete_keyboard(), admin_payment_keyboard(), admin_retry_keyboard(), admin_whitelist_back_keyboard(), admin_whitelist_keyboard() (+24 more)

### Community 9 - "test_whitelist_reconcile.py"
Cohesion: 0.06
Nodes (63): _fmt_span(), Состояние фоновой сверки расхода для админ-раздела (по данным процесса). «Обход…, _reconcile_gaps(), reconcile_status_lines(), Состояние и наблюдаемость фоновой сверки (хранится в памяти процесса).…, Сколько прошло с завершения последнего обхода (в т. ч. с пропусками)., Верхняя граница возраста данных *сверенных* учётов последнего обхода., Сколько прошло с завершения последнего полностью подтверждённого обхода. (+55 more)

### Community 10 - "billing.py"
Cohesion: 0.09
Nodes (56): Any, AsyncSession, Записывает событие в audit_logs., record(), _apply_panels(), _as_aware(), BillingError, BillingResult (+48 more)

### Community 11 - "LocalSubHub"
Cohesion: 0.20
Nodes (12): StreamReader, StreamWriter, _command(), LocalSubHub, _paid(), HTTP-сервер вместо SubHub: ``accept`` — 202 и запись, ``drop`` — разрыв без…, _settings(), test_balance_adjustment_applied_on_panel_triggers_subhub() (+4 more)

### Community 12 - "_whitelist_reconcile_poller"
Cohesion: 0.09
Nodes (18): Фоновая сверка расхода whitelist-услуги: полный обход пачками. Работает…, _whitelist_reconcile_poller(), decorate(), wrapped(), user_operation(), next_reconcile_delay(), Каждый существующий учёт сверен: ни ошибок, ни пропусков., Пауза до следующего запуска обхода. Прерванный обход (панель недоступна)… (+10 more)

### Community 13 - "test_expiry.py"
Cohesion: 0.15
Nodes (19): notify_user_expiry(), Уведомление пользователя об окончании подписки. True — если доставлено., _as_aware(), process_expiry_notifications(), AsyncSession, datetime, Стадия уведомления по остатку времени до окончания. 0 — рано, 1 — остался день,…, Шлёт уведомления «за день / за час / в момент окончания». Каждая стадия… (+11 more)

### Community 14 - "sqlalchemy"
Cohesion: 0.06
Nodes (3): alembic, collections_abc, sqlalchemy

### Community 15 - "PendingServerUpdate"
Cohesion: 0.14
Nodes (16): PendingServerUpdate, PendingServerUpdateRepository, AsyncSession, apply_pending_for_server(), apply_pending_update(), _apply_to_server(), _as_aware(), _clear_payment_error_if_complete() (+8 more)

### Community 16 - "test_whitelist_pg.py"
Cohesion: 0.10
Nodes (27): AttachmentType, Пакет покупки трафика «Обход белых списков» (настраивается админом)., TrafficPackage, attach_proof(), Прикрепляет подтверждение оплаты (текст/фото/документ) к заявке., 4. Автоматические тесты, _package(), _ledger() (+19 more)

### Community 17 - "test_payment_kind_conflict.py"
Cohesion: 0.24
Nodes (21): PlanCallback, Callback выбора тарифа пользователем. code — код тарифа из PLANS (1m/6m/12m)…, ProofStates, _open_count(), _package(), D-1: заявку с отправленной квитанцией нельзя превратить в заявку другого вида., _snapshot(), _subscription_with_proof() (+13 more)

### Community 18 - "main.go"
Cohesion: 0.07
Nodes (29): credentials, go_pkg_bytes, go_pkg_context, go_pkg_crypto_hmac, go_pkg_crypto_rand, go_pkg_crypto_sha256, go_pkg_crypto_subtle, go_pkg_crypto_tls (+21 more)

### Community 19 - "App.vue"
Cohesion: 0.07
Nodes (24): authTitles, awaiting, busy, code, comment, config, connection, days (+16 more)

### Community 20 - "test_crypto.py"
Cohesion: 0.13
Nodes (24): decrypt(), encrypt(), _fernet(), is_encrypted(), Возвращает Fernet, выведенный из SECRET_KEY, либо None если ключ не задан.…, Шифрует строку. Без SECRET_KEY возвращает значение как есть (dev/тесты)., Расшифровывает строку. Legacy-значения в открытом виде возвращает как есть., cryptography_fernet (+16 more)

### Community 21 - "whitelist_e2e.py"
Cohesion: 0.06
Nodes (64): aiogram, aiogram_client_default, aiogram_fsm_storage_memory, aiogram_types, aiogram_utils_token, aiohttp, build_root_router(), get_settings() (+56 more)

### Community 22 - "PaymentRequest"
Cohesion: 0.06
Nodes (49): PaymentStatus, PaymentAttachment, PaymentRequest, PaymentRepository, Берёт заявку с блокировкой строки (SELECT ... FOR UPDATE). На Postgres…, Число применённых оплат подписки (покупки трафика не учитываются)., Удаляет заявку (вместе с вложениями по каскаду)., Последняя успешная (применённая/подтверждённая) оплата пользователя.… (+41 more)

### Community 23 - "utcnow"
Cohesion: 0.17
Nodes (38): IpObservation, _active_clients(), collect_all(), collect_for_client(), compute_status(), _level_for(), list_all_statuses(), list_flagged() (+30 more)

### Community 24 - "._api"
Cohesion: 0.11
Nodes (17): Any, Response, _quote_path_segment(), Авторизованный запрос: гарантирует login и при истёкшей сессии выполняет…, Берёт CSRF-токен с /csrf-token (3x-ui >= 3.2.x). На старых панелях endpoint…, Возвращает список inbound'ов панели с их БД-id, портами и протоколами., Ищет клиента в inbound по uuid, email или subId (стабильные ID)., Совместимый алиас find_client (по uuid/email). (+9 more)

### Community 25 - "Settings"
Cohesion: 0.08
Nodes (24): IsAdmin, TelegramObject, Пропускает событие только если пользователь — администратор., Разрешает задавать ADMIN_TELEGRAM_IDS как строку '1,2,3' или одно число., Конфигурация приложения из переменных окружения / .env., Убирает пробелы и обрамляющие кавычки вокруг токена., Settings, _anti_sharing_poller() (+16 more)

### Community 26 - "test_all_inline_buttons_have_color_style"
Cohesion: 0.17
Nodes (14): aiogram_filters_callback_data, AdminCallback, BindCallback, OnboardCallback, Callback админских действий над заявкой на привязку подписки., Онбординг: был ли пользователь клиентом до внедрения бота., Навигация по админ-панели (/admin). action: home | servers | server | rename |…, admin_bind_keyboard() (+6 more)

### Community 27 - "broadcast.py"
Cohesion: 0.28
Nodes (6): BroadcastResult, Рассылает текстовое сообщение всем пользователям. Сообщение отправляется…, send_broadcast(), FakeBot, test_send_broadcast_counts_sent_and_failed(), test_send_broadcast_empty_list()

### Community 28 - "_describe_event"
Cohesion: 0.24
Nodes (14): _command_name(), _describe_callback(), _describe_event(), _describe_message(), CallbackQuery, Message, Chat, _private_chat() (+6 more)

### Community 29 - "Protocol"
Cohesion: 0.09
Nodes (39): Protocol, ProvisionTarget, Описание клиента, которого нужно создать/обновить в конкретном inbound., build_client_object(), build_client_record(), client_identifier(), client_record_body(), _client_uuid_for_api() (+31 more)

### Community 30 - "xui_traffic_d3.py"
Cohesion: 0.18
Nodes (33): accounted(), add_client(), container_started(), delta(), _disable_case(), Lab, m1_planned_restart(), m2_disable_without_restart() (+25 more)

### Community 31 - "User"
Cohesion: 0.12
Nodes (16): notify_admins_new_request(), User, _expiry_notify_poller(), Фоновая рассылка уведомлений об окончании подписки (день/час/в момент)., Bot, async_sessionmaker, Обработчики бота с сессией на каждое обновление, как у middleware., Пользователь создаёт заявку на подписку и присылает квитанцию. (+8 more)

### Community 32 - "Контекст проекта"
Cohesion: 0.11
Nodes (17): Запуск, Запуск через Docker Compose, API, Архитектура, Безопасность аутентификации (backend/main.go), Важные инженерные правила, Доменная модель (таблицы веб-части, в БД бота), Запуск (+9 more)

### Community 33 - "Server"
Cohesion: 0.06
Nodes (21): connection_overview(), Unified SubHub connection screen with live server availability., server_button_label(), ClientServerMapping, Server, Включённые серверы. По умолчанию — только обычные (безлимитные)., Цели обычного provisioning: whitelist-сервер ведётся отдельно., MockIpProvider (+13 more)

### Community 34 - "VpnClientRepository"
Cohesion: 0.12
Nodes (28): VpnClientRepository, _delete_local_subscription(), delete_user_subscription(), AsyncSession, Удаляет VPN-подписку пользователя с панелей и из БД бота. История оплат, заявки…, SubscriptionDeleteResult, _make_waiting_payment(), AsyncSession (+20 more)

### Community 35 - "Base"
Cohesion: 0.17
Nodes (22): Base, Базовый класс для всех ORM-моделей., WebAccount, WebLinkRequest, WebSession, WebToken, decide_link(), link_callback() (+14 more)

### Community 36 - "test_whitelist_queue_worker.py"
Cohesion: 0.18
Nodes (29): _queue_worker_alive(), Запускает фоновые циклы процесса бота (кроме доставки сайта). Одна сборка для…, start_background_tasks(), stop_background_tasks(), Task, _expire(), _purchase_while_panel_down(), parametrize (+21 more)

### Community 37 - "XuiPanelUpdater"
Cohesion: 0.11
Nodes (38): ProvisionInbound, QuotaTarget, Создаёт/обновляет клиента с квотой и проверяет результат чтением., Inbound сервера, к которому нужно привязать клиента., Один клиент панели (глобальный по email), привязанный к её inbound'ам.…, Абсолютное целевое состояние клиента с учётом трафика. ``total_bytes`` —…, ServerProvision, Старые панели: отдельный клиент в каждом inbound (per-inbound email). (+30 more)

### Community 38 - "_all_buttons"
Cohesion: 0.14
Nodes (20): custom_emoji_id(), emoji_char(), Возвращает unicode-символ значка (без анимации)., Возвращает custom_emoji_id значка или None, если значок не найден., connection_keyboard(), free_proxies_keyboard(), Главное меню под приветствием. Зависит от наличия активной подписки., Бесплатные прокси Telegram — ссылки t.me/proxy и t.me/socks. (+12 more)

### Community 39 - "MockPanelUpdater"
Cohesion: 0.19
Nodes (24): admin_payment_card(), payment_status_label(), MockPanelUpdater, datetime, Mock-реализация: ничего не делает либо имитирует сбой нужных серверов. Для…, _down(), _fresh(), _is_waiting() (+16 more)

### Community 40 - "package.json"
Cohesion: 0.11
Nodes (17): lucide-vue-next, typescript, vite, @vitejs/plugin-vue, vue-tsc, dependencies, lucide-vue-next, vue (+9 more)

### Community 41 - "scenario"
Cohesion: 0.09
Nodes (27): import_control_inbound(), main(), panel_view(), Any, Path, Квота трафика 3x-ui → SubHub на реальной панели, без маскирующего…, Расход, не менявшийся между двумя чтениями с интервалом 12 с., Что SubHub получает из ``inbounds/list`` для клиента: settings и clientStats. (+19 more)

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
Cohesion: 0.05
Nodes (39): EncryptedString, Any, Прозрачно шифрует значение при записи и расшифровывает при чтении. - Если…, Админские команды, Антишеринг, Важные инженерные правила проекта, Интеграция с 3x-ui, Контекст проекта (+31 more)

### Community 46 - ".auth"
Cohesion: 0.53
Nodes (6): net/http.Request, net/http.ResponseWriter, decode(), digest(), fail(), respond()

### Community 47 - "Panel"
Cohesion: 0.12
Nodes (8): Panel, Прямой доступ к тестовой панели — для проверок и действий «вручную в панели»., Разрешает трафик к частной подсети стенда — только на тестовых панелях.…, VLESS + REALITY (TCP), как у рабочих серверов; цель — локальный TLS 1.3., {'body': тело клиента, 'inboundIds': [...], 'traffic': client_traffics|None}., Изменение клиента «вручную в панели» (тот же API, что у веб-интерфейса)., up+down из счётчиков самого Xray панели (statsquery), минуя учёт панели.…, Сколько секунд работает процесс Xray панели.

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
Cohesion: 0.14
Nodes (12): app_db, do_run_migrations(), run_migrations_online(), Serialize access mutations per user, including commits and panel calls., functools, inspect, check_released(), main() (+4 more)

### Community 52 - "web_preview.mjs"
Cohesion: 0.29
Nodes (6): ref_node_fs_promises, ref_node_http, ref_node_path, ref_node_url, root, types

### Community 53 - "test_whitelist_inbound_compat.py"
Cohesion: 0.05
Nodes (79): Админ-раздел услуги «Обход белых списков». action: home | sync | choose (value…, WhitelistAdminCallback, build_provision_spec(), choose_inbound(), check_inbound(), _check_vless_reality(), describe(), _foreign_flows() (+71 more)

### Community 54 - "test_whitelist_epoch.py"
Cohesion: 0.12
Nodes (36): process_due(), Применяет состояние учёта пользователя на whitelist-панели., Фоновая очередь: применяет несинхронизированные состояния с backoff., Фоновая сверка расхода: обходит все учёты пачками по ``limit``. Возвращает…, reconcile_usage(), sync_user(), _available(), parametrize (+28 more)

### Community 55 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 56 - "test_security.py"
Cohesion: 0.05
Nodes (54): forward_proof_to_admins(), admin_denied(), UserRole, FakeBot, FakeMessage, _make_payment(), _make_waiting(), _persist_payment() (+46 more)

### Community 57 - "run_rollout"
Cohesion: 0.15
Nodes (14): ensure_defaults(), get_config(), Decimal, Exception, Ошибка бизнес-правил услуги., Запускает услугу и выдаёт её нынешним активным пользователям. Повторный запуск…, Настройки услуги; строка с начальными значениями создаётся один раз., Идемпотентная инициализация: настройки и начальные пакеты. (+6 more)

### Community 58 - "UserRepository"
Cohesion: 0.08
Nodes (27): DbSessionMiddleware, Any, TelegramObject, Открывает сессию БД, получает/создаёт пользователя и кладёт их в data., Удаляет пользователя и связанные записи (каскад в ORM)., Telegram ID всех пользователей, когда-либо запускавших бота., Генерирует короткий уникальный публичный ID пользователя., UserRepository (+19 more)

### Community 59 - "PanelUpdateError"
Cohesion: 0.13
Nodes (17): PanelUpdateError, Exception, Ошибка обновления клиента в панели., find_panel_client(), _find_panel_client_by_sub_id(), list_panel_clients(), _panel_client_secret(), PanelClientInfo (+9 more)

### Community 60 - "whitelist_migration_check.py"
Cohesion: 0.22
Nodes (22): Единственная строка настроек услуги (id = 1)., WhitelistConfig, hashlib, alembic(), check(), docker(), downgrade_cycle(), dsn() (+14 more)

### Community 61 - "Telegram VPN Billing Bot"
Cohesion: 0.12
Nodes (16): Telegram VPN Billing Bot, Админ-команды, Антишеринг-мониторинг, Возможности, Граф кода (graphify), Единая подписка SubHub, Как формируется клиент, Конфигурация (+8 more)

### Community 62 - "Report"
Cohesion: 0.25
Nodes (4): Any, Конфигурация xray-клиента: SOCKS 127.0.0.1:10808 → VLESS по ссылке., Report, xray_client_config()

### Community 63 - "D VPN — личный кабинет"
Cohesion: 0.25
Nodes (7): D VPN — личный кабинет, Архитектура, Запуск вместе с существующим ботом, Локальная разработка, Результаты проверки, Что реализовано, Эксплуатация

### Community 64 - "texts.py"
Cohesion: 0.06
Nodes (65): _after_applied_payment(), Уведомления и SubHub после применения; возвращает итог для администратора.…, HTML-строка с анимированным значком для вставки в текст сообщения., tg(), notify_first_purchase_channel(), notify_user_extended(), notify_user_rejected(), notify_user_subscription_deleted() (+57 more)

### Community 65 - "XuiError"
Cohesion: 0.16
Nodes (10): Exception, Базовая ошибка взаимодействия с панелью 3x-ui., Создаёт нового клиента в inbound через addClient., XuiError, parametrize, test_client_read_failure_is_not_misreported_as_missing(), test_malformed_inbounds_is_not_treated_as_empty_panel(), test_health_check_server_returns_false_on_error() (+2 more)

### Community 66 - "session"
Cohesion: 0.21
Nodes (11): _maker(), _maker_for(), async_sessionmaker, AsyncSession, fixture, Подменяет фоновые циклы метками: видно, какие из них запустил…, БД в файле с отдельными соединениями у теста и у фонового worker'а. Общее…, session() (+3 more)

### Community 67 - "Приёмка услуги «Обход белых списков» — 5 октября 2026"
Cohesion: 0.10
Nodes (24): fmt_gb(), Остаток или расход в ГБ (1 ГБ = 1024³ байт), округлённый вниз: лишнего не…, PaymentRequestError, PendingRequestExists, Exception, Заявку нельзя создать по бизнес-правилам., У пользователя уже есть заявка с отправленной квитанцией., whitelist_package_title() (+16 more)

### Community 71 - "FakeCallback"
Cohesion: 0.13
Nodes (15): Пользовательский раздел «Обход белых списков». action: home | refresh | buy…, WhitelistCallback, get_account(), test_trial_activation_finishes_when_subhub_drops_connection(), parametrize, test_rollout_handles_ambiguous_users_by_admin_choice(), FakeCallback, FakeState (+7 more)

### Community 72 - "test_health_poller_triggers_subhub_after_recovering_payment"
Cohesion: 0.22
Nodes (3): _Maker, parametrize, test_health_poller_triggers_subhub_after_recovering_payment()

### Community 73 - "MenuCallback"
Cohesion: 0.21
Nodes (12): MenuCallback, Навигация по inline-меню (редактирование сообщения на месте). action: home |…, admin_home_keyboard(), cancel_payment_keyboard(), Подтверждение сброса данных пользователя в боте., Кнопка «Отмена» под заявкой на оплату — удаляет заявку., reset_bot_confirm_keyboard(), _all_buttons() (+4 more)

### Community 74 - "VpnClient"
Cohesion: 0.16
Nodes (25): Приветствие. Использует HTML-разметку: ID завёрнут в <code> — Telegram копирует…, welcome(), _is_active(), _needs_onboarding(), Раздел услуги виден при запущенной услуге и подписке или сохранённом остатке., Показываем вопрос только новым пользователям без VPN-клиента., _send_welcome(), _welcome_markup() (+17 more)

### Community 75 - "panel_call"
Cohesion: 0.20
Nodes (4): set_inbound(), panel_call(), Any, restart_later()

### Community 76 - "4. Точки интеграции"
Cohesion: 0.22
Nodes (6): 1. Что получает пользователь, 4. Точки интеграции, 6. Порядок внедрения, 7. Откат, Услуга «Обход белых списков» — реализация и порядок внедрения, Полная синхронизация с ожиданием её завершения.

### Community 77 - "on_bind_action"
Cohesion: 0.33
Nodes (7): on_bind_action(), notify_admins_bind_failed(), notify_user_bind_approved(), notify_user_bind_rejected(), admin_bind_card(), bind_request_approved(), bind_request_rejected()

### Community 78 - "_phases"
Cohesion: 0.06
Nodes (42): BaseException, Acts, _async(), describe(), DiesOnFirstChange, die(), docker(), expect_poll() (+34 more)

### Community 79 - "purchase_plans_keyboard"
Cohesion: 0.33
Nodes (6): extend_plans_keyboard(), _plan_label(), purchase_plans_keyboard(), Тарифы продления (без пробного). Назад — в меню подписки., Тарифы оформления. Пробный — только если доступен. Назад — на главную., test_purchase_keyboard_trial_visibility()

### Community 80 - "admin_server_detail"
Cohesion: 0.33
Nodes (5): admin_server_detail(), admin_servers(), server_purpose_label(), _server_status_mark(), 14. Исправление D-2: SubHub собирается без ручной установки greenlet (результаты от 2026-10-05, после приёмки)

### Community 81 - "pg"
Cohesion: 0.33
Nodes (5): dict, _NoLocalLocks, pg(), fixture, Каждый вызов получает новый asyncio.Lock — как в отдельном процессе.

### Community 82 - "_FakeMessage"
Cohesion: 0.40
Nodes (3): _FakeBot, _FakeMessage, Any

### Community 84 - "api.ts"
Cohesion: 0.33
Nodes (4): APIError, Configuration, Plan, Profile

### Community 86 - "subscriptions.py"
Cohesion: 0.50
Nodes (4): collect_links(), AsyncSession, Возвращает список (метка, ссылка-подписка) по всем серверам пользователя. Для…, _sub_link()

### Community 87 - "PaymentCallback"
Cohesion: 0.50
Nodes (4): PaymentCallback, Callback админских действий над заявкой., test_payment_confirmation_finishes_when_subhub_drops_connection(), test_admin_confirms_purchase_and_user_is_notified()

### Community 88 - "Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026"
Cohesion: 0.50
Nodes (3): Прогон до исправления (SubHub `d9a2c80` + незакоммиченные правки, не относящиеся к задаче), Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026, Финальный прогон после исправления

### Community 89 - "XuiAuthError"
Cohesion: 0.50
Nodes (4): Ошибка авторизации в панели., XuiAuthError, HTTPXMock, test_login_error_does_not_leak_password()

### Community 90 - "reconcile_cycle"
Cohesion: 0.15
Nodes (12): _BatchResult, Итог обхода учётов (накапливается между запусками, если обход прерывали).…, Учёты, чьё состояние этим обходом не подтверждено. Удалённые (``skipped_gone``)…, Следующая пачка учётов: стабильный курсор по id, а не по изменяемой метке., Читает пачку одной сессией панели и сверяет учёты по одному. Сбой одного учёта…, Один повторный проход по учётам, изменившимся между чтением и сверкой., Полный обход учётов whitelist-сервера ограниченными пачками. Пачки берутся по…, _reconcile_batch() (+4 more)

### Community 91 - "resolve_uncertain"
Cohesion: 0.11
Nodes (19): apply_usage(), Списывает новый расход: сначала бесплатный, затем купленный остаток., Решение администратора: неразделённый расход до или после события. Применяет…, Остатки (бесплатный, купленный) на конце неразделённого периода. Первая пара —…, resolve_uncertain(), uncertain_outcomes(), P1: неопределённый учёт скрывает сброс счётчика и увеличивает квоту, P1: смена целевого inbound не переносит существующих пользователей (+11 more)

### Community 92 - "Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026"
Cohesion: 0.33
Nodes (5): 1. 3x-ui v3.9.0 (`ghcr.io/mhsanaei/3x-ui:v3.9.0`), финальный прогон — 25 OK, 5 FAIL, 2. 3x-ui v3.9.0, повтор S6, S6b, S7 с исправленным расчётом — 5 OK, 0 FAIL, 3. 3x-ui v3.5.0 (`ghcr.io/mhsanaei/3x-ui:v3.5.0`, Xray 26.7.11) — 5 OK, 9 FAIL, 4. Первый (предварительный) прогон на v3.9.0 — 24 OK, 6 FAIL, Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026

### Community 93 - "provisioning.py"
Cohesion: 0.12
Nodes (39): ServerUpdateResult, apply_access(), apply_access_to_server(), bind_existing_client(), bind_user_by_public_id(), BindResult, _build_spec(), client_email() (+31 more)

### Community 94 - "active_user"
Cohesion: 0.50
Nodes (4): active_user(), panel(), fixture, Пользователь с оплаченной подпиской: покупка трафика доступна.

### Community 95 - "Q: собери контекст проекта"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: собери контекст проекта, Source Nodes

### Community 96 - "check_servers"
Cohesion: 0.18
Nodes (7): check_server(), check_servers(), AsyncSession, Проверяет доступность панели 3x-ui одного сервера. Успешный login считается…, Проверяет все серверы и сохраняет результат в БД. Возвращает отображение…, Фоновые задачи, test_health_check_server_returns_true_on_success()

### Community 97 - "models.py"
Cohesion: 0.14
Nodes (23): aiogram_exceptions, aiogram_filters, app_bot, TimestampMixin, BindRequestStatus, AuditLog, AuditRepository, app_services (+15 more)

### Community 98 - "SubHubClient"
Cohesion: 0.10
Nodes (20): Exception, Resolve the first panel identity known to SubHub. Older bot records can have a…, Base error for the internal SubHub integration., The panels have not exposed this identity to SubHub yet., The identity exists, but currently has no active nodes., Small authenticated client for the SubHub admin API. Subscription URLs and…, ResolvedSubscription, SubHubClient (+12 more)

### Community 99 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 100 - "conftest.py"
Cohesion: 0.44
Nodes (9): pytest_asyncio, admin(), AsyncSession, datetime, fixture, server(), session(), user() (+1 more)

### Community 101 - "whitelist_admin"
Cohesion: 0.16
Nodes (15): aiogram_fsm_state, InlineKeyboardMarkup, whitelist_admin(), _whitelist_home(), AdminStates, OnboardingStates, admin_whitelist_rollout_report(), answer() (+7 more)

### Community 102 - "admin_nav"
Cohesion: 0.08
Nodes (30): admin_nav(), _edit_panel(), _finalize_new_server(), _finalize_whitelist_server(), on_payment_action(), callback_query, CallbackQuery, Сохраняет сервер и сразу пытается импортировать его inbound'ы. Так добавленный… (+22 more)

### Community 108 - "test_ux.py"
Cohesion: 0.12
Nodes (23): _parse_server_line(), Парсит 'name|country|panel_url|username|password|[kind]|[sub]|[purpose]'.…, country_flag(), Эмодзи-флаг по ISO2-коду страны (напр. 'SE' -> 🇸🇪). Иначе пусто., Пробный доступен, если им не пользовались и подписку никогда не оформляли., _trial_available(), test_parse_server_line_accepts_valid(), test_parse_server_line_rejects_invalid() (+15 more)

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

### Community 117 - "admin_servers_keyboard"
Cohesion: 0.67
Nodes (3): admin_servers_keyboard(), Список серверов: кнопка на каждый + добавить + назад., test_admin_servers_keyboard_has_add_and_back()

### Community 120 - "test_ui.py"
Cohesion: 0.29
Nodes (7): aiogram_methods, TelegramBadRequest, _bad_request(), _Callback, Exception, test_answer_callback_ignores_expired_query_id(), test_answer_callback_reraises_other_bad_request()

### Community 121 - "install_guides_keyboard"
Cohesion: 0.67
Nodes (3): install_guides_keyboard(), Гайды по установке клиента — ссылки на Telegraph., test_install_guides_keyboard_has_telegraph_links()

### Community 131 - "_server_health_poller"
Cohesion: 0.15
Nodes (11): Очередь применения квот «Обхода белых списков» на панели. Единственный…, Best-effort запрос SubHub перечитать панели после фоновых изменений., Фоновая периодическая проверка доступности серверов 3x-ui. Очередь применения…, _server_health_poller(), pending_applied(), subhub_sync(), _subhub_sync(), _whitelist_queue_worker() (+3 more)

### Community 135 - "sh"
Cohesion: 0.20
Nodes (7): 15. Лимит трафика 3x-ui → SubHub: единица `totalGB` и источник расхода (результаты от 2026-10-05, после приёмки), 2. Проверенный контракт 3x-ui, main(), Новый контейнер панели: учётные данные, шаблон для частной сети, inbound., docker stop/start: новый процесс панели и новый процесс Xray., sh(), wait_api()

## Knowledge Gaps
- **178 isolated node(s):** `credentials`, `dvpn/site`, `name`, `version`, `private` (+173 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 929 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `test_provisioning.py`, `whitelist.py`, `test_legacy_bind.py`, `test_whitelist.py`, `menu_nav`, `admin_handlers.py`, `test_whitelist_reconcile.py`, `billing.py`, `test_expiry.py`, `PendingServerUpdate`, `test_whitelist_pg.py`, `whitelist_e2e.py`, `PaymentRequest`, `utcnow`, `Settings`, `VpnClientRepository`, `Base`, `MockPanelUpdater`, `scenario`, `deployment_check.py`, `test_security.py`, `UserRepository`, `PanelUpdateError`, `texts.py`, `FakeCallback`, `VpnClient`, `on_bind_action`, `_phases`, `pg`, `provisioning.py`, `models.py`, `conftest.py`, `whitelist_admin`, `admin_nav`, `test_ux.py`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Why does `Server` connect `Server` to `test_provisioning.py`, `whitelist.py`, `test_legacy_bind.py`, `test_whitelist.py`, `admin_handlers.py`, `ServerInbound`, `keyboards.py`, `test_whitelist_reconcile.py`, `PendingServerUpdate`, `test_whitelist_pg.py`, `test_crypto.py`, `whitelist_e2e.py`, `PaymentRequest`, `utcnow`, `test_all_inline_buttons_have_color_style`, `Protocol`, `VpnClientRepository`, `Base`, `XuiPanelUpdater`, `MockPanelUpdater`, `Контекст проекта`, `test_whitelist_inbound_compat.py`, `test_whitelist_epoch.py`, `What You Must Do When Invoked`, `UserRepository`, `PanelUpdateError`, `texts.py`, `pg`, `reconcile_cycle`, `resolve_uncertain`, `provisioning.py`, `check_servers`, `models.py`, `conftest.py`, `whitelist_admin`, `admin_nav`, `test_ux.py`, `admin_servers_keyboard`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `XuiClient` connect `XuiClient` to `check_servers`, `models.py`, `Server`, `XuiError`, `XuiPanelUpdater`, `admin_handlers.py`, `ServerInbound`, `panel_call`, `Panel`, `test_xui_client.py`, `whitelist_e2e.py`, `._api`, `XuiAuthError`, `test_security.py`, `PanelUpdateError`, `provisioning.py`, `xui_traffic_d3.py`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 167 inferred relationships involving `User` (e.g. with `admin_add_server_line()` and `admin_broadcast_send()`) actually correct?**
  _`User` has 167 INFERRED edges - model-reasoned connections that need verification._
- **Are the 90 inferred relationships involving `VpnClient` (e.g. with `notify_user_extended()` and `access_extended()`) actually correct?**
  _`VpnClient` has 90 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `MockPanelUpdater` (e.g. with `ClientServerMapping` and `Server`) actually correct?**
  _`MockPanelUpdater` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 61 inferred relationships involving `Settings` (e.g. with `add_server()` and `admin_add_server_line()`) actually correct?**
  _`Settings` has 61 INFERRED edges - model-reasoned connections that need verification._
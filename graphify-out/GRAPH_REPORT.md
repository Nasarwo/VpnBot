# Graph Report - VpnBot  (2026-10-06)

## Corpus Check
- 167 files · ~177,097 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 9, .example 3, .conf 1)

## Summary
- 3040 nodes · 10996 edges · 144 communities (111 shown, 33 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1402 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8dece727`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- _pay
- test_provisioning.py
- AsyncSession
- BindRequestRepository
- test_whitelist.py
- user_handlers.py
- admin_handlers.py
- whitelist_compat.py
- keyboards.py
- test_whitelist_reconcile.py
- VpnClientRepository
- test_subhub_trigger.py
- .confirmed
- test_expiry.py
- alembic
- pending_updates.py
- test_whitelist_pg.py
- test_whitelist_bot.py
- main.go
- App.vue
- config.py
- main.py
- PaymentRequest
- utcnow
- XuiClient
- notify.py
- XuiPanelUpdater
- test_broadcast.py
- middlewares.py
- Protocol
- xui_traffic_d3.py
- User
- Контекст проекта
- Server
- PaymentStatus
- web_bridge.py
- test_whitelist_queue_worker.py
- test_whitelist_xui.py
- test_ux.py
- MockPanelUpdater
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
- main
- web_preview.mjs
- test_whitelist_inbound_compat.py
- _wl_state
- What You Must Do When Invoked
- test_security.py
- whitelist_admin
- UserRepository
- test_whitelist_volume_display.py
- whitelist_migration_check.py
- Telegram VPN Billing Bot
- Report
- D VPN — личный кабинет
- texts.py
- sync_inventory
- WhitelistAccount
- payments.py
- dvpn/site
- telegram-vpn-billing-bot
- subscription_link.py
- whitelist.py
- graphify reference: extra exports and benchmark
- VpnClient
- AsyncSession
- 4. Точки интеграции
- Приёмка услуги «Обход белых списков» — 5 октября 2026
- whitelist_background_e2e.py
- collections_abc
- IsAdmin
- models.py
- connection_overview
- AGENTS.md
- api.ts
- FakeBot
- FakeMessage
- EncryptedString
- Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026
- DiesOnFirstChange
- reconcile_cycle
- WhitelistLedger
- Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026
- provisioning.py
- Production deployment — 2026-10-06
- Q: собери контекст проекта
- test_health_check_server_returns_true_on_success
- reset_user_bot_state
- SubHubClient
- graphify reference: query, path, explain
- conftest.py
- ui.py
- sharing_report
- pytest
- Обновление production — 4 октября 2026
- whitelist_e2e_2026-10-05.md
- vue
- Повторное ревью — 6 октября 2026
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
- get_plan
- extraction-spec.md
- active_user
- _Crash
- .bot
- Настройка серверов и авто-провижининг

## God Nodes (most connected - your core abstractions)
1. `User` - 272 edges
2. `MockPanelUpdater` - 153 edges
3. `VpnClient` - 151 edges
4. `Server` - 145 edges
5. `Settings` - 139 edges
6. `PaymentRequest` - 112 edges
7. `PaymentStatus` - 99 edges
8. `_pay()` - 93 edges
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

## Communities (144 total, 33 thin omitted)

### Community 0 - "_pay"
Cohesion: 0.13
Nodes (59): choose_inbound(), InventoryResult, process_due(), Фоновая очередь: применяет несинхронизированные состояния с backoff. Кроме…, Делает выбранный inbound единственной целью whitelist-сервера. Готовность…, P1: смена целевого inbound не переносит существующих пользователей, 19. Перенос клиентов при смене целевого inbound (2026-10-06, P1 ревью), ops (+51 more)

### Community 1 - "test_provisioning.py"
Cohesion: 0.12
Nodes (31): MappingRepository, ensure_inbounds_imported(), ensure_vpn_client(), has_targets(), Импортирует inbound'ы для включённых серверов, у которых их ещё нет. Нужно для…, Есть ли хотя бы один включённый сервер с включённым inbound для провижининга., Возвращает VPN-клиента пользователя, создавая его при отсутствии., days_from_now() (+23 more)

### Community 2 - "AsyncSession"
Cohesion: 0.12
Nodes (32): access_state(), AccessState, _aware(), classify_origin(), _clear_placement(), confirm_traffic_payment(), _finish_reconcile(), forget_panel_client() (+24 more)

### Community 3 - "BindRequestRepository"
Cohesion: 0.12
Nodes (26): confirm_bind_cmd(), BindRequestStatus, BindRequest, Заявка на привязку существующей подписки (до внедрения бота)., BindRequestRepository, approve_request(), BindApproveResult, BindRequestError (+18 more)

### Community 4 - "test_whitelist.py"
Cohesion: 0.10
Nodes (54): list_open_events(), Фоновая сверка расхода: обходит все учёты пачками по ``limit``. Возвращает…, Неприменённые события учёта пользователя в порядке возникновения., reconcile_usage(), 3.1. Бесплатный пакет и доступ, 3.2. Купленный трафик, 3.6. Биллинг, конкуренция, восстановление, 3.7. Интерфейс, миграции, устройство (+46 more)

### Community 5 - "user_handlers.py"
Cohesion: 0.08
Nodes (58): aiogram_fsm_context, aiogram_fsm_state, AdminStates, OnboardingStates, ProofStates, bind_request_received(), connection_unavailable(), free_proxies_intro() (+50 more)

### Community 6 - "admin_handlers.py"
Cohesion: 0.13
Nodes (50): add_inbound(), add_server(), admin_add_server_cancel(), admin_add_server_line(), admin_broadcast_cancel(), admin_broadcast_send(), admin_delete_subscription_cancel(), admin_panel() (+42 more)

### Community 7 - "whitelist_compat.py"
Cohesion: 0.13
Nodes (22): check_inbound(), _check_vless_reality(), describe(), _foreign_flows(), InboundCompat, _json(), _public_key_available(), Any (+14 more)

### Community 8 - "keyboards.py"
Cohesion: 0.10
Nodes (57): BindCallback, Callback админских действий над заявкой на привязку подписки., _adm(), admin_add_server_type_keyboard(), admin_back_keyboard(), admin_bind_keyboard(), admin_bind_retry_keyboard(), admin_confirm_delete_keyboard() (+49 more)

### Community 9 - "test_whitelist_reconcile.py"
Cohesion: 0.06
Nodes (62): _fmt_span(), Состояние фоновой сверки расхода для админ-раздела (по данным процесса). «Обход…, _reconcile_gaps(), reconcile_status_lines(), Состояние и наблюдаемость фоновой сверки (хранится в памяти процесса).…, Сколько прошло с завершения последнего обхода (в т. ч. с пропусками)., Верхняя граница возраста данных *сверенных* учётов последнего обхода., Сколько прошло с завершения последнего полностью подтверждённого обхода. (+54 more)

### Community 10 - "VpnClientRepository"
Cohesion: 0.08
Nodes (59): Клиенты, которым пора слать уведомление об окончании. Берём тех, у кого задан…, VpnClientRepository, Any, AsyncSession, Записывает событие в audit_logs., record(), _apply_panels(), _as_aware() (+51 more)

### Community 11 - "test_subhub_trigger.py"
Cohesion: 0.13
Nodes (17): StreamReader, StreamWriter, _command(), LocalSubHub, _Maker, _paid(), parametrize, Быстрый триггер SubHub (POST /admin/sync) из обработчиков бота. Вместо SubHub —… (+9 more)

### Community 12 - ".confirmed"
Cohesion: 0.40
Nodes (4): Каждый существующий учёт сверен: ни ошибок, ни пропусков., Доменная модель, Логика продления, Пользовательские сценарии

### Community 13 - "test_expiry.py"
Cohesion: 0.15
Nodes (19): notify_user_expiry(), Уведомление пользователя об окончании подписки. True — если доставлено., _as_aware(), process_expiry_notifications(), AsyncSession, datetime, Стадия уведомления по остатку времени до окончания. 0 — рано, 1 — остался день,…, Шлёт уведомления «за день / за час / в момент окончания». Каждая стадия… (+11 more)

### Community 15 - "pending_updates.py"
Cohesion: 0.22
Nodes (17): PendingServerUpdate, PendingServerUpdateRepository, datetime, Сохраняет результат фоновой проверки доступности сервера., _utcnow(), apply_pending_for_server(), apply_pending_update(), _apply_to_server() (+9 more)

### Community 16 - "test_whitelist_pg.py"
Cohesion: 0.08
Nodes (39): attach_proof(), Прикрепляет подтверждение оплаты (текст/фото/документ) к заявке., datetime, dict, 4. Автоматические тесты, _ledger(), Приёмка: гонки услуги на PostgreSQL, не покрытые test_whitelist_pg. Те же…, test_admin_block_is_not_lost_to_queue_reads_or_reconcile() (+31 more)

### Community 17 - "test_whitelist_bot.py"
Cohesion: 0.12
Nodes (38): on_payment_action(), PaymentCallback, PlanCallback, Callback выбора тарифа пользователем. code — код тарифа из PLANS (1m/6m/12m)…, Пользовательский раздел «Обход белых списков». action: home | refresh | buy…, Callback админских действий над заявкой., WhitelistCallback, get_account() (+30 more)

### Community 18 - "main.go"
Cohesion: 0.07
Nodes (29): credentials, go_pkg_bytes, go_pkg_context, go_pkg_crypto_hmac, go_pkg_crypto_rand, go_pkg_crypto_sha256, go_pkg_crypto_subtle, go_pkg_crypto_tls (+21 more)

### Community 19 - "App.vue"
Cohesion: 0.07
Nodes (24): authTitles, awaiting, busy, code, comment, config, connection, days (+16 more)

### Community 20 - "config.py"
Cohesion: 0.11
Nodes (32): get_settings(), decrypt(), encrypt(), _fernet(), is_encrypted(), Возвращает Fernet, выведенный из SECRET_KEY, либо None если ключ не задан.…, Шифрует строку. Без SECRET_KEY возвращает значение как есть (dev/тесты)., Расшифровывает строку. Legacy-значения в открытом виде возвращает как есть. (+24 more)

### Community 21 - "main.py"
Cohesion: 0.09
Nodes (33): aiogram, aiogram_client_default, aiogram_fsm_storage_memory, aiogram_utils_token, build_root_router(), PaymentAttachment, get_session(), get_sessionmaker() (+25 more)

### Community 22 - "PaymentRequest"
Cohesion: 0.14
Nodes (9): PaymentRequest, PaymentRepository, Берёт заявку с блокировкой строки (SELECT ... FOR UPDATE). На Postgres…, Число применённых оплат подписки (покупки трафика не учитываются)., Удаляет заявку (вместе с вложениями по каскаду)., Последняя успешная (применённая/подтверждённая) оплата пользователя.…, _make_waiting(), test_admin_pending_has_no_raw_angle_brackets() (+1 more)

### Community 23 - "utcnow"
Cohesion: 0.18
Nodes (36): IpObservation, _active_clients(), collect_all(), collect_for_client(), compute_status(), _level_for(), list_all_statuses(), list_flagged() (+28 more)

### Community 24 - "XuiClient"
Cohesion: 0.05
Nodes (47): check_server(), Проверяет доступность панели 3x-ui одного сервера. Успешный login считается…, list_panel_clients(), Возвращает список клиентов, уже существующих на панели сервера., Any, Exception, Response, _quote_path_segment() (+39 more)

### Community 25 - "notify.py"
Cohesion: 0.16
Nodes (16): admin_delete_subscription_by_client_id(), _after_applied_payment(), on_bind_action(), Уведомления и SubHub после применения; возвращает итог для администратора.…, notify_admins_bind_failed(), notify_admins_new_bind_request(), notify_user_bind_approved(), notify_user_bind_rejected() (+8 more)

### Community 26 - "XuiPanelUpdater"
Cohesion: 0.08
Nodes (32): ProvisionInbound, Inbound сервера, к которому нужно привязать клиента., Один клиент панели (глобальный по email), привязанный к её inbound'ам.…, ServerProvision, build_client_record(), client_record_body(), Извлекает model.Client из ответа ``clients/get``., Унифицированный объект клиента для нового client-API (3x-ui >= 3.2.x).… (+24 more)

### Community 27 - "test_broadcast.py"
Cohesion: 0.23
Nodes (9): aiogram_exceptions, BroadcastResult, Рассылает текстовое сообщение всем пользователям. Сообщение отправляется…, send_broadcast(), FakeBot, Текст рассылки шлётся без parse_mode — произвольный текст админа не должен…, test_broadcast_text_is_plain_no_parse_mode(), test_send_broadcast_counts_sent_and_failed() (+1 more)

### Community 28 - "middlewares.py"
Cohesion: 0.16
Nodes (20): aiogram_types, _command_name(), DbSessionMiddleware, _describe_callback(), _describe_event(), _describe_message(), Any, CallbackQuery (+12 more)

### Community 29 - "Protocol"
Cohesion: 0.07
Nodes (54): admin_import_inbounds(), Protocol, Inbound на панели сервера, в который нужно заводить клиентов. На одном сервере…, ServerInbound, ProvisionTarget, Описание клиента, которого нужно создать/обновить в конкретном inbound., build_client_object(), client_identifier() (+46 more)

### Community 30 - "xui_traffic_d3.py"
Cohesion: 0.10
Nodes (46): 15. Лимит трафика 3x-ui → SubHub: единица `totalGB` и источник расхода (результаты от 2026-10-05, после приёмки), 2. Проверенный контракт 3x-ui, Число строк и хэш упорядоченного содержимого прежних столбцов., snapshot(), accounted(), add_client(), container_started(), delta() (+38 more)

### Community 31 - "User"
Cohesion: 0.13
Nodes (12): notify_admins_failed(), notify_admins_new_request(), User, _expiry_notify_poller(), Фоновая рассылка уведомлений об окончании подписки (день/час/в момент)., Bot, Обработчики бота с сессией на каждое обновление, как у middleware., Пользователь создаёт заявку на подписку и присылает квитанцию. (+4 more)

### Community 32 - "Контекст проекта"
Cohesion: 0.13
Nodes (14): Архитектура, Безопасность аутентификации (backend/main.go), Важные инженерные правила, Доменная модель (таблицы веб-части, в БД бота), Запуск, Контекст проекта, Конфигурация, Локальные артефакты (+6 more)

### Community 33 - "Server"
Cohesion: 0.04
Nodes (45): _finalize_new_server(), _finalize_whitelist_server(), Сохраняет сервер и сразу пытается импортировать его inbound'ы. Так добавленный…, Добавляет сервер услуги и сразу сверяет его inbound'ы. До успешной сверки с…, Server, Меняет только имя, сохраняя сервер и все его связи., Меняет URL подписки, не затрагивая связи сервера., Удаляет сервер вместе с inbound'ами и привязками (каскад). Коллекции грузим… (+37 more)

### Community 34 - "PaymentStatus"
Cohesion: 0.24
Nodes (22): PaymentStatus, confirm_payment(), Идемпотентное подтверждение оплаты администратором. Повторный вызов для уже…, _make_waiting_payment(), AsyncSession, test_compute_new_expiry_active(), test_compute_new_expiry_expired(), test_compute_new_expiry_none() (+14 more)

### Community 35 - "web_bridge.py"
Cohesion: 0.11
Nodes (30): aiohttp, Durable per-admin Telegram delivery, retried independently of HTTP requests., WebAccount, WebDelivery, WebLinkRequest, decide_link(), has_purchase(), link_callback() (+22 more)

### Community 36 - "test_whitelist_queue_worker.py"
Cohesion: 0.06
Nodes (59): _queue_worker_alive(), Очередь применения квот «Обхода белых списков» на панели. Единственный…, Фоновая сверка расхода whitelist-услуги: полный обход пачками. Работает…, Запускает фоновые циклы процесса бота (кроме доставки сайта). Одна сборка для…, Best-effort запрос SubHub перечитать панели после фоновых изменений., Фоновая периодическая проверка доступности серверов 3x-ui. Очередь применения…, _server_health_poller(), pending_applied() (+51 more)

### Community 37 - "test_whitelist_xui.py"
Cohesion: 0.21
Nodes (34): QuotaTarget, Абсолютное целевое состояние клиента с учётом трафика. ``total_bytes`` —…, 3.5. Учёт трафика и интеграция 3x-ui, _apply_existing(), _auth(), _body(), _inbound(), HTTPXMock (+26 more)

### Community 38 - "test_ux.py"
Cohesion: 0.07
Nodes (50): aiogram_filters_callback_data, app_bot, AdminCallback, MenuCallback, OnboardCallback, Навигация по inline-меню (редактирование сообщения на месте). action: home |…, Онбординг: был ли пользователь клиентом до внедрения бота., Навигация по админ-панели (/admin). action: home | servers | server | rename |… (+42 more)

### Community 39 - "MockPanelUpdater"
Cohesion: 0.18
Nodes (25): MockPanelUpdater, datetime, Mock-реализация: ничего не делает либо имитирует сбой нужных серверов. Для…, Inbound удалён на панели: его привязки исчезают у всех клиентов., _buy(), _down(), _fresh(), _is_waiting() (+17 more)

### Community 40 - "package.json"
Cohesion: 0.11
Nodes (17): lucide-vue-next, typescript, vite, @vitejs/plugin-vue, vue-tsc, dependencies, lucide-vue-next, vue (+9 more)

### Community 41 - "whitelist_e2e.py"
Cohesion: 0.06
Nodes (51): build_updater(), argparse, asyncio, json, ops_acceptance, main(), panel_view(), Any (+43 more)

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
Nodes (12): Админские команды, Антишеринг, Контекст проекта, Конфигурация, Локальные артефакты, Назначение, Основные пользовательские сценарии, Структура (+4 more)

### Community 46 - ".auth"
Cohesion: 0.53
Nodes (6): net/http.Request, net/http.ResponseWriter, decode(), digest(), fail(), respond()

### Community 47 - "Panel"
Cohesion: 0.09
Nodes (15): admin_servers(), 14. Исправление D-2: SubHub собирается без ручной установки greenlet (результаты от 2026-10-05, после приёмки), import_control_inbound(), VLESS REALITY inbound с клиентом контрольного примера и его статистикой., Panel, Use the binary packaged for the container image's architecture., Прямой доступ к тестовой панели — для проверок и действий «вручную в панели»., Разрешает трафик к частной подсети стенда — только на тестовых панелях.… (+7 more)

### Community 48 - "Задание агенту: услуга «Обход белых списков» в VpnBot"
Cohesion: 0.15
Nodes (12): 1. Контекст проекта, 2. Согласованное поведение услуги, 3. Сервер и настройки администратора, 4. Технический контракт учёта трафика, 5. Биллинг, конкуренция и восстановление, 6. Пользовательский интерфейс, 7. Обязательная проверка, 8. Порядок работы и сдача (+4 more)

### Community 49 - "app"
Cohesion: 0.29
Nodes (6): app, config, context.Context, github.com/jackc/pgx/v5/pgxpool.Pool, net/http.Client, pgx.Tx

### Community 50 - "main"
Cohesion: 0.22
Nodes (7): bucket, limiter, net/http.Handler, sync.Mutex, time.Time, env(), main()

### Community 51 - "main"
Cohesion: 0.23
Nodes (12): decorate(), wrapped(), user_operation(), 5. Конкуренция и восстановление, Восстановление после недоступной статистики, Фоновая сверка расхода: обход, гарантии, ограничения, check_released(), main() (+4 more)

### Community 52 - "web_preview.mjs"
Cohesion: 0.29
Nodes (6): ref_node_fs_promises, ref_node_http, ref_node_path, ref_node_url, root, types

### Community 53 - "test_whitelist_inbound_compat.py"
Cohesion: 0.17
Nodes (32): get_active_server(), Включённый whitelist-сервер (не более одного по уникальному индексу)., server_ready(), target_inbound(), cryptography_hazmat_primitives, cryptography_hazmat_primitives_asymmetric_x25519, 3.4. Сервер, импорт, выдача, администрирование, 8. Проверки (+24 more)

### Community 54 - "_wl_state"
Cohesion: 0.09
Nodes (47): AwaitingCredit, Применяет состояние учёта пользователя на whitelist-панели., Сохранённое начисление, ещё не сверенное с расходом., Остатки пользователя; при доступной панели — с актуальной сверкой. Чтение…, sync_user(), user_overview(), 3.3. Ограничения доступа, _available() (+39 more)

### Community 55 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 56 - "test_security.py"
Cohesion: 0.06
Nodes (53): aiogram_filters, forward_proof_to_admins(), UserRole, FakeBot, _make_payment(), _persist_payment(), AsyncSession, parametrize (+45 more)

### Community 57 - "whitelist_admin"
Cohesion: 0.19
Nodes (13): InlineKeyboardMarkup, whitelist_admin(), _whitelist_home(), admin_whitelist_inventory(), admin_whitelist_rollout_report(), get_config(), list_packages(), Запускает услугу и выдаёт её нынешним активным пользователям. Повторный запуск… (+5 more)

### Community 58 - "UserRepository"
Cohesion: 0.20
Nodes (8): Удаляет пользователя и связанные записи (каскад в ORM)., Telegram ID всех пользователей, когда-либо запускавших бота., Генерирует короткий уникальный публичный ID пользователя., UserRepository, AsyncSession, test_backfills_public_id_for_existing(), test_get_or_create_assigns_public_id(), test_public_id_is_stable_and_unique()

### Community 59 - "test_whitelist_volume_display.py"
Cohesion: 0.14
Nodes (18): fmt_gb(), Остаток или расход в ГБ (1 ГБ = 1024³ байт), округлённый вниз: лишнего не…, gib_to_bytes(), Overview, Заданный объём в ГБ (без единицы, точка): так, как он вводился. Байты при вводе…, set_volume_gib_text(), decimal, 12. Исправление D-4 (результаты от 2026-10-05, после приёмки) (+10 more)

### Community 60 - "whitelist_migration_check.py"
Cohesion: 0.25
Nodes (19): Единственная строка настроек услуги (id = 1)., WhitelistConfig, alembic(), check(), docker(), downgrade_cycle(), dsn(), ensure_defaults_idempotent() (+11 more)

### Community 61 - "Telegram VPN Billing Bot"
Cohesion: 0.13
Nodes (12): Telegram VPN Billing Bot, Админ-команды, Антишеринг-мониторинг, Возможности, Граф кода (graphify), Единая подписка SubHub, Конфигурация, Локальный запуск (dev) (+4 more)

### Community 63 - "D VPN — личный кабинет"
Cohesion: 0.25
Nodes (7): D VPN — личный кабинет, Архитектура, Запуск вместе с существующим ботом, Локальная разработка, Результаты проверки, Что реализовано, Эксплуатация

### Community 64 - "texts.py"
Cohesion: 0.05
Nodes (79): admin_nav(), _edit_panel(), callback_query, CallbackQuery, Редактирует сообщение админ-панели, мягко гасит ошибки. parse_mode=None —…, HTML-строка с анимированным значком для вставки в текст сообщения., tg(), notify_user_traffic_credited() (+71 more)

### Community 65 - "sync_inventory"
Cohesion: 0.24
Nodes (12): fetch_inbounds(), import_inbounds(), Any, Сверяет inbound'ы панели с локальными целями провижининга. Удалённые и…, Читает список inbound'ов панели (``inbounds/list``) как есть., Сверка реестра с уже прочитанным списком (см. :func:`import_inbounds`)., reconcile_inbounds(), _ss_method() (+4 more)

### Community 66 - "WhitelistAccount"
Cohesion: 0.07
Nodes (37): Бизнес-учёт трафика пользователя на whitelist-сервере. Остатки…, Привязка клиента whitelist-панели к inbound'у, созданная самой услугой. Строка…, WhitelistAccount, WhitelistPlacement, admin_summary(), AdminSummary, _applied_target(), compute_target() (+29 more)

### Community 67 - "payments.py"
Cohesion: 0.12
Nodes (30): Пакет покупки трафика «Обход белых списков» (настраивается админом)., TrafficPackage, cancel_open_request(), create_request(), create_traffic_request(), _new_payment_code(), _open_request_for_update(), PaymentRequestError (+22 more)

### Community 71 - "subscription_link.py"
Cohesion: 0.22
Nodes (9): _is_valid_public_id(), parse_subhub_subscription_token(), parse_subscription_public_id(), Извлекает ID подписки из последнего сегмента URL. Примеры: -…, Extract a secret token only from a SubHub /connection[/raw]/ URL., re, parametrize, test_parse_subhub_subscription_token_supports_encoded_and_raw_endpoints() (+1 more)

### Community 72 - "whitelist.py"
Cohesion: 0.10
Nodes (35): adjust_balance(), after_access_change(), _append_note(), apply_usage(), mark_dirty(), next_reconcile_delay(), Decimal, Exception (+27 more)

### Community 73 - "graphify reference: extra exports and benchmark"
Cohesion: 0.20
Nodes (9): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000) (+1 more)

### Community 74 - "VpnClient"
Cohesion: 0.09
Nodes (34): _is_active(), Разрешает задавать ADMIN_TELEGRAM_IDS как строку '1,2,3' или одно число., Конфигурация приложения из переменных окружения / .env., Убирает пробелы и обрамляющие кавычки вокруг токена., Settings, VpnClient, has_active_timed_client(), has_client_access() (+26 more)

### Community 76 - "4. Точки интеграции"
Cohesion: 0.18
Nodes (11): claim_inbound(), ensure_defaults(), Администратор признаёт привязки клиентов услуги к inbound'у привязками услуги.…, Идемпотентная инициализация: настройки и начальные пакеты., 1. Что получает пользователь, 3. Модель учёта, 4. Точки интеграции, 6. Порядок внедрения (+3 more)

### Community 77 - "Приёмка услуги «Обход белых списков» — 5 октября 2026"
Cohesion: 0.25
Nodes (7): 10. Заключение, 1. Итог, 5. Миграции и резервная копия (PostgreSQL 16.15), 6. Реальные 3x-ui и SubHub, 7. Happ — не выполнено, 9. Что не проверялось, Приёмка услуги «Обход белых списков» — 5 октября 2026

### Community 78 - "whitelist_background_e2e.py"
Cohesion: 0.08
Nodes (36): asyncpg, contextlib, Acts, _async(), describe(), docker(), expect_poll(), expect_trigger() (+28 more)

### Community 80 - "IsAdmin"
Cohesion: 0.21
Nodes (10): IsAdmin, TelegramObject, Пропускает событие только если пользователь — администратор., BaseFilter, test_is_admin_filter_accepts_admin(), test_is_admin_filter_rejects_missing_user(), test_is_admin_filter_rejects_regular_user(), test_settings_is_admin() (+2 more)

### Community 81 - "models.py"
Cohesion: 0.06
Nodes (39): app_db, Base, Базовый класс для всех ORM-моделей., TimestampMixin, AuditLog, ClientServerMapping, WebSession, WebToken (+31 more)

### Community 82 - "connection_overview"
Cohesion: 0.33
Nodes (6): connection_overview(), Unified SubHub connection screen with live server availability., server_button_label(), Флаг не добавляется автоматически — он уже в названии сервера., test_connection_overview_shows_server_availability(), test_server_button_label_has_no_autoflag()

### Community 84 - "api.ts"
Cohesion: 0.33
Nodes (4): APIError, Configuration, Plan, Profile

### Community 85 - "FakeBot"
Cohesion: 0.17
Nodes (13): notify_user_extended(), notify_user_rejected(), whitelist_pending_note(), 2. Стенд, async_sessionmaker, FakeBot, Any, AsyncSession (+5 more)

### Community 86 - "FakeMessage"
Cohesion: 0.33
Nodes (4): admin_denied(), FakeMessage, Заменитель Message: запоминает ответы., test_non_admin_admin_command_denied()

### Community 87 - "EncryptedString"
Cohesion: 0.33
Nodes (5): EncryptedString, Any, Прозрачно шифрует значение при записи и расшифровывает при чтении. - Если…, Важные инженерные правила проекта, TypeDecorator

### Community 88 - "Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026"
Cohesion: 0.50
Nodes (3): Прогон до исправления (SubHub `d9a2c80` + незакоммиченные правки, не относящиеся к задаче), Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026, Финальный прогон после исправления

### Community 89 - "DiesOnFirstChange"
Cohesion: 0.25
Nodes (7): BaseException, DiesOnFirstChange, die(), ProcessKilled, Any, Имитация гибели процесса: не перехватывается ``except Exception`` кода бота., Настоящий updater, у которого первое изменение панели «убивает процесс».

### Community 90 - "reconcile_cycle"
Cohesion: 0.15
Nodes (12): _BatchResult, Итог обхода учётов (накапливается между запусками, если обход прерывали).…, Учёты, чьё состояние этим обходом не подтверждено. Удалённые (``skipped_gone``)…, Следующая пачка учётов: стабильный курсор по id, а не по изменяемой метке., Читает пачку одной сессией панели и сверяет учёты по одному. Сбой одного учёта…, Один повторный проход по учётам, изменившимся между чтением и сверкой., Полный обход учётов whitelist-сервера ограниченными пачками. Пачки берутся по…, _reconcile_batch() (+4 more)

### Community 91 - "WhitelistLedger"
Cohesion: 0.09
Nodes (38): Журнал выдач/начислений/корректировок, привязанных к исходной операции. Выдача…, WhitelistLedger, QuotaClientState, Прочитанное с панели состояние клиента и его счётчика трафика., apply_event(), _apply_quota(), _consistent_anchor(), _Context (+30 more)

### Community 92 - "Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026"
Cohesion: 0.33
Nodes (5): 1. 3x-ui v3.9.0 (`ghcr.io/mhsanaei/3x-ui:v3.9.0`), финальный прогон — 25 OK, 5 FAIL, 2. 3x-ui v3.9.0, повтор S6, S6b, S7 с исправленным расчётом — 5 OK, 0 FAIL, 3. 3x-ui v3.5.0 (`ghcr.io/mhsanaei/3x-ui:v3.5.0`, Xray 26.7.11) — 5 OK, 9 FAIL, 4. Первый (предварительный) прогон на v3.9.0 — 24 OK, 6 FAIL, Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026

### Community 93 - "provisioning.py"
Cohesion: 0.08
Nodes (52): app_services, ServerUpdateResult, apply_access(), apply_access_to_server(), bind_existing_client(), bind_user_by_public_id(), BindResult, build_provision_spec() (+44 more)

### Community 94 - "Production deployment — 2026-10-06"
Cohesion: 0.33
Nodes (5): Backups and rollback, Checks after deployment, Deployment incidents and limits, Production deployment — 2026-10-06, Release

### Community 95 - "Q: собери контекст проекта"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: собери контекст проекта, Source Nodes

### Community 97 - "reset_user_bot_state"
Cohesion: 0.50
Nodes (4): AsyncSession, Удаляет пользователя и связанные данные только из БД бота. 3x-ui панели не…, reset_user_bot_state(), UserResetResult

### Community 98 - "SubHubClient"
Cohesion: 0.10
Nodes (24): build_happ_import_url(), Exception, Resolve the first panel identity known to SubHub. Older bot records can have a…, Base error for the internal SubHub integration., The panels have not exposed this identity to SubHub yet., The identity exists, but currently has no active nodes., Build a signed HTTPS trampoline for importing a legacy subscription., Small authenticated client for the SubHub admin API. Subscription URLs and… (+16 more)

### Community 99 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 100 - "conftest.py"
Cohesion: 0.53
Nodes (8): admin(), AsyncSession, datetime, fixture, server(), session(), user(), vpn_client()

### Community 101 - "ui.py"
Cohesion: 0.16
Nodes (13): aiogram_methods, answer(), edit(), Any, CallbackQuery, Безопасно редактирует сообщение callback'а. ``callback.message`` может быть…, Безопасно отправляет ответ в чат callback'а (если сообщение доступно)., TelegramBadRequest (+5 more)

### Community 102 - "sharing_report"
Cohesion: 0.31
Nodes (9): ip_scan(), sharing_report(), items: список кортежей (VpnClient, SharingStatus)., Полный краткий отчёт по IP-наблюдениям всех VPN-клиентов., sharing_all(), sharing_detail(), sharing_disabled(), sharing_level_label() (+1 more)

### Community 103 - "pytest"
Cohesion: 0.16
Nodes (10): pytest, _payment(), parametrize, Приёмка: происхождение текущего доступа при выдаче услуги нынешним…, test_origin_of_current_access(), test_rollout_handles_ambiguous_users_by_admin_choice(), panel(), fixture (+2 more)

### Community 104 - "Обновление production — 4 октября 2026"
Cohesion: 0.25
Nodes (6): PAY-1C3F1344, Внедрено, Дополнительный дефект, обнаруженный при приёмке, Незавершённые операции, Обновление production — 4 октября 2026, Проверки и резервирование

### Community 107 - "Повторное ревью — 6 октября 2026"
Cohesion: 0.33
Nodes (5): P1: неопределённый учёт скрывает сброс счётчика и увеличивает квоту, Spec, Выполненные проверки, Повторное ревью — 6 октября 2026, Что подтверждено и что остаётся перед внедрением

### Community 108 - "_parse_server_line"
Cohesion: 0.40
Nodes (5): _parse_server_line(), Парсит 'name|country|panel_url|username|password|[kind]|[sub]|[purpose]'.…, test_parse_server_line_accepts_valid(), test_parse_server_line_rejects_invalid(), test_parse_server_line()

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

### Community 117 - "Ревью VpnBot — 4 октября 2026"
Cohesion: 0.25
Nodes (8): Исправления в рабочем дереве, Объём и доказательства, Порядок применения в production, Проверки, Разбор PAY-1C3F1344, Ревью VpnBot — 4 октября 2026, Результат, Устройство production

### Community 120 - "Оставшиеся риски и решения"
Cohesion: 0.25
Nodes (8): P1/P2 — частичный успех внешней операции требует сверки, P1 — административные права зависят от тарифа, P1 — биллинг и панели не образуют одну транзакцию, P1 — пароли панелей не защищены шифрованием приложения, P2 — мониторинг и производительность, P2 — старые ошибки оплат без ожидающих задач, P2 — эксплуатация и воспроизводимость, Оставшиеся риски и решения

### Community 121 - "get_plan"
Cohesion: 0.40
Nodes (4): get_plan(), PaymentPlan, Выгода относительно помесячной оплаты за тот же срок., test_get_plan()

### Community 127 - "active_user"
Cohesion: 0.50
Nodes (4): active_user(), panel(), fixture, Пользователь с оплаченной подпиской: покупка трафика доступна.

### Community 130 - "_Crash"
Cohesion: 0.40
Nodes (3): RuntimeError, _Crash, Процесс завершился после запроса к панели, до commit.

### Community 131 - ".bot"
Cohesion: 0.50
Nodes (3): Запуск, Запуск через Docker Compose, API

### Community 132 - "Настройка серверов и авто-провижининг"
Cohesion: 0.33
Nodes (6): Как формируется клиент, Настройка серверов и авто-провижининг, Перенос пользователей, существовавших до бота, Шаг 1. Добавить серверы, Шаг 2. Импортировать inbound'ы каждого сервера, hysteria()

## Knowledge Gaps
- **182 isolated node(s):** `credentials`, `dvpn/site`, `name`, `version`, `private` (+177 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 983 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **33 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `test_provisioning.py`, `AsyncSession`, `BindRequestRepository`, `test_whitelist.py`, `user_handlers.py`, `admin_handlers.py`, `test_whitelist_reconcile.py`, `VpnClientRepository`, `test_expiry.py`, `pending_updates.py`, `test_whitelist_pg.py`, `test_whitelist_bot.py`, `config.py`, `main.py`, `PaymentRequest`, `utcnow`, `notify.py`, `test_broadcast.py`, `PaymentStatus`, `web_bridge.py`, `test_ux.py`, `whitelist_e2e.py`, `main`, `test_security.py`, `whitelist_admin`, `UserRepository`, `test_whitelist_volume_display.py`, `texts.py`, `WhitelistAccount`, `payments.py`, `whitelist.py`, `VpnClient`, `whitelist_background_e2e.py`, `IsAdmin`, `models.py`, `FakeBot`, `WhitelistLedger`, `provisioning.py`, `reset_user_bot_state`, `conftest.py`, `sharing_report`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Why does `Server` connect `Server` to `_pay`, `test_provisioning.py`, `test_whitelist.py`, `admin_handlers.py`, `keyboards.py`, `test_whitelist_reconcile.py`, `VpnClientRepository`, `pending_updates.py`, `test_whitelist_pg.py`, `test_whitelist_bot.py`, `config.py`, `main.py`, `utcnow`, `XuiClient`, `XuiPanelUpdater`, `Protocol`, `PaymentStatus`, `web_bridge.py`, `test_whitelist_xui.py`, `test_ux.py`, `MockPanelUpdater`, `test_whitelist_inbound_compat.py`, `_wl_state`, `whitelist_admin`, `texts.py`, `sync_inventory`, `WhitelistAccount`, `whitelist.py`, `models.py`, `connection_overview`, `EncryptedString`, `reconcile_cycle`, `WhitelistLedger`, `provisioning.py`, `conftest.py`, `pytest`, `_parse_server_line`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `MockPanelUpdater` connect `MockPanelUpdater` to `_pay`, `test_provisioning.py`, `test_whitelist.py`, `test_whitelist_reconcile.py`, `VpnClientRepository`, `test_subhub_trigger.py`, `pending_updates.py`, `test_whitelist_pg.py`, `test_whitelist_bot.py`, `notify.py`, `Protocol`, `Server`, `PaymentStatus`, `web_bridge.py`, `test_whitelist_queue_worker.py`, `main`, `test_whitelist_inbound_compat.py`, `_wl_state`, `test_security.py`, `VpnClient`, `4. Точки интеграции`, `models.py`, `FakeBot`, `WhitelistLedger`, `provisioning.py`, `pytest`, `Повторное ревью — 6 октября 2026`, `active_user`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Are the 171 inferred relationships involving `User` (e.g. with `add_inbound()` and `admin_add_server_line()`) actually correct?**
  _`User` has 171 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `MockPanelUpdater` (e.g. with `ClientServerMapping` and `Server`) actually correct?**
  _`MockPanelUpdater` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 92 inferred relationships involving `VpnClient` (e.g. with `notify_user_extended()` and `access_extended()`) actually correct?**
  _`VpnClient` has 92 INFERRED edges - model-reasoned connections that need verification._
- **Are the 57 inferred relationships involving `Server` (e.g. with `_finalize_new_server()` and `_finalize_whitelist_server()`) actually correct?**
  _`Server` has 57 INFERRED edges - model-reasoned connections that need verification._
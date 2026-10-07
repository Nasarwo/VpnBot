# Graph Report - VpnBot  (2026-10-06)

## Corpus Check
- 197 files · ~207,177 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 23 file(s) not represented in the graph (top: (none) 9, .example 3, .patch 3)

## Summary
- 3136 nodes · 11166 edges · 142 communities (124 shown, 18 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1414 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `520d65e2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_whitelist_retarget.py
- provisioning.py
- PanelUpdater
- test_broadcast.py
- test_whitelist.py
- Panel
- Settings
- user_overview
- keyboards.py
- test_whitelist_reconcile.py
- billing.py
- test_whitelist_bot.py
- test_notify_swallows_telegram_api_errors
- get_active_server
- sqlalchemy
- test_review_regressions.py
- test_whitelist_pg.py
- XuiClient
- main.go
- App.vue
- pytest
- main.py
- Услуга «Обход белых списков» — реализация и порядок внедрения
- utcnow
- _push
- VpnClientRepository
- XuiPanelUpdater
- import_inbounds
- .__call__
- Protocol
- xui_traffic_d3.py
- Bot
- Контекст проекта
- User
- create_request
- web_bridge.py
- test_whitelist_queue_worker.py
- test_whitelist_xui.py
- AsyncSession
- MockPanelUpdater
- package.json
- xui_updater.py
- compilerOptions
- main_test.go
- api
- Контекст проекта
- .auth
- test_ux.py
- Задание агенту: услуга «Обход белых списков» в VpnBot
- app
- main
- QuotaClientState
- web_preview.mjs
- test_whitelist_inbound_compat.py
- _wl_state
- What You Must Do When Invoked
- test_security.py
- test_xui_client.py
- notify.py
- user_handlers.py
- whitelist_migration_check.py
- Telegram VPN Billing Bot
- Report
- D VPN — личный кабинет
- texts.py
- bind_requests.py
- test_plans.py
- WhitelistAccount
- dvpn/site
- telegram-vpn-billing-bot
- test_subhub_trigger.py
- IsAdmin
- user_operation
- VpnClient
- whitelist_e2e.py
- Оставшиеся риски и решения
- Приёмка услуги «Обход белых списков» — 5 октября 2026
- whitelist_background_e2e.py
- Финальное сохранение расхода 3x-ui — 6 октября 2026
- ClientServerMapping
- AsyncSession
- _utcnow
- AGENTS.md
- models.py
- Динамические названия whitelist — 6 октября 2026
- PaymentRequest
- EncryptedString
- Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026
- whitelist.py
- reconcile_cycle
- test_verdicts_agree_with_subhub_link_builder
- Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026
- FakeMessage
- Production deployment — 2026-10-06
- Q: собери контекст проекта
- test_health_check_server_returns_false_on_error
- ._clean_bot_token
- SubHubClient
- graphify reference: query, path, explain
- devDependencies
- ._http
- Обновление whitelist-панели — 6 октября 2026
- admin_nav
- Обновление production — 4 октября 2026
- whitelist_e2e_2026-10-05.md
- PaymentStatus
- stack.sh
- whitelist_migration_2026-10-05.md
- scripts
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- ref_node_fs
- Ревью VpnBot — 4 октября 2026
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- record
- Проверка исправленной 3x-ui — 6 октября 2026
- extraction-spec.md
- graphify reference: extra exports and benchmark
- test_payment_kind_conflict.py
- _Crash
- session
- Повторная приёмка whitelist — 6 октября 2026
- sharing_summary
- wl_server
- parametrize
- Приёмка на Android / Happ 4.6.0
- Повторное ревью — 6 октября 2026
- Server
- Ограниченное подключение whitelist к production — 6 октября 2026
- web_smoke.py
- _server_health_poller
- Включение whitelist для действующих пользователей — 6 октября 2026
- test_subscription_delete.py
- whitelist_inbounds.py
- _PoisonedPanel

## God Nodes (most connected - your core abstractions)
1. `User` - 272 edges
2. `VpnClient` - 153 edges
3. `MockPanelUpdater` - 153 edges
4. `Server` - 145 edges
5. `Settings` - 143 edges
6. `PaymentRequest` - 112 edges
7. `PaymentStatus` - 99 edges
8. `_pay()` - 93 edges
9. `VpnClientRepository` - 86 edges
10. `XuiClient` - 83 edges

## Surprising Connections (you probably didn't know these)
- `Изменения` --references--> `EncryptedString`  [INFERRED]
  docs/acceptance/whitelist_integration_2026-10-06.md → app/db/types.py
- `P1 — пароли панелей не защищены шифрованием приложения` --references--> `EncryptedString`  [INFERRED]
  docs/REVIEW_2026-10-04.md → app/db/types.py
- `6. Реальные 3x-ui и SubHub` --references--> `recover_confirmed_payments()`  [INFERRED]
  docs/WHITELIST_ACCEPTANCE.md → app/services/billing.py
- `Фоновые задачи` --references--> `check_servers()`  [INFERRED]
  context.md → app/services/health.py
- `Смена целевого inbound и перенос клиентов (2026-10-06)` --references--> `_push()`  [INFERRED]
  docs/WHITELIST_SERVICE.md → app/services/whitelist.py

## Import Cycles
- None detected.

## Communities (142 total, 18 thin omitted)

### Community 0 - "test_whitelist_retarget.py"
Cohesion: 0.13
Nodes (53): process_due(), Фоновая очередь: применяет несинхронизированные состояния с backoff. Кроме…, ops, _add_candidate(), _available(), _callback(), _command(), Перенос клиентов при смене цели: админ-сценарии бота, SubHub и ops-сверка.… (+45 more)

### Community 1 - "provisioning.py"
Cohesion: 0.08
Nodes (55): PanelUpdateError, Exception, Ошибка обновления клиента в панели., ServerUpdateResult, apply_access(), apply_access_to_server(), bind_existing_client(), BindResult (+47 more)

### Community 2 - "PanelUpdater"
Cohesion: 0.15
Nodes (21): PanelUpdater, Интерфейс работы с клиентом в панели. Реализуется как mock (для тестов/MVP) и…, Создаёт/обновляет клиента сразу для всех inbound'ов сервера., _delete_local_subscription(), delete_user_subscription(), AsyncSession, Удаляет VPN-подписку пользователя с панелей и из БД бота. История оплат, заявки…, adjust_balance() (+13 more)

### Community 3 - "test_broadcast.py"
Cohesion: 0.31
Nodes (6): BroadcastResult, Рассылает текстовое сообщение всем пользователям. Сообщение отправляется…, send_broadcast(), FakeBot, test_send_broadcast_counts_sent_and_failed(), test_send_broadcast_empty_list()

### Community 4 - "test_whitelist.py"
Cohesion: 0.11
Nodes (50): 3.1. Бесплатный пакет и доступ, 3.2. Купленный трафик, 3.3. Ограничения доступа, 3.6. Биллинг, конкуренция, восстановление, 3.7. Интерфейс, миграции, устройство, 3. Матрица требований и доказательств, _account(), _ledger_count() (+42 more)

### Community 5 - "Panel"
Cohesion: 0.07
Nodes (31): admin_servers(), 14. Исправление D-2: SubHub собирается без ручной установки greenlet (результаты от 2026-10-05, после приёмки), import_control_inbound(), main(), panel_view(), Any, Path, Квота трафика 3x-ui → SubHub на реальной панели, без маскирующего… (+23 more)

### Community 6 - "Settings"
Cohesion: 0.09
Nodes (73): add_inbound(), add_server(), admin_add_server_cancel(), admin_add_server_line(), admin_broadcast_cancel(), admin_broadcast_send(), admin_delete_subscription_by_client_id(), admin_delete_subscription_cancel() (+65 more)

### Community 7 - "user_overview"
Cohesion: 0.16
Nodes (27): AwaitingCredit, list_open_events(), Фоновая сверка расхода: обходит все учёты пачками по ``limit``. Возвращает…, Сохранённое начисление, ещё не сверенное с расходом., Остатки пользователя; при доступной панели — с актуальной сверкой. Чтение…, Неприменённые события учёта пользователя в порядке возникновения., reconcile_usage(), user_overview() (+19 more)

### Community 8 - "keyboards.py"
Cohesion: 0.09
Nodes (66): aiogram_filters_callback_data, AdminCallback, MenuCallback, OnboardCallback, PaymentCallback, Навигация по inline-меню (редактирование сообщения на месте). action: home |…, Онбординг: был ли пользователь клиентом до внедрения бота., Навигация по админ-панели (/admin). action: home | servers | server | rename |… (+58 more)

### Community 9 - "test_whitelist_reconcile.py"
Cohesion: 0.06
Nodes (59): Состояние фоновой сверки расхода для админ-раздела (по данным процесса). «Обход…, reconcile_status_lines(), Состояние и наблюдаемость фоновой сверки (хранится в памяти процесса).…, Сколько прошло с завершения последнего обхода (в т. ч. с пропусками)., Верхняя граница возраста данных *сверенных* учётов последнего обхода., Сколько прошло с завершения последнего полностью подтверждённого обхода., Верхняя граница возраста данных всех учётов после последнего подтверждённого…, ReconcileStatus (+51 more)

### Community 10 - "billing.py"
Cohesion: 0.12
Nodes (41): _apply_panels(), _as_aware(), BillingError, BillingResult, compute_new_expiry(), _confirm_traffic(), _count_eligible_mappings(), _evaluate_panel_results() (+33 more)

### Community 11 - "test_whitelist_bot.py"
Cohesion: 0.15
Nodes (17): Пользовательский раздел «Обход белых списков». action: home | refresh | buy…, WhitelistCallback, callback_query, whitelist_menu(), test_conflicted_subscription_request_extends_once_and_adds_no_traffic(), test_whitelist_buy_reports_pending_subscription_request(), FakeCallback, FakeState (+9 more)

### Community 12 - "test_notify_swallows_telegram_api_errors"
Cohesion: 0.14
Nodes (13): forward_proof_to_admins(), notify_admins_new_request(), FakeBot, _make_payment(), Минимальный заменитель aiogram.Bot для проверки notify-функций., Подпись к чеку полностью контролируется пользователем и уходит админу с…, Для фото/документа подпись пользователя НЕ используется как caption —…, Сбой отправки одному админу не должен ронять обработку апдейта. (+5 more)

### Community 13 - "get_active_server"
Cohesion: 0.25
Nodes (14): get_active_server(), Включённый whitelist-сервер (не более одного по уникальному индексу)., 3.4. Сервер, импорт, выдача, администрирование, 8. Проверки, rollout(), FakeMessage, test_admin_adds_whitelist_server_with_automatic_inventory(), test_admin_failed_first_sync_is_visible_and_retryable() (+6 more)

### Community 14 - "sqlalchemy"
Cohesion: 0.06
Nodes (3): alembic, collections_abc, sqlalchemy

### Community 15 - "test_review_regressions.py"
Cohesion: 0.11
Nodes (30): PendingServerUpdate, Inbound на панели сервера, в который нужно заводить клиентов. На одном сервере…, ServerInbound, PendingServerUpdateRepository, apply_pending_for_server(), apply_pending_update(), _apply_to_server(), _as_aware() (+22 more)

### Community 16 - "test_whitelist_pg.py"
Cohesion: 0.09
Nodes (34): dict, 4. Автоматические тесты, _ledger(), Приёмка: гонки услуги на PostgreSQL, не покрытые test_whitelist_pg. Те же…, test_admin_block_is_not_lost_to_queue_reads_or_reconcile(), test_concurrent_rollouts_grant_once_and_keep_purchase(), test_purchase_confirmed_after_expiry_races_queue_without_enabling(), test_trial_double_click_grants_three_gb_once() (+26 more)

### Community 17 - "XuiClient"
Cohesion: 0.06
Nodes (41): Any, Exception, Response, _quote_path_segment(), Авторизованный запрос: гарантирует login и при истёкшей сессии выполняет…, Берёт CSRF-токен с /csrf-token (3x-ui >= 3.2.x). На старых панелях endpoint…, Базовая ошибка взаимодействия с панелью 3x-ui., Read 3x-ui external endpoints for a reverse-proxied inbound. (+33 more)

### Community 18 - "main.go"
Cohesion: 0.07
Nodes (29): credentials, go_pkg_bytes, go_pkg_context, go_pkg_crypto_hmac, go_pkg_crypto_rand, go_pkg_crypto_sha256, go_pkg_crypto_subtle, go_pkg_crypto_tls (+21 more)

### Community 19 - "App.vue"
Cohesion: 0.07
Nodes (28): APIError, Configuration, Plan, Profile, authTitles, awaiting, busy, code (+20 more)

### Community 20 - "pytest"
Cohesion: 0.14
Nodes (25): get_settings(), decrypt(), encrypt(), _fernet(), is_encrypted(), Возвращает Fernet, выведенный из SECRET_KEY, либо None если ключ не задан.…, Шифрует строку. Без SECRET_KEY возвращает значение как есть (dev/тесты)., Расшифровывает строку. Legacy-значения в открытом виде возвращает как есть. (+17 more)

### Community 21 - "main.py"
Cohesion: 0.07
Nodes (34): aiogram_client_default, aiogram_fsm_storage_memory, aiogram_utils_token, DbSessionMiddleware, Открывает сессию БД, получает/создаёт пользователя и кладёт их в data., build_root_router(), Настраивает логирование приложения. - корневой логгер: WARNING (чтобы сторонние…, setup_logging() (+26 more)

### Community 22 - "Услуга «Обход белых списков» — реализация и порядок внедрения"
Cohesion: 0.29
Nodes (8): _parse_gb(), gib_to_bytes(), 1. Что получает пользователь, 6. Порядок внедрения, 7. Откат, 9. Ограничения и решения, Услуга «Обход белых списков» — реализация и порядок внедрения, test_accounting_stays_integer_truncated_bytes()

### Community 23 - "utcnow"
Cohesion: 0.09
Nodes (55): IpObservation, _active_clients(), collect_all(), collect_for_client(), compute_status(), _level_for(), list_all_statuses(), list_flagged() (+47 more)

### Community 24 - "_push"
Cohesion: 0.09
Nodes (31): Привязка клиента whitelist-панели к inbound'у, созданная самой услугой. Строка…, WhitelistPlacement, claim_inbound(), _confirm_attach(), _defer(), _find_placement(), _Link, _list_placements() (+23 more)

### Community 25 - "VpnClientRepository"
Cohesion: 0.14
Nodes (29): MappingRepository, VpnClientRepository, bind_user_by_public_id(), ensure_vpn_client(), Возвращает VPN-клиента пользователя, создавая его при отсутствии., Привязывает пользователя по ID из ссылки-подписки. Ищет клиента на всех…, days_from_now(), _panel_info() (+21 more)

### Community 26 - "XuiPanelUpdater"
Cohesion: 0.10
Nodes (21): Один клиент панели (глобальный по email), привязанный к её inbound'ам.…, ServerProvision, build_client_record(), client_record_body(), Извлекает model.Client из ответа ``clients/get``., Унифицированный объект клиента для нового client-API (3x-ui >= 3.2.x).…, _is_missing_client_error(), Старые панели: отдельный клиент в каждом inbound (per-inbound email). (+13 more)

### Community 27 - "import_inbounds"
Cohesion: 0.24
Nodes (11): ensure_inbounds_imported(), fetch_inbounds(), import_inbounds(), Any, Сверяет inbound'ы панели с локальными целями провижининга. Удалённые и…, Read inventory and external Hosts needed for whitelist XHTTP links., Сверка реестра с уже прочитанным списком (см. :func:`import_inbounds`)., Импортирует inbound'ы для включённых серверов, у которых их ещё нет. Нужно для… (+3 more)

### Community 28 - ".__call__"
Cohesion: 0.25
Nodes (13): _describe_callback(), _describe_event(), Any, CallbackQuery, TelegramObject, Chat, _private_chat(), test_describe_addserver_redacts_secrets() (+5 more)

### Community 29 - "Protocol"
Cohesion: 0.11
Nodes (35): Protocol, ProvisionTarget, Описание клиента, которого нужно создать/обновить в конкретном inbound., build_client_object(), client_identifier(), _client_uuid_for_api(), _looks_like_db_id(), merge_client_record_for_update() (+27 more)

### Community 30 - "xui_traffic_d3.py"
Cohesion: 0.10
Nodes (47): 15. Лимит трафика 3x-ui → SubHub: единица `totalGB` и источник расхода (результаты от 2026-10-05, после приёмки), 2. Проверенный контракт 3x-ui, Число строк и хэш упорядоченного содержимого прежних столбцов., snapshot(), accounted(), add_client(), container_started(), delta() (+39 more)

### Community 31 - "Bot"
Cohesion: 0.12
Nodes (9): _expiry_notify_poller(), Фоновая рассылка уведомлений об окончании подписки (день/час/в момент)., build_updater(), Bot, async_sessionmaker, Обработчики бота с сессией на каждое обновление, как у middleware., Пользователь создаёт заявку на подписку и присылает квитанцию., Сдвиг срока в БД вместо ожидания реального окончания (минуты, а не дни). (+1 more)

### Community 32 - "Контекст проекта"
Cohesion: 0.13
Nodes (14): Архитектура, Безопасность аутентификации (backend/main.go), Важные инженерные правила, Доменная модель (таблицы веб-части, в БД бота), Запуск, Контекст проекта, Конфигурация, Локальные артефакты (+6 more)

### Community 33 - "User"
Cohesion: 0.09
Nodes (36): Приветствие. Использует HTML-разметку: ID завёрнут в <code> — Telegram копирует…, welcome(), Удаляет данные пользователя в боте и показывает онбординг заново., _reset_bot_user(), User, Удаляет пользователя и связанные записи (каскад в ORM)., Telegram ID всех пользователей, когда-либо запускавших бота., Генерирует короткий уникальный публичный ID пользователя. (+28 more)

### Community 34 - "create_request"
Cohesion: 0.09
Nodes (30): Прежняя заявка с квитанцией на проверке: новой не создаём, квитанций не ждём., _refuse_pending_request(), cancel_open_request(), create_request(), create_traffic_request(), _new_payment_code(), _open_request_for_update(), PaymentRequestError (+22 more)

### Community 35 - "web_bridge.py"
Cohesion: 0.12
Nodes (33): aiohttp, Durable per-admin Telegram delivery, retried independently of HTTP requests., WebAccount, WebDelivery, WebLinkRequest, decide_link(), delivery_loop(), has_purchase() (+25 more)

### Community 36 - "test_whitelist_queue_worker.py"
Cohesion: 0.19
Nodes (28): Запускает фоновые циклы процесса бота (кроме доставки сайта). Одна сборка для…, start_background_tasks(), stop_background_tasks(), Task, _expire(), _purchase_while_panel_down(), parametrize, Очередь применения whitelist-квот не зависит от проверки здоровья серверов.… (+20 more)

### Community 37 - "test_whitelist_xui.py"
Cohesion: 0.20
Nodes (36): ProvisionInbound, QuotaTarget, Inbound сервера, к которому нужно привязать клиента., Абсолютное целевое состояние клиента с учётом трафика. ``total_bytes`` —…, 3.5. Учёт трафика и интеграция 3x-ui, _apply_existing(), _auth(), _body() (+28 more)

### Community 38 - "AsyncSession"
Cohesion: 0.15
Nodes (30): Единственная строка настроек услуги (id = 1)., WhitelistConfig, confirm_traffic_payment(), ensure_defaults(), get_config(), grant_for_subscription_payment(), grant_for_trial(), _ledger_exists() (+22 more)

### Community 39 - "MockPanelUpdater"
Cohesion: 0.18
Nodes (26): admin_payment_card(), payment_status_label(), MockPanelUpdater, Mock-реализация: ничего не делает либо имитирует сбой нужных серверов. Для…, Inbound удалён на панели: его привязки исчезают у всех клиентов., _buy(), _down(), _fresh() (+18 more)

### Community 40 - "package.json"
Cohesion: 0.12
Nodes (14): lucide-vue-next, typescript, vite, @vitejs/plugin-vue, vue, vue-tsc, dependencies, lucide-vue-next (+6 more)

### Community 41 - "xui_updater.py"
Cohesion: 0.24
Nodes (10): _client_flows(), _inbound_client_flow(), _other_flow(), Any, flow клиента в ``settings.clients[]`` inbound'а; None — клиента там нет., flow прочей привязки после обновления (best-effort, для наблюдения). В 3x-ui…, Read-after-write: панель должна хранить ровно заданные значения., _verify_quota_state() (+2 more)

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
Cohesion: 0.11
Nodes (17): Каждый существующий учёт сверен: ни ошибок, ни пропусков., Админские команды, Антишеринг, Доменная модель, Интеграция с 3x-ui, Контекст проекта, Конфигурация, Локальные артефакты (+9 more)

### Community 46 - ".auth"
Cohesion: 0.53
Nodes (6): net/http.Request, net/http.ResponseWriter, decode(), digest(), fail(), respond()

### Community 47 - "test_ux.py"
Cohesion: 0.10
Nodes (32): _parse_server_line(), Парсит 'name|country|panel_url|username|password|[kind]|[sub]|[purpose]'.…, custom_emoji_id(), emoji_char(), Возвращает unicode-символ значка (без анимации)., Возвращает custom_emoji_id значка или None, если значок не найден., connection_keyboard(), One stable SubHub subscription link for every location and protocol. (+24 more)

### Community 48 - "Задание агенту: услуга «Обход белых списков» в VpnBot"
Cohesion: 0.15
Nodes (12): 1. Контекст проекта, 2. Согласованное поведение услуги, 3. Сервер и настройки администратора, 4. Технический контракт учёта трафика, 5. Биллинг, конкуренция и восстановление, 6. Пользовательский интерфейс, 7. Обязательная проверка, 8. Порядок работы и сдача (+4 more)

### Community 49 - "app"
Cohesion: 0.29
Nodes (6): app, config, context.Context, github.com/jackc/pgx/v5/pgxpool.Pool, net/http.Client, pgx.Tx

### Community 50 - "main"
Cohesion: 0.22
Nodes (7): bucket, limiter, net/http.Handler, sync.Mutex, time.Time, env(), main()

### Community 51 - "QuotaClientState"
Cohesion: 0.10
Nodes (15): effective_flow(), QuotaClientState, Читает клиента и его счётчик трафика (None — клиента нет)., Пакетное чтение клиентов одной сессией панели., Создаёт/обновляет клиента с квотой и проверяет результат чтением.…, Снимает привязки клиента к ``inbound_ids`` (счётчик сохраняется). Проверяет…, flow, который 3x-ui копирует при attach: первый непустой по id inbound'а., Прочитанное с панели состояние клиента и его счётчика трафика. (+7 more)

### Community 52 - "web_preview.mjs"
Cohesion: 0.29
Nodes (6): ref_node_fs_promises, ref_node_http, ref_node_path, ref_node_url, root, types

### Community 53 - "test_whitelist_inbound_compat.py"
Cohesion: 0.33
Nodes (17): build_provision_spec(), server_ready(), target_inbound(), _assert_no_secrets(), parametrize, Совместимость целевого inbound услуги с форматом ссылок SubHub. Импорт inbound…, _server(), _sync() (+9 more)

### Community 54 - "_wl_state"
Cohesion: 0.18
Nodes (25): Применяет состояние учёта пользователя на whitelist-панели., sync_user(), _available(), Смена эпохи счётчика whitelist-панели при неприменённых событиях учёта. Внешний…, Пересоздание клиента: значение не уменьшилось, сменилась строка статистики., Сброс обнаруживается по последнему прочитанному значению, а не только по…, Строка до миграции f3a4b5c6d7e8: последнее чтение есть только в границах…, Операция взяла время до пакетного чтения, а счётчик прочитала после него. (+17 more)

### Community 55 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (25): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+17 more)

### Community 56 - "test_security.py"
Cohesion: 0.08
Nodes (34): _make_waiting(), _persist_payment(), AsyncSession, Тесты безопасности и устойчивости приложения. Покрывают ключевые свойства…, Роль не хранится «навсегда»: middleware пересчитывает её из настроек.…, Пользователь по callback может прислать только код тарифа — не цену/срок. Это…, Повторное создание заявки не плодит дубликаты (анти-спам / целостность)., Нельзя «откатить» уже применённую заявку отклонением. (+26 more)

### Community 57 - "test_xui_client.py"
Cohesion: 0.21
Nodes (28): Ошибка авторизации в панели., XuiAuthError, pytest_httpx, HTTPXMock, test_login_error_does_not_leak_password(), _client(), _mock_csrf(), HTTPXMock (+20 more)

### Community 58 - "notify.py"
Cohesion: 0.11
Nodes (24): on_bind_action(), BindCallback, Callback админских действий над заявкой на привязку подписки., admin_bind_retry_keyboard(), notify_admins_bind_failed(), notify_admins_new_bind_request(), notify_first_purchase_channel(), notify_user_bind_approved() (+16 more)

### Community 59 - "user_handlers.py"
Cohesion: 0.12
Nodes (35): aiogram, aiogram_fsm_context, app_bot, OnboardingStates, bind_request_received(), bind_request_waiting(), no_open_request(), onboarding_invalid_link() (+27 more)

### Community 60 - "whitelist_migration_check.py"
Cohesion: 0.24
Nodes (19): alembic_config, alembic_script, alembic(), check(), docker(), downgrade_cycle(), dsn(), ensure_defaults_idempotent() (+11 more)

### Community 61 - "Telegram VPN Billing Bot"
Cohesion: 0.15
Nodes (12): Telegram VPN Billing Bot, Админ-команды, Антишеринг-мониторинг, Возможности, Граф кода (graphify), Единая подписка SubHub, Конфигурация, Локальный запуск (dev) (+4 more)

### Community 62 - "Report"
Cohesion: 0.25
Nodes (4): Any, Конфигурация xray-клиента: SOCKS 127.0.0.1:10808 → VLESS по ссылке., Report, xray_client_config()

### Community 63 - "D VPN — личный кабинет"
Cohesion: 0.25
Nodes (7): D VPN — личный кабинет, Архитектура, Запуск вместе с существующим ботом, Локальная разработка, Результаты проверки, Что реализовано, Эксплуатация

### Community 64 - "texts.py"
Cohesion: 0.05
Nodes (86): HTML-строка с анимированным значком для вставки в текст сообщения., tg(), notify_user_traffic_credited(), access_extended(), admin_add_cancelled(), admin_bind_result(), admin_broadcast_cancelled(), admin_broadcast_result() (+78 more)

### Community 65 - "bind_requests.py"
Cohesion: 0.09
Nodes (39): app_db, BindRequestStatus, BindRequest, Заявка на привязку существующей подписки (до внедрения бота)., BindRequestRepository, approve_request(), BindApproveResult, BindRequestError (+31 more)

### Community 66 - "test_plans.py"
Cohesion: 0.23
Nodes (7): get_plan(), PaymentPlan, Выгода относительно помесячной оплаты за тот же срок., AsyncSession, test_changing_plan_updates_open_request(), test_create_request_with_plan(), test_get_plan()

### Community 67 - "WhitelistAccount"
Cohesion: 0.11
Nodes (25): Бизнес-учёт трафика пользователя на whitelist-сервере. Остатки…, WhitelistAccount, _applied_target(), _clear_placement(), compute_target(), _detect_external_disable(), forget_panel_client(), mark_dirty() (+17 more)

### Community 71 - "test_subhub_trigger.py"
Cohesion: 0.12
Nodes (19): StreamReader, StreamWriter, _command(), LocalSubHub, _Maker, _paid(), parametrize, Быстрый триггер SubHub (POST /admin/sync) из обработчиков бота. Вместо SubHub —… (+11 more)

### Community 72 - "IsAdmin"
Cohesion: 0.19
Nodes (11): aiogram_filters, IsAdmin, TelegramObject, Пропускает событие только если пользователь — администратор., BaseFilter, test_is_admin_filter_accepts_admin(), test_is_admin_filter_rejects_missing_user(), test_is_admin_filter_rejects_regular_user() (+3 more)

### Community 73 - "user_operation"
Cohesion: 0.24
Nodes (11): decorate(), wrapped(), user_operation(), 5. Конкуренция и восстановление, Восстановление после недоступной статистики, Синхронизация подписки SubHub: быстрый триггер и резервный опрос (2026-10-05), Фоновая сверка расхода: обход, гарантии, ограничения, check_released() (+3 more)

### Community 74 - "VpnClient"
Cohesion: 0.26
Nodes (20): _is_active(), Раздел услуги виден при запущенной услуге и подписке или сохранённом остатке., _welcome_markup(), _whitelist_visible(), UserRole, VpnClient, has_active_timed_client(), has_client_access() (+12 more)

### Community 75 - "whitelist_e2e.py"
Cohesion: 0.05
Nodes (49): argparse, asyncpg, fresh_client(), Handler, functools, hashlib, http_server, ipaddress (+41 more)

### Community 76 - "Оставшиеся риски и решения"
Cohesion: 0.22
Nodes (8): P1/P2 — частичный успех внешней операции требует сверки, P1 — административные права зависят от тарифа, P1 — биллинг и панели не образуют одну транзакцию, P1 — пароли панелей не защищены шифрованием приложения, P2 — мониторинг и производительность, P2 — старые ошибки оплат без ожидающих задач, P2 — эксплуатация и воспроизводимость, Оставшиеся риски и решения

### Community 77 - "Приёмка услуги «Обход белых списков» — 5 октября 2026"
Cohesion: 0.15
Nodes (13): 10. Заключение, 19. Перенос клиентов при смене целевого inbound (2026-10-06, P1 ревью), 1. Итог, 20. Повторная приёмка на реальных панелях (2026-10-06), 21. Исправленная 3x-ui и подготовка Happ — 6 октября 2026, 22. Финальное сохранение расхода — локальные тесты пропущены, 23. Обновление рабочей whitelist-панели — 6 октября 2026, 24. Подключение и массовое включение — 6 октября 2026 (+5 more)

### Community 78 - "whitelist_background_e2e.py"
Cohesion: 0.07
Nodes (41): BaseException, Acts, _async(), describe(), DiesOnFirstChange, die(), docker(), expect_poll() (+33 more)

### Community 79 - "Финальное сохранение расхода 3x-ui — 6 октября 2026"
Cohesion: 0.33
Nodes (5): Границы гарантии, Изменения, Проверки и исторические результаты, Статус, Финальное сохранение расхода 3x-ui — 6 октября 2026

### Community 80 - "ClientServerMapping"
Cohesion: 0.11
Nodes (16): ClientServerMapping, MockIpProvider, Mock-провайдер для тестов: возвращает заранее заданные IP по server_id., Реальный провайдер: берёт IP клиента из журнала панели 3x-ui., XuiIpProvider, Удаляет клиента с сервера по сохранённым привязкам., pytest_asyncio, admin() (+8 more)

### Community 82 - "_utcnow"
Cohesion: 0.25
Nodes (4): datetime, Клиенты, которым пора слать уведомление об окончании. Берём тех, у кого задан…, Сохраняет результат фоновой проверки доступности сервера., _utcnow()

### Community 84 - "models.py"
Cohesion: 0.09
Nodes (37): Base, Базовый класс для всех ORM-моделей., TimestampMixin, AttachmentType, AuditLog, PaymentAttachment, Пакет покупки трафика «Обход белых списков» (настраивается админом)., TrafficPackage (+29 more)

### Community 85 - "Динамические названия whitelist — 6 октября 2026"
Cohesion: 0.25
Nodes (5): Динамические названия whitelist — 6 октября 2026, Контракт и обновление, Реализация, Резервные копии и откат, Удалённая приёмка

### Community 86 - "PaymentRequest"
Cohesion: 0.18
Nodes (10): PaymentRequest, Берёт заявку с блокировкой строки (SELECT ... FOR UPDATE). На Postgres…, Удаляет заявку (вместе с вложениями по каскаду)., Последняя успешная (применённая/подтверждённая) оплата пользователя.…, _payment(), parametrize, Приёмка: происхождение текущего доступа при выдаче услуги нынешним…, test_origin_of_current_access() (+2 more)

### Community 87 - "EncryptedString"
Cohesion: 0.25
Nodes (7): EncryptedString, Any, Прозрачно шифрует значение при записи и расшифровывает при чтении. - Если…, Важные инженерные правила проекта, Выполненные проверки, 5. Миграции и резервная копия (PostgreSQL 16.15), TypeDecorator

### Community 88 - "Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026"
Cohesion: 0.50
Nodes (3): Прогон до исправления (SubHub `d9a2c80` + незакоммиченные правки, не относящиеся к задаче), Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026, Финальный прогон после исправления

### Community 89 - "whitelist.py"
Cohesion: 0.09
Nodes (43): Журнал выдач/начислений/корректировок, привязанных к исходной операции. Выдача…, WhitelistLedger, access_state(), AccessState, admin_summary(), AdminSummary, _append_note(), apply_event() (+35 more)

### Community 90 - "reconcile_cycle"
Cohesion: 0.14
Nodes (13): _BatchResult, _finish_reconcile(), Итог обхода учётов (накапливается между запусками, если обход прерывали).…, Учёты, чьё состояние этим обходом не подтверждено. Удалённые (``skipped_gone``)…, Следующая пачка учётов: стабильный курсор по id, а не по изменяемой метке., Читает пачку одной сессией панели и сверяет учёты по одному. Сбой одного учёта…, Один повторный проход по учётам, изменившимся между чтением и сверкой., Полный обход учётов whitelist-сервера ограниченными пачками. Пачки берутся по… (+5 more)

### Community 91 - "test_verdicts_agree_with_subhub_link_builder"
Cohesion: 0.40
Nodes (5): skipif, Path, Проверка против исходников SubHub (не рабочего экземпляра и его config.yaml)., _subhub_runner(), test_verdicts_agree_with_subhub_link_builder()

### Community 92 - "Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026"
Cohesion: 0.33
Nodes (5): 1. 3x-ui v3.9.0 (`ghcr.io/mhsanaei/3x-ui:v3.9.0`), финальный прогон — 25 OK, 5 FAIL, 2. 3x-ui v3.9.0, повтор S6, S6b, S7 с исправленным расчётом — 5 OK, 0 FAIL, 3. 3x-ui v3.5.0 (`ghcr.io/mhsanaei/3x-ui:v3.5.0`, Xray 26.7.11) — 5 OK, 9 FAIL, 4. Первый (предварительный) прогон на v3.9.0 — 24 OK, 6 FAIL, Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026

### Community 93 - "FakeMessage"
Cohesion: 0.40
Nodes (3): FakeMessage, Заменитель Message: запоминает ответы., test_non_admin_admin_command_denied()

### Community 94 - "Production deployment — 2026-10-06"
Cohesion: 0.33
Nodes (5): Backups and rollback, Checks after deployment, Deployment incidents and limits, Production deployment — 2026-10-06, Release

### Community 95 - "Q: собери контекст проекта"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: собери контекст проекта, Source Nodes

### Community 97 - "._clean_bot_token"
Cohesion: 0.33
Nodes (3): Разрешает задавать ADMIN_TELEGRAM_IDS как строку '1,2,3' или одно число., Убирает пробелы и обрамляющие кавычки вокруг токена., field_validator

### Community 98 - "SubHubClient"
Cohesion: 0.10
Nodes (24): build_happ_import_url(), Exception, Resolve the first panel identity known to SubHub. Older bot records can have a…, Base error for the internal SubHub integration., The panels have not exposed this identity to SubHub yet., The identity exists, but currently has no active nodes., Build a signed HTTPS trampoline for importing a legacy subscription., Small authenticated client for the SubHub admin API. Subscription URLs and… (+16 more)

### Community 99 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 100 - "devDependencies"
Cohesion: 0.40
Nodes (5): devDependencies, typescript, vite, @vitejs/plugin-vue, vue-tsc

### Community 102 - "Обновление whitelist-панели — 6 октября 2026"
Cohesion: 0.22
Nodes (8): DNS и TLS, Границы проверки, Итоговая удалённая приёмка, Обновление whitelist-панели — 6 октября 2026, Остановка systemd, Первая удалённая приёмка, Развёртывание, Резервная копия и откат

### Community 103 - "admin_nav"
Cohesion: 0.07
Nodes (40): aiogram_exceptions, aiogram_methods, aiogram_types, admin_nav(), _edit_panel(), on_payment_action(), callback_query, CallbackQuery (+32 more)

### Community 104 - "Обновление production — 4 октября 2026"
Cohesion: 0.25
Nodes (6): PAY-1C3F1344, Внедрено, Дополнительный дефект, обнаруженный при приёмке, Незавершённые операции, Обновление production — 4 октября 2026, Проверки и резервирование

### Community 107 - "PaymentStatus"
Cohesion: 0.11
Nodes (31): Пробный доступен, если им не пользовались и подписку никогда не оформляли., _trial_available(), PaymentStatus, PaymentRepository, Число применённых оплат подписки (покупки трафика не учитываются)., confirm_payment(), Идемпотентное подтверждение оплаты администратором. Повторный вызов для уже…, main() (+23 more)

### Community 109 - "stack.sh"
Cohesion: 0.57
Nodes (5): running(), stack.sh script, start_panel(), start_subhub(), subhub_config()

### Community 111 - "scripts"
Cohesion: 0.50
Nodes (4): scripts, build, dev, preview

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

### Community 120 - "record"
Cohesion: 0.10
Nodes (33): Any, AsyncSession, Записывает событие в audit_logs., record(), choose_inbound(), check_inbound(), _check_vless_reality(), describe() (+25 more)

### Community 121 - "Проверка исправленной 3x-ui — 6 октября 2026"
Cohesion: 0.22
Nodes (8): Как повторить, Неуспешные промежуточные прогоны, Область проверки, Ограничения учёта и отключения, Проверка исправленной 3x-ui — 6 октября 2026, Проверки, Сборка и патч, Следующий этап

### Community 127 - "graphify reference: extra exports and benchmark"
Cohesion: 0.20
Nodes (9): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000) (+1 more)

### Community 129 - "test_payment_kind_conflict.py"
Cohesion: 0.20
Nodes (23): aiogram_fsm_state, PlanCallback, Callback выбора тарифа пользователем. code — код тарифа из PLANS (1m/6m/12m)…, ProofStates, select_plan(), active_user(), _open_count(), _package() (+15 more)

### Community 130 - "_Crash"
Cohesion: 0.40
Nodes (3): RuntimeError, _Crash, Процесс завершился после запроса к панели, до commit.

### Community 131 - "session"
Cohesion: 0.21
Nodes (11): _maker(), _maker_for(), async_sessionmaker, AsyncSession, fixture, Подменяет фоновые циклы метками: видно, какие из них запустил…, БД в файле с отдельными соединениями у теста и у фонового worker'а. Общее…, session() (+3 more)

### Community 132 - "Повторная приёмка whitelist — 6 октября 2026"
Cohesion: 0.22
Nodes (7): D-3: потеря учёта подтверждена на штатном образе, Версии и изоляция, Вывод, Изменения средств приёмки, Ограничения, Повторная приёмка whitelist — 6 октября 2026, Следующий шаг

### Community 135 - "sharing_summary"
Cohesion: 0.33
Nodes (6): items: список кортежей (VpnClient, SharingStatus)., Полный краткий отчёт по IP-наблюдениям всех VPN-клиентов., sharing_all(), sharing_detail(), sharing_level_label(), sharing_summary()

### Community 136 - "wl_server"
Cohesion: 0.22
Nodes (5): panel(), fixture, service_on(), std_target(), wl_server()

### Community 137 - "parametrize"
Cohesion: 0.33
Nodes (6): parametrize, test_parse_server_line_rejects_invalid(), test_settings_rejects_dangerous_numeric_values(), test_unknown_or_forged_plan_code_rejected(), test_validate_server_name_rejects_invalid(), test_validate_subscription_base_rejects_invalid()

### Community 138 - "Приёмка на Android / Happ 4.6.0"
Cohesion: 0.29
Nodes (6): Подготовленный Wi-Fi стенд, Приёмка на Android / Happ 4.6.0, Протокол, Сверка после подтверждения пользователя, Условия начала, Шаги

### Community 140 - "Повторное ревью — 6 октября 2026"
Cohesion: 0.22
Nodes (8): P1: неопределённый учёт скрывает сброс счётчика и увеличивает квоту, P1: смена целевого inbound не переносит существующих пользователей, P2: отключение health polling отключает восстановление очереди, Spec, Standards / корректность, Выполненные проверки, Повторное ревью — 6 октября 2026, Что подтверждено и что остаётся перед внедрением

### Community 141 - "Server"
Cohesion: 0.07
Nodes (29): connection_overview(), Unified SubHub connection screen with live server availability., server_button_label(), Server, Меняет только имя, сохраняя сервер и все его связи., Меняет URL подписки, не затрагивая связи сервера., Удаляет сервер вместе с inbound'ами и привязками (каскад). Коллекции грузим…, Включённые серверы. По умолчанию — только обычные (безлимитные). (+21 more)

### Community 143 - "Ограниченное подключение whitelist к production — 6 октября 2026"
Cohesion: 0.29
Nodes (6): Изменения, Инциденты подготовки, Ограниченное подключение whitelist к production — 6 октября 2026, Проверки, Резервные копии и откат, Состояние

### Community 146 - "web_smoke.py"
Cohesion: 0.09
Nodes (23): _command_name(), _describe_message(), Message, get_engine(), get_session(), get_sessionmaker(), async_sessionmaker, AsyncSession (+15 more)

### Community 147 - "_server_health_poller"
Cohesion: 0.22
Nodes (6): Фоновая периодическая проверка доступности серверов 3x-ui. Очередь применения…, _server_health_poller(), pending_applied(), subhub_sync(), Очередь обслуживает только worker: при включённом health polling обработки нет…, test_health_poller_no_longer_processes_whitelist_queue()

### Community 150 - "Включение whitelist для действующих пользователей — 6 октября 2026"
Cohesion: 0.40
Nodes (4): Включение whitelist для действующих пользователей — 6 октября 2026, Особенность существующей идентичности, Резервные копии и ограничения отката, Результат

### Community 151 - "test_subscription_delete.py"
Cohesion: 0.23
Nodes (9): _FakeBot, _FakeMessage, _FakeState, Any, AsyncSession, test_admin_delete_subscription_uses_client_id_not_telegram_id(), test_delete_subscription_keeps_local_client_on_panel_failure(), test_delete_subscription_removes_panel_and_local_client() (+1 more)

### Community 154 - "whitelist_inbounds.py"
Cohesion: 0.17
Nodes (10): cryptography_hazmat_primitives, cryptography_hazmat_primitives_asymmetric_x25519, Как формируется клиент, Настройка серверов и авто-провижининг, Перенос пользователей, существовавших до бота, Шаг 1. Добавить серверы, Шаг 2. Импортировать inbound'ы каждого сервера, hysteria() (+2 more)

## Knowledge Gaps
- **226 isolated node(s):** `credentials`, `dvpn/site`, `name`, `version`, `private` (+221 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1049 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `test_payment_kind_conflict.py`, `provisioning.py`, `PanelUpdater`, `test_broadcast.py`, `test_whitelist.py`, `Settings`, `sharing_summary`, `test_whitelist_reconcile.py`, `billing.py`, `test_whitelist_bot.py`, `test_notify_swallows_telegram_api_errors`, `test_review_regressions.py`, `test_whitelist_pg.py`, `web_smoke.py`, `utcnow`, `test_subscription_delete.py`, `VpnClientRepository`, `Bot`, `create_request`, `web_bridge.py`, `AsyncSession`, `MockPanelUpdater`, `test_ux.py`, `QuotaClientState`, `test_security.py`, `notify.py`, `user_handlers.py`, `texts.py`, `bind_requests.py`, `test_plans.py`, `IsAdmin`, `VpnClient`, `whitelist_e2e.py`, `whitelist_background_e2e.py`, `ClientServerMapping`, `models.py`, `whitelist.py`, `admin_nav`, `PaymentStatus`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `Server` connect `Server` to `provisioning.py`, `PanelUpdater`, `test_whitelist.py`, `Settings`, `user_overview`, `keyboards.py`, `test_whitelist_reconcile.py`, `wl_server`, `test_whitelist_bot.py`, `get_active_server`, `test_review_regressions.py`, `test_whitelist_pg.py`, `web_smoke.py`, `pytest`, `utcnow`, `_push`, `VpnClientRepository`, `XuiPanelUpdater`, `import_inbounds`, `User`, `web_bridge.py`, `test_whitelist_xui.py`, `MockPanelUpdater`, `xui_updater.py`, `Контекст проекта`, `test_ux.py`, `QuotaClientState`, `test_whitelist_inbound_compat.py`, `_wl_state`, `texts.py`, `bind_requests.py`, `ClientServerMapping`, `models.py`, `EncryptedString`, `whitelist.py`, `reconcile_cycle`, `admin_nav`, `PaymentStatus`, `record`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Why does `MockPanelUpdater` connect `MockPanelUpdater` to `test_whitelist_retarget.py`, `provisioning.py`, `PanelUpdater`, `test_payment_kind_conflict.py`, `test_whitelist.py`, `user_overview`, `wl_server`, `test_whitelist_reconcile.py`, `test_whitelist_bot.py`, `Повторное ревью — 6 октября 2026`, `Server`, `test_review_regressions.py`, `test_whitelist_pg.py`, `web_smoke.py`, `_server_health_poller`, `main.py`, `test_subscription_delete.py`, `_push`, `VpnClientRepository`, `XuiPanelUpdater`, `_PoisonedPanel`, `Bot`, `User`, `create_request`, `test_whitelist_queue_worker.py`, `QuotaClientState`, `test_whitelist_inbound_compat.py`, `_wl_state`, `test_security.py`, `bind_requests.py`, `test_subhub_trigger.py`, `Приёмка услуги «Обход белых списков» — 5 октября 2026`, `ClientServerMapping`, `models.py`, `PaymentRequest`, `SubHubClient`, `PaymentStatus`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 171 inferred relationships involving `User` (e.g. with `add_inbound()` and `admin_add_server_line()`) actually correct?**
  _`User` has 171 INFERRED edges - model-reasoned connections that need verification._
- **Are the 93 inferred relationships involving `VpnClient` (e.g. with `notify_user_extended()` and `access_extended()`) actually correct?**
  _`VpnClient` has 93 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `MockPanelUpdater` (e.g. with `ClientServerMapping` and `Server`) actually correct?**
  _`MockPanelUpdater` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 57 inferred relationships involving `Server` (e.g. with `_finalize_new_server()` and `_finalize_whitelist_server()`) actually correct?**
  _`Server` has 57 INFERRED edges - model-reasoned connections that need verification._
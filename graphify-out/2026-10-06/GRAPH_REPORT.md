# Graph Report - VpnBot  (2026-10-06)

## Corpus Check
- 194 files · ~206,099 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 23 file(s) not represented in the graph (top: (none) 9, .example 3, .patch 3)

## Summary
- 3123 nodes · 11126 edges · 158 communities (139 shown, 19 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1409 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `520d65e2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_whitelist_retarget.py
- provisioning.py
- PanelUpdater
- user_handlers.py
- test_whitelist.py
- Panel
- admin_handlers.py
- record
- keyboards.py
- test_whitelist_reconcile.py
- billing.py
- FakeState
- test_xui_updater.py
- FakeBot
- alembic
- PendingServerUpdate
- test_whitelist_pg.py
- XuiClient
- main.go
- App.vue
- config.py
- main.py
- fmt_gb
- utcnow
- whitelist.py
- test_provisioning.py
- XuiPanelUpdater
- import_inbounds
- _describe_event
- Protocol
- xui_traffic_d3.py
- User
- Контекст проекта
- VpnClientRepository
- create_request
- web_bridge.py
- test_whitelist_queue_worker.py
- test_whitelist_xui.py
- AsyncSession
- MockPanelUpdater
- package.json
- subhub_quota_e2e.py
- compilerOptions
- main_test.go
- api
- Контекст проекта
- .auth
- test_ux.py
- Задание агенту: услуга «Обход белых списков» в VpnBot
- app
- main
- PanelUpdateError
- web_preview.mjs
- ServerInbound
- _wl_state
- What You Must Do When Invoked
- test_security.py
- test_xui_client.py
- test_expiry.py
- AsyncSession
- whitelist_migration_check.py
- Telegram VPN Billing Bot
- Report
- D VPN — личный кабинет
- texts.py
- BindRequestRepository
- test_set_volume_is_shown_as_entered
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
- _phases
- Финальное сохранение расхода 3x-ui — 6 октября 2026
- ClientServerMapping
- menu_nav
- scenario
- AGENTS.md
- models.py
- .confirmed
- PaymentRequest
- EncryptedString
- Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026
- QuotaClientState
- reconcile_cycle
- test_ui.py
- Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026
- InlineKeyboardMarkup
- Production deployment — 2026-10-06
- Q: собери контекст проекта
- check_server
- Settings
- SubHubClient
- graphify reference: query, path, explain
- select_plan
- answer
- Обновление whitelist-панели — 6 октября 2026
- whitelist_admin
- Обновление production — 4 октября 2026
- whitelist_e2e_2026-10-05.md
- find_panel_client
- PaymentStatus
- sh
- stack.sh
- whitelist_migration_2026-10-05.md
- scripts
- .panel_changes
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- ref_node_fs
- Ревью VpnBot — 4 октября 2026
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- whitelist_compat.py
- Проверка исправленной 3x-ui — 6 октября 2026
- extraction-spec.md
- graphify reference: extra exports and benchmark
- api.ts
- test_payment_kind_conflict.py
- _Crash
- session
- Повторная приёмка whitelist — 6 октября 2026
- vue
- conftest.py
- sharing_report
- test_whitelist_retarget_bot.py
- _parse_server_line
- Приёмка на Android / Happ 4.6.0
- delete_user_subscription
- Повторное ревью — 6 октября 2026
- Server
- recover_confirmed_payments
- Ограниченное подключение whitelist к production — 6 октября 2026
- ProofStates
- _cancel_payment
- env.py
- test_health_poller_no_longer_processes_whitelist_queue
- notify_user_rejected
- subscriptions.py
- Включение whitelist для действующих пользователей — 6 октября 2026
- _FakeMessage
- .bot
- _NoLocalLocks
- Настройка серверов и авто-провижининг
- active_user
- _PoisonedPanel
- admin_server_keyboard

## God Nodes (most connected - your core abstractions)
1. `User` - 272 edges
2. `MockPanelUpdater` - 153 edges
3. `VpnClient` - 151 edges
4. `Server` - 145 edges
5. `Settings` - 141 edges
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
- `Смена целевого inbound и перенос клиентов (2026-10-06)` --references--> `_push()`  [INFERRED]
  docs/WHITELIST_SERVICE.md → app/services/whitelist.py
- `Как формируется клиент` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py

## Import Cycles
- None detected.

## Communities (158 total, 19 thin omitted)

### Community 0 - "test_whitelist_retarget.py"
Cohesion: 0.15
Nodes (46): process_due(), Фоновая очередь: применяет несинхронизированные состояния с backoff. Кроме…, _add_candidate(), _available(), test_claim_command_releases_legacy_attachment(), test_whitelist_check_reports_actual_placement(), _choose(), _CrashAfterApply (+38 more)

### Community 1 - "provisioning.py"
Cohesion: 0.11
Nodes (43): ServerUpdateResult, apply_access(), apply_access_to_server(), bind_existing_client(), bind_user_by_public_id(), BindResult, _build_spec(), client_email() (+35 more)

### Community 2 - "PanelUpdater"
Cohesion: 0.12
Nodes (24): PanelUpdater, Интерфейс работы с клиентом в панели. Реализуется как mock (для тестов/MVP) и…, Читает клиента и его счётчик трафика (None — клиента нет)., Создаёт/обновляет клиента с квотой и проверяет результат чтением.…, Снимает привязки клиента к ``inbound_ids`` (счётчик сохраняется). Проверяет…, adjust_balance(), after_access_change(), _append_note() (+16 more)

### Community 3 - "user_handlers.py"
Cohesion: 0.10
Nodes (21): aiogram_exceptions, aiogram_filters, aiogram_types, BroadcastResult, Рассылает текстовое сообщение всем пользователям. Сообщение отправляется…, send_broadcast(), _is_valid_public_id(), parse_subhub_subscription_token() (+13 more)

### Community 4 - "test_whitelist.py"
Cohesion: 0.09
Nodes (74): AwaitingCredit, list_open_events(), Сохранённое начисление, ещё не сверенное с расходом., Остатки пользователя; при доступной панели — с актуальной сверкой. Чтение…, Неприменённые события учёта пользователя в порядке возникновения., user_overview(), 3.1. Бесплатный пакет и доступ, 3.2. Купленный трафик (+66 more)

### Community 5 - "Panel"
Cohesion: 0.11
Nodes (9): admin_servers(), 14. Исправление D-2: SubHub собирается без ручной установки greenlet (результаты от 2026-10-05, после приёмки), Panel, Прямой доступ к тестовой панели — для проверок и действий «вручную в панели»., Разрешает трафик к частной подсети стенда — только на тестовых панелях.…, VLESS + REALITY (TCP), как у рабочих серверов; цель — локальный TLS 1.3., {'body': тело клиента, 'inboundIds': [...], 'traffic': client_traffics|None}., Изменение клиента «вручную в панели» (тот же API, что у веб-интерфейса). (+1 more)

### Community 6 - "admin_handlers.py"
Cohesion: 0.12
Nodes (56): aiogram_fsm_context, add_inbound(), add_server(), admin_add_server_cancel(), admin_add_server_line(), admin_broadcast_cancel(), admin_broadcast_send(), admin_delete_subscription_by_client_id() (+48 more)

### Community 7 - "record"
Cohesion: 0.11
Nodes (24): Единственная строка настроек услуги (id = 1)., WhitelistConfig, Any, AsyncSession, Записывает событие в audit_logs., record(), choose_inbound(), claim_inbound() (+16 more)

### Community 8 - "keyboards.py"
Cohesion: 0.13
Nodes (27): aiogram_filters_callback_data, AdminCallback, BindCallback, OnboardCallback, PaymentCallback, PlanCallback, Callback админских действий над заявкой на привязку подписки., Callback выбора тарифа пользователем. code — код тарифа из PLANS (1m/6m/12m)… (+19 more)

### Community 9 - "test_whitelist_reconcile.py"
Cohesion: 0.06
Nodes (59): Состояние фоновой сверки расхода для админ-раздела (по данным процесса). «Обход…, reconcile_status_lines(), Состояние и наблюдаемость фоновой сверки (хранится в памяти процесса).…, Сколько прошло с завершения последнего обхода (в т. ч. с пропусками)., Верхняя граница возраста данных *сверенных* учётов последнего обхода., Сколько прошло с завершения последнего полностью подтверждённого обхода., Верхняя граница возраста данных всех учётов после последнего подтверждённого…, ReconcileStatus (+51 more)

### Community 10 - "billing.py"
Cohesion: 0.14
Nodes (38): _apply_panels(), _as_aware(), BillingError, BillingResult, compute_new_expiry(), _confirm_traffic(), _count_eligible_mappings(), _evaluate_panel_results() (+30 more)

### Community 11 - "FakeState"
Cohesion: 0.13
Nodes (12): Пользовательский раздел «Обход белых списков». action: home | refresh | buy…, WhitelistCallback, Step 7d - MCP server (only if --mcp flag), FakeState, Any, test_expired_user_gets_clear_explanation(), test_outage_payment_is_shown_as_awaiting_and_admin_resolves(), command() (+4 more)

### Community 12 - "test_xui_updater.py"
Cohesion: 0.17
Nodes (12): ProvisionInbound, Inbound сервера, к которому нужно привязать клиента., pytest_httpx, test_attach_success_without_membership_is_not_provisioning_success(), test_stale_inbound_is_rejected_before_client_creation(), _mock_auth(), HTTPXMock, _spec() (+4 more)

### Community 13 - "FakeBot"
Cohesion: 0.22
Nodes (9): 2. Стенд, async_sessionmaker, FakeBot, Any, AsyncSession, test_admin_notified_about_new_request(), test_confirm_then_notify_user(), test_first_purchase_sends_channel_prompt() (+1 more)

### Community 15 - "PendingServerUpdate"
Cohesion: 0.12
Nodes (19): PendingServerUpdate, PendingServerUpdateRepository, AsyncSession, apply_pending_for_server(), apply_pending_update(), _apply_to_server(), _as_aware(), _clear_payment_error_if_complete() (+11 more)

### Community 16 - "test_whitelist_pg.py"
Cohesion: 0.09
Nodes (38): Пакет покупки трафика «Обход белых списков» (настраивается админом)., TrafficPackage, attach_proof(), Прикрепляет подтверждение оплаты (текст/фото/документ) к заявке., get_account(), 4. Автоматические тесты, _ledger(), Приёмка: гонки услуги на PostgreSQL, не покрытые test_whitelist_pg. Те же… (+30 more)

### Community 17 - "XuiClient"
Cohesion: 0.06
Nodes (43): Any, Exception, Response, _quote_path_segment(), Авторизованный запрос: гарантирует login и при истёкшей сессии выполняет…, Берёт CSRF-токен с /csrf-token (3x-ui >= 3.2.x). На старых панелях endpoint…, Базовая ошибка взаимодействия с панелью 3x-ui., Read 3x-ui external endpoints for a reverse-proxied inbound. (+35 more)

### Community 18 - "main.go"
Cohesion: 0.07
Nodes (29): credentials, go_pkg_bytes, go_pkg_context, go_pkg_crypto_hmac, go_pkg_crypto_rand, go_pkg_crypto_sha256, go_pkg_crypto_subtle, go_pkg_crypto_tls (+21 more)

### Community 19 - "App.vue"
Cohesion: 0.07
Nodes (24): authTitles, awaiting, busy, code, comment, config, connection, days (+16 more)

### Community 20 - "config.py"
Cohesion: 0.09
Nodes (39): Any, get_settings(), decrypt(), encrypt(), _fernet(), is_encrypted(), Возвращает Fernet, выведенный из SECRET_KEY, либо None если ключ не задан.…, Шифрует строку. Без SECRET_KEY возвращает значение как есть (dev/тесты). (+31 more)

### Community 21 - "main.py"
Cohesion: 0.08
Nodes (39): aiogram, aiogram_client_default, aiogram_fsm_storage_memory, aiogram_utils_token, DbSessionMiddleware, Открывает сессию БД, получает/создаёт пользователя и кладёт их в data., build_root_router(), _anti_sharing_poller() (+31 more)

### Community 22 - "fmt_gb"
Cohesion: 0.15
Nodes (18): _parse_gb(), fmt_gb(), Остаток или расход в ГБ (1 ГБ = 1024³ байт), округлённый вниз: лишнего не…, whitelist_package_title(), gib_to_bytes(), Заданный объём в ГБ (без единицы, точка): так, как он вводился. Байты при вводе…, set_volume_gib_text(), 12. Исправление D-4 (результаты от 2026-10-05, после приёмки) (+10 more)

### Community 23 - "utcnow"
Cohesion: 0.15
Nodes (41): IpObservation, _active_clients(), collect_all(), collect_for_client(), compute_status(), _level_for(), list_all_statuses(), list_flagged() (+33 more)

### Community 24 - "whitelist.py"
Cohesion: 0.07
Nodes (43): Привязка клиента whitelist-панели к inbound'у, созданная самой услугой. Строка…, WhitelistPlacement, admin_summary(), AdminSummary, _applied_target(), _clear_placement(), _confirm_attach(), _defer() (+35 more)

### Community 25 - "test_provisioning.py"
Cohesion: 0.13
Nodes (28): MappingRepository, ensure_inbounds_imported(), Импортирует inbound'ы для включённых серверов, у которых их ещё нет. Нужно для…, days_from_now(), _panel_info(), AsyncSession, HTTPXMock, Ссылка содержит subId, а в панели email другой — оба поля сохраняются. (+20 more)

### Community 26 - "XuiPanelUpdater"
Cohesion: 0.10
Nodes (22): Создаёт/обновляет клиента сразу для всех inbound'ов сервера., Один клиент панели (глобальный по email), привязанный к её inbound'ам.…, ServerProvision, build_client_record(), client_record_body(), Извлекает model.Client из ответа ``clients/get``., Унифицированный объект клиента для нового client-API (3x-ui >= 3.2.x).…, _client_flows() (+14 more)

### Community 27 - "import_inbounds"
Cohesion: 0.16
Nodes (12): fetch_inbounds(), import_inbounds(), Any, Сверяет inbound'ы панели с локальными целями провижининга. Удалённые и…, Read inventory and external Hosts needed for whitelist XHTTP links., Сверка реестра с уже прочитанным списком (см. :func:`import_inbounds`)., reconcile_inbounds(), _ss_method() (+4 more)

### Community 28 - "_describe_event"
Cohesion: 0.22
Nodes (15): _command_name(), _describe_callback(), _describe_event(), _describe_message(), CallbackQuery, Message, TelegramObject, Chat (+7 more)

### Community 29 - "Protocol"
Cohesion: 0.11
Nodes (34): Protocol, ProvisionTarget, Описание клиента, которого нужно создать/обновить в конкретном inbound., build_client_object(), client_identifier(), _client_uuid_for_api(), _looks_like_db_id(), merge_client_record_for_update() (+26 more)

### Community 30 - "xui_traffic_d3.py"
Cohesion: 0.15
Nodes (36): Число строк и хэш упорядоченного содержимого прежних столбцов., snapshot(), accounted(), add_client(), container_started(), delta(), _disable_case(), Lab (+28 more)

### Community 31 - "User"
Cohesion: 0.16
Nodes (9): notify_admins_new_request(), User, Bot, Обработчики бота с сессией на каждое обновление, как у middleware., Пользователь создаёт заявку на подписку и присылает квитанцию., Сдвиг срока в БД вместо ожидания реального окончания (минуты, а не дни)., check_released(), main() (+1 more)

### Community 32 - "Контекст проекта"
Cohesion: 0.13
Nodes (14): Архитектура, Безопасность аутентификации (backend/main.go), Важные инженерные правила, Доменная модель (таблицы веб-части, в БД бота), Запуск, Контекст проекта, Конфигурация, Локальные артефакты (+6 more)

### Community 33 - "VpnClientRepository"
Cohesion: 0.09
Nodes (28): Удаляет пользователя и связанные записи (каскад в ORM)., Telegram ID всех пользователей, когда-либо запускавших бота., Генерирует короткий уникальный публичный ID пользователя., UserRepository, VpnClientRepository, AsyncSession, test_all_telegram_ids_returns_every_user(), test_user_role_downgrades_when_unlimited_mapping_is_removed() (+20 more)

### Community 34 - "create_request"
Cohesion: 0.11
Nodes (26): cancel_open_request(), create_request(), create_traffic_request(), _new_payment_code(), _open_request_for_update(), PaymentRequestError, PendingRequestExists, AsyncSession (+18 more)

### Community 35 - "web_bridge.py"
Cohesion: 0.06
Nodes (53): aiohttp, Base, Базовый класс для всех ORM-моделей., AttachmentType, PaymentAttachment, Durable per-admin Telegram delivery, retried independently of HTTP requests., WebAccount, WebDelivery (+45 more)

### Community 36 - "test_whitelist_queue_worker.py"
Cohesion: 0.20
Nodes (25): stop_background_tasks(), _expire(), _purchase_while_panel_down(), parametrize, Очередь применения whitelist-квот не зависит от проверки здоровья серверов.…, Ждёт, пока worker зафиксирует применение в БД (на панели оно видно раньше…, Завершение не зависает на зависшем запросе панели: задача отменяется., Недоступный SubHub не откатывает применение и не создаёт повторов. (+17 more)

### Community 37 - "test_whitelist_xui.py"
Cohesion: 0.21
Nodes (34): QuotaTarget, Абсолютное целевое состояние клиента с учётом трафика. ``total_bytes`` —…, 3.5. Учёт трафика и интеграция 3x-ui, _apply_existing(), _auth(), _body(), _inbound(), HTTPXMock (+26 more)

### Community 38 - "AsyncSession"
Cohesion: 0.14
Nodes (29): Журнал выдач/начислений/корректировок, привязанных к исходной операции. Выдача…, WhitelistLedger, apply_event(), classify_origin(), confirm_traffic_payment(), ensure_defaults(), get_config(), grant_for_subscription_payment() (+21 more)

### Community 39 - "MockPanelUpdater"
Cohesion: 0.17
Nodes (26): admin_payment_card(), payment_status_label(), MockPanelUpdater, datetime, Mock-реализация: ничего не делает либо имитирует сбой нужных серверов. Для…, Inbound удалён на панели: его привязки исчезают у всех клиентов., test_confirmation_resumes_saved_target_after_process_interruption(), _down() (+18 more)

### Community 40 - "package.json"
Cohesion: 0.11
Nodes (17): lucide-vue-next, typescript, vite, @vitejs/plugin-vue, vue-tsc, dependencies, lucide-vue-next, vue (+9 more)

### Community 41 - "subhub_quota_e2e.py"
Cohesion: 0.13
Nodes (22): import_control_inbound(), main(), panel_view(), Any, Path, Квота трафика 3x-ui → SubHub на реальной панели, без маскирующего…, Расход, не менявшийся между двумя чтениями с интервалом 12 с., Что SubHub получает из ``inbounds/list`` для клиента: settings и clientStats. (+14 more)

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

### Community 47 - "test_ux.py"
Cohesion: 0.10
Nodes (36): MenuCallback, Навигация по inline-меню (редактирование сообщения на месте). action: home |…, custom_emoji_id(), emoji_char(), Возвращает unicode-символ значка (без анимации)., Возвращает custom_emoji_id значка или None, если значок не найден., admin_home_keyboard(), cancel_payment_keyboard() (+28 more)

### Community 48 - "Задание агенту: услуга «Обход белых списков» в VpnBot"
Cohesion: 0.15
Nodes (12): 1. Контекст проекта, 2. Согласованное поведение услуги, 3. Сервер и настройки администратора, 4. Технический контракт учёта трафика, 5. Биллинг, конкуренция и восстановление, 6. Пользовательский интерфейс, 7. Обязательная проверка, 8. Порядок работы и сдача (+4 more)

### Community 49 - "app"
Cohesion: 0.29
Nodes (6): app, config, context.Context, github.com/jackc/pgx/v5/pgxpool.Pool, net/http.Client, pgx.Tx

### Community 50 - "main"
Cohesion: 0.22
Nodes (7): bucket, limiter, net/http.Handler, sync.Mutex, time.Time, env(), main()

### Community 51 - "PanelUpdateError"
Cohesion: 0.15
Nodes (8): effective_flow(), PanelUpdateError, Exception, Ошибка обновления клиента в панели., Пакетное чтение клиентов одной сессией панели., flow, который 3x-ui копирует при attach: первый непустой по id inbound'а., LostDetachResponse, Perform the real detach, then simulate losing its HTTP acknowledgement.

### Community 52 - "web_preview.mjs"
Cohesion: 0.29
Nodes (6): ref_node_fs_promises, ref_node_http, ref_node_path, ref_node_url, root, types

### Community 53 - "ServerInbound"
Cohesion: 0.10
Nodes (50): Inbound на панели сервера, в который нужно заводить клиентов. На одном сервере…, ServerInbound, build_provision_spec(), get_active_server(), Запускает услугу и выдаёт её нынешним активным пользователям. Повторный запуск…, Включённый whitelist-сервер (не более одного по уникальному индексу)., run_rollout(), server_ready() (+42 more)

### Community 54 - "_wl_state"
Cohesion: 0.18
Nodes (28): Применяет состояние учёта пользователя на whitelist-панели., Фоновая сверка расхода: обходит все учёты пачками по ``limit``. Возвращает…, reconcile_usage(), sync_user(), _available(), parametrize, Смена эпохи счётчика whitelist-панели при неприменённых событиях учёта. Внешний…, Пересоздание клиента: значение не уменьшилось, сменилась строка статистики. (+20 more)

### Community 55 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (25): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+17 more)

### Community 56 - "test_security.py"
Cohesion: 0.06
Nodes (50): forward_proof_to_admins(), UserRole, FakeBot, _make_payment(), _make_waiting(), _persist_payment(), AsyncSession, Тесты безопасности и устойчивости приложения. Покрывают ключевые свойства… (+42 more)

### Community 57 - "test_xui_client.py"
Cohesion: 0.22
Nodes (27): Ошибка авторизации в панели., XuiAuthError, HTTPXMock, test_login_error_does_not_leak_password(), _client(), _mock_csrf(), HTTPXMock, Регистрирует ответ /csrf-token (3x-ui 3.2.x запрашивает его перед login). (+19 more)

### Community 58 - "test_expiry.py"
Cohesion: 0.15
Nodes (19): notify_user_expiry(), Уведомление пользователя об окончании подписки. True — если доставлено., _as_aware(), process_expiry_notifications(), AsyncSession, datetime, Стадия уведомления по остатку времени до окончания. 0 — рано, 1 — остался день,…, Шлёт уведомления «за день / за час / в момент окончания». Каждая стадия… (+11 more)

### Community 59 - "AsyncSession"
Cohesion: 0.12
Nodes (26): bind_request_waiting(), no_open_request(), onboarding_legacy_question(), onboarding_send_link_prompt(), Приветствие. Использует HTML-разметку: ID завёрнут в <code> — Telegram копирует…, welcome(), admin_denied(), _attach_and_notify() (+18 more)

### Community 60 - "whitelist_migration_check.py"
Cohesion: 0.24
Nodes (19): alembic_config, alembic_script, alembic(), check(), docker(), downgrade_cycle(), dsn(), ensure_defaults_idempotent() (+11 more)

### Community 61 - "Telegram VPN Billing Bot"
Cohesion: 0.13
Nodes (12): Telegram VPN Billing Bot, Админ-команды, Антишеринг-мониторинг, Возможности, Граф кода (graphify), Единая подписка SubHub, Конфигурация, Локальный запуск (dev) (+4 more)

### Community 62 - "Report"
Cohesion: 0.25
Nodes (4): Any, Конфигурация xray-клиента: SOCKS 127.0.0.1:10808 → VLESS по ссылке., Report, xray_client_config()

### Community 63 - "D VPN — личный кабинет"
Cohesion: 0.25
Nodes (7): D VPN — личный кабинет, Архитектура, Запуск вместе с существующим ботом, Локальная разработка, Результаты проверки, Что реализовано, Эксплуатация

### Community 64 - "texts.py"
Cohesion: 0.05
Nodes (60): admin_nav(), HTML-строка с анимированным значком для вставки в текст сообщения., tg(), notify_first_purchase_channel(), notify_user_extended(), notify_user_subscription_deleted(), access_extended(), access_update_pending() (+52 more)

### Community 65 - "BindRequestRepository"
Cohesion: 0.09
Nodes (33): BindRequestStatus, BindRequest, Заявка на привязку существующей подписки (до внедрения бота)., BindRequestRepository, approve_request(), BindApproveResult, BindRequestError, create_request() (+25 more)

### Community 66 - "test_set_volume_is_shown_as_entered"
Cohesion: 0.13
Nodes (26): _after_applied_payment(), Уведомления и SubHub после применения; возвращает итог для администратора.…, notify_user_traffic_credited(), admin_history(), admin_pending(), admin_whitelist_home(), admin_whitelist_packages(), admin_whitelist_rollout_plan() (+18 more)

### Community 67 - "WhitelistAccount"
Cohesion: 0.12
Nodes (21): Бизнес-учёт трафика пользователя на whitelist-сервере. Остатки…, WhitelistAccount, apply_usage(), compute_target(), last_known_usage(), quota_room(), Списывает новый расход: сначала бесплатный, затем купленный остаток., Гарантированный объём квоты сверх контрольной точки. Остатки с неприменёнными… (+13 more)

### Community 71 - "test_subhub_trigger.py"
Cohesion: 0.12
Nodes (19): StreamReader, StreamWriter, _command(), LocalSubHub, _Maker, _paid(), parametrize, Быстрый триггер SubHub (POST /admin/sync) из обработчиков бота. Вместо SubHub —… (+11 more)

### Community 72 - "IsAdmin"
Cohesion: 0.21
Nodes (10): IsAdmin, TelegramObject, Пропускает событие только если пользователь — администратор., BaseFilter, test_is_admin_filter_accepts_admin(), test_is_admin_filter_rejects_missing_user(), test_is_admin_filter_rejects_regular_user(), test_settings_is_admin() (+2 more)

### Community 73 - "user_operation"
Cohesion: 0.31
Nodes (9): decorate(), wrapped(), user_operation(), 5. Конкуренция и восстановление, Восстановление после недоступной статистики, Фоновая сверка расхода: обход, гарантии, ограничения, test_user_operations_serialize_and_release_on_failure(), first() (+1 more)

### Community 74 - "VpnClient"
Cohesion: 0.23
Nodes (17): _is_active(), VpnClient, datetime, Клиенты, которым пора слать уведомление об окончании. Берём тех, у кого задан…, _utcnow(), has_active_timed_client(), has_client_access(), has_unlimited_bound_client() (+9 more)

### Community 75 - "whitelist_e2e.py"
Cohesion: 0.09
Nodes (36): Настраивает логирование приложения. - корневой логгер: WARNING (чтобы сторонние…, setup_logging(), build_happ_import_url(), Build a signed HTTPS trampoline for importing a legacy subscription., build_updater(), argparse, asyncio, asyncpg (+28 more)

### Community 76 - "Оставшиеся риски и решения"
Cohesion: 0.25
Nodes (8): P1/P2 — частичный успех внешней операции требует сверки, P1 — административные права зависят от тарифа, P1 — биллинг и панели не образуют одну транзакцию, P1 — пароли панелей не защищены шифрованием приложения, P2 — мониторинг и производительность, P2 — старые ошибки оплат без ожидающих задач, P2 — эксплуатация и воспроизводимость, Оставшиеся риски и решения

### Community 77 - "Приёмка услуги «Обход белых списков» — 5 октября 2026"
Cohesion: 0.18
Nodes (11): 10. Заключение, 19. Перенос клиентов при смене целевого inbound (2026-10-06, P1 ревью), 1. Итог, 20. Повторная приёмка на реальных панелях (2026-10-06), 21. Исправленная 3x-ui и подготовка Happ — 6 октября 2026, 22. Финальное сохранение расхода — локальные тесты пропущены, 23. Обновление рабочей whitelist-панели — 6 октября 2026, 24. Подключение и массовое включение — 6 октября 2026 (+3 more)

### Community 78 - "_phases"
Cohesion: 0.06
Nodes (37): BaseException, Acts, _async(), describe(), DiesOnFirstChange, die(), docker(), expect_poll() (+29 more)

### Community 79 - "Финальное сохранение расхода 3x-ui — 6 октября 2026"
Cohesion: 0.33
Nodes (5): Границы гарантии, Изменения, Проверки и исторические результаты, Статус, Финальное сохранение расхода 3x-ui — 6 октября 2026

### Community 80 - "ClientServerMapping"
Cohesion: 0.12
Nodes (6): ClientServerMapping, MockIpProvider, Mock-провайдер для тестов: возвращает заранее заданные IP по server_id., Реальный провайдер: берёт IP клиента из журнала панели 3x-ui., XuiIpProvider, Удаляет клиента с сервера по сохранённым привязкам.

### Community 81 - "menu_nav"
Cohesion: 0.12
Nodes (25): _back_button(), back_keyboard(), _btn(), free_proxies_keyboard(), install_guides_keyboard(), news_channel_keyboard(), Подтверждение сброса данных пользователя в боте., Гайды по установке клиента — ссылки на Telegraph. (+17 more)

### Community 82 - "scenario"
Cohesion: 0.10
Nodes (20): docker(), prepare(), Path, gb(), load_env(), main(), ms(), _package() (+12 more)

### Community 84 - "models.py"
Cohesion: 0.14
Nodes (22): app_bot, TimestampMixin, AuditLog, AuditRepository, app_services, Serialize access mutations per user, including commits and panel calls., dataclasses, datetime (+14 more)

### Community 85 - ".confirmed"
Cohesion: 0.40
Nodes (4): Каждый существующий учёт сверен: ни ошибок, ни пропусков., Доменная модель, Логика продления, Пользовательские сценарии

### Community 86 - "PaymentRequest"
Cohesion: 0.16
Nodes (7): PaymentRequest, PaymentRepository, Берёт заявку с блокировкой строки (SELECT ... FOR UPDATE). На Postgres…, Число применённых оплат подписки (покупки трафика не учитываются)., Удаляет заявку (вместе с вложениями по каскаду)., Последняя успешная (применённая/подтверждённая) оплата пользователя.…, _payment()

### Community 87 - "EncryptedString"
Cohesion: 0.25
Nodes (7): EncryptedString, Any, Прозрачно шифрует значение при записи и расшифровывает при чтении. - Если…, Важные инженерные правила проекта, Выполненные проверки, 5. Миграции и резервная копия (PostgreSQL 16.15), TypeDecorator

### Community 88 - "Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026"
Cohesion: 0.50
Nodes (3): Прогон до исправления (SubHub `d9a2c80` + незакоммиченные правки, не относящиеся к задаче), Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026, Финальный прогон после исправления

### Community 89 - "QuotaClientState"
Cohesion: 0.11
Nodes (32): QuotaClientState, Прочитанное с панели состояние клиента и его счётчика трафика., access_state(), AccessState, _apply_quota(), _aware(), _consistent_anchor(), _Context (+24 more)

### Community 90 - "reconcile_cycle"
Cohesion: 0.15
Nodes (14): _BatchResult, _finish_reconcile(), Итог обхода учётов (накапливается между запусками, если обход прерывали).…, Учёты, чьё состояние этим обходом не подтверждено. Удалённые (``skipped_gone``)…, Следующая пачка учётов: стабильный курсор по id, а не по изменяемой метке., Читает пачку одной сессией панели и сверяет учёты по одному. Сбой одного учёта…, Один повторный проход по учётам, изменившимся между чтением и сверкой., Полный обход учётов whitelist-сервера ограниченными пачками. Пачки берутся по… (+6 more)

### Community 91 - "test_ui.py"
Cohesion: 0.29
Nodes (7): aiogram_methods, TelegramBadRequest, _bad_request(), _Callback, Exception, test_answer_callback_ignores_expired_query_id(), test_answer_callback_reraises_other_bad_request()

### Community 92 - "Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026"
Cohesion: 0.33
Nodes (5): 1. 3x-ui v3.9.0 (`ghcr.io/mhsanaei/3x-ui:v3.9.0`), финальный прогон — 25 OK, 5 FAIL, 2. 3x-ui v3.9.0, повтор S6, S6b, S7 с исправленным расчётом — 5 OK, 0 FAIL, 3. 3x-ui v3.5.0 (`ghcr.io/mhsanaei/3x-ui:v3.5.0`, Xray 26.7.11) — 5 OK, 9 FAIL, 4. Первый (предварительный) прогон на v3.9.0 — 24 OK, 6 FAIL, Протокол: D-3 — учёт трафика 3x-ui после запуска панели и перезапусков Xray — 6 октября 2026

### Community 93 - "InlineKeyboardMarkup"
Cohesion: 0.20
Nodes (18): _adm(), admin_add_server_type_keyboard(), admin_back_keyboard(), admin_confirm_delete_keyboard(), admin_servers_keyboard(), admin_whitelist_back_keyboard(), admin_whitelist_keyboard(), admin_whitelist_package_keyboard() (+10 more)

### Community 94 - "Production deployment — 2026-10-06"
Cohesion: 0.33
Nodes (5): Backups and rollback, Checks after deployment, Deployment incidents and limits, Production deployment — 2026-10-06, Release

### Community 95 - "Q: собери контекст проекта"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: собери контекст проекта, Source Nodes

### Community 96 - "check_server"
Cohesion: 0.17
Nodes (5): check_server(), Проверяет доступность панели 3x-ui одного сервера. Успешный login считается…, test_health_check_server_returns_false_on_error(), login(), test_health_check_server_returns_true_on_success()

### Community 97 - "Settings"
Cohesion: 0.10
Nodes (19): provision_user(), notify_admins_new_bind_request(), admin_provision_result(), bind_request_received(), connection_unavailable(), onboarding_invalid_link(), onboard_legacy_link(), Разрешает задавать ADMIN_TELEGRAM_IDS как строку '1,2,3' или одно число. (+11 more)

### Community 98 - "SubHubClient"
Cohesion: 0.10
Nodes (19): Exception, Resolve the first panel identity known to SubHub. Older bot records can have a…, Base error for the internal SubHub integration., The panels have not exposed this identity to SubHub yet., The identity exists, but currently has no active nodes., Small authenticated client for the SubHub admin API. Subscription URLs and…, ResolvedSubscription, SubHubClient (+11 more)

### Community 99 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 100 - "select_plan"
Cohesion: 0.22
Nodes (18): payment_created(), trial_already_used(), trial_failed(), trial_no_client(), answer_callback(), Отвечает на callback и игнорирует протухшие query-id после сетевых лагов., _activate_trial(), _edit() (+10 more)

### Community 101 - "answer"
Cohesion: 0.40
Nodes (6): answer(), edit(), Any, CallbackQuery, Безопасно редактирует сообщение callback'а. ``callback.message`` может быть…, Безопасно отправляет ответ в чат callback'а (если сообщение доступно).

### Community 102 - "Обновление whitelist-панели — 6 октября 2026"
Cohesion: 0.22
Nodes (8): DNS и TLS, Границы проверки, Итоговая удалённая приёмка, Обновление whitelist-панели — 6 октября 2026, Остановка systemd, Первая удалённая приёмка, Развёртывание, Резервная копия и откат

### Community 103 - "whitelist_admin"
Cohesion: 0.13
Nodes (20): _edit_panel(), on_bind_action(), on_payment_action(), callback_query, CallbackQuery, InlineKeyboardMarkup, Редактирует сообщение админ-панели, мягко гасит ошибки. parse_mode=None —…, whitelist_admin() (+12 more)

### Community 104 - "Обновление production — 4 октября 2026"
Cohesion: 0.25
Nodes (6): PAY-1C3F1344, Внедрено, Дополнительный дефект, обнаруженный при приёмке, Незавершённые операции, Обновление production — 4 октября 2026, Проверки и резервирование

### Community 106 - "find_panel_client"
Cohesion: 0.20
Nodes (12): find_panel_client(), _find_panel_client_by_sub_id(), list_panel_clients(), _panel_client_secret(), PanelClientInfo, _pick_secret(), Нормализованные данные существующего клиента панели., Возвращает список клиентов, уже существующих на панели сервера. (+4 more)

### Community 107 - "PaymentStatus"
Cohesion: 0.35
Nodes (17): PaymentStatus, confirm_payment(), Идемпотентное подтверждение оплаты администратором. Повторный вызов для уже…, _make_waiting_payment(), AsyncSession, test_confirm_applies_available_servers_and_queues_unavailable(), test_confirm_no_client_marks_failed(), test_confirm_payment_extends_expired() (+9 more)

### Community 108 - "sh"
Cohesion: 0.15
Nodes (10): 15. Лимит трафика 3x-ui → SubHub: единица `totalGB` и источник расхода (результаты от 2026-10-05, после приёмки), 2. Проверенный контракт 3x-ui, set_inbound(), main(), panel_call(), Новый контейнер панели: учётные данные, шаблон для частной сети, inbound., docker stop/start: новый процесс панели и новый процесс Xray., restart_later() (+2 more)

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

### Community 120 - "whitelist_compat.py"
Cohesion: 0.20
Nodes (16): check_inbound(), _check_vless_reality(), describe(), _foreign_flows(), InboundCompat, _json(), _public_key_available(), Any (+8 more)

### Community 121 - "Проверка исправленной 3x-ui — 6 октября 2026"
Cohesion: 0.22
Nodes (8): Как повторить, Неуспешные промежуточные прогоны, Область проверки, Ограничения учёта и отключения, Проверка исправленной 3x-ui — 6 октября 2026, Проверки, Сборка и патч, Следующий этап

### Community 127 - "graphify reference: extra exports and benchmark"
Cohesion: 0.25
Nodes (7): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 128 - "api.ts"
Cohesion: 0.33
Nodes (4): APIError, Configuration, Plan, Profile

### Community 129 - "test_payment_kind_conflict.py"
Cohesion: 0.34
Nodes (17): _open_count(), _package(), D-1: заявку с отправленной квитанцией нельзя превратить в заявку другого вида., _snapshot(), _subscription_with_proof(), test_conflicted_subscription_request_extends_once_and_adds_no_traffic(), test_conflicted_traffic_request_credits_traffic_once_and_no_subscription_time(), test_kind_switch_without_proof_still_converts_single_request() (+9 more)

### Community 130 - "_Crash"
Cohesion: 0.40
Nodes (3): RuntimeError, _Crash, Процесс завершился после запроса к панели, до commit.

### Community 131 - "session"
Cohesion: 0.21
Nodes (11): _maker(), _maker_for(), async_sessionmaker, AsyncSession, fixture, Подменяет фоновые циклы метками: видно, какие из них запустил…, БД в файле с отдельными соединениями у теста и у фонового worker'а. Общее…, session() (+3 more)

### Community 132 - "Повторная приёмка whitelist — 6 октября 2026"
Cohesion: 0.22
Nodes (7): D-3: потеря учёта подтверждена на штатном образе, Версии и изоляция, Вывод, Изменения средств приёмки, Ограничения, Повторная приёмка whitelist — 6 октября 2026, Следующий шаг

### Community 134 - "conftest.py"
Cohesion: 0.44
Nodes (9): pytest_asyncio, admin(), AsyncSession, datetime, fixture, server(), session(), user() (+1 more)

### Community 135 - "sharing_report"
Cohesion: 0.31
Nodes (9): ip_scan(), sharing_report(), items: список кортежей (VpnClient, SharingStatus)., Полный краткий отчёт по IP-наблюдениям всех VPN-клиентов., sharing_all(), sharing_detail(), sharing_disabled(), sharing_level_label() (+1 more)

### Community 136 - "test_whitelist_retarget_bot.py"
Cohesion: 0.15
Nodes (13): ops, FakeMessage, panel(), fixture, _callback(), _command(), Перенос клиентов при смене цели: админ-сценарии бота, SubHub и ops-сверка.…, test_choosing_target_moves_clients_notifies_subhub_and_shows_progress() (+5 more)

### Community 137 - "_parse_server_line"
Cohesion: 0.22
Nodes (9): _parse_server_line(), Парсит 'name|country|panel_url|username|password|[kind]|[sub]|[purpose]'.…, parametrize, test_parse_server_line_accepts_valid(), test_parse_server_line_rejects_invalid(), test_settings_rejects_dangerous_numeric_values(), test_validate_server_name_rejects_invalid(), test_validate_subscription_base_rejects_invalid() (+1 more)

### Community 138 - "Приёмка на Android / Happ 4.6.0"
Cohesion: 0.29
Nodes (6): Подготовленный Wi-Fi стенд, Приёмка на Android / Happ 4.6.0, Протокол, Сверка после подтверждения пользователя, Условия начала, Шаги

### Community 139 - "delete_user_subscription"
Cohesion: 0.31
Nodes (9): _delete_local_subscription(), delete_user_subscription(), AsyncSession, Удаляет VPN-подписку пользователя с панелей и из БД бота. История оплат, заявки…, SubscriptionDeleteResult, AsyncSession, test_delete_subscription_keeps_local_client_on_panel_failure(), test_delete_subscription_removes_panel_and_local_client() (+1 more)

### Community 140 - "Повторное ревью — 6 октября 2026"
Cohesion: 0.22
Nodes (8): P1: неопределённый учёт скрывает сброс счётчика и увеличивает квоту, P1: смена целевого inbound не переносит существующих пользователей, P2: отключение health polling отключает восстановление очереди, Spec, Standards / корректность, Выполненные проверки, Повторное ревью — 6 октября 2026, Что подтверждено и что остаётся перед внедрением

### Community 141 - "Server"
Cohesion: 0.08
Nodes (24): _finalize_whitelist_server(), Добавляет сервер услуги и сразу сверяет его inbound'ы. До успешной сверки с…, Server, Меняет только имя, сохраняя сервер и все его связи., Меняет URL подписки, не затрагивая связи сервера., Удаляет сервер вместе с inbound'ами и привязками (каскад). Коллекции грузим…, Включённые серверы. По умолчанию — только обычные (безлимитные)., Цели обычного provisioning: whitelist-сервер ведётся отдельно. (+16 more)

### Community 142 - "recover_confirmed_payments"
Cohesion: 0.33
Nodes (6): Resume durable payment intents after a process interruption., recover_confirmed_payments(), Прогон 1 — до исправлений (бот и SubHub без изменений этой задачи), Прогон 2 — SubHub исправлен (D-6), бот: исправлен D-5, исправления D-7 и D-8 временно сняты, Прогон 3 — финальный, все исправления, Протокол: R46 без принудительной синхронизации, фоновые циклы бота — 5 октября 2026

### Community 143 - "Ограниченное подключение whitelist к production — 6 октября 2026"
Cohesion: 0.29
Nodes (6): Изменения, Инциденты подготовки, Ограниченное подключение whitelist к production — 6 октября 2026, Проверки, Резервные копии и откат, Состояние

### Community 144 - "ProofStates"
Cohesion: 0.47
Nodes (5): aiogram_fsm_state, AdminStates, OnboardingStates, ProofStates, StatesGroup

### Community 145 - "_cancel_payment"
Cohesion: 0.40
Nodes (5): _cancel_payment(), Удаляет неподтверждённую заявку (без приложенного скриншота)., _DummyState, test_cancel_payment_deletes_unsubmitted(), test_cancel_payment_keeps_submitted()

### Community 146 - "env.py"
Cohesion: 0.40
Nodes (4): app_db, do_run_migrations(), run_migrations_online(), sqlalchemy_pool

### Community 148 - "notify_user_rejected"
Cohesion: 0.40
Nodes (5): notify_user_rejected(), payment_rejected(), proof_received(), test_payment_code_wrapped_in_code_tag(), test_web_user_gets_no_telegram_notification()

### Community 149 - "subscriptions.py"
Cohesion: 0.50
Nodes (4): collect_links(), AsyncSession, Возвращает список (метка, ссылка-подписка) по всем серверам пользователя. Для…, _sub_link()

### Community 150 - "Включение whitelist для действующих пользователей — 6 октября 2026"
Cohesion: 0.40
Nodes (4): Включение whitelist для действующих пользователей — 6 октября 2026, Особенность существующей идентичности, Резервные копии и ограничения отката, Результат

### Community 151 - "_FakeMessage"
Cohesion: 0.40
Nodes (3): _FakeBot, _FakeMessage, Any

### Community 152 - ".bot"
Cohesion: 0.50
Nodes (3): Запуск, Запуск через Docker Compose, API

### Community 153 - "_NoLocalLocks"
Cohesion: 0.50
Nodes (3): dict, _NoLocalLocks, Каждый вызов получает новый asyncio.Lock — как в отдельном процессе.

### Community 154 - "Настройка серверов и авто-провижининг"
Cohesion: 0.50
Nodes (4): Как формируется клиент, Настройка серверов и авто-провижининг, Перенос пользователей, существовавших до бота, Шаг 1. Добавить серверы

### Community 155 - "active_user"
Cohesion: 0.50
Nodes (4): active_user(), panel(), fixture, Пользователь с оплаченной подпиской: покупка трафика доступна.

### Community 157 - "admin_server_keyboard"
Cohesion: 0.67
Nodes (3): admin_server_keyboard(), Управление конкретным сервером., test_admin_server_keyboard_toggle_label()

## Knowledge Gaps
- **221 isolated node(s):** `credentials`, `dvpn/site`, `name`, `version`, `private` (+216 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1042 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Server` connect `Server` to `provisioning.py`, `PanelUpdater`, `test_whitelist.py`, `admin_handlers.py`, `record`, `keyboards.py`, `_parse_server_line`, `conftest.py`, `delete_user_subscription`, `test_whitelist_reconcile.py`, `test_whitelist_retarget_bot.py`, `test_xui_updater.py`, `PendingServerUpdate`, `test_whitelist_pg.py`, `config.py`, `utcnow`, `whitelist.py`, `test_provisioning.py`, `XuiPanelUpdater`, `import_inbounds`, `admin_server_keyboard`, `VpnClientRepository`, `web_bridge.py`, `test_whitelist_xui.py`, `MockPanelUpdater`, `Контекст проекта`, `test_ux.py`, `PanelUpdateError`, `ServerInbound`, `_wl_state`, `texts.py`, `BindRequestRepository`, `whitelist_e2e.py`, `ClientServerMapping`, `models.py`, `EncryptedString`, `QuotaClientState`, `reconcile_cycle`, `InlineKeyboardMarkup`, `check_server`, `whitelist_admin`, `find_panel_client`, `PaymentStatus`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Why does `User` connect `User` to `provisioning.py`, `user_handlers.py`, `test_whitelist.py`, `admin_handlers.py`, `sharing_report`, `conftest.py`, `test_whitelist_reconcile.py`, `billing.py`, `delete_user_subscription`, `FakeBot`, `PendingServerUpdate`, `test_whitelist_pg.py`, `_cancel_payment`, `config.py`, `utcnow`, `whitelist.py`, `test_provisioning.py`, `VpnClientRepository`, `create_request`, `web_bridge.py`, `AsyncSession`, `MockPanelUpdater`, `test_ux.py`, `test_security.py`, `test_expiry.py`, `AsyncSession`, `texts.py`, `BindRequestRepository`, `test_set_volume_is_shown_as_entered`, `WhitelistAccount`, `IsAdmin`, `whitelist_e2e.py`, `_phases`, `menu_nav`, `scenario`, `models.py`, `QuotaClientState`, `Settings`, `select_plan`, `whitelist_admin`, `PaymentStatus`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `Settings` connect `Settings` to `test_payment_kind_conflict.py`, `user_handlers.py`, `test_whitelist.py`, `admin_handlers.py`, `sharing_report`, `_parse_server_line`, `FakeState`, `Server`, `FakeBot`, `config.py`, `main.py`, `utcnow`, `User`, `VpnClientRepository`, `create_request`, `web_bridge.py`, `test_whitelist_queue_worker.py`, `MockPanelUpdater`, `test_ux.py`, `ServerInbound`, `test_security.py`, `AsyncSession`, `texts.py`, `test_set_volume_is_shown_as_entered`, `test_subhub_trigger.py`, `IsAdmin`, `VpnClient`, `whitelist_e2e.py`, `menu_nav`, `scenario`, `models.py`, `select_plan`, `whitelist_admin`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 171 inferred relationships involving `User` (e.g. with `add_inbound()` and `admin_add_server_line()`) actually correct?**
  _`User` has 171 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `MockPanelUpdater` (e.g. with `ClientServerMapping` and `Server`) actually correct?**
  _`MockPanelUpdater` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 92 inferred relationships involving `VpnClient` (e.g. with `notify_user_extended()` and `access_extended()`) actually correct?**
  _`VpnClient` has 92 INFERRED edges - model-reasoned connections that need verification._
- **Are the 57 inferred relationships involving `Server` (e.g. with `_finalize_new_server()` and `_finalize_whitelist_server()`) actually correct?**
  _`Server` has 57 INFERRED edges - model-reasoned connections that need verification._
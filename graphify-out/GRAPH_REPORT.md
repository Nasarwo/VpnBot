# Graph Report - VpnBot  (2026-09-17)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1538 nodes · 5112 edges · 71 communities (60 shown, 11 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 650 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7915e96b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 63
- Community 68
- Community 69

## God Nodes (most connected - your core abstractions)
1. `User` - 211 edges
2. `VpnClient` - 119 edges
3. `Settings` - 94 edges
4. `Server` - 91 edges
5. `VpnClientRepository` - 69 edges
6. `XuiClient` - 63 edges
7. `MockPanelUpdater` - 60 edges
8. `PaymentRepository` - 58 edges
9. `ServerRepository` - 58 edges
10. `UserRole` - 55 edges

## Surprising Connections (you probably didn't know these)
- `test_menu_callback_actions_are_strings()` --uses--> `MenuCallback`  [INFERRED]
  tests/test_security.py → app/bot/callbacks.py
- `fake_import()` --calls--> `ServerInbound`  [EXTRACTED]
  tests/test_trial.py → app/db/models.py
- `vpn_client()` --uses--> `Protocol`  [INFERRED]
  tests/conftest.py → app/db/enums.py
- `_mapping()` --uses--> `Protocol`  [INFERRED]
  tests/test_access.py → app/db/enums.py
- `test_confirm_applies_available_servers_and_queues_unavailable()` --uses--> `Protocol`  [INFERRED]
  tests/test_billing.py → app/db/enums.py

## Import Cycles
- None detected.

## Communities (71 total, 11 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (91): Inbound на панели сервера, в который нужно заводить клиентов. На одном сервере…, ServerInbound, MappingRepository, VpnClientRepository, PanelUpdateError, Exception, Ошибка обновления клиента в панели., apply_access() (+83 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (57): Protocol, ClientServerMapping, ProvisionInbound, ProvisionTarget, Описание клиента, которого нужно создать/обновить в конкретном inbound., Inbound сервера, к которому нужно привязать клиента., Один клиент панели (глобальный по email), привязанный к её inbound'ам.…, Создаёт/обновляет клиента сразу для всех inbound'ов сервера. (+49 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (65): admin_nav(), _edit_panel(), ip_scan(), on_payment_action(), CallbackQuery, Редактирует сообщение админ-панели, мягко гасит ошибки. parse_mode=None —…, HTML-строка с анимированным значком для вставки в текст сообщения., tg() (+57 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (38): BindRequestStatus, BindRequest, Заявка на привязку существующей подписки (до внедрения бота)., BindRequestRepository, approve_request(), BindApproveResult, BindRequestError, create_request() (+30 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (30): AsyncSession, Удаляет пользователя и связанные записи (каскад в ORM)., Telegram ID всех пользователей, когда-либо запускавших бота., Генерирует короткий уникальный публичный ID пользователя., UserRepository, BroadcastResult, Bot, Рассылает текстовое сообщение всем пользователям. Сообщение отправляется… (+22 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (45): aiogram_fsm_context, aiogram_fsm_state, AdminStates, OnboardingStates, ProofStates, bind_request_received(), no_open_request(), onboarding_invalid_link() (+37 more)

### Community 6 - "Community 6"
Cohesion: 0.15
Nodes (43): add_inbound(), add_server(), admin_add_server_cancel(), admin_add_server_line(), admin_broadcast_cancel(), admin_broadcast_send(), admin_delete_subscription_by_client_id(), admin_delete_subscription_cancel() (+35 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (32): _parse_server_line(), Парсит строку 'name|country|panel_url|username|password|[kind]|[sub]'.…, pytest_httpx, FakeBot, FakeMessage, parametrize, Тесты безопасности и устойчивости приложения. Покрывают ключевые свойства…, Порядок важен: для не-админа /admin проскакивает админ-роутер (фильтр IsAdmin… (+24 more)

### Community 8 - "Community 8"
Cohesion: 0.14
Nodes (40): _adm(), admin_back_keyboard(), admin_bind_keyboard(), admin_bind_retry_keyboard(), admin_confirm_delete_keyboard(), admin_home_keyboard(), admin_payment_keyboard(), admin_retry_keyboard() (+32 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (25): connection_overview(), Unified SubHub connection screen with live server availability., server_button_label(), Server, Меняет только имя, сохраняя сервер и все его связи., Меняет URL подписки, не затрагивая связи сервера., Удаляет сервер вместе с inbound'ами и привязками (каскад). Коллекции грузим…, Удаляет настроенный inbound. Возвращает число удалённых записей. (+17 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (37): _apply_panels(), _as_aware(), BillingError, BillingResult, compute_new_expiry(), _count_eligible_mappings(), _evaluate_panel_results(), expiry_to_ms() (+29 more)

### Community 11 - "Community 11"
Cohesion: 0.09
Nodes (25): build_happ_import_url(), Exception, Base error for the internal SubHub integration., Resolve the first panel identity known to SubHub. Older bot records can have a…, The panels have not exposed this identity to SubHub yet., The identity exists, but currently has no active nodes., Build a signed HTTPS trampoline for importing a legacy subscription., Small authenticated client for the SubHub admin API. Subscription URLs and… (+17 more)

### Community 12 - "Community 12"
Cohesion: 0.15
Nodes (35): PaymentStatus, confirm_payment(), Идемпотентное подтверждение оплаты администратором. Повторный вызов для уже…, MockPanelUpdater, Mock-реализация: ничего не делает либо имитирует сбой нужных серверов., _make_waiting_payment(), AsyncSession, test_confirm_applies_available_servers_and_queues_unavailable() (+27 more)

### Community 13 - "Community 13"
Cohesion: 0.10
Nodes (26): AuditLog, AuditRepository, Any, AsyncSession, Записывает событие в audit_logs., record(), _delete_local_subscription(), delete_user_subscription() (+18 more)

### Community 14 - "Community 14"
Cohesion: 0.09
Nodes (4): alembic, collections_abc, sqlalchemy, sqlalchemy_types

### Community 15 - "Community 15"
Cohesion: 0.11
Nodes (32): AdminCallback, Навигация по админ-панели (/admin). action: home | servers | server | rename |…, custom_emoji_id(), emoji_char(), Возвращает unicode-символ значка (без анимации)., Возвращает custom_emoji_id значка или None, если значок не найден., Главное меню под приветствием. Зависит от наличия активной подписки., welcome_menu() (+24 more)

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (24): aiohttp, get_settings(), _fernet(), Возвращает Fernet, выведенный из SECRET_KEY, либо None если ключ не задан.…, get_engine(), get_session(), get_sessionmaker(), AsyncSession (+16 more)

### Community 17 - "Community 17"
Cohesion: 0.10
Nodes (27): aiogram, aiogram_client_default, aiogram_fsm_storage_memory, aiogram_utils_token, build_root_router(), Настраивает логирование приложения. - корневой логгер: WARNING (чтобы сторонние…, setup_logging(), _anti_sharing_poller() (+19 more)

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (29): credentials, go_pkg_bytes, go_pkg_context, go_pkg_crypto_hmac, go_pkg_crypto_rand, go_pkg_crypto_sha256, go_pkg_crypto_subtle, go_pkg_crypto_tls (+21 more)

### Community 19 - "Community 19"
Cohesion: 0.07
Nodes (24): authTitles, awaiting, busy, code, comment, config, connection, days (+16 more)

### Community 20 - "Community 20"
Cohesion: 0.20
Nodes (23): _is_active(), UserRole, VpnClient, Клиенты, которым пора слать уведомление об окончании. Берём тех, у кого задан…, has_active_timed_client(), has_client_access(), has_unlimited_bound_client(), resolve_effective_role() (+15 more)

### Community 21 - "Community 21"
Cohesion: 0.13
Nodes (12): Response, Авторизованный запрос: гарантирует login и при истёкшей сессии выполняет…, Берёт CSRF-токен с /csrf-token (3x-ui >= 3.2.x). На старых панелях endpoint…, Изолированный REST-клиент панели 3x-ui (MHSanaei/3x-ui). Принципы: - одна…, Создаёт нового клиента в inbound через addClient., Определяет, есть ли у панели новый client-API /panel/api/clients. В 3x-ui 3.2.x…, Возвращает список IP-адресов клиента из журнала 3x-ui (iplimit log). Требует…, Извлекает IP из вариантов ответа 3x-ui, не сохраняя метаданные лога. (+4 more)

### Community 22 - "Community 22"
Cohesion: 0.14
Nodes (25): on_bind_action(), callback_query, notify_admins_bind_failed(), notify_admins_failed(), notify_admins_new_bind_request(), notify_admins_new_request(), notify_first_purchase_channel(), notify_user_bind_approved() (+17 more)

### Community 23 - "Community 23"
Cohesion: 0.22
Nodes (23): sharing_report(), IpObservation, _active_clients(), collect_all(), collect_for_client(), compute_status(), _level_for(), list_all_statuses() (+15 more)

### Community 24 - "Community 24"
Cohesion: 0.13
Nodes (12): Any, _quote_path_segment(), Возвращает список inbound'ов панели с их БД-id, портами и протоколами., Ищет клиента в inbound по uuid, email или subId (стабильные ID)., Совместимый алиас find_client (по uuid/email)., Удаляет клиента из inbound., Список всех клиентов панели. На 3x-ui >= 3.2.x берётся из…, Возвращает запись клиента нового API: {"client": {...}, "inboundIds": [...]}.… (+4 more)

### Community 25 - "Community 25"
Cohesion: 0.22
Nodes (21): Сохраняет наблюдения IP. Возвращает число добавленных записей., record_ips(), MockIpProvider, Mock-провайдер для тестов: возвращает заранее заданные IP по server_id., utcnow(), _ips(), AsyncSession, _settings() (+13 more)

### Community 26 - "Community 26"
Cohesion: 0.16
Nodes (19): create_request(), _new_payment_code(), AsyncSession, Создаёт заявку на продление и переводит её в ожидание проверки админом., FakeBot, Any, AsyncSession, test_admin_notified_about_new_request() (+11 more)

### Community 27 - "Community 27"
Cohesion: 0.28
Nodes (23): _client(), _mock_csrf(), HTTPXMock, Регистрирует ответ /csrf-token (3x-ui 3.2.x запрашивает его перед login)., test_bearer_token_skips_login_and_csrf(), test_create_client_record(), test_del_client_quotes_identifier_path_segment(), test_find_client_by_sub_id() (+15 more)

### Community 28 - "Community 28"
Cohesion: 0.16
Nodes (20): aiogram_types, _command_name(), DbSessionMiddleware, _describe_callback(), _describe_event(), _describe_message(), Any, CallbackQuery (+12 more)

### Community 29 - "Community 29"
Cohesion: 0.13
Nodes (20): aiogram_filters_callback_data, app_bot, BindCallback, MenuCallback, OnboardCallback, PaymentCallback, PlanCallback, Callback админских действий над заявкой на привязку подписки. (+12 more)

### Community 30 - "Community 30"
Cohesion: 0.18
Nodes (18): AttachmentType, PaymentAttachment, Durable per-admin Telegram delivery, retried independently of HTTP requests., WebDelivery, attach_proof(), Прикрепляет подтверждение оплаты (текст/фото/документ) к заявке., delivery_loop(), has_purchase() (+10 more)

### Community 31 - "Community 31"
Cohesion: 0.13
Nodes (16): forward_proof_to_admins(), admin_pending(), Конфигурация приложения из переменных окружения / .env., Убирает пробелы и обрамляющие кавычки вокруг токена., Разрешает задавать ADMIN_TELEGRAM_IDS как строку '1,2,3' или одно число., Settings, BaseSettings, field_validator (+8 more)

### Community 32 - "Community 32"
Cohesion: 0.19
Nodes (16): _as_aware(), process_expiry_notifications(), AsyncSession, Bot, datetime, Стадия уведомления по остатку времени до окончания. 0 — рано, 1 — остался день,…, Шлёт уведомления «за день / за час / в момент окончания». Каждая стадия…, _target_stage() (+8 more)

### Community 33 - "Community 33"
Cohesion: 0.12
Nodes (13): Реальный провайдер: берёт IP клиента из журнала панели 3x-ui., XuiIpProvider, Exception, Базовая ошибка взаимодействия с панелью 3x-ui., Ошибка авторизации в панели., XuiAuthError, XuiError, ipaddress (+5 more)

### Community 34 - "Community 34"
Cohesion: 0.18
Nodes (18): decrypt(), encrypt(), is_encrypted(), Шифрует строку. Без SECRET_KEY возвращает значение как есть (dev/тесты)., Расшифровывает строку. Legacy-значения в открытом виде возвращает как есть., MonkeyPatch, no_key(), AsyncSession (+10 more)

### Community 35 - "Community 35"
Cohesion: 0.24
Nodes (17): WebAccount, WebLinkRequest, decide_link(), link_callback(), callback_query, CallbackQuery, receipt_bytes(), make_account() (+9 more)

### Community 36 - "Community 36"
Cohesion: 0.19
Nodes (5): PaymentRequest, PaymentRepository, Берёт заявку с блокировкой строки (SELECT ... FOR UPDATE). На Postgres…, Удаляет заявку (вместе с вложениями по каскаду)., Последняя успешная (применённая/подтверждённая) оплата пользователя.…

### Community 37 - "Community 37"
Cohesion: 0.30
Nodes (13): PendingServerUpdate, PendingServerUpdateRepository, datetime, apply_pending_for_server(), apply_pending_update(), _apply_to_server(), _as_aware(), _clear_payment_error_if_complete() (+5 more)

### Community 38 - "Community 38"
Cohesion: 0.20
Nodes (12): app_db, Base, Базовый класс для всех ORM-моделей., TimestampMixin, WebSession, WebToken, do_run_migrations(), run_migrations_online() (+4 more)

### Community 39 - "Community 39"
Cohesion: 0.19
Nodes (11): aiogram_filters, IsAdmin, TelegramObject, Пропускает событие только если пользователь — администратор., BaseFilter, test_is_admin_filter_accepts_admin(), test_is_admin_filter_rejects_missing_user(), test_is_admin_filter_rejects_regular_user() (+3 more)

### Community 40 - "Community 40"
Cohesion: 0.15
Nodes (12): lucide-vue-next, typescript, vite, @vitejs/plugin-vue, vue-tsc, dependencies, lucide-vue-next, vue (+4 more)

### Community 41 - "Community 41"
Cohesion: 0.21
Nodes (8): app_services, get_plan(), PaymentPlan, Выгода относительно помесячной оплаты за тот же срок., AsyncSession, test_changing_plan_updates_open_request(), test_create_request_with_plan(), test_get_plan()

### Community 42 - "Community 42"
Cohesion: 0.15
Nodes (12): compilerOptions, esModuleInterop, jsx, lib, module, moduleResolution, resolveJsonModule, skipLibCheck (+4 more)

### Community 43 - "Community 43"
Cohesion: 0.21
Nodes (11): go_pkg_net_http, go_pkg_net_http_httptest, go_pkg_strings, go_pkg_testing, go_pkg_time, testing.T, canonicalEmail(), TestCodesBoundToAccountAndPurpose() (+3 more)

### Community 44 - "Community 44"
Cohesion: 0.32
Nodes (12): api(), authenticate(), copy(), getConnection(), go(), link(), logout(), pay() (+4 more)

### Community 45 - "Community 45"
Cohesion: 0.18
Nodes (5): Идентификатор для updateClient/{id}: id для vless/vmess, иначе email., Обновляет клиента, сохраняя все его поля и меняя только нужные. Возвращает…, Устанавливает expiryTime (мс) и включает клиента., Лимит уникальных IP (0 = без лимита). Не считать точным лимитом устройств., Совместимый метод: продление через read-modify-write.

### Community 46 - "Community 46"
Cohesion: 0.53
Nodes (6): net/http.Request, net/http.ResponseWriter, decode(), digest(), fail(), respond()

### Community 47 - "Community 47"
Cohesion: 0.29
Nodes (9): aiogram_exceptions, answer(), answer_callback(), edit(), Any, CallbackQuery, Безопасно редактирует сообщение callback'а. ``callback.message`` может быть…, Безопасно отправляет ответ в чат callback'а (если сообщение доступно). (+1 more)

### Community 48 - "Community 48"
Cohesion: 0.29
Nodes (7): aiogram_methods, TelegramBadRequest, _bad_request(), _Callback, Exception, test_answer_callback_ignores_expired_query_id(), test_answer_callback_reraises_other_bad_request()

### Community 49 - "Community 49"
Cohesion: 0.29
Nodes (6): app, config, context.Context, github.com/jackc/pgx/v5/pgxpool.Pool, net/http.Client, pgx.Tx

### Community 50 - "Community 50"
Cohesion: 0.22
Nodes (7): bucket, limiter, net/http.Handler, sync.Mutex, time.Time, env(), main()

### Community 51 - "Community 51"
Cohesion: 0.47
Nodes (8): pytest_asyncio, admin(), AsyncSession, datetime, fixture, server(), user(), vpn_client()

### Community 52 - "Community 52"
Cohesion: 0.29
Nodes (6): ref_node_fs_promises, ref_node_http, ref_node_path, ref_node_url, root, types

### Community 53 - "Community 53"
Cohesion: 0.40
Nodes (4): EncryptedString, Any, Прозрачно шифрует значение при записи и расшифровывает при чтении. - Если…, TypeDecorator

### Community 54 - "Community 54"
Cohesion: 0.33
Nodes (4): APIError, Configuration, Plan, Profile

### Community 56 - "Community 56"
Cohesion: 0.50
Nodes (4): collect_links(), AsyncSession, Возвращает список (метка, ссылка-подписка) по всем серверам пользователя. Для…, _sub_link()

### Community 57 - "Community 57"
Cohesion: 0.40
Nodes (5): devDependencies, typescript, vite, @vitejs/plugin-vue, vue-tsc

### Community 58 - "Community 58"
Cohesion: 0.50
Nodes (4): scripts, build, dev, preview

### Community 59 - "Community 59"
Cohesion: 0.67
Nodes (3): country_flag(), Эмодзи-флаг по ISO2-коду страны (напр. 'SE' -> 🇸🇪). Иначе пусто., test_country_flag()

### Community 60 - "Community 60"
Cohesion: 0.67
Nodes (3): purchase_info(), Экран «Оформить подписку»: цены и правила. parse_mode='HTML'., test_purchase_info_contains_promo_and_prices()

## Knowledge Gaps
- **55 isolated node(s):** `credentials`, `authTitles`, `awaiting`, `busy`, `code` (+50 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 469 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `Community 5` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 6`, `Community 7`, `Community 8`, `Community 9`, `Community 10`, `Community 12`, `Community 13`, `Community 15`, `Community 16`, `Community 20`, `Community 22`, `Community 25`, `Community 26`, `Community 29`, `Community 30`, `Community 31`, `Community 32`, `Community 35`, `Community 37`, `Community 38`, `Community 39`, `Community 41`, `Community 51`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Why does `Server` connect `Community 9` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 6`, `Community 7`, `Community 8`, `Community 10`, `Community 12`, `Community 13`, `Community 15`, `Community 16`, `Community 23`, `Community 25`, `Community 30`, `Community 33`, `Community 34`, `Community 37`, `Community 38`, `Community 51`, `Community 53`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 31` to `Community 2`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 8`, `Community 13`, `Community 15`, `Community 16`, `Community 17`, `Community 20`, `Community 22`, `Community 23`, `Community 25`, `Community 26`, `Community 28`, `Community 30`, `Community 34`, `Community 39`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Are the 141 inferred relationships involving `User` (e.g. with `admin_broadcast_send()` and `admin_delete_subscription_by_client_id()`) actually correct?**
  _`User` has 141 INFERRED edges - model-reasoned connections that need verification._
- **Are the 72 inferred relationships involving `VpnClient` (e.g. with `notify_user_extended()` and `access_extended()`) actually correct?**
  _`VpnClient` has 72 INFERRED edges - model-reasoned connections that need verification._
- **Are the 47 inferred relationships involving `Settings` (e.g. with `add_server()` and `admin_add_server_line()`) actually correct?**
  _`Settings` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `Server` (e.g. with `_finalize_new_server()` and `admin_server_keyboard()`) actually correct?**
  _`Server` has 32 INFERRED edges - model-reasoned connections that need verification._
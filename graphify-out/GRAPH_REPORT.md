# Graph Report - VpnBot  (2026-10-05)

## Corpus Check
- 127 files · ~95,477 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 3, .conf 1)

## Summary
- 2227 nodes · 7944 edges · 91 communities (75 shown, 16 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1012 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `81e37358`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- provisioning.py
- texts.py
- WhitelistLedger
- test_legacy_bind.py
- test_whitelist.py
- user_handlers.py
- admin_handlers.py
- _parse_server_line
- keyboards.py
- test_whitelist_reconcile.py
- PanelUpdater
- SubHubClient
- VpnClientRepository
- models.py
- sqlalchemy
- pending_updates.py
- test_whitelist_pg.py
- main.py
- main.go
- App.vue
- get_sessionmaker
- whitelist.py
- payments.py
- utcnow
- XuiClient
- web_smoke.py
- User
- test_xui_client.py
- _describe_event
- Protocol
- reconcile_cycle
- .__call__
- Контекст проекта
- IsAdmin
- MockPanelUpdater
- web_bridge.py
- ServerRepository
- test_whitelist_xui.py
- delete_user_subscription
- test_whitelist_payment_status.py
- package.json
- Ревью VpnBot — 4 октября 2026
- compilerOptions
- main_test.go
- api
- Контекст проекта
- .auth
- broadcast.py
- Задание агенту: услуга «Обход белых списков» в VpnBot
- app
- main
- Telegram VPN Billing Bot
- web_preview.mjs
- EncryptedString
- api.ts
- test_security.py
- reset_user_bot_state
- whitelist_admin
- D VPN — личный кабинет
- dvpn/site
- telegram-vpn-billing-bot
- panel_updater.py
- test_ux.py
- MenuCallback
- get_plan
- test_health_check_server_returns_false_on_error
- VpnClient
- AGENTS.md
- Обновление production — 4 октября 2026
- conftest.py
- PaymentRequest
- Оставшиеся риски и решения
- Server
- find_panel_client
- test_subscription_delete.py
- test_whitelist_bot.py
- ServerInbound
- panel
- menu_nav
- answer_callback
- operation_lock.py
- check_servers
- devDependencies
- test_review_regressions.py
- create_request

## God Nodes (most connected - your core abstractions)
1. `User` - 240 edges
2. `VpnClient` - 140 edges
3. `Server` - 131 edges
4. `Settings` - 120 edges
5. `MockPanelUpdater` - 108 edges
6. `PaymentRequest` - 84 edges
7. `PaymentStatus` - 81 edges
8. `VpnClientRepository` - 78 edges
9. `XuiClient` - 74 edges
10. `PanelUpdater` - 66 edges

## Surprising Connections (you probably didn't know these)
- `Как формируется клиент` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py
- `Логика продления` --references--> `vpn_client()`  [INFERRED]
  README.md → tests/conftest.py
- `3. Модель учёта` --references--> `payment_status_label()`  [INFERRED]
  docs/WHITELIST_SERVICE.md → app/bot/texts.py
- `Доменная модель` --references--> `PaymentStatus`  [INFERRED]
  context.md → app/db/enums.py
- `Доменная модель` --references--> `BindRequestStatus`  [INFERRED]
  context.md → app/db/enums.py

## Import Cycles
- None detected.

## Communities (91 total, 16 thin omitted)

### Community 0 - "provisioning.py"
Cohesion: 0.11
Nodes (25): ServerUpdateResult, apply_access(), apply_access_to_server(), bind_existing_client(), bind_user_by_public_id(), BindResult, build_provision_spec(), _build_spec() (+17 more)

### Community 1 - "texts.py"
Cohesion: 0.04
Nodes (76): admin_nav(), emoji_char(), tg(), access_extended(), access_update_pending(), admin_add_cancelled(), admin_add_server_prompt(), admin_bind_pending() (+68 more)

### Community 2 - "WhitelistLedger"
Cohesion: 0.12
Nodes (15): WhitelistAccount, WhitelistLedger, admin_summary(), AdminSummary, apply_event(), apply_usage(), compute_target(), _consistent_anchor() (+7 more)

### Community 3 - "test_legacy_bind.py"
Cohesion: 0.09
Nodes (23): BindRequestStatus, BindRequest, BindRequestRepository, approve_request(), BindApproveResult, BindRequestError, create_request(), reject_request() (+15 more)

### Community 4 - "test_whitelist.py"
Cohesion: 0.09
Nodes (61): AwaitingCredit, list_open_events(), process_due(), reconcile_usage(), user_overview(), _account(), _ago(), _baseline() (+53 more)

### Community 5 - "user_handlers.py"
Cohesion: 0.11
Nodes (32): AdminStates, OnboardingStates, ProofStates, bind_request_received(), bind_request_waiting(), no_open_request(), onboarding_invalid_link(), onboarding_legacy_question() (+24 more)

### Community 6 - "admin_handlers.py"
Cohesion: 0.11
Nodes (49): add_inbound(), add_server(), admin_add_server_cancel(), admin_add_server_line(), admin_broadcast_cancel(), admin_broadcast_send(), admin_delete_subscription_by_client_id(), admin_delete_subscription_cancel() (+41 more)

### Community 7 - "_parse_server_line"
Cohesion: 0.18
Nodes (9): _parse_server_line(), _validate_subscription_base(), test_parse_server_line_accepts_valid(), test_parse_server_line_rejects_invalid(), test_unknown_or_forged_plan_code_rejected(), test_validate_server_name_rejects_invalid(), test_validate_subscription_base_accepts_url_and_clear_marker(), test_validate_subscription_base_rejects_invalid() (+1 more)

### Community 8 - "keyboards.py"
Cohesion: 0.14
Nodes (30): _adm(), admin_add_server_type_keyboard(), admin_back_keyboard(), admin_bind_keyboard(), admin_bind_retry_keyboard(), admin_confirm_delete_keyboard(), admin_home_keyboard(), admin_payment_keyboard() (+22 more)

### Community 9 - "test_whitelist_reconcile.py"
Cohesion: 0.07
Nodes (32): ReconcileStatus, _add_account(), _cycle(), _email(), _free(), panel(), _populate(), _reconciled() (+24 more)

### Community 10 - "PanelUpdater"
Cohesion: 0.13
Nodes (23): _apply_panels(), _as_aware(), BillingError, BillingResult, compute_new_expiry(), _confirm_traffic(), _count_eligible_mappings(), _evaluate_panel_results() (+15 more)

### Community 11 - "SubHubClient"
Cohesion: 0.10
Nodes (13): build_happ_import_url(), ResolvedSubscription, SubHubClient, try_candidates(), SubHubError, SubHubNotFound, SubHubNotReady, test_authentication_failure_has_safe_error_message() (+5 more)

### Community 12 - "VpnClientRepository"
Cohesion: 0.12
Nodes (23): MappingRepository, VpnClientRepository, ensure_vpn_client(), days_from_now(), _panel_info(), _server_with_inbounds(), test_apply_access_creates_clients_and_mappings(), test_apply_access_idempotent() (+15 more)

### Community 13 - "models.py"
Cohesion: 0.12
Nodes (9): Base, TimestampMixin, AuditLog, WebSession, WebToken, AuditRepository, SubscriptionDeleteResult, collect_links() (+1 more)

### Community 14 - "sqlalchemy"
Cohesion: 0.08
Nodes (18): upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade() (+10 more)

### Community 15 - "pending_updates.py"
Cohesion: 0.16
Nodes (16): PendingServerUpdate, PendingServerUpdateRepository, _utcnow(), apply_pending_for_server(), apply_pending_update(), _apply_to_server(), _as_aware(), _clear_payment_error_if_complete() (+8 more)

### Community 16 - "test_whitelist_pg.py"
Cohesion: 0.16
Nodes (16): session(), _confirm(), _NoLocalLocks, pg(), SlowPanel, _state(), _subscription_request(), test_background_queue_racing_purchase_never_rolls_back() (+8 more)

### Community 17 - "main.py"
Cohesion: 0.12
Nodes (14): setup_logging(), _anti_sharing_poller(), _expiry_notify_poller(), main(), run(), _server_health_poller(), subhub_sync(), _setup_menu_button() (+6 more)

### Community 18 - "main.go"
Cohesion: 0.07
Nodes (3): credentials, secret(), validPassword()

### Community 19 - "App.vue"
Cohesion: 0.07
Nodes (24): authTitles, awaiting, busy, code, comment, config, connection, days (+16 more)

### Community 20 - "get_sessionmaker"
Cohesion: 0.10
Nodes (17): get_settings(), decrypt(), encrypt(), _fernet(), is_encrypted(), get_engine(), get_session(), get_sessionmaker() (+9 more)

### Community 21 - "whitelist.py"
Cohesion: 0.06
Nodes (55): record(), serialized_access(), access_state(), AccessState, adjust_balance(), after_access_change(), _append_note(), _applied_target() (+47 more)

### Community 22 - "payments.py"
Cohesion: 0.18
Nodes (8): AttachmentType, PaymentAttachment, TrafficPackage, attach_proof(), cancel_open_request(), _new_payment_code(), _open_request_for_update(), whitelist_package_title()

### Community 23 - "utcnow"
Cohesion: 0.07
Nodes (45): sharing_report(), IpObservation, _active_clients(), collect_all(), collect_for_client(), compute_status(), _level_for(), list_all_statuses() (+37 more)

### Community 24 - "XuiClient"
Cohesion: 0.07
Nodes (8): _quote_path_segment(), XuiClient, XuiError, test_capability_failure_does_not_fall_back_to_legacy_writes(), test_base_url_is_normalized(), test_parse_ips_handles_arbitrary_input(), test_parse_json_invalid_raises_xuierror_not_crash(), test_parse_ips_extracts_ip_from_panel_log_objects()

### Community 25 - "web_smoke.py"
Cohesion: 0.16
Nodes (5): WebDelivery, queue(), code_from_mail(), main(), TelegramMock

### Community 26 - "User"
Cohesion: 0.13
Nodes (15): User, UserRepository, test_generated_public_id_is_unique_and_hex(), test_grant_trial_success(), test_trial_auto_imports_inbounds_when_servers_added(), test_trial_extends_active_subscription(), test_trial_failure_can_be_retried(), test_trial_only_once() (+7 more)

### Community 27 - "test_xui_client.py"
Cohesion: 0.19
Nodes (23): XuiAuthError, test_login_error_does_not_leak_password(), _client(), _mock_csrf(), test_bearer_token_skips_login_and_csrf(), test_create_client_record(), test_del_client_quotes_identifier_path_segment(), test_find_client_by_sub_id() (+15 more)

### Community 28 - "_describe_event"
Cohesion: 0.24
Nodes (10): _command_name(), _describe_callback(), _describe_event(), _describe_message(), _private_chat(), test_describe_addserver_redacts_secrets(), test_describe_callback_shows_action_only(), test_describe_command_without_args_shows_name() (+2 more)

### Community 29 - "Protocol"
Cohesion: 0.12
Nodes (22): Protocol, build_client_object(), client_identifier(), _client_uuid_for_api(), _looks_like_db_id(), merge_client_record_for_update(), pick_panel_client_secret(), sanitize_client_for_api() (+14 more)

### Community 30 - "reconcile_cycle"
Cohesion: 0.16
Nodes (6): _BatchResult, _reconcile_batch(), reconcile_cycle(), ReconcileReport, _retry_busy(), _select_reconcile_rows()

### Community 32 - "Контекст проекта"
Cohesion: 0.10
Nodes (18): Запуск, Запуск через Docker Compose, API, Архитектура, Безопасность аутентификации (backend/main.go), Важные инженерные правила, Доменная модель (таблицы веб-части, в БД бота), Запуск (+10 more)

### Community 33 - "IsAdmin"
Cohesion: 0.17
Nodes (7): IsAdmin, test_is_admin_filter_accepts_admin(), test_is_admin_filter_rejects_missing_user(), test_is_admin_filter_rejects_regular_user(), test_settings_is_admin(), test_settings_parses_admin_ids_from_string(), test_is_admin_filter_is_used_on_both_observers()

### Community 34 - "MockPanelUpdater"
Cohesion: 0.13
Nodes (27): PaymentStatus, PaymentRepository, confirm_payment(), MockPanelUpdater, check_released(), main(), confirm(), test_confirm_then_notify_user() (+19 more)

### Community 35 - "web_bridge.py"
Cohesion: 0.14
Nodes (18): WebAccount, WebLinkRequest, decide_link(), has_purchase(), link_callback(), problem(), receipt_bytes(), start_bridge() (+10 more)

### Community 36 - "ServerRepository"
Cohesion: 0.08
Nodes (5): _finalize_new_server(), _finalize_whitelist_server(), admin_import_inbounds(), admin_whitelist_inventory(), ServerRepository

### Community 37 - "test_whitelist_xui.py"
Cohesion: 0.30
Nodes (15): QuotaTarget, _auth(), _body(), _record(), _spec(), test_create_sends_bytes_and_disables_panel_auto_reset(), test_legacy_panel_is_rejected_for_quota(), test_missing_traffic_row_is_unknown_not_zero() (+7 more)

### Community 39 - "test_whitelist_payment_status.py"
Cohesion: 0.29
Nodes (16): payment_status_label(), _buy(), _down(), _fresh(), _is_waiting(), _queue(), test_admin_and_user_screens_follow_application(), test_applied_version_gates_each_payment_separately() (+8 more)

### Community 40 - "package.json"
Cohesion: 0.10
Nodes (17): lucide-vue-next, typescript, vite, @vitejs/plugin-vue, vue, vue-tsc, dependencies, lucide-vue-next (+9 more)

### Community 41 - "Ревью VpnBot — 4 октября 2026"
Cohesion: 0.25
Nodes (8): Исправления в рабочем дереве, Объём и доказательства, Порядок применения в production, Проверки, Разбор PAY-1C3F1344, Ревью VpnBot — 4 октября 2026, Результат, Устройство production

### Community 42 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, esModuleInterop, jsx, lib, module, moduleResolution, resolveJsonModule, skipLibCheck (+4 more)

### Community 43 - "main_test.go"
Cohesion: 0.21
Nodes (5): canonicalEmail(), TestCodesBoundToAccountAndPurpose(), TestEmailRejectsHeaderInjection(), TestOriginRejectsCrossSiteMutation(), TestRateLimitExpires()

### Community 44 - "api"
Cohesion: 0.32
Nodes (12): api(), authenticate(), copy(), getConnection(), go(), link(), logout(), pay() (+4 more)

### Community 45 - "Контекст проекта"
Cohesion: 0.14
Nodes (13): Админские команды, Антишеринг, Доменная модель, Интеграция с 3x-ui, Контекст проекта, Конфигурация, Локальные артефакты, Назначение (+5 more)

### Community 46 - ".auth"
Cohesion: 0.53
Nodes (4): decode(), digest(), fail(), respond()

### Community 47 - "broadcast.py"
Cohesion: 0.24
Nodes (5): BroadcastResult, send_broadcast(), FakeBot, test_send_broadcast_counts_sent_and_failed(), test_send_broadcast_empty_list()

### Community 48 - "Задание агенту: услуга «Обход белых списков» в VpnBot"
Cohesion: 0.15
Nodes (12): 1. Контекст проекта, 2. Согласованное поведение услуги, 3. Сервер и настройки администратора, 4. Технический контракт учёта трафика, 5. Биллинг, конкуренция и восстановление, 6. Пользовательский интерфейс, 7. Обязательная проверка, 8. Порядок работы и сдача (+4 more)

### Community 50 - "main"
Cohesion: 0.22
Nodes (4): bucket, limiter, env(), main()

### Community 51 - "Telegram VPN Billing Bot"
Cohesion: 0.06
Nodes (32): decorate(), wrapped(), user_operation(), 1. Что получает пользователь, 2. Проверенный контракт 3x-ui, 5. Конкуренция и восстановление, 6. Порядок внедрения, 7. Откат (+24 more)

### Community 53 - "EncryptedString"
Cohesion: 0.29
Nodes (3): EncryptedString, Важные инженерные правила проекта, P1 — пароли панелей не защищены шифрованием приложения

### Community 54 - "api.ts"
Cohesion: 0.33
Nodes (4): APIError, Configuration, Plan, Profile

### Community 56 - "test_security.py"
Cohesion: 0.06
Nodes (25): build_root_router(), FakeBot, FakeMessage, _make_payment(), _persist_payment(), test_admin_callback_filter_allows_admin(), test_admin_callback_filter_blocks_regular_user(), test_admin_message_filter_allows_admin() (+17 more)

### Community 59 - "whitelist_admin"
Cohesion: 0.14
Nodes (15): whitelist_admin(), WhitelistConfig, create_traffic_request(), ensure_defaults(), get_active_server(), get_config(), list_packages(), RolloutReport (+7 more)

### Community 63 - "D VPN — личный кабинет"
Cohesion: 0.25
Nodes (7): D VPN — личный кабинет, Архитектура, Запуск вместе с существующим ботом, Локальная разработка, Результаты проверки, Что реализовано, Эксплуатация

### Community 71 - "panel_updater.py"
Cohesion: 0.11
Nodes (11): ProvisionInbound, ProvisionTarget, ServerProvision, build_client_record(), _is_missing_client_error(), _mock_auth(), _spec(), test_legacy_provisioning_keeps_one_email_for_every_inbound() (+3 more)

### Community 72 - "test_ux.py"
Cohesion: 0.09
Nodes (33): custom_emoji_id(), connection_keyboard(), welcome_menu(), _cancel_payment(), _trial_available(), _all_buttons(), _DummyState, test_admin_home_keyboard_sections() (+25 more)

### Community 73 - "MenuCallback"
Cohesion: 0.28
Nodes (6): MenuCallback, cancel_payment_keyboard(), reset_bot_confirm_keyboard(), _all_buttons(), test_reset_confirm_keyboard(), test_cancel_payment_keyboard()

### Community 74 - "get_plan"
Cohesion: 0.33
Nodes (4): get_plan(), PaymentPlan, test_get_plan(), test_plan_amounts_are_fixed_server_side()

### Community 76 - "VpnClient"
Cohesion: 0.12
Nodes (23): _is_active(), Settings, UserRole, VpnClient, has_active_timed_client(), has_client_access(), has_unlimited_bound_client(), resolve_effective_role() (+15 more)

### Community 85 - "Обновление production — 4 октября 2026"
Cohesion: 0.25
Nodes (6): PAY-1C3F1344, Внедрено, Дополнительный дефект, обнаруженный при приёмке, Незавершённые операции, Обновление production — 4 октября 2026, Проверки и резервирование

### Community 87 - "conftest.py"
Cohesion: 0.57
Nodes (4): admin(), server(), user(), vpn_client()

### Community 88 - "PaymentRequest"
Cohesion: 0.08
Nodes (23): _after_applied_payment(), on_bind_action(), on_payment_action(), forward_proof_to_admins(), notify_admins_bind_failed(), notify_admins_failed(), notify_admins_new_bind_request(), notify_admins_new_request() (+15 more)

### Community 89 - "Оставшиеся риски и решения"
Cohesion: 0.25
Nodes (7): P1/P2 — частичный успех внешней операции требует сверки, P1 — административные права зависят от тарифа, P1 — биллинг и панели не образуют одну транзакцию, P2 — мониторинг и производительность, P2 — старые ошибки оплат без ожидающих задач, P2 — эксплуатация и воспроизводимость, Оставшиеся риски и решения

### Community 90 - "Server"
Cohesion: 0.07
Nodes (16): connection_overview(), server_button_label(), ClientServerMapping, Server, XuiIpProvider, PanelUpdateError, QuotaClientState, _find_panel_client_by_sub_id() (+8 more)

### Community 91 - "find_panel_client"
Cohesion: 0.29
Nodes (5): find_panel_client(), _panel_client_secret(), PanelClientInfo, _pick_secret(), fake_find()

### Community 92 - "test_subscription_delete.py"
Cohesion: 0.23
Nodes (7): _FakeBot, _FakeMessage, _FakeState, test_admin_delete_subscription_uses_client_id_not_telegram_id(), test_delete_subscription_keeps_local_client_on_panel_failure(), test_delete_subscription_removes_panel_and_local_client(), test_delete_subscription_without_client_is_noop()

### Community 93 - "test_whitelist_bot.py"
Cohesion: 0.10
Nodes (20): AdminCallback, BindCallback, OnboardCallback, PaymentCallback, WhitelistAdminCallback, WhitelistCallback, Возможности, FakeCallback (+12 more)

### Community 94 - "ServerInbound"
Cohesion: 0.18
Nodes (9): ServerInbound, ensure_inbounds_imported(), import_inbounds(), _ss_method(), test_ensure_inbounds_imported_imports_when_missing(), fake_import(), test_disabled_inbounds_are_not_bypassed_by_mapping_retry(), fake_import() (+1 more)

### Community 96 - "panel"
Cohesion: 0.22
Nodes (4): panel(), service_on(), std_target(), wl_server()

### Community 97 - "menu_nav"
Cohesion: 0.15
Nodes (10): PlanCallback, extend_plans_keyboard(), install_guides_keyboard(), _plan_label(), purchase_plans_keyboard(), menu_nav(), _plan_title_for_period(), test_plan_callback_carries_only_code() (+2 more)

### Community 98 - "answer_callback"
Cohesion: 0.13
Nodes (8): _edit_panel(), answer(), answer_callback(), edit(), _bad_request(), _Callback, test_answer_callback_ignores_expired_query_id(), test_answer_callback_reraises_other_bad_request()

### Community 102 - "check_servers"
Cohesion: 0.18
Nodes (4): check_server(), check_servers(), Фоновые задачи, test_health_check_server_returns_true_on_success()

### Community 103 - "devDependencies"
Cohesion: 0.40
Nodes (5): devDependencies, typescript, vite, @vitejs/plugin-vue, vue-tsc

### Community 104 - "test_review_regressions.py"
Cohesion: 0.15
Nodes (8): ReadOnlyPanel, test_attach_success_without_membership_is_not_provisioning_success(), test_client_read_failure_is_not_misreported_as_missing(), test_import_network_failure_preserves_targets(), test_import_reconciles_deleted_disabled_and_new_inbounds(), test_malformed_inbounds_is_not_treated_as_empty_panel(), test_stale_inbound_is_rejected_before_client_creation(), test_stored_tunnel_ips_are_normalized_for_client_api()

### Community 105 - "create_request"
Cohesion: 0.21
Nodes (10): create_request(), test_admin_notified_about_new_request(), test_reject_then_notify_user(), test_attach_proof_creates_attachment(), test_create_request_reuses_open_request(), test_create_request_sets_waiting_admin(), test_get_by_code_and_list_waiting(), test_payment_code_increments() (+2 more)

## Knowledge Gaps
- **125 isolated node(s):** `credentials`, `dvpn/site`, `name`, `version`, `private` (+120 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 690 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `provisioning.py`, `texts.py`, `test_legacy_bind.py`, `test_whitelist.py`, `user_handlers.py`, `admin_handlers.py`, `test_whitelist_reconcile.py`, `PanelUpdater`, `VpnClientRepository`, `models.py`, `pending_updates.py`, `test_whitelist_pg.py`, `get_sessionmaker`, `whitelist.py`, `payments.py`, `utcnow`, `web_smoke.py`, `IsAdmin`, `MockPanelUpdater`, `web_bridge.py`, `delete_user_subscription`, `test_security.py`, `reset_user_bot_state`, `whitelist_admin`, `test_ux.py`, `VpnClient`, `conftest.py`, `PaymentRequest`, `test_subscription_delete.py`, `menu_nav`, `create_request`?**
  _High betweenness centrality (0.135) - this node is a cross-community bridge._
- **Are the 162 inferred relationships involving `User` (e.g. with `admin_add_server_line()` and `admin_broadcast_send()`) actually correct?**
  _`User` has 162 INFERRED edges - model-reasoned connections that need verification._
- **What connects `credentials`, `dvpn/site`, `name` to the rest of the system?**
  _125 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `provisioning.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10887949260042283 - nodes in this community are weakly interconnected._
- **Why does `Server` connect `Server` to `provisioning.py`, `texts.py`, `test_legacy_bind.py`, `test_whitelist.py`, `admin_handlers.py`, `_parse_server_line`, `keyboards.py`, `test_whitelist_reconcile.py`, `PanelUpdater`, `VpnClientRepository`, `models.py`, `pending_updates.py`, `test_whitelist_pg.py`, `get_sessionmaker`, `whitelist.py`, `utcnow`, `web_smoke.py`, `User`, `reconcile_cycle`, `MockPanelUpdater`, `web_bridge.py`, `ServerRepository`, `test_whitelist_xui.py`, `delete_user_subscription`, `Контекст проекта`, `EncryptedString`, `whitelist_admin`, `panel_updater.py`, `test_ux.py`, `conftest.py`, `find_panel_client`, `test_whitelist_bot.py`, `ServerInbound`, `panel`, `check_servers`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 87 inferred relationships involving `VpnClient` (e.g. with `notify_user_extended()` and `access_extended()`) actually correct?**
  _`VpnClient` has 87 INFERRED edges - model-reasoned connections that need verification._
- **Should `texts.py` be split into smaller, more focused modules?**
  _Cohesion score 0.03965599617773531 - nodes in this community are weakly interconnected._
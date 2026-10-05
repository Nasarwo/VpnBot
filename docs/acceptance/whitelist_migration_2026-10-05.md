# Протокол проверки миграций и резервной копии — 5 октября 2026

`ops/acceptance/whitelist_migration_check.py` на PostgreSQL 16.15 (postgres:16-alpine).

```text
[OK] исходная база на f9b2c3d4e5f6 с данными — {'users': (7, '1db352dd0f2570bb'), 'servers': (3, '933199cdc937daa9'), 'server_inbounds': (4, '35acefcfe0b02864'), 'vpn_clients': (5, '8bed30ff34d230e3'), 'client_server_mappings': (6, '98aeae3584a8561b'), 'payment_requests': (5, 'e8bf7fbd762c98bf'), 'payment_attachments': (1, '46ec8df8610c07d0'), 'pending_server_updates': (1, 'c77acea7ecdddd6e'), 'audit_logs': (1, '45b820f4922a5bfb'), 'alembic_version': (1, 'f9b2c3d4e5f6')}
[OK] pg_dump -Fc создан и читается pg_restore --list — 54109 байт, <dump-dir>/before-whitelist.dump
[OK] восстановление в отдельную базу совпадает с источником — совпадают
[OK] alembic upgrade head: три ревизии услуги
[OK] prod_sim: users без изменений прежних данных — (7, '1db352dd0f2570bb') → (7, '1db352dd0f2570bb')
[OK] prod_sim: servers без изменений прежних данных — (3, '933199cdc937daa9') → (3, '933199cdc937daa9')
[OK] prod_sim: server_inbounds без изменений прежних данных — (4, '35acefcfe0b02864') → (4, '35acefcfe0b02864')
[OK] prod_sim: vpn_clients без изменений прежних данных — (5, '8bed30ff34d230e3') → (5, '8bed30ff34d230e3')
[OK] prod_sim: client_server_mappings без изменений прежних данных — (6, '98aeae3584a8561b') → (6, '98aeae3584a8561b')
[OK] prod_sim: payment_requests без изменений прежних данных — (5, 'e8bf7fbd762c98bf') → (5, 'e8bf7fbd762c98bf')
[OK] prod_sim: payment_attachments без изменений прежних данных — (1, '46ec8df8610c07d0') → (1, '46ec8df8610c07d0')
[OK] prod_sim: pending_server_updates без изменений прежних данных — (1, 'c77acea7ecdddd6e') → (1, 'c77acea7ecdddd6e')
[OK] prod_sim: audit_logs без изменений прежних данных — (1, '45b820f4922a5bfb') → (1, '45b820f4922a5bfb')
[OK] prod_sim: alembic head — e2f3a4b5c6d7
[OK] prod_sim: старые серверы → standard — ['standard']
[OK] prod_sim: inventory_status пуст у старых серверов
[OK] prod_sim: старые заявки → subscription — ['subscription']
[OK] prod_sim: ожидание применения не выставлено подпискам
[OK] prod_sim: last_error подписки сохранён (маркер трогает только kind=traffic)
[OK] prod_sim: whitelist_config выключен, 10/3 ГиБ — {'id': 1, 'service_enabled': False, 'paid_free_bytes': 10737418240, 'trial_free_bytes': 3221225472, 'updated_at': None}
[OK] prod_sim: пакеты 10/49, 25/99, 50/199 — [(10, '49.00', True), (25, '99.00', True), (50, '199.00', True)]
[OK] prod_sim: учёт и журнал пусты (услуга не выдана) — [0, 0]
[OK] prod_sim: частичный уникальный индекс — CREATE UNIQUE INDEX uq_servers_single_enabled_whitelist ON public.servers USING btree (purpose) WHERE (((purpose)::text = 'whitelist'::text) AND enabled)
[OK] индекс: второй включённый whitelist-сервер отклонён, выключенный допустим
[OK] ensure_defaults дважды: 3 пакета, одна строка настроек — 3, 1
[OK] rehearsal: users без изменений прежних данных — (7, '1db352dd0f2570bb') → (7, '1db352dd0f2570bb')
[OK] rehearsal: servers без изменений прежних данных — (3, '933199cdc937daa9') → (3, '933199cdc937daa9')
[OK] rehearsal: server_inbounds без изменений прежних данных — (4, '35acefcfe0b02864') → (4, '35acefcfe0b02864')
[OK] rehearsal: vpn_clients без изменений прежних данных — (5, '8bed30ff34d230e3') → (5, '8bed30ff34d230e3')
[OK] rehearsal: client_server_mappings без изменений прежних данных — (6, '98aeae3584a8561b') → (6, '98aeae3584a8561b')
[OK] rehearsal: payment_requests без изменений прежних данных — (5, 'e8bf7fbd762c98bf') → (5, 'e8bf7fbd762c98bf')
[OK] rehearsal: payment_attachments без изменений прежних данных — (1, '46ec8df8610c07d0') → (1, '46ec8df8610c07d0')
[OK] rehearsal: pending_server_updates без изменений прежних данных — (1, 'c77acea7ecdddd6e') → (1, 'c77acea7ecdddd6e')
[OK] rehearsal: audit_logs без изменений прежних данных — (1, '45b820f4922a5bfb') → (1, '45b820f4922a5bfb')
[OK] rehearsal: alembic head — e2f3a4b5c6d7
[OK] rehearsal: старые серверы → standard — ['standard']
[OK] rehearsal: inventory_status пуст у старых серверов
[OK] rehearsal: старые заявки → subscription — ['subscription']
[OK] rehearsal: ожидание применения не выставлено подпискам
[OK] rehearsal: last_error подписки сохранён (маркер трогает только kind=traffic)
[OK] rehearsal: whitelist_config выключен, 10/3 ГиБ — {'id': 1, 'service_enabled': False, 'paid_free_bytes': 10737418240, 'trial_free_bytes': 3221225472, 'updated_at': None}
[OK] rehearsal: пакеты 10/49, 25/99, 50/199 — [(10, '49.00', True), (25, '99.00', True), (50, '199.00', True)]
[OK] rehearsal: учёт и журнал пусты (услуга не выдана) — [0, 0]
[OK] rehearsal: частичный уникальный индекс — CREATE UNIQUE INDEX uq_servers_single_enabled_whitelist ON public.servers USING btree (purpose) WHERE (((purpose)::text = 'whitelist'::text) AND enabled)
[OK] downgrade e2f3: ожидание → прежний маркер, иные ошибки не тронуты — {21: 'Сервер недоступен', 20: 'Трафик начислен; применение на сервере «Обход белых списков» ожидается'}
[OK] upgrade e2f3: маркер → apply_pending_version=desired_version, last_error снят — {21: (None, 'Сервер недоступен'), 20: (7, None)}
[OK] журнал сохранил статусы событий — ['settled', 'pending']
[OK] downgrade d1e2: столбцы событий удалены, строки журнала сохранены — rows=2
[OK] повторный upgrade d1e2: прежние строки получают settled (pending теряется — поэтому runbook требует 0 ожидающих перед откатом) — ['settled', 'settled']
[OK] полный откат схемы к f9b2c3d4e5f6: прежние данные совпадают с исходными — совпадают
[OK] полный откат удаляет таблицы услуги — []
[OK] повторный upgrade head после полного отката
[OK] alembic check: нет новых расхождений (прежний долг: 3)
Итого: 53 OK, 0 FAIL
```

"""Приёмка миграций «Обход белых списков» и восстановления резервной копии.

Только для отдельного тестового PostgreSQL (по умолчанию — контейнер Docker
``wlacc-pg`` с образом postgres:16-alpine, как в docker-compose.yml). Скрипт
пересоздаёт базы ``<prefix>_prod_sim``, ``<prefix>_restorecheck`` и
``<prefix>_rehearsal``; на production-базу его направлять нельзя.

Шаги повторяют runbook (docs/WHITELIST_SERVICE.md, раздел 6):

1. база на ревизии до услуги (f9b2c3d4e5f6) с данными всех видов;
2. ``pg_dump -Fc`` и ``pg_restore`` в отдельную базу, сверка содержимого;
3. ``alembic upgrade head`` и проверка результата миграции;
4. та же миграция на восстановленной копии (репетиция);
5. downgrade/upgrade с данными услуги и возврат к исходному содержимому;
6. ``alembic check`` на PostgreSQL.

Запуск (из корня репозитория, PostgreSQL слушает 127.0.0.1:55439):

    .venv/bin/python ops/acceptance/whitelist_migration_check.py \
        --url postgresql+asyncpg://wlacc:wlacc@127.0.0.1:55439 --container wlacc-pg
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import asyncpg

ROOT = Path(__file__).resolve().parents[2]
PRE_WHITELIST = "f9b2c3d4e5f6"
HEAD = "e2f3a4b5c6d7"
GIB = 1024**3

# Таблицы и столбцы, существовавшие до услуги: их содержимое миграция
# не должна менять, а откат схемы обязан вернуть без потерь.
LEGACY_TABLES = {
    "users": "id, telegram_id, public_id, username, role, trial_used, onboarding_done",
    "servers": "id, name, country, panel_url, username, password, kind, subscription_base, "
    "enabled",
    "server_inbounds": "id, server_id, inbound_id, protocol, flow, remark, enabled",
    "vpn_clients": "id, user_id, email, external_client_id, expires_at, is_active, "
    "expiry_notify_stage",
    "client_server_mappings": "id, vpn_client_id, server_id, inbound_id, protocol, "
    "client_uuid, email, sub_id, enabled",
    "payment_requests": "id, user_id, amount, currency, period_days, status, payment_code, "
    "last_error, target_expires_at, confirmed_at, applied_at",
    "payment_attachments": "id, payment_request_id, telegram_file_id, file_type, caption",
    "pending_server_updates": "id, vpn_client_id, server_id, payment_request_id, "
    "target_expires_at, status, attempts, last_error",
    "audit_logs": "id, actor_user_id, action, entity_type, entity_id",
}

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"[{'OK' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def dsn(base: str, db: str) -> str:
    return base.rstrip("/") + "/" + db


def plain(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://")


def alembic(base: str, db: str, *args: str) -> str:
    env = dict(os.environ, DATABASE_URL=dsn(base, db), BOT_TOKEN="acceptance")
    proc = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"alembic {' '.join(args)}: {proc.stderr[-2000:]}")
    return proc.stdout + proc.stderr


async def recreate(base: str, db: str) -> None:
    conn = await asyncpg.connect(plain(dsn(base, "postgres")))
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{db}" WITH (FORCE)')
        await conn.execute(f'CREATE DATABASE "{db}"')
    finally:
        await conn.close()


async def snapshot(base: str, db: str) -> dict[str, tuple[int, str]]:
    """Число строк и хэш упорядоченного содержимого прежних столбцов."""
    conn = await asyncpg.connect(plain(dsn(base, db)))
    try:
        result = {}
        for table, columns in LEGACY_TABLES.items():
            rows = await conn.fetch(f"SELECT {columns} FROM {table} ORDER BY id")
            digest = hashlib.sha256(repr([tuple(r) for r in rows]).encode()).hexdigest()
            result[table] = (len(rows), digest[:16])
        result["alembic_version"] = (
            1, await conn.fetchval("SELECT version_num FROM alembic_version")
        )
        return result
    finally:
        await conn.close()


SEED = """
INSERT INTO users (id, telegram_id, public_id, username, first_name, role, trial_used,
                   onboarding_done) VALUES
 (1, 900001, 'ADMIN001', 'admin', 'Admin', 'ADMIN', false, true),
 (2, 900002, 'PAID0002', 'paid', 'Paid', 'USER', true, true),
 (3, 900003, 'TRIAL003', 'trial', 'Trial', 'USER', true, true),
 (4, 900004, 'LIFE0004', 'life', 'Life', 'USER', false, true),
 (5, 900005, 'AMBIG005', 'bound', 'Bound', 'USER', false, true),
 (6, 900006, 'EXPIR006', 'expired', 'Expired', 'USER', true, true),
 (7, 900007, 'WAIT0007', 'waiting', 'Waiting', 'USER', false, true);
SELECT setval('users_id_seq', 7);
INSERT INTO servers (id, name, country, panel_url, username, password, kind,
                     subscription_base, enabled, created_at) VALUES
 (1, 'Финляндия', 'FI', 'https://fi.example.test:65000/p', 'u', 'enc:v1:secret', 'direct',
  NULL, true, now()),
 (2, 'Россия', 'RU', 'https://ru.example.test:65000/p', 'u', 'enc:v1:secret2', 'ru_proxy',
  'https://sub.example.test', true, now()),
 (3, 'Старый', 'NL', 'https://nl.example.test:65000/p', 'u', 'plain', 'direct', NULL,
  false, now());
SELECT setval('servers_id_seq', 3);
INSERT INTO server_inbounds (id, server_id, inbound_id, protocol, flow, remark, enabled) VALUES
 (1, 1, 1, 'VLESS', 'xtls-rprx-vision', 'fi-reality', true),
 (2, 1, 9, 'TROJAN', NULL, 'fi-trojan', true),
 (3, 2, 5, 'VLESS', NULL, 'ru', true),
 (4, 3, 1, 'VLESS', NULL, 'old', false);
SELECT setval('server_inbounds_id_seq', 4);
INSERT INTO vpn_clients (id, user_id, display_name, email, external_client_id, expires_at,
                         is_active, expiry_notify_stage) VALUES
 (1, 2, 'paid', 'PAID0002', 'uuid-2', now() + interval '20 days', true, 0),
 (2, 3, 'trial', 'TRIAL003', 'uuid-3', now() + interval '2 days', true, 0),
 (3, 4, 'life', 'LIFE0004', 'uuid-4', NULL, true, 0),
 (4, 5, 'bound', 'AMBIG005', 'uuid-5', now() + interval '40 days', true, 0),
 (5, 6, 'expired', 'EXPIR006', 'uuid-6', now() - interval '3 days', true, 3);
SELECT setval('vpn_clients_id_seq', 5);
INSERT INTO client_server_mappings (id, vpn_client_id, server_id, inbound_id, protocol,
                                    client_uuid, email, sub_id, enabled) VALUES
 (1, 1, 1, 1, 'VLESS', 'uuid-2', 'PAID0002', 'PAID0002', true),
 (2, 1, 1, 9, 'TROJAN', 'uuid-2', 'PAID0002', 'PAID0002', true),
 (3, 2, 1, 1, 'VLESS', 'uuid-3', 'TRIAL003', 'TRIAL003', true),
 (4, 3, 1, 1, 'VLESS', 'uuid-4', 'LIFE0004', 'LIFE0004', true),
 (5, 4, 2, 5, 'VLESS', 'uuid-5', 'legacy-email-5', 'legacysub5', true),
 (6, 5, 1, 1, 'VLESS', 'uuid-6', 'EXPIR006', 'EXPIR006', true);
SELECT setval('client_server_mappings_id_seq', 6);
INSERT INTO payment_requests (id, user_id, amount, currency, period_days, status, payment_code,
                              last_error, created_at, confirmed_at, applied_at,
                              target_expires_at) VALUES
 (1, 2, 175.00, 'RUB', 30, 'APPLIED', 'PAY-A1', NULL, now() - interval '10 days',
  now() - interval '10 days', now() - interval '10 days', now() + interval '20 days'),
 (2, 6, 175.00, 'RUB', 30, 'APPLIED', 'PAY-A2', NULL, now() - interval '40 days',
  now() - interval '40 days', now() - interval '40 days', now() - interval '3 days'),
 (3, 7, 175.00, 'RUB', 30, 'WAITING_ADMIN', 'PAY-W3', NULL, now(), NULL, NULL, NULL),
 (4, 6, 175.00, 'RUB', 30, 'FAILED', 'PAY-F4',
  'Трафик начислен; применение на сервере ожидается (имитация старого текста)',
  now() - interval '2 days', NULL, NULL, NULL),
 (5, 2, 850.00, 'RUB', 180, 'CONFIRMED', 'PAY-C5', NULL, now() - interval '1 hour',
  now() - interval '1 hour', NULL, now() + interval '200 days');
SELECT setval('payment_requests_id_seq', 5);
INSERT INTO payment_attachments (id, payment_request_id, telegram_file_id, file_type, caption,
                                 created_at) VALUES
 (1, 3, 'AgACAgIAAx', 'PHOTO', 'квитанция', now());
SELECT setval('payment_attachments_id_seq', 1);
INSERT INTO pending_server_updates (id, vpn_client_id, server_id, payment_request_id,
                                    target_expires_at, status, attempts, last_error) VALUES
 (1, 1, 2, 1, now() + interval '20 days', 'pending', 2, 'timeout');
SELECT setval('pending_server_updates_id_seq', 1);
INSERT INTO audit_logs (id, actor_user_id, action, entity_type, entity_id, created_at) VALUES
 (1, 1, 'billing.applied', 'payment_request', 1, now());
SELECT setval('audit_logs_id_seq', 1);
"""


async def seed(base: str, db: str) -> None:
    conn = await asyncpg.connect(plain(dsn(base, db)))
    try:
        await conn.execute(SEED)
    finally:
        await conn.close()


def docker(container: str, *args: str, stdin: bytes | None = None) -> bytes:
    proc = subprocess.run(
        ["docker", "exec", "-i", container, *args],
        input=stdin, capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"docker exec {' '.join(args)}: {proc.stderr.decode()[-2000:]}")
    return proc.stdout


async def verify_head(base: str, db: str, before: dict[str, tuple[int, str]], label: str) -> None:
    after = await snapshot(base, db)
    for table in LEGACY_TABLES:
        check(f"{label}: {table} без изменений прежних данных", after[table] == before[table],
              f"{before[table]} → {after[table]}")
    check(f"{label}: alembic head", after["alembic_version"][1] == HEAD,
          after["alembic_version"][1])
    conn = await asyncpg.connect(plain(dsn(base, db)))
    try:
        purposes = await conn.fetch("SELECT DISTINCT purpose FROM servers")
        check(f"{label}: старые серверы → standard",
              [r[0] for r in purposes] == ["standard"], str([r[0] for r in purposes]))
        inv = await conn.fetchval("SELECT count(*) FROM servers WHERE inventory_status IS NOT NULL")
        check(f"{label}: inventory_status пуст у старых серверов", inv == 0)
        kinds = await conn.fetch("SELECT DISTINCT kind FROM payment_requests")
        check(f"{label}: старые заявки → subscription",
              [r[0] for r in kinds] == ["subscription"], str([r[0] for r in kinds]))
        apv = await conn.fetchval(
            "SELECT count(*) FROM payment_requests WHERE apply_pending_version IS NOT NULL"
        )
        check(f"{label}: ожидание применения не выставлено подпискам", apv == 0)
        old_err = await conn.fetchval("SELECT last_error FROM payment_requests WHERE id = 4")
        check(f"{label}: last_error подписки сохранён (маркер трогает только kind=traffic)",
              old_err is not None and old_err.startswith("Трафик начислен"))
        cfg = await conn.fetchrow("SELECT * FROM whitelist_config")
        check(f"{label}: whitelist_config выключен, 10/3 ГиБ",
              cfg is not None and not cfg["service_enabled"]
              and cfg["paid_free_bytes"] == 10 * GIB and cfg["trial_free_bytes"] == 3 * GIB,
              str(dict(cfg) if cfg else None))
        packages = [
            (r["traffic_bytes"] // GIB, str(r["price"]), r["enabled"])
            for r in await conn.fetch(
                "SELECT traffic_bytes, price, enabled FROM traffic_packages ORDER BY sort_order"
            )
        ]
        check(f"{label}: пакеты 10/49, 25/99, 50/199",
              packages == [(10, "49.00", True), (25, "99.00", True), (50, "199.00", True)],
              str(packages))
        empty = [
            await conn.fetchval(f"SELECT count(*) FROM {t}")
            for t in ("whitelist_accounts", "whitelist_ledger")
        ]
        check(f"{label}: учёт и журнал пусты (услуга не выдана)", empty == [0, 0], str(empty))
        index = await conn.fetchval(
            "SELECT indexdef FROM pg_indexes WHERE indexname = "
            "'uq_servers_single_enabled_whitelist'"
        )
        check(f"{label}: частичный уникальный индекс",
              index is not None and "WHERE" in index and "whitelist" in index, str(index))
    finally:
        await conn.close()


async def verify_single_whitelist_index(base: str, db: str) -> None:
    conn = await asyncpg.connect(plain(dsn(base, db)))
    try:
        async with conn.transaction():
            await conn.execute(
                "INSERT INTO servers (name, panel_url, username, password, kind, enabled, "
                "created_at, purpose) VALUES ('wl1', 'https://wl1', 'u', 'p', 'direct', true, "
                "now(), 'whitelist'), ('wl-off', 'https://wl2', 'u', 'p', 'direct', false, "
                "now(), 'whitelist')"
            )
            try:
                async with conn.transaction():
                    await conn.execute(
                        "INSERT INTO servers (name, panel_url, username, password, kind, "
                        "enabled, created_at, purpose) VALUES ('wl2', 'https://wl3', 'u', 'p', "
                        "'direct', true, now(), 'whitelist')"
                    )
                rejected = False
            except asyncpg.UniqueViolationError:
                rejected = True
            check("индекс: второй включённый whitelist-сервер отклонён, выключенный допустим",
                  rejected)
            raise _Rollback
    except _Rollback:
        pass
    finally:
        await conn.close()


class _Rollback(Exception):
    pass


async def ensure_defaults_idempotent(base: str, db: str) -> None:
    """Старт бота (ensure_defaults) после миграции не дублирует пакеты и настройки."""
    from sqlalchemy import func, select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.db.models import TrafficPackage, WhitelistConfig
    from app.services import whitelist

    engine = create_async_engine(dsn(base, db))
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        for _ in range(2):
            async with maker() as session:
                await whitelist.ensure_defaults(session)
        async with maker() as session:
            packages = await session.scalar(select(func.count(TrafficPackage.id)))
            configs = await session.scalar(select(func.count(WhitelistConfig.id)))
        check("ensure_defaults дважды: 3 пакета, одна строка настроек",
              (packages, configs) == (3, 1), f"{packages}, {configs}")
    finally:
        await engine.dispose()


SERVICE_STATE = """
UPDATE whitelist_config SET service_enabled = true;
INSERT INTO servers (id, name, panel_url, username, password, kind, enabled, created_at,
                     purpose, inventory_status)
VALUES (10, 'Обход белых списков', 'https://wl.example.test:2053/p', 'u', 'p', 'direct', true,
        now(), 'whitelist', 'ready');
INSERT INTO server_inbounds (server_id, inbound_id, protocol, enabled, remark)
VALUES (10, 3, 'VLESS', true, 'wl');
INSERT INTO whitelist_accounts (id, user_id, free_bytes, paid_bytes, server_id, panel_email,
                                usage_checkpoint_bytes, traffic_row_id, desired_version,
                                applied_version, created_at)
VALUES (1, 2, 5368709120, 26843545600, 10, 'PAID0002', 1073741824, 41, 7, 6, now());
INSERT INTO payment_requests (id, user_id, amount, currency, period_days, status, payment_code,
                              kind, traffic_bytes, traffic_package_title, created_at,
                              confirmed_at, applied_at, apply_pending_version)
VALUES (20, 2, 99.00, 'RUB', 0, 'APPLIED', 'PAY-T20', 'traffic', 26843545600, '25 ГБ',
        now(), now(), now(), 7),
       (21, 2, 49.00, 'RUB', 0, 'APPLIED', 'PAY-T21', 'traffic', 10737418240, '10 ГБ',
        now(), now(), now(), NULL);
UPDATE payment_requests SET last_error = 'Сервер недоступен' WHERE id = 21;
INSERT INTO whitelist_ledger (user_id, kind, source_key, payment_request_id, free_before,
                              free_after, paid_before, paid_after, created_at, status, free_set,
                              paid_delta, anchor_bytes)
VALUES (2, 'free_grant', 'payment:1', 1, 0, 10737418240, 0, 0, now(), 'settled',
        10737418240, NULL, 0),
       (2, 'purchase', 'payment:20', 20, 10737418240, 10737418240, 0, 26843545600, now(),
        'pending', NULL, 26843545600, NULL);
"""


async def downgrade_cycle(base: str, db: str, original: dict[str, tuple[int, str]]) -> None:
    conn = await asyncpg.connect(plain(dsn(base, db)))
    try:
        await conn.execute(SERVICE_STATE)
    finally:
        await conn.close()

    alembic(base, db, "downgrade", "d1e2f3a4b5c6")
    conn = await asyncpg.connect(plain(dsn(base, db)))
    try:
        rows = {r["id"]: r["last_error"] for r in await conn.fetch(
            "SELECT id, last_error FROM payment_requests WHERE id IN (20, 21)")}
        check("downgrade e2f3: ожидание → прежний маркер, иные ошибки не тронуты",
              rows[20] is not None and "ожидается" in rows[20]
              and rows[21] == "Сервер недоступен", str(rows))
    finally:
        await conn.close()

    alembic(base, db, "upgrade", HEAD)
    conn = await asyncpg.connect(plain(dsn(base, db)))
    try:
        rows = {r["id"]: (r["apply_pending_version"], r["last_error"]) for r in await conn.fetch(
            "SELECT id, apply_pending_version, last_error FROM payment_requests "
            "WHERE id IN (20, 21)")}
        check("upgrade e2f3: маркер → apply_pending_version=desired_version, last_error снят",
              rows[20] == (7, None) and rows[21] == (None, "Сервер недоступен"), str(rows))
        statuses = [r[0] for r in await conn.fetch(
            "SELECT status FROM whitelist_ledger ORDER BY id")]
        check("журнал сохранил статусы событий", statuses == ["settled", "pending"],
              str(statuses))
    finally:
        await conn.close()

    alembic(base, db, "downgrade", "b7c8d9e0f1a2")
    conn = await asyncpg.connect(plain(dsn(base, db)))
    try:
        columns = {r[0] for r in await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'whitelist_ledger'")}
        ledger = await conn.fetchval("SELECT count(*) FROM whitelist_ledger")
        check("downgrade d1e2: столбцы событий удалены, строки журнала сохранены",
              "status" not in columns and ledger == 2, f"rows={ledger}")
    finally:
        await conn.close()

    alembic(base, db, "upgrade", HEAD)
    conn = await asyncpg.connect(plain(dsn(base, db)))
    try:
        statuses = [r[0] for r in await conn.fetch(
            "SELECT status FROM whitelist_ledger ORDER BY id")]
        check("повторный upgrade d1e2: прежние строки получают settled "
              "(pending теряется — поэтому runbook требует 0 ожидающих перед откатом)",
              statuses == ["settled", "settled"], str(statuses))
        # Подготовка к полному откату по runbook: данные услуги выгружены/не нужны.
        await conn.execute("DELETE FROM payment_requests WHERE kind = 'traffic'")
        await conn.execute("DELETE FROM server_inbounds WHERE server_id = 10")
        await conn.execute("DELETE FROM servers WHERE id = 10")
    finally:
        await conn.close()

    alembic(base, db, "downgrade", PRE_WHITELIST)
    restored = await snapshot(base, db)
    check("полный откат схемы к f9b2c3d4e5f6: прежние данные совпадают с исходными",
          restored == original,
          "; ".join(f"{t}: {original[t]}→{restored[t]}" for t in original
                    if original[t] != restored[t]) or "совпадают")
    conn = await asyncpg.connect(plain(dsn(base, db)))
    try:
        left = [r[0] for r in await conn.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_name IN "
            "('whitelist_accounts', 'whitelist_ledger', 'whitelist_config', "
            "'traffic_packages')")]
        check("полный откат удаляет таблицы услуги", left == [], str(left))
    finally:
        await conn.close()
    alembic(base, db, "upgrade", HEAD)
    check("повторный upgrade head после полного отката", True)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--url", required=True,
                        help="postgresql+asyncpg://user:pass@127.0.0.1:port (без имени базы)")
    parser.add_argument("--container", required=True, help="контейнер PostgreSQL для pg_dump")
    parser.add_argument("--prefix", default="wlacc")
    parser.add_argument("--dump-dir", default=None)
    args = parser.parse_args()
    host = urlparse(plain(args.url)).hostname
    if host not in ("127.0.0.1", "localhost", "::1"):
        print("Отказ: скрипт работает только с локальным тестовым PostgreSQL", file=sys.stderr)
        return 2
    user = urlparse(plain(args.url)).username or "postgres"
    prod, restore, rehearsal = (f"{args.prefix}_{n}" for n in
                                ("prod_sim", "restorecheck", "rehearsal"))

    await recreate(args.url, prod)
    alembic(args.url, prod, "upgrade", PRE_WHITELIST)
    await seed(args.url, prod)
    original = await snapshot(args.url, prod)
    check("исходная база на f9b2c3d4e5f6 с данными",
          original["alembic_version"][1] == PRE_WHITELIST
          and all(original[t][0] > 0 for t in LEGACY_TABLES), str(original))

    # Шаг 1 runbook: резервная копия и проверка восстановления в отдельную базу.
    dump = docker(args.container, "pg_dump", "-U", user, "-Fc", prod)
    dump_dir = Path(args.dump_dir or tempfile.mkdtemp(prefix="wlacc-dump-"))
    dump_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(dump_dir, 0o700)
    dump_path = dump_dir / "before-whitelist.dump"
    dump_path.write_bytes(dump)
    os.chmod(dump_path, 0o600)
    listing = docker(args.container, "pg_restore", "--list", stdin=dump).decode()
    check("pg_dump -Fc создан и читается pg_restore --list",
          len(dump) > 0 and "TABLE DATA public payment_requests" in listing,
          f"{len(dump)} байт, {dump_path}")
    await recreate(args.url, restore)
    docker(args.container, "pg_restore", "-U", user, "-d", restore, "--no-owner",
           "--exit-on-error", stdin=dump)
    restored = await snapshot(args.url, restore)
    check("восстановление в отдельную базу совпадает с источником", restored == original,
          "; ".join(f"{t}: {original[t]}→{restored[t]}" for t in original
                    if original[t] != restored[t]) or "совпадают")

    # Шаг 3 runbook: миграция.
    out = alembic(args.url, prod, "upgrade", "head")
    check("alembic upgrade head: три ревизии услуги",
          all(rev in out for rev in ("b7c8d9e0f1a2", "d1e2f3a4b5c6", HEAD)))
    await verify_head(args.url, prod, original, "prod_sim")
    await verify_single_whitelist_index(args.url, prod)
    await ensure_defaults_idempotent(args.url, prod)

    # Репетиция на восстановленной копии.
    await recreate(args.url, rehearsal)
    docker(args.container, "pg_restore", "-U", user, "-d", rehearsal, "--no-owner",
           "--exit-on-error", stdin=dump)
    alembic(args.url, rehearsal, "upgrade", "head")
    await verify_head(args.url, rehearsal, original, "rehearsal")

    # Откат схемы с данными услуги.
    await downgrade_cycle(args.url, prod, original)

    # Расхождения моделей и схемы на PostgreSQL. Три расхождения существовали до
    # услуги (индексы старых миграций и тип EncryptedString) и считаются долгом.
    known = (
        "removed index 'ix_pending_server_updates_status_server'",
        "removed index 'ix_web_deliveries_due'",
        "to EncryptedString(length=1024) on 'servers.password'",
    )
    try:
        alembic(args.url, prod, "check")
        check("alembic check: схема совпадает с моделями", True)
    except RuntimeError as exc:
        detected = [
            line.split("Detected ", 1)[1] for line in str(exc).splitlines()
            if "Detected" in line and "sequence named" not in line
        ]
        new = [line for line in detected if not any(k in line for k in known)]
        check("alembic check: нет новых расхождений (прежний долг: "
              f"{len(detected) - len(new)})", not new, " | ".join(new)[:900])

    failed = [name for name, ok, _ in results if not ok]
    print(f"\nИтого: {len(results) - len(failed)} OK, {len(failed)} FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(asyncio.run(main()))

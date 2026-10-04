"""Сверка «Обход белых списков»: БД бота против whitelist-панели (только чтение).

Запуск в контейнере бота после выдачи услуги:
    python -m ops.whitelist_check            # сводка
    python -m ops.whitelist_check --details  # + строки расхождений (без секретов)

Панель только читается (clients/get, clients/traffic); БД не изменяется:
транзакция откатывается. Выводятся public_id и числа, без UUID/паролей/ссылок.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime

from sqlalchemy import select

from app.config import get_settings
from app.db.models import User, VpnClient, WhitelistAccount
from app.db.repositories import VpnClientRepository
from app.db.session import get_engine, get_sessionmaker
from app.services import whitelist
from app.services.panel_updater import QuotaClientState
from app.services.xui_updater import build_updater


async def main(details: bool) -> int:
    settings = get_settings()
    updater = build_updater(timeout=float(settings.xui_request_timeout))
    now = datetime.now(UTC)
    problems: list[str] = []
    counts = {"accounts": 0, "checked": 0, "missing_on_panel": 0, "read_errors": 0,
              "mismatch": 0, "pending": 0, "conflicts": 0, "blocked": 0,
              "unsettled": 0, "uncertain": 0}
    async with get_sessionmaker()() as session:
        config = await whitelist.get_config(session)
        server = await whitelist.get_active_server(session)
        server_label = f"#{server.id}" if server else "—"
        print(f"service_enabled={config.service_enabled} server={server_label} "
              f"ready={whitelist.server_ready(server)}")
        if not whitelist.server_ready(server):
            await session.rollback()
            return 2
        assert server is not None
        accounts = (await session.scalars(select(WhitelistAccount))).all()
        counts["accounts"] = len(accounts)
        emails = [a.panel_email for a in accounts if a.panel_email]
        states = await updater.read_quota_clients(server, emails)
        for account in accounts:
            user = await session.get(User, account.user_id)
            client: VpnClient | None = await VpnClientRepository(session).get_for_user(
                account.user_id
            )
            label = user.public_id if user else f"user#{account.user_id}"
            events = await whitelist.list_open_events(session, account.user_id)
            uncertain = any(e.status == whitelist.EVENT_UNCERTAIN for e in events)
            counts["unsettled"] += int(bool(events) and not uncertain)
            counts["uncertain"] += int(uncertain)
            if uncertain:
                problems.append(f"{label}: начисление ждёт решения (/wl, /wlresolve)")
            counts["pending"] += int(account.desired_version > account.applied_version)
            counts["conflicts"] += int(account.conflict is not None)
            counts["blocked"] += int(account.admin_blocked)
            if not account.panel_email:
                continue
            state = states.get(account.panel_email)
            if not isinstance(state, QuotaClientState):
                key = "missing_on_panel" if state is None else "read_errors"
                counts[key] += 1
                problems.append(f"{label}: {key}")
                continue
            counts["checked"] += 1
            access = whitelist.access_state(client, now)
            # Несверенные начисления входят в квоту нижней границей остатка.
            target = whitelist.compute_target(account, access, now, events)
            issues = []
            if state.total_bytes != target.total_bytes:
                issues.append(f"totalGB panel={state.total_bytes} target={target.total_bytes}")
            if state.expiry_ms != target.expiry_ms:
                issues.append(f"expiry panel={state.expiry_ms} target={target.expiry_ms}")
            if state.enable and not target.enable:
                issues.append("panel enabled, target disabled")
            if not state.enable and target.enable and not state.depleted:
                issues.append("panel disabled, target enabled")
            if (
                state.used_bytes is not None
                and account.usage_checkpoint_bytes is not None
                and state.used_bytes < account.usage_checkpoint_bytes
            ):
                issues.append("panel counter below checkpoint (reset?)")
            if issues:
                counts["mismatch"] += 1
                problems.append(f"{label}: " + "; ".join(issues))
        await session.rollback()
    print(" ".join(f"{key}={value}" for key, value in counts.items()))
    if details:
        for line in problems:
            print(line)
    await get_engine().dispose()
    # Расхождения с ожидающим применением ожидаемы до прохода фоновой очереди.
    return 1 if counts["mismatch"] or counts["read_errors"] else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--details", action="store_true")
    raise SystemExit(asyncio.run(main(parser.parse_args().details)))

"""Сверка «Обход белых списков»: БД бота против whitelist-панели (только чтение).

Запуск в контейнере бота после выдачи услуги:
    python -m ops.whitelist_check            # сводка
    python -m ops.whitelist_check --details  # + строки расхождений (без секретов)

Панель только читается (clients/get, clients/traffic, inbounds/list); БД не
изменяется: транзакция откатывается. Выводятся public_id и числа, без
UUID/паролей/ссылок.

Размещение (с 2026-10-06): клиент привязан к целевому inbound'у с его flow, привязки
услуги к прежним целям сняты (``placement_mismatch`` — фактическое расхождение на
панели); ``placement_pending`` — размещение в БД ещё не подтверждено очередью
(перенос не завершён). Чужие привязки клиента расхождением не считаются.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import User, VpnClient, WhitelistAccount, WhitelistPlacement
from app.db.repositories import VpnClientRepository
from app.db.session import get_engine, get_sessionmaker
from app.services import whitelist
from app.services.panel_updater import PanelUpdater, QuotaClientState
from app.services.xui_updater import build_updater


async def collect(
    session: AsyncSession, updater: PanelUpdater, now: datetime
) -> tuple[dict[str, int], list[str]] | None:
    """Сверка учётов с панелью; None — сервер услуги не готов."""
    problems: list[str] = []
    counts = {"accounts": 0, "checked": 0, "missing_on_panel": 0, "read_errors": 0,
              "mismatch": 0, "pending": 0, "conflicts": 0, "blocked": 0,
              "unsettled": 0, "uncertain": 0, "placement_mismatch": 0,
              "placement_pending": 0}
    server = await whitelist.get_active_server(session)
    if not whitelist.server_ready(server):
        return None
    assert server is not None
    progress = await whitelist.placement_progress(session, server)
    if progress is not None:
        counts["placement_pending"] = progress.pending + progress.failed
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
        last_read = whitelist.last_known_usage(account, events)
        if (
            state.used_bytes is not None
            and last_read is not None
            and state.used_bytes < last_read
        ):
            issues.append("panel counter below last reading (reset?)")
        if issues:
            counts["mismatch"] += 1
            problems.append(f"{label}: " + "; ".join(issues))
        placements = (
            await session.scalars(
                select(WhitelistPlacement).where(WhitelistPlacement.user_id == account.user_id)
            )
        ).all()
        drift = whitelist.placement_drift(server, state, list(placements))
        if drift is not None:
            counts["placement_mismatch"] += 1
            problems.append(f"{label}: размещение — {drift}")
    return counts, problems


async def main(details: bool) -> int:
    settings = get_settings()
    updater = build_updater(timeout=float(settings.xui_request_timeout))
    now = datetime.now(UTC)
    async with get_sessionmaker()() as session:
        config = await whitelist.get_config(session)
        server = await whitelist.get_active_server(session)
        server_label = f"#{server.id}" if server else "—"
        print(f"service_enabled={config.service_enabled} server={server_label} "
              f"ready={whitelist.server_ready(server)}")
        result = await collect(session, updater, now)
        await session.rollback()
    await get_engine().dispose()
    if result is None:
        return 2
    counts, problems = result
    print(" ".join(f"{key}={value}" for key, value in counts.items()))
    if details:
        for line in problems:
            print(line)
    # Расхождения с ожидающим применением ожидаемы до прохода фоновой очереди.
    failed = counts["mismatch"] or counts["read_errors"] or counts["placement_mismatch"]
    return 1 if failed else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--details", action="store_true")
    raise SystemExit(asyncio.run(main(parser.parse_args().details)))

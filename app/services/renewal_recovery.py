"""Восстановление обычных VPN-продлений после сбоев панелей и рестартов.

Один проход фонового worker'а восстановления: возобновляет подтверждения оплат,
прерванные после фиксации целевого срока, и применяет очередь отложенных
обновлений обычных серверов. Не зависит от проверки доступности серверов
(``SERVER_HEALTH_POLL_SECONDS``): backoff каждой записи определяет, когда к
панели обращаться снова. Квоты «Обхода белых списков» ведёт отдельная очередь.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import billing, pending_updates
from app.services.panel_updater import PanelUpdater

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RecoveryReport:
    payments_recovered: int = 0
    updates_applied: int = 0
    updates_failed: int = 0

    @property
    def changed(self) -> bool:
        """Панели изменены и изменения зафиксированы в БД — нужен SubHub sync."""
        return self.payments_recovered > 0 or self.updates_applied > 0


async def run_once(
    session: AsyncSession,
    updater: PanelUpdater,
    *,
    backoff: pending_updates.RetryBackoff,
) -> RecoveryReport:
    """Один проход восстановления; ошибка одного шага не отменяет другой.

    Сначала возобновляются подтверждения: их недоступные панели попадают в
    очередь отложенных обновлений, которую обрабатывает второй шаг.
    """
    report = RecoveryReport()
    try:
        report.payments_recovered = await billing.recover_confirmed_payments(
            session, updater, backoff=backoff
        )
    except Exception:  # noqa: BLE001 - очередь обновлений обслуживается всё равно
        await session.rollback()
        logger.exception("Ошибка возобновления прерванных оплат")
    try:
        results = await pending_updates.process_due(session, updater)
    except Exception:  # noqa: BLE001 - повтор в следующем цикле
        await session.rollback()
        logger.exception("Ошибка обработки отложенных обновлений серверов")
        results = []
    report.updates_applied = sum(1 for item in results if item.ok and not item.already_done)
    report.updates_failed = sum(1 for item in results if not item.ok)
    if report.payments_recovered or results:
        logger.info(
            "Восстановление продлений: оплат возобновлено=%s, обновлений применено=%s, "
            "отложено снова=%s",
            report.payments_recovered,
            report.updates_applied,
            report.updates_failed,
        )
    return report

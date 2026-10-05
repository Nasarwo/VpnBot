"""Приёмка: происхождение текущего доступа при выдаче услуги нынешним пользователям.

``trial_used`` остаётся истинным после перехода на оплату, поэтому trial
определяется только при отсутствии оплаты, покрывающей текущий срок; доступ без
оплаты и без следа trial (привязка, ручное продление) — неоднозначный.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.db.enums import PaymentStatus
from app.db.models import PaymentRequest
from app.services import whitelist
from app.services.panel_updater import MockPanelUpdater
from tests.test_whitelist import service_on, wl_server  # noqa: F401

GIB = whitelist.GIB
NOW = datetime.now(UTC)


def _payment(user, status, target, code):
    return PaymentRequest(
        user_id=user.id, amount=175, period_days=30, payment_code=code,
        status=status, target_expires_at=target,
    )


@pytest.mark.parametrize(
    ("trial_used", "payments", "expires", "expected"),
    [
        # trial → оплата: флаг trial остался, но текущий срок покрыт оплатой.
        (True, [(PaymentStatus.APPLIED, 20)], 20, whitelist.ORIGIN_PAID),
        (True, [], 2, whitelist.ORIGIN_TRIAL),
        # Оплата была, но истекла; доступ продлён вручную — не trial и не оплата.
        (True, [(PaymentStatus.APPLIED, -10)], 15, whitelist.ORIGIN_AMBIGUOUS),
        # Привязанная старая подписка без оплат и без trial.
        (False, [], 40, whitelist.ORIGIN_AMBIGUOUS),
        # Отклонённая заявка не делает доступ оплаченным.
        (False, [(PaymentStatus.REJECTED, 30)], 30, whitelist.ORIGIN_AMBIGUOUS),
        (False, [], None, whitelist.ORIGIN_LIFETIME),
        (True, [(PaymentStatus.APPLIED, -1)], -1, whitelist.ORIGIN_INACTIVE),
    ],
)
async def test_origin_of_current_access(
    session, user, vpn_client, trial_used, payments, expires, expected
):
    user.trial_used = trial_used
    vpn_client.is_active = True
    vpn_client.expires_at = None if expires is None else NOW + timedelta(days=expires)
    for index, (status, days) in enumerate(payments):
        session.add(_payment(user, status, NOW + timedelta(days=days), f"PAY-O{index}"))
    await session.commit()
    await session.refresh(vpn_client, ["mappings"])
    assert await whitelist.classify_origin(session, user, vpn_client, NOW) == expected


@pytest.mark.parametrize(
    ("include_ambiguous", "granted", "free"),
    [(False, {}, 0), (True, {"ambiguous": 1}, 10 * GIB)],
)
async def test_rollout_handles_ambiguous_users_by_admin_choice(
    session, user, vpn_client, service_on, include_ambiguous, granted, free  # noqa: F811
):
    vpn_client.is_active = True
    vpn_client.expires_at = NOW + timedelta(days=40)  # привязка без оплат и trial
    await session.commit()
    plan = await whitelist.rollout_plan(session)
    assert plan.counts == {"ambiguous": 1} and len(plan.ambiguous_users) == 1
    report = await whitelist.run_rollout(
        session, MockPanelUpdater(), include_ambiguous=include_ambiguous, actor_user_id=None
    )
    assert report.granted == granted
    assert report.skipped_ambiguous == (0 if include_ambiguous else 1)
    account = await whitelist.get_account(session, user.id)
    assert (account.free_bytes if account else 0) == free

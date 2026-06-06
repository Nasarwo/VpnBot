from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.services import payments, plans


def test_plan_catalog():
    by_code = {p.code: p for p in plans.PLANS}
    assert by_code["1m"].amount_rub == 175
    assert by_code["1m"].period_days == 30
    assert by_code["6m"].amount_rub == 850
    assert by_code["6m"].period_days == 180
    assert by_code["12m"].amount_rub == 1600
    assert by_code["12m"].period_days == 360


def test_plan_savings():
    by_code = {p.code: p for p in plans.PLANS}
    assert by_code["1m"].savings_rub == 0
    assert by_code["6m"].savings_rub == 200
    assert by_code["12m"].savings_rub == 500


def test_get_plan():
    assert plans.get_plan("6m").title == "6 месяцев"
    assert plans.get_plan("unknown") is None


async def test_create_request_with_plan(session: AsyncSession, user: User):
    plan = plans.get_plan("6m")
    payment = await payments.create_request(
        session,
        user_id=user.id,
        amount=float(plan.amount_rub),
        period_days=plan.period_days,
    )
    assert float(payment.amount) == 850.0
    assert payment.period_days == 180


async def test_changing_plan_updates_open_request(session: AsyncSession, user: User):
    p1 = await payments.create_request(
        session, user_id=user.id, amount=175, period_days=30
    )
    p2 = await payments.create_request(
        session, user_id=user.id, amount=1600, period_days=360
    )
    assert p1.id == p2.id
    assert float(p2.amount) == 1600.0
    assert p2.period_days == 360

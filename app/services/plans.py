from __future__ import annotations

from dataclasses import dataclass

# Базовая месячная цена используется для расчёта выгоды относительно
# помесячной оплаты.
MONTHLY_PRICE_RUB = 175


@dataclass(frozen=True, slots=True)
class PaymentPlan:
    code: str
    title: str
    months: int
    period_days: int
    amount_rub: int

    @property
    def savings_rub(self) -> int:
        """Выгода относительно помесячной оплаты за тот же срок."""
        return MONTHLY_PRICE_RUB * self.months - self.amount_rub


PLANS: tuple[PaymentPlan, ...] = (
    PaymentPlan(code="1m", title="1 месяц", months=1, period_days=30, amount_rub=175),
    PaymentPlan(code="6m", title="6 месяцев", months=6, period_days=180, amount_rub=850),
    PaymentPlan(code="12m", title="1 год", months=12, period_days=360, amount_rub=1600),
)

_PLANS_BY_CODE: dict[str, PaymentPlan] = {plan.code: plan for plan in PLANS}


def get_plan(code: str) -> PaymentPlan | None:
    return _PLANS_BY_CODE.get(code)

"""Отображение объёмов «Обхода белых списков» (D-4).

Заданный объём (пакет, начисление, бесплатный пакет) показывается так, как его ввёл
администратор; текущий остаток округляется вниз, чтобы не обещать лишнего. Учёт и API
панели остаются целыми байтами: gib_to_bytes по-прежнему усекает дробные байты.
"""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.bot import admin_handlers, keyboards, texts
from app.db.enums import PaymentStatus
from app.db.models import PAYMENT_KIND_TRAFFIC, PaymentRequest, TrafficPackage, User
from app.services import payments, whitelist
from app.services.panel_updater import QuotaTarget

GIB = whitelist.GIB

# (ввод администратора, байты после усечения, заданный объём на экране)
SET_VOLUMES = [
    ("0,02", 21474836, "0,02 ГБ"),
    ("0.02", 21474836, "0,02 ГБ"),
    ("0,1", 107374182, "0,1 ГБ"),
    ("1,1", 1181116006, "1,1 ГБ"),
    ("3", 3 * GIB, "3 ГБ"),
    ("10", 10 * GIB, "10 ГБ"),
    ("25", 25 * GIB, "25 ГБ"),
    ("50", 50 * GIB, "50 ГБ"),
    ("0,005", 5368709, "0,005 ГБ"),
]
IDS = [case[0] for case in SET_VOLUMES]


def _payment(size_bytes: int, **extra) -> PaymentRequest:
    fields = {
        "id": 1, "user_id": 1, "amount": Decimal("49"), "period_days": 0,
        "kind": PAYMENT_KIND_TRAFFIC, "traffic_bytes": size_bytes,
        "payment_code": "PAY-D4", "status": PaymentStatus.WAITING_ADMIN,
        "created_at": datetime(2026, 10, 5, tzinfo=UTC),
    }
    fields.update(extra)
    return PaymentRequest(**fields)


@pytest.mark.parametrize(("raw", "size_bytes", "shown"), SET_VOLUMES, ids=IDS)
def test_accounting_stays_integer_truncated_bytes(raw, size_bytes, shown):
    parsed = admin_handlers._parse_gb(raw)
    assert parsed == size_bytes and type(parsed) is int
    assert whitelist.gib_to_bytes(Decimal(raw.replace(",", "."))) == size_bytes
    # Покупаемый остаток не увеличивается ради текста: не больше введённого объёма.
    assert size_bytes <= Decimal(raw.replace(",", ".")) * GIB
    assert type(QuotaTarget(total_bytes=size_bytes, enable=True, expiry_ms=1).total_bytes) is int


@pytest.mark.parametrize(("raw", "size_bytes", "shown"), SET_VOLUMES, ids=IDS)
def test_set_volume_is_shown_as_entered(raw, size_bytes, shown):
    package = TrafficPackage(id=7, traffic_bytes=size_bytes, price=Decimal("49"), enabled=True)

    # Карточки пакетов: кнопка пользователя, админская кнопка, списки.
    assert texts.whitelist_package_button(package) == f"{shown} — 49 ₽"
    buttons = [
        b.text for row in keyboards.whitelist_keyboard(
            whitelist.Overview(status="active", can_buy=True, packages=[package])
        ).inline_keyboard for b in row
    ]
    assert f"{shown} — 49 ₽" in buttons
    admin_buttons = [
        b.text for row in keyboards.admin_whitelist_packages_keyboard([package]).inline_keyboard
        for b in row
    ]
    assert f"#7: {shown} — 49 ₽" in admin_buttons
    assert f"#7: {shown} — 49 ₽ — включён" in texts.admin_whitelist_packages([package])
    overview = whitelist.Overview(
        status="active", free_bytes=GIB, can_buy=True, packages=[package],
    )
    assert f"• {shown} — 49 ₽" in texts.whitelist_overview(overview, 10 * GIB)

    # Заявки: создание, ожидание проверки, карточка и списки администратора.
    payment = _payment(size_bytes)
    assert f"Трафик «Обход белых списков»: {shown}" in texts.payment_created(payment, "x")
    assert f"покупка трафика, {shown}" in texts.payment_pending_review(payment)
    assert f"Покупка трафика «Обход белых списков»: {shown}" in texts.admin_payment_card(
        payment, SimpleNamespace(username=None, public_id=None, telegram_id=5)
    )
    assert f"трафик {shown}" in texts.admin_history([payment])
    pending = _payment(size_bytes, user=User(username="u"))
    assert f"трафик {shown}" in texts.admin_pending([pending])

    # Уведомления о начислении и ответ администратору.
    assert f"Начислено {shown} трафика" in texts.traffic_credited(size_bytes, pending=False)
    assert f"Начислено {shown} трафика" in texts.traffic_credited_expired(size_bytes)

    # Журнал начислений и обещанные пользователю суммы — тоже заданные объёмы.
    awaiting = whitelist.AwaitingCredit(free_set=size_bytes, paid_delta=size_bytes)
    waiting = whitelist.Overview(status="active", free_bytes=GIB, awaiting=[awaiting])
    screen = texts.whitelist_overview(waiting, size_bytes)
    assert f"бесплатный остаток будет восстановлен до {shown}" in screen
    assert f"купленный трафик +{shown}" in screen
    assert f"восстанавливает бесплатный остаток до {shown}. Купленный" in screen
    event = SimpleNamespace(
        id=3, created_at=datetime(2026, 10, 5, tzinfo=UTC), free_set=size_bytes,
        paid_delta=size_bytes, status="pending", note=None,
    )
    assert f"бесплатный := {shown}, купленный +{shown}" in texts._wl_event_label(event)

    # Настройки услуги и план выдачи.
    config = SimpleNamespace(
        service_enabled=True, paid_free_bytes=size_bytes, trial_free_bytes=size_bytes,
    )
    summary = SimpleNamespace(
        accounts=0, pending=0, errors=0, conflicts=0, blocked=0, unsettled=0, uncertain=0,
        reconcile=None,
    )
    home = texts.admin_whitelist_home(config, None, summary, [package])
    assert f"Бесплатно за оплату подписки: {shown}" in home
    assert f"Бесплатно за пробный период: {shown}" in home
    assert f"#7: {shown} — 49 ₽" in home
    plan = SimpleNamespace(counts={}, already_served=0, ambiguous_users=[])
    rollout = texts.admin_whitelist_rollout_plan(plan, config)
    assert f"→ {shown}" in rollout
    assert texts.fmt_gb_set(size_bytes) == shown


@pytest.mark.parametrize(("raw", "size_bytes", "shown"), SET_VOLUMES, ids=IDS)
def test_package_title_snapshot_for_new_requests_matches_display(raw, size_bytes, shown):
    package = TrafficPackage(id=7, traffic_bytes=size_bytes, price=Decimal("49"), enabled=True)
    assert payments.whitelist_package_title(package) == shown.replace(",", ".")


@pytest.mark.parametrize(
    ("size_bytes", "shown"),
    [
        (0, "0 ГБ"),
        (1, "0 ГБ"),                       # малый остаток не округляется вверх
        (5 * 1024 * 1024, "0 ГБ"),         # 5 МиБ меньше сотой доли гигабайта
        (21474836, "0,01 ГБ"),             # остаток от 0,02 ГБ: вниз, не вверх
        (1181116006, "1,09 ГБ"),           # остаток от 1,1 ГБ: вниз, не вверх
        (10 * GIB - 1, "9,99 ГБ"),
        (10 * GIB, "10 ГБ"),
        (int(7.5 * GIB), "7,5 ГБ"),
        (None, "0 ГБ"),
        (-5, "0 ГБ"),
    ],
)
def test_remainder_is_rounded_down(size_bytes, shown):
    assert texts.fmt_gb(size_bytes) == shown


def test_set_volume_and_remainder_differ_for_same_bytes():
    credited = 21474836
    assert texts.fmt_gb_set(credited) == "0,02 ГБ"
    assert texts.fmt_gb(credited) == "0,01 ГБ"
    assert texts.fmt_gb_set(0) == "0 ГБ" and texts.fmt_gb_set(None) == "0 ГБ"
    assert texts.fmt_gb_set(-1) == "0 ГБ"


def test_set_volume_never_exceeds_what_bytes_can_prove():
    # Байты, не соответствующие вводу до 4 знаков (например, пересчитанное значение), не
    # округляются вверх: показывается усечённое значение.
    assert texts.fmt_gb_set(10 * GIB - 1) == "9,99 ГБ"
    assert texts.fmt_gb_set(5 * 1024 * 1024) == "0 ГБ"


def test_remainder_on_admin_user_screen_is_floor_and_exact_bytes():
    account = SimpleNamespace(
        free_bytes=21474836, paid_bytes=1181116006, usage_checkpoint_bytes=0,
        last_synced_at=None, applied_total_bytes=0, applied_enable=True,
        applied_version=1, desired_version=1, admin_blocked=False, last_error=None,
        conflict=None,
    )
    overview = whitelist.Overview(status="active")
    user = SimpleNamespace(public_id="X", telegram_id=5)
    card = texts.admin_whitelist_user(user, account, overview)
    assert "Бесплатный: 0,01 ГБ (21474836 байт)" in card
    assert "Купленный: 1,09 ГБ (1181116006 байт)" in card

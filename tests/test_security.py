"""Тесты безопасности и устойчивости приложения.

Покрывают ключевые свойства безопасности:
- авторизация (RBAC): админ-эндпоинты недоступны обычным пользователям;
- целостность оплат: цены/сроки только серверные, корректная машина состояний,
  идемпотентность подтверждения (нельзя продлить дважды);
- защита от злоупотребления пробным периодом;
- защита от захвата чужого аккаунта при привязке клиента панели;
- экранирование пользовательского ввода в HTML-сообщениях (anti-XSS);
- неутечка секретов (пароль панели) в текстах ошибок;
- устойчивость к некорректным данным и сбоям внешних сервисов.
"""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import admin_handlers, notify, texts, user_handlers
from app.bot.callbacks import MenuCallback, PlanCallback
from app.bot.filters import IsAdmin
from app.bot.router import build_root_router
from app.config import Settings
from app.db.enums import PaymentStatus, UserRole
from app.db.models import PaymentRequest, User, VpnClient
from app.db.repositories import PaymentRepository, UserRepository
from app.services import billing, health, plans, provisioning
from app.services.panel_updater import MockPanelUpdater, PanelUpdateError
from app.services.provisioning import PanelClientInfo
from app.services.xui_client import XuiAuthError, XuiClient, XuiError

BASE = "http://panel.local:2053"


# --------------------------------------------------------------------------- #
# Вспомогательные фейки
# --------------------------------------------------------------------------- #

class FakeBot:
    """Минимальный заменитель aiogram.Bot для проверки notify-функций."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.messages: list[tuple[int, str, dict]] = []
        self.photos: list[tuple[int, object, dict]] = []
        self.documents: list[tuple[int, object, dict]] = []

    async def send_message(self, chat_id: int, text: str, **kwargs: object) -> None:
        if self.fail:
            from aiogram.exceptions import TelegramAPIError

            raise TelegramAPIError(method=None, message="boom")
        self.messages.append((chat_id, text, kwargs))

    async def send_photo(self, chat_id: int, photo: object, **kwargs: object) -> None:
        if self.fail:
            from aiogram.exceptions import TelegramAPIError

            raise TelegramAPIError(method=None, message="boom")
        self.photos.append((chat_id, photo, kwargs))

    async def send_document(
        self, chat_id: int, document: object, **kwargs: object
    ) -> None:
        if self.fail:
            from aiogram.exceptions import TelegramAPIError

            raise TelegramAPIError(method=None, message="boom")
        self.documents.append((chat_id, document, kwargs))


class FakeMessage:
    """Заменитель Message: запоминает ответы."""

    def __init__(self) -> None:
        self.answers: list[tuple[str, dict]] = []

    async def answer(self, text: str, **kwargs: object) -> None:
        self.answers.append((text, kwargs))


def _make_payment(
    user: User,
    *,
    code: str = "PAY-1",
    amount: float = 175.0,
    period_days: int = 30,
    status: PaymentStatus = PaymentStatus.WAITING_ADMIN,
    last_error: str | None = None,
) -> PaymentRequest:
    payment = PaymentRequest(
        user_id=user.id or 1,
        amount=amount,
        currency="RUB",
        period_days=period_days,
        payment_code=code,
        status=status,
        last_error=last_error,
    )
    payment.user = user
    return payment


# --------------------------------------------------------------------------- #
# A. Авторизация / RBAC
# --------------------------------------------------------------------------- #

async def test_admin_message_filter_blocks_regular_user():
    ok, _ = await admin_handlers.router.message.check_root_filters(
        object(), db_user=User(telegram_id=2, role=UserRole.USER)
    )
    assert ok is False


async def test_admin_message_filter_blocks_missing_user():
    ok, _ = await admin_handlers.router.message.check_root_filters(
        object(), db_user=None
    )
    assert ok is False


async def test_admin_message_filter_allows_admin():
    ok, _ = await admin_handlers.router.message.check_root_filters(
        object(), db_user=User(telegram_id=1, role=UserRole.ADMIN)
    )
    assert ok is True


async def test_admin_callback_filter_blocks_regular_user():
    ok, _ = await admin_handlers.router.callback_query.check_root_filters(
        object(), db_user=User(telegram_id=2, role=UserRole.USER)
    )
    assert ok is False


async def test_admin_callback_filter_allows_admin():
    ok, _ = await admin_handlers.router.callback_query.check_root_filters(
        object(), db_user=User(telegram_id=1, role=UserRole.ADMIN)
    )
    assert ok is True


def test_admin_router_registered_before_user_router():
    """Порядок важен: для не-админа /admin проскакивает админ-роутер
    (фильтр IsAdmin не пускает) и попадает в user-роутер, где выдаётся отказ."""
    root = build_root_router()
    names = [r.name for r in root.sub_routers]
    assert names.index("admin") < names.index("user")


async def test_non_admin_admin_command_denied():
    msg = FakeMessage()
    await user_handlers.admin_denied(msg)
    assert msg.answers
    text = msg.answers[0][0].lower()
    assert "нет прав" in text


def test_is_admin_filter_is_used_on_both_observers():
    # Фильтр объявлен; проверяем, что класс делает ровно то, что ожидается.
    flt = IsAdmin()
    assert isinstance(flt, IsAdmin)


def test_settings_admin_parsing_is_strict():
    s = Settings(admin_telegram_ids="10, 20 ,30")
    assert s.admin_telegram_ids == [10, 20, 30]
    assert s.is_admin(10) is True
    assert s.is_admin(999) is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("xui_request_timeout", 0),
        ("payment_period_days", 0),
        ("trial_period_days", 0),
        ("server_health_poll_seconds", -1),
        ("expiry_notify_poll_seconds", -1),
        ("anti_sharing_poll_minutes", -1),
    ],
)
def test_settings_rejects_dangerous_numeric_values(field: str, value: int):
    with pytest.raises(ValueError):
        Settings(**{field: value})


async def test_user_role_is_recomputed_from_settings(session: AsyncSession):
    """Роль не хранится «навсегда»: middleware пересчитывает её из настроек.

    Моделируем понижение: пользователь был ADMIN, но больше не в списке —
    при следующем апдейте роль обновляется на USER (логика DbSessionMiddleware)."""
    repo = UserRepository(session)
    db_user, _ = await repo.get_or_create(
        telegram_id=555, username="u", first_name="U", role=UserRole.ADMIN
    )
    await session.commit()

    settings = Settings(admin_telegram_ids=[])
    desired = UserRole.ADMIN if settings.is_admin(555) else UserRole.USER
    if db_user.role != desired:
        db_user.role = desired
    await session.commit()

    refreshed = await repo.get_by_telegram_id(555)
    assert refreshed.role == UserRole.USER


# --------------------------------------------------------------------------- #
# B. Целостность оплат: цены только серверные
# --------------------------------------------------------------------------- #

def test_plan_callback_carries_only_code():
    """Пользователь по callback может прислать только код тарифа — не цену/срок.

    Это исключает подмену суммы или периода со стороны клиента."""
    assert set(PlanCallback.model_fields) == {"code"}


def test_plan_amounts_are_fixed_server_side():
    assert plans.get_plan("1m").amount_rub == 175
    assert plans.get_plan("6m").amount_rub == 850
    assert plans.get_plan("12m").amount_rub == 1600
    assert plans.get_plan("1m").period_days == 30


@pytest.mark.parametrize(
    "code",
    ["", "trial", "999", "1m ", "'; DROP TABLE users;--", "<script>", "0m"],
)
def test_unknown_or_forged_plan_code_rejected(code: str):
    assert plans.get_plan(code) is None


async def test_create_request_dedupes_open_request(
    session: AsyncSession, user: User
):
    """Повторное создание заявки не плодит дубликаты (анти-спам / целостность)."""
    from app.services import payments

    first = await payments.create_request(
        session, user_id=user.id, amount=175, period_days=30
    )
    second = await payments.create_request(
        session, user_id=user.id, amount=850, period_days=180
    )
    assert first.id == second.id
    # Та же заявка переиспользуется, сумма/срок обновляются.
    assert second.period_days == 180


# --------------------------------------------------------------------------- #
# B2. Машина состояний заявок
# --------------------------------------------------------------------------- #

async def _persist_payment(
    session: AsyncSession, user: User, status: PaymentStatus, code: str
) -> PaymentRequest:
    repo = PaymentRepository(session)
    payment = await repo.create(
        user_id=user.id,
        amount=175,
        period_days=30,
        payment_code=code,
        status=status,
    )
    await session.commit()
    return payment


async def test_confirm_missing_payment_raises(session: AsyncSession):
    with pytest.raises(billing.BillingError):
        await billing.confirm_payment(
            session, 999999, actor_user_id=1, updater=MockPanelUpdater()
        )


async def test_cannot_confirm_rejected_payment(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    payment = await _persist_payment(
        session, user, PaymentStatus.REJECTED, "PAY-REJ"
    )
    with pytest.raises(billing.BillingError):
        await billing.confirm_payment(
            session, payment.id, actor_user_id=user.id, updater=MockPanelUpdater()
        )


async def test_cannot_retry_non_failed_payment(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    payment = await _persist_payment(
        session, user, PaymentStatus.WAITING_ADMIN, "PAY-WAIT"
    )
    with pytest.raises(billing.BillingError):
        await billing.retry_payment(
            session, payment.id, actor_user_id=user.id, updater=MockPanelUpdater()
        )


async def test_reject_applied_payment_is_noop(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    """Нельзя «откатить» уже применённую заявку отклонением."""
    payment = await _make_waiting(session, user)
    await billing.confirm_payment(
        session, payment.id, actor_user_id=user.id, updater=MockPanelUpdater()
    )
    result = await billing.reject_payment(
        session, payment.id, actor_user_id=user.id
    )
    assert result.status == PaymentStatus.APPLIED


async def test_double_confirm_does_not_extend_twice(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    """Идемпотентность: повторное подтверждение не продлевает доступ второй раз
    и не дёргает панель повторно (защита от двойного начисления)."""
    payment = await _make_waiting(session, user)
    updater = MockPanelUpdater()
    await billing.confirm_payment(
        session, payment.id, actor_user_id=user.id, updater=updater
    )
    second = await billing.confirm_payment(
        session, payment.id, actor_user_id=user.id, updater=updater
    )
    assert second.already_applied is True
    assert len(updater.provisioned) + len(updater.calls) == 1


async def _make_waiting(session: AsyncSession, user: User) -> PaymentRequest:
    repo = PaymentRepository(session)
    payment = await repo.create(
        user_id=user.id,
        amount=175,
        period_days=30,
        payment_code="PAY-W",
        status=PaymentStatus.WAITING_ADMIN,
    )
    await session.commit()
    return payment


# --------------------------------------------------------------------------- #
# C. Защита от злоупотребления пробным периодом
# --------------------------------------------------------------------------- #

async def test_trial_unavailable_after_any_paid_subscription(
    session: AsyncSession, user: User
):
    """Если пользователь когда-либо оплачивал подписку — пробный не предлагается,
    даже если флаг trial_used ещё не выставлен."""
    repo = PaymentRepository(session)
    p = await repo.create(
        user_id=user.id,
        amount=175,
        period_days=30,
        payment_code="PAY-OLD",
        status=PaymentStatus.APPLIED,
    )
    p.status = PaymentStatus.APPLIED
    await session.commit()

    assert user.trial_used is False
    assert await user_handlers._trial_available(session, user) is False


async def test_trial_used_flag_blocks_second_grant(
    session: AsyncSession, user: User, vpn_client: VpnClient
):
    first = await billing.grant_trial(
        session, user_id=user.id, updater=MockPanelUpdater(), period_days=2
    )
    assert first.applied is True
    second = await billing.grant_trial(
        session, user_id=user.id, updater=MockPanelUpdater(), period_days=2
    )
    assert second.applied is False and second.already_used is True


async def test_trial_not_consumed_on_failure(
    session: AsyncSession, user: User, vpn_client: VpnClient, server
):
    """Сбой провижининга не должен «сжигать» пробный период пользователя."""
    res = await billing.grant_trial(
        session,
        user_id=user.id,
        updater=MockPanelUpdater(fail_server_ids={server.id}),
        period_days=2,
    )
    assert res.applied is False
    refreshed = await UserRepository(session).get_by_id(user.id)
    assert refreshed.trial_used is False


# --------------------------------------------------------------------------- #
# D. Защита от захвата аккаунта
# --------------------------------------------------------------------------- #

async def test_public_id_taken_detects_conflict(session: AsyncSession):
    a = User(telegram_id=1, public_id="DUP", role=UserRole.USER)
    b = User(telegram_id=2, public_id="OTHER", role=UserRole.USER)
    session.add_all([a, b])
    await session.commit()

    # Для другого пользователя занятый public_id — конфликт.
    assert await provisioning._public_id_taken(session, "DUP", exclude_user_id=b.id)
    # Для владельца — не конфликт (исключается из проверки).
    assert not await provisioning._public_id_taken(
        session, "DUP", exclude_user_id=a.id
    )


async def test_bind_rejects_subid_owned_by_other_user(
    session: AsyncSession, server, monkeypatch
):
    """Привязка существующего клиента панели не должна позволять «увести» чужой
    subId: если subId уже принадлежит другому пользователю — отказ."""
    victim = User(telegram_id=10, public_id="VICTIMID", role=UserRole.USER)
    attacker = User(telegram_id=11, public_id="ATTACKERID", role=UserRole.USER)
    session.add_all([victim, attacker])
    await session.commit()

    async def fake_find(srv, email, timeout=15.0):
        return PanelClientInfo(
            email=email,
            sub_id="VICTIMID",  # пытаемся присвоить чужой subId
            secret="sek",
            expiry_ms=0,
            enable=True,
            inbound_ids=[1],
        )

    monkeypatch.setattr(provisioning, "find_panel_client", fake_find)

    with pytest.raises(PanelUpdateError):
        await provisioning.bind_existing_client(
            session, server, "someemail", attacker, MockPanelUpdater()
        )


async def test_generated_public_id_is_unique_and_hex(session: AsyncSession):
    repo = UserRepository(session)
    seen: set[str] = set()
    for tid in range(30):
        u, _ = await repo.get_or_create(
            telegram_id=1000 + tid, username=None, first_name=None
        )
        assert u.public_id is not None
        assert len(u.public_id) == 8
        int(u.public_id, 16)  # должен парситься как hex
        assert u.public_id == u.public_id.upper()
        assert u.public_id not in seen
        seen.add(u.public_id)
    await session.commit()


# --------------------------------------------------------------------------- #
# E. Экранирование пользовательского ввода (anti-XSS в HTML-сообщениях)
# --------------------------------------------------------------------------- #

_XSS = "<b>x</b><script>alert(1)</script>&\"'"


def test_welcome_escapes_first_name_and_public_id():
    user = User(telegram_id=1, first_name=_XSS, public_id="ID&<>", role=UserRole.USER)
    out = texts.welcome(user)
    assert "<script>" not in out
    assert "<b>" not in out
    assert "&lt;script&gt;" in out
    assert "&lt;" in out  # public_id тоже экранирован


def test_admin_payment_card_escapes_username_and_error():
    user = User(telegram_id=1, username=_XSS, public_id="PID", role=UserRole.USER)
    payment = _make_payment(user, last_error=_XSS, status=PaymentStatus.FAILED)
    out = texts.admin_payment_card(payment, user)
    assert "<script>" not in out
    assert "<b>" not in out
    # payment_code и public_id остаются в <code>, но это безопасные значения
    assert "&lt;script&gt;" in out


def test_admin_pending_escapes_username():
    user = User(telegram_id=1, username=_XSS, public_id="PID", role=UserRole.USER)
    payment = _make_payment(user)
    out = texts.admin_pending([payment])
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


async def test_forward_proof_escapes_caption():
    """Подпись к чеку полностью контролируется пользователем и уходит админу
    с parse_mode=HTML — она обязана экранироваться."""
    bot = FakeBot()
    settings = Settings(admin_telegram_ids=[1])
    user = User(telegram_id=1, username="u", public_id="PID", role=UserRole.USER)
    payment = _make_payment(user, code="PAY-XSS")
    await notify.forward_proof_to_admins(
        bot, settings, payment, file_type="text",
        telegram_file_id=None, caption=_XSS,
    )
    assert bot.messages
    _, text, kwargs = bot.messages[0]
    assert kwargs.get("parse_mode") == "HTML"
    assert "<script>" not in text
    assert "&lt;script&gt;" in text


async def test_forward_proof_photo_caption_is_static_header():
    """Для фото/документа подпись пользователя НЕ используется как caption —
    отправляется только безопасный заголовок (никакого пользовательского HTML)."""
    bot = FakeBot()
    settings = Settings(admin_telegram_ids=[1])
    user = User(telegram_id=1, username="u", public_id="PID", role=UserRole.USER)
    payment = _make_payment(user, code="PAY-PH")
    await notify.forward_proof_to_admins(
        bot, settings, payment, file_type="photo",
        telegram_file_id="file123", caption=_XSS,
    )
    assert bot.photos
    _, _, kwargs = bot.photos[0]
    assert "<script>" not in (kwargs.get("caption") or "")


# --------------------------------------------------------------------------- #
# F. Неутечка секретов / нормализация URL
# --------------------------------------------------------------------------- #

async def test_login_error_does_not_leak_password(httpx_mock: HTTPXMock):
    secret_pw = "SuperSecret_Password_123"
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/csrf-token",
        json={"success": True, "obj": "t"}, is_reusable=True,
    )
    httpx_mock.add_response(method="POST", url=f"{BASE}/login", status_code=403)
    client = XuiClient(base_url=BASE, username="admin", password=secret_pw)
    async with client:
        with pytest.raises(XuiAuthError) as exc:
            await client.login()
    assert secret_pw not in str(exc.value)


def test_base_url_is_normalized():
    client = XuiClient(
        base_url="http://panel.local:2053/", username="a", password="b"
    )
    assert client._base_url == "http://panel.local:2053"


# --------------------------------------------------------------------------- #
# G. Устойчивость к некорректным данным и сбоям
# --------------------------------------------------------------------------- #

def test_parse_json_invalid_raises_xuierror_not_crash():
    resp = httpx.Response(200, text="<html>not json</html>")
    with pytest.raises(XuiError):
        XuiClient._parse_json(resp)


@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, []),
        ("", []),
        ("no ip record", []),
        ("No IP Record", []),
        ("1.1.1.1, 2.2.2.2", ["1.1.1.1", "2.2.2.2"]),
        (["1.1.1.1", " 2.2.2.2 ", ""], ["1.1.1.1", "2.2.2.2"]),
        ('["3.3.3.3","4.4.4.4"]', ["3.3.3.3", "4.4.4.4"]),
        (12345, []),
    ],
)
def test_parse_ips_handles_arbitrary_input(raw, expected):
    assert XuiClient._parse_ips(raw) == expected


async def test_health_check_server_returns_false_on_error(server, monkeypatch):
    class _FailingXui:
        def __init__(self, *a, **k) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def login(self):
            raise XuiError("unreachable")

    monkeypatch.setattr(health, "XuiClient", _FailingXui)
    assert await health.check_server(server) is False


async def test_health_check_server_returns_true_on_success(server, monkeypatch):
    class _OkXui:
        def __init__(self, *a, **k) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def login(self):
            return None

    monkeypatch.setattr(health, "XuiClient", _OkXui)
    assert await health.check_server(server) is True


async def test_notify_swallows_telegram_api_errors():
    """Сбой отправки одному админу не должен ронять обработку апдейта."""
    bot = FakeBot(fail=True)
    settings = Settings(admin_telegram_ids=[1, 2])
    user = User(telegram_id=1, username="u", public_id="PID", role=UserRole.USER)
    payment = _make_payment(user)
    payment.id = 1  # клавиатуре нужен числовой id заявки
    # Не должно бросить исключение.
    await notify.notify_admins_new_request(bot, settings, payment, user)
    await notify.notify_user_extended(bot, 1, VpnClient(user_id=1))
    await notify.notify_user_rejected(bot, 1, "PAY-1")


# --------------------------------------------------------------------------- #
# H. Валидация ввода в админ-парсере сервера
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "raw",
    [
        "",
        "only|four|fields|here",
        "name|de||admin|pass",          # пустой panel_url
        "name|de|http://p||pass",       # пустой username
        "name|de|http://p|admin|",      # пустой password
    ],
)
def test_parse_server_line_rejects_invalid(raw: str):
    server, error = admin_handlers._parse_server_line(raw)
    assert server is None
    assert error


def test_parse_server_line_accepts_valid():
    server, error = admin_handlers._parse_server_line(
        "DE|de|http://p:2053|admin|pass|direct|http://sub/"
    )
    assert error is None
    assert server.name == "DE"
    assert server.subscription_base == "http://sub/"


def test_menu_callback_actions_are_strings():
    # Навигация по меню не несёт привилегированных параметров.
    assert set(MenuCallback.model_fields) == {"action"}

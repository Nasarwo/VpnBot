from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import emoji, keyboards, texts
from app.bot.callbacks import MenuCallback
from app.bot.user_handlers import _cancel_payment, _is_active, _trial_available
from app.db.enums import AttachmentType, PaymentStatus
from app.db.models import PaymentRequest, Server, User, VpnClient
from app.db.repositories import PaymentRepository, ServerRepository
from app.services import health
from tests.conftest import utcnow


class _DummyState:
    async def clear(self) -> None:
        return None


def _all_buttons(markup):
    return [btn for row in markup.inline_keyboard for btn in row]


# --- Клавиатуры: цвет, значки, copy ---

def test_welcome_menu_active_vs_inactive():
    active = _all_buttons(keyboards.welcome_menu(True))
    assert active[0].text == texts.BTN_MY_SUBSCRIPTION
    assert active[0].style == "primary"
    assert active[0].icon_custom_emoji_id  # анимированный значок проставлен

    inactive = _all_buttons(keyboards.welcome_menu(False))
    assert inactive[0].text == texts.BTN_BUY
    assert inactive[1].text == texts.BTN_INSTALL
    assert inactive[2].text == texts.BTN_FREE_PROXIES
    # Поддержка всегда зелёная
    assert inactive[3].text == texts.BTN_SUPPORT
    assert inactive[3].style == "success"
    assert inactive[4].text == texts.BTN_RESET
    assert inactive[4].style == "danger"


def test_welcome_menu_auto_admin_has_panel_and_connection():
    admin = _all_buttons(keyboards.welcome_menu(True, is_admin=True))
    labels = [button.text for button in admin]

    assert admin[0].text == texts.BTN_ADMIN_PANEL
    assert admin[0].style == "primary"
    assert MenuCallback.unpack(admin[0].callback_data).action == "admin_panel"
    assert texts.BTN_CONNECT in labels
    assert texts.BTN_BUY not in labels


def test_install_guides_keyboard_has_telegraph_links():
    buttons = _all_buttons(keyboards.install_guides_keyboard())
    assert buttons[0].text == texts.BTN_GUIDE_WINDOWS
    assert buttons[0].url == texts.INSTALL_GUIDE_WINDOWS_URL
    assert buttons[0].icon_custom_emoji_id
    assert buttons[1].text == texts.BTN_GUIDE_ANDROID_IOS
    assert buttons[1].url == texts.INSTALL_GUIDE_ANDROID_IOS_URL
    assert buttons[1].icon_custom_emoji_id
    assert buttons[2].text == texts.BTN_BACK


def test_welcome_menu_install_has_icon():
    inactive = _all_buttons(keyboards.welcome_menu(False))
    install_btn = inactive[1]
    assert install_btn.text == texts.BTN_INSTALL
    assert install_btn.icon_custom_emoji_id == emoji.custom_emoji_id("install")


def test_free_proxies_keyboard_links():
    buttons = _all_buttons(keyboards.free_proxies_keyboard())
    assert len(buttons) == 3
    assert buttons[0].text == texts.BTN_PROXY_MTPROTO
    assert buttons[0].url == texts.FREE_PROXY_MTPROTO_URL
    assert buttons[0].icon_custom_emoji_id == emoji.custom_emoji_id("connect")
    assert buttons[1].text == texts.BTN_PROXY_SOCKS5
    assert buttons[1].url == texts.FREE_PROXY_SOCKS5_URL
    assert buttons[1].icon_custom_emoji_id == emoji.custom_emoji_id("server")
    assert buttons[2].text == texts.BTN_BACK
    assert all("nasarwo.pro" in (button.url or "") for button in buttons[:2])
    assert all("mind-forge.tech" not in (button.url or "") for button in buttons)


def test_welcome_menu_free_proxies_has_icon():
    inactive = _all_buttons(keyboards.welcome_menu(False))
    proxy_btn = inactive[2]
    assert proxy_btn.text == texts.BTN_FREE_PROXIES
    assert proxy_btn.icon_custom_emoji_id == emoji.custom_emoji_id("globe")


def test_purchase_keyboard_trial_visibility():
    with_trial = _all_buttons(keyboards.purchase_plans_keyboard(True))
    assert any(b.text == texts.BTN_TRIAL for b in with_trial)

    without_trial = _all_buttons(keyboards.purchase_plans_keyboard(False))
    assert all(b.text != texts.BTN_TRIAL for b in without_trial)
    # Кнопка «Назад» присутствует
    assert any(b.text == texts.BTN_BACK for b in without_trial)


def test_connection_keyboard_uses_copy_text():
    srv = Server(
        id=1,
        name="Швеция",
        country="SE",
        panel_url="http://x",
        username="u",
        password="p",
        subscription_base="https://sub.example/sub/",
        enabled=True,
    )
    markup = keyboards.connection_keyboard([srv], "ABCD1234")
    copy_buttons = [b for b in _all_buttons(markup) if b.copy_text is not None]
    assert len(copy_buttons) == 1
    assert copy_buttons[0].copy_text.text == "https://sub.example/sub/ABCD1234"
    assert "Швеция" in copy_buttons[0].text


def test_connection_keyboard_without_public_id_only_back():
    srv = Server(
        id=1, name="X", country="SE", panel_url="http://x",
        username="u", password="p", subscription_base="https://s/sub/",
    )
    markup = keyboards.connection_keyboard([srv], None)
    buttons = _all_buttons(markup)
    assert len(buttons) == 1
    assert buttons[0].text == texts.BTN_BACK


def test_cancel_payment_keyboard():
    buttons = _all_buttons(keyboards.cancel_payment_keyboard())
    assert len(buttons) == 1
    assert buttons[0].text == texts.BTN_CANCEL
    assert buttons[0].style == "danger"
    assert MenuCallback.unpack(buttons[0].callback_data).action == "cancel_payment"


def test_all_inline_buttons_have_color_style():
    srv = Server(
        id=1,
        name="Server",
        country="SE",
        panel_url="http://x",
        username="u",
        password="p",
        subscription_base="https://sub.example/sub/",
        enabled=True,
    )
    markups = [
        keyboards.back_keyboard("home"),
        keyboards.cancel_payment_keyboard(),
        keyboards.welcome_menu(True),
        keyboards.welcome_menu(False),
        keyboards.welcome_menu(True, is_admin=True),
        keyboards.reset_bot_confirm_keyboard(),
        keyboards.install_guides_keyboard(),
        keyboards.free_proxies_keyboard(),
        keyboards.news_channel_keyboard(),
        keyboards.subscription_menu(),
        keyboards.extend_plans_keyboard(),
        keyboards.purchase_plans_keyboard(True),
        keyboards.connection_keyboard([srv], "ABCD1234"),
        keyboards.connection_keyboard([srv], None),
        keyboards.admin_home_keyboard(),
        keyboards.admin_servers_keyboard([srv]),
        keyboards.admin_server_keyboard(srv),
        keyboards.admin_confirm_delete_keyboard(1),
        keyboards.admin_back_keyboard("home"),
        keyboards.onboarding_legacy_keyboard(),
        keyboards.admin_bind_keyboard(1),
        keyboards.admin_bind_retry_keyboard(1),
        keyboards.admin_payment_keyboard(1),
        keyboards.admin_retry_keyboard(1),
    ]

    allowed = {"primary", "success", "danger"}
    for markup in markups:
        for button in _all_buttons(markup):
            assert getattr(button, "style", None) in allowed, button.text


async def test_cancel_payment_deletes_unsubmitted(
    session: AsyncSession, user: User
):
    repo = PaymentRepository(session)
    await repo.create(
        user_id=user.id, amount=175, period_days=30, payment_code="PAY-CANCEL",
        status=PaymentStatus.WAITING_ADMIN,
    )
    await session.commit()

    await _cancel_payment(session, user, _DummyState())

    assert await repo.latest_open_for_user(user.id) is None


async def test_cancel_payment_keeps_submitted(
    session: AsyncSession, user: User
):
    repo = PaymentRepository(session)
    payment = await repo.create(
        user_id=user.id, amount=175, period_days=30, payment_code="PAY-SENT",
        status=PaymentStatus.WAITING_ADMIN,
    )
    await repo.add_attachment(
        payment_request_id=payment.id, file_type=AttachmentType.TEXT,
        caption="оплатил",
    )
    await session.commit()

    await _cancel_payment(session, user, _DummyState())

    # Заявка с приложенным подтверждением не удаляется.
    assert await repo.latest_open_for_user(user.id) is not None


# --- Тексты ---

def test_country_flag():
    assert texts.country_flag("SE") == "\U0001f1f8\U0001f1ea"
    assert texts.country_flag("ru") == "\U0001f1f7\U0001f1fa"
    assert texts.country_flag(None) == ""
    assert texts.country_flag("Sweden") == ""


def test_server_button_label_has_no_autoflag():
    """Флаг не добавляется автоматически — он уже в названии сервера."""
    srv = Server(
        id=1, name="🇸🇪 Швеция", country="SE", panel_url="http://x",
        username="u", password="p",
    )
    label = texts.server_button_label(srv)
    assert label == "🇸🇪 Швеция"
    # Ровно один флаг, без дублирования.
    assert label.count("\U0001f1f8") == 1


def test_trial_period_default_is_three_days():
    from app.config import Settings

    assert Settings(admin_telegram_ids=[]).trial_period_days == 3


def test_purchase_info_contains_promo_and_prices():
    text = texts.purchase_info(show_trial=True)
    assert "175 рублей" in text
    assert "приведи друга" in text
    assert "пробный" in text.lower()


def test_payment_code_wrapped_in_code_tag():
    payment = PaymentRequest(
        user_id=1, amount=175, period_days=30, payment_code="PAY-1042",
        status=PaymentStatus.CREATED,
    )
    created = texts.payment_created(payment, "реквизиты")
    assert "<code>PAY-1042</code>" in created
    assert "PAY-1042" not in created.replace("<code>PAY-1042</code>", "")

    assert "<code>PAY-1042</code>" in texts.proof_received("PAY-1042")
    assert "<code>PAY-1042</code>" in texts.payment_rejected("PAY-1042")


def test_admin_pending_has_no_raw_angle_brackets():
    user = User(telegram_id=1, username="bob", public_id="AB12")
    payment = PaymentRequest(
        user_id=1, amount=175, period_days=30, payment_code="PAY-7",
        status=PaymentStatus.WAITING_ADMIN, user=user,
    )
    text = texts.admin_pending([payment])
    assert "<code>PAY-7</code>" in text
    # Никаких «сырых» <код> — они ломают HTML-разметку.
    assert "<код>" not in text


def test_access_extended_has_animated_check():
    from app.bot import emoji

    text = texts.access_extended(VpnClient(user_id=1, expires_at=utcnow()))
    assert text.startswith(emoji.tg("ok"))
    assert "Доступ продлён" in text
    assert "Мои ссылки" not in text


def test_no_texts_reference_removed_buttons():
    text = texts.trial_granted(VpnClient(user_id=1, expires_at=utcnow()), 3)
    assert "Мои ссылки" not in text
    assert texts.trial_granted.__name__  # smoke
    assert "Мои ссылки" not in texts.access_extended(
        VpnClient(user_id=1, expires_at=utcnow())
    )


def test_connection_overview_status_icons():
    online = Server(
        id=1, name="Швеция", country="SE", panel_url="http://x",
        username="u", password="p", subscription_base="https://s/sub/",
        is_online=True,
    )
    offline = Server(
        id=2, name="Финляндия", country="FI", panel_url="http://y",
        username="u", password="p", subscription_base="https://s/sub/",
        is_online=False,
    )
    text = texts.connection_overview([online, offline])
    assert "Швеция" in text and "Финляндия" in text
    assert "tg-emoji" in text  # анимированные статус-иконки


# --- Логика состояний ---

def test_admin_panel_clients_supports_nested_client_api_records():
    text = texts.admin_panel_clients(
        7,
        [
            {
                "client": {
                    "email": "client@example",
                    "subId": "SUB-1",
                    "enable": False,
                    "expiryTime": 0,
                },
                "inboundIds": [1, 2],
            }
        ],
    )

    assert "client@example" in text
    assert "SUB-1" in text
    assert "выкл" in text


def test_is_active():
    assert _is_active(None) is False
    assert _is_active(VpnClient(user_id=1, expires_at=None)) is False
    assert _is_active(
        VpnClient(user_id=1, expires_at=utcnow() - timedelta(days=1))
    ) is False
    assert _is_active(
        VpnClient(user_id=1, expires_at=utcnow() + timedelta(days=5))
    ) is True


async def test_trial_available(session: AsyncSession, user: User):
    assert await _trial_available(session, user) is True

    payment = await PaymentRepository(session).create(
        user_id=user.id, amount=175, period_days=30, payment_code="PAY-1"
    )
    payment.status = PaymentStatus.APPLIED
    await session.commit()
    assert await _trial_available(session, user) is False


async def test_trial_unavailable_when_used(session: AsyncSession, user: User):
    user.trial_used = True
    await session.commit()
    assert await _trial_available(session, user) is False


# --- Репозиторий и health-check ---

async def test_set_status(session: AsyncSession, server: Server):
    await ServerRepository(session).set_status(server.id, True)
    await session.commit()
    refreshed = await ServerRepository(session).get_by_id(server.id)
    assert refreshed.is_online is True
    assert refreshed.last_checked_at is not None


async def test_last_successful_for_user(session: AsyncSession, user: User):
    repo = PaymentRepository(session)
    assert await repo.last_successful_for_user(user.id) is None

    p1 = await repo.create(user_id=user.id, amount=175, period_days=30,
                           payment_code="P1")
    p1.status = PaymentStatus.APPLIED
    p2 = await repo.create(user_id=user.id, amount=850, period_days=180,
                           payment_code="P2")
    p2.status = PaymentStatus.CONFIRMED
    await session.commit()

    last = await repo.last_successful_for_user(user.id)
    assert last is not None
    assert last.payment_code == "P2"


# --- Админ-панель ---

def test_admin_home_keyboard_sections():
    btns = _all_buttons(keyboards.admin_home_keyboard())
    labels = [b.text for b in btns]
    assert "Серверы" in labels
    assert "Заявки в ожидании" in labels
    assert "Удалить инбаунды" in labels
    assert "Антишеринг" in labels


def test_admin_servers_keyboard_has_add_and_back():
    srv = Server(
        id=5, name="DE", country="DE", panel_url="http://x", username="a",
        password="b", enabled=True, is_online=True,
    )
    btns = _all_buttons(keyboards.admin_servers_keyboard([srv]))
    labels = [b.text for b in btns]
    assert any("#5" in label and "DE" in label for label in labels)
    assert any(label == "Добавить сервер" for label in labels)
    assert any(label == texts.BTN_BACK for label in labels)


def test_admin_server_keyboard_toggle_label():
    on = Server(id=1, name="s", panel_url="x", username="a", password="b",
                enabled=True)
    off = Server(id=1, name="s", panel_url="x", username="a", password="b",
                 enabled=False)
    assert any(b.text == "Выключить" for b in _all_buttons(
        keyboards.admin_server_keyboard(on)))
    assert any(b.text == "Включить" for b in _all_buttons(
        keyboards.admin_server_keyboard(off)))


def test_parse_server_line():
    from app.bot.admin_handlers import _parse_server_line

    srv, err = _parse_server_line("DE|de|http://p|admin|pass|direct|http://sub/")
    assert err is None
    assert srv.name == "DE" and srv.country == "de"
    assert srv.subscription_base == "http://sub/"

    _, err2 = _parse_server_line("too|few")
    assert err2 is not None


async def test_server_repository_delete(session: AsyncSession, server: Server):
    repo = ServerRepository(session)
    assert await repo.delete(server.id) is True
    await session.commit()
    assert await repo.get_by_id(server.id) is None
    assert await repo.delete(server.id) is False


async def test_check_servers_saves_status(
    session: AsyncSession, server: Server, monkeypatch
):
    second = Server(
        name="srv-2", country="SE", panel_url="http://other:2053",
        username="u", password="p", enabled=True,
    )
    session.add(second)
    await session.commit()

    async def fake_check(srv, timeout=10.0):
        return srv.id == server.id

    monkeypatch.setattr(health, "check_server", fake_check)
    result = await health.check_servers(session, timeout=1.0)

    assert result[server.id] is True
    assert result[second.id] is False
    refreshed = await ServerRepository(session).get_by_id(server.id)
    assert refreshed.is_online is True

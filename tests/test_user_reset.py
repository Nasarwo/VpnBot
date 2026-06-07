from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import keyboards, texts
from app.bot.callbacks import MenuCallback
from app.db.enums import PaymentStatus, UserRole
from app.db.models import BindRequest, PaymentRequest, User, VpnClient
from app.db.repositories import UserRepository, VpnClientRepository


def _all_buttons(markup):
    return [btn for row in markup.inline_keyboard for btn in row]


def test_reset_confirm_keyboard():
    buttons = _all_buttons(keyboards.reset_bot_confirm_keyboard())
    assert buttons[0].text == texts.BTN_RESET_YES
    assert buttons[0].style == "danger"
    assert MenuCallback.unpack(buttons[0].callback_data).action == "reset_yes"
    assert buttons[1].text == texts.BTN_CANCEL
    assert MenuCallback.unpack(buttons[1].callback_data).action == "home"


async def test_delete_user_removes_related_data(session: AsyncSession, user: User):
    user.onboarding_done = True
    user.trial_used = True
    user.public_id = "ABCD1234"
    session.add(
        VpnClient(
            user_id=user.id,
            display_name="c1",
            email="u@local",
            is_active=True,
        )
    )
    session.add(
        PaymentRequest(
            user_id=user.id,
            payment_code="PAY1",
            amount=100.0,
            period_days=30,
            status=PaymentStatus.CONFIRMED,
        )
    )
    session.add(
        BindRequest(
            user_id=user.id,
            request_code="BIND1",
            subscription_link="https://example.com/sub/x",
            public_id="x",
        )
    )
    await session.commit()
    telegram_id = user.telegram_id

    repo = UserRepository(session)
    await repo.delete_user(user)
    await session.commit()

    assert await repo.get_by_telegram_id(telegram_id) is None
    assert (await session.execute(select(VpnClient))).scalars().all() == []
    assert (await session.execute(select(PaymentRequest))).scalars().all() == []
    assert (await session.execute(select(BindRequest))).scalars().all() == []


async def test_get_or_create_after_delete_starts_fresh(session: AsyncSession):
    old = User(
        telegram_id=777,
        username="old",
        first_name="Old",
        role=UserRole.USER,
        onboarding_done=True,
        trial_used=True,
        public_id="OLDID111",
    )
    session.add(old)
    await session.flush()
    session.add(
        VpnClient(
            user_id=old.id,
            display_name="c",
            email="e@local",
            is_active=False,
        )
    )
    await session.commit()

    repo = UserRepository(session)
    await repo.delete_user(old)
    await session.commit()

    new_user, created = await repo.get_or_create(
        telegram_id=777,
        username="old",
        first_name="Old",
    )
    await session.commit()

    assert created is True
    assert new_user.public_id != "OLDID111"
    assert new_user.onboarding_done is False
    assert new_user.trial_used is False
    assert await VpnClientRepository(session).get_for_user(new_user.id) is None
    assert await repo.get_by_telegram_id(777) is new_user

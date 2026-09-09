from __future__ import annotations

import base64
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from app.bot.notify import notify_user_extended, notify_user_rejected
from app.db.enums import AttachmentType, UserRole
from app.db.models import PaymentRequest, User, VpnClient, WebAccount, WebLinkRequest
from app.services import payments
from app.services.web_bridge import decide_link, receipt_bytes


async def make_account(session):
    source = User(public_id="WEB12345", telegram_id=None, role=UserRole.USER)
    session.add(source)
    await session.flush()
    account = WebAccount(
        user_id=source.id, email="web@example.com", password_hash="test-hash", verified=True
    )
    session.add(account)
    await session.commit()
    return account, source


async def test_link_preserves_existing_subscription(session, user, vpn_client):
    account, source = await make_account(session)
    req = WebLinkRequest(account_id=account.id, target_user_id=user.id, status="pending")
    session.add(req)
    await session.commit()
    assert await decide_link(session, req.id, True) == "Привязка одобрена"
    assert account.user_id == user.id
    assert vpn_client.user_id == user.id
    assert await session.get(User, source.id) is not None
    assert await decide_link(session, req.id, True) == "Заявка уже обработана"


async def test_link_rechecks_purchase_at_approval(session, user):
    account, source = await make_account(session)
    req = WebLinkRequest(account_id=account.id, target_user_id=user.id, status="pending")
    session.add(req)
    await session.commit()
    await payments.create_request(session, source.id, 175, 30)
    await decide_link(session, req.id, True)
    assert req.status == "conflict"
    assert account.user_id == source.id


async def test_link_cannot_take_occupied_telegram(session, user):
    account, source = await make_account(session)
    session.add(
        WebAccount(user_id=user.id, email="owner@example.com", password_hash="hash", verified=True)
    )
    req = WebLinkRequest(account_id=account.id, target_user_id=user.id, status="pending")
    session.add(req)
    await session.commit()
    await decide_link(session, req.id, True)
    assert req.status == "conflict"
    assert account.user_id == source.id


async def test_reject_does_not_reassign(session, user):
    account, source = await make_account(session)
    req = WebLinkRequest(account_id=account.id, target_user_id=user.id, status="pending")
    session.add(req)
    await session.commit()
    await decide_link(session, req.id, False)
    assert req.status == "rejected"
    assert account.user_id == source.id


async def test_bot_cannot_change_submitted_web_payment(session):
    _, source = await make_account(session)
    payment = await payments.create_request(session, source.id, 175, 30)
    await payments.attach_proof(session, payment.id, AttachmentType.TEXT, caption="Paid")
    repeated = await payments.create_request(session, source.id, 1600, 360)
    assert repeated.id == payment.id
    assert repeated.amount == 175
    assert repeated.period_days == 30
    assert len((await session.scalars(select(PaymentRequest))).all()) == 1


async def test_web_user_gets_no_telegram_notification():
    bot = AsyncMock()
    await notify_user_extended(bot, None, VpnClient())
    await notify_user_rejected(bot, None, "WEB-1")
    bot.send_message.assert_not_called()


@pytest.mark.parametrize("data", [b"<script>alert(1)</script>", b"", b"x" * (5 * 1024 * 1024 + 1)])
def test_receipt_rejects_invalid_content(data):
    with pytest.raises(ValueError):
        receipt_bytes(base64.b64encode(data).decode())


def test_receipt_preserves_pdf():
    raw = b"%PDF-1.7\noriginal receipt"
    data, name = receipt_bytes(base64.b64encode(raw).decode())
    assert data == raw
    assert name == "receipt.pdf"

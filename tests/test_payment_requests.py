from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import AttachmentType, PaymentStatus
from app.db.models import User
from app.db.repositories import PaymentRepository
from app.services import payments


async def test_create_request_sets_waiting_admin(session: AsyncSession, user: User):
    payment = await payments.create_request(
        session, user_id=user.id, amount=175, period_days=30
    )
    assert payment.status == PaymentStatus.WAITING_ADMIN
    assert payment.payment_code.startswith("PAY-")
    assert payment.period_days == 30
    assert float(payment.amount) == 175.0


async def test_create_request_reuses_open_request(session: AsyncSession, user: User):
    first = await payments.create_request(
        session, user_id=user.id, amount=175, period_days=30
    )
    second = await payments.create_request(
        session, user_id=user.id, amount=175, period_days=30
    )
    assert first.id == second.id


async def test_attach_proof_creates_attachment(session: AsyncSession, user: User):
    payment = await payments.create_request(
        session, user_id=user.id, amount=175, period_days=30
    )
    attachment = await payments.attach_proof(
        session,
        payment_id=payment.id,
        file_type=AttachmentType.PHOTO,
        telegram_file_id="file-123",
        caption="чек",
    )
    assert attachment.id is not None

    refreshed = await PaymentRepository(session).get_by_id_with_relations(payment.id)
    assert len(refreshed.attachments) == 1
    assert refreshed.attachments[0].file_type == AttachmentType.PHOTO
    assert refreshed.attachments[0].telegram_file_id == "file-123"


async def test_get_by_code_and_list_waiting(session: AsyncSession, user: User):
    payment = await payments.create_request(
        session, user_id=user.id, amount=175, period_days=30
    )
    repo = PaymentRepository(session)

    by_code = await repo.get_by_code(payment.payment_code)
    assert by_code is not None
    assert by_code.id == payment.id

    waiting = await repo.list_waiting_admin()
    assert [p.id for p in waiting] == [payment.id]


async def test_payment_code_increments(session: AsyncSession, user: User):
    p1 = await payments.create_request(
        session, user_id=user.id, amount=175, period_days=30
    )
    # завершим первую, чтобы вторая создалась как новая
    p1.status = PaymentStatus.APPLIED
    await session.commit()

    p2 = await payments.create_request(
        session, user_id=user.id, amount=175, period_days=30
    )
    assert p1.payment_code != p2.payment_code

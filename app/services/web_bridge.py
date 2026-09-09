"""Private adapter for the Go API. Never expose this listener to the Internet.

Authentication stays in Go; billing and provisioning use the same services as Telegram.
Only a verified web account ID is accepted, never a user ID chosen by the browser.
"""

from __future__ import annotations

import asyncio
import base64
import hmac
import json
import logging
import secrets
from datetime import UTC, datetime, timedelta
from html import escape

from aiogram import Bot, F, Router
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiohttp import web
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.bot import keyboards, texts
from app.bot.filters import IsAdmin
from app.config import Settings
from app.db.enums import AttachmentType, PaymentStatus, UserRole
from app.db.models import (
    PaymentAttachment,
    PaymentRequest,
    Server,
    User,
    VpnClient,
    WebAccount,
    WebDelivery,
    WebLinkRequest,
)
from app.db.repositories import VpnClientRepository
from app.db.session import get_sessionmaker
from app.services import billing
from app.services.access import has_client_access
from app.services.plans import get_plan
from app.services.subhub_client import SubHubClient, SubHubError, trigger_configured_sync
from app.services.xui_updater import build_updater

logger = logging.getLogger(__name__)
router = Router(name="web_link_admin")
router.callback_query.filter(IsAdmin())


def problem(message: str, status: int = 400) -> web.Response:
    return web.json_response({"error": message}, status=status)


async def has_purchase(session, user_id: int) -> bool:
    return (
        await session.scalar(
            select(PaymentRequest.id)
            .where(
                PaymentRequest.user_id == user_id,
                PaymentRequest.status.in_(
                    [
                        PaymentStatus.CREATED,
                        PaymentStatus.WAITING_ADMIN,
                        PaymentStatus.CONFIRMED,
                        PaymentStatus.APPLIED,
                        PaymentStatus.FAILED,
                    ]
                ),
            )
            .limit(1)
        )
    ) is not None


async def queue(session, settings: Settings, payload: dict) -> None:
    if not settings.admin_telegram_ids:
        raise ValueError("Не настроены администраторы")
    for admin_id in settings.admin_telegram_ids:
        session.add(WebDelivery(admin_id=admin_id, payload=json.dumps(payload)))


async def decide_link(session, request_id: int, approve: bool) -> str:
    # Same account lock as purchases. Recheck eligibility at approval time.
    req = await session.get(WebLinkRequest, request_id)
    if req is None:
        return "Заявка не найдена"
    account = await session.scalar(
        select(WebAccount).where(WebAccount.id == req.account_id).with_for_update()
    )
    await session.refresh(req)
    if account is None or req.status != "pending":
        return "Заявка уже обработана"
    if not approve:
        req.status = "rejected"
    else:
        target = await session.scalar(
            select(User).where(User.id == req.target_user_id).with_for_update()
        )
        occupied = await session.scalar(
            select(WebAccount.id).where(WebAccount.user_id == req.target_user_id)
        )
        source = await session.get(User, account.user_id) if account.user_id else None
        client = await session.scalar(
            select(VpnClient.id).where(VpnClient.user_id == account.user_id)
        )
        if (
            target is None
            or target.telegram_id is None
            or occupied is not None
            or (source and source.telegram_id is not None)
            or client is not None
            or await has_purchase(session, account.user_id)
        ):
            req.status = "conflict"
            await session.commit()
            return "Привязка невозможна: аккаунт занят или появился доступ/платёж. Нужна поддержка."
        account.user_id = target.id
        req.status = "approved"
    await session.commit()
    return "Привязка одобрена" if approve else "Привязка отклонена"


@router.callback_query(F.data.startswith("weblink:"))
async def link_callback(callback: CallbackQuery, session, db_user: User):
    try:
        _, action, identifier = (callback.data or "").split(":")
        if action not in {"yes", "no"}:
            raise ValueError
        result = await decide_link(session, int(identifier), action == "yes")
    except (ValueError, IntegrityError):
        await session.rollback()
        result = "Привязка невозможна или уже обработана"
    await callback.answer(result, show_alert=True)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)


def receipt_bytes(encoded: str) -> tuple[bytes, str]:
    data = base64.b64decode(encoded, validate=True)
    if not data or len(data) > 5 * 1024 * 1024:
        raise ValueError("Размер квитанции — до 5 МБ")
    if data.startswith(b"%PDF-"):
        return data, "receipt.pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return data, "receipt.png"
    if data.startswith(b"\xff\xd8\xff"):
        return data, "receipt.jpg"
    raise ValueError("Загрузите PDF, PNG или JPEG")


async def delivery_loop(bot: Bot):
    while True:
        try:
            async with get_sessionmaker()() as session:
                item = await session.scalar(
                    select(WebDelivery)
                    .where(
                        WebDelivery.status == "pending",
                        WebDelivery.next_attempt_at <= datetime.now(UTC),
                    )
                    .order_by(WebDelivery.id)
                    .with_for_update(skip_locked=True)
                    .limit(1)
                )
                if item is not None:
                    payload = json.loads(item.payload)
                    try:
                        markup = InlineKeyboardMarkup.model_validate(payload["keyboard"])
                        if payload.get("receipt"):
                            data, filename = receipt_bytes(payload["receipt"])
                            # Documents preserve the original receipt; no lossy photo compression.
                            sent = await bot.send_document(
                                item.admin_id,
                                BufferedInputFile(data, filename=filename),
                                caption=payload.get("receipt_caption", "Квитанция с сайта"),
                                parse_mode="HTML",
                                reply_markup=markup,
                            )
                            if sent.document and payload.get("attachment_id"):
                                attachment = await session.get(
                                    PaymentAttachment, payload["attachment_id"]
                                )
                                if attachment:
                                    attachment.telegram_file_id = sent.document.file_id
                        else:
                            await bot.send_message(
                                item.admin_id,
                                payload["text"],
                                parse_mode="HTML",
                                reply_markup=markup,
                            )
                        item.status = "sent"
                        item.payload = "{}"  # Do not retain duplicate receipt bytes.
                    except Exception:
                        item.attempts += 1
                        item.next_attempt_at = datetime.now(UTC) + timedelta(
                            seconds=min(3600, 15 * 2 ** min(item.attempts, 8))
                        )
                        logger.warning("Web delivery %s failed; retry scheduled", item.id)
                    await session.commit()
                    continue
        except Exception as exc:
            logger.warning("Web delivery worker failed (%s)", type(exc).__name__)
        await asyncio.sleep(3)


async def start_bridge(bot: Bot, settings: Settings) -> web.AppRunner | None:
    if not settings.web_bridge_token:
        return None
    if len(settings.web_bridge_token) < 32:
        raise ValueError("WEB_BRIDGE_TOKEN must contain at least 32 characters")

    async def handle(request: web.Request):
        if not hmac.compare_digest(
            request.headers.get("X-Bridge-Token", ""), settings.web_bridge_token
        ):
            return problem("Unauthorized", 401)
        try:
            body = await request.json()
            account_id = int(body["account_id"])
        except (ValueError, KeyError, TypeError):
            return problem("Неверный запрос")
        action = request.match_info["action"]
        async with get_sessionmaker()() as session:
            account = await session.scalar(
                select(WebAccount)
                .where(WebAccount.id == account_id, WebAccount.verified.is_(True))
                .with_for_update()
            )
            if account is None:
                return problem("Войдите в аккаунт", 401)
            if account.user_id is None:
                user = User(
                    public_id=secrets.token_hex(4).upper(),
                    first_name=account.email,
                    role=UserRole.USER,
                    onboarding_done=True,
                )
                session.add(user)
                await session.flush()
                account.user_id = user.id
            user = await session.scalar(
                select(User).where(User.id == account.user_id).with_for_update()
            )
            client = await VpnClientRepository(session).get_for_user(user.id)
            link = await session.scalar(
                select(WebLinkRequest)
                .where(WebLinkRequest.account_id == account.id)
                .order_by(WebLinkRequest.id.desc())
                .limit(1)
            )
            if action == "profile":
                payments = (
                    await session.scalars(
                        select(PaymentRequest)
                        .where(PaymentRequest.user_id == user.id)
                        .order_by(PaymentRequest.id.desc())
                        .limit(30)
                    )
                ).all()
                servers = (
                    await session.scalars(select(Server).where(Server.enabled.is_(True)))
                ).all()
                result = {
                    "email": account.email,
                    "public_id": user.public_id,
                    "telegram_linked": user.telegram_id is not None,
                    "link_status": link.status if link else None,
                    "active": has_client_access(client),
                    "expires_at": client.expires_at.isoformat()
                    if client and client.expires_at
                    else None,
                    "trial_available": user.telegram_id is not None
                    and not user.trial_used
                    and client is None,
                    "payments": [
                        {
                            "id": p.id,
                            "code": p.payment_code,
                            "amount": float(p.amount),
                            "days": p.period_days,
                            "status": p.status.value,
                            "created_at": p.created_at.isoformat(),
                        }
                        for p in payments
                    ],
                    "servers": [
                        {"name": s.name, "country": s.country, "online": s.is_online}
                        for s in servers
                    ],
                }
                await session.commit()
                return web.json_response(result)
            if action == "payment":
                plan = get_plan(str(body.get("plan", "")))
                if plan is None:
                    return problem("Выберите тариф")
                if link and link.status == "pending":
                    return problem("Дождитесь решения по привязке Telegram", 409)
                existing = await session.scalar(
                    select(PaymentRequest.id)
                    .where(
                        PaymentRequest.user_id == user.id,
                        PaymentRequest.status.in_(
                            [
                                PaymentStatus.WAITING_ADMIN,
                                PaymentStatus.CONFIRMED,
                                PaymentStatus.FAILED,
                            ]
                        ),
                    )
                    .limit(1)
                )
                if existing:
                    return problem("У вас уже есть заявка на проверке", 409)
                caption = str(body.get("comment", "")).strip()
                encoded = str(body.get("receipt", ""))
                if len(caption) > 1000:
                    return problem("Комментарий — до 1000 символов")
                if not caption and not encoded:
                    return problem("Добавьте квитанцию или текст подтверждения")
                if encoded:
                    try:
                        receipt_bytes(encoded)
                    except ValueError as exc:
                        return problem(str(exc))
                payment = PaymentRequest(
                    user_id=user.id,
                    amount=plan.amount_rub,
                    period_days=plan.period_days,
                    currency="RUB",
                    status=PaymentStatus.WAITING_ADMIN,
                    payment_code="WEB-" + secrets.token_hex(8).upper(),
                )
                session.add(payment)
                await session.flush()
                attachment = PaymentAttachment(
                    payment_request_id=payment.id,
                    file_type=AttachmentType.DOCUMENT if encoded else AttachmentType.TEXT,
                    caption=caption or None,
                )
                session.add(attachment)
                await session.flush()
                card = texts.admin_payment_card(payment, user)
                card += f"\nИсточник: сайт\nEmail: {escape(account.email)}"
                # Keep full text confirmation in the admin card (and payment attachments).
                payload = {
                    "text": card,
                    "keyboard": keyboards.admin_payment_keyboard(payment.id).model_dump(
                        exclude_none=True
                    ),
                }
                if encoded:
                    await queue(
                        session,
                        settings,
                        {
                            "receipt": encoded,
                            "receipt_caption": f"Квитанция {escape(payment.payment_code)}",
                            "attachment_id": attachment.id,
                            "keyboard": {"inline_keyboard": []},
                        },
                    )
                await queue(session, settings, payload)
                if caption:
                    await queue(
                        session,
                        settings,
                        {
                            "text": f"{escape(payment.payment_code)}\n{escape(caption)}",
                            "keyboard": {"inline_keyboard": []},
                        },
                    )
                await session.commit()
                return web.json_response({"ok": True}, status=201)
            if action == "link":
                if user.telegram_id is not None:
                    return problem("Telegram уже привязан", 409)
                if client is not None or await has_purchase(session, user.id):
                    return problem(
                        "При наличии подписки или заявки привязка недоступна. "
                        "Обратитесь в поддержку.",
                        409,
                    )
                if link and link.status == "pending":
                    return problem("Запрос уже рассматривается", 409)
                from sqlalchemy import func

                target = await session.scalar(
                    select(User).where(
                        func.upper(User.public_id)
                        == str(body.get("public_id", "")).strip().upper(),
                        User.telegram_id.is_not(None),
                    )
                )
                if not target:
                    return problem("Проверьте ID из раздела «Моя подписка» в боте")
                req = WebLinkRequest(
                    account_id=account.id, target_user_id=target.id, status="pending"
                )
                session.add(req)
                await session.flush()
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Одобрить", callback_data=f"weblink:yes:{req.id}"
                            ),
                            InlineKeyboardButton(
                                text="Отклонить", callback_data=f"weblink:no:{req.id}"
                            ),
                        ]
                    ]
                )
                await queue(
                    session,
                    settings,
                    {
                        "text": f"Привязка сайта #{req.id}\n"
                        f"Email заявителя: {escape(account.email)}\n"
                        f"ID владельца: {escape(target.public_id or '')}\n"
                        f"Telegram ID: {target.telegram_id}\n"
                        f"Профиль: @{escape(target.username or '—')}\n"
                        "Проверьте владение аккаунтом перед одобрением.",
                        "keyboard": keyboard.model_dump(exclude_none=True),
                    },
                )
                await session.commit()
                return web.json_response({"ok": True}, status=201)
            if action == "trial":
                if user.telegram_id is None or user.trial_used or client is not None:
                    return problem(
                        "Пробный доступ доступен только после привязки Telegram "
                        "и до первой подписки",
                        409,
                    )
                # Serialize against trial activation in the bot as well.
                await session.execute(select(User).where(User.id == user.id).with_for_update())
                result = await billing.grant_trial(
                    session,
                    user.id,
                    build_updater(timeout=settings.xui_request_timeout),
                    settings.trial_period_days,
                )
                if not result.applied:
                    return problem("Не удалось выдать доступ. Попробуйте позднее.", 503)
                await trigger_configured_sync(settings.subhub_url, settings.subhub_admin_token)
                return web.json_response({"ok": True})
            if action == "connection":
                if not has_client_access(client):
                    return problem("Сначала оформите подписку", 403)
                identities = [
                    client.email or "",
                    *(m.email for m in client.mappings),
                    user.public_id or "",
                ]
                await session.commit()
                try:
                    async with SubHubClient(
                        settings.subhub_url, settings.subhub_admin_token
                    ) as hub:
                        resolved = await hub.resolve_candidates_after_sync(
                            identities, attempts=settings.subhub_resolve_attempts
                        )
                    return web.json_response(
                        {"url": resolved.subscription_url, "happ_url": resolved.happ_url}
                    )
                except (SubHubError, ValueError):
                    return problem("Подписка готовится. Попробуйте ещё раз через минуту.", 503)
            return problem("Not found", 404)

    @web.middleware
    async def errors(request, handler):
        try:
            return await handler(request)
        except web.HTTPException:
            raise
        except Exception as exc:
            # SQL errors can contain bound parameters (receipts and identities).
            logger.warning("Web bridge request failed (%s)", type(exc).__name__)
            return problem("Сервис временно недоступен", 503)

    application = web.Application(client_max_size=8 * 1024 * 1024, middlewares=[errors])
    application.router.add_post("/internal/{action}", handle)
    runner = web.AppRunner(application, access_log=None)
    await runner.setup()
    await web.TCPSite(runner, settings.web_bridge_host, settings.web_bridge_port).start()
    return runner

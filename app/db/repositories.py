from __future__ import annotations

import secrets
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.enums import AttachmentType, BindRequestStatus, PaymentStatus, Protocol, UserRole
from app.db.models import (
    AuditLog,
    BindRequest,
    ClientServerMapping,
    PaymentAttachment,
    PaymentRequest,
    PendingServerUpdate,
    Server,
    ServerInbound,
    User,
    VpnClient,
)


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_public_id(self, public_id: str) -> User | None:
        cleaned = public_id.strip()
        if not cleaned:
            return None
        result = await self.session.execute(
            select(User).where(User.public_id == cleaned)
        )
        user = result.scalar_one_or_none()
        if user is not None:
            return user

        result = await self.session.execute(
            select(User).where(func.upper(User.public_id) == cleaned.upper())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def all_telegram_ids(self) -> list[int]:
        """Telegram ID всех пользователей, когда-либо запускавших бота."""
        result = await self.session.execute(
            select(User.telegram_id).order_by(User.id.asc())
        )
        return [int(tid) for tid in result.scalars().all() if tid is not None]

    async def count(self) -> int:
        from sqlalchemy import func

        result = await self.session.execute(select(func.count(User.id)))
        return int(result.scalar_one())

    async def _generate_public_id(self) -> str:
        """Генерирует короткий уникальный публичный ID пользователя."""
        while True:
            code = secrets.token_hex(4).upper()  # 8 hex-символов, напр. 'A1B2C3D4'
            existing = await self.session.execute(
                select(User.id).where(User.public_id == code)
            )
            if existing.first() is None:
                return code

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        role: UserRole = UserRole.USER,
    ) -> tuple[User, bool]:
        user = await self.get_by_telegram_id(telegram_id)
        if user is not None:
            changed = False
            if username is not None and user.username != username:
                user.username = username
                changed = True
            if first_name is not None and user.first_name != first_name:
                user.first_name = first_name
                changed = True
            if user.public_id is None:
                user.public_id = await self._generate_public_id()
                changed = True
            if changed:
                await self.session.flush()
            return user, False

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            role=role,
            public_id=await self._generate_public_id(),
        )
        self.session.add(user)
        await self.session.flush()
        return user, True

    async def delete_user(self, user: User) -> None:
        """Удаляет пользователя и связанные записи (каскад в ORM)."""
        await self.session.delete(user)
        await self.session.flush()


class VpnClientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_user(self, user_id: int) -> VpnClient | None:
        result = await self.session.execute(
            select(VpnClient)
            .where(VpnClient.user_id == user_id)
            .options(selectinload(VpnClient.mappings))
        )
        return result.scalars().first()

    async def get_for_user_client(self, vpn_client_id: int) -> VpnClient | None:
        result = await self.session.execute(
            select(VpnClient)
            .where(VpnClient.id == vpn_client_id)
            .options(selectinload(VpnClient.mappings))
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[VpnClient]:
        now = _utcnow()
        result = await self.session.execute(
            select(VpnClient)
            .where(VpnClient.expires_at.is_not(None))
            .where(VpnClient.expires_at > now)
            .options(selectinload(VpnClient.user))
        )
        return list(result.scalars().all())

    async def list_expired(self) -> list[VpnClient]:
        now = _utcnow()
        result = await self.session.execute(
            select(VpnClient)
            .where((VpnClient.expires_at.is_(None)) | (VpnClient.expires_at <= now))
            .options(selectinload(VpnClient.user))
        )
        return list(result.scalars().all())

    async def list_for_expiry_notifications(
        self, now: datetime, horizon_hours: int = 24
    ) -> list[VpnClient]:
        """Клиенты, которым пора слать уведомление об окончании.

        Берём тех, у кого задан срок, ещё не пройдена финальная стадия
        уведомлений (stage < 3) и срок наступает не позже горизонта (по умолчанию
        24 ч) — включая уже истёкшие.
        """
        from datetime import timedelta

        deadline = now + timedelta(hours=horizon_hours)
        result = await self.session.execute(
            select(VpnClient)
            .where(VpnClient.expires_at.is_not(None))
            .where(VpnClient.expires_at <= deadline)
            .where(VpnClient.expiry_notify_stage < 3)
            .options(selectinload(VpnClient.user))
        )
        return list(result.scalars().all())


class ServerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, server_id: int) -> Server | None:
        return await self.session.get(Server, server_id)

    async def get_with_inbounds(self, server_id: int) -> Server | None:
        result = await self.session.execute(
            select(Server)
            .where(Server.id == server_id)
            .options(selectinload(Server.inbounds))
        )
        return result.scalar_one_or_none()

    async def add(self, server: Server) -> Server:
        self.session.add(server)
        await self.session.flush()
        return server

    async def delete(self, server_id: int) -> bool:
        """Удаляет сервер вместе с inbound'ами и привязками (каскад).

        Коллекции грузим заранее: cascade='all, delete-orphan' в async-сессии
        требует, чтобы связанные объекты были загружены до flush.
        """
        result = await self.session.execute(
            select(Server)
            .where(Server.id == server_id)
            .options(
                selectinload(Server.inbounds),
                selectinload(Server.mappings),
            )
        )
        server = result.scalar_one_or_none()
        if server is None:
            return False
        await self.session.delete(server)
        await self.session.flush()
        return True

    async def list_enabled(self) -> list[Server]:
        result = await self.session.execute(
            select(Server).where(Server.enabled.is_(True))
        )
        return list(result.scalars().all())

    async def list_enabled_with_inbounds(self) -> list[Server]:
        result = await self.session.execute(
            select(Server)
            .where(Server.enabled.is_(True))
            .options(selectinload(Server.inbounds))
            .order_by(Server.id.asc())
            .execution_options(populate_existing=True)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Server]:
        result = await self.session.execute(
            select(Server).options(selectinload(Server.inbounds)).order_by(
                Server.id.asc()
            )
        )
        return list(result.scalars().all())

    async def list_inbounds(self, server_id: int) -> list[ServerInbound]:
        result = await self.session.execute(
            select(ServerInbound)
            .where(ServerInbound.server_id == server_id)
            .order_by(ServerInbound.inbound_id.asc())
        )
        return list(result.scalars().all())

    async def get_inbound(
        self, server_id: int, inbound_id: int
    ) -> ServerInbound | None:
        result = await self.session.execute(
            select(ServerInbound)
            .where(ServerInbound.server_id == server_id)
            .where(ServerInbound.inbound_id == inbound_id)
        )
        return result.scalar_one_or_none()

    async def delete_inbound(self, server_id: int, inbound_id: int) -> int:
        """Удаляет настроенный inbound. Возвращает число удалённых записей."""
        rows = await self.list_inbounds(server_id)
        deleted = 0
        for row in rows:
            if row.inbound_id == inbound_id:
                await self.session.delete(row)
                deleted += 1
        return deleted

    async def clear_inbounds(self, server_id: int) -> int:
        """Удаляет все настроенные inbound'ы сервера. Возвращает их число."""
        rows = await self.list_inbounds(server_id)
        for row in rows:
            await self.session.delete(row)
        return len(rows)

    async def set_status(self, server_id: int, online: bool) -> None:
        """Сохраняет результат фоновой проверки доступности сервера."""
        server = await self.session.get(Server, server_id)
        if server is None:
            return
        server.is_online = online
        server.last_checked_at = _utcnow()
        await self.session.flush()

    async def has_provision_targets(self) -> bool:
        result = await self.session.execute(
            select(ServerInbound.id)
            .join(Server, Server.id == ServerInbound.server_id)
            .where(Server.enabled.is_(True))
            .where(ServerInbound.enabled.is_(True))
            .limit(1)
        )
        return result.first() is not None


class MappingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_client(self, vpn_client_id: int) -> list[ClientServerMapping]:
        result = await self.session.execute(
            select(ClientServerMapping)
            .where(ClientServerMapping.vpn_client_id == vpn_client_id)
            .options(selectinload(ClientServerMapping.server))
        )
        return list(result.scalars().all())

    async def get_for_inbound(
        self, vpn_client_id: int, server_id: int, inbound_id: int
    ) -> ClientServerMapping | None:
        result = await self.session.execute(
            select(ClientServerMapping)
            .where(ClientServerMapping.vpn_client_id == vpn_client_id)
            .where(ClientServerMapping.server_id == server_id)
            .where(ClientServerMapping.inbound_id == inbound_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        vpn_client_id: int,
        server_id: int,
        inbound_id: int,
        protocol: Protocol,
        client_uuid: str,
        email: str,
        sub_id: str | None = None,
    ) -> ClientServerMapping:
        mapping = ClientServerMapping(
            vpn_client_id=vpn_client_id,
            server_id=server_id,
            inbound_id=inbound_id,
            protocol=protocol,
            client_uuid=client_uuid,
            email=email,
            sub_id=sub_id,
            enabled=True,
        )
        self.session.add(mapping)
        await self.session.flush()
        return mapping


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, payment_id: int) -> PaymentRequest | None:
        return await self.session.get(PaymentRequest, payment_id)

    async def get_by_id_for_update(
        self, payment_id: int
    ) -> PaymentRequest | None:
        """Берёт заявку с блокировкой строки (SELECT ... FOR UPDATE).

        На Postgres сериализует параллельные подтверждения одной заявки —
        защита от двойного применения при двойном клике/ретрае админа. На
        SQLite FOR UPDATE не поддерживается и тихо игнорируется (там запись
        и так сериализуется глобальной блокировкой на коммите).
        """
        result = await self.session.execute(
            select(PaymentRequest)
            .where(PaymentRequest.id == payment_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_relations(
        self, payment_id: int
    ) -> PaymentRequest | None:
        result = await self.session.execute(
            select(PaymentRequest)
            .where(PaymentRequest.id == payment_id)
            .options(
                selectinload(PaymentRequest.user),
                selectinload(PaymentRequest.attachments),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, payment_code: str) -> PaymentRequest | None:
        result = await self.session.execute(
            select(PaymentRequest)
            .where(PaymentRequest.payment_code == payment_code)
            .options(selectinload(PaymentRequest.user))
        )
        return result.scalar_one_or_none()

    async def list_waiting_admin(self) -> list[PaymentRequest]:
        result = await self.session.execute(
            select(PaymentRequest)
            .where(PaymentRequest.status == PaymentStatus.WAITING_ADMIN)
            .order_by(PaymentRequest.id.asc())
            .options(selectinload(PaymentRequest.user))
        )
        return list(result.scalars().all())

    async def create(
        self,
        user_id: int,
        amount: float,
        period_days: int,
        payment_code: str,
        currency: str = "RUB",
        status: PaymentStatus = PaymentStatus.CREATED,
    ) -> PaymentRequest:
        payment = PaymentRequest(
            user_id=user_id,
            amount=amount,
            currency=currency,
            period_days=period_days,
            payment_code=payment_code,
            status=status,
        )
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def count(self) -> int:
        from sqlalchemy import func

        result = await self.session.execute(select(func.count(PaymentRequest.id)))
        return int(result.scalar_one())

    async def count_applied_for_user(self, user_id: int) -> int:
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count(PaymentRequest.id))
            .where(PaymentRequest.user_id == user_id)
            .where(PaymentRequest.status == PaymentStatus.APPLIED)
        )
        return int(result.scalar_one())

    async def delete(self, payment: PaymentRequest) -> None:
        """Удаляет заявку (вместе с вложениями по каскаду)."""
        await self.session.delete(payment)
        await self.session.flush()

    async def latest_open_for_user(self, user_id: int) -> PaymentRequest | None:
        result = await self.session.execute(
            select(PaymentRequest)
            .where(PaymentRequest.user_id == user_id)
            .where(
                PaymentRequest.status.in_(
                    [PaymentStatus.CREATED, PaymentStatus.WAITING_ADMIN]
                )
            )
            .order_by(PaymentRequest.id.desc())
        )
        return result.scalars().first()

    async def last_successful_for_user(self, user_id: int) -> PaymentRequest | None:
        """Последняя успешная (применённая/подтверждённая) оплата пользователя.

        Используется, чтобы (1) понять, оформлял ли пользователь подписку хоть раз
        (тогда пробный больше не предлагаем) и (2) подсказать прошлый тариф при
        продлении.
        """
        result = await self.session.execute(
            select(PaymentRequest)
            .where(PaymentRequest.user_id == user_id)
            .where(
                PaymentRequest.status.in_(
                    [PaymentStatus.APPLIED, PaymentStatus.CONFIRMED]
                )
            )
            .order_by(PaymentRequest.id.desc())
        )
        return result.scalars().first()

    async def history_for_user(self, user_id: int) -> list[PaymentRequest]:
        result = await self.session.execute(
            select(PaymentRequest)
            .where(PaymentRequest.user_id == user_id)
            .order_by(PaymentRequest.id.desc())
        )
        return list(result.scalars().all())

    async def add_attachment(
        self,
        payment_request_id: int,
        file_type: AttachmentType,
        telegram_file_id: str | None = None,
        caption: str | None = None,
    ) -> PaymentAttachment:
        attachment = PaymentAttachment(
            payment_request_id=payment_request_id,
            file_type=file_type,
            telegram_file_id=telegram_file_id,
            caption=caption,
        )
        self.session.add(attachment)
        await self.session.flush()
        return attachment


class BindRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, request_id: int) -> BindRequest | None:
        return await self.session.get(BindRequest, request_id)

    async def get_by_id_with_user(self, request_id: int) -> BindRequest | None:
        result = await self.session.execute(
            select(BindRequest)
            .where(BindRequest.id == request_id)
            .options(selectinload(BindRequest.user))
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> BindRequest | None:
        result = await self.session.execute(
            select(BindRequest)
            .where(BindRequest.request_code == code)
            .options(selectinload(BindRequest.user))
        )
        return result.scalar_one_or_none()

    async def latest_waiting_for_user(self, user_id: int) -> BindRequest | None:
        result = await self.session.execute(
            select(BindRequest)
            .where(BindRequest.user_id == user_id)
            .where(BindRequest.status == BindRequestStatus.WAITING_ADMIN)
            .order_by(BindRequest.id.desc())
        )
        return result.scalars().first()

    async def list_waiting_admin(self) -> list[BindRequest]:
        result = await self.session.execute(
            select(BindRequest)
            .where(BindRequest.status == BindRequestStatus.WAITING_ADMIN)
            .order_by(BindRequest.id.asc())
            .options(selectinload(BindRequest.user))
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        from sqlalchemy import func

        result = await self.session.execute(select(func.count(BindRequest.id)))
        return int(result.scalar_one())

    async def _generate_request_code(self) -> str:
        while True:
            code = f"BIND-{secrets.token_hex(4).upper()}"
            existing = await self.session.execute(
                select(BindRequest.id).where(BindRequest.request_code == code)
            )
            if existing.first() is None:
                return code

    async def create(
        self,
        user_id: int,
        subscription_link: str,
        public_id: str,
    ) -> BindRequest:
        request_code = await self._generate_request_code()
        req = BindRequest(
            user_id=user_id,
            subscription_link=subscription_link,
            public_id=public_id,
            request_code=request_code,
            status=BindRequestStatus.WAITING_ADMIN,
        )
        self.session.add(req)
        await self.session.flush()
        return req


class PendingServerUpdateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_pending(
        self,
        *,
        vpn_client_id: int,
        server_id: int,
        payment_request_id: int | None,
    ) -> PendingServerUpdate | None:
        query = (
            select(PendingServerUpdate)
            .where(PendingServerUpdate.vpn_client_id == vpn_client_id)
            .where(PendingServerUpdate.server_id == server_id)
            .where(PendingServerUpdate.status == "pending")
        )
        if payment_request_id is None:
            query = query.where(PendingServerUpdate.payment_request_id.is_(None))
        else:
            query = query.where(
                PendingServerUpdate.payment_request_id == payment_request_id
            )
        result = await self.session.execute(query.order_by(PendingServerUpdate.id.desc()))
        return result.scalars().first()

    async def upsert_pending(
        self,
        *,
        vpn_client_id: int,
        server_id: int,
        payment_request_id: int | None,
        target_expires_at: datetime,
        last_error: str | None,
    ) -> PendingServerUpdate:
        existing = await self.get_pending(
            vpn_client_id=vpn_client_id,
            server_id=server_id,
            payment_request_id=payment_request_id,
        )
        if existing is not None:
            existing.target_expires_at = target_expires_at
            existing.last_error = last_error
            existing.next_retry_at = None
            await self.session.flush()
            return existing

        update = PendingServerUpdate(
            vpn_client_id=vpn_client_id,
            server_id=server_id,
            payment_request_id=payment_request_id,
            target_expires_at=target_expires_at,
            status="pending",
            attempts=0,
            last_error=last_error,
        )
        self.session.add(update)
        await self.session.flush()
        return update

    async def list_pending_for_server(
        self, server_id: int
    ) -> list[PendingServerUpdate]:
        result = await self.session.execute(
            select(PendingServerUpdate)
            .where(PendingServerUpdate.server_id == server_id)
            .where(PendingServerUpdate.status == "pending")
            .order_by(PendingServerUpdate.id.asc())
        )
        return list(result.scalars().all())


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self,
        action: str,
        actor_user_id: int | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        payload: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            action=action,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

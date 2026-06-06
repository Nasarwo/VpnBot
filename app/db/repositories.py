from __future__ import annotations

import secrets
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.enums import AttachmentType, PaymentStatus, Protocol, UserRole
from app.db.models import (
    AuditLog,
    ClientServerMapping,
    PaymentAttachment,
    PaymentRequest,
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

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

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


class ServerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, server_id: int) -> Server | None:
        return await self.session.get(Server, server_id)

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
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Server]:
        result = await self.session.execute(
            select(Server).options(selectinload(Server.inbounds)).order_by(
                Server.id.asc()
            )
        )
        return list(result.scalars().all())

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

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.enums import (
    AttachmentType,
    BindRequestStatus,
    PaymentStatus,
    Protocol,
    UserRole,
)
from app.db.types import EncryptedString


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    public_id: Mapped[str | None] = mapped_column(
        String(32), unique=True, index=True, nullable=True
    )
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=16),
        default=UserRole.USER,
        nullable=False,
    )
    trial_used: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="0"
    )
    # Пользователь прошёл вопрос «были ли вы клиентом до бота» (да/нет).
    onboarding_done: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="0"
    )

    vpn_clients: Mapped[list[VpnClient]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    payment_requests: Mapped[list[PaymentRequest]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    bind_requests: Mapped[list[BindRequest]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class VpnClient(Base):
    __tablename__ = "vpn_clients"
    __table_args__ = (UniqueConstraint("user_id", name="uq_vpn_clients_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_client_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subscription_url_direct: Mapped[str | None] = mapped_column(Text, nullable=True)
    subscription_url_ru_proxy: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Стадия отправленных уведомлений об окончании текущего срока:
    # 0 — ничего, 1 — «за день», 2 — «за час», 3 — «истекла».
    # Сбрасывается в 0 при продлении/выдаче нового срока.
    expiry_notify_stage: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default="0"
    )

    user: Mapped[User] = relationship(back_populates="vpn_clients")
    mappings: Mapped[list[ClientServerMapping]] = relationship(
        back_populates="vpn_client", cascade="all, delete-orphan"
    )


class Server(Base):
    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    panel_url: Mapped[str] = mapped_column(String(512), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(EncryptedString(1024), nullable=False)
    # Тип сервера для отображения: direct (зарубежный exit) / ru_proxy (RU-вход) и т.п.
    kind: Mapped[str] = mapped_column(
        String(16), default="direct", nullable=False, server_default="direct"
    )
    # База ссылки-подписки 3x-ui, напр. https://host:2096/sub/ — полный URL = base + public_id
    subscription_base: Mapped[str | None] = mapped_column(String(512), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Результат фоновой проверки доступности панели: None — ещё не проверялся.
    is_online: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    mappings: Mapped[list[ClientServerMapping]] = relationship(
        back_populates="server", cascade="all, delete-orphan"
    )
    inbounds: Mapped[list[ServerInbound]] = relationship(
        back_populates="server", cascade="all, delete-orphan"
    )


class ServerInbound(Base):
    """Inbound на панели сервера, в который нужно заводить клиентов.

    На одном сервере может быть несколько inbound'ов с разными протоколами/транспортами.
    """

    __tablename__ = "server_inbounds"
    __table_args__ = (
        UniqueConstraint(
            "server_id",
            "inbound_id",
            name="uq_server_inbounds_server_inbound",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    inbound_id: Mapped[int] = mapped_column(Integer, nullable=False)
    protocol: Mapped[Protocol] = mapped_column(
        Enum(Protocol, native_enum=False, length=16), nullable=False
    )
    # Для vless+reality обычно flow=xtls-rprx-vision; для ws/grpc/xhttp — пусто.
    flow: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # Для shadowsocks: метод шифрования (если задаётся на уровне клиента).
    method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    server: Mapped[Server] = relationship(back_populates="inbounds")


class ClientServerMapping(Base):
    __tablename__ = "client_server_mappings"
    __table_args__ = (
        UniqueConstraint(
            "vpn_client_id",
            "server_id",
            "inbound_id",
            name="uq_client_server_mappings_client_server_inbound",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vpn_client_id: Mapped[int] = mapped_column(
        ForeignKey("vpn_clients.id", ondelete="CASCADE"), index=True, nullable=False
    )
    server_id: Mapped[int] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    inbound_id: Mapped[int] = mapped_column(Integer, nullable=False)
    protocol: Mapped[Protocol] = mapped_column(
        Enum(Protocol, native_enum=False, length=16), nullable=False
    )
    client_uuid: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    sub_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    vpn_client: Mapped[VpnClient] = relationship(back_populates="mappings")
    server: Mapped[Server] = relationship(back_populates="mappings")


class PaymentRequest(Base):
    __tablename__ = "payment_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="RUB", nullable=False)
    period_days: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False, length=16),
        default=PaymentStatus.CREATED,
        index=True,
        nullable=False,
    )
    payment_code: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    admin_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Целевой срок доступа, зафиксированный до обновления панелей (для идемпотентного retry).
    target_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[User] = relationship(back_populates="payment_requests")
    attachments: Mapped[list[PaymentAttachment]] = relationship(
        back_populates="payment_request", cascade="all, delete-orphan"
    )


class PaymentAttachment(Base):
    __tablename__ = "payment_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_request_id: Mapped[int] = mapped_column(
        ForeignKey("payment_requests.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    telegram_file_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_type: Mapped[AttachmentType] = mapped_column(
        Enum(AttachmentType, native_enum=False, length=16), nullable=False
    )
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    payment_request: Mapped[PaymentRequest] = relationship(
        back_populates="attachments"
    )


class BindRequest(Base):
    """Заявка на привязку существующей подписки (до внедрения бота)."""

    __tablename__ = "bind_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    subscription_link: Mapped[str] = mapped_column(Text, nullable=False)
    public_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    request_code: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    status: Mapped[BindRequestStatus] = mapped_column(
        Enum(BindRequestStatus, native_enum=False, length=16),
        default=BindRequestStatus.WAITING_ADMIN,
        index=True,
        nullable=False,
    )
    admin_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[User] = relationship(back_populates="bind_requests")


class IpObservation(Base):
    __tablename__ = "ip_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vpn_client_id: Mapped[int] = mapped_column(
        ForeignKey("vpn_clients.id", ondelete="CASCADE"), index=True, nullable=False
    )
    server_id: Mapped[int | None] = mapped_column(
        ForeignKey("servers.id", ondelete="SET NULL"), nullable=True
    )
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip: Mapped[str] = mapped_column(String(64), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

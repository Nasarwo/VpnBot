from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
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
    telegram_id: Mapped[int | None] = mapped_column(
        BigInteger, unique=True, index=True, nullable=True
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
    whitelist_account: Mapped[WhitelistAccount | None] = relationship(
        cascade="all, delete-orphan", uselist=False
    )
    whitelist_ledger: Mapped[list[WhitelistLedger]] = relationship(
        cascade="all, delete-orphan",
        foreign_keys="WhitelistLedger.user_id",
    )


class TrialGrant(Base):
    """Пробный период, выданный Telegram-аккаунту.

    Хранится по Telegram ID отдельно от ``users``: сброс бота удаляет ``User`` и
    создаёт новую запись для того же Telegram ID, а факт использования trial
    должен остаться. ``user_id`` — справочно, без внешнего ключа: пользователь,
    получивший trial, может быть уже удалён.
    """

    __tablename__ = "trial_grants"

    telegram_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=False
    )
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SubscriptionPurchase(Base):
    """Первая применённая оплата подписки Telegram-аккаунта.

    Закрывает trial так же, как ``trial_grants``: хранится по Telegram ID без
    внешних ключей, поэтому сброс бота, удаляющий ``User`` вместе с заявками,
    факт оплаты не удаляет. ``user_id`` и ``payment_request_id`` — справочно:
    пользователь и заявка могут быть уже удалены.
    """

    __tablename__ = "subscription_purchases"

    telegram_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=False
    )
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payment_request_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class WebAccount(Base):
    __tablename__ = "web_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), unique=True
    )
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    verified: Mapped[bool] = mapped_column(Boolean, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WebLinkRequest(Base):
    __tablename__ = "web_link_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("web_accounts.id", ondelete="CASCADE"))
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class WebToken(Base):
    __tablename__ = "web_tokens"

    account_id: Mapped[int] = mapped_column(
        ForeignKey("web_accounts.id", ondelete="CASCADE"), primary_key=True
    )
    purpose: Mapped[str] = mapped_column(String(16), primary_key=True)
    digest: Mapped[str] = mapped_column(String(64))
    attempts: Mapped[int] = mapped_column(Integer, server_default="0")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WebSession(Base):
    __tablename__ = "web_sessions"

    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("web_accounts.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WebDelivery(Base):
    """Durable per-admin Telegram delivery, retried independently of HTTP requests."""

    __tablename__ = "web_deliveries"
    __table_args__ = (Index("ix_web_deliveries_due", "status", "next_attempt_at"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_id: Mapped[int] = mapped_column(BigInteger)
    payload: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
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
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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


SERVER_PURPOSE_STANDARD = "standard"
SERVER_PURPOSE_WHITELIST = "whitelist"


class Server(Base):
    __tablename__ = "servers"
    __table_args__ = (
        # Независимые панели не делят одну квоту: активен не более чем один
        # сервер услуги «Обход белых списков».
        Index(
            "uq_servers_single_enabled_whitelist",
            "purpose",
            unique=True,
            sqlite_where=text("purpose = 'whitelist' AND enabled"),
            postgresql_where=text("purpose = 'whitelist' AND enabled"),
        ),
    )

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
    # Назначение услуги (не путать с сетевой ролью kind): standard — обычный
    # безлимитный VPN, whitelist — «Обход белых списков» с учётом трафика.
    purpose: Mapped[str] = mapped_column(
        String(16),
        default=SERVER_PURPOSE_STANDARD,
        nullable=False,
        server_default=SERVER_PURPOSE_STANDARD,
    )
    # Результат последней сверки inbound'ов (используется для whitelist-сервера):
    # None — не выполнялась, ready / error / needs_choice.
    inventory_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    inventory_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    inventory_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Результат фоновой проверки доступности панели: None — ещё не проверялся.
    is_online: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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


PAYMENT_KIND_SUBSCRIPTION = "subscription"
PAYMENT_KIND_TRAFFIC = "traffic"


class PaymentRequest(Base):
    __tablename__ = "payment_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="RUB", nullable=False)
    # Для покупки трафика срок не начисляется: period_days = 0.
    period_days: Mapped[int] = mapped_column(Integer, nullable=False)
    # subscription — продление VPN; traffic — пакет «Обход белых списков».
    kind: Mapped[str] = mapped_column(
        String(16),
        default=PAYMENT_KIND_SUBSCRIPTION,
        nullable=False,
        server_default=PAYMENT_KIND_SUBSCRIPTION,
    )
    # Снимок пакета на момент создания заявки: объём и название не меняются
    # при последующем редактировании пакетов администратором.
    traffic_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    traffic_package_id: Mapped[int | None] = mapped_column(
        ForeignKey("traffic_packages.id", ondelete="SET NULL"), nullable=True
    )
    traffic_package_title: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False, length=16),
        default=PaymentStatus.CREATED,
        index=True,
        nullable=False,
    )
    payment_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    admin_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Покупка трафика: версия desired учёта (whitelist_accounts.desired_version), с
    # которой начисление попадает на панель. NULL — ожидания нет; значение снимается,
    # когда applied_version достигла её и событие учёта сверено с расходом.
    apply_pending_version: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    payment_request: Mapped[PaymentRequest] = relationship(back_populates="attachments")


class BindRequest(Base):
    """Заявка на привязку существующей подписки (до внедрения бота)."""

    __tablename__ = "bind_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    subscription_link: Mapped[str] = mapped_column(Text, nullable=False)
    public_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    request_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
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
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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


class PendingServerUpdate(Base, TimestampMixin):
    __tablename__ = "pending_server_updates"
    __table_args__ = (Index("ix_pending_server_updates_status_server", "status", "server_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vpn_client_id: Mapped[int] = mapped_column(
        ForeignKey("vpn_clients.id", ondelete="CASCADE"), index=True, nullable=False
    )
    server_id: Mapped[int] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    payment_request_id: Mapped[int | None] = mapped_column(
        ForeignKey("payment_requests.id", ondelete="SET NULL"), index=True, nullable=True
    )
    target_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), default="pending", nullable=False, server_default="pending"
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    vpn_client: Mapped[VpnClient] = relationship()
    server: Mapped[Server] = relationship()
    payment_request: Mapped[PaymentRequest | None] = relationship()


class TrafficPackage(Base):
    """Пакет покупки трафика «Обход белых списков» (настраивается админом)."""

    __tablename__ = "traffic_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    traffic_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, server_default=text("true")
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WhitelistConfig(Base):
    """Единственная строка настроек услуги (id = 1)."""

    __tablename__ = "whitelist_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Услуга запущена администратором: оплаты и trial начинают выдавать пакеты.
    service_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default=text("false")
    )
    paid_free_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    trial_free_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WhitelistAccount(Base):
    """Бизнес-учёт трафика пользователя на whitelist-сервере.

    Остатки ``free_bytes``/``paid_bytes`` — подтверждённые: на контрольной точке
    ``usage_checkpoint_bytes`` (накопленный up+down клиента панели) с учётом всех
    применённых событий журнала. Неприменённые события (``WhitelistLedger``
    pending/uncertain) их не меняют. Панели задаётся абсолютная квота
    ``checkpoint + free + paid`` с предварительно (без расхода) применёнными
    неприменёнными событиями — гарантированная нижняя граница остатка.
    ``last_synced_at`` — момент, к которому относятся подтверждённые остатки.

    Значения счётчика (точка, привязки событий) хранятся в координатах текущей
    эпохи строки статистики. При сбросе/пересоздании клиента новая эпоха
    продолжает последнее прочитанное значение прежней: прежние значения
    сдвигаются, и точка может стать отрицательной — это расход прежней эпохи,
    ещё не списанный с остатков (ждёт решения администратора).
    """

    __tablename__ = "whitelist_accounts"
    __table_args__ = (UniqueConstraint("user_id", name="uq_whitelist_accounts_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    free_bytes: Mapped[int] = mapped_column(
        BigInteger, default=0, nullable=False, server_default="0"
    )
    paid_bytes: Mapped[int] = mapped_column(
        BigInteger, default=0, nullable=False, server_default="0"
    )
    # Сервер и строка статистики панели, к которым относится контрольная точка.
    server_id: Mapped[int | None] = mapped_column(
        ForeignKey("servers.id", ondelete="SET NULL"), nullable=True
    )
    # Идентичность клиента на whitelist-панели (совпадает с общей идентичностью
    # подписки, чтобы SubHub включил конфиг в существующую ссылку).
    panel_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    usage_checkpoint_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    traffic_row_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Последнее прочитанное значение счётчика текущей эпохи и момент, не раньше
    # которого оно прочитано (пакетное чтение, начатое до него, устарело).
    # Обновляется и тогда, когда остатки не сверяются (событие ждёт решения):
    # по нему обнаруживается сброс счётчика.
    usage_observed_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    usage_observed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Целевое состояние панели: desired_version растёт при каждом изменении
    # остатков/доступа; applied_version — последнее подтверждённое панелью.
    desired_version: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, server_default="1"
    )
    applied_version: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default="0"
    )
    applied_total_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    applied_enable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    applied_expiry_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default="0"
    )
    next_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Расхождение счётчика (сброс/пересоздание клиента панели) для администратора.
    conflict: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Отключение администратором (в боте или вручную на панели) — не снимается
    # фоновыми повторами и чтением баланса.
    admin_blocked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default=text("false")
    )
    # Подтверждённое размещение клиента: сервер, целевой inbound и flow, на которых
    # чтением подтверждено, что клиент привязан к цели, а прежние привязки услуги
    # сняты. NULL — не подтверждалось (в т. ч. строки до миграции a4b5c6d7e8f9):
    # очередь проверит размещение заново. flow '' — без flow.
    placement_server_id: Mapped[int | None] = mapped_column(
        ForeignKey("servers.id", ondelete="SET NULL"), nullable=True
    )
    placement_inbound_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    placement_flow: Mapped[str | None] = mapped_column(String(32), nullable=True)
    placement_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    __mapper_args__ = {"version_id_col": version}


class WhitelistPlacement(Base):
    """Привязка клиента whitelist-панели к inbound'у, созданная самой услугой.

    Строка появляется до запроса attach/create, только если чтение перед ним
    показало, что привязки нет (``attaching``), и подтверждается чтением после
    него (``attached``). Привязки без строки — чужие или неизвестного
    происхождения: услуга их не снимает. При смене цели прежние привязки услуги
    снимаются (``detaching``) после подтверждения новой; строка удаляется, когда
    чтение показало, что привязки на панели нет.
    """

    __tablename__ = "whitelist_placements"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "server_id", "inbound_id", name="uq_whitelist_placements_target"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    server_id: Mapped[int] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"), nullable=False
    )
    inbound_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # Email клиента панели, под которым создана привязка.
    panel_email: Mapped[str] = mapped_column(String(255), nullable=False)
    # attaching | attached | detaching
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    # service — создана услугой; claimed — признана администратором (/wlclaim).
    origin: Mapped[str] = mapped_column(
        String(16), nullable=False, default="service", server_default="service"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WhitelistLedger(Base):
    """Журнал выдач/начислений/корректировок, привязанных к исходной операции.

    Выдача пакета (``free_set``) и покупка (``paid_delta``) — упорядоченные (по
    ``id``) события учёта. Событие применяется к подтверждённым остаткам учёта
    только вместе с расходом до него, поэтому ему нужна привязка к счётчику
    панели ``anchor_bytes``. Без привязки событие ждёт (``pending``); если
    сверка не может определить, был расход до или после события, оно остаётся
    ``uncertain`` с границами ``anchor_min_bytes..anchor_max_bytes`` до решения
    администратора. ``free/paid_before/after`` у неприменённого события —
    предварительные (без расхода) и уточняются при применении.
    """

    __tablename__ = "whitelist_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # free_grant | purchase | rollout | usage_rebase | adjust
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    # Уникальный ключ исходной операции: payment:12, trial:5, rollout:5 …
    source_key: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    payment_request_id: Mapped[int | None] = mapped_column(
        ForeignKey("payment_requests.id", ondelete="SET NULL"), nullable=True
    )
    free_before: Mapped[int] = mapped_column(BigInteger, nullable=False)
    free_after: Mapped[int] = mapped_column(BigInteger, nullable=False)
    paid_before: Mapped[int] = mapped_column(BigInteger, nullable=False)
    paid_after: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # settled | pending | uncertain (см. docstring).
    status: Mapped[str] = mapped_column(
        String(16), default="settled", nullable=False, server_default="settled"
    )
    # Действие события: бесплатный остаток := free_set; купленный += paid_delta.
    free_set: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    paid_delta: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Значение счётчика up+down панели в момент события (если известно).
    anchor_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    anchor_min_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    anchor_max_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Время события (для событий учёта задаётся явно, с часовым поясом).
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
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

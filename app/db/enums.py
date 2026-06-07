from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class PaymentStatus(str, enum.Enum):
    CREATED = "created"
    WAITING_ADMIN = "waiting_admin"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"


class BindRequestStatus(str, enum.Enum):
    WAITING_ADMIN = "waiting_admin"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class AttachmentType(str, enum.Enum):
    TEXT = "text"
    PHOTO = "photo"
    DOCUMENT = "document"


class Protocol(str, enum.Enum):
    VMESS = "vmess"
    VLESS = "vless"
    TROJAN = "trojan"
    SHADOWSOCKS = "shadowsocks"
    HYSTERIA2 = "hysteria2"

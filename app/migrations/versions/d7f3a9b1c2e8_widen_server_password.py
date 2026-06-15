"""widen servers.password for encrypted values

Revision ID: d7f3a9b1c2e8
Revises: c1d2e3f4a5b6
Create Date: 2026-06-16 00:00:00.000000

Пароль панели теперь хранится в зашифрованном виде (Fernet), шифротекст длиннее
исходного значения — расширяем колонку с 255 до 512 символов. Сами значения
шифруются прозрачно на уровне приложения (см. app.db.types.EncryptedString),
поэтому миграция меняет только тип/длину колонки.

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d7f3a9b1c2e8"
down_revision: str | None = "c1d2e3f4a5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("servers", schema=None) as batch_op:
        batch_op.alter_column(
            "password",
            existing_type=sa.String(length=255),
            type_=sa.String(length=512),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("servers", schema=None) as batch_op:
        batch_op.alter_column(
            "password",
            existing_type=sa.String(length=512),
            type_=sa.String(length=255),
            existing_nullable=False,
        )

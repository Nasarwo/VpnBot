"""add public_id to users

Revision ID: c3a2b8e5f1d4
Revises: b2f1a7c4d9e0
Create Date: 2026-06-06 07:55:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3a2b8e5f1d4"
down_revision: str | None = "b2f1a7c4d9e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("public_id", sa.String(length=32), nullable=True))
        batch_op.create_index("ix_users_public_id", ["public_id"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_public_id")
        batch_op.drop_column("public_id")

"""Учёт whitelist: последнее прочитанное значение счётчика текущей эпохи.

Пока событие учёта ждёт решения администратора (``uncertain``), контрольная точка
не сдвигается, и сброс счётчика панели нельзя было обнаружить по ней. Новые поля
хранят последнее чтение и его время независимо от состояния событий. Для
существующих строк они пустые: до первого чтения сброс сравнивается с точкой и
границами неприменённых событий, как прежде.

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "f3a4b5c6d7e8"
down_revision: str | None = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("whitelist_accounts") as batch:
        batch.add_column(sa.Column("usage_observed_bytes", sa.BigInteger(), nullable=True))
        batch.add_column(
            sa.Column("usage_observed_at", sa.DateTime(timezone=True), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("whitelist_accounts") as batch:
        batch.drop_column("usage_observed_at")
        batch.drop_column("usage_observed_bytes")

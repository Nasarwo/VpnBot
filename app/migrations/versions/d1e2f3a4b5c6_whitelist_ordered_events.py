"""«Обход белых списков»: упорядоченные события учёта с привязкой к счётчику.

Выдача бесплатного пакета и покупка трафика записываются как события журнала.
Событие без известного расхода до него не применяется к подтверждённым
остаткам (pending), а при невозможности разделить расход — остаётся
uncertain до решения администратора. Существующие строки журнала уже
применены: status=settled.

Revision ID: d1e2f3a4b5c6
Revises: b7c8d9e0f1a2
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "d1e2f3a4b5c6"
down_revision: str | None = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("whitelist_ledger") as batch:
        batch.add_column(
            sa.Column("status", sa.String(16), nullable=False, server_default="settled")
        )
        batch.add_column(sa.Column("free_set", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("paid_delta", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("anchor_bytes", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("anchor_min_bytes", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("anchor_max_bytes", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    # Неприменённые события теряются: перед откатом их нужно разрешить
    # (см. docs/WHITELIST_SERVICE.md, «Откат»).
    with op.batch_alter_table("whitelist_ledger") as batch:
        batch.drop_column("anchor_max_bytes")
        batch.drop_column("anchor_min_bytes")
        batch.drop_column("anchor_bytes")
        batch.drop_column("paid_delta")
        batch.drop_column("free_set")
        batch.drop_column("status")

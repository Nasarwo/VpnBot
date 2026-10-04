"""Заявка на покупку трафика: версия учёта, ожидающая применения на панели.

Ожидание применения раньше записывалось в ``payment_requests.last_error`` и не
снималось после успешной синхронизации. Теперь оно хранится отдельно как версия
``whitelist_accounts.desired_version``, с которой начисление должно быть применено.
Ожидавшие заявки прежней схемы переносятся с версией текущего учёта: она снимется
при ближайшем успешном применении.

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "e2f3a4b5c6d7"
down_revision: str | None = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None

_LEGACY_MARKER = "Трафик начислен; применение на сервере%ожидается"
_DOWNGRADE_MARKER = "Трафик начислен; применение на сервере «Обход белых списков» ожидается"


def upgrade() -> None:
    with op.batch_alter_table("payment_requests") as batch:
        batch.add_column(sa.Column("apply_pending_version", sa.Integer(), nullable=True))
    # Прежний маркер ожидания в last_error переносится в новое поле; иные
    # ошибки заявок не затрагиваются.
    op.execute(
        sa.text(
            "UPDATE payment_requests SET apply_pending_version = COALESCE("
            "(SELECT desired_version FROM whitelist_accounts "
            "WHERE whitelist_accounts.user_id = payment_requests.user_id), 1), "
            "last_error = NULL "
            "WHERE kind = 'traffic' AND last_error LIKE :marker"
        ).bindparams(marker=_LEGACY_MARKER)
    )


def downgrade() -> None:
    # Возвращаем прежний маркер ожидания в last_error (без перезаписи иных ошибок).
    op.execute(
        sa.text(
            "UPDATE payment_requests SET last_error = :marker "
            "WHERE apply_pending_version IS NOT NULL AND last_error IS NULL"
        ).bindparams(marker=_DOWNGRADE_MARKER)
    )
    with op.batch_alter_table("payment_requests") as batch:
        batch.drop_column("apply_pending_version")

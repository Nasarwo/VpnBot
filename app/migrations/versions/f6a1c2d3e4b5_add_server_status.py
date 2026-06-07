"""add server health status fields

Revision ID: f6a1c2d3e4b5
Revises: e5f0a2c9b831
Create Date: 2026-06-07 11:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6a1c2d3e4b5"
down_revision: str | None = "e5f0a2c9b831"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "servers",
        sa.Column("is_online", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "servers",
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("servers", "last_checked_at")
    op.drop_column("servers", "is_online")

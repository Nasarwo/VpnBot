"""add server_inbounds and server provisioning fields

Revision ID: e5f0a2c9b831
Revises: d4e9c1a6b720
Create Date: 2026-06-06 08:20:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f0a2c9b831"
down_revision: str | None = "d4e9c1a6b720"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "servers",
        sa.Column(
            "kind",
            sa.String(length=16),
            nullable=False,
            server_default="direct",
        ),
    )
    op.add_column(
        "servers",
        sa.Column("subscription_base", sa.String(length=512), nullable=True),
    )

    op.create_table(
        "server_inbounds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("server_id", sa.Integer(), nullable=False),
        sa.Column("inbound_id", sa.Integer(), nullable=False),
        sa.Column("protocol", sa.String(length=16), nullable=False),
        sa.Column("flow", sa.String(length=32), nullable=True),
        sa.Column("method", sa.String(length=64), nullable=True),
        sa.Column("remark", sa.String(length=255), nullable=True),
        sa.Column(
            "enabled", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.ForeignKeyConstraint(
            ["server_id"], ["servers.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_server_inbounds_server_id", "server_inbounds", ["server_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_server_inbounds_server_id", table_name="server_inbounds")
    op.drop_table("server_inbounds")
    op.drop_column("servers", "subscription_base")
    op.drop_column("servers", "kind")

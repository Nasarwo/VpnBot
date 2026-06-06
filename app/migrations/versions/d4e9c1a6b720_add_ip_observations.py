"""add ip_observations for anti-sharing monitoring

Revision ID: d4e9c1a6b720
Revises: c3a2b8e5f1d4
Create Date: 2026-06-06 08:02:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e9c1a6b720"
down_revision: str | None = "c3a2b8e5f1d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ip_observations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vpn_client_id", sa.Integer(), nullable=False),
        sa.Column("server_id", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["vpn_client_id"], ["vpn_clients.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["server_id"], ["servers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ip_observations_vpn_client_id", "ip_observations", ["vpn_client_id"]
    )
    op.create_index(
        "ix_ip_observations_observed_at", "ip_observations", ["observed_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_ip_observations_observed_at", table_name="ip_observations")
    op.drop_index("ix_ip_observations_vpn_client_id", table_name="ip_observations")
    op.drop_table("ip_observations")

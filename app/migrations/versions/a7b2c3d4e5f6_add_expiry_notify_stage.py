"""add expiry_notify_stage to vpn_clients

Revision ID: a7b2c3d4e5f6
Revises: f6a1c2d3e4b5
Create Date: 2026-06-07 14:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7b2c3d4e5f6"
down_revision: str | None = "f6a1c2d3e4b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "vpn_clients",
        sa.Column(
            "expiry_notify_stage",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("vpn_clients", "expiry_notify_stage")

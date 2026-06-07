"""add payment target expiry and unique constraints

Revision ID: c1d2e3f4a5b6
Revises: b8c9d0e1f2a3
Create Date: 2026-06-07 21:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: str | None = "b8c9d0e1f2a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "payment_requests",
        sa.Column("target_expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    with op.batch_alter_table("vpn_clients", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_vpn_clients_user_id",
            ["user_id"],
        )

    with op.batch_alter_table("server_inbounds", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_server_inbounds_server_inbound",
            ["server_id", "inbound_id"],
        )

    with op.batch_alter_table("client_server_mappings", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_client_server_mappings_client_server_inbound",
            ["vpn_client_id", "server_id", "inbound_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("client_server_mappings", schema=None) as batch_op:
        batch_op.drop_constraint(
            "uq_client_server_mappings_client_server_inbound",
            type_="unique",
        )

    with op.batch_alter_table("server_inbounds", schema=None) as batch_op:
        batch_op.drop_constraint(
            "uq_server_inbounds_server_inbound",
            type_="unique",
        )

    with op.batch_alter_table("vpn_clients", schema=None) as batch_op:
        batch_op.drop_constraint("uq_vpn_clients_user_id", type_="unique")

    op.drop_column("payment_requests", "target_expires_at")

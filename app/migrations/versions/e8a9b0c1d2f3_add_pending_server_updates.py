"""add pending server updates

Revision ID: e8a9b0c1d2f3
Revises: d7f3a9b1c2e8
Create Date: 2026-06-26 22:45:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e8a9b0c1d2f3"
down_revision: str | None = "d7f3a9b1c2e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pending_server_updates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vpn_client_id", sa.Integer(), nullable=False),
        sa.Column("server_id", sa.Integer(), nullable=False),
        sa.Column("payment_request_id", sa.Integer(), nullable=True),
        sa.Column("target_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default="pending", nullable=False
        ),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["payment_request_id"], ["payment_requests.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["server_id"], ["servers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["vpn_client_id"], ["vpn_clients.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_pending_server_updates_payment_request_id",
        "pending_server_updates",
        ["payment_request_id"],
    )
    op.create_index(
        "ix_pending_server_updates_server_id",
        "pending_server_updates",
        ["server_id"],
    )
    op.create_index(
        "ix_pending_server_updates_vpn_client_id",
        "pending_server_updates",
        ["vpn_client_id"],
    )
    op.create_index(
        "ix_pending_server_updates_status_server",
        "pending_server_updates",
        ["status", "server_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pending_server_updates_status_server",
        table_name="pending_server_updates",
    )
    op.drop_index(
        "ix_pending_server_updates_vpn_client_id",
        table_name="pending_server_updates",
    )
    op.drop_index(
        "ix_pending_server_updates_server_id",
        table_name="pending_server_updates",
    )
    op.drop_index(
        "ix_pending_server_updates_payment_request_id",
        table_name="pending_server_updates",
    )
    op.drop_table("pending_server_updates")

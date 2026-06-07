"""add onboarding_done and bind_requests

Revision ID: b8c9d0e1f2a3
Revises: a7b2c3d4e5f6
Create Date: 2026-06-07 16:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8c9d0e1f2a3"
down_revision: str | None = "a7b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "onboarding_done",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    # Уже зарегистрированные пользователи не должны видеть вопрос повторно.
    op.execute("UPDATE users SET onboarding_done = true")

    op.create_table(
        "bind_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subscription_link", sa.Text(), nullable=False),
        sa.Column("public_id", sa.String(length=64), nullable=False),
        sa.Column("request_code", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("admin_comment", sa.Text(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_bind_requests_user_id"), "bind_requests", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_bind_requests_public_id"), "bind_requests", ["public_id"], unique=False
    )
    op.create_index(
        op.f("ix_bind_requests_request_code"),
        "bind_requests",
        ["request_code"],
        unique=True,
    )
    op.create_index(
        op.f("ix_bind_requests_status"), "bind_requests", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_bind_requests_status"), table_name="bind_requests")
    op.drop_index(op.f("ix_bind_requests_request_code"), table_name="bind_requests")
    op.drop_index(op.f("ix_bind_requests_public_id"), table_name="bind_requests")
    op.drop_index(op.f("ix_bind_requests_user_id"), table_name="bind_requests")
    op.drop_table("bind_requests")
    op.drop_column("users", "onboarding_done")

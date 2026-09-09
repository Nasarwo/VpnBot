"""Independent web accounts, authentication and Telegram delivery queue."""

import sqlalchemy as sa
from alembic import op

revision = "f9b2c3d4e5f6"
down_revision = "e8a9b0c1d2f3"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch:
        batch.alter_column("telegram_id", existing_type=sa.BigInteger(), nullable=True)
    op.create_table(
        "web_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), unique=True
        ),
        sa.Column("email", sa.String(254), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("verified", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "web_tokens",
        sa.Column(
            "account_id",
            sa.Integer(),
            sa.ForeignKey("web_accounts.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("purpose", sa.String(16), primary_key=True),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "sent_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "web_sessions",
        sa.Column("digest", sa.String(64), primary_key=True),
        sa.Column(
            "account_id",
            sa.Integer(),
            sa.ForeignKey("web_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "web_link_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "account_id",
            sa.Integer(),
            sa.ForeignKey("web_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "web_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admin_id", sa.BigInteger(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "next_attempt_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_web_deliveries_due", "web_deliveries", ["status", "next_attempt_at"])


def downgrade():
    # Do not silently destroy independent customers when rolling back.
    if (
        op.get_bind()
        .execute(sa.text("SELECT id FROM users WHERE telegram_id IS NULL LIMIT 1"))
        .first()
    ):
        raise RuntimeError("Web customers exist; export/migrate them before downgrade")
    for table in (
        "web_deliveries",
        "web_link_requests",
        "web_sessions",
        "web_tokens",
        "web_accounts",
    ):
        op.drop_table(table)
    with op.batch_alter_table("users") as batch:
        batch.alter_column("telegram_id", existing_type=sa.BigInteger(), nullable=False)

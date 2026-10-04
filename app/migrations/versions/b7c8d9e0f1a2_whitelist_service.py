"""Услуга «Обход белых списков»: назначение сервера, пакеты, учёт трафика.

Старые серверы получают purpose=standard и остаются безлимитными. Старые
заявки получают kind=subscription. Начальные объёмы бесплатных пакетов и
пакеты покупки записываются один раз; услуга создаётся выключенной.

Revision ID: b7c8d9e0f1a2
Revises: f9b2c3d4e5f6
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "b7c8d9e0f1a2"
down_revision: str | None = "f9b2c3d4e5f6"
branch_labels = None
depends_on = None

GIB = 1024**3


def upgrade() -> None:
    with op.batch_alter_table("servers") as batch:
        batch.add_column(
            sa.Column(
                "purpose", sa.String(16), nullable=False, server_default="standard"
            )
        )
        batch.add_column(sa.Column("inventory_status", sa.String(16), nullable=True))
        batch.add_column(sa.Column("inventory_error", sa.Text(), nullable=True))
        batch.add_column(
            sa.Column("inventory_synced_at", sa.DateTime(timezone=True), nullable=True)
        )
    op.create_index(
        "uq_servers_single_enabled_whitelist",
        "servers",
        ["purpose"],
        unique=True,
        sqlite_where=sa.text("purpose = 'whitelist' AND enabled"),
        postgresql_where=sa.text("purpose = 'whitelist' AND enabled"),
    )

    op.create_table(
        "traffic_packages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("traffic_bytes", sa.BigInteger(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    with op.batch_alter_table("payment_requests") as batch:
        batch.add_column(
            sa.Column(
                "kind", sa.String(16), nullable=False, server_default="subscription"
            )
        )
        batch.add_column(sa.Column("traffic_bytes", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("traffic_package_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("traffic_package_title", sa.String(64), nullable=True))
        batch.create_foreign_key(
            "fk_payment_requests_traffic_package_id",
            "traffic_packages",
            ["traffic_package_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_table(
        "whitelist_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "service_enabled", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("paid_free_bytes", sa.BigInteger(), nullable=False),
        sa.Column("trial_free_bytes", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "whitelist_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("free_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("paid_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column(
            "server_id",
            sa.Integer(),
            sa.ForeignKey("servers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("panel_email", sa.String(255), nullable=True),
        sa.Column("usage_checkpoint_bytes", sa.BigInteger(), nullable=True),
        sa.Column("traffic_row_id", sa.Integer(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("desired_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("applied_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("applied_total_bytes", sa.BigInteger(), nullable=True),
        sa.Column("applied_enable", sa.Boolean(), nullable=True),
        sa.Column("applied_expiry_ms", sa.BigInteger(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("conflict", sa.Text(), nullable=True),
        sa.Column(
            "admin_blocked", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_whitelist_accounts_user_id"),
    )

    op.create_table(
        "whitelist_ledger",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("source_key", sa.String(64), nullable=True, unique=True),
        sa.Column(
            "payment_request_id",
            sa.Integer(),
            sa.ForeignKey("payment_requests.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("free_before", sa.BigInteger(), nullable=False),
        sa.Column("free_after", sa.BigInteger(), nullable=False),
        sa.Column("paid_before", sa.BigInteger(), nullable=False),
        sa.Column("paid_after", sa.BigInteger(), nullable=False),
        sa.Column(
            "actor_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_whitelist_ledger_user_id", "whitelist_ledger", ["user_id"])

    now = sa.func.now()
    config = sa.table(
        "whitelist_config",
        sa.column("id", sa.Integer()),
        sa.column("service_enabled", sa.Boolean()),
        sa.column("paid_free_bytes", sa.BigInteger()),
        sa.column("trial_free_bytes", sa.BigInteger()),
    )
    op.bulk_insert(
        config,
        [
            {
                "id": 1,
                "service_enabled": False,
                "paid_free_bytes": 10 * GIB,
                "trial_free_bytes": 3 * GIB,
            }
        ],
    )
    packages = sa.table(
        "traffic_packages",
        sa.column("traffic_bytes", sa.BigInteger()),
        sa.column("price", sa.Numeric(10, 2)),
        sa.column("enabled", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    op.execute(
        packages.insert().values(
            [
                {"traffic_bytes": 10 * GIB, "price": 49, "enabled": True,
                 "sort_order": 1, "created_at": now},
                {"traffic_bytes": 25 * GIB, "price": 99, "enabled": True,
                 "sort_order": 2, "created_at": now},
                {"traffic_bytes": 50 * GIB, "price": 199, "enabled": True,
                 "sort_order": 3, "created_at": now},
            ]
        )
    )


def downgrade() -> None:
    op.drop_index("ix_whitelist_ledger_user_id", table_name="whitelist_ledger")
    op.drop_table("whitelist_ledger")
    op.drop_table("whitelist_accounts")
    op.drop_table("whitelist_config")
    with op.batch_alter_table("payment_requests") as batch:
        batch.drop_constraint("fk_payment_requests_traffic_package_id", type_="foreignkey")
        batch.drop_column("traffic_package_title")
        batch.drop_column("traffic_package_id")
        batch.drop_column("traffic_bytes")
        batch.drop_column("kind")
    op.drop_table("traffic_packages")
    op.drop_index("uq_servers_single_enabled_whitelist", table_name="servers")
    with op.batch_alter_table("servers") as batch:
        batch.drop_column("inventory_synced_at")
        batch.drop_column("inventory_error")
        batch.drop_column("inventory_status")
        batch.drop_column("purpose")

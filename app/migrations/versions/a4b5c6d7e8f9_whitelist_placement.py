"""Учёт whitelist: подтверждённое размещение клиента и привязки, созданные услугой.

Смена целевого inbound (или его flow) должна переносить уже синхронизированных
клиентов: прикрепить к новой цели, применить её параметры, снять прежние привязки
услуги и подтвердить результат чтением. Для восстановления после рестарта и
частичного применения сохраняются:

* ``whitelist_accounts.placement_*`` — подтверждённое размещение (сервер, inbound,
  flow); NULL — не подтверждалось, очередь проверит размещение заново;
* ``whitelist_placements`` — привязки, созданные услугой (``attaching`` до запроса,
  ``attached`` после подтверждения, ``detaching`` при снятии).

Существующие учёты получают NULL и ни одной строки привязки: прежние привязки
неизвестного происхождения не объявляются привязками услуги и автоматически не
снимаются (признать их может администратор командой ``/wlclaim``).

Revision ID: a4b5c6d7e8f9
Revises: f3a4b5c6d7e8
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "a4b5c6d7e8f9"
down_revision: str | None = "f3a4b5c6d7e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("whitelist_accounts") as batch:
        batch.add_column(sa.Column("placement_server_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("placement_inbound_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("placement_flow", sa.String(32), nullable=True))
        batch.add_column(
            sa.Column("placement_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch.create_foreign_key(
            "fk_whitelist_accounts_placement_server_id",
            "servers",
            ["placement_server_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_table(
        "whitelist_placements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "server_id",
            sa.Integer(),
            sa.ForeignKey("servers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("inbound_id", sa.Integer(), nullable=False),
        sa.Column("panel_email", sa.String(255), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("origin", sa.String(16), nullable=False, server_default="service"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "user_id", "server_id", "inbound_id", name="uq_whitelist_placements_target"
        ),
    )
    op.create_index(
        "ix_whitelist_placements_user_id", "whitelist_placements", ["user_id"]
    )


def downgrade() -> None:
    # Незавершённый перенос теряет сведения о привязках услуги: перед откатом
    # дождитесь «перенос: ожидает 0, ошибок 0» (docs/WHITELIST_SERVICE.md, «Откат»).
    op.drop_index("ix_whitelist_placements_user_id", table_name="whitelist_placements")
    op.drop_table("whitelist_placements")
    with op.batch_alter_table("whitelist_accounts") as batch:
        batch.drop_constraint(
            "fk_whitelist_accounts_placement_server_id", type_="foreignkey"
        )
        batch.drop_column("placement_at")
        batch.drop_column("placement_flow")
        batch.drop_column("placement_inbound_id")
        batch.drop_column("placement_server_id")

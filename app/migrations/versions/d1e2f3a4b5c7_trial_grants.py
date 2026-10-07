"""trial_grants: одноразовость пробного периода по Telegram ID

``users.trial_used`` пропадал при сбросе бота вместе с ``User``: новая запись для
того же Telegram ID снова получала trial. Факт выдачи теперь хранится в
``trial_grants`` по Telegram ID, независимо от жизненного цикла ``User``.

Перенос существующих фактов:

* ``users.trial_used`` у пользователей с Telegram ID;
* trial, выданные уже удалённым сбросом пользователям: запись аудита
  ``billing.trial_granted`` (``actor_user_id`` — получатель) сопоставляется с
  ближайшей последующей записью ``user.self_reset``/``user.reset_bot_state`` того
  же пользователя, где сохранён Telegram ID. Если ``actor_user_id`` уже обнулён
  внешним ключом ``ON DELETE SET NULL`` (PostgreSQL), получателя установить
  нельзя, и такой trial не переносится.

Downgrade удаляет таблицу; факты trial у сброшенных пользователей теряются.

Revision ID: d1e2f3a4b5c7
Revises: a4b5c6d7e8f9
"""
from __future__ import annotations

import json
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "d1e2f3a4b5c7"
down_revision: str | None = "a4b5c6d7e8f9"
branch_labels = None
depends_on = None

_RESET_ACTIONS = ("user.self_reset", "user.reset_bot_state")


def upgrade() -> None:
    grants_table = op.create_table(
        "trial_grants",
        sa.Column("telegram_id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    bind = op.get_bind()
    users = sa.table(
        "users",
        sa.column("id", sa.Integer()),
        sa.column("telegram_id", sa.BigInteger()),
        sa.column("trial_used", sa.Boolean()),
    )
    audit = sa.table(
        "audit_logs",
        sa.column("actor_user_id", sa.Integer()),
        sa.column("action", sa.String()),
        sa.column("entity_id", sa.Integer()),
        sa.column("payload", sa.Text()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )

    trials = bind.execute(
        sa.select(audit.c.actor_user_id, audit.c.created_at)
        .where(
            audit.c.action == "billing.trial_granted",
            audit.c.actor_user_id.is_not(None),
        )
        .order_by(audit.c.created_at)
    ).all()

    # Сбросы: прежний user_id → (момент, Telegram ID).
    resets: dict[int, list[tuple[datetime, int]]] = {}
    for user_id, payload, at in bind.execute(
        sa.select(audit.c.entity_id, audit.c.payload, audit.c.created_at)
        .where(audit.c.action.in_(_RESET_ACTIONS), audit.c.entity_id.is_not(None))
        .order_by(audit.c.created_at)
    ):
        try:
            telegram_id = int(json.loads(payload or "{}")["telegram_id"])
        except (ValueError, TypeError, KeyError):
            continue
        resets.setdefault(user_id, []).append((at, telegram_id))

    grants: dict[int, tuple[int | None, datetime]] = {}
    current: dict[int, datetime] = {}  # выдачи живым пользователям: user_id → момент
    # Без AUTOINCREMENT SQLite может повторно выдать id удалённого пользователя:
    # trial относится к первому сбросу этого id после выдачи.
    for actor, at in trials:
        telegram_id = next((tg for when, tg in resets.get(actor, ()) if when >= at), None)
        if telegram_id is None:
            current.setdefault(actor, at)
        elif telegram_id not in grants:
            grants[telegram_id] = (actor, at)

    now = datetime.now(UTC)
    for user_id, telegram_id in bind.execute(
        sa.select(users.c.id, users.c.telegram_id).where(
            users.c.trial_used == sa.true(), users.c.telegram_id.is_not(None)
        )
    ):
        if telegram_id not in grants:
            grants[telegram_id] = (user_id, current.get(user_id, now))

    if grants:
        op.bulk_insert(
            grants_table,
            [
                {"telegram_id": tg, "user_id": user_id, "granted_at": at}
                for tg, (user_id, at) in sorted(grants.items())
            ],
        )


def downgrade() -> None:
    op.drop_table("trial_grants")

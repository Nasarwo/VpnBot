"""subscription_purchases: оплата подписки закрывает trial по Telegram ID

Правило «trial только до первой подписки» проверяло заявки пользователя, а сброс
бота удаляет ``User`` вместе с заявками: новый ``User`` того же Telegram ID снова
получал trial. Факт первой применённой оплаты подписки теперь хранится по
Telegram ID, независимо от жизненного цикла ``User`` (как ``trial_grants``).

Перенос существующих фактов — только из сохранившихся заявок: ``kind =
subscription``, статус ``applied``, у пользователя есть Telegram ID. Для каждого
Telegram ID берётся самая ранняя такая заявка (``applied_at``, при его отсутствии
``confirmed_at``/``created_at``).

Не переносятся:

* заявки ``confirmed`` — ещё не применены и могут стать ``failed``/``rejected``;
  до применения trial закрывает сама заявка (сброс при ней запрещён);
* оплаты, удалённые сбросом до миграции. Аудит ``billing.applied`` хранит id
  заявки и администратора, но не получателя; id заявок и пользователей SQLite
  может выдать повторно, а на PostgreSQL ``actor_user_id`` удалённого
  пользователя обнулён. Принадлежность таких оплат не восстанавливается.

Downgrade удаляет таблицу; факты оплат у сброшенных пользователей теряются.

Revision ID: e3f4a5b6c7d8
Revises: d1e2f3a4b5c7
"""
from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision: str = "e3f4a5b6c7d8"
down_revision: str | None = "d1e2f3a4b5c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    purchases_table = op.create_table(
        "subscription_purchases",
        sa.Column("telegram_id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("payment_request_id", sa.Integer(), nullable=True),
        sa.Column(
            "paid_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    users = sa.table(
        "users",
        sa.column("id", sa.Integer()),
        sa.column("telegram_id", sa.BigInteger()),
    )
    payments = sa.table(
        "payment_requests",
        sa.column("id", sa.Integer()),
        sa.column("user_id", sa.Integer()),
        sa.column("kind", sa.String()),
        sa.column("status", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("confirmed_at", sa.DateTime(timezone=True)),
        sa.column("applied_at", sa.DateTime(timezone=True)),
    )
    paid_at = sa.func.coalesce(
        payments.c.applied_at,
        payments.c.confirmed_at,
        payments.c.created_at,
        type_=sa.DateTime(timezone=True),
    )
    rows = op.get_bind().execute(
        sa.select(users.c.telegram_id, users.c.id, payments.c.id, paid_at)
        .join(payments, payments.c.user_id == users.c.id)
        .where(
            users.c.telegram_id.is_not(None),
            payments.c.kind == "subscription",
            # Enum(native_enum=False) хранит имя члена перечисления.
            payments.c.status == "APPLIED",
        )
        .order_by(paid_at, payments.c.id)
    ).all()

    purchases: dict[int, tuple[int, int, datetime]] = {}
    for telegram_id, user_id, payment_id, at in rows:
        purchases.setdefault(telegram_id, (user_id, payment_id, at))
    if purchases:
        op.bulk_insert(
            purchases_table,
            [
                {
                    "telegram_id": tg,
                    "user_id": user_id,
                    "payment_request_id": payment_id,
                    "paid_at": at,
                }
                for tg, (user_id, payment_id, at) in sorted(purchases.items())
            ],
        )


def downgrade() -> None:
    op.drop_table("subscription_purchases")

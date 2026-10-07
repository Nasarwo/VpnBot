"""Align servers.password with encrypted password storage in the ORM.

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8

Existing revisions remain unchanged, including those already applied from GitHub.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "f4a5b6c7d8e9"
down_revision = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("servers") as batch:
        batch.alter_column(
            "password",
            existing_type=sa.String(512),
            type_=sa.String(1024),
            existing_nullable=False,
        )


def downgrade() -> None:
    # PostgreSQL would reject these values; SQLite would silently retain them in
    # a VARCHAR(512). Give both backends the same safe, explicit refusal.
    too_long = op.get_bind().execute(
        sa.text("SELECT id FROM servers WHERE length(password) > 512 LIMIT 1")
    ).first()
    if too_long is not None:
        raise RuntimeError("Server passwords exceed 512 characters; downgrade is unsafe")
    with op.batch_alter_table("servers") as batch:
        batch.alter_column(
            "password",
            existing_type=sa.String(1024),
            type_=sa.String(512),
            existing_nullable=False,
        )

"""add news event ranking reasons

Revision ID: 202606140004
Revises: 202606140003
Create Date: 2026-06-14 00:04:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202606140004"
down_revision: str | None = "202606140003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("news_events", sa.Column("reasons", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("news_events", "reasons")

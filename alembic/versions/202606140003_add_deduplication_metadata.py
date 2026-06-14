"""add deduplication metadata

Revision ID: 202606140003
Revises: 202606140002
Create Date: 2026-06-14 00:03:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202606140003"
down_revision: str | None = "202606140002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("news_events", sa.Column("metadata", sa.JSON(), nullable=True))
    op.add_column("source_links", sa.Column("reasons", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("source_links", "reasons")
    op.drop_column("news_events", "metadata")

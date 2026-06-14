"""add raw item metadata

Revision ID: 202606140002
Revises: 202606140001
Create Date: 2026-06-14 00:02:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202606140002"
down_revision: str | None = "202606140001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("raw_items", sa.Column("raw_metadata", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("raw_items", "raw_metadata")

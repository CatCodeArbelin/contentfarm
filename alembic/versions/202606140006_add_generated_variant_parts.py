"""Add structured generated variant fields.

Revision ID: 202606140006
Revises: 202606140005
Create Date: 2026-06-14 00:06:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202606140006"
down_revision: str | Sequence[str] | None = "202606140005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("generated_variants", sa.Column("title", sa.String(length=500), nullable=True))
    op.add_column("generated_variants", sa.Column("lead", sa.Text(), nullable=True))
    op.add_column("generated_variants", sa.Column("body", sa.Text(), nullable=True))
    op.add_column("generated_variants", sa.Column("sources", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("generated_variants", "sources")
    op.drop_column("generated_variants", "body")
    op.drop_column("generated_variants", "lead")
    op.drop_column("generated_variants", "title")

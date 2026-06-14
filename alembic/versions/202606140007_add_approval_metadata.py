"""Add approval metadata to variants and publications.

Revision ID: 202606140007
Revises: 202606140006
Create Date: 2026-06-14 00:07:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202606140007"
down_revision: str | None = "202606140006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("generated_variants", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("generated_variants", sa.Column("approved_by", sa.String(length=200), nullable=True))
    op.add_column("publications", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("publications", sa.Column("approved_by", sa.String(length=200), nullable=True))


def downgrade() -> None:
    op.drop_column("publications", "approved_by")
    op.drop_column("publications", "approved_at")
    op.drop_column("generated_variants", "approved_by")
    op.drop_column("generated_variants", "approved_at")

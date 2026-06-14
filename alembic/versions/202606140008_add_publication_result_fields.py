"""Add publication result fields.

Revision ID: 202606140008
Revises: 202606140007
Create Date: 2026-06-14 00:08:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202606140008"
down_revision: str | None = "202606140007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("publications", sa.Column("message_id", sa.String(length=128), nullable=True))
    op.add_column("publications", sa.Column("export_path", sa.String(length=2048), nullable=True))
    op.add_column("publications", sa.Column("error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("publications", "error")
    op.drop_column("publications", "export_path")
    op.drop_column("publications", "message_id")

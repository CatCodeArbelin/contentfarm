"""Add moderation audits.

Revision ID: 202606140009
Revises: 202606140008
Create Date: 2026-06-14 00:09:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202606140009"
down_revision: str | None = "202606140008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "moderation_audits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("variant_id", sa.Integer(), nullable=False),
        sa.Column("reviewer", sa.String(length=200), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("url_hash", sa.String(length=64), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("topic", sa.String(length=128), nullable=True),
        sa.Column("platform", sa.String(length=64), nullable=True),
        sa.Column("strategy", sa.String(length=128), nullable=True),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["variant_id"], ["generated_variants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("id", "status", "created_at", "url_hash", "language", "topic", "platform", "strategy", "risk_level", "variant_id"):
        op.create_index(op.f(f"ix_moderation_audits_{column}"), "moderation_audits", [column], unique=False)
    op.create_index("ix_moderation_audits_variant_status", "moderation_audits", ["variant_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_table("moderation_audits")

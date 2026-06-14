"""add prompt versions

Revision ID: 202606140005
Revises: 202606140004
Create Date: 2026-06-14 00:05:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202606140005"
down_revision: str | None = "202606140004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("prompts", sa.Column("prompt_type", sa.String(length=64), nullable=False, server_default="global_humanizer"))
    op.add_column("prompts", sa.Column("version", sa.String(length=64), nullable=False, server_default="1.0.0"))
    op.add_column("prompts", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("generated_variants", sa.Column("prompt_version", sa.String(length=64), nullable=True))

    op.drop_constraint("uq_prompts_name_platform_strategy", "prompts", type_="unique")
    op.create_unique_constraint(
        "uq_prompts_name_type_version_platform_strategy",
        "prompts",
        ["name", "prompt_type", "version", "platform", "strategy"],
    )
    op.create_index(op.f("ix_prompts_prompt_type"), "prompts", ["prompt_type"], unique=False)
    op.create_index(op.f("ix_prompts_version"), "prompts", ["version"], unique=False)
    op.create_index(op.f("ix_prompts_is_active"), "prompts", ["is_active"], unique=False)
    op.create_index("ix_prompts_active_lookup", "prompts", ["prompt_type", "platform", "strategy", "is_active"], unique=False)
    op.create_index(op.f("ix_generated_variants_prompt_version"), "generated_variants", ["prompt_version"], unique=False)

    op.alter_column("prompts", "prompt_type", server_default=None)
    op.alter_column("prompts", "version", server_default=None)
    op.alter_column("prompts", "is_active", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_generated_variants_prompt_version"), table_name="generated_variants")
    op.drop_index("ix_prompts_active_lookup", table_name="prompts")
    op.drop_index(op.f("ix_prompts_is_active"), table_name="prompts")
    op.drop_index(op.f("ix_prompts_version"), table_name="prompts")
    op.drop_index(op.f("ix_prompts_prompt_type"), table_name="prompts")
    op.drop_constraint("uq_prompts_name_type_version_platform_strategy", "prompts", type_="unique")
    op.create_unique_constraint("uq_prompts_name_platform_strategy", "prompts", ["name", "platform", "strategy"])

    op.drop_column("generated_variants", "prompt_version")
    op.drop_column("prompts", "is_active")
    op.drop_column("prompts", "version")
    op.drop_column("prompts", "prompt_type")

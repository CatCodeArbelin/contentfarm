"""add prompt versions

Revision ID: 202606140005
Revises: 202606140004
Create Date: 2026-06-14 00:05:00.000000
"""

from collections.abc import Sequence

import sqlalchemy
import sqlalchemy as sa
from alembic import op

revision: str = "202606140005"
down_revision: str | None = "202606140004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def has_column(table_name: str, column_name: str) -> bool:
    inspector = sqlalchemy.inspect(op.get_bind())
    return any(
        column["name"] == column_name for column in inspector.get_columns(table_name)
    )


def has_index(table_name: str, index_name: str) -> bool:
    inspector = sqlalchemy.inspect(op.get_bind())
    return any(
        index["name"] == index_name for index in inspector.get_indexes(table_name)
    )


def has_unique_constraint(table_name: str, constraint_name: str) -> bool:
    inspector = sqlalchemy.inspect(op.get_bind())
    return any(
        constraint["name"] == constraint_name
        for constraint in inspector.get_unique_constraints(table_name)
    )


def upgrade() -> None:
    if not has_column("prompts", "prompt_type"):
        op.add_column(
            "prompts",
            sa.Column(
                "prompt_type",
                sa.String(length=64),
                nullable=False,
                server_default="global_humanizer",
            ),
        )
    if not has_column("prompts", "version"):
        op.add_column(
            "prompts",
            sa.Column(
                "version",
                sa.String(length=64),
                nullable=False,
                server_default="1.0.0",
            ),
        )
    if not has_column("prompts", "is_active"):
        op.add_column(
            "prompts",
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            ),
        )
    if not has_column("generated_variants", "prompt_version"):
        op.add_column(
            "generated_variants",
            sa.Column("prompt_version", sa.String(length=64), nullable=True),
        )

    if has_unique_constraint("prompts", "uq_prompts_name_platform_strategy"):
        op.drop_constraint(
            "uq_prompts_name_platform_strategy", "prompts", type_="unique"
        )
    if not has_unique_constraint(
        "prompts", "uq_prompts_name_type_version_platform_strategy"
    ):
        op.create_unique_constraint(
            "uq_prompts_name_type_version_platform_strategy",
            "prompts",
            ["name", "prompt_type", "version", "platform", "strategy"],
        )
    if not has_index("prompts", "ix_prompts_prompt_type"):
        op.create_index(
            op.f("ix_prompts_prompt_type"),
            "prompts",
            ["prompt_type"],
            unique=False,
        )
    if not has_index("prompts", "ix_prompts_version"):
        op.create_index(
            op.f("ix_prompts_version"),
            "prompts",
            ["version"],
            unique=False,
        )
    if not has_index("prompts", "ix_prompts_is_active"):
        op.create_index(
            op.f("ix_prompts_is_active"),
            "prompts",
            ["is_active"],
            unique=False,
        )
    if not has_index("prompts", "ix_prompts_active_lookup"):
        op.create_index(
            "ix_prompts_active_lookup",
            "prompts",
            ["prompt_type", "platform", "strategy", "is_active"],
            unique=False,
        )
    if not has_index("generated_variants", "ix_generated_variants_prompt_version"):
        op.create_index(
            op.f("ix_generated_variants_prompt_version"),
            "generated_variants",
            ["prompt_version"],
            unique=False,
        )

    if has_column("prompts", "prompt_type"):
        op.alter_column("prompts", "prompt_type", server_default=None)
    if has_column("prompts", "version"):
        op.alter_column("prompts", "version", server_default=None)
    if has_column("prompts", "is_active"):
        op.alter_column("prompts", "is_active", server_default=None)


def downgrade() -> None:
    if has_index("generated_variants", "ix_generated_variants_prompt_version"):
        op.drop_index(
            op.f("ix_generated_variants_prompt_version"),
            table_name="generated_variants",
        )
    if has_index("prompts", "ix_prompts_active_lookup"):
        op.drop_index("ix_prompts_active_lookup", table_name="prompts")
    if has_index("prompts", "ix_prompts_is_active"):
        op.drop_index(op.f("ix_prompts_is_active"), table_name="prompts")
    if has_index("prompts", "ix_prompts_version"):
        op.drop_index(op.f("ix_prompts_version"), table_name="prompts")
    if has_index("prompts", "ix_prompts_prompt_type"):
        op.drop_index(op.f("ix_prompts_prompt_type"), table_name="prompts")
    if has_unique_constraint(
        "prompts", "uq_prompts_name_type_version_platform_strategy"
    ):
        op.drop_constraint(
            "uq_prompts_name_type_version_platform_strategy",
            "prompts",
            type_="unique",
        )
    if not has_unique_constraint("prompts", "uq_prompts_name_platform_strategy"):
        op.create_unique_constraint(
            "uq_prompts_name_platform_strategy",
            "prompts",
            ["name", "platform", "strategy"],
        )

    if has_column("generated_variants", "prompt_version"):
        op.drop_column("generated_variants", "prompt_version")
    if has_column("prompts", "is_active"):
        op.drop_column("prompts", "is_active")
    if has_column("prompts", "version"):
        op.drop_column("prompts", "version")
    if has_column("prompts", "prompt_type"):
        op.drop_column("prompts", "prompt_type")

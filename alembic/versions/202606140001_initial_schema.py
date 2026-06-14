"""Initial contentfarm schema.

Revision ID: 202606140001
Revises:
Create Date: 2026-06-14 00:01:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202606140001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def common_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    ]


def domain_columns(*, source_url_nullable: bool = True, language_nullable: bool = True, topic_nullable: bool = True, platform_nullable: bool = True, strategy_nullable: bool = True) -> list[sa.Column]:
    return [
        sa.Column("source_url", sa.String(length=2048), nullable=source_url_nullable),
        sa.Column("url_hash", sa.String(length=64), nullable=source_url_nullable),
        sa.Column("language", sa.String(length=16), nullable=language_nullable),
        sa.Column("topic", sa.String(length=128), nullable=topic_nullable),
        sa.Column("platform", sa.String(length=64), nullable=platform_nullable),
        sa.Column("strategy", sa.String(length=128), nullable=strategy_nullable),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
    ]


def add_common_indexes(table_name: str) -> None:
    for column in ("id", "status", "created_at", "url_hash", "language", "topic", "platform", "strategy", "risk_level"):
        op.create_index(op.f(f"ix_{table_name}_{column}"), table_name, [column], unique=False)


def upgrade() -> None:
    op.create_table(
        "sources",
        *common_columns(),
        sa.Column("name", sa.String(length=200), nullable=False),
        *domain_columns(source_url_nullable=False, language_nullable=False, platform_nullable=False),
        sa.UniqueConstraint("url_hash", name="uq_sources_url_hash"),
    )
    add_common_indexes("sources")
    op.create_index("ix_sources_platform_topic", "sources", ["platform", "topic"], unique=False)

    op.create_table(
        "raw_items",
        *common_columns(),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        *domain_columns(source_url_nullable=False, language_nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("url_hash", name="uq_raw_items_url_hash"),
    )
    add_common_indexes("raw_items")
    op.create_index(op.f("ix_raw_items_source_id"), "raw_items", ["source_id"], unique=False)
    op.create_index("ix_raw_items_source_status", "raw_items", ["source_id", "status"], unique=False)

    op.create_table("news_events", *common_columns(), sa.Column("title", sa.String(length=500), nullable=False), sa.Column("summary", sa.Text(), nullable=False), *domain_columns(language_nullable=False))
    add_common_indexes("news_events")
    op.create_index("ix_news_events_topic_score", "news_events", ["topic", "score"], unique=False)

    op.create_table("topics", *common_columns(), sa.Column("name", sa.String(length=128), nullable=False), sa.Column("slug", sa.String(length=128), nullable=False), *domain_columns(language_nullable=False, topic_nullable=False), sa.UniqueConstraint("slug", name="uq_topics_slug"))
    add_common_indexes("topics")

    op.create_table("strategies", *common_columns(), sa.Column("name", sa.String(length=128), nullable=False), sa.Column("description", sa.Text(), nullable=True), *domain_columns(strategy_nullable=False), sa.UniqueConstraint("name", name="uq_strategies_name"))
    add_common_indexes("strategies")

    op.create_table("platforms", *common_columns(), sa.Column("name", sa.String(length=64), nullable=False), *domain_columns(platform_nullable=False), sa.UniqueConstraint("name", name="uq_platforms_name"))
    add_common_indexes("platforms")

    op.create_table("prompts", *common_columns(), sa.Column("name", sa.String(length=128), nullable=False), sa.Column("prompt_type", sa.String(length=64), nullable=False), sa.Column("version", sa.String(length=64), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("template", sa.Text(), nullable=False), *domain_columns(language_nullable=False, platform_nullable=False, strategy_nullable=False), sa.UniqueConstraint("name", "prompt_type", "version", "platform", "strategy", name="uq_prompts_name_type_version_platform_strategy"))
    add_common_indexes("prompts")
    op.create_index(op.f("ix_prompts_prompt_type"), "prompts", ["prompt_type"], unique=False)
    op.create_index(op.f("ix_prompts_version"), "prompts", ["version"], unique=False)
    op.create_index(op.f("ix_prompts_is_active"), "prompts", ["is_active"], unique=False)
    op.create_index("ix_prompts_active_lookup", "prompts", ["prompt_type", "platform", "strategy", "is_active"], unique=False)

    op.create_table("source_links", *common_columns(), sa.Column("news_event_id", sa.Integer(), nullable=False), sa.Column("raw_item_id", sa.Integer(), nullable=False), *domain_columns(), sa.ForeignKeyConstraint(["news_event_id"], ["news_events.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["raw_item_id"], ["raw_items.id"], ondelete="CASCADE"), sa.UniqueConstraint("news_event_id", "raw_item_id", name="uq_source_links_event_raw_item"))
    add_common_indexes("source_links")
    op.create_index(op.f("ix_source_links_news_event_id"), "source_links", ["news_event_id"], unique=False)
    op.create_index(op.f("ix_source_links_raw_item_id"), "source_links", ["raw_item_id"], unique=False)

    op.create_table("generated_variants", *common_columns(), sa.Column("news_event_id", sa.Integer(), nullable=False), sa.Column("prompt_id", sa.Integer(), nullable=True), sa.Column("prompt_version", sa.String(length=64), nullable=True), sa.Column("content", sa.Text(), nullable=False), *domain_columns(language_nullable=False, platform_nullable=False, strategy_nullable=False), sa.ForeignKeyConstraint(["news_event_id"], ["news_events.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["prompt_id"], ["prompts.id"], ondelete="SET NULL"))
    add_common_indexes("generated_variants")
    op.create_index(op.f("ix_generated_variants_news_event_id"), "generated_variants", ["news_event_id"], unique=False)
    op.create_index(op.f("ix_generated_variants_prompt_id"), "generated_variants", ["prompt_id"], unique=False)
    op.create_index(op.f("ix_generated_variants_prompt_version"), "generated_variants", ["prompt_version"], unique=False)
    op.create_index("ix_generated_variants_event_status", "generated_variants", ["news_event_id", "status"], unique=False)

    op.create_table("publications", *common_columns(), sa.Column("variant_id", sa.Integer(), nullable=False), sa.Column("publication_url", sa.String(length=2048), nullable=True), *domain_columns(platform_nullable=False, strategy_nullable=False), sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True), sa.Column("published_at", sa.DateTime(timezone=True), nullable=True), sa.ForeignKeyConstraint(["variant_id"], ["generated_variants.id"], ondelete="CASCADE"))
    add_common_indexes("publications")
    op.create_index(op.f("ix_publications_variant_id"), "publications", ["variant_id"], unique=False)
    op.create_index("ix_publications_platform_status", "publications", ["platform", "status"], unique=False)

    op.create_table("metrics", *common_columns(), sa.Column("publication_id", sa.Integer(), nullable=False), sa.Column("name", sa.String(length=128), nullable=False), sa.Column("value", sa.Float(), nullable=False), *domain_columns(platform_nullable=False), sa.ForeignKeyConstraint(["publication_id"], ["publications.id"], ondelete="CASCADE"), sa.UniqueConstraint("publication_id", "name", "created_at", name="uq_metrics_publication_name_created"))
    add_common_indexes("metrics")
    op.create_index(op.f("ix_metrics_publication_id"), "metrics", ["publication_id"], unique=False)
    op.create_index(op.f("ix_metrics_name"), "metrics", ["name"], unique=False)

    op.create_table("jobs", *common_columns(), sa.Column("job_type", sa.String(length=128), nullable=False), sa.Column("payload", sa.JSON(), nullable=True), *domain_columns(), sa.Column("run_at", sa.DateTime(timezone=True), nullable=True), sa.Column("attempts", sa.Integer(), nullable=False))
    add_common_indexes("jobs")
    op.create_index(op.f("ix_jobs_run_at"), "jobs", ["run_at"], unique=False)
    op.create_index("ix_jobs_type_status", "jobs", ["job_type", "status"], unique=False)

    op.create_table("error_logs", *common_columns(), sa.Column("entity_type", sa.String(length=128), nullable=True), sa.Column("entity_id", sa.Integer(), nullable=True), sa.Column("message", sa.Text(), nullable=False), sa.Column("traceback", sa.Text(), nullable=True), *domain_columns())
    add_common_indexes("error_logs")
    op.create_index(op.f("ix_error_logs_entity_type"), "error_logs", ["entity_type"], unique=False)
    op.create_index(op.f("ix_error_logs_entity_id"), "error_logs", ["entity_id"], unique=False)
    op.create_index("ix_error_logs_entity", "error_logs", ["entity_type", "entity_id"], unique=False)


def downgrade() -> None:
    for table_name in ("error_logs", "jobs", "metrics", "publications", "generated_variants", "source_links", "prompts", "platforms", "strategies", "topics", "news_events", "raw_items", "sources"):
        op.drop_table(table_name)

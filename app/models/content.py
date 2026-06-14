from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampStatusMixin


class Source(TimestampStatusMixin, Base):
    __tablename__ = "sources"
    __table_args__ = (UniqueConstraint("url_hash", name="uq_sources_url_hash"), Index("ix_sources_platform_topic", "platform", "topic"))

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en", index=True)
    topic: Mapped[str | None] = mapped_column(String(128), index=True)
    platform: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    strategy: Mapped[str | None] = mapped_column(String(128), index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="low", index=True)

    raw_items: Mapped[list["RawItem"]] = relationship(back_populates="source")


class RawItem(TimestampStatusMixin, Base):
    __tablename__ = "raw_items"
    __table_args__ = (UniqueConstraint("url_hash", name="uq_raw_items_url_hash"), Index("ix_raw_items_source_status", "source_id", "status"))

    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en", index=True)
    topic: Mapped[str | None] = mapped_column(String(128), index=True)
    platform: Mapped[str | None] = mapped_column(String(64), index=True)
    strategy: Mapped[str | None] = mapped_column(String(128), index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="low", index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    source: Mapped[Source | None] = relationship(back_populates="raw_items")
    event_links: Mapped[list["SourceLink"]] = relationship(back_populates="raw_item")


class NewsEvent(TimestampStatusMixin, Base):
    __tablename__ = "news_events"
    __table_args__ = (Index("ix_news_events_topic_score", "topic", "score"),)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    url_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en", index=True)
    topic: Mapped[str | None] = mapped_column(String(128), index=True)
    platform: Mapped[str | None] = mapped_column(String(64), index=True)
    strategy: Mapped[str | None] = mapped_column(String(128), index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="low", index=True)
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    reasons: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)

    source_links: Mapped[list["SourceLink"]] = relationship(back_populates="news_event")
    variants: Mapped[list["GeneratedVariant"]] = relationship(back_populates="news_event")


class SourceLink(TimestampStatusMixin, Base):
    __tablename__ = "source_links"
    __table_args__ = (UniqueConstraint("news_event_id", "raw_item_id", name="uq_source_links_event_raw_item"),)

    news_event_id: Mapped[int] = mapped_column(ForeignKey("news_events.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_item_id: Mapped[int] = mapped_column(ForeignKey("raw_items.id", ondelete="CASCADE"), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    url_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    language: Mapped[str | None] = mapped_column(String(16), index=True)
    topic: Mapped[str | None] = mapped_column(String(128), index=True)
    platform: Mapped[str | None] = mapped_column(String(64), index=True)
    strategy: Mapped[str | None] = mapped_column(String(128), index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="low", index=True)
    reasons: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)

    news_event: Mapped[NewsEvent] = relationship(back_populates="source_links")
    raw_item: Mapped[RawItem] = relationship(back_populates="event_links")


class Topic(TimestampStatusMixin, Base):
    __tablename__ = "topics"
    __table_args__ = (UniqueConstraint("slug", name="uq_topics_slug"),)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    url_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en", index=True)
    topic: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    platform: Mapped[str | None] = mapped_column(String(64), index=True)
    strategy: Mapped[str | None] = mapped_column(String(128), index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="low", index=True)


class Strategy(TimestampStatusMixin, Base):
    __tablename__ = "strategies"
    __table_args__ = (UniqueConstraint("name", name="uq_strategies_name"),)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    url_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    language: Mapped[str | None] = mapped_column(String(16), index=True)
    topic: Mapped[str | None] = mapped_column(String(128), index=True)
    platform: Mapped[str | None] = mapped_column(String(64), index=True)
    strategy: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="low", index=True)


class Platform(TimestampStatusMixin, Base):
    __tablename__ = "platforms"
    __table_args__ = (UniqueConstraint("name", name="uq_platforms_name"),)

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    url_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    language: Mapped[str | None] = mapped_column(String(16), index=True)
    topic: Mapped[str | None] = mapped_column(String(128), index=True)
    platform: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    strategy: Mapped[str | None] = mapped_column(String(128), index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="low", index=True)


class Prompt(TimestampStatusMixin, Base):
    __tablename__ = "prompts"
    __table_args__ = (
        UniqueConstraint("name", "prompt_type", "version", "platform", "strategy", name="uq_prompts_name_type_version_platform_strategy"),
        Index("ix_prompts_active_lookup", "prompt_type", "platform", "strategy", "is_active"),
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_type: Mapped[str] = mapped_column(String(64), nullable=False, default="global_humanizer", index=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False, default="1.0.0", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    url_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en", index=True)
    topic: Mapped[str | None] = mapped_column(String(128), index=True)
    platform: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    strategy: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="low", index=True)

    variants: Mapped[list["GeneratedVariant"]] = relationship(back_populates="prompt")


class GeneratedVariant(TimestampStatusMixin, Base):
    __tablename__ = "generated_variants"
    __table_args__ = (Index("ix_generated_variants_event_status", "news_event_id", "status"),)

    news_event_id: Mapped[int] = mapped_column(ForeignKey("news_events.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt_id: Mapped[int | None] = mapped_column(ForeignKey("prompts.id", ondelete="SET NULL"), index=True)
    prompt_version: Mapped[str | None] = mapped_column(String(64), index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    lead: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    sources: Mapped[list[str] | None] = mapped_column(JSON)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    url_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en", index=True)
    topic: Mapped[str | None] = mapped_column(String(128), index=True)
    platform: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    strategy: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="low", index=True)

    news_event: Mapped[NewsEvent] = relationship(back_populates="variants")
    prompt: Mapped[Prompt | None] = relationship(back_populates="variants")
    publications: Mapped[list["Publication"]] = relationship(back_populates="variant")


class Publication(TimestampStatusMixin, Base):
    __tablename__ = "publications"
    __table_args__ = (Index("ix_publications_platform_status", "platform", "status"),)

    variant_id: Mapped[int] = mapped_column(ForeignKey("generated_variants.id", ondelete="CASCADE"), nullable=False, index=True)
    publication_url: Mapped[str | None] = mapped_column(String(2048))
    source_url: Mapped[str | None] = mapped_column(String(2048))
    url_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    language: Mapped[str | None] = mapped_column(String(16), index=True)
    topic: Mapped[str | None] = mapped_column(String(128), index=True)
    platform: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    strategy: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="low", index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    variant: Mapped[GeneratedVariant] = relationship(back_populates="publications")
    metrics: Mapped[list["Metric"]] = relationship(back_populates="publication")


class Metric(TimestampStatusMixin, Base):
    __tablename__ = "metrics"
    __table_args__ = (UniqueConstraint("publication_id", "name", "created_at", name="uq_metrics_publication_name_created"),)

    publication_id: Mapped[int] = mapped_column(ForeignKey("publications.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    url_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    language: Mapped[str | None] = mapped_column(String(16), index=True)
    topic: Mapped[str | None] = mapped_column(String(128), index=True)
    platform: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    strategy: Mapped[str | None] = mapped_column(String(128), index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="low", index=True)

    publication: Mapped[Publication] = relationship(back_populates="metrics")


class Job(TimestampStatusMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (Index("ix_jobs_type_status", "job_type", "status"),)

    job_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    url_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    language: Mapped[str | None] = mapped_column(String(16), index=True)
    topic: Mapped[str | None] = mapped_column(String(128), index=True)
    platform: Mapped[str | None] = mapped_column(String(64), index=True)
    strategy: Mapped[str | None] = mapped_column(String(128), index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="low", index=True)
    run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)


class ErrorLog(TimestampStatusMixin, Base):
    __tablename__ = "error_logs"
    __table_args__ = (Index("ix_error_logs_entity", "entity_type", "entity_id"),)

    entity_type: Mapped[str | None] = mapped_column(String(128), index=True)
    entity_id: Mapped[int | None] = mapped_column(index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    traceback: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    url_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    language: Mapped[str | None] = mapped_column(String(16), index=True)
    topic: Mapped[str | None] = mapped_column(String(128), index=True)
    platform: Mapped[str | None] = mapped_column(String(64), index=True)
    strategy: Mapped[str | None] = mapped_column(String(128), index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="low", index=True)

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.content import NewsEvent, RawItem, SourceLink
from app.services.ranking import apply_ranking

_WORD_RE = re.compile(r"[\w]+", re.UNICODE)
_DEFAULT_STOPWORDS = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it", "of", "on", "or", "the", "to", "with",
        "и", "в", "во", "не", "на", "с", "со", "по", "к", "ко", "у", "о", "об", "от", "за", "для", "как", "что",
    }
)


@dataclass(frozen=True)
class DeduplicationConfig:
    title_similarity_threshold: float = 0.86
    publication_window: timedelta = timedelta(hours=24)
    candidate_limit: int = 100
    same_domain_bonus: float = 0.04
    cross_domain_min_similarity: float = 0.92


@dataclass(frozen=True)
class DeduplicationResult:
    news_event: NewsEvent
    source_link: SourceLink
    created: bool
    reasons: list[dict[str, Any]]


def normalize_title(title: str) -> str:
    """Normalize a headline for deterministic fuzzy matching."""
    words = _WORD_RE.findall(title.casefold())
    return " ".join(word for word in words if word not in _DEFAULT_STOPWORDS)


def title_similarity(left: str, right: str) -> float:
    left_normalized = normalize_title(left)
    right_normalized = normalize_title(right)
    if not left_normalized or not right_normalized:
        return 0.0
    return SequenceMatcher(None, left_normalized, right_normalized).ratio()


def source_domain(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url if "://" in url else f"//{url}")
    host = (parsed.hostname or "").casefold()
    return host[4:] if host.startswith("www.") else host or None


def deduplicate_raw_item(
    session: Session,
    raw_item: RawItem,
    *,
    config: DeduplicationConfig | None = None,
    commit: bool = False,
) -> DeduplicationResult:
    """Attach a raw item to an existing event or create a new event.

    Matching priority:
    1. exact ``url_hash`` match against an existing linked raw item/event;
    2. normalized title similarity among events in the publication time window;
    3. domain-aware thresholding (same domain gets a small bonus, cross-domain requires
       a stricter threshold to avoid merging unrelated local reposts).
    """
    config = config or DeduplicationConfig()
    reasons: list[dict[str, Any]] = []
    if raw_item.id is None:
        session.flush()

    existing_link = _find_existing_link(session, raw_item)
    if existing_link is not None:
        reasons.append({"type": "already_linked", "raw_item_id": raw_item.id, "news_event_id": existing_link.news_event_id})
        _merge_reasons(existing_link, reasons)
        if commit:
            session.commit()
        return DeduplicationResult(existing_link.news_event, existing_link, created=False, reasons=reasons)

    duplicate_url_link = _find_existing_url_hash_link(session, raw_item, reasons)
    if duplicate_url_link is not None:
        _merge_reasons(duplicate_url_link, reasons)
        if commit:
            session.commit()
        return DeduplicationResult(duplicate_url_link.news_event, duplicate_url_link, created=False, reasons=reasons)

    matched_event = _find_by_url_hash(session, raw_item, reasons)
    if matched_event is None:
        matched_event = _find_by_title(session, raw_item, config, reasons)

    created = matched_event is None
    if created:
        matched_event = _create_event(raw_item)
        session.add(matched_event)
        session.flush()
        reasons.append({"type": "new_event", "raw_item_id": raw_item.id, "url_hash": raw_item.url_hash})
    else:
        _update_event(matched_event, raw_item)

    source_link = _get_or_create_link(session, matched_event, raw_item, reasons)
    _merge_event_metadata(matched_event, raw_item, reasons)
    apply_ranking(matched_event)
    _merge_reasons(source_link, reasons)
    session.flush()
    if commit:
        session.commit()
    return DeduplicationResult(matched_event, source_link, created=created, reasons=reasons)


def _find_existing_link(session: Session, raw_item: RawItem) -> SourceLink | None:
    if raw_item.id is None:
        return None
    return session.scalar(select(SourceLink).options(selectinload(SourceLink.news_event)).where(SourceLink.raw_item_id == raw_item.id))


def _find_existing_url_hash_link(session: Session, raw_item: RawItem, reasons: list[dict[str, Any]]) -> SourceLink | None:
    if not raw_item.url_hash:
        return None
    link = session.scalar(
        select(SourceLink)
        .options(selectinload(SourceLink.news_event))
        .where(SourceLink.url_hash == raw_item.url_hash)
        .order_by(SourceLink.id.asc())
        .limit(1)
    )
    if link is not None:
        reasons.append(
            {
                "type": "duplicate_url_hash_already_linked",
                "url_hash": raw_item.url_hash,
                "source_link_id": link.id,
                "news_event_id": link.news_event_id,
            }
        )
    return link


def _find_by_url_hash(session: Session, raw_item: RawItem, reasons: list[dict[str, Any]]) -> NewsEvent | None:
    if not raw_item.url_hash:
        return None
    event = session.scalar(select(NewsEvent).where(NewsEvent.url_hash == raw_item.url_hash).limit(1))
    if event is None:
        event = session.scalar(
            select(NewsEvent)
            .join(SourceLink, SourceLink.news_event_id == NewsEvent.id)
            .where(SourceLink.url_hash == raw_item.url_hash)
            .limit(1)
        )
    if event is not None:
        reasons.append({"type": "exact_url_hash", "url_hash": raw_item.url_hash, "news_event_id": event.id})
    return event


def _find_by_title(session: Session, raw_item: RawItem, config: DeduplicationConfig, reasons: list[dict[str, Any]]) -> NewsEvent | None:
    now = datetime.now(timezone.utc)
    cutoff = now - config.publication_window
    published_at = _ensure_timezone(raw_item.published_at) if raw_item.published_at else now
    if published_at < cutoff:
        reasons.append(
            {
                "type": "title_similarity_skipped",
                "reason": "raw_item_outside_publication_window",
                "publication_window_hours": config.publication_window.total_seconds() / 3600,
            }
        )
        return None
    query = select(NewsEvent).where(NewsEvent.created_at >= cutoff).order_by(NewsEvent.created_at.desc()).limit(config.candidate_limit)
    if raw_item.topic:
        query = query.where(NewsEvent.topic == raw_item.topic)
    candidates = session.scalars(query).all()
    raw_domain = source_domain(raw_item.source_url)
    best: tuple[float, NewsEvent, dict[str, Any]] | None = None
    for event in candidates:
        event_time = _event_publication_time(event)
        if event_time is not None:
            event_time = _ensure_timezone(event_time)
        if event_time is not None and event_time < cutoff:
            continue
        similarity = title_similarity(raw_item.title, event.title)
        same_domain = raw_domain is not None and raw_domain == source_domain(event.source_url)
        adjusted = similarity + (config.same_domain_bonus if same_domain else 0.0)
        threshold = config.title_similarity_threshold if same_domain else max(config.title_similarity_threshold, config.cross_domain_min_similarity)
        reason = {
            "type": "title_similarity",
            "similarity": round(similarity, 4),
            "adjusted_similarity": round(adjusted, 4),
            "threshold": threshold,
            "same_domain": same_domain,
            "domain": raw_domain,
            "publication_window_hours": config.publication_window.total_seconds() / 3600,
            "news_event_id": event.id,
        }
        if adjusted >= threshold and (best is None or adjusted > best[0]):
            best = (adjusted, event, reason)
    if best is not None:
        reasons.append(best[2])
        return best[1]
    return None


def _event_publication_time(event: NewsEvent) -> datetime | None:
    metadata = getattr(event, "event_metadata", None) or {}
    value = metadata.get("published_at") or metadata.get("first_published_at")
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return _ensure_timezone(event.created_at) if event.created_at else None


def _create_event(raw_item: RawItem) -> NewsEvent:
    return NewsEvent(
        title=raw_item.title,
        summary=raw_item.content[:1000],
        source_url=raw_item.source_url,
        url_hash=raw_item.url_hash,
        language=raw_item.language,
        topic=raw_item.topic,
        platform=raw_item.platform,
        strategy=raw_item.strategy,
        score=raw_item.score,
        risk_level=raw_item.risk_level,
        status="pending",
        event_metadata={"raw_item_ids": [raw_item.id], "source_domains": [source_domain(raw_item.source_url)], "published_at": _iso(raw_item.published_at)},
    )


def _update_event(event: NewsEvent, raw_item: RawItem) -> None:
    event.score = max(event.score or 0.0, raw_item.score or 0.0)
    if not event.summary and raw_item.content:
        event.summary = raw_item.content[:1000]
    for field in ("topic", "platform", "strategy"):
        if getattr(event, field) is None and getattr(raw_item, field) is not None:
            setattr(event, field, getattr(raw_item, field))


def _get_or_create_link(session: Session, event: NewsEvent, raw_item: RawItem, reasons: list[dict[str, Any]]) -> SourceLink:
    link = session.scalar(select(SourceLink).where(SourceLink.news_event_id == event.id, SourceLink.raw_item_id == raw_item.id))
    if link is None:
        link = SourceLink(
            news_event_id=event.id,
            raw_item_id=raw_item.id,
            source_url=raw_item.source_url,
            url_hash=raw_item.url_hash,
            language=raw_item.language,
            topic=raw_item.topic,
            platform=raw_item.platform,
            strategy=raw_item.strategy,
            score=raw_item.score,
            risk_level=raw_item.risk_level,
        )
        session.add(link)
        session.flush()
        reasons.append({"type": "source_link_created", "source_link_id": link.id})
    return link


def _merge_event_metadata(event: NewsEvent, raw_item: RawItem, reasons: list[dict[str, Any]]) -> None:
    metadata = dict(event.event_metadata or {})
    raw_item_ids = set(metadata.get("raw_item_ids") or [])
    if raw_item.id is not None:
        raw_item_ids.add(raw_item.id)
    domains = {domain for domain in (metadata.get("source_domains") or []) if domain}
    domain = source_domain(raw_item.source_url)
    if domain:
        domains.add(domain)
    metadata["raw_item_ids"] = sorted(raw_item_ids)
    metadata["source_domains"] = sorted(domains)
    metadata["deduplication_reasons"] = [*metadata.get("deduplication_reasons", []), *reasons]
    if raw_item.published_at:
        metadata.setdefault("first_published_at", _iso(raw_item.published_at))
        metadata["last_published_at"] = _iso(raw_item.published_at)
    event.event_metadata = metadata


def _merge_reasons(link: SourceLink, reasons: list[dict[str, Any]]) -> None:
    existing = list(link.reasons or [])
    link.reasons = [*existing, *reasons]


def _ensure_timezone(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _iso(value: datetime | None) -> str | None:
    return _ensure_timezone(value).isoformat() if value else None


def deduplicate_pending_raw_items(session: Session, *, config: DeduplicationConfig | None = None, limit: int = 100, commit: bool = False) -> list[DeduplicationResult]:
    items = session.scalars(select(RawItem).where(RawItem.status == "pending").order_by(func.coalesce(RawItem.published_at, RawItem.created_at)).limit(limit)).all()
    results = [deduplicate_raw_item(session, item, config=config, commit=False) for item in items]
    if commit:
        session.commit()
    return results

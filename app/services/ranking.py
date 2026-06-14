from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Mapping, Sequence

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.content import NewsEvent

_WORD_RE = re.compile(r"[\w]+", re.UNICODE)
_RU_RE = re.compile(r"[а-яё]", re.IGNORECASE)
_EXCLAMATION_RE = re.compile(r"[!?]")

_PRACTICAL_TERMS = frozenset(
    {
        "как", "инструкция", "гайд", "совет", "шаг", "способ", "проверить", "сделать", "получить",
        "how", "guide", "tips", "steps", "check", "use", "save", "apply", "fix",
    }
)
_EMOTIONAL_TERMS = frozenset(
    {
        "скандал", "шок", "кризис", "угроза", "победа", "провал", "срочно", "впервые", "важно",
        "scandal", "shock", "crisis", "threat", "win", "fail", "urgent", "first", "major",
    }
)
_SEO_TERMS = frozenset(
    {
        "что", "почему", "как", "когда", "цена", "список", "лучший", "обзор", "причины",
        "what", "why", "how", "when", "price", "list", "best", "review", "reasons",
    }
)
_DISCUSSION_TERMS = frozenset(
    {
        "запрет", "закон", "налог", "выборы", "штраф", "конфликт", "мнения", "спор", "суд",
        "ban", "law", "tax", "election", "fine", "conflict", "debate", "court", "versus",
    }
)
_FAKE_RISK_TERMS = frozenset(
    {
        "слух", "инсайд", "неподтвержден", "аноним", "сенсация", "шокирующий",
        "rumor", "unconfirmed", "anonymous", "leak", "shocking",
    }
)
_LEGAL_RISK_TERMS = frozenset(
    {
        "обвиняет", "мошенник", "преступник", "экстремист", "пиратский", "взлом", "утечка данных",
        "accuses", "fraudster", "criminal", "extremist", "pirated", "hack", "data leak",
    }
)


@dataclass(frozen=True)
class RankingConfig:
    """Weights and bounds used by pure ranking functions."""

    positive_weights: Mapping[str, float] = field(
        default_factory=lambda: {
            "interest_ru": 1.25,
            "novelty": 1.15,
            "practical_value": 1.0,
            "emotional_value": 0.8,
            "seo_potential": 0.9,
            "discussion_potential": 0.9,
        }
    )
    negative_weights: Mapping[str, float] = field(default_factory=lambda: {"fake_risk": 1.4, "legal_risk": 1.2, "saturation": 1.0})
    min_score: float = 0.0
    max_score: float = 100.0


@dataclass(frozen=True)
class RankingResult:
    score: float
    components: dict[str, float]
    penalties: dict[str, float]
    reasons: list[dict[str, Any]]


def tokenize(text: str) -> list[str]:
    """Return lowercase tokens. Pure helper kept separate for unit tests."""
    return _WORD_RE.findall(text.casefold())


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def keyword_score(tokens: Sequence[str], keywords: set[str] | frozenset[str]) -> float:
    if not tokens:
        return 0.0
    hits = sum(1 for token in tokens if token in keywords)
    return clamp(hits / 3)


def recency_score(published_at: datetime | None, *, now: datetime | None = None) -> float:
    if published_at is None:
        return 0.45
    now = now or datetime.now(timezone.utc)
    published_at = published_at if published_at.tzinfo else published_at.replace(tzinfo=timezone.utc)
    hours = max(0.0, (now - published_at).total_seconds() / 3600)
    return clamp(math.exp(-hours / 48))


def calculate_components(event: "NewsEvent" | Mapping[str, Any], *, now: datetime | None = None) -> dict[str, float]:
    data = _event_data(event)
    title = data.get("title") or ""
    summary = data.get("summary") or ""
    text = f"{title} {summary}"
    tokens = tokenize(text)
    title_tokens = tokenize(title)
    metadata = data.get("event_metadata") or data.get("metadata") or {}
    source_count = len(metadata.get("source_domains") or []) or len(metadata.get("raw_item_ids") or [])

    return {
        "interest_ru": round(clamp((_ru_share(text) * 0.7) + (keyword_score(tokens, _DISCUSSION_TERMS) * 0.3)), 4),
        "novelty": round(recency_score(_published_at(data, metadata), now=now), 4),
        "practical_value": round(keyword_score(tokens, _PRACTICAL_TERMS), 4),
        "emotional_value": round(clamp(keyword_score(tokens, _EMOTIONAL_TERMS) + min(0.25, len(_EXCLAMATION_RE.findall(title)) * 0.08)), 4),
        "seo_potential": round(clamp(keyword_score(title_tokens, _SEO_TERMS) + (0.25 if 6 <= len(title_tokens) <= 14 else 0.0)), 4),
        "discussion_potential": round(clamp(keyword_score(tokens, _DISCUSSION_TERMS) + min(0.3, source_count * 0.08)), 4),
    }


def calculate_penalties(event: "NewsEvent" | Mapping[str, Any]) -> dict[str, float]:
    data = _event_data(event)
    text = f"{data.get('title') or ''} {data.get('summary') or ''}".casefold()
    tokens = tokenize(text)
    metadata = data.get("event_metadata") or data.get("metadata") or {}
    source_count = len(metadata.get("source_domains") or []) or len(metadata.get("raw_item_ids") or [])
    return {
        "fake_risk": round(clamp(keyword_score(tokens, _FAKE_RISK_TERMS) + (0.15 if source_count <= 1 else 0.0)), 4),
        "legal_risk": round(clamp(keyword_score(tokens, _LEGAL_RISK_TERMS)), 4),
        "saturation": round(clamp(max(0, source_count - 3) / 7), 4),
    }


def calculate_score(components: Mapping[str, float], penalties: Mapping[str, float], config: RankingConfig | None = None) -> float:
    config = config or RankingConfig()
    positive = sum(components.get(name, 0.0) * weight for name, weight in config.positive_weights.items())
    negative = sum(penalties.get(name, 0.0) * weight for name, weight in config.negative_weights.items())
    normalized = (positive - negative) / sum(config.positive_weights.values())
    return round(clamp(normalized, 0.0, 1.0) * config.max_score, 2)


def build_reasons(components: Mapping[str, float], penalties: Mapping[str, float]) -> list[dict[str, Any]]:
    reasons = [{"type": "component", "name": name, "value": value} for name, value in components.items() if value > 0]
    reasons.extend({"type": "penalty", "name": name, "value": value} for name, value in penalties.items() if value > 0)
    return reasons


def rank_event(event: "NewsEvent" | Mapping[str, Any], *, config: RankingConfig | None = None, now: datetime | None = None) -> RankingResult:
    components = calculate_components(event, now=now)
    penalties = calculate_penalties(event)
    score = calculate_score(components, penalties, config=config)
    return RankingResult(score=score, components=components, penalties=penalties, reasons=build_reasons(components, penalties))


def apply_ranking(event: "NewsEvent", *, config: RankingConfig | None = None, now: datetime | None = None) -> RankingResult:
    result = rank_event(event, config=config, now=now)
    event.score = result.score
    event.reasons = result.reasons
    metadata = dict(event.event_metadata or {})
    metadata["ranking"] = {"components": result.components, "penalties": result.penalties}
    event.event_metadata = metadata
    return result


def rank_news_events(session: "Session", *, limit: int = 100, commit: bool = False, config: RankingConfig | None = None) -> list[RankingResult]:
    from sqlalchemy import select

    from app.models.content import NewsEvent

    events = session.scalars(select(NewsEvent).order_by(NewsEvent.created_at.desc()).limit(limit)).all()
    results = [apply_ranking(event, config=config) for event in events]
    session.flush()
    if commit:
        session.commit()
    return results


def _event_data(event: "NewsEvent" | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(event, Mapping):
        return event
    return {
        "title": event.title,
        "summary": event.summary,
        "created_at": event.created_at,
        "event_metadata": event.event_metadata,
        "source_url": event.source_url,
    }


def _published_at(data: Mapping[str, Any], metadata: Mapping[str, Any]) -> datetime | None:
    value = metadata.get("published_at") or metadata.get("first_published_at") or data.get("created_at")
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _ru_share(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0.0
    ru_letters = len(_RU_RE.findall(text))
    return clamp(ru_letters / len(letters))

"""Generate platform-specific draft variants for news events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Final

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.llm import OllamaClient
from app.models.content import GeneratedVariant, NewsEvent, SourceLink
from app.prompts.engine import PromptEngine

GENERATION_PLATFORMS: Final[tuple[str, ...]] = (
    "telegram_short",
    "dzen_article",
    "max_post",
    "vc_case_analysis",
    "habr_technical_draft",
    "dtf_geek_post",
    "pikabu_story",
)

_STRATEGY_BY_PLATFORM: Final[dict[str, str]] = {
    "telegram_short": "short_news_post",
    "dzen_article": "longform_explainer",
    "max_post": "social_news_post",
    "vc_case_analysis": "business_case_analysis",
    "habr_technical_draft": "technical_draft",
    "dtf_geek_post": "geek_culture_post",
    "pikabu_story": "storytelling_post",
}

_GENERATION_TEMPLATE: Final[str] = """
Ты редактор русскоязычного контент-проекта. Создай вариант публикации для платформы {{ platform }}.

Новостное событие:
Заголовок: {{ event.title }}
Краткое описание: {{ event.summary }}
Тема: {{ event.topic or "не указана" }}
Риск исходного события: {{ event.risk_level }}

Источники:
{% for source in sources -%}
- {{ source.title }}{% if source.url %} — {{ source.url }}{% endif %}
  {{ source.content }}
{% endfor %}

Требования:
- Сохраняй факты и не добавляй неподтвержденные утверждения.
- Подстрой стиль и длину под {{ platform }}.
- Верни только валидный JSON без markdown-блока.
- JSON-схема: {"title": "...", "lead": "...", "body": "...", "sources": ["url или название", "..."], "risk_level": "low|medium|high"}.
""".strip()


@dataclass(frozen=True, slots=True)
class GeneratedVariantPayload:
    title: str
    lead: str
    body: str
    sources: list[str]
    platform: str
    strategy: str
    risk_level: str


def generate_variants_for_news_event(
    session: Session,
    news_event_id: int,
    *,
    prompt_engine: PromptEngine | None = None,
    ollama_client: OllamaClient | None = None,
    platforms: tuple[str, ...] = GENERATION_PLATFORMS,
    commit: bool = True,
) -> list[GeneratedVariant]:
    """Generate and persist draft variants for one news event."""
    event = session.scalar(
        select(NewsEvent)
        .options(selectinload(NewsEvent.source_links).selectinload(SourceLink.raw_item))
        .where(NewsEvent.id == news_event_id)
    )
    if event is None:
        raise ValueError(f"News event {news_event_id} was not found")

    engine = prompt_engine or PromptEngine()
    client = ollama_client or OllamaClient(prompt_engine=engine)
    source_context = _build_source_context(event)

    variants: list[GeneratedVariant] = []
    for platform in platforms:
        strategy = _STRATEGY_BY_PLATFORM[platform]
        prompt = engine.render_template(
            _GENERATION_TEMPLATE,
            {"event": event, "sources": source_context, "platform": platform},
        )
        response = client._request(prompt, task="platform_adapt")
        payload = _parse_generation_response(
            str(response.get("response", "")),
            platform=platform,
            strategy=strategy,
            fallback_risk_level=event.risk_level,
        )
        variant = GeneratedVariant(
            news_event_id=event.id,
            prompt_version=None,
            title=payload.title,
            lead=payload.lead,
            body=payload.body,
            sources=payload.sources,
            content=payload.body,
            language=event.language,
            topic=event.topic,
            platform=payload.platform,
            strategy=payload.strategy,
            risk_level=payload.risk_level,
            status="draft",
        )
        session.add(variant)
        variants.append(variant)

    session.flush()
    if commit:
        session.commit()
        for variant in variants:
            session.refresh(variant)
    return variants


def _build_source_context(event: NewsEvent) -> list[dict[str, str | None]]:
    sources: list[dict[str, str | None]] = []
    for link in event.source_links:
        raw_item = link.raw_item
        if raw_item is None:
            continue
        sources.append({"title": raw_item.title, "url": raw_item.source_url, "content": raw_item.content[:4000]})
    if not sources:
        sources.append({"title": event.title, "url": event.source_url, "content": event.summary})
    return sources


def _parse_generation_response(raw_response: str, *, platform: str, strategy: str, fallback_risk_level: str) -> GeneratedVariantPayload:
    data = _load_json_object(raw_response)
    title = str(data.get("title") or "").strip()
    lead = str(data.get("lead") or "").strip()
    body = str(data.get("body") or data.get("content") or "").strip()
    if not title or not body:
        raise ValueError("Generated response must include non-empty title and body")
    raw_sources = data.get("sources") or []
    sources = [str(source).strip() for source in raw_sources if str(source).strip()] if isinstance(raw_sources, list) else [str(raw_sources).strip()]
    risk_level = str(data.get("risk_level") or fallback_risk_level or "low").strip().lower()
    if risk_level not in {"low", "medium", "high"}:
        risk_level = fallback_risk_level or "low"
    return GeneratedVariantPayload(title=title, lead=lead, body=body, sources=sources, platform=platform, strategy=strategy, risk_level=risk_level)


def _load_json_object(raw_response: str) -> dict[str, Any]:
    text = raw_response.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Generated response must be a JSON object")
    return data

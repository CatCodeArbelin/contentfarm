from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import AliasChoices, BaseModel, Field, HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes.db_helpers import commit_or_rollback
from app.collectors.rss import collect_rss
from app.collectors.runner import collect_active_sources
from app.collectors.utils import url_hash
from app.db.session import get_db
from app.models.content import Source

router = APIRouter(prefix="/collectors", tags=["Collectors"])


class RssCollectRequest(BaseModel):
    source_id: int | None = Field(default=None, ge=1, description="Existing source ID to collect.")
    url: HttpUrl | None = Field(
        default=None,
        validation_alias=AliasChoices("url", "source_url"),
        description="RSS/Atom feed URL to create or upsert before collection.",
    )
    name: str | None = Field(default=None, min_length=1, max_length=200)
    language: str = Field(default="en", min_length=2, max_length=16)
    topic: str | None = None
    strategy: str | None = None


def _source_from_rss_payload(db: Session, payload: RssCollectRequest) -> Source:
    if payload.source_id is not None:
        source = db.get(Source, payload.source_id)
        if source is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
        return source

    if payload.url is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Provide either source_id or url")

    source_url = str(payload.url)
    digest = url_hash(source_url)
    source = db.scalar(select(Source).where(Source.url_hash == digest))
    if source is None:
        source = Source(
            name=payload.name or source_url,
            source_url=source_url,
            url_hash=digest,
            language=payload.language,
            topic=payload.topic,
            platform="rss",
            strategy=payload.strategy,
            status="active",
        )
        db.add(source)
    else:
        source.source_url = source_url
        source.platform = "rss"
        source.name = payload.name or source.name
        source.language = payload.language or source.language
        source.topic = payload.topic if payload.topic is not None else source.topic
        source.strategy = payload.strategy if payload.strategy is not None else source.strategy
    commit_or_rollback(db)
    db.refresh(source)
    return source


@router.post("/run", status_code=status.HTTP_202_ACCEPTED, summary="Run collectors for active sources")
def run_collectors(db: Session = Depends(get_db)) -> dict[str, object]:
    return collect_active_sources(db)


@router.post("/rss", summary="Collect a single RSS source")
def collect_rss_source(payload: RssCollectRequest, db: Session = Depends(get_db)) -> dict[str, int]:
    source = _source_from_rss_payload(db, payload)
    return collect_rss(db, source)

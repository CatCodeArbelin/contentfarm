from fastapi import APIRouter, HTTPException, status

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery, apply_filters, now_utc
from app.api.routes.variants import _ITEMS as VARIANTS
from app.exporters.html import export_html
from app.exporters.markdown import SUPPORTED_PLATFORMS as EXPORT_PLATFORMS
from app.exporters.markdown import export_markdown
from app.publishers.max import MaxPublisher
from app.publishers.telegram import TelegramPublisher
from app.schemas.common import ListFilters, PaginatedResponse, Status
from app.schemas.publications import PublicationRead, PublicationRequest, PublishRequest

router = APIRouter(prefix="/publications", tags=["Publications"])
publish_router = APIRouter(tags=["Publications"])

_ITEMS: list[PublicationRead] = []


def _find_variant(variant_id: int):
    return next((item for item in VARIANTS if item.id == variant_id), None)


def _find_publication(publication_id: int) -> PublicationRead | None:
    return next((item for item in _ITEMS if item.id == publication_id), None)


@router.get("", response_model=PaginatedResponse[PublicationRead], summary="List publications")
def list_publications(
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
    status: StatusQuery = None,
    language: TextQuery = None,
    topic: TextQuery = None,
    platform: TextQuery = None,
    strategy: TextQuery = None,
    created_at: CreatedAtQuery = None,
) -> PaginatedResponse[PublicationRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = apply_filters(_ITEMS, filters, limit, offset)
    return PaginatedResponse[PublicationRead](items=items, limit=limit, offset=offset, total=total)


@router.post("", response_model=PublicationRead, status_code=status.HTTP_202_ACCEPTED, summary="Queue publication")
def queue_publication(payload: PublicationRequest) -> PublicationRead:
    item = PublicationRead(
        id=len(_ITEMS) + 1,
        variant_id=payload.variant_id,
        platform=payload.platform,
        strategy=payload.strategy,
        language=None,
        topic=None,
        status=Status.scheduled if payload.scheduled_at else Status.draft,
        url=None,
        message_id=None,
        export_path=None,
        error=None,
        created_at=now_utc(),
        scheduled_at=payload.scheduled_at,
        published_at=None,
        approved_at=None,
        approved_by=None,
    )
    _ITEMS.append(item)
    return item


@publish_router.post("/publish", response_model=PublicationRead, summary="Publish or export content by platform")
def publish(payload: PublishRequest) -> PublicationRead:
    if payload.target_type == "publication":
        publication = _find_publication(payload.target_id)
        if publication is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publication not found")
        variant = _find_variant(publication.variant_id)
        if variant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
    else:
        variant = _find_variant(payload.target_id)
        if variant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
        publication = PublicationRead(
            id=len(_ITEMS) + 1,
            variant_id=variant.id,
            platform=payload.platform or variant.platform,
            strategy=variant.strategy,
            language=variant.language,
            topic=variant.topic,
            status=Status.processing,
            url=None,
            message_id=None,
            export_path=None,
            error=None,
            created_at=now_utc(),
            scheduled_at=None,
            published_at=None,
            approved_at=variant.approved_at,
            approved_by=variant.approved_by,
        )
        _ITEMS.append(publication)

    platform = payload.platform or publication.platform
    content = variant.content
    result_status = Status.failed
    message_id = None
    export_path = None
    publication_url = str(payload.publication_url) if payload.publication_url else None
    error = None

    if platform == "telegram":
        result = TelegramPublisher().publish(content)
        result_status = Status(result.status)
        message_id = result.message_id
        publication_url = publication_url or result.publication_url
        error = result.error
    elif platform == "max":
        result = MaxPublisher().publish(content)
        result_status = Status(result.status)
        message_id = result.message_id
        publication_url = publication_url or result.publication_url
        error = result.error
    elif platform in EXPORT_PLATFORMS:
        export_format = payload.export_format or "markdown"
        exporter = export_html if export_format == "html" else export_markdown
        title = getattr(variant, "title", None) or (content.splitlines()[0] if content.splitlines() else None)
        export_path = exporter(title=title, content=content, platform=platform)
        result_status = Status.published
    else:
        error = f"Unsupported platform: {platform}"

    updated = publication.model_copy(
        update={
            "platform": platform,
            "status": result_status,
            "url": publication_url,
            "message_id": message_id,
            "export_path": export_path,
            "error": error,
            "published_at": now_utc() if result_status == Status.published else publication.published_at,
        }
    )
    _ITEMS[_ITEMS.index(publication)] = updated
    return updated

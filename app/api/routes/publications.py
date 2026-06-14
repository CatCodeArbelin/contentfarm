from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery, now_utc
from app.api.routes.db_helpers import commit_or_rollback, get_model_or_404, list_models
from app.db.session import get_db
from app.exporters.html import export_html
from app.exporters.markdown import SUPPORTED_PLATFORMS as EXPORT_PLATFORMS
from app.exporters.markdown import export_markdown
from app.models.content import GeneratedVariant, Publication
from app.publishers.max import MaxPublisher
from app.publishers.telegram import TelegramPublisher
from app.schemas.common import ListFilters, PaginatedResponse, Status
from app.schemas.publications import PublicationRead, PublicationRequest, PublishRequest

router = APIRouter(prefix="/publications", tags=["Publications"])
publish_router = APIRouter(tags=["Publications"])


@router.get("", response_model=PaginatedResponse[PublicationRead], summary="List publications")
def list_publications(limit: LimitQuery = 50, offset: OffsetQuery = 0, status: StatusQuery = None, language: TextQuery = None, topic: TextQuery = None, platform: TextQuery = None, strategy: TextQuery = None, created_at: CreatedAtQuery = None, db: Session = Depends(get_db)) -> PaginatedResponse[PublicationRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = list_models(db, Publication, filters, limit, offset)
    return PaginatedResponse[PublicationRead](items=items, limit=limit, offset=offset, total=total)


@router.get("/{item_id}", response_model=PublicationRead, summary="Get publication")
def get_publication(item_id: int, db: Session = Depends(get_db)) -> PublicationRead:
    return get_model_or_404(db, Publication, item_id, "Publication")


@router.post("", response_model=PublicationRead, status_code=status.HTTP_202_ACCEPTED, summary="Queue publication")
def queue_publication(payload: PublicationRequest, db: Session = Depends(get_db)) -> PublicationRead:
    variant = get_model_or_404(db, GeneratedVariant, payload.variant_id, "Variant")
    item = Publication(variant_id=variant.id, platform=payload.platform, strategy=payload.strategy, language=variant.language, topic=variant.topic, status=Status.scheduled.value if payload.scheduled_at else Status.draft.value, scheduled_at=payload.scheduled_at, approved_at=variant.approved_at, approved_by=variant.approved_by)
    db.add(item)
    commit_or_rollback(db)
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=PublicationRead, summary="Update publication")
def update_publication(item_id: int, payload: PublicationRequest, db: Session = Depends(get_db)) -> PublicationRead:
    item = get_model_or_404(db, Publication, item_id, "Publication")
    for key, value in payload.model_dump(exclude_unset=True, mode="json").items():
        setattr(item, key, value)
    commit_or_rollback(db)
    db.refresh(item)
    return item


@publish_router.post("/publish", response_model=PublicationRead, summary="Publish or export content by platform")
def publish(payload: PublishRequest, db: Session = Depends(get_db)) -> PublicationRead:
    if payload.target_type == "publication":
        publication = get_model_or_404(db, Publication, payload.target_id, "Publication")
        variant = get_model_or_404(db, GeneratedVariant, publication.variant_id, "Variant")
    else:
        variant = get_model_or_404(db, GeneratedVariant, payload.target_id, "Variant")
        publication = Publication(variant_id=variant.id, platform=payload.platform or variant.platform, strategy=variant.strategy, language=variant.language, topic=variant.topic, status=Status.processing.value, approved_at=variant.approved_at, approved_by=variant.approved_by)
        db.add(publication)
        db.flush()

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
        exporter = export_html if (payload.export_format or "markdown") == "html" else export_markdown
        title = variant.title or (content.splitlines()[0] if content.splitlines() else None)
        export_path = exporter(title=title, content=content, platform=platform)
        result_status = Status.published
    else:
        error = f"Unsupported platform: {platform}"

    publication.platform = platform
    publication.status = result_status.value
    publication.publication_url = publication_url
    publication.message_id = message_id
    publication.export_path = export_path
    publication.error = error
    if result_status == Status.published:
        publication.published_at = now_utc()
    commit_or_rollback(db)
    db.refresh(publication)
    return publication

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery, now_utc
from app.api.routes.db_helpers import commit_or_rollback, get_model_or_404, list_models
from app.db.session import get_db
from app.exporters.html import export_html
from app.exporters.markdown import SUPPORTED_PLATFORMS as EXPORT_PLATFORMS
from app.exporters.markdown import export_markdown
from app.models.content import GeneratedVariant, Publication
from app.publishers.telegram import TelegramPublisher
from app.schemas.common import ListFilters, PaginatedResponse, Status
from app.schemas.publications import PublicationExportRequest, PublicationRead, PublicationRequest, PublishRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/publications", tags=["Publications"])
publish_router = APIRouter(tags=["Publications"])


def ensure_variant_approved(variant: GeneratedVariant) -> None:
    if variant.status != Status.approved.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Variant must be approved before publishing or exporting.")


def _get_approved_variant(session: Session, variant_id: int) -> GeneratedVariant:
    variant = session.get(GeneratedVariant, variant_id)
    if variant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
    ensure_variant_approved(variant)
    return variant


def _publication_from_variant(variant: GeneratedVariant, *, platform: str, status_value: str) -> Publication:
    return Publication(
        variant_id=variant.id,
        platform=platform,
        strategy=variant.strategy,
        language=variant.language,
        topic=variant.topic,
        status=status_value,
        approved_at=variant.approved_at,
        approved_by=variant.approved_by,
    )


def _commit_failed_publication(session: Session, variant: GeneratedVariant, *, platform: str, error: str) -> Publication | None:
    try:
        failed = _publication_from_variant(variant, platform=platform, status_value=Status.failed.value)
        failed.error = error
        session.add(failed)
        session.commit()
        session.refresh(failed)
        return failed
    except SQLAlchemyError:
        session.rollback()
        logger.exception("Failed to persist failed publication state: variant_id=%s platform=%s", variant.id, platform)
        return None


@router.get("", response_model=PaginatedResponse[PublicationRead], summary="List publications")
def list_publications(limit: LimitQuery = 50, offset: OffsetQuery = 0, status: StatusQuery = None, language: TextQuery = None, topic: TextQuery = None, platform: TextQuery = None, strategy: TextQuery = None, created_at: CreatedAtQuery = None, session: Session = Depends(get_db)) -> PaginatedResponse[PublicationRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = list_models(session, Publication, filters, limit, offset)
    return PaginatedResponse[PublicationRead](items=items, limit=limit, offset=offset, total=total)


@router.get("/{item_id}", response_model=PublicationRead, summary="Get publication")
def get_publication(item_id: int, session: Session = Depends(get_db)) -> PublicationRead:
    return get_model_or_404(session, Publication, item_id, "Publication")


@router.post("", response_model=PublicationRead, status_code=status.HTTP_202_ACCEPTED, summary="Queue publication")
def queue_publication(payload: PublicationRequest, session: Session = Depends(get_db)) -> PublicationRead:
    variant = get_model_or_404(session, GeneratedVariant, payload.variant_id, "Variant")
    item = Publication(variant_id=variant.id, platform=payload.platform, strategy=payload.strategy, language=variant.language, topic=variant.topic, status=Status.scheduled.value if payload.scheduled_at else Status.draft.value, scheduled_at=payload.scheduled_at, approved_at=variant.approved_at, approved_by=variant.approved_by)
    session.add(item)
    commit_or_rollback(session)
    session.refresh(item)
    return item


@router.post("/{variant_id}/publish-telegram", response_model=PublicationRead, summary="Publish variant to Telegram")
def publish_variant_to_telegram(variant_id: int, session: Session = Depends(get_db)) -> PublicationRead:
    variant = _get_approved_variant(session, variant_id)
    publication = _publication_from_variant(variant, platform="telegram", status_value=Status.processing.value)
    session.add(publication)

    try:
        result = TelegramPublisher().publish(variant.content)
        publication.status = result.status
        publication.message_id = result.message_id
        publication.publication_url = result.publication_url
        publication.error = result.error
        if result.status == Status.published.value:
            publication.published_at = now_utc()
        session.commit()
        session.refresh(publication)
        return publication
    except Exception as exc:
        session.rollback()
        logger.exception("Telegram publication failed: variant_id=%s", variant_id)
        failed = _commit_failed_publication(session, variant, platform="telegram", error=str(exc))
        if failed is not None:
            return failed
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Telegram publication failed and failed state could not be saved.") from exc


def _export_approved_variant(session: Session, variant: GeneratedVariant, payload: PublicationExportRequest) -> Publication:
    platform = payload.platform
    if platform not in EXPORT_PLATFORMS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported export platform: {platform}")

    publication = _publication_from_variant(variant, platform=platform, status_value=Status.processing.value)
    session.add(publication)

    try:
        exporter = export_html if payload.export_format == "html" else export_markdown
        title = variant.title or (variant.content.splitlines()[0] if variant.content.splitlines() else None)
        publication.export_path = exporter(title=title, content=variant.content, platform=platform)
        publication.status = Status.published.value
        publication.published_at = now_utc()
        session.commit()
        session.refresh(publication)
        return publication
    except Exception as exc:
        session.rollback()
        logger.exception("Variant export failed: variant_id=%s platform=%s", variant.id, platform)
        failed = _commit_failed_publication(session, variant, platform=platform, error=str(exc))
        if failed is not None:
            return failed
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Variant export failed and failed state could not be saved.") from exc


@router.post("/{variant_id}/export", response_model=PublicationRead, summary="Export variant")
def export_variant(variant_id: int, payload: PublicationExportRequest, session: Session = Depends(get_db)) -> PublicationRead:
    variant = _get_approved_variant(session, variant_id)
    return _export_approved_variant(session, variant, payload)


@router.patch("/{item_id}", response_model=PublicationRead, summary="Update publication")
def update_publication(item_id: int, payload: PublicationRequest, session: Session = Depends(get_db)) -> PublicationRead:
    item = get_model_or_404(session, Publication, item_id, "Publication")
    for key, value in payload.model_dump(exclude_unset=True, mode="json").items():
        setattr(item, key, value)
    commit_or_rollback(session)
    session.refresh(item)
    return item


@publish_router.post("/publish", response_model=PublicationRead, summary="Publish or export content by platform")
def publish(payload: PublishRequest, session: Session = Depends(get_db)) -> PublicationRead:
    variant_id = payload.target_id
    if payload.target_type == "publication":
        existing = get_model_or_404(session, Publication, payload.target_id, "Publication")
        variant_id = existing.variant_id

    variant = _get_approved_variant(session, variant_id)
    platform = payload.platform or variant.platform
    if platform == "telegram":
        return publish_variant_to_telegram(variant.id, session)
    if platform in EXPORT_PLATFORMS:
        return _export_approved_variant(
            session,
            variant,
            PublicationExportRequest(platform=platform, format=payload.export_format or "markdown"),
        )
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported platform: {platform}")

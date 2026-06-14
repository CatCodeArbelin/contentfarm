import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes._helpers import now_utc
from app.api.routes.db_helpers import commit_or_rollback, get_model_or_404
from app.db.session import get_db
from app.models.content import GeneratedVariant, Publication
from app.schemas.common import Status
from app.schemas.publications import ApprovalRequest, PublicationRead, PublishRequest
from app.schemas.variants import VariantRead

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Publications", "Variants"])
PublishableTarget = Literal["variant", "publication"]
_ALLOWED_PUBLISH_STATUSES = {Status.approved.value, Status.scheduled.value}


def _get_target(db: Session, target_type: str, target_id: int) -> GeneratedVariant | Publication:
    return get_model_or_404(db, GeneratedVariant if target_type == "variant" else Publication, target_id, target_type.capitalize())


@router.post("/approve", response_model=VariantRead | PublicationRead, summary="Approve a variant or publication")
def approve(payload: ApprovalRequest, db: Session = Depends(get_db)) -> VariantRead | PublicationRead:
    item = _get_target(db, payload.target_type, payload.target_id)
    item.status = Status.approved.value
    item.approved_at = now_utc()
    item.approved_by = payload.approved_by
    commit_or_rollback(db)
    db.refresh(item)
    return item


@router.post("/publish", response_model=VariantRead | PublicationRead, summary="Publish an approved or scheduled variant/publication")
def publish(payload: PublishRequest, db: Session = Depends(get_db)) -> VariantRead | PublicationRead:
    item = _get_target(db, payload.target_type, payload.target_id)
    if item.status not in _ALLOWED_PUBLISH_STATUSES:
        logger.warning("Publication attempt rejected because target is not approved: target_type=%s target_id=%s status=%s", payload.target_type, payload.target_id, item.status)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Target must be approved or scheduled before publishing.")
    item.status = Status.published.value
    item.published_at = now_utc()
    if isinstance(item, Publication) and payload.publication_url is not None:
        item.publication_url = str(payload.publication_url)
    commit_or_rollback(db)
    db.refresh(item)
    return item

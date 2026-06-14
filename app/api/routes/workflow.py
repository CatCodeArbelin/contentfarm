import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, status

from app.api.routes._helpers import now_utc
from app.api.routes.publications import _ITEMS as PUBLICATIONS
from app.api.routes.variants import _ITEMS as VARIANTS
from app.schemas.common import Status
from app.schemas.publications import ApprovalRequest, PublicationRead, PublishRequest
from app.schemas.variants import VariantRead

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Publications", "Variants"])

PublishableTarget = Literal["variant", "publication"]
_ALLOWED_PUBLISH_STATUSES = {Status.approved, Status.scheduled}


def _get_target(target_type: PublishableTarget, target_id: int) -> VariantRead | PublicationRead:
    collection = VARIANTS if target_type == "variant" else PUBLICATIONS
    for item in collection:
        if item.id == target_id:
            return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{target_type} not found")


@router.post("/approve", response_model=VariantRead | PublicationRead, summary="Approve a variant or publication")
def approve(payload: ApprovalRequest) -> VariantRead | PublicationRead:
    item = _get_target(payload.target_type, payload.target_id)
    approved_at = now_utc()
    updated = item.model_copy(update={"status": Status.approved, "approved_at": approved_at, "approved_by": payload.approved_by})
    collection = VARIANTS if payload.target_type == "variant" else PUBLICATIONS
    collection[item.id - 1] = updated
    return updated


@router.post("/publish", response_model=VariantRead | PublicationRead, summary="Publish an approved or scheduled variant/publication")
def publish(payload: PublishRequest) -> VariantRead | PublicationRead:
    item = _get_target(payload.target_type, payload.target_id)
    if item.status not in _ALLOWED_PUBLISH_STATUSES:
        logger.warning(
            "Publication attempt rejected because target is not approved: target_type=%s target_id=%s status=%s",
            payload.target_type,
            payload.target_id,
            item.status.value,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Target must be approved or scheduled before publishing.",
        )

    updates = {"status": Status.published, "published_at": now_utc()}
    if isinstance(item, PublicationRead) and payload.publication_url is not None:
        updates["url"] = payload.publication_url
    updated = item.model_copy(update=updates)
    collection = VARIANTS if payload.target_type == "variant" else PUBLICATIONS
    collection[item.id - 1] = updated
    return updated

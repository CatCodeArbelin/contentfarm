import hmac
import os
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session

from app.api.routes.publications import publish as publish_content
from app.api.routes.raw_items import create_rawitem
from app.api.routes.db_helpers import get_model_or_404
from app.db.session import get_db
from app.models.content import GeneratedVariant, Publication
from app.schemas.common import Status
from app.schemas.generation import GenerateResponse
from app.schemas.publications import PublicationRead, PublishRequest
from app.schemas.raw_items import RawItemCreate, RawItemRead
from app.schemas.variants import VariantRead
from app.services.generator import generate_variants_for_news_event

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class WebhookGenerateRequest(BaseModel):
    news_event_id: int
    strategy: str = Field(default="telegram_short", examples=["telegram_short"])
    language: str = Field(default="en", min_length=2, max_length=16)
    topic: str | None = None
    platform: str | None = Field(default=None, examples=["telegram"])
    prompt_id: int | None = None
    prompt_version: str | None = None


class ReviewNotifyRequest(BaseModel):
    target_type: Literal["variant", "publication"] = "variant"
    target_id: int
    admin_chat_id: str | None = Field(default=None, description="Optional Telegram admin chat id for n8n to use.")
    approve_command: str = "/approve"
    reject_command: str = "/reject"
    publish_command: str = "/publish"


class ReviewNotifyResponse(BaseModel):
    target_type: Literal["variant", "publication"]
    target_id: int
    admin_chat_id: str | None = None
    message: str
    parse_mode: Literal["HTML"] = "HTML"


class WebhookPublishRequest(BaseModel):
    target_type: Literal["variant", "publication"]
    target_id: int
    platform: str | None = Field(default=None, examples=["telegram", "max"])
    export_format: str | None = Field(default=None, pattern="^(markdown|html)$")
    publication_url: HttpUrl | None = None


def _configured_webhook_token() -> str:
    return os.getenv("WEBHOOK_API_TOKEN") or os.getenv("APP_SECRET_KEY") or ""


def validate_webhook_token(
    x_webhook_token: str | None = Header(default=None, alias="X-Webhook-Token"),
    authorization: str | None = Header(default=None),
) -> None:
    expected = _configured_webhook_token()
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Webhook token is not configured")

    supplied = x_webhook_token
    if supplied is None and authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            supplied = token

    if not supplied:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Webhook token is required")
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook token")


def _get_target(db: Session, target_type: Literal["variant", "publication"], target_id: int) -> GeneratedVariant | Publication:
    return get_model_or_404(db, GeneratedVariant if target_type == "variant" else Publication, target_id, target_type)


def _render_review_message(item: VariantRead | PublicationRead, request: ReviewNotifyRequest) -> str:
    header = f"Review required: {request.target_type} #{request.target_id}"
    item_status = item.status.value if hasattr(item.status, "value") else item.status
    status_line = f"Status: {item_status}"
    platform = getattr(item, "platform", None)
    strategy = getattr(item, "strategy", None)
    content = getattr(item, "content", None)
    preview = f"\n\nPreview:\n{content[:1000]}" if content else ""
    commands = (
        "\n\nCommands:\n"
        f"{request.approve_command} {request.target_id}\n"
        f"{request.reject_command} {request.target_id} <reason>\n"
        f"{request.publish_command} {request.target_id}"
    )
    meta = f"Platform: {platform or 'n/a'}\nStrategy: {strategy or 'n/a'}"
    return f"<b>{header}</b>\n{status_line}\n{meta}{preview}{commands}"


@router.post("/raw-item", response_model=RawItemRead, status_code=status.HTTP_201_CREATED, summary="Receive a raw item from n8n/RSS")
def receive_raw_item(payload: RawItemCreate, _: None = Depends(validate_webhook_token), db: Session = Depends(get_db)) -> RawItemRead:
    return create_rawitem(payload, db)


@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_201_CREATED, summary="Generate variants for a news event")
def generate_from_webhook(payload: WebhookGenerateRequest, _: None = Depends(validate_webhook_token), db: Session = Depends(get_db)) -> GenerateResponse:
    try:
        variants = generate_variants_for_news_event(db, payload.news_event_id)
    except ValueError as exc:
        db.rollback()
        message = str(exc)
        if "was not found" in message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=message) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Generation failed: {exc}") from exc
    return GenerateResponse(generated_variants=variants)


@router.post("/review-notify", response_model=ReviewNotifyResponse, summary="Prepare a Telegram admin review notification")
def prepare_review_notification(payload: ReviewNotifyRequest, _: None = Depends(validate_webhook_token), db: Session = Depends(get_db)) -> ReviewNotifyResponse:
    item = _get_target(db, payload.target_type, payload.target_id)
    return ReviewNotifyResponse(
        target_type=payload.target_type,
        target_id=payload.target_id,
        admin_chat_id=payload.admin_chat_id,
        message=_render_review_message(item, payload),
    )


@router.post("/publish", response_model=PublicationRead, summary="Publish an approved post")
def publish_from_webhook(payload: WebhookPublishRequest, _: None = Depends(validate_webhook_token), db: Session = Depends(get_db)) -> PublicationRead:
    if payload.target_type == "publication":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Publishing by publication target is not supported in MVP v0.1; use target_type=variant")

    item = get_model_or_404(db, GeneratedVariant, payload.target_id, "variant")
    if item.status != Status.approved.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only approved variants can be published")

    result = publish_content(
        PublishRequest(
            target_type=payload.target_type,
            target_id=payload.target_id,
            platform=payload.platform,
            export_format=payload.export_format,
            publication_url=payload.publication_url,
        ),
        db,
    )
    return result

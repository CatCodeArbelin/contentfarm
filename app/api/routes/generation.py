from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery, apply_filters, now_utc
from app.db.session import get_db
from app.schemas.common import ListFilters, PaginatedResponse, Status
from app.schemas.generation import GenerateRequest, GenerateResponse, GenerationRead, GenerationRequest
from app.services.generator import generate_variants_for_news_event

router = APIRouter(prefix="/generation", tags=["Generation"])
generate_router = APIRouter(tags=["Generation"])

_ITEMS: list[GenerationRead] = []


@router.get("", response_model=PaginatedResponse[GenerationRead], summary="List generation jobs")
def list_generation(
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
    status: StatusQuery = None,
    language: TextQuery = None,
    topic: TextQuery = None,
    platform: TextQuery = None,
    strategy: TextQuery = None,
    created_at: CreatedAtQuery = None,
) -> PaginatedResponse[GenerationRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = apply_filters(_ITEMS, filters, limit, offset)
    return PaginatedResponse[GenerationRead](items=items, limit=limit, offset=offset, total=total)


@router.post("", response_model=GenerationRead, status_code=status.HTTP_202_ACCEPTED, summary="Start generation")
def start_generation(payload: GenerationRequest) -> GenerationRead:
    item = GenerationRead(
        id=len(_ITEMS) + 1,
        news_event_id=payload.news_event_id,
        strategy=payload.strategy,
        language=payload.language,
        topic=payload.topic,
        platform=payload.platform,
        status=Status.processing,
        output=None,
        prompt_id=payload.prompt_id,
        prompt_version=payload.prompt_version,
        created_at=now_utc(),
    )
    _ITEMS.append(item)
    return item


@generate_router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_201_CREATED, summary="Generate variants for a news event")
def generate(payload: GenerateRequest, db: Session = Depends(get_db)) -> GenerateResponse:
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

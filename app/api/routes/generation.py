from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery
from app.api.routes.db_helpers import commit_or_rollback, get_model_or_404, list_models
from app.db.session import get_db
from app.models.content import Job
from app.schemas.common import ListFilters, PaginatedResponse, Status
from app.schemas.generation import GenerateRequest, GenerateResponse, GenerationRead, GenerationRequest
from app.services.generator import generate_variants_for_news_event

router = APIRouter(prefix="/generation", tags=["Generation"])
generate_router = APIRouter(tags=["Generation"])


def _job_to_read(job: Job) -> GenerationRead:
    payload = job.payload or {}
    return GenerationRead(
        id=job.id,
        news_event_id=payload.get("news_event_id"),
        strategy=job.strategy or payload.get("strategy"),
        language=job.language or payload.get("language") or "en",
        topic=job.topic,
        platform=job.platform,
        status=Status(job.status),
        output=payload.get("output"),
        prompt_id=payload.get("prompt_id"),
        prompt_version=payload.get("prompt_version"),
        created_at=job.created_at,
    )


@router.get("", response_model=PaginatedResponse[GenerationRead], summary="List generation jobs")
def list_generation(limit: LimitQuery = 50, offset: OffsetQuery = 0, status: StatusQuery = None, language: TextQuery = None, topic: TextQuery = None, platform: TextQuery = None, strategy: TextQuery = None, created_at: CreatedAtQuery = None, db: Session = Depends(get_db)) -> PaginatedResponse[GenerationRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = list_models(db, Job, filters, limit, offset)
    return PaginatedResponse[GenerationRead](items=[_job_to_read(item) for item in items], limit=limit, offset=offset, total=total)


@router.get("/{item_id}", response_model=GenerationRead, summary="Get generation job")
def get_generation(item_id: int, db: Session = Depends(get_db)) -> GenerationRead:
    return _job_to_read(get_model_or_404(db, Job, item_id, "Generation job"))


@router.post("", response_model=GenerationRead, status_code=status.HTTP_202_ACCEPTED, summary="Start generation")
def start_generation(payload: GenerationRequest, db: Session = Depends(get_db)) -> GenerationRead:
    job = Job(job_type="generation", payload=payload.model_dump(mode="json"), status=Status.processing.value, language=payload.language, topic=payload.topic, platform=payload.platform, strategy=payload.strategy)
    db.add(job)
    commit_or_rollback(db)
    db.refresh(job)
    return _job_to_read(job)


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

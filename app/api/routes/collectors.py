from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.collectors.runner import collect_active_sources
from app.db.session import get_db

router = APIRouter(prefix="/collectors", tags=["Collectors"])


@router.post("/run", status_code=status.HTTP_202_ACCEPTED, summary="Run collectors for active sources")
def run_collectors(db: Session = Depends(get_db)) -> dict[str, object]:
    return collect_active_sources(db)

from collections.abc import Sequence
from typing import Any, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.schemas.common import ListFilters

ModelT = TypeVar("ModelT")


def apply_db_filters(stmt: Select[tuple[ModelT]], model: type[ModelT], filters: ListFilters) -> Select[tuple[ModelT]]:
    for field in ("status", "language", "topic", "platform", "strategy"):
        expected = getattr(filters, field)
        if expected is not None and hasattr(model, field):
            value = expected.value if hasattr(expected, "value") else expected
            stmt = stmt.where(getattr(model, field) == value)
    if filters.created_at is not None and hasattr(model, "created_at"):
        stmt = stmt.where(getattr(model, "created_at") >= filters.created_at)
    if filters.min_score is not None and hasattr(model, "score"):
        stmt = stmt.where(getattr(model, "score") >= filters.min_score)
    if filters.max_score is not None and hasattr(model, "score"):
        stmt = stmt.where(getattr(model, "score") <= filters.max_score)
    return stmt


def list_models(session: Session, model: type[ModelT], filters: ListFilters, limit: int, offset: int) -> tuple[Sequence[ModelT], int]:
    filtered = apply_db_filters(select(model), model, filters)
    total = session.scalar(select(func.count()).select_from(filtered.order_by(None).subquery())) or 0
    order_field = getattr(model, filters.sort_by, getattr(model, "created_at"))
    if filters.sort_order == "desc":
        order_field = order_field.desc()
    return session.scalars(filtered.order_by(order_field).limit(limit).offset(offset)).all(), total


def get_model_or_404(session: Session, model: type[ModelT], item_id: int, label: str) -> ModelT:
    item = session.get(model, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return item


def commit_or_rollback(session: Session, *, detail: str = "Database operation failed") -> None:
    try:
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc


def enum_dump(payload: Any, *, exclude_unset: bool = False) -> dict[str, Any]:
    return payload.model_dump(exclude_unset=exclude_unset, mode="json")

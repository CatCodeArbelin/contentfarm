from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.gdelt import collect_gdelt
from app.collectors.rss import collect_rss
from app.models.content import Source


def collect_source(db: Session, source: Source) -> dict[str, int | str]:
    platform = source.platform.lower()
    if platform in {"rss", "atom", "feed"}:
        result = collect_rss(db, source)
    elif platform == "gdelt":
        result = collect_gdelt(db, source)
    else:
        return {"source_id": source.id, "source": source.name, "platform": source.platform, "created": 0, "updated": 0, "total": 0, "status": "skipped"}
    return {"source_id": source.id, "source": source.name, "platform": source.platform, "status": "collected", **result}


def collect_active_sources(db: Session) -> dict[str, object]:
    sources = db.scalars(select(Source).where(Source.status == "active")).all()
    results = [collect_source(db, source) for source in sources]
    return {
        "sources": len(results),
        "created": sum(int(item.get("created", 0)) for item in results),
        "updated": sum(int(item.get("updated", 0)) for item in results),
        "items": sum(int(item.get("total", 0)) for item in results),
        "results": results,
    }

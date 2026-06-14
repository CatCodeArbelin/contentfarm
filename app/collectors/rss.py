from __future__ import annotations

from typing import Any

import feedparser
from sqlalchemy.orm import Session

from app.collectors.utils import upsert_raw_item
from app.models.content import Source


def collect_rss(db: Session, source: Source) -> dict[str, int]:
    """Collect title, link, summary, published and source from an RSS/Atom feed."""
    feed = feedparser.parse(source.source_url)
    created = updated = 0
    for entry in feed.entries:
        link = getattr(entry, "link", None)
        if not link:
            continue
        metadata: dict[str, Any] = {
            "collector": "rss",
            "source": source.name,
            "feed_url": source.source_url,
            "entry_id": getattr(entry, "id", None),
            "authors": getattr(entry, "authors", None),
            "tags": [tag.get("term") for tag in getattr(entry, "tags", []) if isinstance(tag, dict)],
        }
        _, was_created = upsert_raw_item(
            db,
            source=source,
            title=getattr(entry, "title", ""),
            link=link,
            summary=getattr(entry, "summary", ""),
            published=getattr(entry, "published", None) or getattr(entry, "updated", None),
            metadata=metadata,
        )
        created += int(was_created)
        updated += int(not was_created)
    db.commit()
    return {"created": created, "updated": updated, "total": created + updated}

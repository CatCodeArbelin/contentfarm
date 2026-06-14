from __future__ import annotations

import time
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.collectors.utils import parse_datetime, upsert_raw_item
from app.models.content import Source

DEFAULT_GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"


class RateLimiter:
    def __init__(self, requests_per_second: float = 1.0) -> None:
        self.min_interval = 1.0 / max(requests_per_second, 0.1)
        self._last_request = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request = time.monotonic()


class GdeltClient:
    def __init__(self, *, timeout: float = 20.0, retries: int = 3, requests_per_second: float = 1.0) -> None:
        self.retries = retries
        self.rate_limiter = RateLimiter(requests_per_second)
        self.client = httpx.Client(timeout=timeout, headers={"User-Agent": "contentfarm/0.1"})

    def fetch_articles(self, query: str, *, max_records: int = 50) -> list[dict[str, Any]]:
        params = {"query": query, "mode": "artlist", "format": "json", "maxrecords": max_records, "sort": "hybridrel"}
        for attempt in range(self.retries):
            self.rate_limiter.wait()
            try:
                response = self.client.get(DEFAULT_GDELT_DOC_API, params=params)
                response.raise_for_status()
                payload = response.json()
                return list(payload.get("articles", []))
            except (httpx.HTTPError, ValueError):
                if attempt >= self.retries - 1:
                    raise
                time.sleep(2**attempt)
        return []

    def close(self) -> None:
        self.client.close()


def _query_for_source(source: Source) -> str:
    if source.source_url.startswith("gdelt://"):
        return source.source_url.removeprefix("gdelt://")
    return source.topic or source.name


def collect_gdelt(db: Session, source: Source, *, client: GdeltClient | None = None, max_records: int = 50) -> dict[str, int]:
    owns_client = client is None
    client = client or GdeltClient()
    created = updated = 0
    try:
        for article in client.fetch_articles(_query_for_source(source), max_records=max_records):
            link = article.get("url")
            if not link:
                continue
            metadata = {"collector": "gdelt", "source": source.name, "gdelt": article}
            _, was_created = upsert_raw_item(
                db,
                source=source,
                title=article.get("title") or link,
                link=link,
                summary=article.get("seendate") or "",
                published=parse_datetime(article.get("seendate")),
                metadata=metadata,
            )
            created += int(was_created)
            updated += int(not was_created)
        db.commit()
        return {"created": created, "updated": updated, "total": created + updated}
    finally:
        if owns_client:
            client.close()

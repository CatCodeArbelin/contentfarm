from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content import RawItem, Source

_TRACKING_PREFIXES = ("utm_",)
_TRACKING_PARAMS = {"fbclid", "gclid", "dclid", "yclid", "mc_cid", "mc_eid", "igshid"}


def normalize_url(url: str) -> str:
    """Return a canonical URL suitable for duplicate detection."""
    parts = urlsplit(str(url).strip())
    scheme = (parts.scheme or "https").lower()
    netloc = parts.netloc.lower()
    if (scheme == "http" and netloc.endswith(":80")) or (scheme == "https" and netloc.endswith(":443")):
        netloc = netloc.rsplit(":", 1)[0]
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in _TRACKING_PARAMS and not key.lower().startswith(_TRACKING_PREFIXES)
    ]
    query = urlencode(sorted(query_pairs), doseq=True)
    return urlunsplit((scheme, netloc, path, query, ""))


def url_hash(url: str) -> str:
    return hashlib.sha256(normalize_url(url).encode("utf-8")).hexdigest()


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value.strip():
        try:
            parsed = parsedate_to_datetime(value)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError, IndexError):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                return None
    return None


def upsert_raw_item(
    db: Session,
    *,
    source: Source,
    title: str,
    link: str,
    summary: str = "",
    published: datetime | str | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[RawItem, bool]:
    normalized = normalize_url(link)
    digest = url_hash(normalized)
    existing = db.scalar(select(RawItem).where(RawItem.url_hash == digest))
    values = {
        "source_id": source.id,
        "title": (title or normalized)[:500],
        "source_url": normalized,
        "url_hash": digest,
        "content": summary or "",
        "language": source.language,
        "topic": source.topic,
        "platform": source.platform,
        "strategy": source.strategy,
        "risk_level": source.risk_level,
        "published_at": parse_datetime(published),
        "raw_metadata": metadata or {},
    }
    if existing:
        for key, value in values.items():
            setattr(existing, key, value)
        return existing, False
    item = RawItem(**values)
    db.add(item)
    return item, True

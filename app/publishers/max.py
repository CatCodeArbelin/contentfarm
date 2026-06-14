from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MaxPublishResult:
    status: str = "failed"
    message_id: str | None = None
    publication_url: str | None = None
    error: str | None = "MAX publisher adapter is disabled by default"


class MaxPublisher:
    enabled = False

    def publish(self, content: str) -> MaxPublishResult:
        return MaxPublishResult()

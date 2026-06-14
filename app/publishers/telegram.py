from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class TelegramPublishResult:
    status: str
    message_id: str | None = None
    publication_url: str | None = None
    error: str | None = None


class TelegramPublisher:
    def __init__(self, *, bot_token: str | None = None, channel_id: str | None = None) -> None:
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.channel_id = channel_id or os.getenv("TELEGRAM_CHANNEL_ID")

    def publish(self, content: str) -> TelegramPublishResult:
        if not self.bot_token or not self.channel_id:
            return TelegramPublishResult(status="failed", error="TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID are required")

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            response = httpx.post(url, json={"chat_id": self.channel_id, "text": content}, timeout=20.0)
            response.raise_for_status()
            payload = response.json()
            if not payload.get("ok"):
                return TelegramPublishResult(status="failed", error=str(payload.get("description") or "Telegram API returned ok=false"))
            message = payload.get("result", {})
            message_id = str(message.get("message_id")) if message.get("message_id") is not None else None
            publication_url = None
            if str(self.channel_id).startswith("@") and message_id:
                publication_url = f"https://t.me/{str(self.channel_id).lstrip('@')}/{message_id}"
            return TelegramPublishResult(status="published", message_id=message_id, publication_url=publication_url)
        except Exception as exc:  # network/API errors are persisted in publication.error
            return TelegramPublishResult(status="failed", error=str(exc))

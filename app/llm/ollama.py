"""Ollama client for generating content variants.

The client reads its default connection settings from environment variables
loaded by the application runtime or from a local ``.env`` file during local
execution:

- ``OLLAMA_BASE_URL`` (default: ``http://localhost:11434``)
- ``OLLAMA_MODEL`` (default: ``llama3.1``)
- ``OLLAMA_TIMEOUT_SECONDS`` (default: ``60``)
- ``OLLAMA_RETRIES`` (default: ``2``)
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

import httpx

from app.prompts.engine import PromptEngine, PromptError, PromptType

logger = logging.getLogger("contentfarm.llm.ollama")

TaskName = Literal["summarize", "localize_ru", "humanize", "platform_adapt"]


class LLMGenerationError(RuntimeError):
    """Raised when Ollama cannot produce a valid generation."""


@dataclass(slots=True)
class OllamaGenerationResult:
    """Structured LLM result ready to map into ``generated_variants`` rows."""

    content: str
    model: str
    task: TaskName
    language: str
    platform: str
    strategy: str
    prompt: str
    source_text: str
    prompt_version: str | None = None
    score: float = 0.0
    risk_level: str = "low"
    provider: str = "ollama"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_generated_variant(self, news_event_id: int, prompt_id: int | None = None) -> dict[str, Any]:
        """Return fields that can be passed to ``GeneratedVariant(**fields)``."""
        return {
            "news_event_id": news_event_id,
            "prompt_id": prompt_id,
            "prompt_version": self.prompt_version,
            "content": self.content,
            "language": self.language,
            "platform": self.platform,
            "strategy": self.strategy,
            "score": self.score,
            "risk_level": self.risk_level,
        }

    def model_dump(self) -> dict[str, Any]:
        """Return a serializable representation for APIs, jobs, or logs."""
        return asdict(self)


class OllamaClient:
    """Small synchronous wrapper around the Ollama ``/api/generate`` endpoint."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        retries: int | None = None,
        prompt_engine: PromptEngine | None = None,
    ) -> None:
        _load_dotenv_if_needed()
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL") or "llama3.1"
        self.timeout = timeout if timeout is not None else _env_float("OLLAMA_TIMEOUT_SECONDS", 60.0)
        self.retries = retries if retries is not None else _env_int("OLLAMA_RETRIES", 2)
        self.prompt_engine = prompt_engine or PromptEngine()

    def summarize(
        self, text: str, *, language: str = "en", platform: str = "generic", strategy: str = "summary"
    ) -> OllamaGenerationResult:
        prompt, prompt_version = self._build_prompt(
            "topic_strategy",
            fallback=(
                "Summarize the source material into a concise, factual draft. "
                "Keep the key facts, avoid unsupported claims, and return only the draft text.\n\n"
                f"Source material:\n{text}"
            ),
            context={"text": text, "topic": strategy},
            language=language,
            platform=platform,
            strategy=strategy,
        )
        return self._generate_result("summarize", prompt, text, language=language, platform=platform, strategy=strategy, prompt_version=prompt_version)

    def localize_ru(
        self, text: str, *, platform: str = "generic", strategy: str = "localize_ru"
    ) -> OllamaGenerationResult:
        prompt, prompt_version = self._build_prompt(
            "global_humanizer",
            fallback=(
                "Translate and localize the text for a Russian-speaking audience. "
                "Use natural Russian, preserve names and facts, and return only the localized text.\n\n"
                f"Text:\n{text}"
            ),
            context={"text": text},
            language="ru",
            platform=platform,
            strategy=strategy,
        )
        return self._generate_result("localize_ru", prompt, text, language="ru", platform=platform, strategy=strategy, prompt_version=prompt_version)

    def humanize(
        self, text: str, *, language: str = "ru", platform: str = "generic", strategy: str = "humanize"
    ) -> OllamaGenerationResult:
        prompt, prompt_version = self._build_prompt(
            "global_humanizer",
            fallback=(
                "Rewrite the text so it sounds natural, clear, and human-written. "
                "Keep the meaning and facts unchanged, remove robotic phrasing, and return only the rewritten text.\n\n"
                f"Text:\n{text}"
            ),
            context={"text": text},
            language=language,
            platform=platform,
            strategy=strategy,
        )
        return self._generate_result("humanize", prompt, text, language=language, platform=platform, strategy=strategy, prompt_version=prompt_version)

    def platform_adapt(
        self,
        text: str,
        *,
        platform: str,
        language: str = "ru",
        strategy: str = "platform_adapt",
    ) -> OllamaGenerationResult:
        prompt, prompt_version = self._build_prompt(
            "platform_style",
            fallback=(
                f"Adapt the text for publication on {platform}. Match the platform style, length, and formatting. "
                "Keep facts intact, avoid clickbait, and return only the adapted post.\n\n"
                f"Text:\n{text}"
            ),
            context={"text": text, "platform": platform},
            language=language,
            platform=platform,
            strategy=strategy,
        )
        return self._generate_result("platform_adapt", prompt, text, language=language, platform=platform, strategy=strategy, prompt_version=prompt_version)

    def _generate_result(
        self,
        task: TaskName,
        prompt: str,
        source_text: str,
        *,
        language: str,
        platform: str,
        strategy: str,
        prompt_version: str | None = None,
    ) -> OllamaGenerationResult:
        response = self._request(prompt, task=task)
        content = str(response.get("response", "")).strip()
        if not content:
            self._log_failure(task, "Ollama returned an empty response", payload=response)
            raise LLMGenerationError("Ollama returned an empty response")

        return OllamaGenerationResult(
            content=content,
            model=self.model,
            task=task,
            language=language,
            platform=platform,
            strategy=strategy,
            prompt=prompt,
            source_text=source_text,
            prompt_version=prompt_version,
            metadata={
                "done": response.get("done"),
                "total_duration": response.get("total_duration"),
                "load_duration": response.get("load_duration"),
                "prompt_eval_count": response.get("prompt_eval_count"),
                "eval_count": response.get("eval_count"),
            },
        )


    def _build_prompt(
        self,
        prompt_type: PromptType,
        *,
        fallback: str,
        context: dict[str, Any],
        language: str,
        platform: str,
        strategy: str,
    ) -> tuple[str, str | None]:
        try:
            prompt = self.prompt_engine.get_active(
                prompt_type=prompt_type,
                language=language,
                platform=platform,
                strategy=strategy,
            )
            return self.prompt_engine.render(prompt, **context), prompt.version
        except PromptError:
            logger.info(
                "Falling back to built-in prompt",
                extra={"prompt_type": prompt_type, "language": language, "platform": platform, "strategy": strategy},
            )
            return fallback, None

    def _request(self, prompt: str, *, task: TaskName) -> dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        last_error: Exception | None = None

        for attempt in range(self.retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    if not isinstance(data, dict):
                        raise LLMGenerationError("Ollama returned a non-object JSON response")
                    return data
            except (httpx.HTTPError, ValueError, LLMGenerationError) as exc:
                last_error = exc
                self._log_failure(task, f"Ollama request failed on attempt {attempt + 1}: {exc}")
                if attempt < self.retries:
                    time.sleep(min(2**attempt, 10))

        raise LLMGenerationError(f"Ollama request failed after {self.retries + 1} attempts: {last_error}") from last_error

    def _log_failure(self, task: TaskName, message: str, *, payload: dict[str, Any] | None = None) -> None:
        logger.error(
            message,
            extra={
                "provider": "ollama",
                "task": task,
                "model": self.model,
                "base_url": self.base_url,
                "payload": payload,
            },
        )


def _load_dotenv_if_needed(path: str | os.PathLike[str] = ".env") -> None:
    """Load simple KEY=VALUE pairs from .env without overriding real env vars."""
    dotenv_path = Path(path)
    if not dotenv_path.exists():
        return
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default

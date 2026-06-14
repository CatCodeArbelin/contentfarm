"""Prompt template loading and rendering utilities.

Prompt definitions are versioned records stored as YAML or JSON files under the
repository-level ``prompts/`` directory by default. Each file describes a single
Jinja2 template and can later be mirrored into the database ``prompts`` table.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import yaml
from jinja2 import Environment, StrictUndefined, TemplateError

PromptType = Literal["global_humanizer", "platform_style", "topic_strategy", "output_schema"]


class PromptError(RuntimeError):
    """Raised when a prompt cannot be loaded or rendered."""


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    """Versioned prompt template ready for Jinja2 rendering."""

    name: str
    prompt_type: PromptType
    version: str
    template: str
    is_active: bool
    created_at: datetime
    language: str = "en"
    platform: str = "generic"
    strategy: str = "generic"
    topic: str | None = None
    source_path: Path | None = None

    @classmethod
    def from_mapping(cls, data: dict[str, Any], *, source_path: Path | None = None) -> "PromptTemplate":
        """Build a prompt from a JSON/YAML mapping and validate required fields."""
        missing = [field for field in ("name", "prompt_type", "version", "template") if not data.get(field)]
        if missing:
            location = f" in {source_path}" if source_path else ""
            raise PromptError(f"Prompt definition{location} is missing required fields: {', '.join(missing)}")

        prompt_type = data["prompt_type"]
        if prompt_type not in {"global_humanizer", "platform_style", "topic_strategy", "output_schema"}:
            raise PromptError(f"Unsupported prompt_type {prompt_type!r}")

        return cls(
            name=str(data["name"]),
            prompt_type=prompt_type,
            version=str(data["version"]),
            template=str(data["template"]),
            is_active=bool(data.get("is_active", True)),
            created_at=_parse_created_at(data.get("created_at")),
            language=str(data.get("language") or "en"),
            platform=str(data.get("platform") or "generic"),
            strategy=str(data.get("strategy") or "generic"),
            topic=str(data["topic"]) if data.get("topic") is not None else None,
            source_path=source_path,
        )

    def render(self, **context: Any) -> str:
        """Render the prompt with strict Jinja2 variable checking."""
        return PromptEngine().render_template(self.template, context)


class PromptEngine:
    """Load versioned prompt definitions and render Jinja2 templates."""

    def __init__(self, prompts_dir: str | Path = "prompts") -> None:
        self.prompts_dir = Path(prompts_dir)
        self.environment = Environment(autoescape=False, undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)

    def render_template(self, template: str, context: dict[str, Any] | None = None) -> str:
        """Render an arbitrary Jinja2 template string."""
        try:
            return self.environment.from_string(template).render(context or {}).strip()
        except TemplateError as exc:
            raise PromptError(f"Prompt rendering failed: {exc}") from exc

    def render(self, prompt: PromptTemplate, **context: Any) -> str:
        """Render a loaded prompt template."""
        return self.render_template(prompt.template, context)

    def load(self, path: str | Path) -> PromptTemplate:
        """Load a single prompt definition from a YAML or JSON file."""
        prompt_path = Path(path)
        if not prompt_path.is_absolute():
            prompt_path = self.prompts_dir / prompt_path
        data = self._read_mapping(prompt_path)
        return PromptTemplate.from_mapping(data, source_path=prompt_path)

    def load_all(self) -> list[PromptTemplate]:
        """Load all YAML and JSON prompt files from the configured directory."""
        if not self.prompts_dir.exists():
            return []
        prompts = [self.load(path) for path in sorted(self.prompts_dir.iterdir()) if path.suffix.lower() in {".yaml", ".yml", ".json"}]
        return prompts

    def get_active(
        self,
        *,
        name: str | None = None,
        prompt_type: PromptType | None = None,
        platform: str | None = None,
        strategy: str | None = None,
        language: str | None = None,
    ) -> PromptTemplate:
        """Return the newest active prompt matching the supplied filters."""
        candidates = [prompt for prompt in self.load_all() if prompt.is_active]
        if name is not None:
            candidates = [prompt for prompt in candidates if prompt.name == name]
        if prompt_type is not None:
            candidates = [prompt for prompt in candidates if prompt.prompt_type == prompt_type]
        if platform is not None:
            candidates = [prompt for prompt in candidates if prompt.platform in {platform, "generic"}]
        if strategy is not None:
            candidates = [prompt for prompt in candidates if prompt.strategy in {strategy, "generic"}]
        if language is not None:
            candidates = [prompt for prompt in candidates if prompt.language == language]
        if not candidates:
            raise PromptError("No active prompt matched the requested filters")
        return max(candidates, key=lambda prompt: prompt.created_at)

    def _read_mapping(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise PromptError(f"Prompt file does not exist: {path}")
        raw = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            data = json.loads(raw)
        elif path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(raw)
        else:
            raise PromptError(f"Unsupported prompt file type: {path.suffix}")
        if not isinstance(data, dict):
            raise PromptError(f"Prompt file must contain an object mapping: {path}")
        return data


def _parse_created_at(value: Any) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    raise PromptError("created_at must be an ISO datetime string")

from __future__ import annotations

from pathlib import Path
import re

SUPPORTED_PLATFORMS = {"dzen", "vc.ru", "habr", "dtf", "pikabu"}


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9а-яё]+", "-", value, flags=re.IGNORECASE)
    return value.strip("-") or "publication"


def render_markdown(*, title: str | None, content: str, platform: str) -> str:
    if platform not in SUPPORTED_PLATFORMS:
        raise ValueError(f"Markdown export is not configured for platform: {platform}")
    parts: list[str] = []
    if title:
        parts.append(f"# {title.strip()}")
    parts.append(content.strip())
    return "\n\n".join(parts).strip() + "\n"


def export_markdown(*, title: str | None, content: str, platform: str, output_dir: str | Path = "exports") -> str:
    output_root = Path(output_dir) / platform / "markdown"
    output_root.mkdir(parents=True, exist_ok=True)
    filename = f"{slugify(title or content[:80])}.md"
    path = output_root / filename
    path.write_text(render_markdown(title=title, content=content, platform=platform), encoding="utf-8")
    return str(path)

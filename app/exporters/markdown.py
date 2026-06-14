from __future__ import annotations

import hashlib
from pathlib import Path
import re
import unicodedata

SUPPORTED_PLATFORMS = {"telegram", "dzen", "max", "vc", "habr", "dtf", "pikabu"}

CYRILLIC_TRANSLITERATION = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def _transliterate(value: str) -> str:
    return "".join(CYRILLIC_TRANSLITERATION.get(char, char) for char in value.lower())


def slugify(value: str) -> str:
    original = value.strip()
    value = _transliterate(original)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", "-", value.lower())
    value = re.sub(r"-{2,}", "-", value).strip("-")
    if value:
        return value[:120].strip("-") or value
    digest = hashlib.sha256(original.encode("utf-8")).hexdigest()[:12]
    return f"publication-{digest}"


def export_filename(value: str, extension: str) -> str:
    return f"{slugify(value)}.{extension.lstrip('.')}"


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
    filename = export_filename(title or content[:80], "md")
    path = output_root / filename
    path.write_text(render_markdown(title=title, content=content, platform=platform), encoding="utf-8")
    return str(path)

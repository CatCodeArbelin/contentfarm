from __future__ import annotations

from html import escape
from pathlib import Path

from app.exporters.markdown import SUPPORTED_PLATFORMS, slugify


def render_html(*, title: str | None, content: str, platform: str) -> str:
    if platform not in SUPPORTED_PLATFORMS:
        raise ValueError(f"HTML export is not configured for platform: {platform}")
    body = "\n".join(f"<p>{escape(paragraph)}</p>" for paragraph in content.strip().split("\n\n") if paragraph.strip())
    heading = f"<h1>{escape(title.strip())}</h1>\n" if title else ""
    page_title = escape(title or "Publication export")
    return f"<!doctype html>\n<html lang=\"ru\">\n<head><meta charset=\"utf-8\"><title>{page_title}</title></head>\n<body>\n{heading}{body}\n</body>\n</html>\n"


def export_html(*, title: str | None, content: str, platform: str, output_dir: str | Path = "exports") -> str:
    output_root = Path(output_dir) / platform / "html"
    output_root.mkdir(parents=True, exist_ok=True)
    filename = f"{slugify(title or content[:80])}.html"
    path = output_root / filename
    path.write_text(render_html(title=title, content=content, platform=platform), encoding="utf-8")
    return str(path)

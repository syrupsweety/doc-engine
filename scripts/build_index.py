#!/usr/bin/env python3
"""Build the GitHub Pages landing page listing downloadable artifacts."""

import argparse
import html
import os
from datetime import UTC, datetime
from pathlib import Path

import yaml

SUFFIXES = {".pdf": "PDF", ".docx": "DOCX", ".html": "HTML"}


def human_size(size: int) -> str:
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "Б" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} ТБ"


def document_title(markdown: Path) -> str:
    text = markdown.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return markdown.stem
    front = text.split("---", 2)
    if len(front) < 3:
        return markdown.stem
    meta = yaml.safe_load(front[1]) or {}
    return str(meta.get("title") or markdown.stem)


def build(source: Path, site: Path, markdown: Path, profile: str) -> Path:
    files = sorted(path for path in source.iterdir() if path.suffix in SUFFIXES and path.is_file())
    if not files:
        raise SystemExit(f"no artifacts in {source}")

    revision = os.environ.get("GITHUB_SHA", "")[:7]
    stamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    meta = " · ".join(filter(None, [f"профиль {profile}", f"сборка {stamp}", f"коммит {revision}"]))

    items = "\n".join(
        f'      <li><a href="{path.name}" download>'
        f'<span class="kind">{SUFFIXES[path.suffix]}</span>'
        f'<span class="name">{html.escape(path.name)}</span>'
        f'<span class="size">{human_size(path.stat().st_size)}</span></a></li>'
        for path in files
    )
    preview = next((p.name for p in files if p.suffix == ".html"), None)
    preview_link = (
        f'\n    <p class="preview"><a href="{preview}">Открыть HTML-версию в браузере</a></p>'
        if preview
        else ""
    )

    page = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(document_title(markdown))}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ margin: 0; font: 16px/1.55 -apple-system, "Segoe UI", Roboto, sans-serif;
         background: #f6f7f9; color: #1d2129; }}
  main {{ max-width: 720px; margin: 0 auto; padding: 56px 24px 64px; }}
  h1 {{ font-size: 1.55rem; line-height: 1.3; margin: 0 0 8px; }}
  .meta {{ color: #6b7280; font-size: .85rem; margin: 0 0 28px; }}
  ul {{ list-style: none; margin: 0; padding: 0; }}
  li + li {{ margin-top: 10px; }}
  li a {{ display: flex; align-items: baseline; gap: 12px; padding: 14px 16px;
          background: #fff; border: 1px solid #e3e6ea; border-radius: 10px;
          text-decoration: none; color: inherit; }}
  li a:hover {{ border-color: #4c8bf5; }}
  .kind {{ font-size: .72rem; font-weight: 700; letter-spacing: .06em;
           color: #4c8bf5; min-width: 42px; }}
  .name {{ flex: 1; font-variant-numeric: tabular-nums; }}
  .size {{ color: #6b7280; font-size: .85rem; }}
  .preview {{ margin-top: 26px; font-size: .92rem; }}
  .preview a {{ color: #2563eb; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #14161a; color: #e6e8eb; }}
    li a {{ background: #1b1e24; border-color: #2a2f37; }}
    .size, .meta {{ color: #9aa1ab; }}
  }}
</style>
</head>
<body>
  <main>
    <h1>{html.escape(document_title(markdown))}</h1>
    <p class="meta">{html.escape(meta)}</p>
    <ul>
{items}
    </ul>{preview_link}
  </main>
</body>
</html>
"""
    target = site / "index.html"
    target.write_text(page, encoding="utf-8")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("output/example"))
    parser.add_argument("--site", type=Path, default=Path("site"))
    parser.add_argument("--input", type=Path, default=Path("docs/example/manuscript.md"))
    parser.add_argument("--profile", default="gost-7.32")
    args = parser.parse_args()

    args.site.mkdir(parents=True, exist_ok=True)
    target = build(args.source, args.site, args.input, args.profile)
    print(f"index: {target}")


if __name__ == "__main__":
    main()

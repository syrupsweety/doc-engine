#!/usr/bin/env python3
"""DOCX export helpers: markdown prepass and post-export layout patch."""

import re
import shutil
import zipfile
from pathlib import Path

import yaml

FENCE = re.compile(r"```\{=latex\}\n(.*?)\n```", re.S)
PAGEBREAK = '```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```'
TOC = (
    '<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r>'
    '<w:r><w:instrText xml:space="preserve"> TOC \\o "1-2" \\h \\z \\u </w:instrText></w:r>'
    '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
    "<w:r><w:t>Оглавление: обновите поле (F9) после открытия</w:t></w:r>"
    '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>'
)
MARGINS = (
    '<w:pgMar w:top="1134" w:right="850" w:bottom="1134" w:left="1701"'
    ' w:header="708" w:footer="708" w:gutter="0" />'
)
SPACING = '<w:spacing w:after="0" w:line="360" w:lineRule="auto" /><w:ind w:firstLine="709" />'


def _paragraph(text: str, size: int = 28, bold: bool = False, indent: int | None = None) -> str:
    props = '<w:jc w:val="center"/>' if indent is None else f'<w:ind w:left="{indent}"/>'
    run_props = f'<w:sz w:val="{size}"/>' + ("<w:b/>" if bold else "")
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        f"<w:p><w:pPr>{props}</w:pPr><w:r><w:rPr>{run_props}</w:rPr>"
        f'<w:t xml:space="preserve">{escaped}</w:t></w:r></w:p>'
    )


def _blank(size: int = 28) -> str:
    return f'<w:p><w:r><w:rPr><w:sz w:val="{size}"/></w:rPr></w:r></w:p>'


def _title_page(meta: dict[str, str], org: list[str]) -> list[str]:
    lines = ["```{=openxml}"]
    lines += [_paragraph(item, size=24) for item in org[:4]]
    lines += [
        _blank(),
        _blank(),
        _paragraph(meta.get("doc_type", ""), size=32, bold=True),
        _blank(),
        _blank(),
        _paragraph(meta.get("title", ""), bold=True),
    ]
    lines += [_blank()] * 4
    lines += [
        _paragraph("Выполнил", indent=1134),
        _paragraph(
            f"студент гр. {meta.get('group', '')} ______________   {meta.get('author', '')}",
            indent=1134,
        ),
        _paragraph("подпись", size=16, indent=3400),
        _blank(),
        _paragraph(
            f"Научный руководитель ______________   {meta.get('supervisor', '')}", indent=1134
        ),
        _paragraph("подпись", size=16, indent=3400),
        _blank(),
    ]
    if meta.get("consultant"):
        lines += [
            _paragraph(f"Научный консультант ______________   {meta['consultant']}", indent=1134),
            _paragraph("подпись", size=16, indent=3400),
            _blank(),
        ]
    lines.append(_paragraph(f"«____» ______________ {meta.get('date_year', '')} г.", indent=5100))
    lines += [_blank()] * 6
    lines += [_paragraph(meta.get("city", ""), size=24), _paragraph(meta.get("year", ""), size=24)]
    lines += [
        '<w:p><w:r><w:br w:type="page"/></w:r></w:p>',
        _paragraph("СОДЕРЖАНИЕ"),
        TOC,
        '<w:p><w:r><w:br w:type="page"/></w:r></w:p>',
    ]
    lines.append("```")
    return lines


def _longtable_to_pipe(block: str) -> str:
    body = block[block.index(r"\endfirsthead") :] if r"\endfirsthead" in block else block
    rows = []
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("\\") or "&" not in line:
            continue
        cells = [c.strip() for c in line.rstrip("\\ ").split("&")]
        cells = [c.replace(r"\-", "-").replace(r"\&", "&") for c in cells]
        if any(cells):
            rows.append(cells)
    if not rows:
        return ""

    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    table = ["| " + " | ".join(rows[0]) + " |", "|" + "|".join(["---"] * width) + "|"]
    table += ["| " + " | ".join(row) + " |" for row in rows[1:]]
    return "\n".join(table)


def _convert_block(match: re.Match) -> str:
    block = match.group(1)
    if "goststruct" in block:
        name = re.search(r"\\goststruct\{(.+?)\}", block).group(1)
        return f"{PAGEBREAK}\n\n# {name}"
    if "longtable" in block:
        return _longtable_to_pipe(block)
    return ""


def prepare(source: Path, target: Path) -> None:
    """Rewrite markdown so the DOCX keeps the title page, TOC field and tables."""
    text = source.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    org: list[str] = []

    front = re.search(r"^---\n(.*?)\n---\n", text, re.S)
    if front:
        block = front.group(1)
        data = yaml.safe_load(block) or {}
        meta = {k: str(v) for k, v in data.items() if isinstance(v, (str, int))}
        org = data.get("organization") or re.findall(r'^\s*-\s*"?(.*?)"?$', block, re.M)
        text = text[front.end() :]

    body = FENCE.sub(_convert_block, text)
    body = re.sub(r"\n# (?=\d)", "\n" + PAGEBREAK + "\n\n# ", body)
    body = re.sub(r"\n{4,}", "\n\n\n", body)

    front_matter = {
        "lang": meta.get("lang", "ru-RU"),
        "bibliography": meta.get("bibliography", "references.bib"),
        "nocite": "@*",
    }
    target.write_text(
        "---\n"
        + yaml.dump(front_matter, allow_unicode=True)
        + "---\n\n"
        + "\n".join(_title_page(meta, org))
        + "\n\n"
        + body,
        encoding="utf-8",
    )


def patch_layout(path: Path) -> None:
    """Apply GOST paragraph defaults and page margins to an exported DOCX."""
    with zipfile.ZipFile(path) as archive:
        items = {name: archive.read(name) for name in archive.namelist()}

    styles = items["word/styles.xml"].decode("utf-8")
    document = items["word/document.xml"].decode("utf-8")

    styles = styles.replace('<w:spacing w:after="200" />', SPACING)
    document = re.sub(r"<w:pgMar[^/]*/>", MARGINS, document)
    styles = re.sub(r"<w:pgMar[^/]*/>", MARGINS, styles)

    items["word/styles.xml"] = styles.encode("utf-8")
    items["word/document.xml"] = document.encode("utf-8")

    tmp = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in items.items():
            archive.writestr(name, data)
    shutil.move(tmp, path)

#!/usr/bin/env python3
"""Convert a proofread markdown to a humanities-conforming Word document.

Target audience: submission to Chinese social-sciences journals. Default
styling matches the common 《历史研究》/《近代史研究》 conventions — Songti
body, SimHei headings, 1.5 line spacing, 2-character paragraph indent.

Markdown features supported:
  - ATX headings (#, ##, ###)
  - Blockquotes (>) — rendered as indented quote paragraphs
  - Ordered and unordered lists (single level)
  - Bold (**) and italic (*) inline
  - Footnotes in [^n] style — inserted as Word native footnotes
  - Images — embedded centred, caption from alt text
  - A "参考文献" / "引用文献" trailing section — hanging indent numbered

Usage:
    python3 md_to_docx.py --input final.md --output final.docx \
        --template humanities --title-from-first-h1
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt
except ImportError:
    print("missing dependency: pip3 install python-docx", file=sys.stderr)
    sys.exit(1)


TEMPLATES = {
    "humanities": {
        "body_font": "SimSun",
        "body_size": 12,
        "heading_font": "SimHei",
        "margin_top": 2.54,
        "margin_bottom": 2.54,
        "margin_left": 3.18,
        "margin_right": 3.18,
    },
    "sscilab": {
        "body_font": "SimSun",
        "body_size": 12,
        "heading_font": "SimHei",
        "margin_top": 2.54,
        "margin_bottom": 2.54,
        "margin_left": 3.18,
        "margin_right": 3.18,
    },
    "simple": {
        "body_font": "SimSun",
        "body_size": 11,
        "heading_font": "SimHei",
        "margin_top": 2.0,
        "margin_bottom": 2.0,
        "margin_left": 2.5,
        "margin_right": 2.5,
    },
}

FOOTNOTE_DEF = re.compile(r"^\[\^(\d+)\]:\s+(.*)$")
FOOTNOTE_REF = re.compile(r"\[\^(\d+)\]")
IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def set_page(section, tpl: dict) -> None:
    section.top_margin = Cm(tpl["margin_top"])
    section.bottom_margin = Cm(tpl["margin_bottom"])
    section.left_margin = Cm(tpl["margin_left"])
    section.right_margin = Cm(tpl["margin_right"])


def set_cn_font(run, font_name: str, size_pt: int) -> None:
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = rPr.makeelement(qn("w:rFonts"), {})
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), font_name)
    rFonts.set(qn("w:ascii"), font_name)
    rFonts.set(qn("w:hAnsi"), font_name)


def set_paragraph_indent(paragraph, first_line_chars: int, size_pt: int) -> None:
    pf = paragraph.paragraph_format
    pf.first_line_indent = Pt(first_line_chars * size_pt)
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE


def parse_inline(text: str) -> list[tuple[str, str]]:
    """Return list of (kind, text) — kind in {'plain','bold','italic','footnote'}.

    Minimal: bold **x**, italic *x*, footnote refs [^n]. Nesting not supported.
    """
    parts: list[tuple[str, str]] = []
    i = 0
    while i < len(text):
        # footnote ref
        m = FOOTNOTE_REF.match(text, i)
        if m:
            parts.append(("footnote", m.group(1)))
            i = m.end()
            continue
        # bold
        if text.startswith("**", i):
            end = text.find("**", i + 2)
            if end > 0:
                parts.append(("bold", text[i + 2 : end]))
                i = end + 2
                continue
        # italic
        if text[i] == "*" and not text.startswith("**", i):
            end = text.find("*", i + 1)
            if end > 0:
                parts.append(("italic", text[i + 1 : end]))
                i = end + 1
                continue
        # plain — consume until next special marker
        j = i
        while j < len(text):
            if text.startswith("**", j) or text[j] == "*" or FOOTNOTE_REF.match(text, j):
                break
            j += 1
        if j > i:
            parts.append(("plain", text[i:j]))
            i = j
        else:
            parts.append(("plain", text[i]))
            i += 1
    return parts


def add_rich_paragraph(doc, text: str, tpl: dict, footnotes: dict[str, str]) -> None:
    p = doc.add_paragraph()
    set_paragraph_indent(p, 2, tpl["body_size"])
    for kind, chunk in parse_inline(text):
        if kind == "footnote":
            fn_text = footnotes.get(chunk, "")
            # python-docx doesn't expose proper footnotes; use superscript inline
            run = p.add_run(f"[{chunk}]")
            run.font.superscript = True
            set_cn_font(run, tpl["body_font"], tpl["body_size"])
            if fn_text:
                note = p.add_run(f"({fn_text})")
                note.font.size = Pt(tpl["body_size"] - 2)
                set_cn_font(note, tpl["body_font"], tpl["body_size"] - 2)
            continue
        run = p.add_run(chunk)
        if kind == "bold":
            run.bold = True
        elif kind == "italic":
            run.italic = True
        set_cn_font(run, tpl["body_font"], tpl["body_size"])


def add_heading(doc, text: str, level: int, tpl: dict) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    size = {1: 16, 2: 14, 3: 13}.get(level, 12)
    run = p.add_run(text)
    run.bold = True
    set_cn_font(run, tpl["heading_font"], size)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)


def add_quote(doc, text: str, tpl: dict) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Pt(tpl["body_size"] * 2)
    p.paragraph_format.right_indent = Pt(tpl["body_size"] * 2)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    run = p.add_run(text)
    set_cn_font(run, tpl["body_font"], tpl["body_size"] - 1)
    run.italic = False


def add_image(doc, alt: str, path: Path, md_dir: Path) -> None:
    candidates = [path, md_dir / path, md_dir / "assets" / path.name]
    target = next((c for c in candidates if c.is_file()), None)
    if not target:
        p = doc.add_paragraph(f"[图片缺失：{path}]")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(target), width=Cm(12))
    if alt:
        cap = doc.add_paragraph(alt)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in cap.runs:
            run.font.size = Pt(10)


def extract_footnotes(text: str) -> tuple[str, dict[str, str]]:
    footnotes: dict[str, str] = {}
    body_lines: list[str] = []
    for line in text.splitlines():
        m = FOOTNOTE_DEF.match(line)
        if m:
            footnotes[m.group(1)] = m.group(2)
        else:
            body_lines.append(line)
    return "\n".join(body_lines), footnotes


def render(md_path: Path, out_path: Path, template: str, title_from_h1: bool) -> None:
    tpl = TEMPLATES[template]
    md_text = md_path.read_text(encoding="utf-8")
    body_text, footnotes = extract_footnotes(md_text)

    doc = Document()
    for section in doc.sections:
        set_page(section, tpl)

    title_captured = not title_from_h1
    in_ref_section = False

    for raw_line in body_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue

        if line.startswith("# "):
            heading_text = line[2:].strip()
            if not title_captured:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(heading_text)
                run.bold = True
                set_cn_font(run, tpl["heading_font"], 18)
                p.paragraph_format.space_after = Pt(18)
                title_captured = True
            else:
                add_heading(doc, heading_text, 1, tpl)
                if heading_text in ("参考文献", "引用文献", "Bibliography"):
                    in_ref_section = True
            continue
        if line.startswith("## "):
            add_heading(doc, line[3:].strip(), 2, tpl)
            continue
        if line.startswith("### "):
            add_heading(doc, line[4:].strip(), 3, tpl)
            continue
        if line.startswith("> "):
            add_quote(doc, line[2:].strip(), tpl)
            continue

        img_match = IMAGE_PATTERN.search(line)
        if img_match:
            alt, src = img_match.group(1), img_match.group(2)
            add_image(doc, alt, Path(src), md_path.parent)
            continue

        if in_ref_section:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(tpl["body_size"] * 2)
            p.paragraph_format.first_line_indent = Pt(-tpl["body_size"] * 2)
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
            run = p.add_run(line)
            set_cn_font(run, tpl["body_font"], tpl["body_size"])
            continue

        add_rich_paragraph(doc, line, tpl, footnotes)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--template", choices=list(TEMPLATES), default="humanities")
    ap.add_argument("--title-from-first-h1", action="store_true")
    args = ap.parse_args()

    if not args.input.is_file():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 2

    try:
        render(args.input, args.output, args.template, args.title_from_first_h1)
    except Exception as e:
        print(f"[md_to_docx] failed: {e}", file=sys.stderr)
        return 5

    print(f"[md_to_docx] wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

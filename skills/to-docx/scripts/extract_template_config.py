#!/usr/bin/env python3
"""Reverse-engineer a YAML preset from a Word template.

Workflow the user follows: an editor sends them a `.docx` with the journal's
house style baked in (margins, body font, heading sizes, line spacing).
Instead of eyeballing Word's Format Painter and hand-editing the plugin's
YAML, point this script at the template and it emits a preset file that
`md_to_docx.py --template <path.yaml>` will consume verbatim.

Scope is deliberately narrow — we only read the fields our YAML schema
uses (margins, body font/size/spacing, heading sizes, basic image caps).
Rich Word features the plugin doesn't use (page numbers, code blocks,
tables styling) are skipped silently.

Usage:
    python3 extract_template_config.py --template journal.docx \\
        --out ../assets/presets/journal.yaml \\
        [--name journal] [--description "《XX 研究》投稿模板"]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    from docx import Document
    from docx.shared import Emu
except ImportError:
    print("missing dependency: pip3 install python-docx", file=sys.stderr)
    sys.exit(1)

try:
    import yaml  # PyYAML
except ImportError:
    print("missing dependency: pip3 install pyyaml", file=sys.stderr)
    sys.exit(1)


def _cm(emu_value: Any) -> float | None:
    """python-docx returns margins as Emu; convert to cm (914400 EMU per inch)."""
    if emu_value is None:
        return None
    try:
        return round(Emu(emu_value).cm, 2)
    except Exception:
        return None


def _pt(length_value: Any) -> float | None:
    if length_value is None:
        return None
    try:
        return round(float(length_value.pt), 2)
    except Exception:
        return None


def _first_east_asia_font(font) -> str | None:
    """python-docx's `font.name` only reports the ASCII slot. For a Chinese
    template we want the East-Asia font — peel it from the underlying XML."""
    try:
        rPr = font.element.rPr
        if rPr is None:
            return None
        rfonts = rPr.find(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts"
        )
        if rfonts is None:
            return None
        val = rfonts.get(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia"
        )
        return val or None
    except Exception:
        return None


def _style(doc, name: str):
    try:
        return doc.styles[name]
    except KeyError:
        return None


def extract(doc_path: Path, name: str, description: str) -> dict:
    doc = Document(str(doc_path))
    section = doc.sections[0]

    page = {
        "margin_top": _cm(section.top_margin) or 2.0,
        "margin_bottom": _cm(section.bottom_margin) or 2.0,
        "margin_left": _cm(section.left_margin) or 2.0,
        "margin_right": _cm(section.right_margin) or 2.0,
    }

    body = {
        "font": "Source Han Serif SC",
        "size": 12,
        "line_spacing": 1.2,
        "first_line_indent_chars": 2,
        "character_spacing_pt": 0.0,
    }
    normal = _style(doc, "Normal")
    # python-docx's stub lies about BaseStyle here: the concrete _ParagraphStyle
    # we get back does carry `.font` and `.paragraph_format`, but the attribute
    # is missing from BaseStyle's declared API. Access via getattr to silence
    # pyright without silencing real AttributeErrors at runtime.
    if normal is not None:
        font = getattr(normal, "font", None)
        para = getattr(normal, "paragraph_format", None)
        if font is not None:
            ea_font = _first_east_asia_font(font)
            if ea_font:
                body["font"] = ea_font
            size = _pt(font.size)
            if size:
                body["size"] = int(round(size))
        if para is not None:
            ls = para.line_spacing
            if isinstance(ls, (int, float)):
                body["line_spacing"] = round(float(ls), 2)

    heading_sizes: dict[int, int] = {}
    heading_font = "SimHei"
    for lvl in range(1, 5):
        st = _style(doc, f"Heading {lvl}")
        if st is None:
            continue
        font = getattr(st, "font", None)
        if font is None:
            continue
        sz = _pt(font.size)
        if sz:
            heading_sizes[lvl] = int(round(sz))
        if lvl == 1:
            ea = _first_east_asia_font(font)
            if ea:
                heading_font = ea
    # Fill in sensible defaults for missing levels so md_to_docx never KeyErrors.
    for lvl, default in ((1, 18), (2, 16), (3, 14), (4, 12)):
        heading_sizes.setdefault(lvl, default)

    config = {
        "name": name,
        "description": description,
        "page": page,
        "body": body,
        "heading": {
            "font": heading_font,
            "sizes": heading_sizes,
        },
        "image": {
            "max_width_cm": 14,
            "max_file_kb": 800,
        },
    }
    return config


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True, type=Path,
                    help="Word .docx template to reverse-engineer")
    ap.add_argument("--out", required=True, type=Path,
                    help="Where to write the generated preset YAML")
    ap.add_argument("--name", default=None,
                    help="Preset name (default: template filename stem)")
    ap.add_argument("--description", default="",
                    help="Short human description of the source template")
    args = ap.parse_args()

    if not args.template.is_file():
        print(f"template not found: {args.template}", file=sys.stderr)
        return 2

    name = args.name or args.template.stem
    config = extract(args.template, name=name,
                     description=args.description or f"Extracted from {args.template.name}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        # Disable the default PyYAML alphabetical sort so the file stays
        # human-friendly: the top-level ordering matches the schema order
        # we use in the shipped presets.
        yaml.safe_dump(config, fh, allow_unicode=True, sort_keys=False, default_flow_style=False)
    print(f"[extract_template_config] wrote preset '{name}' -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

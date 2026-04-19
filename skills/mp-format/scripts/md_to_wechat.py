#!/usr/bin/env python3
"""Convert a proofread markdown into a WeChat Official Account-ready HTML.

WeChat's backend strips external stylesheets and most class-based rules, so
every rule is inlined. The output is designed to paste into WeChat's "HTML
mode" editor or the Xiumi / Yiban formatters.

Styling emphasises readability on mobile:
  - 段首缩进 2 字符
  - Blockquotes rendered with a left bar + faint background
  - Footnotes gathered at end, small type, subtle separator
  - Figures centred with caption below
  - Body wraps around 16px sans-serif (WeChat default inherited)

Optional features:
  --simplify  : OpenCC zh-hant -> zh-hans on body (quoted passages preserved)
  --byline    : author/affiliation line at top
  --source    : "原载XXX" source line at top

Usage:
    python3 md_to_wechat.py --input final.md --output final.mp.html \
        --also-markdown final.mp.md --byline "作者 · 机构" --source "《历史研究》2024.3"
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path


FOOTNOTE_DEF = re.compile(r"^\[\^(\d+)\]:\s+(.*)$")
FOOTNOTE_REF = re.compile(r"\[\^(\d+)\]")
IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
BOLD_PATTERN = re.compile(r"\*\*([^*]+)\*\*")
ITALIC_PATTERN = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")


STYLE_BODY = (
    "font-family:-apple-system,\"PingFang SC\",\"Helvetica Neue\",sans-serif;"
    "font-size:16px;line-height:1.85;color:#1d1c1b;"
    "max-width:680px;margin:0 auto;padding:16px;"
)
STYLE_P = "margin:0 0 1.1em 0;text-indent:2em;letter-spacing:.02em;"
STYLE_H1 = "font-size:22px;font-weight:700;color:#1d1c1b;margin:1.4em 0 .6em 0;text-indent:0;"
STYLE_H2 = (
    "font-size:18px;font-weight:700;color:#c97d5d;margin:1.2em 0 .5em 0;"
    "border-left:3px solid #c97d5d;padding-left:10px;text-indent:0;"
)
STYLE_H3 = "font-size:16px;font-weight:700;color:#1d1c1b;margin:1em 0 .4em 0;text-indent:0;"
STYLE_QUOTE = (
    "margin:1em 0;padding:.8em 1em;background:#f3ede3;border-left:3px solid #c2b8a7;"
    "font-size:15px;line-height:1.8;color:#4b4237;text-indent:0;"
)
STYLE_IMG = "display:block;width:100%;margin:1.2em auto .3em auto;border-radius:2px;"
STYLE_CAPTION = (
    "text-align:center;font-size:13px;color:#6b6157;margin:0 0 1.4em 0;"
    "text-indent:0;letter-spacing:.06em;"
)
STYLE_META = (
    "text-align:center;font-size:13px;color:#6b6157;margin:0 0 2em 0;"
    "text-indent:0;border-bottom:1px solid #d9cfc1;padding-bottom:1em;"
)
STYLE_FN_WRAP = (
    "margin-top:3em;padding-top:1em;border-top:1px solid #d9cfc1;"
    "font-size:13px;color:#6b6157;line-height:1.7;"
)
STYLE_FN_ITEM = "margin:.3em 0;text-indent:0;"
STYLE_SUP = "font-size:11px;color:#c97d5d;vertical-align:super;"


def maybe_simplify(text: str) -> str:
    try:
        from opencc import OpenCC  # type: ignore[import-not-found]
    except ImportError:
        print("[md_to_wechat] opencc not installed, keeping original text", file=sys.stderr)
        return text
    cc = OpenCC("t2s")
    # preserve quoted passages — split on block quote / fullwidth quotes
    # A light touch: we simplify outside of paragraphs that start with > only.
    out = []
    for line in text.splitlines():
        if line.startswith(">"):
            out.append(line)
        else:
            out.append(cc.convert(line))
    return "\n".join(out)


def render_inline(s: str) -> str:
    s = html.escape(s)
    s = BOLD_PATTERN.sub(r"<strong>\1</strong>", s)
    s = ITALIC_PATTERN.sub(r"<em>\1</em>", s)
    s = FOOTNOTE_REF.sub(
        lambda m: f"<sup style=\"{STYLE_SUP}\">[{m.group(1)}]</sup>",
        s,
    )
    return s


def extract_footnotes(lines: list[str]) -> tuple[list[str], list[tuple[str, str]]]:
    body: list[str] = []
    notes: list[tuple[str, str]] = []
    for ln in lines:
        m = FOOTNOTE_DEF.match(ln)
        if m:
            notes.append((m.group(1), m.group(2)))
        else:
            body.append(ln)
    return body, notes


def render(md_text: str, byline: str, source: str) -> str:
    lines = md_text.splitlines()
    lines, footnotes = extract_footnotes(lines)

    out: list[str] = ["<div style=\"" + STYLE_BODY + "\">"]
    title_done = False

    meta_bits = []
    if byline:
        meta_bits.append(html.escape(byline))
    if source:
        meta_bits.append(html.escape(source))

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1
            continue

        if line.startswith("# "):
            text = line[2:].strip()
            if not title_done:
                out.append(f"<h1 style=\"{STYLE_H1}\">{html.escape(text)}</h1>")
                if meta_bits:
                    out.append(f"<p style=\"{STYLE_META}\">{' · '.join(meta_bits)}</p>")
                title_done = True
            else:
                out.append(f"<h1 style=\"{STYLE_H1}\">{html.escape(text)}</h1>")
            i += 1
            continue
        if line.startswith("## "):
            out.append(f"<h2 style=\"{STYLE_H2}\">{html.escape(line[3:].strip())}</h2>")
            i += 1
            continue
        if line.startswith("### "):
            out.append(f"<h3 style=\"{STYLE_H3}\">{html.escape(line[4:].strip())}</h3>")
            i += 1
            continue
        if line.startswith(">"):
            quote_lines = [line[1:].lstrip()]
            j = i + 1
            while j < len(lines) and lines[j].startswith(">"):
                quote_lines.append(lines[j][1:].lstrip())
                j += 1
            joined = "<br>".join(render_inline(q) for q in quote_lines)
            out.append(f"<blockquote style=\"{STYLE_QUOTE}\">{joined}</blockquote>")
            i = j
            continue
        img_match = IMAGE_PATTERN.search(line)
        if img_match:
            alt, src = img_match.group(1), img_match.group(2)
            out.append(f"<img src=\"{html.escape(src)}\" alt=\"{html.escape(alt)}\" style=\"{STYLE_IMG}\">")
            if alt:
                out.append(f"<p style=\"{STYLE_CAPTION}\">{html.escape(alt)}</p>")
            i += 1
            continue

        # default: paragraph
        out.append(f"<p style=\"{STYLE_P}\">{render_inline(line)}</p>")
        i += 1

    if footnotes:
        out.append(f"<div style=\"{STYLE_FN_WRAP}\">")
        out.append("<p style=\"margin:0 0 .4em 0;font-weight:600;\">注释</p>")
        for num, text in footnotes:
            out.append(
                f"<p style=\"{STYLE_FN_ITEM}\">[{html.escape(num)}] {render_inline(text)}</p>"
            )
        out.append("</div>")

    out.append("</div>")
    return "\n".join(out)


def also_markdown(md_text: str, byline: str, source: str) -> str:
    header = []
    if byline:
        header.append(f"*{byline}*")
    if source:
        header.append(f"*{source}*")
    if header:
        return "\n".join(header) + "\n\n" + md_text
    return md_text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--also-markdown", type=Path)
    ap.add_argument("--simplify", action="store_true")
    ap.add_argument("--byline", default="")
    ap.add_argument("--source", default="")
    args = ap.parse_args()

    if not args.input.is_file():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 2

    text = args.input.read_text(encoding="utf-8")
    if args.simplify:
        text = maybe_simplify(text)

    html_str = render(text, args.byline, args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html_str, encoding="utf-8")
    print(f"[md_to_wechat] wrote {args.output}")

    if args.also_markdown:
        args.also_markdown.write_text(also_markdown(text, args.byline, args.source), encoding="utf-8")
        print(f"[md_to_wechat] wrote {args.also_markdown}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

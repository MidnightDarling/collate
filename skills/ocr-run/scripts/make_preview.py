#!/usr/bin/env python3
"""Generate a side-by-side HTML viewer for OCR review.

Left column shows each page's rendered PNG. Right column shows the
corresponding OCR text as editable HTML. JN can fix obvious OCR errors
directly in the browser; clicking "保存所有修改" downloads a corrected
markdown file.

Entirely offline — uses relative paths for images, no external scripts
except a tiny inline save handler.

Usage:
    python3 make_preview.py --markdown raw.md --pages-dir ../pages \
        --out preview.html
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path


PAGE_MARKER = re.compile(r"<!--\s*page\s+(\d+)\s*-->", re.IGNORECASE)


def split_by_page(markdown: str) -> list[tuple[int, str]]:
    """Split OCR markdown into (page_number, text) tuples.

    baidu_client writes explicit `<!-- page N -->` markers. MinerU doesn't,
    so if we don't find markers, we split evenly. That's a compromise — the
    left/right won't align perfectly, but JN can still eyeball errors.
    """
    matches = list(PAGE_MARKER.finditer(markdown))
    if matches:
        blocks: list[tuple[int, str]] = []
        for i, m in enumerate(matches):
            page = int(m.group(1))
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
            blocks.append((page, markdown[start:end].strip()))
        return blocks
    # Fallback: treat whole doc as page 1
    return [(1, markdown.strip())]


def build_html(pages: list[tuple[int, str]], pages_dir: Path, title: str) -> str:
    rows = []
    pages_rel = pages_dir  # relative path used in the HTML
    for page_num, text in pages:
        img_name = f"page_{page_num:03d}.png"
        img_src = f"{pages_rel}/{img_name}"
        escaped = html.escape(text)
        rows.append(
            f"""
<section class="pair" data-page="{page_num}">
  <div class="col left">
    <div class="page-label">第 {page_num} 页</div>
    <img src="{img_src}" alt="page {page_num}" loading="lazy">
  </div>
  <div class="col right">
    <div class="toolbar">
      <span class="page-num">第 {page_num} 页</span>
      <span class="hint">直接点击文字修改</span>
    </div>
    <pre class="editable" contenteditable="true" spellcheck="false">{escaped}</pre>
  </div>
</section>
"""
        )

    joined = "\n".join(rows)
    return (
        "<!doctype html><html lang=\"zh-CN\"><head>"
        "<meta charset=\"utf-8\">"
        f"<title>{html.escape(title)} · 校对预览</title>"
        "<style>"
        "body{font-family:-apple-system,\"PingFang SC\",\"Helvetica Neue\",sans-serif;"
        "margin:0;background:#f3ede3;color:#1d1c1b;}"
        "header{position:sticky;top:0;background:#1d1c1b;color:#f3ede3;"
        "padding:12px 24px;z-index:10;display:flex;gap:16px;align-items:center;}"
        "header h1{font-size:16px;margin:0;font-weight:500;letter-spacing:.05em;}"
        "header .actions{margin-left:auto;}"
        "header button{background:#c97d5d;color:#fff;border:0;padding:8px 18px;"
        "border-radius:2px;cursor:pointer;font-size:14px;}"
        "header button:hover{background:#b86a48;}"
        ".pair{display:grid;grid-template-columns:1fr 1fr;gap:24px;"
        "padding:24px;border-bottom:1px solid #d9cfc1;}"
        ".col{background:#fff;border:1px solid #d9cfc1;border-radius:2px;overflow:hidden;}"
        ".col img{width:100%;display:block;}"
        ".page-label{padding:10px 14px;background:#e8ddcd;font-size:12px;"
        "letter-spacing:.2em;color:#6b6157;}"
        ".toolbar{display:flex;align-items:center;padding:10px 14px;"
        "background:#e8ddcd;font-size:12px;color:#6b6157;}"
        ".toolbar .hint{margin-left:auto;font-style:italic;}"
        ".editable{margin:0;padding:20px;white-space:pre-wrap;"
        "font-family:\"Songti SC\",\"Source Han Serif SC\",Georgia,serif;"
        "font-size:15px;line-height:1.9;min-height:200px;outline:none;}"
        ".editable:focus{background:#fff8ec;}"
        ".footer{padding:40px;text-align:center;color:#6b6157;font-size:13px;}"
        "</style></head><body>"
        "<header>"
        f"<h1>{html.escape(title)} — 校对预览</h1>"
        "<div class=\"actions\">"
        "<button onclick=\"saveAll()\">保存所有修改</button>"
        "</div></header>"
        + joined
        + "<div class=\"footer\">所有修改在本地浏览器内，点「保存所有修改」后下载一份 corrected.md</div>"
        "<script>"
        "function saveAll(){"
        "var parts=[];"
        "document.querySelectorAll('.pair').forEach(function(p){"
        "var num=p.dataset.page;"
        "var txt=p.querySelector('.editable').innerText;"
        "parts.push('<!-- page '+num+' -->\\n\\n'+txt);"
        "});"
        "var blob=new Blob([parts.join('\\n\\n')],{type:'text/markdown;charset=utf-8'});"
        "var a=document.createElement('a');"
        "a.href=URL.createObjectURL(blob);"
        "a.download='corrected.md';"
        "a.click();"
        "}"
        "</script>"
        "</body></html>"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--markdown", required=True, type=Path)
    ap.add_argument("--pages-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--title", default="")
    args = ap.parse_args()

    if not args.markdown.is_file():
        print(f"markdown not found: {args.markdown}", file=sys.stderr)
        return 2

    text = args.markdown.read_text(encoding="utf-8")
    pages = split_by_page(text)

    # compute a relative path from the HTML location to the pages dir
    try:
        rel = Path.relative_to(args.pages_dir.resolve(), args.out.resolve().parent)
    except ValueError:
        rel = args.pages_dir.resolve()

    html_str = build_html(pages, rel, args.title or args.markdown.stem)
    args.out.write_text(html_str, encoding="utf-8")
    print(f"[make_preview] {len(pages)} pages -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

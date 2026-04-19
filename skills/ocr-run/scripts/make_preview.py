#!/usr/bin/env python3
"""Generate a side-by-side HTML viewer for OCR review.

Left column shows each page's rendered PNG. Right column shows the
corresponding OCR text as editable HTML. The user can fix obvious OCR errors
directly in the browser; clicking "下载修改后的 Markdown" saves a file named
`corrected.md` to the browser's Downloads folder. The file is NOT written
back to `raw.md` in place — browsers cannot silently write to disk, so the
user is expected to move `corrected.md` over `raw.md` before the next step.
The footer of the generated HTML spells this out.

Entirely offline — uses relative paths for images, no external scripts
except a tiny inline save handler.

Usage:
    python3 make_preview.py --markdown raw.md --pages-dir ../pages \
        --out preview.html
"""
from __future__ import annotations

import argparse
import html
import os
import re
import sys
from pathlib import Path


PAGE_MARKER = re.compile(r"<!--\s*page\s+(\d+)\s*-->", re.IGNORECASE)


def split_by_page(markdown: str, total_pages: int) -> list[tuple[int, str]]:
    """Split OCR markdown into (page_number, text) tuples.

    baidu_client writes explicit `<!-- page N -->` markers. MinerU does not,
    so when markers are absent we fall back to an even split across
    `total_pages` — the number of source page PNGs we know exist. The split
    prefers paragraph boundaries (`\\n\\n`) so sentences don't get sliced
    mid-line. Alignment is imperfect by construction (MinerU does not tell
    us which text came from which page), but a roughly-right split is
    materially better than stuffing the entire document onto page 1.
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

    text = markdown.strip()
    if total_pages <= 1 or not text:
        return [(1, text)]

    # Split into paragraphs (keep blank-line boundaries) and greedily pack
    # them into N buckets of roughly equal character count.
    paragraphs = [p for p in re.split(r"\n{2,}", text) if p.strip()]
    if len(paragraphs) <= 1:
        # Single-paragraph dump: fall back to a hard character slice so the
        # viewer still shows N sections rather than one giant block.
        step = max(1, len(text) // total_pages)
        chunks = [text[i : i + step] for i in range(0, len(text), step)]
        # Trim to exactly total_pages; merge any overflow into the last slot.
        if len(chunks) > total_pages:
            chunks = chunks[: total_pages - 1] + ["".join(chunks[total_pages - 1 :])]
        return [(i + 1, c.strip()) for i, c in enumerate(chunks)]

    target = max(1, sum(len(p) for p in paragraphs) // total_pages)
    blocks_text: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for p in paragraphs:
        cur.append(p)
        cur_len += len(p)
        # Start a new bucket once we cross the target and still have enough
        # paragraphs left to fill the remaining pages.
        remaining = total_pages - len(blocks_text) - 1
        if cur_len >= target and remaining > 0 and len(paragraphs) - paragraphs.index(p) - 1 >= remaining:
            blocks_text.append("\n\n".join(cur))
            cur = []
            cur_len = 0
    if cur:
        blocks_text.append("\n\n".join(cur))

    # Pad empty buckets so we always emit exactly `total_pages` sections.
    while len(blocks_text) < total_pages:
        blocks_text.append("")
    # Merge surplus into the last page (shouldn't normally happen).
    if len(blocks_text) > total_pages:
        tail = "\n\n".join(blocks_text[total_pages - 1 :])
        blocks_text = blocks_text[: total_pages - 1] + [tail]

    return [(i + 1, body.strip()) for i, body in enumerate(blocks_text)]


def count_source_pages(pages_dir: Path) -> int:
    """Return the number of page_*.png files in the prep pages directory."""
    try:
        return sum(1 for _ in pages_dir.glob("page_*.png"))
    except Exception:
        return 0


def build_html(pages: list[tuple[int, str]], pages_rel: str, title: str) -> str:
    rows = []
    pages_rel = pages_rel.rstrip("/")  # always forward-slash join below
    for page_num, text in pages:
        img_name = f"page_{page_num:03d}.png"
        img_src = f"{pages_rel}/{img_name}" if pages_rel else img_name
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
        "header .hint-inline{font-size:12px;color:#d9cfc1;margin-right:16px;}"
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
        "<span class=\"hint-inline\">改完点按钮下载 corrected.md，然后回 Claude Code 说「改完了」</span>"
        "<button onclick=\"saveAll()\">下载修改后的 Markdown</button>"
        "</div></header>"
        + joined
        + "<div class=\"footer\">"
        "浏览器不能直接写磁盘，所以按钮只能把右栏文字打包成 <code>corrected.md</code> 下载到你的下载目录。"
        "<br>你不用自己搬文件——下载完回到 Claude Code 说「改完了」或「应用修改」，"
        "Agent 会自动备份 <code>raw.md</code> 并把 <code>corrected.md</code> 替换上去，然后进入 proofread。"
        "</div>"
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
    total_pages = count_source_pages(args.pages_dir)
    pages = split_by_page(text, total_pages if total_pages > 0 else 1)

    # Use os.path.relpath so the HTML stays portable even when the output
    # directory is a sibling of the pages directory (needs `..`). We
    # normalise to forward slashes so the browser interprets it as a URL.
    try:
        rel = os.path.relpath(args.pages_dir.resolve(), args.out.resolve().parent)
    except ValueError:
        # Different drives on Windows — fall back to an absolute file URL.
        rel = args.pages_dir.resolve().as_posix()
    rel_url = rel.replace(os.sep, "/")

    html_str = build_html(pages, rel_url, args.title or args.markdown.stem)
    args.out.write_text(html_str, encoding="utf-8")
    print(
        f"[make_preview] {len(pages)} pages "
        f"(source pages detected: {total_pages}) -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

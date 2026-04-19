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
import json
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


def load_meta(markdown_path: Path) -> dict:
    """Read meta.json sitting next to raw.md if it exists. Missing fields are OK."""
    meta_path = markdown_path.parent / "meta.json"
    if not meta_path.is_file():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def engine_label(engine: str) -> str:
    return {
        "mineru": "MinerU（本地）",
        "mineru-desktop": "MinerU（legacy import）",
        "mineru-legacy-job": "MinerU（legacy import）",
        "mineru-cloud": "MinerU（云 API）",
        "baidu": "百度 OCR",
    }.get(engine, engine or "未知引擎")


def build_html(
    pages: list[tuple[int, str]],
    pages_rel: str,
    title: str,
    meta: dict,
    has_page_markers: bool,
) -> str:
    low_conf = set(int(n) for n in meta.get("low_confidence_pages") or [])
    rows = []
    pages_rel = pages_rel.rstrip("/")  # always forward-slash join below
    for page_num, text in pages:
        img_name = f"page_{page_num:03d}.png"
        img_src = f"{pages_rel}/{img_name}" if pages_rel else img_name
        escaped = html.escape(text)
        flag = ' data-low-conf="1"' if page_num in low_conf else ""
        flag_badge = (
            '<span class="flag">这页请多留意</span>'
            if page_num in low_conf
            else ""
        )
        rows.append(
            f"""
<section class="pair"{flag} data-page="{page_num}">
  <div class="col left">
    <div class="page-label">第 {page_num} 页{flag_badge}</div>
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

    # Header stats — only show fields that are present in meta.
    stats: list[str] = []
    engine = meta.get("engine")
    if engine:
        stats.append(f'<span class="stat">引擎 {html.escape(engine_label(engine))}</span>')
    stats.append(f'<span class="stat">{len(pages)} 页</span>')
    dur = meta.get("duration_seconds")
    if isinstance(dur, (int, float)) and dur > 0:
        stats.append(f'<span class="stat">用时 {dur:.1f} 秒</span>')
    if low_conf:
        pages_str = "、".join(f"第 {n} 页" for n in sorted(low_conf))
        stats.append(f'<span class="stat warn">低置信 {html.escape(pages_str)}</span>')
    align_note = (
        "按页标记精准分页"
        if has_page_markers
        else "文本按段落估算分页"
    )
    stats.append(f'<span class="stat">{html.escape(align_note)}</span>')
    stats_html = "".join(stats)

    return (
        "<!doctype html><html lang=\"zh-CN\"><head>"
        "<meta charset=\"utf-8\">"
        f"<title>{html.escape(title)} · 校对预览</title>"
        "<style>"
        "/* Palette: hero-aligned neutral darks (ATTRIBUTION° Ink Stone family). */"
        "body{font-family:-apple-system,\"PingFang SC\",\"Helvetica Neue\",sans-serif;"
        "margin:0;background:#0E0E11;color:#E0DCD6;}"
        "header{position:sticky;top:0;background:#08080A;color:#E0DCD6;"
        "padding:14px 24px;z-index:10;display:flex;gap:12px;align-items:center;"
        "flex-wrap:wrap;border-bottom:1px solid rgba(255,255,255,.07);}"
        "header h1{font-size:15px;margin:0;font-weight:500;letter-spacing:.05em;color:#E0DCD6;}"
        "header .stat{font-size:12px;padding:4px 10px;border-radius:2px;"
        "background:#1E1E21;color:#C9C5BF;letter-spacing:.03em;}"
        "header .stat.warn{background:#262618;color:#B8AC88;}"
        "header .actions{margin-left:auto;display:flex;gap:12px;align-items:center;}"
        "header button{background:transparent;color:#F0EDE6;"
        "border:1px solid #F0EDE6;padding:8px 18px;"
        "border-radius:2px;cursor:pointer;font-size:14px;letter-spacing:.02em;"
        "box-shadow:0 0 24px rgba(240,237,230,.15),0 0 80px rgba(240,237,230,.04);"
        "transition:all .15s ease;}"
        "header button:hover{background:#F0EDE6;color:#000;}"
        "header .hint-inline{font-size:12px;color:#9A9690;}"
        ".pair{display:grid;grid-template-columns:1fr 1fr;gap:24px;"
        "padding:24px;border-bottom:1px solid rgba(255,255,255,.07);align-items:start;}"
        ".pair[data-low-conf=\"1\"]{background:#1C1812;}"
        ".col{background:#161618;border:1px solid rgba(255,255,255,.07);border-radius:2px;"
        "overflow:hidden;}"
        ".col.left{position:sticky;top:76px;max-height:calc(100vh - 100px);"
        "display:flex;flex-direction:column;}"
        ".col.left .page-label{flex-shrink:0;}"
        ".col.left img{flex:1;min-height:0;width:100%;object-fit:contain;"
        "background:#0E0E11;display:block;}"
        ".col.right img{width:100%;display:block;}"
        ".page-label{padding:10px 14px;background:#1E1E21;font-size:12px;"
        "letter-spacing:.2em;color:#9A9690;display:flex;gap:12px;align-items:center;}"
        ".page-label .flag{font-size:11px;letter-spacing:.08em;padding:2px 8px;"
        "background:#262618;color:#B8AC88;border-radius:2px;}"
        ".toolbar{display:flex;align-items:center;padding:10px 14px;"
        "background:#1E1E21;font-size:12px;color:#9A9690;letter-spacing:.05em;}"
        ".toolbar .hint{margin-left:auto;color:#605C56;}"
        ".editable{margin:0;padding:20px;white-space:pre-wrap;"
        "font-family:\"Songti SC\",\"Source Han Serif SC\",\"Noto Serif SC\",Georgia,serif;"
        "font-size:15px;line-height:1.95;min-height:200px;outline:none;color:#E0DCD6;"
        "caret-color:#F0EDE6;}"
        ".editable:focus{background:#1A1A1D;}"
        ".footer{padding:40px;color:#9A9690;font-size:14px;line-height:1.8;"
        "text-align:center;border-top:1px solid rgba(255,255,255,.07);background:#08080A;}"
        "</style></head><body>"
        "<header>"
        f"<h1>{html.escape(title)} — 校对预览</h1>"
        f"{stats_html}"
        "<div class=\"actions\">"
        "<span class=\"hint-inline\">你可以直接下载，或者告诉我你的其他需求 ☕</span>"
        "<button onclick=\"saveAll()\">下载修改后的 Markdown</button>"
        "</div></header>"
        + joined
        + "<div class=\"footer\">"
        "你不用自己搬文档，下载完了告诉我，我来处理。"
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
    has_page_markers = bool(PAGE_MARKER.search(text))
    meta = load_meta(args.markdown)

    # Use os.path.relpath so the HTML stays portable even when the output
    # directory is a sibling of the pages directory (needs `..`). We
    # normalise to forward slashes so the browser interprets it as a URL.
    try:
        rel = os.path.relpath(args.pages_dir.resolve(), args.out.resolve().parent)
    except ValueError:
        # Different drives on Windows — fall back to an absolute file URL.
        rel = args.pages_dir.resolve().as_posix()
    rel_url = rel.replace(os.sep, "/")

    html_str = build_html(
        pages, rel_url, args.title or args.markdown.stem, meta, has_page_markers
    )
    args.out.write_text(html_str, encoding="utf-8")
    print(
        f"[make_preview] {len(pages)} pages "
        f"(source pages detected: {total_pages}) -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

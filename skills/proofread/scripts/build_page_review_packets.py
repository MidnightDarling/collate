#!/usr/bin/env python3
"""Build deterministic page-aligned review packets for proofread.

Inputs:
  - <workspace>/raw.md
  - <workspace>/prep/pages/page_*.png
  - optional <workspace>/meta.json (for low-confidence hints)

Output:
  - <workspace>/review/page_review_packets.json

Each packet gives the proofread agent one page worth of source evidence:
the original PNG path plus the OCR text currently attributed to that page.
Primary source is raw.md with explicit `<!-- page N -->` markers. If a
fallback OCR path cannot truthfully inject markers into raw.md, it may
write `_internal/page_texts.json` as a separate per-page sidecar; we accept
that too. What we do NOT do is invent page boundaries by evenly slicing the
document.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PAGE_MARKER = re.compile(r"<!--\s*page\s+(\d+)\s*-->", re.IGNORECASE)
PAGE_IMAGE_RE = re.compile(r"page_(\d+)\.png$", re.IGNORECASE)


def split_by_page(markdown: str, total_pages: int) -> list[tuple[int, str]]:
    matches = list(PAGE_MARKER.finditer(markdown))
    if matches:
        blocks: list[tuple[int, str]] = []
        for i, match in enumerate(matches):
            page = int(match.group(1))
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
            blocks.append((page, markdown[start:end].strip()))
        return blocks

    if total_pages > 1:
        raise ValueError(
            "page markers missing: multi-page raw.md cannot be split truthfully; "
            "rerun OCR/reflow so raw.md contains `<!-- page N -->` markers"
        )

    text = markdown.strip()
    if total_pages <= 1:
        return [(1, text)]

    raise ValueError(
        "page markers missing: multi-page raw.md cannot be split truthfully; "
        "rerun OCR/reflow so raw.md contains `<!-- page N -->` markers"
    )


def sidecar_blocks(sidecar_path: Path, total_pages: int) -> list[tuple[int, str]]:
    if not sidecar_path.is_file():
        return []
    try:
        payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    blocks = [
        (int(item.get("page")), str(item.get("text", "")))
        for item in payload
        if str(item.get("page", "")).isdigit()
    ]
    if len(blocks) != total_pages:
        return []
    return sorted(blocks)

def low_confidence_pages(meta_path: Path) -> set[int]:
    if not meta_path.is_file():
        return set()
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    raw = meta.get("low_confidence_pages") or []
    pages: set[int] = set()
    for item in raw:
        try:
            pages.add(int(item))
        except Exception:
            continue
    return pages


def page_images(pages_dir: Path) -> list[tuple[int, Path]]:
    images: list[tuple[int, Path]] = []
    for path in sorted(pages_dir.glob("page_*.png")):
        match = PAGE_IMAGE_RE.search(path.name)
        if not match:
            continue
        images.append((int(match.group(1)), path.resolve()))
    return images


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    workspace = args.workspace
    raw_path = workspace / "raw.md"
    pages_dir = workspace / "prep" / "pages"
    if not raw_path.is_file():
        print(f"raw not found: {raw_path}", file=sys.stderr)
        return 2
    if not pages_dir.is_dir():
        print(f"pages dir not found: {pages_dir}", file=sys.stderr)
        return 2

    images = page_images(pages_dir)
    if not images:
        print(f"no page_*.png found under {pages_dir}", file=sys.stderr)
        return 2

    try:
        blocks = split_by_page(raw_path.read_text(encoding="utf-8"), len(images))
    except ValueError as exc:
        blocks = sidecar_blocks(workspace / "_internal" / "page_texts.json", len(images))
        if not blocks:
            print(str(exc), file=sys.stderr)
            return 2
    block_map = {page: text for page, text in blocks}
    low_conf = low_confidence_pages(workspace / "meta.json")

    packets = []
    for page, image in images:
        text = block_map.get(page, "")
        packets.append({
            "page": page,
            "image": str(image),
            "ocr_text": text,
            "ocr_chars": len(text),
            "low_confidence": page in low_conf,
        })

    out = args.out or (workspace / "review" / "page_review_packets.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packets, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[build_page_review_packets] wrote {out} ({len(packets)} packets)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

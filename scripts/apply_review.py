#!/usr/bin/env python3
"""Conservatively apply raw.review.md onto raw.md to produce final.md."""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

from review_contract import ReviewItem, parse_review


ARROW_RE = re.compile(r"(?:→|->|⇒)\s*(.+)$")
QUOTED_RE = re.compile(r"[“\"'「『](.+?)[”\"'」』]")


def extract_replacement(item: ReviewItem) -> str:
    suggestion = item.suggestion.strip()
    arrow = ARROW_RE.search(suggestion)
    if arrow:
        return arrow.group(1).strip().strip('"')
    quoted = QUOTED_RE.findall(suggestion)
    if quoted:
        return quoted[-1].strip()
    return suggestion


def apply_items(lines: list[str], items: list[ReviewItem]) -> tuple[list[str], dict[str, int]]:
    applied = 0
    skipped = 0
    commented = 0
    comments_by_line: dict[int, list[str]] = {}
    for item in items:
        if item.line_number is None or item.line_number < 1 or item.line_number > len(lines):
            skipped += 1
            continue
        idx = item.line_number - 1
        line = lines[idx]
        if item.category == "C":
            comments_by_line.setdefault(idx, []).append(
                f"<!-- proofread-C: {item.item_id} | {html.escape(item.title)} | {html.escape(item.suggestion)} -->"
            )
            commented += 1
            continue
        fragment = item.fragment.strip()
        replacement = extract_replacement(item)
        if not fragment or not replacement:
            skipped += 1
            continue
        if line.count(fragment) != 1:
            skipped += 1
            continue
        lines[idx] = line.replace(fragment, replacement, 1)
        applied += 1
    output: list[str] = []
    for idx, line in enumerate(lines):
        output.append(line)
        output.extend(comments_by_line.get(idx, []))
    return output, {"applied": applied, "skipped": skipped, "commented": commented}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--review", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    if not args.raw.is_file():
        print(f"raw not found: {args.raw}", file=sys.stderr)
        return 2
    if not args.review.is_file():
        print(f"review not found: {args.review}", file=sys.stderr)
        return 2

    out = args.out or (args.raw.parent / "final.md")
    items = parse_review(args.review)
    lines = args.raw.read_text(encoding="utf-8").splitlines()
    rendered, stats = apply_items(lines, items)
    out.write_text("\n".join(rendered).rstrip() + "\n", encoding="utf-8")
    print(
        f"[apply_review] wrote {out}\n"
        f"  items={len(items)} applied={stats['applied']} commented={stats['commented']} skipped={stats['skipped']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

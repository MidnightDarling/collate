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
STRUCTURE_APPROVED_RE = re.compile(
    r"^\s*structure_approved\s*:\s*true\s*$", re.IGNORECASE
)
DIRECT_REPLACEMENT_RE = re.compile(
    r"^(?:改为|改作|应为|應為|修正为|修訂為|更正为)[:：]?\s*(.+)$"
)
EDITORIAL_MARKERS = (
    "删除", "刪除", "移除", "连读", "連讀", "合并", "合併", "脚注",
    "腳注", "原文", "保留", "注释", "注釋", "未定", "待核", "另起",
    "不改", "整段", "上下文", "段落",
)


def review_has_structure_approval(review_text: str) -> bool:
    """Scan top-of-file YAML-ish frontmatter for `structure_approved: true`.

    The proofread subagent, when it has walked every page against the
    PNG originals and confirmed the structural skeleton (title, author,
    headings, footnote split) is usable, prepends a small frontmatter
    block. We look for it *only* inside the first `---`…`---` fence; any
    later occurrence inside the body is treated as coincidental.
    """
    lines = review_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if STRUCTURE_APPROVED_RE.match(line):
            return True
    return False


def extract_replacement(item: ReviewItem) -> str:
    suggestion = item.suggestion.strip()
    arrow = ARROW_RE.search(suggestion)
    if arrow:
        suggestion = arrow.group(1).strip().strip('"')
    else:
        direct = DIRECT_REPLACEMENT_RE.match(suggestion)
        if direct:
            suggestion = direct.group(1).strip().strip('"')
        else:
            quoted = QUOTED_RE.findall(suggestion)
            if quoted:
                suggestion = quoted[-1].strip()

    if not suggestion:
        return ""
    if any(marker in suggestion for marker in EDITORIAL_MARKERS):
        return ""
    if "\n" in suggestion:
        return ""
    if len(suggestion) > 40:
        return ""
    if any(ch in suggestion for ch in "，。；：？！"):
        return ""
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
    review_text = args.review.read_text(encoding="utf-8")
    items = parse_review(args.review)
    lines = args.raw.read_text(encoding="utf-8").splitlines()
    rendered, stats = apply_items(lines, items)
    out.write_text("\n".join(rendered).rstrip() + "\n", encoding="utf-8")

    # Emit the _structure_approved marker if the proofread subagent has
    # attested the structural skeleton of raw.md via frontmatter. The
    # Bundle 4 fidelity gate reads this marker (alongside meta.json's
    # structural_risk field) to decide whether export can proceed.
    if review_has_structure_approval(review_text):
        workspace = args.raw.parent
        internal = workspace / "_internal"
        internal.mkdir(parents=True, exist_ok=True)
        (internal / "_structure_approved").write_text("", encoding="utf-8")

    print(
        f"[apply_review] wrote {out}\n"
        f"  items={len(items)} applied={stats['applied']} commented={stats['commented']} skipped={stats['skipped']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

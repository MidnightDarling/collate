#!/usr/bin/env python3
"""Shared review-contract parsing for proofread/apply/diff stages."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ReviewItem:
    category: str
    item_id: str
    title: str
    line_number: Optional[int]
    fragment: str
    suggestion: str
    status: str = "unanchored"
    anchored_paragraph_idx: Optional[int] = None
    reason: str = ""


CANON_HEADER_RE = re.compile(
    r"^###\s+([ABC]\d+)\.\s+(.*?)(?:\s+·\s+(?:Line\s+(\d+)|全文))?\s*$"
)
LEGACY_SECTION_RE = re.compile(r"^##\s+([ABC])(?:\b|（)")
LEGACY_BULLET_RE = re.compile(
    r'^-\s*(?:(?:line|Line)\s+(\d+)|全文)\s*\|\s*原文[:：]\s*"?(.+?)"?\s*\|\s*建议[:：]\s*"?(.+?)"?\s*\|\s*理由[:：]\s*(.+?)\s*$'
)


def _parse_canonical(lines: list[str]) -> list[ReviewItem]:
    items: list[ReviewItem] = []
    i = 0
    while i < len(lines):
        match = CANON_HEADER_RE.match(lines[i])
        if not match:
            i += 1
            continue
        item_id = match.group(1)
        title = (match.group(2) or "").strip()
        line_number = int(match.group(3)) if match.group(3) else None
        fragment_lines: list[str] = []
        suggestion = ""
        j = i + 1
        while j < len(lines):
            peek = lines[j]
            if CANON_HEADER_RE.match(peek) or peek.startswith("## ") or peek.startswith("# "):
                break
            if peek.startswith("> "):
                fragment_lines.append(peek[2:].rstrip())
            if "**建议**" in peek or peek.startswith("**建议"):
                rest = peek.split("**建议**", 1)[-1].lstrip("：:*").strip()
                suggestion = rest or (lines[j + 1].strip() if j + 1 < len(lines) else "")
            j += 1
        items.append(
            ReviewItem(
                category=item_id[0],
                item_id=item_id,
                title=title,
                line_number=line_number,
                fragment=" ".join(fragment_lines).strip(),
                suggestion=suggestion,
            )
        )
        i = j
    return items


def _parse_legacy(lines: list[str]) -> list[ReviewItem]:
    items: list[ReviewItem] = []
    current_category = ""
    counters: dict[str, int] = {"A": 0, "B": 0, "C": 0}
    for line in lines:
        section = LEGACY_SECTION_RE.match(line)
        if section:
            current_category = section.group(1)
            continue
        bullet = LEGACY_BULLET_RE.match(line)
        if not bullet or not current_category:
            continue
        counters[current_category] += 1
        item_id = f"{current_category}{counters[current_category]}"
        line_number = int(bullet.group(1)) if bullet.group(1) else None
        fragment = bullet.group(2).strip().strip('"')
        suggestion = bullet.group(3).strip().strip('"')
        reason = bullet.group(4).strip()
        title = reason[:40] or fragment[:40] or item_id
        items.append(
            ReviewItem(
                category=current_category,
                item_id=item_id,
                title=title,
                line_number=line_number,
                fragment=fragment,
                suggestion=suggestion,
                reason=reason,
            )
        )
    return items


def parse_review_text(text: str) -> list[ReviewItem]:
    lines = text.splitlines()
    canonical = _parse_canonical(lines)
    return canonical or _parse_legacy(lines)


def parse_review(path: Path) -> list[ReviewItem]:
    return parse_review_text(path.read_text(encoding="utf-8"))

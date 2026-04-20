#!/usr/bin/env python3
"""Verify that a proofread review is mechanically page-grounded and complete.

Checks:
  - review/page_review_packets.json exists and is non-empty
  - review/raw.review.md exists
  - review frontmatter contains `proofread_method: page-grounded`
  - review frontmatter lists `checked_pages: [...]` covering every packet page

This does not judge whether the review is *good*. It verifies that the
minimum completion markers for an agent-owned page-grounded pass are present.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_frontmatter(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data: dict[str, object] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.lower() in {"true", "false"}:
            data[key] = value.lower() == "true"
            continue
        if value.startswith("[") and value.endswith("]"):
            data[key] = [int(n) for n in re.findall(r"\d+", value)]
            continue
        data[key] = value.strip("\"'")
    return data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True, type=Path)
    args = ap.parse_args()

    workspace = args.workspace
    packets_path = workspace / "review" / "page_review_packets.json"
    review_path = workspace / "review" / "raw.review.md"
    if not packets_path.is_file():
        print(f"missing packets: {packets_path}", file=sys.stderr)
        return 2
    if not review_path.is_file():
        print(f"missing review: {review_path}", file=sys.stderr)
        return 2

    packets = json.loads(packets_path.read_text(encoding="utf-8"))
    if not packets:
        print("page_review_packets.json is empty", file=sys.stderr)
        return 2
    packet_pages = sorted(int(p["page"]) for p in packets)

    frontmatter = parse_frontmatter(review_path.read_text(encoding="utf-8"))
    if frontmatter.get("proofread_method") != "page-grounded":
        print(
            "review frontmatter missing `proofread_method: page-grounded`",
            file=sys.stderr,
        )
        return 3

    checked_pages = frontmatter.get("checked_pages")
    if not isinstance(checked_pages, list) or not checked_pages:
        print(
            "review frontmatter missing non-empty `checked_pages: [...]` coverage",
            file=sys.stderr,
        )
        return 3

    checked_set = {int(n) for n in checked_pages}
    packet_set = set(packet_pages)
    missing = sorted(packet_set - checked_set)
    extra = sorted(checked_set - packet_set)
    if missing or extra:
        print(
            "checked_pages does not match packet pages "
            f"(missing={missing or '[]'} extra={extra or '[]'})",
            file=sys.stderr,
        )
        return 4

    print(
        "[verify_page_grounded_review] ok "
        f"(pages={packet_pages}, proofread_method=page-grounded)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

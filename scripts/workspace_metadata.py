#!/usr/bin/env python3
"""Workspace metadata fallback helpers."""
from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path


H1_RE = re.compile(r"^#\s+(.+?)\s*$")
CANONICAL_OUTPUT_PATTERNS = {
    "_final.docx": "*_final.docx",
    "_wechat.html": "*_wechat.html",
    "_wechat.md": "*_wechat.md",
}


def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _first_heading(md_path: Path) -> str:
    if not md_path.is_file():
        return ""
    for line in md_path.read_text(encoding="utf-8").splitlines():
        match = H1_RE.match(line.strip())
        if match:
            return match.group(1).strip()
    return ""


def _author_hint(md_path: Path) -> str:
    if not md_path.is_file():
        return ""
    seen_h1 = False
    for raw in md_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if not seen_h1:
            if H1_RE.match(line):
                seen_h1 = True
            continue
        if line.startswith(("<!--", "#", ">", "## ")):
            continue
        if (
            len(line) <= 40
            and not any(ch.isdigit() for ch in line)
            and not any(ch in line for ch in "。；！？，,.;!?()[]（）【】")
        ):
            return line
        break
    return ""


def load_workspace_metadata(workspace: Path, markdown_hint: Path | None = None) -> dict:
    """Return best-effort title/author/year for a `.ocr/` workspace."""
    meta = {"title": "", "author": "", "year": ""}

    for cand in (
        workspace / "_internal" / "_import_provenance.json",
        workspace / "_import_provenance.json",
        workspace / "meta.json",
    ):
        data = _read_json(cand)
        for key in ("title", "author", "year"):
            value = str(data.get(key) or "").strip()
            if value and not meta[key]:
                meta[key] = value

    markdown_candidates = [
        markdown_hint,
        workspace / "final.md",
        workspace / "raw.md",
    ]
    for cand in markdown_candidates:
        if cand is None:
            continue
        if not meta["title"]:
            meta["title"] = _first_heading(cand)
        if not meta["author"]:
            meta["author"] = _author_hint(cand)
        if meta["title"] and meta["author"]:
            break

    return meta


def purge_stale_workspace_outputs(
    workspace: Path,
    keep_paths: Iterable[Path],
) -> list[Path]:
    """Remove superseded canonical outputs from `<workspace>/output/`.

    Reruns are meant to overwrite the canonical deliverables in-place, not
    accumulate an old title-derived filename beside a new one. The caller
    passes the output path(s) it intends to keep; sibling files of the same
    canonical family are deleted.
    """
    output_dir = workspace / "output"
    if not output_dir.is_dir():
        return []

    keep = list(keep_paths)
    keep_resolved = {p.resolve() for p in keep}
    patterns = {
        glob
        for path in keep
        for suffix, glob in CANONICAL_OUTPUT_PATTERNS.items()
        if path.name.endswith(suffix)
    }
    removed: list[Path] = []
    for pattern in patterns:
        for candidate in output_dir.glob(pattern):
            if not candidate.is_file() or candidate.resolve() in keep_resolved:
                continue
            candidate.unlink()
            removed.append(candidate)
    return removed

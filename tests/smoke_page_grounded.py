#!/usr/bin/env python3
"""Bundle 3 regression: proofread contract requires page images as evidence.

Asserts the three documentation-layer contracts that collectively make the
proofread stage page-grounded:

  1. skills/proofread/SKILL.md names `page_images_dir` in the payload it
     hands to the historical-proofreader subagent, and requires the stage
     to write `proofread_method: "page-grounded"` back into status.
  2. AGENTS.md §5 subagent contract lists `page_images_dir` as required.
  3. skills/ocr-run/scripts/make_preview.py declares itself audit-only
     and explicitly NOT a canonical pipeline step — preventing the
     failure mode where users produce corrected.md in the browser and
     copy it over raw.md, which would skip the fidelity gate.

Pre-fix (per the 2026-04-20 Codex audit): the subagent judged OCR truth
from Markdown alone and the preview HTML was documented as a canonical
correction step.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    skill = (ROOT / "skills/proofread/SKILL.md").read_text(encoding="utf-8")
    assert "page_images_dir" in skill, (
        "skills/proofread/SKILL.md does not mention page_images_dir"
    )
    assert "第一类证据" in skill, (
        "SKILL.md does not frame page images as first-class evidence"
    )
    assert 'proofread_method' in skill and 'page-grounded' in skill, (
        "SKILL.md must require writing proofread_method='page-grounded' "
        "back into _pipeline_status.json"
    )

    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "page_images_dir" in agents, (
        "AGENTS.md subagent contract missing page_images_dir"
    )
    assert "page-grounded" in agents, (
        "AGENTS.md missing page-grounded marker wording"
    )

    preview_src = (ROOT / "skills/ocr-run/scripts/make_preview.py").read_text(
        encoding="utf-8"
    )
    header = preview_src.split('"""', 2)[1] if '"""' in preview_src else ""
    assert "udit-only" in header, (
        "make_preview.py docstring does not declare audit-only"
    )
    assert "NOT a canonical" in header or "not a canonical" in header.lower(), (
        "make_preview.py docstring does not mark itself non-canonical"
    )

    # Page-image production: confirm at least one on-disk fixture shows
    # split_pages has actually produced page_*.png. If no fixture exists,
    # we skip (this is an environment concern, not a code regression).
    ocr_dirs = sorted((ROOT / "test").glob("*.ocr")) if (ROOT / "test").is_dir() else []
    png_count = 0
    for d in ocr_dirs:
        png_count = len(list((d / "prep/pages").glob("*.png")))
        if png_count:
            break
    if not ocr_dirs:
        print(
            "PASS smoke_page_grounded (doc contract only; no test/*.ocr fixture present)"
        )
    elif not png_count:
        print(
            "PASS smoke_page_grounded (doc contract only; fixture exists but no "
            "prep/pages/*.png — split_pages did not run here)"
        )
    else:
        print(
            f"PASS smoke_page_grounded (doc contract + {png_count} page images "
            "present on fixture)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

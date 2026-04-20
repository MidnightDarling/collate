#!/usr/bin/env python3
"""Proofread recipe regression: page packets + verifier are executable.

This locks the first non-doc-only part of the reset plan:

1. A workspace with `raw.md` + `prep/pages/page_*.png` can be converted into
   `review/page_review_packets.json`.
2. A page-grounded review without explicit page coverage is rejected.
3. The same review passes once it records `proofread_method: page-grounded`
   and `checked_pages: [...]` for every packet page.

Pre-fix, the repo had wording about page-grounded review but no deterministic
packet builder or completion verifier to make that recipe mechanically
executable by an agent.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_py(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, script, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def seed_workspace(ws: Path) -> None:
    (ws / "prep" / "pages").mkdir(parents=True, exist_ok=True)
    (ws / "review").mkdir(parents=True, exist_ok=True)
    (ws / "raw.md").write_text(
        "<!-- page 1 -->\n\n第一页正文。\n\n<!-- page 2 -->\n\n第二页正文。\n",
        encoding="utf-8",
    )
    for n in (1, 2):
        (ws / "prep" / "pages" / f"page_{n:03d}.png").write_bytes(b"png-stub")


def seed_unmarked_workspace(ws: Path) -> None:
    (ws / "prep" / "pages").mkdir(parents=True, exist_ok=True)
    (ws / "review").mkdir(parents=True, exist_ok=True)
    (ws / "raw.md").write_text(
        "第一页正文。\n\n第二页正文。\n",
        encoding="utf-8",
    )
    for n in (1, 2):
        (ws / "prep" / "pages" / f"page_{n:03d}.png").write_bytes(b"png-stub")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td) / "smoke_recipe.ocr"
        seed_workspace(ws)

        build = run_py(
            "skills/proofread/scripts/build_page_review_packets.py",
            "--workspace",
            str(ws),
        )
        assert build.returncode == 0, (
            f"build packets should pass\nstdout:\n{build.stdout}\nstderr:\n{build.stderr}"
        )
        packets = json.loads(
            (ws / "review" / "page_review_packets.json").read_text(encoding="utf-8")
        )
        assert [p["page"] for p in packets] == [1, 2], (
            f"unexpected packet pages: {packets}"
        )

        # Missing explicit page coverage -> reject.
        (ws / "review" / "raw.review.md").write_text(
            "---\nproofread_method: page-grounded\n---\n\n"
            "# 校对报告：smoke\n\n"
            "## Checklist 执行证明\n| 步骤 | 命中数 |\n|------|-------|\n| 结构预检 | 0 |\n",
            encoding="utf-8",
        )
        verify_fail = run_py(
            "skills/proofread/scripts/verify_page_grounded_review.py",
            "--workspace",
            str(ws),
        )
        assert verify_fail.returncode != 0, (
            "verifier must reject review without checked_pages coverage"
        )
        assert "checked_pages" in (verify_fail.stderr + verify_fail.stdout), (
            "rejection should explain missing checked_pages coverage"
        )

        # Full page coverage -> pass.
        (ws / "review" / "raw.review.md").write_text(
            "---\n"
            "proofread_method: page-grounded\n"
            "checked_pages: [1, 2]\n"
            "structure_approved: true\n"
            "---\n\n"
            "# 校对报告：smoke\n\n"
            "## Checklist 执行证明\n| 步骤 | 命中数 |\n|------|-------|\n| 结构预检 | 0 |\n",
            encoding="utf-8",
        )
        verify_ok = run_py(
            "skills/proofread/scripts/verify_page_grounded_review.py",
            "--workspace",
            str(ws),
        )
        assert verify_ok.returncode == 0, (
            f"verifier should pass\nstdout:\n{verify_ok.stdout}\nstderr:\n{verify_ok.stderr}"
        )

        # Multi-page review without explicit page markers must not invent
        # fake page packets by evenly slicing the text.
        ws_unmarked = Path(td) / "smoke_recipe_unmarked.ocr"
        seed_unmarked_workspace(ws_unmarked)
        build_fail = run_py(
            "skills/proofread/scripts/build_page_review_packets.py",
            "--workspace",
            str(ws_unmarked),
        )
        assert build_fail.returncode != 0, (
            "packet builder must reject multi-page raw.md without page markers"
        )
        assert "page markers" in (build_fail.stderr + build_fail.stdout).lower(), (
            "rejection should explain missing page markers"
        )

    print("PASS smoke_real_user_contract")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Workspace README must reflect done status after a successful pipeline run."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def seed_workspace(ws: Path) -> None:
    for sub in ("_internal", "review", "prep/pages", "previews", "output"):
        (ws / sub).mkdir(parents=True, exist_ok=True)
    (ws / "prep" / "pages" / "page_001.png").write_bytes(b"stub-png")
    (ws / "raw.md").write_text(
        "<!-- page 1 -->\n\n# smoke\n\ncontent\n",
        encoding="utf-8",
    )
    (ws / "meta.json").write_text(
        json.dumps(
            {
                "engine": "pdf-text-layer",
                "structural_risk": "high",
                "layout": "horizontal",
                "lang": "zh-hans",
                "pages": 1,
                "avg_confidence": None,
                "low_confidence_pages": [],
                "title": "smoke",
                "author": "tester",
                "year": "2026",
                "duration_seconds": 0.01,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (ws / "review" / "raw.review.md").write_text(
        "---\n"
        "proofread_method: page-grounded\n"
        "checked_pages: [1]\n"
        "structure_approved: true\n"
        "---\n\n"
        "# 校对报告：smoke\n\n"
        "## Checklist 执行证明\n| 步骤 | 命中数 |\n|------|-------|\n| 结构预检 | 0 |\n",
        encoding="utf-8",
    )
    (ws / "_internal" / "_pipeline_status.json").write_text(
        json.dumps(
            {
                "stage": "proofread",
                "status": "awaiting_agent_review",
                "ocr_engine": "pdf-text-layer",
                "proofread_method": "page-grounded",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td) / "smoke_readme_done.ocr"
        seed_workspace(ws)
        env = {**os.environ, "PYTHONPATH": str(ROOT / "scripts")}
        run = subprocess.run(
            [sys.executable, "scripts/run_full_pipeline.py", "--workspace", str(ws)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        assert run.returncode == 0, (
            f"pipeline should finish\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"
        )
        readme = (ws / "README.md").read_text(encoding="utf-8")
        assert "全部交付物已生成 — 完成 ✓" in readme, (
            "workspace README did not reflect done status"
        )
        assert "停在校对阶段" not in readme, (
            "workspace README still shows stale review-stage wording"
        )

    print("PASS smoke_readme_done_sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())

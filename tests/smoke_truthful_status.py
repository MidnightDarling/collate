#!/usr/bin/env python3
"""Bundle 1 regression: workspace_readme.py must trust _pipeline_status.json.

Seeds a workspace where every delivery file (raw.md, final.md, docx, wechat
HTML) is present but `_pipeline_status.json` reports status="error".
Pre-fix, workspace_readme.py inferred from file presence alone and would
cheerfully stamp "全部交付物已生成 — 完成 ✓" on top of a failed run.
Post-fix, it must surface the cause and refuse the completion line.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td) / "smoke_truth.ocr"
        for sub in ("_internal", "review", "output", "previews"):
            (ws / sub).mkdir(parents=True, exist_ok=True)
        # Seed the workspace as if every stage had completed — including
        # review and diff-review — so the pipeline_stage cascade reaches
        # its terminal `has_docx and has_mp` branch, which is the exact
        # branch Codex caught silently rubber-stamping failed runs.
        (ws / "raw.md").write_text("# test\ncontent\n", encoding="utf-8")
        (ws / "final.md").write_text("# test\ncontent\n", encoding="utf-8")
        (ws / "review" / "raw.review.md").write_text(
            "# 校对\n## A\n无\n## B\n无\n## C\n无\n", encoding="utf-8"
        )
        (ws / "previews" / "diff-review.html").write_text(
            "<html></html>", encoding="utf-8"
        )
        (ws / "output" / "final_final.docx").write_bytes(b"")
        (ws / "output" / "final_wechat.html").write_text("", encoding="utf-8")
        (ws / "output" / "final_wechat.md").write_text("", encoding="utf-8")

        status = {
            "stage": "failed",
            "status": "error",
            "error": "smoke-injection",
            "cause": "artificial failure for smoke_truthful_status",
        }
        (ws / "_internal" / "_pipeline_status.json").write_text(
            json.dumps(status, ensure_ascii=False), encoding="utf-8"
        )

        env = {**os.environ, "PYTHONPATH": str(ROOT / "scripts")}
        result = subprocess.run(
            [sys.executable, "scripts/workspace_readme.py", "--workspace", str(ws)],
            cwd=ROOT, env=env, capture_output=True, text=True,
        )
        assert result.returncode == 0, (
            f"workspace_readme.py failed: rc={result.returncode}\n"
            f"stderr:\n{result.stderr}"
        )

        readme = (ws / "README.md").read_text(encoding="utf-8")
        assert "完成 ✓" not in readme, (
            "README lies about completion despite status=error:\n" + readme
        )
        assert "报错" in readme or "artificial failure" in readme, (
            "README failed to surface the injected cause:\n" + readme
        )

    print("PASS smoke_truthful_status")
    return 0


if __name__ == "__main__":
    sys.exit(main())

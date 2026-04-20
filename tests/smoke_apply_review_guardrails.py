#!/usr/bin/env python3
"""apply_review must not leak editorial instructions into final.md."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td) / "smoke_apply.ocr"
        ws.mkdir(parents=True, exist_ok=True)
        raw = ws / "raw.md"
        review = ws / "review.md"
        out = ws / "final.md"

        raw.write_text(
            "# 标题\n\n这一行是上一段。\n问题行\n下一行是后文。\n",
            encoding="utf-8",
        )
        review.write_text(
            "# 校对报告：smoke\n\n"
            "## A 类 — 极可能是 OCR 错\n\n"
            "### A1. 操作性建议不得入正文 · Line 4\n\n"
            "**原文**：\n"
            "> 问题行\n\n"
            "**建议**：删除该行并与上下文连读\n\n"
            "**理由**：这是编辑动作，不是字面替换。\n",
            encoding="utf-8",
        )

        run = subprocess.run(
            [
                sys.executable,
                "scripts/apply_review.py",
                "--raw",
                str(raw),
                "--review",
                str(review),
                "--out",
                str(out),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert run.returncode == 0, (
            f"apply_review should run\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"
        )
        text = out.read_text(encoding="utf-8")
        assert "删除该行并与上下文连读" not in text, (
            "editorial instruction leaked into final.md"
        )
        assert "问题行" in text, (
            "non-literal instruction should be skipped rather than deleting text"
        )

    print("PASS smoke_apply_review_guardrails")
    return 0


if __name__ == "__main__":
    sys.exit(main())

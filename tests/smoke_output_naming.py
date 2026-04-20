#!/usr/bin/env python3
"""Workspace exports should honour metadata naming when provenance is absent."""
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


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td) / "smoke_naming.ocr"
        (ws / "output").mkdir(parents=True, exist_ok=True)
        (ws / "final.md").write_text("# 标题\n\n正文。\n", encoding="utf-8")
        (ws / "meta.json").write_text(
            json.dumps(
                {
                    "title": "标题",
                    "author": "作者",
                    "year": "2026",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        docx = run_py(
            "skills/to-docx/scripts/md_to_docx.py",
            "--input",
            str(ws / "final.md"),
            "--title-from-first-h1",
        )
        assert docx.returncode == 0, (
            f"docx export should pass\nstdout:\n{docx.stdout}\nstderr:\n{docx.stderr}"
        )
        html = run_py(
            "skills/mp-format/scripts/md_to_wechat.py",
            "--input",
            str(ws / "final.md"),
            "--also-markdown",
        )
        assert html.returncode == 0, (
            f"wechat export should pass\nstdout:\n{html.stdout}\nstderr:\n{html.stderr}"
        )

        expected = [
            ws / "output" / "标题_作者_2026_final.docx",
            ws / "output" / "标题_作者_2026_wechat.html",
            ws / "output" / "标题_作者_2026_wechat.md",
        ]
        missing = [str(p) for p in expected if not p.exists()]
        assert not missing, f"expected metadata-based filenames missing: {missing}"

    print("PASS smoke_output_naming")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Canonical output reruns should prune stale title-derived siblings."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_py(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, script, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td) / "cleanup_smoke.ocr"
        out = ws / "output"
        out.mkdir(parents=True, exist_ok=True)
        final = ws / "final.md"
        final.write_text("# 新標題——校對後\n\n正文。\n", encoding="utf-8")

        stale = [
            out / "舊標題_未知作者_未知年份_final.docx",
            out / "舊標題_未知作者_未知年份_wechat.html",
            out / "舊標題_未知作者_未知年份_wechat.md",
        ]
        for path in stale:
            path.write_text("stale", encoding="utf-8")

        docx = run_py(
            "skills/to-docx/scripts/md_to_docx.py",
            "--input",
            str(final),
            "--title-from-first-h1",
        )
        assert docx.returncode == 0, (
            f"docx export should pass\nstdout:\n{docx.stdout}\nstderr:\n{docx.stderr}"
        )

        wechat = run_py(
            "skills/mp-format/scripts/md_to_wechat.py",
            "--input",
            str(final),
            "--also-markdown",
        )
        assert wechat.returncode == 0, (
            f"wechat export should pass\nstdout:\n{wechat.stdout}\nstderr:\n{wechat.stderr}"
        )

        docx_outputs = sorted(out.glob("*_final.docx"))
        html_outputs = sorted(out.glob("*_wechat.html"))
        md_outputs = sorted(out.glob("*_wechat.md"))

        assert [p.name for p in docx_outputs] == ["新標題——校對後_未知作者_未知年份_final.docx"], (
            f"stale docx should be pruned: {docx_outputs}"
        )
        assert [p.name for p in html_outputs] == ["新標題——校對後_未知作者_未知年份_wechat.html"], (
            f"stale html should be pruned: {html_outputs}"
        )
        assert [p.name for p in md_outputs] == ["新標題——校對後_未知作者_未知年份_wechat.md"], (
            f"stale markdown should be pruned: {md_outputs}"
        )

    print("PASS smoke_output_cleanup")
    return 0


if __name__ == "__main__":
    sys.exit(main())

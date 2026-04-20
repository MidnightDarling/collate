#!/usr/bin/env python3
"""MinerU reflow must preserve explicit page markers for downstream review."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        content = td_path / "content_list_v2.json"
        out = td_path / "raw.md"
        content.write_text(
            json.dumps(
                [
                    [
                        {
                            "type": "title",
                            "content": {
                                "level": 1,
                                "title_content": [{"type": "text", "content": "标题"}],
                            },
                        },
                        {
                            "type": "paragraph",
                            "content": {
                                "paragraph_content": [{"type": "text", "content": "第一页正文。"}],
                            },
                        },
                    ],
                    [
                        {
                            "type": "paragraph",
                            "content": {
                                "paragraph_content": [{"type": "text", "content": "第二页正文。"}],
                            },
                        }
                    ],
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        run = subprocess.run(
            [
                sys.executable,
                "skills/ocr-run/scripts/reflow_mineru.py",
                "--content-list",
                str(content),
                "--out",
                str(out),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert run.returncode == 0, (
            f"reflow should pass\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"
        )
        text = out.read_text(encoding="utf-8")
        assert "<!-- page 1 -->" in text and "<!-- page 2 -->" in text, (
            "raw.md must preserve explicit page markers"
        )

    print("PASS smoke_reflow_page_markers")
    return 0


if __name__ == "__main__":
    sys.exit(main())

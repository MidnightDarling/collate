#!/usr/bin/env python3
"""OCR resilience regression: local timeout + incomplete cloud fallback."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import run_full_pipeline  # type: ignore[import-not-found]  # noqa: E402


def assert_local_timeout() -> None:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        fake_bin = td_path / "bin"
        fake_bin.mkdir()
        fake_mineru = fake_bin / "mineru"
        fake_mineru.write_text("#!/bin/sh\nsleep 5\n", encoding="utf-8")
        fake_mineru.chmod(0o755)
        pdf = td_path / "stub.pdf"
        pdf.write_bytes(b"%PDF-1.4 stub\n")
        out = td_path / "stub.ocr"

        env = os.environ.copy()
        env["PATH"] = f"{fake_bin}:{env['PATH']}"
        env["COLLATE_MINERU_QUIET_TIMEOUT"] = "1"
        env["COLLATE_MINERU_TOTAL_TIMEOUT"] = "10"

        run = subprocess.run(
            [
                sys.executable,
                "skills/ocr-run/scripts/run_mineru.py",
                "--pdf",
                str(pdf),
                "--out",
                str(out),
                "--lang",
                "ch",
            ],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        assert run.returncode == 124, (
            f"local timeout should exit 124\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"
        )
        assert "produced no job files" in (run.stderr + run.stdout), (
            "timeout should explain artifact-free local MinerU fallback"
        )


def assert_try_ocr_skips_incomplete_cloud() -> None:
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td) / "smoke_cloud_incomplete.ocr"
        ws.mkdir()
        (ws / "_internal").mkdir()
        (ws / "source.pdf").write_bytes(b"%PDF-1.4 stub\n")

        original_run = subprocess.run

        def fake_run(cmd, **kwargs):
            script = next(
                (c for c in cmd if isinstance(c, str) and c.endswith(".py")),
                "",
            )
            if script.endswith("run_mineru.py"):
                return SimpleNamespace(
                    returncode=1,
                    stderr="[stub] local MinerU unavailable\n",
                    stdout="",
                )
            if script.endswith("mineru_client.py"):
                out_idx = cmd.index("--out") + 1
                out = Path(cmd[out_idx])
                out.mkdir(parents=True, exist_ok=True)
                (out / "raw.md").write_text("# cloud raw\n\n没有页标记。\n", encoding="utf-8")
                (out / "meta.json").write_text(
                    '{"engine": "mineru-cloud", "pages": 2}',
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=0, stderr="", stdout="")
            if script.endswith("extract_text_layer.py"):
                out_idx = cmd.index("--out") + 1
                out = Path(cmd[out_idx])
                out.mkdir(parents=True, exist_ok=True)
                (out / "raw.md").write_text(
                    "<!-- structural-risk: high -->\n\n<!-- page 1 -->\n\n第一页。\n\n<!-- page 2 -->\n\n第二页。\n",
                    encoding="utf-8",
                )
                (out / "meta.json").write_text(
                    '{"engine": "pdf-text-layer", "structural_risk": "high", "pages": 2}',
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=0, stderr="", stdout="")
            return original_run(cmd, **kwargs)

        env_backup = dict(os.environ)
        os.environ["MINERU_API_KEY"] = "stub-key"
        os.environ["COLLATE_ALLOW_TEXTLAYER"] = "1"
        try:
            with patch("subprocess.run", side_effect=fake_run):
                engine, attempts = run_full_pipeline.try_ocr(ws)
        finally:
            os.environ.clear()
            os.environ.update(env_backup)

        assert engine == "text-layer", (
            f"incomplete cloud output should fall through to text-layer, got {engine!r}"
        )
        assert any("mineru-cloud rc=0 but page packets remain unavailable" in a for a in attempts), (
            f"cloud incomplete attempt missing from log: {attempts}"
        )
        assert any("text-layer rc=0" in a for a in attempts), (
            f"text-layer success missing from log: {attempts}"
        )


def main() -> int:
    assert_local_timeout()
    assert_try_ocr_skips_incomplete_cloud()
    print("PASS smoke_ocr_resilience")
    return 0


if __name__ == "__main__":
    sys.exit(main())

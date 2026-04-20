#!/usr/bin/env python3
"""Bundle 2 regression: try_ocr reaches text-layer when MinerU is unavailable.

Imports `try_ocr` directly and monkeypatches `subprocess.run` so that
run-mineru fails, mineru-cloud is skipped (no MINERU_API_KEY), and
extract_text_layer.py succeeds. Asserts the returned engine name is
"text-layer" and the attempts log captures every step — the evidence the
downstream gate relies on to know which path produced raw.md.

Pre-fix, try_ocr had a two-strategy loop and no return value; text-layer
was only reachable by manually invoking extract_text_layer.py, which the
audit flagged as shunting OCR correction labour back onto the human.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_full_pipeline  # type: ignore[import-not-found]  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td) / "smoke_fallback.ocr"
        ws.mkdir()
        (ws / "source.pdf").write_bytes(b"%PDF-1.4 stub - never opened by the test\n")

        original_run = subprocess.run

        def fake_run(cmd, **kwargs):
            script = next(
                (c for c in cmd if isinstance(c, str) and c.endswith(".py")),
                "",
            )
            if script.endswith("run_mineru.py"):
                return SimpleNamespace(
                    returncode=1,
                    stderr="[stub] local MinerU unavailable (smoke test)\n",
                    stdout="",
                )
            if script.endswith("mineru_client.py"):
                return SimpleNamespace(
                    returncode=1,
                    stderr="[stub] cloud unreachable\n",
                    stdout="",
                )
            if script.endswith("extract_text_layer.py"):
                out_idx = cmd.index("--out") + 1
                out = Path(cmd[out_idx])
                out.mkdir(parents=True, exist_ok=True)
                (out / "raw.md").write_text(
                    "<!-- structural-risk: high -->\n\n# stub\n",
                    encoding="utf-8",
                )
                (out / "meta.json").write_text(
                    '{"engine": "pdf-text-layer", "structural_risk": "high", "pages": 1}',
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=0, stderr="", stdout="")
            return original_run(cmd, **kwargs)

        env_backup = dict(os.environ)
        os.environ.pop("MINERU_API_KEY", None)
        os.environ["COLLATE_ALLOW_TEXTLAYER"] = "1"
        try:
            with patch("subprocess.run", side_effect=fake_run):
                engine, attempts = run_full_pipeline.try_ocr(ws)
        finally:
            os.environ.clear()
            os.environ.update(env_backup)

        assert engine == "text-layer", (
            f"expected engine='text-layer', got {engine!r}\nattempts={attempts}"
        )
        assert any("run-mineru rc=1" in a for a in attempts), (
            f"attempts missing run-mineru failure: {attempts}"
        )
        assert any("mineru-cloud skipped=not-enabled" in a for a in attempts), (
            f"attempts missing cloud skip: {attempts}"
        )
        assert any("text-layer rc=0" in a for a in attempts), (
            f"attempts missing text-layer success: {attempts}"
        )

        meta = (ws / "meta.json").read_text(encoding="utf-8")
        assert '"engine": "pdf-text-layer"' in meta, (
            f"meta.json engine field missing: {meta}"
        )
        assert '"structural_risk": "high"' in meta, (
            f"meta.json structural_risk missing: {meta}"
        )

    print(f"PASS smoke_fallback_chain (attempts={attempts})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

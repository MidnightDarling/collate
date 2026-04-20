#!/usr/bin/env python3
"""Bundle 1 regression: workspace_readme.py must trust _pipeline_status.json.

Two scenarios, each exercising a distinct failure shape Codex's audit surfaced:

A. FULL DELIVERY + status=error. Every stage's output file is on disk
   (raw.md, final.md, review, diff-review.html, docx, wechat html/md) but
   `_pipeline_status.json` reports status="error". Pre-fix, the has_docx-
   and-has_mp branch cheerfully stamped "全部交付物已生成 — 完成 ✓" on top
   of a failed run.

B. PARTIAL PROGRESS + status=error. Only raw.md on disk (from a scan-only
   text-layer rc=4 that wrote an empty shell before returning) — no review,
   no output. Pre-fix, the `has_raw and not has_review` branch said "OCR
   已完成 — 待校对", masking a concrete OCR failure. This is the exact
   shape the end-to-end Codex-fixture run exposed after Bundles 2-5 landed.

Both scenarios must now render a "Pipeline 报错" line with the injected
cause, and must never emit "完成 ✓" or "OCR 已完成 — 待校对".
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_readme(ws: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(ROOT / "scripts")}
    return subprocess.run(
        [sys.executable, "scripts/workspace_readme.py", "--workspace", str(ws)],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )


def _assert_truthful(readme: str, label: str) -> None:
    assert "完成 ✓" not in readme, (
        f"{label}: README lies with '完成 ✓' despite status=error:\n{readme}"
    )
    assert "OCR 已完成 — 待校对" not in readme, (
        f"{label}: README claims OCR done despite status=error:\n{readme}"
    )
    assert "报错" in readme, (
        f"{label}: README failed to surface the error:\n{readme}"
    )


def scenario_full_delivery(td: Path) -> None:
    """A: every delivery file exists but status=error."""
    ws = td / "smoke_truth_full.ocr"
    for sub in ("_internal", "review", "output", "previews"):
        (ws / sub).mkdir(parents=True, exist_ok=True)
    (ws / "raw.md").write_text("# test\ncontent\n", encoding="utf-8")
    (ws / "final.md").write_text("# test\ncontent\n", encoding="utf-8")
    (ws / "review" / "raw.review.md").write_text(
        "# 校对\n## A\n无\n## B\n无\n## C\n无\n", encoding="utf-8"
    )
    (ws / "previews" / "diff-review.html").write_text("<html></html>", encoding="utf-8")
    (ws / "output" / "final_final.docx").write_bytes(b"")
    (ws / "output" / "final_wechat.html").write_text("", encoding="utf-8")
    (ws / "output" / "final_wechat.md").write_text("", encoding="utf-8")
    status = {
        "stage": "failed", "status": "error",
        "error": "smoke-injection-full",
        "cause": "artificial full-delivery failure",
    }
    (ws / "_internal" / "_pipeline_status.json").write_text(
        json.dumps(status, ensure_ascii=False), encoding="utf-8"
    )

    r = _run_readme(ws)
    assert r.returncode == 0, f"A: workspace_readme failed: {r.stderr}"
    readme = (ws / "README.md").read_text(encoding="utf-8")
    _assert_truthful(readme, "A[full-delivery]")
    assert "artificial full-delivery failure" in readme, (
        f"A: README missed injected cause:\n{readme}"
    )


def scenario_partial_progress(td: Path) -> None:
    """B: only raw.md exists (scan-only text-layer leftover) + status=error."""
    ws = td / "smoke_truth_partial.ocr"
    (ws / "_internal").mkdir(parents=True, exist_ok=True)
    (ws / "raw.md").write_text("", encoding="utf-8")  # empty shell from rc=4
    status = {
        "stage": "failed", "status": "error",
        "error": "ocr-run failed: text-layer rc=4: scan-only PDF",
        "cause": "See preserved workspace artifacts and preceding command output.",
    }
    (ws / "_internal" / "_pipeline_status.json").write_text(
        json.dumps(status, ensure_ascii=False), encoding="utf-8"
    )

    r = _run_readme(ws)
    assert r.returncode == 0, f"B: workspace_readme failed: {r.stderr}"
    readme = (ws / "README.md").read_text(encoding="utf-8")
    _assert_truthful(readme, "B[partial-progress]")
    assert "Pipeline 报错（failed）" in readme, (
        f"B: README did not surface the top-level error override:\n{readme}"
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        scenario_full_delivery(root)
        scenario_partial_progress(root)
    print("PASS smoke_truthful_status (A: full-delivery, B: partial-progress)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

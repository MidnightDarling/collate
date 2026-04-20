#!/usr/bin/env python3
"""Bundle 4 regression: export blocked unless structure has been attested.

Exercises three scenarios end-to-end through run_full_pipeline.py:

  A. Text-layer workspace (structural_risk=high) with a mechanically valid
     page-grounded review, but no `structure_approved: true` attestation.
     Expectation: exit code 11, status stage=fidelity_gate, no docx/wechat
     artifacts.

  B. Same skeleton, but the review carries the structural attestation too.
     Expectation: exit 0, `_structure_approved` marker written, export
     artifacts produced.

  C. Structurally approved review, but one A-class item still misses after
     `apply_review`.
     Expectation: exit code 13, status stage=diff_review, no docx/wechat.

Pre-fix, a text-layer fallback workspace could slide all the way to
`final.docx` without anyone approving its structural skeleton, shipping
documents whose layout had never been audited. The gate breaks that
slide.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def seed_workspace(
    ws: Path,
    *,
    approved: bool,
    proofread_method: str | None,
    review_body: str | None = None,
) -> None:
    for sub in ("_internal", "review", "prep/pages", "previews", "output"):
        (ws / sub).mkdir(parents=True, exist_ok=True)
    (ws / "prep" / "pages" / "page_001.png").write_bytes(b"stub-png")
    (ws / "raw.md").write_text(
        "<!-- structural-risk: high; fallback: pdf-text-layer; requires "
        "page-grounded proofread -->\n\n# smoke\n\ncontent\n",
        encoding="utf-8",
    )
    (ws / "meta.json").write_text(
        json.dumps({
            "engine": "pdf-text-layer",
            "structural_risk": "high",
            "layout": "horizontal",
            "lang": "zh-hans",
            "pages": 1,
            "avg_confidence": None,
            "low_confidence_pages": [],
            "title": "smoke",
            "author": None,
            "year": None,
            "duration_seconds": 0.01,
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    frontmatter = [
        "---",
        "proofread_method: page-grounded",
        "checked_pages: [1]",
    ]
    if approved:
        frontmatter.append("structure_approved: true")
    frontmatter = "---\n" + "\n".join(frontmatter[1:]) + "\n---\n\n"
    body = review_body or (
        "# 校对清单\n## A 类 OCR 错\n无\n"
        "## B 类 规范\n无\n## C 类 存疑\n无\n"
    )
    (ws / "review" / "raw.review.md").write_text(frontmatter + body, encoding="utf-8")
    status: dict = {
        "stage": "proofread",
        "status": "awaiting_agent_review",
        "ocr_engine": "pdf-text-layer",
    }
    if proofread_method:
        status["proofread_method"] = proofread_method
    (ws / "_internal" / "_pipeline_status.json").write_text(
        json.dumps(status, ensure_ascii=False), encoding="utf-8"
    )


def run_pipeline(ws: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(ROOT / "scripts")}
    return subprocess.run(
        [sys.executable, "scripts/run_full_pipeline.py", "--workspace", str(ws)],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )


def main() -> int:
    # Scenario A: gate must refuse.
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td) / "smoke_gate_refuse.ocr"
        seed_workspace(ws, approved=False, proofread_method=None)
        r = run_pipeline(ws)
        assert r.returncode == 11, (
            f"A: expected rc=11, got {r.returncode}\n"
            f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
        )
        status = json.loads(
            (ws / "_internal" / "_pipeline_status.json").read_text(encoding="utf-8")
        )
        assert status.get("stage") == "fidelity_gate", (
            f"A: stage wrong: {status}"
        )
        assert status.get("status") == "error", (
            f"A: status not error: {status}"
        )
        docx = list((ws / "output").glob("*.docx"))
        assert not docx, f"A: docx must not exist when gate refuses: {docx}"

    # Scenario B: gate must pass and export must complete.
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td) / "smoke_gate_pass.ocr"
        seed_workspace(ws, approved=True, proofread_method="page-grounded")
        r = run_pipeline(ws)
        assert r.returncode == 0, (
            f"B: expected rc=0, got {r.returncode}\n"
            f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
        )
        marker = ws / "_internal" / "_structure_approved"
        assert marker.is_file(), (
            "B: apply_review did not emit _structure_approved marker"
        )

    # Scenario C: diff-review must refuse export if an A item still misses.
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td) / "smoke_gate_diff_refuse.ocr"
        seed_workspace(
            ws,
            approved=True,
            proofread_method="page-grounded",
            review_body=(
                "# 校对报告：smoke\n\n"
                "## A 类 — 极可能是 OCR 错\n\n"
                "### A1. 刻意留一个漏改项 · Line 3\n"
                "> 不存在的原句\n"
                "**建议**：修正后的句子\n"
                "**理由**：用于锁定 diff-review gate。\n"
            ),
        )
        (ws / "raw.md").write_text(
            "<!-- structural-risk: high; fallback: pdf-text-layer; requires "
            "page-grounded proofread -->\n\n# smoke\n\n原句。\n",
            encoding="utf-8",
        )
        r = run_pipeline(ws)
        assert r.returncode == 13, (
            f"C: expected rc=13, got {r.returncode}\n"
            f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
        )
        status = json.loads(
            (ws / "_internal" / "_pipeline_status.json").read_text(encoding="utf-8")
        )
        assert status.get("stage") == "diff_review", (
            f"C: stage wrong: {status}"
        )
        assert status.get("status") == "error", (
            f"C: status not error: {status}"
        )
        html = list((ws / "output").glob("*_wechat.html"))
        docx = list((ws / "output").glob("*.docx"))
        assert not html and not docx, (
            f"C: exports must not exist when A items still miss: html={html} docx={docx}"
        )

    print("PASS smoke_fidelity_gate (A: refused rc=11, B: passed rc=0, C: refused rc=13)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

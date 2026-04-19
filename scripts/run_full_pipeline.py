#!/usr/bin/env python3
"""One-command mechanical orchestrator for the OCR pipeline workspace."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from pipeline_status import infer_workspace, write_status


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], stage: str) -> None:
    print(f"[pipeline] {stage}: {' '.join(map(str, cmd))}")
    rc = subprocess.run(cmd, cwd=ROOT, check=False).returncode
    if rc != 0:
        raise RuntimeError(f"{stage} failed with exit code {rc}")


def ensure_workspace(pdf: Path, workspace: Path) -> None:
    for subdir in ("prep", "previews", "review", "output", "assets", "_internal"):
        (workspace / subdir).mkdir(parents=True, exist_ok=True)
    if not (workspace / "prep" / "original.pdf").exists():
        shutil.copy2(pdf, workspace / "prep" / "original.pdf")
    if not (workspace / "source.pdf").exists():
        shutil.copy2(pdf, workspace / "source.pdf")


def resolve_pdf_hint(args_pdf: Path | None, workspace: Path) -> Path | None:
    if args_pdf is not None:
        return args_pdf
    for candidate in (
        workspace / "prep" / "original.pdf",
        workspace / "source.pdf",
    ):
        if candidate.is_file():
            return candidate
    return None


def prep_stage(pdf: Path, workspace: Path) -> None:
    prep = workspace / "prep"
    if not (prep / "cleaned.pdf").exists():
        run([sys.executable, "skills/prep-scan/scripts/split_pages.py", "--pdf", str(prep / "original.pdf"), "--out", str(prep / "pages"), "--dpi", "300"], "split-pages")
        run([sys.executable, "skills/prep-scan/scripts/dewatermark.py", "--in", str(prep / "pages"), "--out", str(prep / "cleaned_pages")], "dewatermark")
        run([sys.executable, "skills/prep-scan/scripts/remove_margins.py", "--in", str(prep / "cleaned_pages"), "--out", str(prep / "trimmed_pages"), "--header-ratio", "0.08", "--footer-ratio", "0.08"], "remove-margins")
        run([sys.executable, "skills/prep-scan/scripts/pages_to_pdf.py", "--in", str(prep / "trimmed_pages"), "--out", str(prep / "cleaned.pdf")], "pages-to-pdf")
        shutil.copy2(prep / "cleaned.pdf", workspace / "source.pdf")
    if not (workspace / "previews" / "visual-prep.html").exists():
        run([sys.executable, "skills/visual-preview/scripts/visualize_prep.py", "--prep-dir", str(prep), "--out", str(workspace / "previews" / "visual-prep.html")], "visual-preview")


def try_ocr(workspace: Path) -> None:
    if (workspace / "raw.md").exists():
        return
    source = workspace / "source.pdf"
    local = [sys.executable, "skills/ocr-run/scripts/run_mineru.py", "--pdf", str(source), "--out", str(workspace), "--lang", "ch"]
    cloud = [sys.executable, "skills/ocr-run/scripts/mineru_client.py", "--pdf", str(source), "--out", str(workspace), "--layout", "horizontal", "--lang", "zh-hans", "--poll-interval", "10", "--timeout", "1800"]
    errors: list[str] = []
    for name, cmd, enabled in (
        ("run-mineru", local, True),
        ("mineru-cloud", cloud, bool(os.environ.get("MINERU_API_KEY"))),
    ):
        if not enabled:
            continue
        rc = subprocess.run(cmd, cwd=ROOT, check=False).returncode
        if rc == 0 and (workspace / "raw.md").exists():
            return
        errors.append(f"{name} rc={rc}")
    raise RuntimeError("ocr-run failed: " + ", ".join(errors))


def post_ocr_stage(workspace: Path) -> int:
    review = workspace / "review" / "raw.review.md"
    final = workspace / "final.md"
    if not review.exists():
        write_status(workspace, {"stage": "proofread", "status": "awaiting_agent_review", "next_step": "Generate review/raw.review.md with historical-proofreader, then rerun this command.", "files_preserved": [str(workspace / "raw.md"), str(workspace / "meta.json"), str(workspace / "previews" / "visual-prep.html")]})
        print("[pipeline] OCR ready. Awaiting review/raw.review.md before auto-applying and exporting.")
        return 10
    if not final.exists():
        run([sys.executable, "scripts/apply_review.py", "--raw", str(workspace / "raw.md"), "--review", str(review), "--out", str(final)], "apply-review")
    run([sys.executable, "skills/diff-review/scripts/md_diff.py", "--raw", str(workspace / "raw.md"), "--final", str(final), "--review", str(review), "--out", str(workspace / "previews" / "diff-review.html"), "--summary", str(workspace / "review" / "diff-summary.md")], "diff-review")
    run([sys.executable, "skills/to-docx/scripts/md_to_docx.py", "--input", str(final), "--title-from-first-h1"], "to-docx")
    run([sys.executable, "skills/mp-format/scripts/md_to_wechat.py", "--input", str(final), "--also-markdown"], "mp-format")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path)
    ap.add_argument("--workspace", type=Path)
    args = ap.parse_args()

    if args.pdf is None and args.workspace is None:
        print("pass --pdf <file> or --workspace <dir>", file=sys.stderr)
        return 2
    workspace = infer_workspace(args.pdf, args.workspace)
    pdf = resolve_pdf_hint(args.pdf, workspace)
    try:
        if pdf is None and not (workspace / "raw.md").exists():
            raise RuntimeError("no input PDF found in workspace (expected prep/original.pdf or source.pdf)")
        if pdf is not None:
            ensure_workspace(pdf, workspace)
        if pdf is not None and not (workspace / "raw.md").exists():
            prep_stage(pdf, workspace)
            try_ocr(workspace)
        result = post_ocr_stage(workspace)
        subprocess.run([sys.executable, "scripts/workspace_readme.py", "--workspace", str(workspace)], cwd=ROOT, check=False)
        if result == 0:
            write_status(workspace, {"stage": "done", "status": "ok", "next_step": "Review output/ artifacts and README.md.", "files_preserved": [str(workspace / "output"), str(workspace / "previews")]})
        return result
    except Exception as exc:
        subprocess.run([sys.executable, "scripts/workspace_readme.py", "--workspace", str(workspace)], cwd=ROOT, check=False)
        write_status(workspace, {"stage": "failed", "status": "error", "error": str(exc), "cause": "See preserved workspace artifacts and preceding command output.", "next_step": "Inspect _pipeline_status.json and rerun the failed stage after fixing the blocker.", "files_preserved": [str(workspace), str(workspace / "previews"), str(workspace / "_internal")]})
        print(f"stage: failed\nerror: {exc}\ncause: see command output above\nnext_step: inspect {workspace / '_internal' / '_pipeline_status.json'}\nfiles_preserved: [{workspace}]", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

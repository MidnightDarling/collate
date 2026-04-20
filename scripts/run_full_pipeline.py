#!/usr/bin/env python3
"""One-command mechanical orchestrator for the OCR pipeline workspace."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from pipeline_status import infer_workspace, read_status, write_status


def _engine_from_meta(workspace: Path) -> str | None:
    """Return meta.json.engine if readable, else None."""
    meta_path = workspace / "meta.json"
    if not meta_path.is_file():
        return None
    try:
        return json.loads(meta_path.read_text(encoding="utf-8")).get("engine")
    except Exception:
        return None


def _meta(workspace: Path) -> dict:
    """Return meta.json as a dict, or {} on error/missing."""
    meta_path = workspace / "meta.json"
    if not meta_path.is_file():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def fidelity_gate(workspace: Path) -> tuple[bool, str]:
    """Refuse export unless page-grounded proofread has attested the skeleton.

    Two independent conditions fire the gate:

    1. ``meta.json.structural_risk == "high"`` (set by the text-layer
       fallback) — no layout inference was run, so the review must
       explicitly ``structure_approved: true`` in its frontmatter; that
       approval is persisted as ``_internal/_structure_approved``.
    2. ``_pipeline_status.json.proofread_method`` must be ``"page-grounded"``
       — the proofread subagent writes this after walking the PNG originals.
       Its absence means the review came from a purely-textual pass (or a
       legacy flow), which is what the Codex audit caught: the subagent
       cannot judge OCR truth without the original image.

    Returns ``(ok, reason)``. When ``ok=False``, ``reason`` is a short,
    human-readable cause suitable for ``_pipeline_status.error``.
    """
    meta = _meta(workspace)
    if meta.get("structural_risk") == "high":
        marker = workspace / "_internal" / "_structure_approved"
        if not marker.is_file():
            return (
                False,
                "structural review required (text-layer fallback) "
                "but review/raw.review.md lacks `structure_approved: true`",
            )
    status = read_status(workspace) or {}
    if status.get("proofread_method") != "page-grounded":
        return (
            False,
            "page-grounded proofread not recorded "
            "(status.proofread_method != 'page-grounded')",
        )
    return True, ""


ROOT = Path(__file__).resolve().parents[1]


def _has_page_markers(raw_path: Path) -> bool:
    if not raw_path.is_file():
        return False
    return "<!-- page " in raw_path.read_text(encoding="utf-8", errors="ignore").lower()


def _has_page_sidecar(workspace: Path) -> bool:
    return (workspace / "_internal" / "page_texts.json").is_file()


def _review_packets_ready(workspace: Path) -> bool:
    return _has_page_markers(workspace / "raw.md") or _has_page_sidecar(workspace)


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


def ensure_page_review_packets(workspace: Path) -> Path:
    packets = workspace / "review" / "page_review_packets.json"
    if packets.is_file():
        return packets
    run(
        [
            sys.executable,
            "skills/proofread/scripts/build_page_review_packets.py",
            "--workspace",
            str(workspace),
        ],
        "build-page-review-packets",
    )
    return packets


def verify_page_grounded_review(workspace: Path) -> tuple[bool, str]:
    completed = subprocess.run(
        [
            sys.executable,
            "skills/proofread/scripts/verify_page_grounded_review.py",
            "--workspace",
            str(workspace),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        return True, (completed.stdout or "").strip()
    reason = (completed.stderr or completed.stdout or "").strip()
    return False, reason or "verify_page_grounded_review failed"


def try_ocr(workspace: Path) -> tuple[str, list[str]]:
    """Run OCR fallback chain. Returns (engine_name, attempts).

    engine_name is the first strategy that produced raw.md.
    attempts is the full log of strategies tried, each entry:
        "<name> rc=<rc>[: <stderr-tail>]"

    The chain is:
      1. run-mineru (local MinerU) — always enabled
      2. mineru-cloud — enabled iff MINERU_API_KEY is set
      3. text-layer  — enabled iff COLLATE_ALLOW_TEXTLAYER != "0"
         (default on; set COLLATE_ALLOW_TEXTLAYER=0 to opt out for audits)

    text-layer is the documented canonical fallback. meta.json.engine will
    be "pdf-text-layer" (or "pdf-text-layer-empty" if the PDF had no text
    layer at all), which flows into the downstream fidelity gate.
    """
    source = workspace / "source.pdf"
    text_layer_source = workspace / "prep" / "original.pdf"
    if not text_layer_source.is_file():
        text_layer_source = source
    local = [sys.executable, "skills/ocr-run/scripts/run_mineru.py", "--pdf", str(source), "--out", str(workspace), "--lang", "ch"]
    cloud = [sys.executable, "skills/ocr-run/scripts/mineru_client.py", "--pdf", str(source), "--out", str(workspace), "--layout", "horizontal", "--lang", "zh-hans", "--poll-interval", "10", "--timeout", "1800"]
    text_layer = [sys.executable, "skills/ocr-run/scripts/extract_text_layer.py", "--pdf", str(text_layer_source), "--out", str(workspace), "--layout", "horizontal", "--lang", "zh-hans"]

    if (workspace / "raw.md").exists() and _review_packets_ready(workspace):
        existing = _engine_from_meta(workspace) or "unknown"
        return existing, [f"cache-hit rc=0 engine={existing}"]

    attempts: list[str] = []
    for name, cmd, enabled in (
        ("run-mineru", local, True),
        ("mineru-cloud", cloud, bool(os.environ.get("MINERU_API_KEY"))),
        ("text-layer", text_layer, os.environ.get("COLLATE_ALLOW_TEXTLAYER", "1") != "0"),
    ):
        if not enabled:
            attempts.append(f"{name} skipped=not-enabled")
            continue
        completed = subprocess.run(cmd, cwd=ROOT, check=False, capture_output=True, text=True)
        rc = completed.returncode
        if rc == 0 and (workspace / "raw.md").exists() and _review_packets_ready(workspace):
            attempts.append(f"{name} rc=0")
            return name, attempts
        if rc == 0 and (workspace / "raw.md").exists():
            attempts.append(f"{name} rc=0 but page packets remain unavailable")
            continue
        tail = (completed.stderr or "").strip().splitlines()[-3:]
        tail_str = " | ".join(tail)[-200:]
        attempts.append(f"{name} rc={rc}: {tail_str}" if tail_str else f"{name} rc={rc}")
    raise RuntimeError("ocr-run failed: " + ", ".join(attempts))


def post_ocr_stage(workspace: Path) -> int:
    review = workspace / "review" / "raw.review.md"
    final = workspace / "final.md"
    packets = ensure_page_review_packets(workspace)
    if not review.exists():
        write_status(workspace, {"stage": "proofread", "status": "awaiting_agent_review", "ocr_engine": _engine_from_meta(workspace), "next_step": "Generate review/raw.review.md with historical-proofreader using review/page_review_packets.json and prep/pages/*.png, then rerun this command.", "files_preserved": [str(workspace / "raw.md"), str(workspace / "meta.json"), str(packets), str(workspace / "previews" / "visual-prep.html")]})
        print("[pipeline] OCR ready. Awaiting review/raw.review.md before auto-applying and exporting.")
        return 10
    verified, verify_reason = verify_page_grounded_review(workspace)
    if not verified:
        write_status(workspace, {
            "stage": "proofread_verification",
            "status": "error",
            "ocr_engine": _engine_from_meta(workspace),
            "error": verify_reason,
            "cause": "review/raw.review.md does not satisfy the deterministic "
                     "page-grounded recipe required by the canonical path.",
            "next_step": "Regenerate review/raw.review.md from review/page_review_packets.json; "
                         "frontmatter must include `proofread_method: page-grounded` "
                         "and `checked_pages: [...]` covering every packet page.",
            "files_preserved": [
                str(workspace / "raw.md"),
                str(review),
                str(packets),
                str(workspace / "prep" / "pages"),
            ],
        })
        print(f"[pipeline] proofread verification refused: {verify_reason}", file=sys.stderr)
        return 12
    status = read_status(workspace) or {}
    status["proofread_method"] = "page-grounded"
    write_status(workspace, status)
    if not final.exists():
        run([sys.executable, "scripts/apply_review.py", "--raw", str(workspace / "raw.md"), "--review", str(review), "--out", str(final)], "apply-review")

    # Fidelity gate: apply_review has now consumed the review, which is also
    # the point at which the _structure_approved marker (if the review
    # carries the frontmatter attestation) has been written. Run the gate
    # before any shareable artifact (docx, wechat, diff-review HTML) is
    # produced. See fidelity_gate() for what it enforces and why.
    gate_ok, gate_reason = fidelity_gate(workspace)
    if not gate_ok:
        write_status(workspace, {
            "stage": "fidelity_gate",
            "status": "error",
            "ocr_engine": _engine_from_meta(workspace),
            "error": gate_reason,
            "cause": "pre-export gate refused: export would ship a document "
                     "whose structural fidelity has not been attested by a "
                     "page-grounded proofread pass.",
            "next_step": "Re-run proofread against prep/pages/*.png, ensure "
                         "review/raw.review.md carries structure_approved: true "
                         "in its frontmatter (for text-layer fallbacks), and "
                         "confirm _pipeline_status.proofread_method == "
                         "'page-grounded'.",
            "files_preserved": [
                str(workspace / "raw.md"),
                str(workspace / "final.md"),
                str(workspace / "review" / "raw.review.md"),
                str(workspace / "meta.json"),
            ],
        })
        print(f"[pipeline] fidelity gate refused: {gate_reason}", file=sys.stderr)
        return 11

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
    ocr_engine: str | None = None
    ocr_attempts: list[str] = []
    try:
        if pdf is None and not (workspace / "raw.md").exists():
            raise RuntimeError("no input PDF found in workspace (expected prep/original.pdf or source.pdf)")
        if pdf is not None:
            ensure_workspace(pdf, workspace)
        if pdf is not None and not (workspace / "raw.md").exists():
            prep_stage(pdf, workspace)
            ocr_engine, ocr_attempts = try_ocr(workspace)
        else:
            ocr_engine = _engine_from_meta(workspace)
        result = post_ocr_stage(workspace)
        if result == 0:
            write_status(workspace, {"stage": "done", "status": "ok", "ocr_engine": ocr_engine, "ocr_attempts": ocr_attempts, "next_step": "Review output/ artifacts and README.md.", "files_preserved": [str(workspace / "output"), str(workspace / "previews")]})
        subprocess.run([sys.executable, "scripts/workspace_readme.py", "--workspace", str(workspace)], cwd=ROOT, check=False)
        return result
    except Exception as exc:
        write_status(workspace, {"stage": "failed", "status": "error", "error": str(exc), "cause": "See preserved workspace artifacts and preceding command output.", "ocr_engine": ocr_engine, "ocr_attempts": ocr_attempts, "next_step": "Inspect _pipeline_status.json and rerun the failed stage after fixing the blocker.", "files_preserved": [str(workspace), str(workspace / "previews"), str(workspace / "_internal")]})
        subprocess.run([sys.executable, "scripts/workspace_readme.py", "--workspace", str(workspace)], cwd=ROOT, check=False)
        print(f"stage: failed\nerror: {exc}\ncause: see command output above\nnext_step: inspect {workspace / '_internal' / '_pipeline_status.json'}\nfiles_preserved: [{workspace}]", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

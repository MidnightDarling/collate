#!/usr/bin/env python3
"""Run MinerU's local pipeline on a PDF and hand the output directory off
to `import_mineru_output.py`.

Background: MinerU ships as a Python package `mineru[pipeline]` that runs
the full layout detection + OCR stack locally via a short-lived FastAPI
service. No cloud API key, no browser hand-off. The `mineru` CLI writes
a per-job tree rooted at `<OUT>/<pdf-stem>/auto/`; this script:

    1. Runs `mineru -p <pdf> -o <tmp> -b pipeline -m auto -l <lang>`.
    2. Validates the output (content_list_v2.json must appear).
    3. Calls import_mineru_output.py --job-dir <tmp> --out <ocr-dir>
       --pdf <pdf>, which in turn triggers reflow + copies assets / meta.
    4. Leaves the tmp dir alone so JN can inspect `_layout.pdf` / `_span.pdf`
       for debugging if needed — we log the path.

First run on a fresh machine takes 5–10 minutes because MinerU has to
download ~2–3 GB of weights. Subsequent runs finish in ~90 s per 30 pages
on Apple Silicon.

Usage:
    python3 run_mineru.py --pdf 论文.pdf --out 论文.ocr
    python3 run_mineru.py --pdf 论文.pdf --out 论文.ocr --lang en
    python3 run_mineru.py --pdf 论文.pdf --out 论文.ocr --keep-mineru-out ./mineru-run
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def ensure_mineru() -> str:
    """Return the absolute path to the `mineru` CLI or fail loudly."""
    path = shutil.which("mineru")
    if path:
        return path
    print(
        "\n".join(
            [
                "`mineru` CLI not found on PATH.",
                "Install with: pip3 install -U 'mineru[pipeline]'",
                "(repo has `requirements.txt` you can pipe through pip too)",
            ]
        ),
        file=sys.stderr,
    )
    raise SystemExit(20)


def run_mineru(pdf: Path, tmp_out: Path, lang: str, method: str) -> None:
    cmd = [
        ensure_mineru(),
        "-p",
        str(pdf),
        "-o",
        str(tmp_out),
        "-b",
        "pipeline",
        "-m",
        method,
        "-l",
        lang,
    ]
    print(f"[run_mineru] $ {' '.join(cmd)}")
    # We stream stdout+stderr so JN sees progress bars — otherwise the
    # model-download + layout/OCR loop looks hung for minutes.
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        raise SystemExit(
            f"[run_mineru] mineru CLI exited with status {proc.returncode}; "
            "inspect the logs above to diagnose"
        )


def locate_job(tmp_out: Path, pdf_stem: str) -> Path:
    """Find MinerU's per-job output directory under tmp_out.

    Newer versions nest as `<stem>/auto/`; older as `<stem>/`. We accept
    either — import_mineru_output.py's `rglob` loaders handle both shapes.
    """
    cand = tmp_out / pdf_stem / "auto"
    if cand.is_dir() and any(cand.rglob("*content_list_v2.json")):
        return tmp_out / pdf_stem
    cand2 = tmp_out / pdf_stem
    if cand2.is_dir() and any(cand2.rglob("*content_list_v2.json")):
        return cand2
    # Last-resort: whatever sub-dir contains the JSON.
    for child in tmp_out.rglob("*content_list_v2.json"):
        return child.parent.parent if child.parent.name == "auto" else child.parent
    raise SystemExit(
        f"[run_mineru] MinerU finished but produced no content_list_v2.json under {tmp_out}"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, type=Path,
                    help="PDF to parse")
    ap.add_argument("--out", required=True, type=Path,
                    help="Target .ocr/ directory for the plugin pipeline")
    ap.add_argument("--lang", default="ch",
                    help="MinerU OCR language code (ch / en / korean / japan ...)")
    ap.add_argument("--method", default="auto",
                    choices=["auto", "txt", "ocr"],
                    help="MinerU parse method: auto (default), txt-only, or ocr-only")
    ap.add_argument("--keep-mineru-out", type=Path,
                    help="Use this directory for MinerU's raw output instead "
                         "of a throwaway tempdir — useful for debugging or "
                         "caching across re-runs")
    args = ap.parse_args()

    if not args.pdf.is_file():
        print(f"pdf not found: {args.pdf}", file=sys.stderr)
        return 2

    if args.keep_mineru_out:
        tmp_out = args.keep_mineru_out
        tmp_out.mkdir(parents=True, exist_ok=True)
        cleanup = False
    else:
        tmp_out = Path(tempfile.mkdtemp(prefix="mineru-"))
        cleanup = False  # keep for now so debugging stays easy

    run_mineru(args.pdf, tmp_out, args.lang, args.method)
    job = locate_job(tmp_out, args.pdf.stem)
    print(f"[run_mineru] job dir: {job}")

    # Chain into the existing importer so the rest of the plugin flow
    # (reflow / raw.md / meta.json / preview-ready assets) stays uniform
    # across "desktop already ran it" and "we just ran it".
    importer = Path(__file__).resolve().parent / "import_mineru_output.py"
    if not importer.is_file():
        raise SystemExit(f"[run_mineru] import_mineru_output.py not found at {importer}")
    rc = subprocess.run(
        [sys.executable, str(importer),
         "--pdf", str(args.pdf),
         "--out", str(args.out),
         "--job-dir", str(job)],
        check=False,
    ).returncode
    if rc != 0:
        return rc

    if cleanup:
        shutil.rmtree(tmp_out, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

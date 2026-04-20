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
    4. Leaves the tmp dir alone so the user can inspect `_layout.pdf` / `_span.pdf`
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
import os
import signal
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


# MinerU's first run downloads ~2–3 GB of weights from HuggingFace Hub.
# From mainland China the default huggingface.co endpoint routinely hangs or
# triggers ProxyError even on a working VPN, so we surface the two supported
# mirrors up-front. `HF_ENDPOINT` swaps in the hf-mirror.com proxy (fastest
# in China) and `MINERU_MODEL_SOURCE=modelscope` routes through ModelScope
# entirely. Setting one is enough; we prefer HF_ENDPOINT because it leaves
# the rest of the HuggingFace toolchain working for non-mineru tools too.
HF_MIRROR_HINT = [
    "",
    "[run_mineru] TIP: if model download fails with ProxyError / network timeout,",
    "  try one of these mirrors (prepend to your `/ocr-run` command):",
    "    export HF_ENDPOINT=https://hf-mirror.com",
    "  — or —",
    "    export MINERU_MODEL_SOURCE=modelscope",
    "  The first run downloads ~2–3 GB; subsequent runs are cached.",
    "",
]


# Substrings we recognise in MinerU's stderr that point to HuggingFace network
# failure specifically (vs. e.g. a genuine PDF parsing bug). Keep this list
# narrow — a false positive just appends a harmless tip, but a false negative
# leaves the user staring at an opaque traceback.
HF_FAILURE_MARKERS = (
    "ProxyError",
    "ConnectionError",
    "huggingface.co",
    "hf-mirror",
    "PDF-Extract-Kit",
    "opendatalab",
    "Failed to download",
    "Connection aborted",
    "Max retries exceeded",
)


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


def _mirror_preflight() -> None:
    """Warn the user about first-run model download before we start.

    If neither `HF_ENDPOINT` nor `MINERU_MODEL_SOURCE` is set, and the MinerU
    model cache does not yet exist locally, the first run will attempt a
    ~2–3 GB pull from huggingface.co — which fails by default from mainland
    China. We surface the mirror options proactively so the user doesn't have
    to watch it fail first. If a mirror IS already configured, we echo which
    one is active so surprises are rare.
    """
    hf_endpoint = os.environ.get("HF_ENDPOINT", "").strip()
    mineru_source = os.environ.get("MINERU_MODEL_SOURCE", "").strip()
    if hf_endpoint:
        print(f"[run_mineru] HF_ENDPOINT={hf_endpoint} (model downloads via mirror)")
        return
    if mineru_source:
        print(f"[run_mineru] MINERU_MODEL_SOURCE={mineru_source}")
        return

    # Best-effort: detect whether the model cache likely exists. We do NOT
    # hard-fail on this — some users are on uncensored networks and the
    # default endpoint works fine. We just hint.
    hf_cache = Path(os.environ.get("HF_HOME") or (Path.home() / ".cache/huggingface"))
    models_root = hf_cache / "hub"
    already_cached = any(
        p.name.startswith("models--opendatalab--PDF-Extract-Kit")
        for p in models_root.iterdir()
    ) if models_root.is_dir() else False
    if already_cached:
        return

    print("\n".join(HF_MIRROR_HINT), file=sys.stderr)


def _captures_hf_failure(stderr_tail: str) -> bool:
    """True when the captured stderr tail looks like a HuggingFace pull failure."""
    return any(marker in stderr_tail for marker in HF_FAILURE_MARKERS)


def _terminate_process_group(proc: subprocess.Popen[str]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        proc.wait(timeout=5)


def run_mineru(pdf: Path, tmp_out: Path, lang: str, method: str) -> None:
    _mirror_preflight()

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
    print(
        "[run_mineru] local MinerU may stay quiet for 30-90 seconds during "
        "layout/model work; silence here is not necessarily a hang"
    )
    quiet_timeout = int(os.environ.get("COLLATE_MINERU_QUIET_TIMEOUT", "120"))
    total_timeout = int(os.environ.get("COLLATE_MINERU_TOTAL_TIMEOUT", "900"))
    # We tee the child process output so the user still sees progress bars
    # in real time AND we retain the stderr tail to pattern-match for
    # HuggingFace-specific failure modes after exit. subprocess.run with
    # capture_output would hide the streaming UI, so we use Popen + manual
    # relay. The tail is a small ring buffer — we only need the last 4 KB
    # to spot ProxyError markers.
    tail: list[str] = []
    tail_cap = 80  # keep the last ~80 stderr lines
    last_output = [time.monotonic()]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        text=True,
        start_new_session=True,
    )
    # Read both streams concurrently via select so neither buffer blocks the
    # other. Using threads here is simpler than asyncio for a one-shot call.
    import threading

    def _relay(stream, dest, keep_tail: bool) -> None:
        for line in stream:
            dest.write(line)
            dest.flush()
            last_output[0] = time.monotonic()
            if keep_tail:
                tail.append(line)
                if len(tail) > tail_cap:
                    tail.pop(0)

    t_out = threading.Thread(target=_relay, args=(proc.stdout, sys.stdout, False))
    t_err = threading.Thread(target=_relay, args=(proc.stderr, sys.stderr, True))
    t_out.start()
    t_err.start()
    start = time.monotonic()
    timeout_reason = ""
    while proc.poll() is None:
        elapsed = time.monotonic() - start
        quiet_for = time.monotonic() - last_output[0]
        no_artifacts_yet = not any(tmp_out.iterdir())
        if total_timeout > 0 and elapsed > total_timeout:
            timeout_reason = (
                f"[run_mineru] local MinerU exceeded {total_timeout}s total runtime; "
                "falling back to the next OCR path"
            )
            _terminate_process_group(proc)
            break
        if quiet_timeout > 0 and elapsed > quiet_timeout and no_artifacts_yet:
            timeout_reason = (
                f"[run_mineru] local MinerU produced no job files within "
                f"{quiet_timeout}s; falling back to the next OCR path"
            )
            _terminate_process_group(proc)
            break
        if quiet_timeout > 0 and quiet_for > quiet_timeout and not no_artifacts_yet:
            timeout_reason = (
                f"[run_mineru] local MinerU stopped emitting progress for "
                f"{quiet_timeout}s after startup; falling back to the next OCR path"
            )
            _terminate_process_group(proc)
            break
        time.sleep(1)
    rc = proc.wait()
    t_out.join()
    t_err.join()

    if timeout_reason:
        print(timeout_reason, file=sys.stderr)
        raise SystemExit(124)
    if rc != 0:
        stderr_tail = "".join(tail)
        if _captures_hf_failure(stderr_tail):
            print(
                "\n".join(
                    [
                        "",
                        "[run_mineru] This looks like a HuggingFace model-download failure.",
                        "  Retry with a mirror:",
                        "    HF_ENDPOINT=https://hf-mirror.com python3 run_mineru.py --pdf ... --out ...",
                        "  — or —",
                        "    MINERU_MODEL_SOURCE=modelscope python3 run_mineru.py --pdf ... --out ...",
                        "",
                    ]
                ),
                file=sys.stderr,
            )
        raise SystemExit(
            f"[run_mineru] mineru CLI exited with status {rc}; "
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

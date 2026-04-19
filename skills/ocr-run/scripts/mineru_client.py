#!/usr/bin/env python3
"""MinerU API client for historical-ocr-review plugin.

MinerU v4 API is URL-based: the `/extract/task` endpoint accepts a PDF URL,
not a multipart upload. For local files, we first upload to catbox.moe
(24-hour anonymous hosting) to obtain a public URL, then submit that URL.

Response envelope: {"code": 0, "data": {...}, "msg": "..."}
Result field: `full_zip_url` pointing to a zip with markdown + assets.

Environment:
    MINERU_API_KEY in ~/.env

Usage:
    python3 mineru_client.py --pdf cleaned.pdf --out out_dir \
        --layout horizontal --lang zh-hans \
        --poll-interval 10 --timeout 900

    # auth check only (no submission)
    python3 mineru_client.py --check-auth
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import statistics
import sys
import time
import zipfile
from pathlib import Path

try:
    import requests
    from dotenv import load_dotenv
except ImportError:
    print("missing dependency: pip3 install requests python-dotenv", file=sys.stderr)
    sys.exit(1)

API_BASE = "https://mineru.net/api/v4"
CATBOX_URL = "https://catbox.moe/user/api.php"
ENV_KEY = "MINERU_API_KEY"


def _read_mineru_cli_token() -> str:
    """Fallback: reuse the token saved by the official `mineru` CLI.

    `mineru auth` writes `~/.mineru/config.yaml` with an `api_key:` (or
    `token:`) field. If the user ran that at some point we should pick it up
    automatically rather than asking them to duplicate it in `~/.env`.
    """
    cfg = Path.home() / ".mineru" / "config.yaml"
    if not cfg.is_file():
        return ""
    try:
        # PyYAML is optional at import-time — only parse if it's available.
        import yaml  # type: ignore
        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    except Exception:
        return ""
    for key in ("api_key", "MINERU_API_KEY", "token", "MINERU_API_TOKEN"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def load_key() -> str:
    """Resolve the MinerU API key across the common storage locations.

    Priority:
      1. `MINERU_API_KEY` in the process environment (highest — explicit)
      2. `~/.env`                                  (plugin convention)
      3. `MINERU_API_TOKEN` / `MINERU_TOKEN` env vars (shared w/ CLI)
      4. `~/.mineru/config.yaml`                   (official CLI's cache)
    """
    # Pull in `~/.env` so we pick up plugin-local config on top of whatever
    # the caller already exported in the shell.
    load_dotenv(Path.home() / ".env")

    key = (os.environ.get(ENV_KEY, "") or "").strip()
    if key:
        return key

    # Some tooling writes under different var names; accept the common ones.
    for alt in ("MINERU_API_TOKEN", "MINERU_TOKEN"):
        val = (os.environ.get(alt, "") or "").strip()
        if val:
            return val

    key = _read_mineru_cli_token()
    if key:
        return key

    print(
        f"{ENV_KEY} not set — run the setup skill, add it to ~/.env, "
        "or log in via `mineru auth` so we can reuse the official CLI token",
        file=sys.stderr,
    )
    sys.exit(10)


def headers(key: str) -> dict:
    return {"Authorization": f"Bearer {key}"}


def check_auth(key: str) -> int:
    """Lightweight GET that verifies the key without submitting work."""
    r = requests.get(f"{API_BASE}/extract/task", headers=headers(key), timeout=30)
    if r.status_code in (200, 400, 405, 422):
        print("AUTH_OK")
        return 0
    if r.status_code == 401:
        print("AUTH_FAIL")
        return 11
    print(f"AUTH_UNKNOWN http={r.status_code}")
    return 12


def upload_to_catbox(pdf: Path, retries: int = 3) -> str:
    """Upload a local PDF to catbox.moe, return public URL. 24h retention.

    catbox occasionally returns 200 with an empty body (appears to be a
    transient nginx/cache issue on their side — the same request succeeds
    on retry). We retry a small number of times before giving up so the
    caller isn't blocked by a flaky upload.
    """
    last_status: int | None = None
    last_body: str = ""
    for attempt in range(1, retries + 1):
        print(f"[mineru] uploading {pdf.name} to catbox.moe (attempt {attempt}/{retries}) …")
        with pdf.open("rb") as f:
            r = requests.post(
                CATBOX_URL,
                data={"reqtype": "fileupload"},
                files={"fileToUpload": (pdf.name, f, "application/pdf")},
                timeout=180,
            )
        body = (r.text or "").strip()
        last_status, last_body = r.status_code, body
        if r.status_code == 200 and body.startswith("https://"):
            print(f"[mineru] uploaded -> {body}")
            return body
        print(
            f"[mineru] catbox returned http={r.status_code} body={body[:120]!r}; "
            "retrying" if attempt < retries else "giving up",
            file=sys.stderr,
        )
        time.sleep(2 * attempt)
    raise RuntimeError(
        f"catbox upload failed after {retries} attempts: "
        f"last http={last_status} body={last_body[:200]!r}"
    )


def _unwrap(body: dict) -> dict:
    """MinerU wraps responses as {code, data, msg}. Check code, return data."""
    if body.get("code") != 0:
        raise RuntimeError(f"MinerU error code={body.get('code')} msg={body.get('msg')}")
    return body.get("data", {})


def submit_url(key: str, url: str) -> str:
    """Submit a public URL for parsing, return task_id.

    MinerU v4 currently only accepts a small set of fields; we keep the payload
    minimal to stay forward-compatible. The caller's layout/lang hints are
    recorded in our own meta.json for the proofreader agent but not forwarded
    to MinerU — that's why this function deliberately has a narrow signature.
    """
    payload = {
        "url": url,
        "is_ocr": True,
        "enable_formula": True,
        "enable_table": True,
    }
    r = requests.post(
        f"{API_BASE}/extract/task",
        headers=headers(key),
        json=payload,
        timeout=60,
    )
    if r.status_code != 200:
        raise RuntimeError(f"submit http={r.status_code} body={r.text[:400]}")
    data = _unwrap(r.json())
    task_id = data.get("task_id")
    if not task_id:
        raise RuntimeError(f"no task_id in response: {data}")
    return task_id


def poll(key: str, task_id: str, interval: int, timeout: int) -> dict:
    """Poll until state=done, return the result data dict.

    The returned dict carries `full_zip_url`; we also keep the last known
    `extract_progress` so callers can read `total_pages` for meta.json.
    """
    start = time.time()
    last_state = ""
    last_progress: dict = {}
    while time.time() - start < timeout:
        r = requests.get(
            f"{API_BASE}/extract/task/{task_id}",
            headers=headers(key),
            timeout=30,
        )
        if r.status_code != 200:
            raise RuntimeError(f"poll http={r.status_code} body={r.text[:300]}")
        data = _unwrap(r.json())
        state = data.get("state", "")
        progress = data.get("extract_progress", {}) or {}
        if progress:
            last_progress = progress
        extracted = progress.get("extracted_pages", "?")
        total = progress.get("total_pages", "?")
        if state != last_state or (extracted != "?" and int(time.time() - start) % 30 == 0):
            elapsed = int(time.time() - start)
            print(f"[mineru] {elapsed}s state={state} progress={extracted}/{total}")
            last_state = state
        if state == "done":
            # make sure progress persists into the caller's snapshot
            if last_progress and not data.get("extract_progress"):
                data["extract_progress"] = last_progress
            return data
        if state == "failed":
            raise RuntimeError(f"task failed: {data.get('err_msg', data)}")
        time.sleep(interval)
    raise TimeoutError(f"task {task_id} did not complete in {timeout}s")


PAGE_MARKER_RE = re.compile(r"<!--\s*page\s+(\d+)\s*-->", re.IGNORECASE)


def compute_page_stats(raw_md: Path, total_pages_hint: int | None) -> tuple[int, list[int]]:
    """Return (pages, low_confidence_pages) from a raw.md file.

    MinerU doesn't emit per-page confidence, so we use a layout heuristic:
    pages whose OCR text is dramatically shorter than the median are flagged
    as low-confidence candidates for the proofread step.

    - If raw.md contains explicit `<!-- page N -->` markers, we split on them
      and score each block by character count.
    - Otherwise `pages` falls back to the hint (typically
      `extract_progress.total_pages` from the MinerU API) and low_confidence
      is left empty (we have no way to score individual pages without markers).
    """
    try:
        text = raw_md.read_text(encoding="utf-8")
    except Exception:
        return (total_pages_hint or 0, [])

    matches = list(PAGE_MARKER_RE.finditer(text))
    if not matches:
        return (total_pages_hint or 0, [])

    blocks: list[tuple[int, str]] = []
    for i, m in enumerate(matches):
        page = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append((page, text[start:end].strip()))

    pages = len(blocks)
    lengths = [len(body) for _, body in blocks]
    if not lengths:
        return (pages, [])

    median = statistics.median(lengths)
    # Flag a page as low-confidence when it is conspicuously short AND
    # absolutely small — avoids false positives on short documents where
    # every page is short.
    threshold = max(200, int(median * 0.5))
    low = sorted(
        page for page, body in blocks if len(body) < threshold
    )
    return (pages, low)


def download_and_extract(result: dict, out_dir: Path) -> None:
    zip_url = result.get("full_zip_url") or result.get("zip_url")
    if not zip_url:
        raise RuntimeError(f"no full_zip_url in result: {result}")
    print(f"[mineru] downloading zip …")
    r = requests.get(zip_url, timeout=300)
    r.raise_for_status()
    out_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = out_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        # Prefer a "full" markdown if present, else the first .md
        md_candidates = [n for n in zf.namelist() if n.lower().endswith(".md")]
        md_candidates.sort(key=lambda n: (0 if "full" in n.lower() else 1, len(n)))
        if not md_candidates:
            raise RuntimeError("no markdown in MinerU zip")
        with zf.open(md_candidates[0]) as mf:
            content = mf.read().decode("utf-8", errors="replace")
        (out_dir / "raw.md").write_text(content, encoding="utf-8")
        print(f"[mineru] saved raw.md ({len(content)} chars)")

        for name in zf.namelist():
            lower = name.lower()
            if any(lower.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp")):
                target = assets_dir / Path(name).name
                with zf.open(name) as src, target.open("wb") as dst:
                    dst.write(src.read())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--url", help="use an existing public URL instead of uploading")
    ap.add_argument("--layout", choices=["horizontal", "vertical"], default="horizontal")
    ap.add_argument("--lang", default="zh-hans")
    ap.add_argument("--poll-interval", type=int, default=10)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--check-auth", action="store_true")
    args = ap.parse_args()

    key = load_key()

    if args.check_auth:
        return check_auth(key)

    if not args.out:
        print("--out is required", file=sys.stderr)
        return 2

    if not args.url:
        if not args.pdf or not args.pdf.is_file():
            print(f"pdf not found: {args.pdf}", file=sys.stderr)
            return 2

    start = time.time()
    total_pages_hint: int | None = None
    try:
        url = args.url or upload_to_catbox(args.pdf)
        task_id = submit_url(key, url)
        print(f"[mineru] submitted task_id={task_id}")
        result = poll(key, task_id, args.poll_interval, args.timeout)
        progress = result.get("extract_progress") or {}
        total = progress.get("total_pages")
        if isinstance(total, int) and total > 0:
            total_pages_hint = total
        download_and_extract(result, args.out)
    except Exception as e:
        print(f"[mineru] error: {e}", file=sys.stderr)
        return 5

    pages, low_conf = compute_page_stats(args.out / "raw.md", total_pages_hint)
    meta = {
        "engine": "mineru",
        "layout": args.layout,
        "lang": args.lang,
        "pages": pages,
        # MinerU's API does not expose per-page confidence scores, so we keep
        # this field explicitly null rather than fabricating a number. The
        # proofread skill treats null as "no signal" and does not gate on it.
        "avg_confidence": None,
        "low_confidence_pages": low_conf,
        "duration_seconds": round(time.time() - start, 1),
    }
    (args.out / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"[mineru] done in {meta['duration_seconds']}s; "
        f"pages={pages} low_confidence={low_conf or '[]'}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

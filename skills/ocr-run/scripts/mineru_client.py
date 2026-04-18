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


def load_key() -> str:
    load_dotenv(Path.home() / ".env")
    key = os.environ.get(ENV_KEY, "").strip()
    if not key:
        print(f"{ENV_KEY} not set — run setup skill first", file=sys.stderr)
        sys.exit(10)
    return key


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


def upload_to_catbox(pdf: Path) -> str:
    """Upload a local PDF to catbox.moe, return public URL. 24h retention."""
    print(f"[mineru] uploading {pdf.name} to catbox.moe …")
    with pdf.open("rb") as f:
        r = requests.post(
            CATBOX_URL,
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (pdf.name, f, "application/pdf")},
            timeout=180,
        )
    if r.status_code != 200 or not r.text.startswith("https://"):
        raise RuntimeError(f"catbox upload failed: http={r.status_code} body={r.text[:200]}")
    url = r.text.strip()
    print(f"[mineru] uploaded -> {url}")
    return url


def _unwrap(body: dict) -> dict:
    """MinerU wraps responses as {code, data, msg}. Check code, return data."""
    if body.get("code") != 0:
        raise RuntimeError(f"MinerU error code={body.get('code')} msg={body.get('msg')}")
    return body.get("data", {})


def submit_url(key: str, url: str, layout: str, lang: str) -> str:
    """Submit a public URL for parsing, return task_id.

    MinerU v4 currently only accepts a small set of fields; we keep the payload
    minimal to stay forward-compatible. layout/lang are retained in our meta
    for the proofreader agent but not sent to MinerU directly.
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
    """Poll until state=done, return the result data dict (has full_zip_url)."""
    start = time.time()
    last_state = ""
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
        progress = data.get("extract_progress", {})
        extracted = progress.get("extracted_pages", "?")
        total = progress.get("total_pages", "?")
        if state != last_state or (extracted != "?" and int(time.time() - start) % 30 == 0):
            elapsed = int(time.time() - start)
            print(f"[mineru] {elapsed}s state={state} progress={extracted}/{total}")
            last_state = state
        if state == "done":
            return data
        if state == "failed":
            raise RuntimeError(f"task failed: {data.get('err_msg', data)}")
        time.sleep(interval)
    raise TimeoutError(f"task {task_id} did not complete in {timeout}s")


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
    try:
        url = args.url or upload_to_catbox(args.pdf)
        task_id = submit_url(key, url, args.layout, args.lang)
        print(f"[mineru] submitted task_id={task_id}")
        result = poll(key, task_id, args.poll_interval, args.timeout)
        download_and_extract(result, args.out)
    except Exception as e:
        print(f"[mineru] error: {e}", file=sys.stderr)
        return 5

    meta = {
        "engine": "mineru",
        "layout": args.layout,
        "lang": args.lang,
        "duration_seconds": round(time.time() - start, 1),
    }
    (args.out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"[mineru] done in {meta['duration_seconds']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())

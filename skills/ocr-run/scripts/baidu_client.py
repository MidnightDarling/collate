#!/usr/bin/env python3
"""Baidu OCR client (per-page) for historical-ocr-review plugin.

Baidu's General OCR (High Accuracy) handles modern simplified Chinese well.
This module is a fallback for users who already have a Baidu key; MinerU is
preferred for traditional / vertical / classical text.

Rendering is done page-by-page: we rely on prep-scan's pages directory rather
than asking Baidu to parse the PDF directly (their batch PDF endpoint has
stricter limits).

Environment:
    BAIDU_OCR_API_KEY
    BAIDU_OCR_SECRET_KEY

Usage:
    python3 baidu_client.py --pdf cleaned.pdf --out out_dir \
        --layout horizontal --lang zh-hans

    # auth check only (fetches access_token)
    python3 baidu_client.py --check-auth
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
    from dotenv import load_dotenv
except ImportError:
    print("missing dependency: pip3 install requests python-dotenv", file=sys.stderr)
    sys.exit(1)

TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
OCR_ACCURATE = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"
OCR_HANDWRITING = "https://aip.baidubce.com/rest/2.0/ocr/v1/handwriting"
TOKEN_CACHE = Path.home() / ".cache" / "baidu_ocr_token.json"


def load_keys() -> tuple[str, str]:
    load_dotenv(Path.home() / ".env")
    api = os.environ.get("BAIDU_OCR_API_KEY", "").strip()
    secret = os.environ.get("BAIDU_OCR_SECRET_KEY", "").strip()
    if not api or not secret:
        print("BAIDU_OCR_API_KEY / BAIDU_OCR_SECRET_KEY missing — run setup", file=sys.stderr)
        sys.exit(10)
    return api, secret


def fetch_token(api: str, secret: str) -> str:
    """Get a fresh access_token from Baidu OAuth."""
    r = requests.post(
        TOKEN_URL,
        params={"grant_type": "client_credentials", "client_id": api, "client_secret": secret},
        timeout=30,
    )
    if r.status_code != 200:
        raise RuntimeError(f"token http={r.status_code} body={r.text[:300]}")
    body = r.json()
    token = body.get("access_token")
    if not token:
        raise RuntimeError(f"no access_token in response: {body}")
    TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_CACHE.write_text(json.dumps({"token": token, "ts": time.time()}))
    return token


def load_token(api: str, secret: str) -> str:
    if TOKEN_CACHE.is_file():
        try:
            data = json.loads(TOKEN_CACHE.read_text())
            # cached for 24h (Baidu tokens live 30 days, but refresh is cheap)
            if time.time() - data.get("ts", 0) < 24 * 3600:
                return data["token"]
        except Exception:
            pass
    return fetch_token(api, secret)


def ocr_one_page(token: str, image_path: Path, lang: str) -> dict:
    """Call Baidu OCR on a single PNG, return {'lines': [...], 'text': '...'}."""
    img_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
    params = {
        "access_token": token,
        "language_type": "CHN_ENG" if lang != "zh-hant" else "TRAD_CHN_ENG",
        "detect_direction": "true",
        "paragraph": "true",
    }
    r = requests.post(
        OCR_ACCURATE,
        params=params,
        data={"image": img_b64},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=60,
    )
    body = r.json()
    if "error_code" in body:
        raise RuntimeError(f"baidu error {body.get('error_code')}: {body.get('error_msg')}")
    lines = [w.get("words", "") for w in body.get("words_result", [])]
    return {"lines": lines, "text": "\n".join(lines)}


def merge_lines(lines: list[str]) -> str:
    """Heuristic merge: join short-wrapped lines into paragraphs.

    Baidu returns one item per visual line. Historical papers often wrap
    mid-sentence. We join two consecutive lines unless the first ends with
    Chinese terminal punctuation (。？！) or is clearly a heading.
    """
    terminators = set("。？！；：")
    paragraphs: list[str] = []
    buf = ""
    for ln in lines:
        ln = ln.rstrip()
        if not ln:
            if buf:
                paragraphs.append(buf)
                buf = ""
            continue
        if not buf:
            buf = ln
        elif buf[-1] in terminators:
            paragraphs.append(buf)
            buf = ln
        else:
            buf += ln
    if buf:
        paragraphs.append(buf)
    return "\n\n".join(paragraphs)


def collect_pages(pdf_path: Path) -> list[Path]:
    """Find the per-page PNGs produced by prep-scan."""
    prep = pdf_path.parent.parent / (pdf_path.parent.name.replace(".prep", "") + ".prep") / "pages"
    if not prep.is_dir():
        # fallback: peer .prep/pages next to the PDF
        prep = pdf_path.parent / "pages"
    if not prep.is_dir():
        prep = pdf_path.parent / (pdf_path.stem + ".prep") / "pages"
    return sorted(prep.glob("page_*.png"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--layout", choices=["horizontal", "vertical"], default="horizontal")
    ap.add_argument("--lang", default="zh-hans")
    ap.add_argument("--check-auth", action="store_true")
    args = ap.parse_args()

    api, secret = load_keys()

    if args.check_auth:
        try:
            fetch_token(api, secret)
            print("AUTH_OK")
            return 0
        except Exception as e:
            print(f"AUTH_FAIL {e}", file=sys.stderr)
            return 11

    if not args.pdf or not args.out:
        print("--pdf and --out required", file=sys.stderr)
        return 2

    pages = collect_pages(args.pdf)
    if not pages:
        print("no per-page PNGs found; run prep-scan first", file=sys.stderr)
        return 3

    args.out.mkdir(parents=True, exist_ok=True)
    token = load_token(api, secret)

    start = time.time()
    all_text: list[str] = []
    for i, page in enumerate(pages, 1):
        try:
            result = ocr_one_page(token, page, args.lang)
        except Exception as e:
            print(f"[baidu] page {i} failed: {e}", file=sys.stderr)
            all_text.append(f"<!-- page {i} OCR failed: {e} -->")
            continue
        merged = merge_lines(result["lines"])
        all_text.append(f"\n\n<!-- page {i} -->\n\n{merged}")
        if i % 5 == 0 or i == len(pages):
            print(f"[baidu] {i}/{len(pages)} pages OCR'd")

    raw = "\n".join(all_text).strip() + "\n"
    (args.out / "raw.md").write_text(raw, encoding="utf-8")

    meta = {
        "engine": "baidu",
        "layout": args.layout,
        "lang": args.lang,
        "pages": len(pages),
        "duration_seconds": round(time.time() - start, 1),
    }
    (args.out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"[baidu] done: {len(pages)} pages in {meta['duration_seconds']}s -> {args.out}/raw.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

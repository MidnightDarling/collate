#!/usr/bin/env python3
"""Crop top and bottom margins (headers, footers, folio numbers) from pages.

Historical journals often carry a header line ("某某史研究 2023年第3期") and a
footer ("第 N 期") that OCR happily reads into the body. For modern scans we
can safely trim; for classical woodblock prints and archives the header/footer
region is part of the research object and should be preserved — use
--header-ratio 0 --footer-ratio 0 (or the wrapper --no-margin-trim) to skip.

Usage:
    python3 remove_margins.py --in dir --out dir \
        --header-ratio 0.08 --footer-ratio 0.08
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("missing dependency: pip3 install pillow", file=sys.stderr)
    sys.exit(1)


def crop(img_path: Path, out_path: Path, header: float, footer: float) -> None:
    if header <= 0 and footer <= 0:
        if img_path != out_path:
            out_path.write_bytes(img_path.read_bytes())
        return
    img = Image.open(img_path)
    w, h = img.size
    top = int(h * header)
    bottom = int(h * (1 - footer))
    if bottom <= top:
        # Degenerate case, skip
        if img_path != out_path:
            out_path.write_bytes(img_path.read_bytes())
        return
    cropped = img.crop((0, top, w, bottom))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(out_path, "PNG")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--header-ratio", type=float, default=0.08)
    ap.add_argument("--footer-ratio", type=float, default=0.08)
    args = ap.parse_args()

    pages = sorted(args.in_dir.glob("page_*.png"))
    if not pages:
        pages = sorted(args.in_dir.glob("*.png"))
    if not pages:
        print(f"no PNGs in {args.in_dir}", file=sys.stderr)
        return 2

    args.out.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(pages, 1):
        crop(p, args.out / p.name, args.header_ratio, args.footer_ratio)
        if i % 20 == 0 or i == len(pages):
            print(f"[remove_margins] {i}/{len(pages)}")
    print(f"[remove_margins] done -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

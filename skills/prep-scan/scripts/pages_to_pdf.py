#!/usr/bin/env python3
"""Assemble per-page PNG files back into a single PDF.

Used after de-watermarking to produce cleaned.pdf. Uses PIL for JPEG-quality
compression to keep the output reasonable in size without sacrificing OCR
legibility.

Usage:
    python3 pages_to_pdf.py --in pages_dir --out cleaned.pdf
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


def collect_pages(in_dir: Path) -> list[Path]:
    pngs = sorted(in_dir.glob("page_*.png"))
    if not pngs:
        pngs = sorted(in_dir.glob("*.png"))
    return pngs


def assemble(pages: list[Path], out_pdf: Path) -> int:
    if not pages:
        return 0
    first = Image.open(pages[0]).convert("RGB")
    rest = [Image.open(p).convert("RGB") for p in pages[1:]]
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    first.save(
        out_pdf,
        "PDF",
        resolution=300.0,
        save_all=True,
        append_images=rest,
    )
    return len(pages)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    pages = collect_pages(args.in_dir)
    if not pages:
        print(f"no PNGs found in {args.in_dir}", file=sys.stderr)
        return 2

    n = assemble(pages, args.out)
    print(f"[pages_to_pdf] {n} pages -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

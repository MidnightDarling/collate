#!/usr/bin/env python3
"""Split PDF into per-page PNG images.

Used by historical-ocr-review's prep-scan skill as the first step before
de-watermarking. High DPI is critical for OCR of small historical fonts
(e.g. Republican-era 5-point type, classical double-column commentary).

Usage:
    python3 split_pages.py --pdf path/to.pdf --out outdir --dpi 300
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from pdf2image import convert_from_path
    from pdf2image.exceptions import PDFInfoNotInstalledError
except ImportError:
    print("missing dependency: pip3 install pdf2image", file=sys.stderr)
    sys.exit(1)


def detect_pdf_dpi(pdf_path: Path) -> int:
    """Probe the first page's native DPI by rendering at 72 and measuring size.

    Returns the rough native DPI (usually 150-600 for scans). Cap to avoid
    forcing 300 DPI on a file that's intrinsically 150 — upsampling just
    amplifies noise.
    """
    try:
        sample = convert_from_path(str(pdf_path), dpi=72, first_page=1, last_page=1)
        if not sample:
            return 300
        w = sample[0].width
        if w > 1800:
            return 450
        if w > 1200:
            return 300
        if w > 700:
            return 200
        return 150
    except Exception:
        return 300


def split(pdf_path: Path, out_dir: Path, target_dpi: int) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    native = detect_pdf_dpi(pdf_path)
    dpi = min(target_dpi, max(native, 150))
    if dpi < target_dpi:
        print(f"[split_pages] native DPI ~{native}, capping render at {dpi}")
    else:
        print(f"[split_pages] rendering at {dpi} DPI")

    images = convert_from_path(str(pdf_path), dpi=dpi)
    for i, img in enumerate(images, 1):
        out = out_dir / f"page_{i:03d}.png"
        img.save(out, "PNG")
        if i % 10 == 0 or i == len(images):
            print(f"[split_pages] {i}/{len(images)} pages saved")
    return len(images)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args()

    if not args.pdf.is_file():
        print(f"input not found: {args.pdf}", file=sys.stderr)
        return 2

    try:
        n = split(args.pdf, args.out, args.dpi)
    except PDFInfoNotInstalledError:
        print("poppler missing — run: brew install poppler", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"split failed: {e}", file=sys.stderr)
        return 4

    print(f"[split_pages] done: {n} pages -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

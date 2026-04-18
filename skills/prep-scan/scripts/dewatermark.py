#!/usr/bin/env python3
"""De-watermark per-page PNG images for historical documents.

Handles three pollutant categories common in JN's workflow:
  1. Colored stamps (library seals, archive chop marks) — red / blue saturation
  2. Diagonal wordmarks (CNKI, Wanfang, Duxiu database overlays) — Hough lines
  3. Faint grey repeated watermarks ("读秀学术搜索") — top-hat morphology

The conservative goal: remove pollution without eating legible text. Classical
texts with faint ink are particularly vulnerable — we keep a low threshold by
default. Use --aggressive only when watermarks resist the default pass.

Usage:
    python3 dewatermark.py --in pages_dir --out cleaned_dir [--aggressive] [--keep-color]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError:
    print("missing dependency: pip3 install opencv-python numpy", file=sys.stderr)
    sys.exit(1)


def remove_color_stamps(bgr: np.ndarray, aggressive: bool) -> np.ndarray:
    """Mask high-saturation red / blue pixels (stamps) and inpaint."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    sat_threshold = 60 if aggressive else 90
    # red wraps around 0° and 180° in OpenCV HSV
    red_mask = ((h < 12) | (h > 168)) & (s > sat_threshold) & (v > 60)
    blue_mask = ((h > 95) & (h < 130)) & (s > sat_threshold) & (v > 60)

    mask = (red_mask | blue_mask).astype(np.uint8) * 255
    # dilate so inpainting covers the stamp edges
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=1)

    # area filter: only treat large connected components as stamps, not ink
    num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    clean_mask = np.zeros_like(mask)
    min_area = 400 if aggressive else 1200
    for i in range(1, num):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_area:
            clean_mask[labels == i] = 255

    if cv2.countNonZero(clean_mask) == 0:
        return bgr

    return cv2.inpaint(bgr, clean_mask, 3, cv2.INPAINT_TELEA)


def remove_diagonal_wordmarks(bgr: np.ndarray, aggressive: bool) -> np.ndarray:
    """Detect diagonal text overlays (CNKI-style) and fade them.

    Strategy: find pixels that are light-grey (typical wordmark lightness) and
    form a coherent diagonal band, then push them toward the page background.
    """
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    # wordmarks are typically in the grey range 120-200
    lo = 110 if aggressive else 130
    hi = 210 if aggressive else 200
    band = (((gray >= lo) & (gray <= hi)).astype(np.uint8)) * 255

    # emphasise diagonal structure
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    rot = cv2.warpAffine(band, cv2.getRotationMatrix2D((band.shape[1] / 2, band.shape[0] / 2), 45, 1), (band.shape[1], band.shape[0]))
    opened = cv2.morphologyEx(rot, cv2.MORPH_OPEN, kernel)
    diag_mask = cv2.warpAffine(opened, cv2.getRotationMatrix2D((band.shape[1] / 2, band.shape[0] / 2), -45, 1), (band.shape[1], band.shape[0]))

    if cv2.countNonZero(diag_mask) < 500:
        return bgr

    # lighten matched pixels toward white
    result = bgr.copy()
    result[diag_mask > 0] = np.clip(result[diag_mask > 0].astype(np.int16) + 60, 0, 255).astype(np.uint8)
    return result


def remove_faint_repeat(bgr: np.ndarray, aggressive: bool) -> np.ndarray:
    """Remove faint repeated greyscale patterns (Duxiu-style)."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=3)

    # top-hat extracts bright features smaller than the kernel
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    tophat = cv2.morphologyEx(blurred, cv2.MORPH_TOPHAT, kernel)
    threshold = 30 if aggressive else 45

    mask = (tophat > threshold).astype(np.uint8) * 255
    # don't touch dense dark regions (body text)
    _, body = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY_INV)
    body_dilated = cv2.dilate(body, np.ones((5, 5), np.uint8), iterations=2)
    mask[body_dilated > 0] = 0

    if cv2.countNonZero(mask) < 200:
        return bgr
    return cv2.inpaint(bgr, mask, 3, cv2.INPAINT_TELEA)


def process(img_path: Path, out_path: Path, aggressive: bool, keep_color: bool) -> None:
    bgr = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
    if bgr is None:
        print(f"[dewatermark] cannot read {img_path}", file=sys.stderr)
        return

    if not keep_color:
        bgr = remove_color_stamps(bgr, aggressive)
    bgr = remove_diagonal_wordmarks(bgr, aggressive)
    bgr = remove_faint_repeat(bgr, aggressive)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), bgr, [cv2.IMWRITE_PNG_COMPRESSION, 3])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--aggressive", action="store_true")
    ap.add_argument("--keep-color", action="store_true")
    args = ap.parse_args()

    pages = sorted(args.in_dir.glob("page_*.png"))
    if not pages:
        pages = sorted(args.in_dir.glob("*.png"))
    if not pages:
        print(f"no PNGs in {args.in_dir}", file=sys.stderr)
        return 2

    args.out.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(pages, 1):
        process(p, args.out / p.name, args.aggressive, args.keep_color)
        if i % 10 == 0 or i == len(pages):
            print(f"[dewatermark] {i}/{len(pages)} cleaned")

    print(f"[dewatermark] done -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

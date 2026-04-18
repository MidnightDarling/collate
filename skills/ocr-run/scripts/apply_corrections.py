#!/usr/bin/env python3
"""Apply a browser-edited `corrected.md` back onto `raw.md`.

preview.html lets the user fix OCR errors in the browser and click
"下载修改后的 Markdown" — the browser saves a file called `corrected.md`
into the user's download directory. This script is what the ocr-run
skill calls to move that correction into place, so the user never has
to `mv` the file themselves.

Behaviour:
    1. Locate the most recent `corrected.md` (explicit --corrected path,
       or the newest file named `corrected*.md` under ~/Downloads).
    2. Back up the current `<ocr-dir>/raw.md` to `raw.md.bak` (timestamped
       if a backup already exists so we never overwrite history).
    3. Move `corrected.md` over `raw.md`.
    4. Print a summary.

Usage:
    python3 apply_corrections.py --ocr-dir /path/to/foo.ocr
    python3 apply_corrections.py --ocr-dir /path/to/foo.ocr \
        --corrected ~/Downloads/corrected.md
    python3 apply_corrections.py --ocr-dir /path/to/foo.ocr --dry-run
"""
from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path


def find_corrected(download_dir: Path) -> Path | None:
    """Return the most recently modified `corrected*.md` in download_dir."""
    if not download_dir.is_dir():
        return None
    candidates = sorted(
        download_dir.glob("corrected*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def backup_path(raw_md: Path) -> Path:
    """Pick a backup path for raw.md that does not clobber existing backups."""
    simple = raw_md.with_suffix(raw_md.suffix + ".bak")
    if not simple.exists():
        return simple
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return raw_md.with_suffix(f"{raw_md.suffix}.bak.{stamp}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ocr-dir", required=True, type=Path,
                    help="Directory containing raw.md (usually <pdf>.ocr/)")
    ap.add_argument("--corrected", type=Path,
                    help="Explicit path to corrected.md; otherwise autodetect")
    ap.add_argument("--download-dir", type=Path,
                    default=Path.home() / "Downloads",
                    help="Where to look for corrected.md if --corrected omitted")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the plan but do not touch any files")
    args = ap.parse_args()

    raw_md = args.ocr_dir / "raw.md"
    if not raw_md.is_file():
        print(f"raw.md not found: {raw_md}", file=sys.stderr)
        return 2

    corrected = args.corrected
    if corrected is None:
        corrected = find_corrected(args.download_dir)
        if corrected is None:
            print(
                f"no corrected*.md in {args.download_dir} — "
                "either pass --corrected <path> or re-download from preview.html",
                file=sys.stderr,
            )
            return 3

    if not corrected.is_file():
        print(f"corrected.md not found: {corrected}", file=sys.stderr)
        return 2

    if corrected.resolve() == raw_md.resolve():
        print("--corrected and raw.md point at the same file; nothing to do",
              file=sys.stderr)
        return 4

    if corrected.stat().st_size == 0:
        print(
            f"refusing to apply an empty corrected file: {corrected}",
            file=sys.stderr,
        )
        return 5

    bak = backup_path(raw_md)
    print(f"plan:")
    print(f"  backup {raw_md} -> {bak}")
    print(f"  move   {corrected} -> {raw_md}")
    if args.dry_run:
        print("(dry-run, nothing changed)")
        return 0

    shutil.copy2(raw_md, bak)
    shutil.move(str(corrected), raw_md)
    print(
        f"applied corrections: raw.md now has {raw_md.stat().st_size} bytes "
        f"(backup at {bak.name})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Import MinerU Desktop output into the plugin's `.ocr/` layout.

MinerU Desktop writes every job into `~/mineru/<pdf-basename>.pdf-<uuid>/`
with files named:
    - full.md                         (MinerU's own markdown)
    - content_list_v2.json            (structured block list; what we actually use)
    - <jobid>_content_list.json       (legacy v1 schema; ignored here)
    - <jobid>_model.json              (model invocation metadata)
    - <jobid>_origin.pdf              (copy of the submitted PDF)
    - layout.json                     (per-page layout + discarded_blocks)

This script locates the right directory for a given PDF, calls
`reflow_mineru.py` to rebuild a clean `raw.md` from `content_list_v2.json`,
and writes a `meta.json` that matches the plugin's OCR contract so
proofread / preview / to-docx can run unchanged.

Usage:
    python3 import_mineru_output.py \\
        --pdf text/foo.pdf \\
        --out text/foo.ocr \\
        [--mineru-dir ~/mineru]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


def extract_title_and_author(content_list: list) -> tuple[str, str]:
    """Pull the document title and likely author name from MinerU's blocks.

    Layout conventions we handle:
      - CNKI / 社科 journal: `title` → `paragraph: "作者名"` → `paragraph: "摘要…"`
      - WPS-composed / self-typeset: `title` → `title(level=2|3): "作者名"`
                                       → `paragraph: "【摘要】…"`
    Either shape is accepted: the author is the FIRST short, punctuation-free
    non-structural block immediately after the first title, so long as it
    isn't itself an abstract / keyword / editor label.
    """
    title = ""
    title_seen = False
    for page in content_list:
        for b in page:
            btype = b.get("type", "")
            c = b.get("content") or {}
            if btype == "title" and not title_seen:
                spans = c.get("title_content", []) or []
                title = "".join(
                    s.get("content", "") for s in spans if s.get("type") == "text"
                ).strip()
                title_seen = True
                continue
            if title_seen and btype in {"paragraph", "title"}:
                # Gather the block's text regardless of tag.
                if btype == "paragraph":
                    spans = c.get("paragraph_content", []) or []
                else:
                    spans = c.get("title_content", []) or []
                text = "".join(
                    s.get("content", "") for s in spans if s.get("type") == "text"
                ).strip()
                if not text:
                    continue
                # Skip the abstract / keywords / editor lines.
                if text.startswith(
                    ("摘要", "【摘要", "关键词", "【关键词", "作者", "基金",
                     "[责任编辑", "责任编辑", "Abstract", "Keywords")
                ):
                    return title, ""
                # Plausible author: short, no punctuation, no digits.
                if (
                    len(text) <= 30
                    and not any(ch in text for ch in "。；！？，,.;!?()[]（）【】")
                    and not any(ch.isdigit() for ch in text)
                ):
                    return title, text
                # Longer / punctuated line after the title is likely the
                # abstract first paragraph — give up cleanly.
                return title, ""
    return title, ""


def extract_year(pdf: Path, content_list: list) -> str:
    """Best-effort year of publication.

    We try, in order:
      1. the PDF's own CreationDate metadata (D:YYYYMMDDHHmmss format)
      2. a 4-digit year between 1900-2099 in the body of the first page
      3. the PDF file's mtime year
    Returns "" when none of these succeeds — the caller just omits the field.
    """
    # 1. PDF metadata
    try:
        import PyPDF2
        with pdf.open("rb") as fh:
            r = PyPDF2.PdfReader(fh)
            meta = r.metadata or {}
            raw = (meta.get("/CreationDate") or meta.get("/ModDate") or "") or ""
            m = re.search(r"(\d{4})", str(raw))
            if m:
                y = int(m.group(1))
                if 1900 <= y <= 2099:
                    return str(y)
    except Exception:
        pass

    # 2. body text of page 1
    try:
        if content_list:
            for b in content_list[0]:
                c = b.get("content") or {}
                text = ""
                for key in ("paragraph_content", "title_content"):
                    for s in c.get(key, []) or []:
                        text += s.get("content", "")
                m = re.search(r"(19\d{2}|20\d{2})\s*年", text)
                if m:
                    return m.group(1)
    except Exception:
        pass

    # 3. mtime fallback
    try:
        return time.strftime("%Y", time.localtime(pdf.stat().st_mtime))
    except Exception:
        return ""


_FILENAME_BAD = re.compile(r'[\x00-\x1f<>:"/\\|?*]')


def safe_filename_fragment(s: str, max_len: int = 60) -> str:
    """Sanitise a title/author fragment for use in a filename."""
    s = (s or "").strip()
    s = _FILENAME_BAD.sub("", s)
    # Collapse repeated whitespace and replace with single space.
    s = re.sub(r"\s+", " ", s)
    if len(s) > max_len:
        s = s[:max_len].rstrip()
    return s


def build_artifact_basename(title: str, author: str, year: str) -> str:
    """Compose `<title>_<author>_<year>_` as the user's preferred draft name.

    The trailing underscore is deliberate — it matches the user's naming
    convention for WIP drafts (`..._YYYY_` leaves a slot for revision
    suffixes like `..._2023_v2.docx`). We substitute "未知" for missing
    fields so the shape is stable.
    """
    parts = [
        safe_filename_fragment(title) or "未知标题",
        safe_filename_fragment(author) or "未知作者",
        safe_filename_fragment(year) or "未知年份",
    ]
    return "_".join(parts) + "_"


def find_job_dir(mineru_dir: Path, pdf: Path) -> Path | None:
    """Return the newest `<pdf-stem>.pdf-*/` directory for this PDF, if any."""
    if not mineru_dir.is_dir():
        return None
    # MinerU uses the ORIGINAL filename + `.pdf-<uuid>` as directory name,
    # even when the PDF has no .pdf suffix. We search on the stem.
    candidates = [d for d in mineru_dir.iterdir()
                  if d.is_dir() and d.name.startswith(f"{pdf.stem}.pdf-")]
    if not candidates:
        return None
    return max(candidates, key=lambda d: d.stat().st_mtime)


def run_reflow(content_list: Path, out_raw: Path, script_dir: Path) -> None:
    reflow = script_dir / "reflow_mineru.py"
    if not reflow.is_file():
        raise RuntimeError(f"reflow_mineru.py not found at {reflow}")
    subprocess.run(
        [sys.executable, str(reflow),
         "--content-list", str(content_list),
         "--out", str(out_raw)],
        check=True,
    )


def build_meta(content_list: Path) -> dict:
    """Produce a meta.json that matches the plugin contract."""
    try:
        cl = json.loads(content_list.read_text(encoding="utf-8"))
    except Exception:
        cl = []
    pages = len(cl) if isinstance(cl, list) else 0

    # Heuristic low-confidence pages: pages with almost no paragraph content
    # (often cover, blank, or OCR-failed pages in the middle of a scan).
    low_conf: list[int] = []
    if isinstance(cl, list):
        for idx, page in enumerate(cl, 1):
            body_chars = 0
            for b in page:
                if b.get("type") in {"paragraph", "title", "list"}:
                    for key in ("paragraph_content", "title_content"):
                        for s in b.get("content", {}).get(key, []) or []:
                            body_chars += len(s.get("content", ""))
                    for it in b.get("content", {}).get("list_items", []) or []:
                        for s in it.get("item_content", []) or []:
                            body_chars += len(s.get("content", ""))
            if body_chars < 80:
                low_conf.append(idx)

    return {
        "engine": "mineru-desktop",
        "layout": "horizontal",
        "lang": "zh-hans",
        "pages": pages,
        # MinerU Desktop does not surface per-block confidence in the public
        # JSON, so we report null rather than fabricate a number.
        "avg_confidence": None,
        "low_confidence_pages": low_conf,
        "duration_seconds": None,
        "source": "imported from ~/mineru via import_mineru_output.py",
    }


def copy_origin_pdf(job_dir: Path, out_dir: Path) -> None:
    """Copy the PDF MinerU actually processed into .ocr/source.pdf for audit."""
    # CLI: <stem>/auto/<stem>_origin.pdf ; Desktop: <uuid>_origin.pdf at root.
    pdfs = list(job_dir.rglob("*_origin.pdf"))
    if pdfs:
        shutil.copy2(pdfs[0], out_dir / "source.pdf")


def copy_images(job_dir: Path, out_dir: Path) -> int:
    """Mirror MinerU's `images/` directory into `<ocr>/assets/`.

    reflow_mineru emits image and table references as
    `![caption](assets/<basename>)`, so the targets must live where
    md_to_docx expects them. Returns the number of files copied.
    """
    # CLI: <stem>/auto/images/ ; Desktop: <uuid>/images/
    candidates = list(job_dir.rglob("images"))
    src = next((p for p in candidates if p.is_dir()), None)
    if src is None:
        return 0
    dst = out_dir / "assets"
    dst.mkdir(exist_ok=True)
    count = 0
    for item in src.iterdir():
        if item.is_file():
            shutil.copy2(item, dst / item.name)
            count += 1
    return count


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, type=Path,
                    help="Path to the original PDF (used to locate MinerU job)")
    ap.add_argument("--out", required=True, type=Path,
                    help="Target .ocr/ directory to populate")
    ap.add_argument("--mineru-dir", type=Path, default=Path.home() / "mineru",
                    help="MinerU Desktop output root (default: ~/mineru)")
    ap.add_argument("--job-dir", type=Path,
                    help="Skip auto-discovery and use this job directory")
    args = ap.parse_args()

    if args.job_dir:
        job = args.job_dir
        if not job.is_dir():
            print(f"job dir not found: {job}", file=sys.stderr)
            return 2
    else:
        job = find_job_dir(args.mineru_dir, args.pdf)
        if job is None:
            print(
                f"no MinerU output for '{args.pdf.stem}' under {args.mineru_dir}. "
                "Submit the PDF via MinerU Desktop first.",
                file=sys.stderr,
            )
            return 3
        print(f"[import_mineru] using {job}")

    # MinerU Desktop writes `content_list_v2.json` at the job root.
    # The `mineru` CLI writes `<stem>/auto/<stem>_content_list_v2.json` —
    # accept either layout so the same agent flow works whether the user opened
    # the Desktop app or we ran the library locally.
    content_list = job / "content_list_v2.json"
    if not content_list.is_file():
        candidates = list(job.rglob("*content_list_v2.json"))
        if candidates:
            content_list = candidates[0]
    if not content_list.is_file():
        print(f"content_list_v2.json missing under {job}", file=sys.stderr)
        return 4

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "assets").mkdir(exist_ok=True)

    # 1. reflow into raw.md
    run_reflow(content_list, args.out / "raw.md", Path(__file__).resolve().parent)

    # 2. also keep MinerU's original full.md alongside for comparison / audit.
    #    CLI layout puts it at `<stem>/auto/<stem>.md`; Desktop puts it as
    #    `full.md` at the job root. Check both.
    full_candidates = [job / "full.md", *list(job.rglob("*.md"))]
    for full in full_candidates:
        if full.is_file():
            shutil.copy2(full, args.out / "mineru_full.md")
            break

    # 3. meta.json
    meta = build_meta(content_list)
    (args.out / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 4. copy the source PDF so downstream can cross-check if needed
    copy_origin_pdf(job, args.out)
    img_count = copy_images(job, args.out)
    if img_count:
        print(f"[import_mineru] copied {img_count} images -> {args.out}/assets")

    # 5. compute the artifact basename (title_author_year_) and record it
    try:
        cl = json.loads(content_list.read_text(encoding="utf-8"))
    except Exception:
        cl = []
    title, author = extract_title_and_author(cl) if isinstance(cl, list) else ("", "")
    year = extract_year(args.pdf, cl) if isinstance(cl, list) else ""
    artifact_basename = build_artifact_basename(title, author, year)

    # 6. stash a small provenance note so it's obvious later where this came from
    note = {
        "imported_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source_job_dir": str(job),
        "source_pdf_name": args.pdf.name,
        "artifact_basename": artifact_basename,
        "title": title,
        "author": author,
        "year": year,
    }
    (args.out / "_import_provenance.json").write_text(
        json.dumps(note, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        f"[import_mineru] imported -> {args.out}\n"
        f"  pages={meta['pages']}  low_confidence={meta['low_confidence_pages'] or '[]'}\n"
        f"  title={title!r}\n"
        f"  author={author!r}\n"
        f"  year={year!r}\n"
        f"  artifact_basename={artifact_basename!r}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

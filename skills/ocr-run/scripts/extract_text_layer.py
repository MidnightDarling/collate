#!/usr/bin/env python3
"""Extract an existing text layer from a PDF — the offline OCR shortcut.

A lot of sources the user downloads from (CNKI "CAJ 转 PDF", 读秀 full-text
export, modern journal archives) already ship PDFs with an embedded
text layer. prep-scan's Step 1 already detects this case and notes that
OCR can be skipped; this script is what actually produces a `raw.md`
from that text layer so the rest of the pipeline (preview.html,
proofread, to-docx) still has the expected inputs.

The output schema mirrors what mineru_client and baidu_client produce:
    - raw.md with `<!-- page N -->` markers between pages
    - meta.json with engine/layout/lang/pages/avg_confidence/low_confidence_pages
      (avg_confidence is null; low_confidence_pages is empty unless a
      page has < 50 chars of extracted text, which we treat as a hint
      that the text layer is absent or corrupted on that page)

Usage:
    python3 extract_text_layer.py --pdf input.pdf --out out_dir \
        --layout horizontal --lang zh-hans
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

try:
    import PyPDF2
except ImportError:
    print("missing dependency: pip3 install PyPDF2", file=sys.stderr)
    sys.exit(1)


# CJK punctuation that ends a paragraph. Latin punctuation is deliberately
# left off this list — running Latin text through PyPDF2 is usually fine,
# and we don't want to over-split acronyms like "U.S.".
PARA_BREAK_PUNCT = tuple("。！？；.!?;」』）)”〉》")


def strip_pua(text: str) -> str:
    """Drop Private Use Area characters that the PDF font uses for its own
    glyph bookkeeping (U+E000–U+F8FF).

    Academic PDFs from 《历史研究》 / 《近代史研究》 / CNKI routinely embed
    a custom font whose PUA codepoints stand in for full-width spaces,
    smart punctuation, or page-mark glyphs. Those characters render as
    tofu / "?" in Word, so we remove them rather than map them — any
    mapping would be specific to this one font.
    """
    return "".join(ch for ch in text if not (0xE000 <= ord(ch) <= 0xF8FF))


def _is_latin_word_char(ch: str) -> bool:
    """A character that can be the edge of a Latin word (letter / digit / closing
    punctuation that legally terminates a word, like `,` or `)`)."""
    if not ch:
        return False
    # Fast ASCII letter/digit check
    if ch.isascii() and (ch.isalnum() or ch in ",.)];:'\"" + "!?"):
        return True
    return False


def smart_merge(raw: str) -> str:
    """Reassemble the paragraph flow PyPDF2 shredded into per-line fragments.

    Academic PDFs produced by layout software place each visual line — and
    sometimes each character — as a separate text object, so PyPDF2's
    `extract_text` gives us a page of tiny fragments instead of running
    prose. The correct glue depends on the script:

    - CJK characters run together with no separator, so consecutive lines
      concatenate directly (无空格).
    - Latin / western scripts NEED a space between words, otherwise the
      page title "Consciousness, Quantum Mechanics, and the" followed by
      "Limits of Scientific Objectivism" fuses into "theLimits...".

    We inspect the characters on either side of the glue point: if either
    side is a Latin word character, insert a single space; otherwise stick
    directly. This handles pure-Chinese, pure-English, and mixed text
    without a --lang switch.

    Paragraph breaks are emitted when the current buffer ends with a
    terminal sentence punctuation (。！？；.!?;" and close-quotes) or a
    blank line appears in the source.
    """
    paragraphs: list[str] = []
    buf = ""
    for ln in raw.split("\n"):
        s = ln.strip()
        if not s:
            if buf:
                paragraphs.append(buf)
                buf = ""
            continue
        if not buf:
            buf = s
            continue
        if buf.endswith(PARA_BREAK_PUNCT):
            paragraphs.append(buf)
            buf = s
            continue
        # Line-break hyphen: PDF typesetters often split a word across
        # lines with a trailing "-". If the buffer ends in "-" and the
        # next line starts with a lower-case letter, join WITHOUT the
        # hyphen to reconstruct the original word ("frag- mentalist"
        # → "fragmentalist"). Real compound hyphens like "non-objectivist"
        # stay intact because they don't appear at a line break with a
        # following lower-case letter on a new line — they appear inside
        # a continuous line.
        if buf.rstrip().endswith("-") and s[:1].isalpha() and s[:1].islower():
            buf = buf.rstrip()[:-1] + s
            continue
        # Inter-line glue — decide whether a space is needed.
        left, right = buf[-1], s[0]
        if _is_latin_word_char(left) or _is_latin_word_char(right):
            # At least one side is Latin-script: insert a space, but avoid
            # doubling if the existing buffer already ends with whitespace.
            if buf.endswith(" "):
                buf += s
            else:
                buf += " " + s
        else:
            # Pure CJK neighbours — glue directly.
            buf += s
    if buf:
        paragraphs.append(buf)
    return "\n\n".join(paragraphs)


# Back-compat alias in case external scripts import the old name.
smart_merge_cjk = smart_merge


def extract_pages(pdf_path: Path) -> list[str]:
    """Return a list of extracted text per page (1-indexed by list position)."""
    with pdf_path.open("rb") as f:
        reader = PyPDF2.PdfReader(f)
        pages: list[str] = []
        for i, page in enumerate(reader.pages, 1):
            try:
                raw = page.extract_text() or ""
            except Exception as e:
                print(f"[text-layer] page {i} extraction error: {e}", file=sys.stderr)
                raw = ""
            pages.append(smart_merge(strip_pua(raw)))
    return pages


def extract_pdf_metadata(pdf_path: Path) -> dict:
    """Pull title / author / year from PDF metadata when present.

    Without MinerU's layout detection we have no reliable way to pick the
    title and author out of the first page's text (it's fused with the
    abstract), so we fall back to what the PDF itself declares. LaTeX /
    arXiv toolchains embed these fields faithfully; some scanned CNKI
    PDFs leave them blank, in which case the caller keeps the raw.md
    without a synthetic H1 rather than invent one.
    """
    import re as _re
    out: dict = {"title": "", "author": "", "year": ""}
    try:
        r = PyPDF2.PdfReader(pdf_path.open("rb"))
        meta = r.metadata or {}
        title = (meta.get("/Title") or "").strip()
        author = (meta.get("/Author") or "").strip()
        creation = str(meta.get("/CreationDate") or meta.get("/ModDate") or "")
        m = _re.search(r"(19\d{2}|20\d{2})", creation)
        year = m.group(1) if m else ""
        out["title"] = title
        out["author"] = author
        out["year"] = year
    except Exception as e:
        print(f"[text-layer] metadata read error: {e}", file=sys.stderr)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--layout", choices=["horizontal", "vertical"], default="horizontal")
    ap.add_argument("--lang", default="zh-hans")
    args = ap.parse_args()

    if not args.pdf.is_file():
        print(f"pdf not found: {args.pdf}", file=sys.stderr)
        return 2

    start = time.time()
    args.out.mkdir(parents=True, exist_ok=True)

    pages = extract_pages(args.pdf)
    if not pages:
        print("no pages extracted — is this really a PDF?", file=sys.stderr)
        return 3

    # Try to recover at least a title / author / year from the PDF's own
    # metadata — without MinerU's layout detection these are the only
    # structural hints we have. Present in raw.md only when populated.
    pdfmeta = extract_pdf_metadata(args.pdf)

    # Build raw.md with per-page markers (keeps preview.html aligned and
    # gives proofread the same scaffolding MinerU/Baidu output would).
    blocks: list[str] = []
    if pdfmeta["title"]:
        header = f"# {pdfmeta['title']}"
        if pdfmeta["author"]:
            header += f"\n\n{pdfmeta['author']}"
        blocks.append(header)
    low_confidence: list[int] = []
    for i, text in enumerate(pages, 1):
        blocks.append(f"<!-- page {i} -->\n\n{text}")
        # Heuristic: a page with almost no text is either blank, image-only,
        # or has a corrupt text layer. Surface it to proofread.
        if len(text.strip()) < 50:
            low_confidence.append(i)

    raw = "\n\n".join(blocks).strip() + "\n"
    (args.out / "raw.md").write_text(raw, encoding="utf-8")

    # If *every* page is low-confidence we suppress the list — it means the
    # PDF simply doesn't have a usable text layer, which is already obvious
    # from raw.md being empty. Flag the engine field instead so the agent
    # can fall back to MinerU/Baidu.
    text_layer_missing = all(len(p.strip()) < 50 for p in pages)

    # Character-length outliers (pages dramatically shorter than median).
    lengths = [len(p) for p in pages if len(p) >= 50]
    if lengths:
        median = statistics.median(lengths)
        threshold = max(200, int(median * 0.5))
        for i, p in enumerate(pages, 1):
            if i not in low_confidence and 50 <= len(p) < threshold:
                low_confidence.append(i)
        low_confidence.sort()

    meta = {
        "engine": "pdf-text-layer" if not text_layer_missing else "pdf-text-layer-empty",
        "layout": args.layout,
        "lang": args.lang,
        "pages": len(pages),
        "avg_confidence": None,  # no confidence signal from a text layer
        "low_confidence_pages": low_confidence,
        "title": pdfmeta["title"],
        "author": pdfmeta["author"],
        "year": pdfmeta["year"],
        "duration_seconds": round(time.time() - start, 3),
    }
    (args.out / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"[text-layer] extracted {len(pages)} pages "
        f"({sum(len(p) for p in pages)} chars total); "
        f"low_confidence={low_confidence or '[]'}"
    )
    if text_layer_missing:
        print(
            "[text-layer] NOTE: every page has < 50 chars — this PDF is scan-only. "
            "Re-run with mineru_client.py or baidu_client.py.",
            file=sys.stderr,
        )
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())

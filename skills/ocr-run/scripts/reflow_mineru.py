#!/usr/bin/env python3
"""Rebuild a structured markdown from MinerU Desktop's content_list_v2.json.

MinerU Desktop ships per-block classification: `paragraph`, `title`,
`page_footnote`, `page_header`, `page_number`, `page_footer`, `list`.
The `full.md` it writes keeps footnote blocks inlined with body text,
splits paragraphs across page boundaries, and leaves per-page circled
numerals (① ② ③ …) in both body and footnote text. This script fixes
all of that in one pass so the downstream Word draft is submission-ready:

    1. The first `title` becomes the document H1; subsequent `title`
       blocks become H2 (real Word Heading 1 when rendered by md_to_docx).
    2. `paragraph` blocks join into prose. When a block ends without a
       terminal punctuation it is glued to the next paragraph — this
       repairs the cross-page splits MinerU leaves in place.
    3. Every `page_footnote` and every `list` block with
       `list_type: "reference_list"` is redirected to an end-of-document
       `## 注释` section.
    4. Footnotes are renumbered linearly across the whole document
       (`[1]` `[2]` … `[N]`) and the in-body circled numerals are
       rewritten in lockstep so the text still cross-references the
       notes correctly. Merged references like `①③` become `[N][M]`,
       matching the format the user expects for 社科 journal drafts.
    5. Everything from the trailing `# ABSTRACTS` heading onward is
       dropped. These English abstracts are issue-level journal matter,
       not part of the article the user is preparing.

Usage:
    python3 reflow_mineru.py \\
        --content-list ~/mineru/<hash>/content_list_v2.json \\
        --out <outdir>/raw.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# Which block types carry body text. Everything else is page furniture.
BODY_TYPES = {"title", "paragraph", "list", "image", "table"}
DROP_TYPES = {
    "page_header",
    "page_number",
    "page_footer",
    # Side-mounted stamp text (e.g. `arXiv:2604.14234v1 [quant-ph] 14 Apr 2026`
    # that runs down the left edge of arXiv print layouts). Not body content.
    "page_aside_text",
}

# Punctuation signalling a complete sentence — determines whether two
# consecutive paragraphs should be glued. Chinese academic PDFs routinely
# split a single sentence across a page break, producing two paragraph
# blocks in the JSON that together form one sentence.
TERMINAL_PUNCT = tuple("。！？；!?;")

# Short metadata-style lines. We never glue across them, and we never glue
# INTO one. Both the prefix list and the regex cover common CNKI / 社科
# variations ("摘要：" vs "摘 要：" etc).
STRUCTURAL_PREFIXES = (
    "摘要：", "摘要:",
    "关键词：", "关键词:",
    "作者", "基金",
    "中图分类号", "文献标识码", "文章编号",
    "DOI:", "doi:",
    "[责任编辑", "[责编", "责任编辑",
)
STRUCTURAL_REGEX = re.compile(
    r"^(\[?(责任编辑|责编|作者|基金|摘\s*要|关键\s*词|"
    r"中图\s*分类号|文献\s*标识码|文章\s*编号|DOI)[:：\s])",
    re.IGNORECASE,
)

# Circled numerals ① … ⑳ in their canonical ordering. MinerU preserves
# these verbatim from the PDF, so we get ① meaning "footnote 1 on this
# page" both inside body text (as a superscript-like marker) and as the
# prefix of the matching footnote block. The linear renumbering step
# rewrites both sides together.
CIRCLED_NUMS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
_CIRCLED_SET = set(CIRCLED_NUMS)


def circled_to_int(ch: str) -> int:
    return CIRCLED_NUMS.index(ch) + 1


def parse_leading_markers(text: str) -> tuple[list[int], str]:
    """Split a footnote text into (leading-circle-markers, body).

    Examples:
        "① 参见柏拉图…"  -> ([1], "参见柏拉图…")
        "①③ 参见卢梭…"  -> ([1, 3], "参见卢梭…")
        "* 本文系…"     -> ([], "* 本文系…")
    """
    markers: list[int] = []
    i = 0
    while i < len(text) and text[i] in _CIRCLED_SET:
        markers.append(circled_to_int(text[i]))
        i += 1
    body = text[i:].lstrip()
    if not markers:
        return [], text  # leave untouched so "* 本文系…" stays prefixed
    return markers, body


def extract_text(block: dict) -> str:
    """Pull the concatenated text out of a content_list_v2 block."""
    c = block.get("content") or {}
    for key in (
        "paragraph_content",
        "title_content",
        "page_footnote_content",
        "page_header_content",
        "page_footer_content",
        "page_number_content",
        "page_aside_text_content",
    ):
        spans = c.get(key)
        if spans:
            return "".join(
                s.get("content", "") for s in spans if s.get("type") == "text"
            ).strip()
    if "list_items" in c:
        items = c["list_items"]
        parts: list[str] = []
        for it in items:
            span = "".join(
                s.get("content", "") for s in it.get("item_content", [])
                if s.get("type") == "text"
            ).strip()
            if span:
                parts.append(span)
        return "\n".join(parts)
    return ""


def _caption_text(caption_spans: list | None) -> str:
    if not caption_spans:
        return ""
    return "".join(
        s.get("content", "") for s in caption_spans if s.get("type") == "text"
    ).strip()


def extract_image_payload(block: dict) -> tuple[str, str]:
    """Return (markdown-safe caption, image_source_path) for an image block."""
    c = block.get("content") or {}
    src = ((c.get("image_source") or {}).get("path") or "").strip()
    caption = _caption_text(c.get("image_caption"))
    return caption, src


def extract_table_payload(block: dict) -> tuple[str, str, str]:
    """Return (caption, html, image_source_path) for a table block."""
    c = block.get("content") or {}
    caption = _caption_text(c.get("table_caption"))
    html = (c.get("html") or "").strip()
    src = ((c.get("image_source") or {}).get("path") or "").strip()
    return caption, html, src


def title_level(block: dict, is_first_title: bool) -> int:
    if is_first_title:
        return 1
    declared = int(block.get("content", {}).get("level", 1) or 1)
    return max(2, min(4, declared + 1))


def _is_structural(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if any(stripped.startswith(p) for p in STRUCTURAL_PREFIXES):
        return True
    if STRUCTURAL_REGEX.match(stripped):
        return True
    return False


# ---------------------------------------------------------------------------
# Pass 1 — walk the page list, collect body blocks and per-page footnotes.
# ---------------------------------------------------------------------------

def collect(
    content_list: list,
) -> tuple[
    list[list[tuple[str, str, dict]]],
    list[list[tuple[list[int], str]]],
    list[tuple[str, str, dict]],
]:
    """Return (body_pages, footnote_pages, abstract_blocks).

    Body and footnote streams work as before. `abstract_blocks` holds the
    THIS-paper English abstract that CNKI tacks on at the tail:
        # ABSTRACTS             ← the section heading
        # (1) <English title>   ← first numbered subtitle = this paper
        <body paragraphs>
        (2) ... (3) ... (4) ... ← other papers in the same issue: dropped

    Blocks are classified once here; `emit()` later places the abstract
    section between the body and the `## 注释` footnotes, matching how the
    original print layout reads.
    """
    body_pages: list[list[tuple[str, str, dict]]] = []
    foot_pages: list[list[tuple[list[int], str]]] = []
    abstracts: list[tuple[str, str, dict]] = []
    first_title_seen = False

    # Abstracts-tail state:
    #   None        — we haven't hit `# ABSTRACTS` yet
    #   "pending"   — we are inside the tail, waiting for the (1) title
    #   "keep"      — we are inside this paper's abstract; keep everything
    #   "drop"      — we are past this paper's abstract; drop the rest
    abstracts_state: str | None = None

    for page in content_list:
        body: list[tuple[str, str, dict]] = []
        foots: list[tuple[list[int], str]] = []
        for block in page:
            btype = block.get("type", "")
            if btype in DROP_TYPES:
                continue

            # Image and table blocks carry no concatenable text — their
            # content lives in `image_source`, `image_caption`, or `html`.
            # Handle them BEFORE the "skip empty text" guard so they don't
            # get silently dropped.
            if btype == "image":
                caption, src = extract_image_payload(block)
                if src:
                    body.append(("image", "", {"caption": caption, "src": src}))
                continue
            if btype == "table":
                caption, html, src = extract_table_payload(block)
                if html or src:
                    body.append(("table", "", {"caption": caption, "html": html, "src": src}))
                continue

            text = extract_text(block)
            if not text:
                continue

            stripped = text.strip()

            # --- ABSTRACTS tail handling -----------------------------------
            if abstracts_state is not None:
                if btype == "title" and re.match(r"^\(\d+\)", stripped):
                    # Numbered subtitle: the first is this paper, rest drop.
                    if abstracts_state == "pending":
                        abstracts_state = "keep"
                        abstracts.append(("title", stripped, {"level": 3}))
                    else:
                        abstracts_state = "drop"
                    continue
                if abstracts_state == "keep":
                    # Keep paragraphs and footnotes belonging to THIS paper's
                    # English abstract; skip unknown block types silently.
                    if btype == "paragraph":
                        abstracts.append(("paragraph", text, {}))
                    elif btype == "page_footnote":
                        markers, fbody = parse_leading_markers(text)
                        foots.append((markers, fbody))
                    # ignore list / other inside the abstract
                    continue
                # drop / pending — swallow anything else (other papers).
                continue

            if btype == "title":
                if stripped.upper() == "ABSTRACTS" or stripped.upper().startswith("ABSTRACTS"):
                    abstracts_state = "pending"
                    abstracts.append(("heading", "ABSTRACTS", {"level": 2}))
                    continue
                lvl = title_level(block, is_first_title=not first_title_seen)
                first_title_seen = True
                body.append(("title", text, {"level": lvl}))
                continue

            if btype == "paragraph":
                body.append(("paragraph", text, {}))
                continue

            if btype == "list":
                list_type = (block.get("content") or {}).get("list_type", "")
                if list_type == "reference_list":
                    for item in text.split("\n"):
                        item = item.strip()
                        if item:
                            markers, fbody = parse_leading_markers(item)
                            foots.append((markers, fbody))
                    continue
                body.append(("list", text, {}))
                continue

            if btype == "page_footnote":
                markers, fbody = parse_leading_markers(text)
                foots.append((markers, fbody))
                continue

            print(
                f"[reflow] unknown block type {btype!r}, treating as paragraph",
                file=sys.stderr,
            )
            body.append(("paragraph", text, {}))

        body_pages.append(body)
        foot_pages.append(foots)

    return body_pages, foot_pages, abstracts


# ---------------------------------------------------------------------------
# Pass 2 — assign one linear number per marker slot across the whole doc.
# ---------------------------------------------------------------------------

def build_marker_maps(foot_pages: list[list[tuple[list[int], str]]]) -> tuple[list[dict[int, int]], int]:
    """For each page, build a dict {circled_int: global_index}.

    The rule: the highest circled number seen on a page tells us how many
    positions that page occupies in the global [1..N] sequence. The next
    page's base advances by that amount. Entries with no markers (like
    "* 本文系…") don't consume positions.
    """
    page_maps: list[dict[int, int]] = []
    base = 0
    for foots in foot_pages:
        max_m = 0
        for markers, _ in foots:
            if markers:
                m = max(markers)
                if m > max_m:
                    max_m = m
        mapping = {i: base + i for i in range(1, max_m + 1)}
        page_maps.append(mapping)
        base += max_m
    return page_maps, base


def rewrite_circles(text: str, mapping: dict[int, int]) -> str:
    """Replace in-body circled numerals (① ② ③ …) with `[N]` bracket refs.

    Only replaces numerals that have a mapping on the current page — if a
    ⑮ shows up with no footnote ⑮ on this page, we leave it alone rather
    than silently drop the reference.
    """
    if not mapping or not text:
        return text

    def repl(m: re.Match) -> str:
        n = circled_to_int(m.group(0))
        if n in mapping:
            return f"[{mapping[n]}]"
        return m.group(0)

    return re.sub(f"[{re.escape(CIRCLED_NUMS)}]", repl, text)


# ---------------------------------------------------------------------------
# Pass 3 — emit markdown with cross-page glue, using the rewritten text.
# ---------------------------------------------------------------------------

def emit(
    body_pages: list[list[tuple[str, str, dict]]],
    foot_pages: list[list[tuple[list[int], str]]],
    page_maps: list[dict[int, int]],
    abstracts: list[tuple[str, str, dict]] | None = None,
) -> str:
    lines: list[str] = []
    prev_needs_glue = False

    for page_idx, body in enumerate(body_pages):
        mapping = page_maps[page_idx]
        for kind, raw_text, meta in body:
            text = rewrite_circles(raw_text, mapping)

            if kind == "title":
                lvl = meta.get("level", 2)
                if lines and lines[-1] != "":
                    lines.append("")
                lines.append(f"{'#' * lvl} {text}")
                lines.append("")
                prev_needs_glue = False
                continue

            if kind == "list":
                if lines and lines[-1] != "":
                    lines.append("")
                for item in text.split("\n"):
                    item = item.strip()
                    if item:
                        lines.append(item)
                lines.append("")
                prev_needs_glue = False
                continue

            if kind == "image":
                # import_mineru_output copies `<job>/images/<hash>.jpg` to
                # `<ocr>/assets/<hash>.jpg`. We always reference assets/ here.
                src = meta.get("src", "")
                caption = meta.get("caption", "") or ""
                basename = src.rsplit("/", 1)[-1] if src else ""
                alt = re.sub(r"[\[\]]", "", caption)  # brackets break markdown
                if lines and lines[-1] != "":
                    lines.append("")
                if basename:
                    lines.append(f"![{alt}](assets/{basename})")
                elif alt:
                    lines.append(f"*{alt}*")
                lines.append("")
                prev_needs_glue = False
                continue

            if kind == "table":
                # Prefer HTML passthrough when MinerU extracted table structure
                # (python-docx can't parse arbitrary HTML, but the raw HTML
                # stays legible in the Word draft for the user to manually replace).
                # Fall back to the rendered table-image if that's all we have.
                html = meta.get("html", "") or ""
                src = meta.get("src", "")
                caption = meta.get("caption", "") or ""
                if lines and lines[-1] != "":
                    lines.append("")
                if caption:
                    lines.append(f"*{caption}*")
                if html:
                    lines.append(html)
                elif src:
                    basename = src.rsplit("/", 1)[-1]
                    lines.append(f"![{caption or 'table'}](assets/{basename})")
                lines.append("")
                prev_needs_glue = False
                continue

            # paragraph
            structural = _is_structural(text)
            last_body_idx = None
            for idx in range(len(lines) - 1, -1, -1):
                ln = lines[idx]
                if not ln or ln.startswith(("#", ">")):
                    continue
                last_body_idx = idx
                break

            can_glue = False
            if (
                prev_needs_glue
                and last_body_idx is not None
                and not structural
                and not _is_structural(lines[last_body_idx])
            ):
                can_glue = True

            if can_glue and last_body_idx is not None:
                lines[last_body_idx] = lines[last_body_idx] + text
            else:
                if lines and lines[-1] != "":
                    lines.append("")
                lines.append(text)

            if structural:
                prev_needs_glue = False
            else:
                prev_needs_glue = not text.rstrip().endswith(TERMINAL_PUNCT)

    # Insert this paper's English abstract BETWEEN the body and the
    # footnote section. This matches the original print order (正文 →
    # ABSTRACTS → 注释) and preserves the `[责任编辑：...]` line that
    # sometimes sits between them.
    if abstracts:
        if lines and lines[-1] != "":
            lines.append("")
        for kind, text, meta in abstracts:
            if kind == "heading":
                lines.append(f"{'#' * meta.get('level', 2)} {text}")
                lines.append("")
            elif kind == "title":
                lines.append(f"{'#' * meta.get('level', 3)} {text}")
                lines.append("")
            elif kind == "paragraph":
                lines.append(text)
                lines.append("")

    # Trailing `## 注释` — linearly numbered across the whole document.
    any_notes = any(foot_pages)
    if any_notes:
        if lines and lines[-1] != "":
            lines.append("")
        lines.append("## 注释")
        lines.append("")
        for page_idx, foots in enumerate(foot_pages):
            mapping = page_maps[page_idx]
            for markers, body in foots:
                if not markers:
                    # Entries without circled markers (e.g. "* 本文系…")
                    # stay with their original prefix; do not assign them
                    # a number that would shift every other footnote.
                    lines.append(body)
                    lines.append("")
                    continue
                prefix = "".join(f"[{mapping[m]}]" for m in markers if m in mapping)
                lines.append(f"{prefix} {body}".strip())
                lines.append("")

    text = "\n".join(lines).rstrip() + "\n"
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def reflow(content_list: list) -> str:
    body_pages, foot_pages, abstracts = collect(content_list)
    page_maps, _ = build_marker_maps(foot_pages)
    return emit(body_pages, foot_pages, page_maps, abstracts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--content-list", required=True, type=Path,
                    help="Path to MinerU's content_list_v2.json")
    ap.add_argument("--out", required=True, type=Path,
                    help="Where to write the reflowed raw.md")
    args = ap.parse_args()

    if not args.content_list.is_file():
        print(f"content-list not found: {args.content_list}", file=sys.stderr)
        return 2

    data = json.loads(args.content_list.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        print(f"unexpected shape: {type(data).__name__}", file=sys.stderr)
        return 3

    md = reflow(data)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(md, encoding="utf-8")

    page_count = len(data)
    block_count = sum(len(p) for p in data)
    print(
        f"[reflow_mineru] {page_count} pages, {block_count} blocks -> "
        f"{args.out} ({len(md)} chars)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

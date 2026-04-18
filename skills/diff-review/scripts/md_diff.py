#!/usr/bin/env python3
"""Paragraph-level diff for raw.md vs final.md, annotated against raw.review.md.

Contract: skills/diff-review/SKILL.md Step 3.1-3.6. This script implements:
  - Paragraph splitting with original line ranges preserved
  - Paragraph-level alignment via difflib.SequenceMatcher
  - Character-level intra-paragraph diff for replace segments
  - review.md annotation parsing and cross-status labeling
    (accepted / rejected_or_missed / own_edit / unanchored)
  - Inline-styled single-file HTML + Markdown summary

Exit codes:
  0   success
  2   input file missing
  3   paragraph count diff > 80% (likely wrong-version pair)
  5   other failure
"""
from __future__ import annotations

import argparse
import difflib
import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ---------- Data classes ----------


@dataclass
class Paragraph:
    text: str
    line_start: int  # 1-based inclusive
    line_end: int    # 1-based inclusive
    index: int       # sequential index within the document


@dataclass
class ReviewItem:
    category: str                       # A / B / C
    item_id: str                        # A3
    title: str
    line_number: Optional[int]
    fragment: str
    suggestion: str
    status: str = "unanchored"          # accepted / rejected_or_missed / own_edit / unanchored
    anchored_paragraph_idx: Optional[int] = None
    reason: str = ""                    # why this status


# ---------- Paragraph splitting ----------


def split_paragraphs(text: str) -> list[Paragraph]:
    """Split on blank-line boundaries. Preserve 1-based start/end line numbers."""
    lines = text.splitlines()
    paragraphs: list[Paragraph] = []
    buf: list[str] = []
    buf_start = 0
    idx = 0
    for i, line in enumerate(lines, 1):
        if line.strip():
            if not buf:
                buf_start = i
            buf.append(line)
        else:
            if buf:
                paragraphs.append(Paragraph(
                    text="\n".join(buf),
                    line_start=buf_start,
                    line_end=i - 1,
                    index=idx,
                ))
                idx += 1
                buf = []
    if buf:
        paragraphs.append(Paragraph(
            text="\n".join(buf),
            line_start=buf_start,
            line_end=len(lines),
            index=idx,
        ))
    return paragraphs


def find_paragraph_by_line(paragraphs: list[Paragraph], line: int) -> Optional[int]:
    for p in paragraphs:
        if p.line_start <= line <= p.line_end:
            return p.index
    return None


# ---------- review.md parsing ----------


REVIEW_HEADER_RE = re.compile(
    r"^###\s+([ABC]\d+)\.\s+(.*?)(?:\s+·\s+Line\s+(\d+))?\s*$"
)


def parse_review(path: Path) -> list[ReviewItem]:
    """Parse ### A3. title · Line N entries from a raw.review.md file."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    items: list[ReviewItem] = []
    i = 0
    while i < len(lines):
        m = REVIEW_HEADER_RE.match(lines[i])
        if not m:
            i += 1
            continue
        item_id = m.group(1)
        title = (m.group(2) or "").strip()
        ln = int(m.group(3)) if m.group(3) else None
        fragment_lines: list[str] = []
        suggestion = ""
        j = i + 1
        while j < len(lines):
            peek = lines[j]
            if REVIEW_HEADER_RE.match(peek):
                break
            if peek.startswith("## ") or peek.startswith("# "):
                break
            if peek.startswith("> "):
                fragment_lines.append(peek[2:].rstrip())
            if "**建议**" in peek or peek.startswith("**建议"):
                rest = peek.split("**建议**", 1)[-1]
                rest = rest.lstrip("：:*").strip()
                if rest:
                    suggestion = rest
                elif j + 1 < len(lines):
                    suggestion = lines[j + 1].strip()
            j += 1
        items.append(ReviewItem(
            category=item_id[0],
            item_id=item_id,
            title=title,
            line_number=ln,
            fragment=" ".join(fragment_lines).strip(),
            suggestion=suggestion,
        ))
        i = j
    return items


# ---------- Alignment ----------


def paragraph_opcodes(raw: list[Paragraph], final: list[Paragraph]):
    raw_texts = [p.text for p in raw]
    final_texts = [p.text for p in final]
    sm = difflib.SequenceMatcher(None, raw_texts, final_texts, autojunk=False)
    return sm.get_opcodes()


def build_raw_to_final_map(
    opcodes, final: list[Paragraph]
) -> dict[int, tuple[str, Optional[Paragraph]]]:
    """raw_idx -> (opcode_tag, matched final paragraph or None)."""
    mapping: dict[int, tuple[str, Optional[Paragraph]]] = {}
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            for k in range(i2 - i1):
                mapping[i1 + k] = ("equal", final[j1 + k])
        elif tag == "replace":
            raw_span = i2 - i1
            final_span = j2 - j1
            for k in range(raw_span):
                fk = j1 + k if k < final_span else None
                mapping[i1 + k] = ("replace", final[fk] if fk is not None else None)
        elif tag == "delete":
            for k in range(i2 - i1):
                mapping[i1 + k] = ("delete", None)
        # insert: no raw index, handled elsewhere
    return mapping


# ---------- Character-level diff ----------


def char_diff_segments(a: str, b: str) -> list[tuple[str, str]]:
    """Return [(tag, text), ...] where tag in {equal, delete, insert}."""
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    out: list[tuple[str, str]] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.append(("equal", a[i1:i2]))
        elif tag == "delete":
            out.append(("delete", a[i1:i2]))
        elif tag == "insert":
            out.append(("insert", b[j1:j2]))
        elif tag == "replace":
            out.append(("delete", a[i1:i2]))
            out.append(("insert", b[j1:j2]))
    return out


def count_char_changes(opcodes, raw: list[Paragraph], final: list[Paragraph]) -> tuple[int, int]:
    dels = 0
    ins = 0
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            continue
        raw_text = "\n".join(p.text for p in raw[i1:i2])
        final_text = "\n".join(p.text for p in final[j1:j2])
        sm = difflib.SequenceMatcher(None, raw_text, final_text, autojunk=False)
        for t, a1, a2, b1, b2 in sm.get_opcodes():
            if t == "delete":
                dels += a2 - a1
            elif t == "insert":
                ins += b2 - b1
            elif t == "replace":
                dels += a2 - a1
                ins += b2 - b1
    return dels, ins


# ---------- Acceptance judgement ----------


KEY_EXTRACT_SEPS = ["→", "->", "⇒", "改为", "应为", "应是", "建议改为"]


def extract_key_chars(suggestion: str) -> list[str]:
    if not suggestion:
        return []
    after = suggestion
    for sep in KEY_EXTRACT_SEPS:
        if sep in suggestion:
            after = suggestion.split(sep, 1)[1]
            break
    tokens = re.findall(
        r"[\u4e00-\u9fff]{1,}|[A-Za-z]{2,}|[\[\]《》「」『』【】（）()：;；:,，]",
        after,
    )
    seen: set[str] = set()
    out: list[str] = []
    for t in tokens:
        if t and t not in seen:
            out.append(t)
            seen.add(t)
    return out[:6]


def judge_acceptance(
    item: ReviewItem,
    raw_para: Paragraph,
    final_para: Optional[Paragraph],
    opcode_tag: str,
) -> tuple[str, str]:
    """Return (status, reason)."""
    if opcode_tag == "equal":
        return ("rejected_or_missed", "段落未改动")
    if opcode_tag == "delete" or final_para is None:
        return ("accepted", "段落被删除（通常是废字符 / 重复段 的 A 类被接受）")
    keys = extract_key_chars(item.suggestion)
    if not keys:
        return ("own_edit", "建议无法抽出关键字，交给 JN 人工核")
    final_hits = sum(1 for k in keys if k in final_para.text)
    raw_hits = sum(1 for k in keys if k in raw_para.text)
    if final_hits > raw_hits:
        return ("accepted", f"关键字 {keys[:3]} 在 final 出现次数高于 raw")
    if final_hits == 0 and raw_hits == 0:
        return ("accepted", "关键字在两边都不存在——可能建议是删除某字符，视作接受")
    if final_hits == raw_hits and raw_para.text != final_para.text:
        return ("own_edit", "段落被改但关键字数相同，JN 用了不同改法")
    return ("rejected_or_missed", "关键字未进入 final")


# ---------- HTML rendering ----------


CSS = """
body{margin:0;background:#f3ede3;color:#1d1c1b;
font-family:-apple-system,"PingFang SC","Helvetica Neue",sans-serif;}
header{position:sticky;top:0;z-index:20;background:#1d1c1b;color:#f3ede3;
padding:14px 24px;display:flex;gap:18px;align-items:center;flex-wrap:wrap;}
header h1{font-size:15px;margin:0;font-weight:500;letter-spacing:.05em;}
header .stat{font-size:13px;padding:4px 10px;border-radius:2px;background:#2d2b29;}
header .stat.accepted{color:#7ec18f;}
header .stat.rejected{color:#e08a72;}
header .stat.own{color:#e0c272;}
header .actions{margin-left:auto;display:flex;gap:10px;}
header button{background:#c97d5d;color:#fff;border:0;padding:6px 14px;
border-radius:2px;cursor:pointer;font-size:13px;}
header button:hover{background:#b86a48;}
main{padding:20px;max-width:1280px;margin:0 auto;}
section.seg{background:#fff;border:1px solid #d9cfc1;border-radius:2px;
margin-bottom:14px;overflow:hidden;}
section.seg .head{padding:8px 14px;background:#e8ddcd;font-size:12px;
color:#6b6157;display:flex;gap:12px;align-items:center;letter-spacing:.05em;}
section.seg .head .tag{padding:2px 8px;border-radius:2px;font-weight:600;}
.tag.equal{background:#efe8dc;color:#6b6157;}
.tag.replace{background:#fbe5d6;color:#a3542f;}
.tag.delete{background:#f1d1d1;color:#8a3535;}
.tag.insert{background:#d4edda;color:#336341;}
.tag.accepted{background:#d4edda;color:#1f4d2c;}
.tag.rejected{background:#fbd7cd;color:#8f2b18;}
.tag.own{background:#fff3cd;color:#7a5b00;}
.tag.unanchored{background:#ececec;color:#555;}
section.seg .body{display:grid;grid-template-columns:1fr 1fr;gap:0;
border-top:1px solid #d9cfc1;}
section.seg .col{padding:14px 18px;font-family:"Songti SC","Source Han Serif SC",Georgia,serif;
font-size:14px;line-height:1.9;white-space:pre-wrap;word-break:break-word;}
section.seg .col.raw{border-right:1px solid #d9cfc1;background:#fcfaf6;}
section.seg .col.final{background:#fff;}
section.seg .col .linehint{font-family:ui-monospace,monospace;font-size:11px;
color:#a89d8f;margin-bottom:6px;letter-spacing:.05em;}
del{background:#fbe5d6;color:#a33;text-decoration:line-through;}
ins{background:#d4edda;color:#161;text-decoration:none;}
section.seg .annotations{padding:10px 14px;background:#f6f1e6;
border-top:1px solid #e5dcc9;font-size:13px;color:#4b4237;line-height:1.7;}
section.seg .annotations .item{margin:4px 0;}
section.seg .annotations .item .id{font-weight:600;color:#c97d5d;margin-right:6px;}
section.seg .annotations .item .reason{color:#6b6157;font-size:12px;margin-left:8px;}
section.seg.collapsed .body,section.seg.collapsed .annotations{display:none;}
section.seg.collapsed .head{cursor:pointer;}
"""


def render_char_segments(segments: list[tuple[str, str]], side: str) -> str:
    """Render (tag, text) segments into HTML. side in {raw, final}.
    Raw shows equal + delete; final shows equal + insert."""
    parts: list[str] = []
    for tag, chunk in segments:
        esc = html.escape(chunk)
        if tag == "equal":
            parts.append(esc)
        elif tag == "delete" and side == "raw":
            parts.append(f"<del>{esc}</del>")
        elif tag == "insert" and side == "final":
            parts.append(f"<ins>{esc}</ins>")
    return "".join(parts)


def render_segment(
    tag: str,
    raw_block: list[Paragraph],
    final_block: list[Paragraph],
    raw_indices: tuple[int, int],
    final_indices: tuple[int, int],
    annotations: list[ReviewItem],
    expand_equal: bool,
) -> str:
    """Render one opcode block as a <section>."""
    collapsed_cls = " collapsed" if (tag == "equal" and not expand_equal) else ""
    tag_label = {
        "equal": "未修改",
        "replace": "改写",
        "delete": "删除",
        "insert": "新增",
    }.get(tag, tag)

    _ = raw_indices  # reserved for future anchor rendering
    _ = final_indices
    line_info_parts = []
    if raw_block:
        line_info_parts.append(f"raw L{raw_block[0].line_start}-{raw_block[-1].line_end}")
    if final_block:
        line_info_parts.append(f"final L{final_block[0].line_start}-{final_block[-1].line_end}")
    line_info = " · ".join(line_info_parts)

    ann_summary = ""
    if annotations:
        accepted = sum(1 for a in annotations if a.status == "accepted")
        rejected = sum(1 for a in annotations if a.status == "rejected_or_missed")
        own = sum(1 for a in annotations if a.status == "own_edit")
        bits = []
        if accepted:
            bits.append(f"<span class='tag accepted'>接受 {accepted}</span>")
        if rejected:
            bits.append(f"<span class='tag rejected'>漏改 {rejected}</span>")
        if own:
            bits.append(f"<span class='tag own'>自创 {own}</span>")
        ann_summary = " ".join(bits)

    # Body (two columns)
    raw_col = ""
    final_col = ""
    if tag == "equal":
        raw_text = "\n\n".join(p.text for p in raw_block)
        final_text = "\n\n".join(p.text for p in final_block)
        raw_col = html.escape(raw_text)
        final_col = html.escape(final_text)
    elif tag == "replace":
        # Align paragraph-by-paragraph; do char diff per pair
        n = max(len(raw_block), len(final_block))
        raw_pieces = []
        final_pieces = []
        for k in range(n):
            rp = raw_block[k] if k < len(raw_block) else None
            fp = final_block[k] if k < len(final_block) else None
            if rp is not None and fp is not None:
                segs = char_diff_segments(rp.text, fp.text)
                raw_pieces.append(render_char_segments(segs, "raw"))
                final_pieces.append(render_char_segments(segs, "final"))
            elif rp is not None:
                raw_pieces.append(f"<del>{html.escape(rp.text)}</del>")
            elif fp is not None:
                final_pieces.append(f"<ins>{html.escape(fp.text)}</ins>")
        raw_col = "\n\n".join(raw_pieces)
        final_col = "\n\n".join(final_pieces)
    elif tag == "delete":
        raw_col = "".join(f"<del>{html.escape(p.text)}</del>" for p in raw_block)
        final_col = "<span style='color:#a89d8f;font-style:italic;'>（此段在 final 中已删除）</span>"
    elif tag == "insert":
        raw_col = "<span style='color:#a89d8f;font-style:italic;'>（此段为 final 新增）</span>"
        final_col = "".join(f"<ins>{html.escape(p.text)}</ins>" for p in final_block)

    # Annotation list
    ann_html = ""
    if annotations:
        items = []
        for a in annotations:
            status_label = {
                "accepted": ("accepted", "接受"),
                "rejected_or_missed": ("rejected", "漏改或拒绝"),
                "own_edit": ("own", "自创"),
                "unanchored": ("unanchored", "未锚定"),
            }.get(a.status, ("unanchored", a.status))
            suggest = html.escape(a.suggestion) if a.suggestion else "（无建议文本）"
            items.append(
                f"<div class='item'>"
                f"<span class='tag {status_label[0]}'>{status_label[1]}</span>"
                f"<span class='id'>{html.escape(a.item_id)}</span>"
                f"{html.escape(a.title)} · 建议：{suggest}"
                f"<span class='reason'>{html.escape(a.reason)}</span>"
                f"</div>"
            )
        ann_html = "<div class='annotations'>" + "".join(items) + "</div>"

    return (
        f"<section class='seg{collapsed_cls}' data-tag='{tag}'>"
        f"<div class='head'>"
        f"<span class='tag {tag}'>{tag_label}</span>"
        f"<span>{line_info}</span>"
        f"{ann_summary}"
        f"</div>"
        f"<div class='body'>"
        f"<div class='col raw'><div class='linehint'>raw.md</div>{raw_col}</div>"
        f"<div class='col final'><div class='linehint'>final.md</div>{final_col}</div>"
        f"</div>"
        f"{ann_html}"
        f"</section>"
    )


def build_html(
    raw: list[Paragraph],
    final: list[Paragraph],
    opcodes,
    items: list[ReviewItem],
    raw_path: Path,
    final_path: Path,
    expand_equal: bool,
) -> str:
    accepted = sum(1 for i in items if i.status == "accepted")
    rejected = sum(1 for i in items if i.status == "rejected_or_missed")
    own = sum(1 for i in items if i.status == "own_edit")
    unanchored = sum(1 for i in items if i.status == "unanchored")
    changed = sum(1 for op in opcodes if op[0] != "equal")
    total = len(opcodes)

    items_by_raw_idx: dict[int, list[ReviewItem]] = {}
    for it in items:
        if it.anchored_paragraph_idx is not None:
            items_by_raw_idx.setdefault(it.anchored_paragraph_idx, []).append(it)

    body_sections: list[str] = []

    for tag, i1, i2, j1, j2 in opcodes:
        raw_block = raw[i1:i2]
        final_block = final[j1:j2]
        annotations: list[ReviewItem] = []
        for idx in range(i1, i2):
            annotations.extend(items_by_raw_idx.get(idx, []))
        # own_edit detection: paragraph changed but no anchored annotation
        if tag != "equal" and not annotations and (raw_block or final_block):
            own_ann = ReviewItem(
                category="-",
                item_id="--",
                title="自创改动（agent 未标注该段）",
                line_number=None,
                fragment="",
                suggestion="",
                status="own_edit",
                reason="此段有改动但无对应 review 标注",
            )
            annotations = [own_ann]
        body_sections.append(render_segment(
            tag, raw_block, final_block,
            (i1, i2), (j1, j2),
            annotations, expand_equal,
        ))

    # Unanchored annotations go in a footer
    unanchored_items = [i for i in items if i.status == "unanchored"]
    footer_html = ""
    if unanchored_items:
        rows = []
        for a in unanchored_items:
            rows.append(
                f"<li><b>{html.escape(a.item_id)}</b> {html.escape(a.title)}"
                f" — 建议：{html.escape(a.suggestion or '（无）')}</li>"
            )
        footer_html = (
            "<section class='seg'><div class='head'><span class='tag unanchored'>"
            "未锚定标注</span><span>无行号，参考不计状态</span></div>"
            f"<div class='annotations'><ul>{''.join(rows)}</ul></div></section>"
        )

    title = f"{raw_path.stem} vs {final_path.stem}"
    head = (
        f"<header>"
        f"<h1>{html.escape(title)} · Diff Review</h1>"
        f"<span class='stat'>改动 {changed}/{total} 段</span>"
        f"<span class='stat accepted'>接受 {accepted}</span>"
        f"<span class='stat rejected'>漏改/拒绝 {rejected}</span>"
        f"<span class='stat own'>自创 {own}</span>"
        f"<span class='stat'>未锚 {unanchored}</span>"
        f"<div class='actions'>"
        f"<button onclick=\"document.querySelectorAll('section.seg.collapsed').forEach(s=>s.classList.remove('collapsed'))\">展开全部</button>"
        f"</div>"
        f"</header>"
    )

    script = (
        "<script>"
        "document.querySelectorAll('section.seg.collapsed .head').forEach(h=>{"
        "h.addEventListener('click',()=>h.parentElement.classList.toggle('collapsed'));"
        "});"
        "</script>"
    )

    return (
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)} · Diff Review</title>"
        f"<style>{CSS}</style>"
        "</head><body>"
        f"{head}"
        f"<main>{''.join(body_sections)}{footer_html}</main>"
        f"{script}"
        "</body></html>"
    )


# ---------- Markdown summary ----------


def build_summary(
    opcodes,
    items: list[ReviewItem],
    dels: int,
    ins: int,
    raw_path: Path,
    final_path: Path,
) -> str:
    changed = sum(1 for op in opcodes if op[0] != "equal")
    total = len(opcodes)
    rate = (changed / total * 100) if total else 0
    accepted = [i for i in items if i.status == "accepted"]
    rejected = [i for i in items if i.status == "rejected_or_missed"]
    own = [i for i in items if i.status == "own_edit"]
    unanchored = [i for i in items if i.status == "unanchored"]

    lines: list[str] = [
        f"# Diff 总结：{final_path.name}",
        "",
        f"- **raw**：`{raw_path}`",
        f"- **final**：`{final_path}`",
        f"- **修改段落数**：{changed} / 总段落数 {total}（改动率 {rate:.1f}%）",
        f"- **字符级改动**：删 {dels} 字 / 增 {ins} 字 / 净 {ins - dels:+d} 字",
    ]
    if items:
        lines.extend([
            f"- **接受 agent 建议**：{len(accepted)} / 共 {len([i for i in items if i.line_number is not None])} 条有锚标注",
            f"- **拒绝或漏改**：{len(rejected)} 条 —— 重点核！",
            f"- **自创改动**：{len(own)} 处",
            f"- **未锚定标注**：{len(unanchored)} 条",
        ])
    lines.append("")

    if accepted:
        lines.append("## 接受的 agent 建议")
        lines.append("")
        for a in accepted:
            ln = f"Line {a.line_number}" if a.line_number else "全文"
            lines.append(f"- `{a.item_id}` · {ln} · {a.title}")
        lines.append("")

    if rejected:
        lines.append("## 拒绝或漏改 —— 重点核")
        lines.append("")
        for a in rejected:
            ln = f"Line {a.line_number}" if a.line_number else "全文"
            lines.append(
                f"- `{a.item_id}` · {ln} · {a.title}"
                f" — 建议：{a.suggestion or '（无）'}"
            )
        lines.append("")

    if own:
        lines.append("## 自创改动（agent 标过该段但改法不同）")
        lines.append("")
        for a in own:
            ln = f"Line {a.line_number}" if a.line_number else "全文"
            lines.append(f"- `{a.item_id}` · {ln} · {a.title}")
        lines.append("")

    if unanchored:
        lines.append("## 未锚定标注（参考，不计状态）")
        lines.append("")
        for a in unanchored:
            lines.append(
                f"- `{a.item_id}` · {a.title}"
                f" — 建议：{a.suggestion or '（无）'}"
            )
        lines.append("")

    return "\n".join(lines)


# ---------- Main ----------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--final", required=True, type=Path)
    ap.add_argument("--review", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--summary", type=Path)
    ap.add_argument("--expand-equal", action="store_true")
    args = ap.parse_args()

    if not args.raw.is_file():
        print(f"raw 不存在：{args.raw}", file=sys.stderr)
        return 2
    if not args.final.is_file():
        print(f"final 不存在：{args.final}", file=sys.stderr)
        return 2

    raw_text = args.raw.read_text(encoding="utf-8")
    final_text = args.final.read_text(encoding="utf-8")

    if raw_text == final_text:
        print("raw 与 final 完全一致，无修改。不生成报告。")
        return 0

    raw_paras = split_paragraphs(raw_text)
    final_paras = split_paragraphs(final_text)

    if not raw_paras or not final_paras:
        print("raw 或 final 切不出任何段落。", file=sys.stderr)
        return 5

    diff_ratio = abs(len(final_paras) - len(raw_paras)) / max(len(raw_paras), 1)
    if diff_ratio > 0.8:
        print(
            f"段落数差异过大：raw {len(raw_paras)} 段 vs final {len(final_paras)} 段。"
            "确认是同一版 raw.md 吗？",
            file=sys.stderr,
        )
        return 3
    if diff_ratio > 0.5:
        print(
            f"警告：段落数差 {diff_ratio:.0%}，raw {len(raw_paras)} vs final {len(final_paras)}。",
            file=sys.stderr,
        )

    opcodes = paragraph_opcodes(raw_paras, final_paras)
    raw_to_final = build_raw_to_final_map(opcodes, final_paras)

    # Parse review.md (optional, degrade on error)
    items: list[ReviewItem] = []
    if args.review:
        if not args.review.is_file():
            print(f"review 路径不存在，降级为纯 diff：{args.review}", file=sys.stderr)
        else:
            try:
                items = parse_review(args.review)
            except Exception as e:
                print(f"review 解析失败，降级为纯 diff：{e}", file=sys.stderr)
                items = []

    # Anchor annotations to paragraphs and judge status
    for item in items:
        if item.line_number is None:
            item.status = "unanchored"
            item.reason = "review 条目未标行号"
            continue
        p_idx = find_paragraph_by_line(raw_paras, item.line_number)
        if p_idx is None:
            item.status = "unanchored"
            item.reason = f"Line {item.line_number} 落在任一段落之外"
            continue
        item.anchored_paragraph_idx = p_idx
        tag, final_para = raw_to_final.get(p_idx, ("equal", None))
        status, reason = judge_acceptance(item, raw_paras[p_idx], final_para, tag)
        item.status = status
        item.reason = reason

    dels, ins = count_char_changes(opcodes, raw_paras, final_paras)

    html_str = build_html(
        raw_paras, final_paras, opcodes, items,
        args.raw, args.final, args.expand_equal,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html_str, encoding="utf-8")

    if args.summary:
        summary = build_summary(
            opcodes, items,
            dels, ins, args.raw, args.final,
        )
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(summary, encoding="utf-8")

    changed = sum(1 for op in opcodes if op[0] != "equal")
    accepted = sum(1 for i in items if i.status == "accepted")
    rejected = sum(1 for i in items if i.status == "rejected_or_missed")
    own = sum(1 for i in items if i.status == "own_edit")

    print(f"改动 {changed} / 总 {len(opcodes)} 段 · 字符 -{dels} +{ins}")
    if items:
        print(f"接受 {accepted} · 漏改/拒绝 {rejected} · 自创 {own}")
    print(f"HTML: {args.out}")
    if args.summary:
        print(f"Summary: {args.summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Paragraph-level diff for raw.md vs final.md, annotated against raw.review.md.

Contract: skills/diff-review/SKILL.md Step 3.1-3.6. This script implements:
  - Paragraph splitting with original line ranges preserved
  - Paragraph-level alignment via difflib.SequenceMatcher
  - Character-level intra-paragraph diff for replace segments
  - review.md annotation parsing and cross-status labeling
    (accepted / rejected_or_missed / outside_fix / unanchored)
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

ROOT = Path(__file__).resolve().parents[3]
HELPERS = ROOT / "scripts"
if str(HELPERS) not in sys.path:
    sys.path.insert(0, str(HELPERS))

from review_contract import ReviewItem, parse_review  # noqa: E402


# ---------- Data classes ----------


@dataclass
class Paragraph:
    text: str
    line_start: int  # 1-based inclusive
    line_end: int    # 1-based inclusive
    index: int       # sequential index within the document


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
        return ("outside_fix", "建议无法抽出关键字，需人工核查")
    final_hits = sum(1 for k in keys if k in final_para.text)
    raw_hits = sum(1 for k in keys if k in raw_para.text)
    if final_hits > raw_hits:
        return ("accepted", f"关键字 {keys[:3]} 在 final 出现次数高于 raw")
    if final_hits == 0 and raw_hits == 0:
        return ("accepted", "关键字在两边都不存在——可能建议是删除某字符，视作接受")
    if final_hits == raw_hits and raw_para.text != final_para.text:
        return ("outside_fix", "段落被改但关键字数相同，采用了不同改法")
    return ("rejected_or_missed", "关键字未进入 final")


# ---------- HTML rendering ----------


CSS = """
/* Palette: hero-aligned neutral darks (ATTRIBUTION° Ink Stone family).
   Structure: #0E0E11 bg / #08080A sticky / #161618 card / #1E1E21 head.
   Raw col slightly dimmer (#121214) than final (#161618) to cue "older".
   Semantic desaturated: ok #1A2420/#A8C4B4, err #2A1A1A/#C49494,
   warn #262618/#B8AC88, info #2A241A/#D4BE94. */
body{margin:0;background:#0E0E11;color:#E0DCD6;
font-family:-apple-system,"PingFang SC","Helvetica Neue",sans-serif;}
header{position:sticky;top:0;z-index:20;background:#08080A;color:#E0DCD6;
padding:14px 24px;display:flex;gap:14px;align-items:center;flex-wrap:wrap;
border-bottom:1px solid rgba(255,255,255,.07);}
header h1{font-size:15px;margin:0;font-weight:500;letter-spacing:.05em;}
header .stat{font-size:12px;padding:4px 10px;border-radius:2px;
background:#1E1E21;color:#C9C5BF;}
header .stat.accepted{background:#1A2420;color:#A8C4B4;}
header .stat.rejected{background:#2A1A1A;color:#C49494;}
header .stat.outside{background:#262618;color:#B8AC88;}
header .hint-inline{font-size:12px;color:#9A9690;margin-left:4px;}
header .actions{margin-left:auto;display:flex;gap:10px;align-items:center;}
header button{background:transparent;color:#F0EDE6;
border:1px solid #F0EDE6;padding:6px 14px;
border-radius:2px;cursor:pointer;font-size:13px;font-weight:500;
box-shadow:0 0 24px rgba(240,237,230,.15),0 0 80px rgba(240,237,230,.04);
transition:all .15s ease;}
header button:hover{background:#F0EDE6;color:#000;}
main{padding:20px;max-width:1280px;margin:0 auto;}
section.seg{background:#161618;border:1px solid rgba(255,255,255,.07);border-radius:2px;
margin-bottom:14px;overflow:hidden;}
section.seg .head{padding:8px 14px;background:#1E1E21;font-size:12px;
color:#9A9690;display:flex;gap:12px;align-items:center;letter-spacing:.05em;
flex-wrap:wrap;}
section.seg .head .tag{padding:2px 8px;border-radius:2px;font-weight:600;font-size:11px;}
.tag.equal{background:#1E1E21;color:#605C56;}
.tag.replace{background:#2A241A;color:#D4BE94;}
.tag.delete{background:#2A1A1A;color:#C49494;}
.tag.insert{background:#1A2420;color:#A8C4B4;}
.tag.accepted{background:#1A2420;color:#A8C4B4;}
.tag.rejected{background:#2A1A1A;color:#C49494;}
.tag.outside{background:#262618;color:#B8AC88;}
.tag.unanchored{background:#1E1E21;color:#605C56;}
section.seg .body{display:grid;grid-template-columns:1fr 1fr;gap:0;
border-top:1px solid rgba(255,255,255,.07);}
section.seg .col{padding:14px 18px;
font-family:"Songti SC","Source Han Serif SC",Georgia,serif;
font-size:14px;line-height:1.9;white-space:pre-wrap;word-break:break-word;
color:#E0DCD6;}
section.seg .col.raw{border-right:1px solid rgba(255,255,255,.07);background:#121214;}
section.seg .col.final{background:#161618;}
section.seg .col .linehint{font-family:ui-monospace,monospace;font-size:11px;
color:#605C56;margin-bottom:6px;letter-spacing:.05em;}
del{background:#2A1A1A;color:#C49494;text-decoration:line-through;
padding:0 2px;border-radius:2px;}
ins{background:#1A2420;color:#A8C4B4;text-decoration:none;
padding:0 2px;border-radius:2px;}
section.seg .annotations{padding:10px 14px;background:#131315;
border-top:1px solid rgba(255,255,255,.07);font-size:13px;color:#C9C5BF;line-height:1.7;}
section.seg .annotations .item{margin:4px 0;}
section.seg .annotations .item .id{font-weight:600;color:#D4BE94;margin-right:6px;}
section.seg .annotations .item .reason{color:#605C56;font-size:12px;margin-left:8px;}
section.seg.collapsed .body,section.seg.collapsed .annotations{display:none;}
section.seg.collapsed .head{cursor:pointer;}
.footer{padding:24px;text-align:center;color:#9A9690;background:#08080A;
font-size:13px;margin-top:24px;border-top:1px solid rgba(255,255,255,.07);}
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
        outside_fix = sum(1 for a in annotations if a.status == "outside_fix")
        bits = []
        if accepted:
            bits.append(f"<span class='tag accepted'>接受 {accepted}</span>")
        if rejected:
            bits.append(f"<span class='tag rejected'>漏改 {rejected}</span>")
        if outside_fix:
            bits.append(f"<span class='tag outside'>清单外 {outside_fix}</span>")
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
        final_col = "<span style='color:#8a7d6c;'>（这段在 final 里删掉了）</span>"
    elif tag == "insert":
        raw_col = "<span style='color:#8a7d6c;'>（这段是 final 新加的）</span>"
        final_col = "".join(f"<ins>{html.escape(p.text)}</ins>" for p in final_block)

    # Annotation list
    ann_html = ""
    if annotations:
        items = []
        for a in annotations:
            status_label = {
                "accepted": ("accepted", "已接受"),
                "rejected_or_missed": ("rejected", "漏改"),
                "outside_fix": ("outside", "清单外"),
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
    outside_fix = sum(1 for i in items if i.status == "outside_fix")
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
        # outside_fix detection: paragraph changed but no anchored annotation
        if tag != "equal" and not annotations and (raw_block or final_block):
            fix_ann = ReviewItem(
                category="-",
                item_id="--",
                title="清单外修正（agent 未在该段标注）",
                line_number=None,
                fragment="",
                suggestion="",
                status="outside_fix",
                reason="此段有改动但无对应 review 标注",
            )
            annotations = [fix_ann]
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
        f"<h1>{html.escape(title)} · 自审对照</h1>"
        f"<span class='stat'>改动 {changed}/{total} 段</span>"
        f"<span class='stat accepted'>接受 {accepted}</span>"
        f"<span class='stat rejected'>漏改 {rejected}</span>"
        f"<span class='stat outside'>清单外 {outside_fix}</span>"
        f"<span class='stat'>未锚 {unanchored}</span>"
        f"<div class='actions'>"
        f"<span class='hint-inline'>把每处改动和清单条目对过了，你重点看漏改和清单外就够 ☕</span>"
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

    page_footer = (
        "<div class='footer'>"
        "有想讨论的条目告诉我就行，我保留了所有中间产物可以回溯。"
        "</div>"
    )

    return (
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)} · 自审对照</title>"
        f"<style>{CSS}</style>"
        "</head><body>"
        f"{head}"
        f"<main>{''.join(body_sections)}{footer_html}</main>"
        f"{page_footer}"
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
    outside_fix = [i for i in items if i.status == "outside_fix"]
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
            f"- **清单外修正**：{len(outside_fix)} 处",
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

    if outside_fix:
        lines.append("## 清单外修正（agent 未标注该段或采用了不同改法）")
        lines.append("")
        for a in outside_fix:
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
    outside_fix = sum(1 for i in items if i.status == "outside_fix")

    print(f"改动 {changed} / 总 {len(opcodes)} 段 · 字符 -{dels} +{ins}")
    if items:
        print(f"接受 {accepted} · 漏改/拒绝 {rejected} · 清单外 {outside_fix}")
    print(f"HTML: {args.out}")
    if args.summary:
        print(f"Summary: {args.summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

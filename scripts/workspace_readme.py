#!/usr/bin/env python3
"""Rewrite `<basename>.ocr/README.md` as the current workspace directory map.

Every skill in the historical-ocr-review pipeline calls this script after
finishing so the user always finds an up-to-date "what's in this folder"
summary at the root of the workspace.  The README is the user's entry
point — they shouldn't have to memorise the layout rules in
`references/workspace-layout.md`; opening README.md should be enough.

What this script does (and only this):

1. Read `_internal/_import_provenance.json` for title/author/year when
   present.  Missing file is fine — we degrade to filename-only headings.
2. List every file/dir defined by the authoritative layout (see
   `references/workspace-layout.md`), marking each present or absent.
3. Recurse into `previews/`, `review/`, `prep/`, `_internal/`, `output/`,
   `assets/` and show what's inside (names + size in KB).
4. Compute the current pipeline stage based on which files exist and
   suggest the next `/historical-ocr-review:<skill>` command.
5. Write the whole thing to `<workspace>/README.md`, overwriting any
   previous version.  Idempotent.

Usage:
    python3 workspace_readme.py --workspace path/to/foo.ocr
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


# The authoritative layout, duplicated here so the generator is a
# single-file tool that doesn't have to parse the spec markdown.  If the
# spec changes, update both together — see workspace-layout.md §"更新本规范".
LAYOUT_ROOT_FILES = [
    ("source.pdf",   "被处理的 PDF（prep-scan 的 cleaned.pdf 或用户原始 PDF）"),
    ("raw.md",       "OCR 产出的原始 Markdown（含 <!-- page N --> 标记）"),
    ("final.md",     "用户按 review/raw.review.md 修改后的定稿"),
    ("meta.json",    "OCR 元数据（engine/pages/low_confidence_pages/...）"),
]

LAYOUT_SUBDIRS = [
    ("assets",    "OCR 提取的图片（图表、古籍插图）"),
    ("prep",      "预处理中间态（prep-scan 工作区）"),
    ("previews",  "可视化 HTML，人眼审查用"),
    ("review",    "校对产出（proofread + diff-review 的文本报告）"),
    ("_internal", "Pipeline 簿记（调试用，可忽略）"),
    ("output",    "最终交付物（可直接发给读者 / 编辑）"),
]


def human_size(num_bytes: int) -> str:
    """Render file size in KB (rounded to 1 dp).  MB for >1000 KB."""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    kb = num_bytes / 1024
    if kb < 1000:
        return f"{kb:.1f} KB"
    mb = kb / 1024
    return f"{mb:.2f} MB"


def load_provenance(workspace: Path) -> dict:
    """Return title/author/year dict, or {} on any failure."""
    prov = workspace / "_internal" / "_import_provenance.json"
    if not prov.is_file():
        # Backwards compat: before the _internal/ move the file lived at
        # the workspace root.  Accept both for a graceful transition.
        prov = workspace / "_import_provenance.json"
    if not prov.is_file():
        return {}
    try:
        return json.loads(prov.read_text(encoding="utf-8"))
    except Exception:
        return {}


def pipeline_stage(workspace: Path) -> tuple[str, list[str]]:
    """Return (stage_label, next_step_suggestions).

    Stage is inferred from file presence.  Suggestions are ordered by
    priority — the first one is what the user probably wants to do next.
    """
    has_raw = (workspace / "raw.md").is_file()
    has_final = (workspace / "final.md").is_file()
    has_review = (workspace / "review" / "raw.review.md").is_file()
    has_diff = (workspace / "previews" / "diff-review.html").is_file()
    has_docx = any((workspace / "output").glob("*_final.docx")) if (workspace / "output").is_dir() else False
    has_mp = any((workspace / "output").glob("*_wechat.html")) if (workspace / "output").is_dir() else False
    has_prep = (workspace / "prep" / "cleaned.pdf").is_file()
    has_visual = (workspace / "previews" / "visual-prep.html").is_file()

    if not has_prep and not has_raw:
        return ("空工作区 — 还没跑任何 skill", [
            "python3 scripts/run_full_pipeline.py --pdf <path-to-pdf>",
        ])
    if has_prep and not has_raw:
        nxt = []
        if not has_visual:
            nxt.append("/historical-ocr-review:visual-preview <workspace>   # 核查清理效果")
        nxt.append("python3 scripts/run_full_pipeline.py --workspace <workspace>")
        return ("prep-scan 已完成 — 待 OCR", nxt)
    if has_raw and not has_review:
        return ("OCR 已完成 — 待校对", [
            "/historical-ocr-review:proofread <workspace>/raw.md",
            "生成 review/raw.review.md 后：python3 scripts/run_full_pipeline.py --workspace <workspace>",
        ])
    if has_review and not has_final:
        return ("校对清单已生成 — 待 agent 应用 review 清单并继续导出", [
            "python3 scripts/run_full_pipeline.py --workspace <workspace>",
        ])
    if has_final and not has_diff:
        return ("定稿已出 — 待闭环核对", [
            "python3 scripts/run_full_pipeline.py --workspace <workspace>",
        ])
    if has_final and has_diff and not has_docx:
        return ("闭环已核 — 待出交付", [
            "python3 scripts/run_full_pipeline.py --workspace <workspace>",
        ])
    if has_docx and not has_mp:
        return ("Word 稿已出 — 可继续出公众号版", [
            "python3 scripts/run_full_pipeline.py --workspace <workspace>",
        ])
    if has_docx and has_mp:
        return ("全部交付物已生成 — 完成 ✓", [])
    # Shouldn't reach here, but don't crash the README.
    return ("状态无法判定（部分文件缺失或顺序异常）", [
        "检查 <workspace>/ 根目录，或重跑上一 skill",
    ])


def list_dir_entries(d: Path, max_entries: int = 20) -> list[str]:
    """Return human-readable lines for each entry in `d`, sorted.

    Directories show "(N items)", files show size.  Truncates with
    "... 还有 K 项" when over `max_entries`.
    """
    if not d.is_dir():
        return []
    items = sorted(d.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    lines: list[str] = []
    for i, item in enumerate(items):
        if i >= max_entries:
            lines.append(f"- ... 还有 {len(items) - max_entries} 项")
            break
        if item.is_dir():
            n = sum(1 for _ in item.iterdir())
            lines.append(f"- `{item.name}/` — {n} 项")
        else:
            try:
                size = human_size(item.stat().st_size)
            except OSError:
                size = "?"
            lines.append(f"- `{item.name}` — {size}")
    return lines


def render(workspace: Path) -> str:
    """Build the README.md body as a single string."""
    prov = load_provenance(workspace)
    title = prov.get("title") or "（未知标题）"
    author = prov.get("author") or "（未知作者）"
    year = prov.get("year") or "（未知年份）"
    stage, next_steps = pipeline_stage(workspace)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    parts: list[str] = []

    # Header
    parts.append(f"# {title}")
    parts.append("")
    parts.append(f"> 作者：{author} · 年份：{year}")
    parts.append(f"> 工作区：`{workspace.name}/` · 更新于 {now}")
    parts.append("")
    parts.append(
        "本 README 由 `scripts/workspace_readme.py` 自动生成，"
        "列出当前工作区内有什么文件、pipeline 走到哪里、下一步建议做什么。"
        "目录布局约定见插件的 `references/workspace-layout.md`。"
    )
    parts.append("")

    # Current state
    parts.append("## 当前状态")
    parts.append("")
    parts.append(f"**Pipeline 阶段**：{stage}")
    parts.append("")
    if next_steps:
        parts.append("**下一步建议**：")
        parts.append("")
        for step in next_steps:
            parts.append(f"```")
            parts.append(step)
            parts.append(f"```")
    parts.append("")

    # Root files
    parts.append("## 根目录")
    parts.append("")
    parts.append("| 文件 | 说明 | 状态 |")
    parts.append("|------|------|------|")
    for name, desc in LAYOUT_ROOT_FILES:
        p = workspace / name
        if p.is_file():
            status = f"✓ {human_size(p.stat().st_size)}"
        else:
            status = "—"
        parts.append(f"| `{name}` | {desc} | {status} |")
    parts.append("")

    # Subdirs
    for sub, desc in LAYOUT_SUBDIRS:
        d = workspace / sub
        parts.append(f"## `{sub}/` — {desc}")
        parts.append("")
        if not d.is_dir():
            parts.append("_（尚未生成）_")
            parts.append("")
            continue
        entries = list_dir_entries(d)
        if not entries:
            parts.append("_（空目录）_")
        else:
            parts.extend(entries)
        parts.append("")

    # Footer
    parts.append("---")
    parts.append("")
    parts.append(
        "## 规范速查"
        "\n\n"
        "- **根目录**：只放 `raw.md` / `final.md` / `meta.json` / `source.pdf` / `README.md`。\n"
        "- **过程产物**：`previews/`（HTML 预览）、`review/`（校对报告）、`prep/`（预处理中间态）。\n"
        "- **Pipeline 簿记**：`_internal/`（mineru_full.md、_import_provenance.json 等）。\n"
        "- **最终交付**：`output/`（docx、公众号 HTML）。\n"
        "- **重跑幂等**：重跑 skill 覆盖同名产物，不产生 `_v2` / `_new` 后缀。\n"
    )

    return "\n".join(parts).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True, type=Path,
                    help="Path to the <basename>.ocr/ directory")
    ap.add_argument("--quiet", action="store_true",
                    help="Suppress the trailing confirmation line")
    args = ap.parse_args()

    ws = args.workspace
    if not ws.is_dir():
        print(f"workspace not found: {ws}", file=sys.stderr)
        return 2
    if not ws.name.endswith(".ocr"):
        # Not fatal — the generator still works on any dir — but warn:
        # someone may be pointing us at the wrong place.
        print(
            f"[workspace_readme] warning: '{ws.name}' doesn't end with .ocr "
            "(expected <basename>.ocr). Continuing anyway.",
            file=sys.stderr,
        )

    body = render(ws)
    (ws / "README.md").write_text(body, encoding="utf-8")
    if not args.quiet:
        print(f"[workspace_readme] wrote {ws / 'README.md'} ({len(body)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Visualize prep-scan before/after results as an offline HTML.

Contract: skills/visual-preview/SKILL.md Step 3. Produces:
  - `<prep-dir>/diff_pages/page_N.png` — heatmap overlay (red highlights on
    pixels that differ between pages/ and cleaned_pages/)
  - `<prep-dir>/visual-preview.html` — single-file offline viewer with
    three-state toggle (original / cleaned / diff) per page

Exit codes:
  0   success
  2   prep dir or subdirs missing
  3   pages/cleaned_pages file-count mismatch
  5   other
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import cv2
    import numpy as np
except ImportError:
    print("missing dependency: pip3 install opencv-python", file=sys.stderr)
    sys.exit(1)


# ---------- Data ----------


@dataclass
class PageResult:
    page_num: int
    orig_name: str
    clean_name: str
    diff_name: Optional[str]
    orig_size: tuple[int, int]       # (w, h)
    clean_size: tuple[int, int]
    trimmed_pct: float               # height trim ratio
    cleaned_pct: Optional[float]     # pixel diff ratio, None if skipped
    diff_skipped_reason: str = ""


PAGE_RE = re.compile(r"page_(\d+)\.png$", re.IGNORECASE)


def imread_unicode(path: Path) -> Optional[np.ndarray]:
    """Read image via numpy buffer to bypass cv2's path-encoding quirks on macOS
    (cv2.imread returns None for some PNGs under unicode paths)."""
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
        if data.size == 0:
            return None
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None


def imwrite_unicode(path: Path, img: np.ndarray, params=None) -> bool:
    """Write image via numpy buffer for unicode path safety."""
    ext = path.suffix if path.suffix else ".png"
    try:
        ok, buf = cv2.imencode(ext, img, params or [])
        if not ok:
            return False
        buf.tofile(str(path))
        return True
    except Exception:
        return False


# ---------- Pairing ----------


def collect_pairs(prep: Path) -> list[tuple[int, Path, Path]]:
    """Return sorted [(page_num, orig_path, clean_path), ...]."""
    orig_dir = prep / "pages"
    clean_dir = prep / "cleaned_pages"
    orig_map: dict[int, Path] = {}
    clean_map: dict[int, Path] = {}
    for p in orig_dir.glob("page_*.png"):
        m = PAGE_RE.search(p.name)
        if m:
            orig_map[int(m.group(1))] = p
    for p in clean_dir.glob("page_*.png"):
        m = PAGE_RE.search(p.name)
        if m:
            clean_map[int(m.group(1))] = p
    common = sorted(set(orig_map) & set(clean_map))
    pairs = [(n, orig_map[n], clean_map[n]) for n in common]
    missing_orig = sorted(set(clean_map) - set(orig_map))
    missing_clean = sorted(set(orig_map) - set(clean_map))
    if missing_orig:
        print(f"警告：clean 有但 orig 缺的页 {missing_orig}", file=sys.stderr)
    if missing_clean:
        print(f"警告：orig 有但 clean 缺的页 {missing_clean}", file=sys.stderr)
    return pairs


# ---------- Diff heatmap ----------


def pad_to_match(smaller: np.ndarray, target_shape: tuple[int, int, int]) -> np.ndarray:
    """Pad smaller image with white to match target shape (H, W, C).

    Used when cleaned page was cropped top/bottom by remove_margins.
    Adds white border evenly on top/bottom (or left/right).
    """
    th, tw = target_shape[:2]
    sh, sw = smaller.shape[:2]
    if sh > th or sw > tw:
        # smaller is actually larger in some dim; downscale
        return cv2.resize(smaller, (tw, th), interpolation=cv2.INTER_AREA)
    dh = th - sh
    dw = tw - sw
    top = dh // 2
    bot = dh - top
    left = dw // 2
    right = dw - left
    return cv2.copyMakeBorder(
        smaller, top, bot, left, right,
        cv2.BORDER_CONSTANT, value=[255, 255, 255],
    )


def compute_diff_heatmap(
    orig_path: Path, clean_path: Path, out_path: Path, threshold: int = 25
) -> tuple[Optional[float], str]:
    """Generate heatmap overlay. Return (cleaned_pct, skip_reason)."""
    orig = imread_unicode(orig_path)
    clean = imread_unicode(clean_path)
    if orig is None or clean is None:
        return None, "读图失败"

    oh, ow = orig.shape[:2]
    ch, cw = clean.shape[:2]
    # If size mismatch is too large in any dim, skip diff
    if max(abs(oh - ch) / max(oh, 1), abs(ow - cw) / max(ow, 1)) > 0.5:
        return None, f"尺寸差异过大（orig {ow}x{oh} vs clean {cw}x{ch}）"

    if (oh, ow) != (ch, cw):
        clean_aligned = pad_to_match(clean, orig.shape)
    else:
        clean_aligned = clean

    absdiff = cv2.absdiff(orig, clean_aligned)
    gray = cv2.cvtColor(absdiff, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)

    # Dilate slightly so the heatmap is more visible
    mask_vis = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=1)

    overlay = orig.copy()
    overlay[mask_vis > 0] = [0, 0, 255]  # BGR red
    heatmap = cv2.addWeighted(orig, 0.55, overlay, 0.45, 0)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not imwrite_unicode(out_path, heatmap, [cv2.IMWRITE_PNG_COMPRESSION, 5]):
        return None, "热图写盘失败"

    total = mask.size
    changed = int(cv2.countNonZero(mask))
    return (changed / total * 100.0), ""


# ---------- Per-page result ----------


def analyze_page(
    page_num: int,
    orig_path: Path,
    clean_path: Path,
    prep: Path,
    do_diff: bool,
) -> PageResult:
    orig = imread_unicode(orig_path)
    clean = imread_unicode(clean_path)
    if orig is None or clean is None:
        return PageResult(
            page_num=page_num,
            orig_name=orig_path.name,
            clean_name=clean_path.name,
            diff_name=None,
            orig_size=(0, 0),
            clean_size=(0, 0),
            trimmed_pct=0.0,
            cleaned_pct=None,
            diff_skipped_reason="读图失败",
        )
    oh, ow = orig.shape[:2]
    ch, cw = clean.shape[:2]
    trimmed_pct = max(0.0, (oh - ch) / max(oh, 1) * 100.0)

    cleaned_pct: Optional[float] = None
    reason = ""
    diff_name: Optional[str] = None
    if do_diff:
        diff_path = prep / "diff_pages" / orig_path.name
        cleaned_pct, reason = compute_diff_heatmap(orig_path, clean_path, diff_path)
        if cleaned_pct is not None:
            diff_name = f"diff_pages/{orig_path.name}"
    else:
        reason = "已通过 --no-diff 跳过热图"

    return PageResult(
        page_num=page_num,
        orig_name=orig_path.name,
        clean_name=clean_path.name,
        diff_name=diff_name,
        orig_size=(ow, oh),
        clean_size=(cw, ch),
        trimmed_pct=trimmed_pct,
        cleaned_pct=cleaned_pct,
        diff_skipped_reason=reason,
    )


# ---------- HTML rendering ----------


CSS = """
body{margin:0;background:#1a1511;color:#ece3d5;
font-family:-apple-system,"PingFang SC","Helvetica Neue",sans-serif;}
header{position:sticky;top:0;z-index:20;background:#120e0a;color:#ece3d5;
padding:14px 24px;display:flex;gap:14px;align-items:center;flex-wrap:wrap;
border-bottom:1px solid #2a2218;}
header h1{font-size:15px;margin:0;font-weight:500;letter-spacing:.05em;}
header .stat{font-size:12px;padding:4px 10px;border-radius:2px;
background:#26201a;color:#c8bba9;}
header .stat.warn{background:#4a2d1f;color:#e8b98f;}
header .stat.ok{background:#2d3a2f;color:#9ec4a8;}
header .hint-inline{font-size:12px;color:#a89584;margin-left:4px;}
header .actions{margin-left:auto;display:flex;gap:10px;align-items:center;}
header button{background:#c97d5d;color:#120e0a;border:0;padding:6px 14px;
border-radius:2px;cursor:pointer;font-size:13px;font-weight:500;}
header button:hover{background:#d88a6a;}
main{padding:20px;max-width:1280px;margin:0 auto;}
section.page{background:#2a2218;border:1px solid #3a2d23;border-radius:2px;
margin-bottom:18px;overflow:hidden;}
section.page.flag-warn{border-left:4px solid #c97d5d;}
section.page .head{padding:10px 14px;background:#332a20;font-size:12px;
color:#a89584;display:flex;gap:14px;align-items:center;letter-spacing:.05em;
flex-wrap:wrap;}
section.page .head .num{font-weight:600;color:#ece3d5;}
section.page .head .metric{font-family:ui-monospace,monospace;font-size:11px;}
section.page .head .switch{margin-left:auto;display:flex;gap:0;}
section.page .head .switch button{background:#2a2218;border:1px solid #3a2d23;
padding:4px 12px;cursor:pointer;font-size:12px;color:#a89584;border-right:0;}
section.page .head .switch button:last-child{border-right:1px solid #3a2d23;}
section.page .head .switch button.active{background:#c97d5d;color:#120e0a;
border-color:#c97d5d;}
section.page .viewport{background:#120e0a;padding:14px;text-align:center;}
section.page .viewport img{max-width:100%;height:auto;background:#fff;
box-shadow:0 2px 14px rgba(0,0,0,.5);}
section.page .note{padding:8px 14px;background:#3a2e1a;color:#e8b98f;
font-size:12px;border-top:1px solid #2a2218;}
.legend{background:#2a2218;padding:14px 18px;border:1px solid #3a2d23;
border-radius:2px;margin-bottom:18px;font-size:13px;color:#ece3d5;line-height:1.75;}
.legend b{color:#e8b98f;}
.legend code{background:#120e0a;color:#c8bba9;padding:1px 6px;border-radius:2px;
font-size:12px;}
.legend .swatch{display:inline-block;width:14px;height:14px;vertical-align:middle;
margin-right:6px;border:1px solid #3a2d23;}
.legend .swatch.red{background:rgba(255,80,80,.55);}
.footer{padding:24px;text-align:center;color:#a89584;background:#120e0a;
font-size:13px;margin-top:24px;border-top:1px solid #2a2218;}
"""


def page_flag(result: PageResult) -> tuple[str, str]:
    """Return (css_class, note_text). Empty strings if normal."""
    notes = []
    css = ""
    if result.cleaned_pct is not None and result.cleaned_pct > 20:
        notes.append(
            f"清理比 {result.cleaned_pct:.1f}%，有点多——差异图里看看红色是不是落在正文上。"
        )
        css = "flag-warn"
    if result.trimmed_pct > 15:
        notes.append(f"裁边 {result.trimmed_pct:.1f}%，看一下首行有没有被切掉。")
        css = "flag-warn"
    if result.diff_skipped_reason and "跳过" not in result.diff_skipped_reason:
        notes.append(f"热图这页没生成：{result.diff_skipped_reason}")
    return css, " ".join(notes)


def build_page_section(result: PageResult) -> str:
    css_flag, note = page_flag(result)
    flag_cls = f" {css_flag}" if css_flag else ""
    metric_cleaned = (
        f"清理 {result.cleaned_pct:.1f}%" if result.cleaned_pct is not None else "清理 —"
    )
    metric_trim = f"裁边 {result.trimmed_pct:.1f}%"
    size_info = f"{result.orig_size[0]}×{result.orig_size[1]} → {result.clean_size[0]}×{result.clean_size[1]}"

    data_diff = f"pages/{result.orig_name}"  # fallback to original if no diff
    if result.diff_name:
        data_diff = html.escape(result.diff_name)

    img_tag = (
        f"<img "
        f"src='cleaned_pages/{html.escape(result.clean_name)}' "
        f"data-original='pages/{html.escape(result.orig_name)}' "
        f"data-cleaned='cleaned_pages/{html.escape(result.clean_name)}' "
        f"data-diff='{data_diff}' "
        f"alt='page {result.page_num}' loading='lazy'>"
    )

    note_html = f"<div class='note'>{html.escape(note)}</div>" if note else ""

    diff_btn_disabled = "" if result.diff_name else "disabled style='opacity:.4;cursor:not-allowed'"

    return (
        f"<section class='page{flag_cls}' data-page='{result.page_num}'>"
        f"<div class='head'>"
        f"<span class='num'>第 {result.page_num} 页</span>"
        f"<span class='metric'>{html.escape(metric_cleaned)}</span>"
        f"<span class='metric'>{html.escape(metric_trim)}</span>"
        f"<span class='metric'>{size_info}</span>"
        f"<div class='switch'>"
        f"<button data-view='original'>原图</button>"
        f"<button data-view='cleaned' class='active'>清理后</button>"
        f"<button data-view='diff' {diff_btn_disabled}>差异热图</button>"
        f"</div>"
        f"</div>"
        f"<div class='viewport'>{img_tag}</div>"
        f"{note_html}"
        f"</section>"
    )


def build_html(prep: Path, results: list[PageResult]) -> str:
    n = len(results)
    cleaned_vals = [r.cleaned_pct for r in results if r.cleaned_pct is not None]
    avg_cleaned = sum(cleaned_vals) / len(cleaned_vals) if cleaned_vals else 0.0
    trim_vals = [r.trimmed_pct for r in results]
    avg_trim = sum(trim_vals) / len(trim_vals) if trim_vals else 0.0

    warn_pages = [r.page_num for r in results if r.cleaned_pct is not None and r.cleaned_pct > 20]
    trim_warn_pages = [r.page_num for r in results if r.trimmed_pct > 15]

    if cleaned_vals:
        sorted_by_clean = sorted(
            [r for r in results if r.cleaned_pct is not None],
            key=lambda x: x.cleaned_pct or 0,
            reverse=True,
        )
        dirtiest = [r.page_num for r in sorted_by_clean[:3]]
        cleanest = [r.page_num for r in sorted_by_clean[-3:]]
    else:
        dirtiest = []
        cleanest = []

    header_stats = [
        f"<span class='stat'>总 {n} 页</span>",
        f"<span class='stat'>平均清理 {avg_cleaned:.1f}%</span>",
        f"<span class='stat'>平均裁边 {avg_trim:.1f}%</span>",
    ]
    if warn_pages:
        header_stats.append(
            f"<span class='stat warn'>过度清理候选 {len(warn_pages)} 页</span>"
        )
    if not warn_pages and not trim_warn_pages and cleaned_vals:
        header_stats.append("<span class='stat ok'>无异常</span>")

    head = (
        "<header>"
        f"<h1>{html.escape(prep.name)} · 清理效果预览</h1>"
        + "".join(header_stats)
        + "<div class='actions'>"
        "<span class='hint-inline'>看看清理得怎么样，有哪页觉得过了告诉我 ☕</span>"
        "<button onclick=\"applyViewAll('original')\">全部原图</button>"
        "<button onclick=\"applyViewAll('cleaned')\">全部清理后</button>"
        "<button onclick=\"applyViewAll('diff')\">全部差异图</button>"
        "</div></header>"
    )

    legend_parts = [
        "<div class='legend'>",
        "<b>这一步做了什么：</b>把扫描原页的彩色馆藏章、水印、斜纹擦掉，"
        "必要时顺手裁掉页眉页脚。每页三态可以切换——"
        "<b>原图</b> 是扫描原貌，<b>清理后</b> 是进 OCR 之前的样子，"
        "<b>差异热图</b> 里 <span class='swatch red'></span> 半透明红色就是被擦掉或裁掉的地方。",
    ]
    if warn_pages:
        legend_parts.append(
            f"<br><br><b>这些页想让你多看一眼：</b>第 {', '.join(map(str, warn_pages))} 页清理比 > 20%。"
            "打开「差异热图」看看红色是不是落在正文上——如果觉得擦过头了，"
            "告诉我，我用 <code>--keep-color</code> 或去掉 <code>--aggressive</code> 再跑一次。"
        )
    if trim_warn_pages:
        legend_parts.append(
            f"<br><b>裁边稍多：</b>第 {', '.join(map(str, trim_warn_pages))} 页裁了 > 15%，"
            "看一下首行有没有被切掉；如果被切了，我调宽裁边阈值重跑。"
        )
    if dirtiest:
        legend_parts.append(
            f"<br><br><b>最脏的几页：</b>{', '.join(map(str, dirtiest))}"
            "（清理量最大的，通常是馆藏章、水印最密集的地方）"
        )
    if cleanest and cleaned_vals and min(cleaned_vals) < 1:
        legend_parts.append(
            f"<br><b>最干净的几页：</b>{', '.join(map(str, cleanest))}（本来就没多少污染）"
        )
    legend_parts.append("</div>")
    legend = "".join(legend_parts)

    sections = "\n".join(build_page_section(r) for r in results)

    script = """
<script>
function applyViewAll(view){
    document.querySelectorAll('section.page').forEach(function(s){
        var btn = s.querySelector('.switch button[data-view="'+view+'"]');
        if(btn && !btn.disabled){ btn.click(); }
    });
}
document.querySelectorAll('.switch button').forEach(function(b){
    b.addEventListener('click', function(){
        if(b.disabled) return;
        var sec = b.closest('.page');
        var view = b.dataset.view;
        var img = sec.querySelector('img');
        var src = img.dataset[view];
        if(src){ img.src = src; }
        sec.querySelectorAll('.switch button').forEach(function(bb){
            bb.classList.toggle('active', bb === b);
        });
    });
});
</script>
"""

    footer = (
        "<div class='footer'>"
        "觉得哪页清理得不对，告诉我就行，我来重跑。"
        "</div>"
    )

    return (
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>"
        f"<title>{html.escape(prep.name)} · 清理预览</title>"
        f"<style>{CSS}</style></head><body>"
        f"{head}<main>{legend}{sections}</main>{footer}{script}"
        "</body></html>"
    )


# ---------- Main ----------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prep-dir", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--sample", type=int, default=0,
                    help="只处理前 N 页（0 = 全部）")
    ap.add_argument("--no-diff", action="store_true")
    args = ap.parse_args()

    prep = args.prep_dir
    if not prep.is_dir():
        print(f"prep 目录不存在：{prep}", file=sys.stderr)
        return 2
    if not (prep / "pages").is_dir() or not (prep / "cleaned_pages").is_dir():
        print(f"缺 pages/ 或 cleaned_pages/ 子目录", file=sys.stderr)
        return 2

    pairs = collect_pairs(prep)
    if not pairs:
        print("找不到可配对的页面", file=sys.stderr)
        return 3
    if args.sample and args.sample > 0:
        pairs = pairs[: args.sample]

    do_diff = not args.no_diff
    if do_diff:
        (prep / "diff_pages").mkdir(exist_ok=True)

    results: list[PageResult] = []
    for n, orig, clean in pairs:
        result = analyze_page(n, orig, clean, prep, do_diff)
        results.append(result)
        pct_str = f"{result.cleaned_pct:.1f}%" if result.cleaned_pct is not None else "—"
        print(f"[visual-preview] page {n}: cleaned {pct_str} trim {result.trimmed_pct:.1f}%")

    out = args.out or (prep / "visual-preview.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    html_str = build_html(prep, results)
    out.write_text(html_str, encoding="utf-8")

    n = len(results)
    cleaned_vals = [r.cleaned_pct for r in results if r.cleaned_pct is not None]
    avg_cleaned = sum(cleaned_vals) / len(cleaned_vals) if cleaned_vals else 0.0
    avg_trim = sum(r.trimmed_pct for r in results) / n if n else 0.0
    warn_pages = [r.page_num for r in results if r.cleaned_pct is not None and r.cleaned_pct > 20]

    print("")
    print(f"总页数：{n}")
    print(f"平均清理：{avg_cleaned:.1f}%")
    print(f"平均裁边：{avg_trim:.1f}%")
    if warn_pages:
        print(f"过度清理候选页（>20%）：{warn_pages}")
    print(f"输出：{out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

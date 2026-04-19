---
name: visual-preview
description: 使用场景：prep-scan 跑完后，用户说"看看清理效果""对比一下""去水印成功没""擦掉了什么""这页裁了多少""效果怎么样""让我看看结果""预览处理""visual preview"等。这个 skill 读 `<workspace>/prep/pages/`（原始）和 `<workspace>/prep/cleaned_pages/`（清理后），生成一份可直接在浏览器打开的 HTML：每页三态切换（原图 / 清理后 / 差异热图 —— 擦掉的水印馆藏章用半透明红色高亮），顶部汇总（总页数、平均清理比例、裁边总量），让用户一眼看出 prep-scan 到底做了什么、有没有误伤正文。主动触发：prep-scan 结束后用户一说"看看""对比""瞧瞧"就走，不必等用户说完整命令名。
argument-hint: "<pdf-path | workspace-path> [--sample=N] [--no-diff]"
allowed-tools: Bash, Read, Write, Edit
---

# Visual Preview — 扫描预处理效果可视化

## Task

prep-scan 做了一堆看不见的事：擦红蓝馆藏章、去对角线水印、刮掉淡灰重复水印、裁掉页眉页脚。**但用户看不到**——用户只得到一份 cleaned.pdf 和一句"清理完成"。这个 skill 把每页**处理前后**的对比直接弹到浏览器里，让用户回答三个问题：

1. **擦对了吗**：水印 / 馆藏章是不是真的没了
2. **擦过头了吗**：有没有误伤正文（淡墨古籍最危险）
3. **裁合适吗**：页眉页脚裁得是不是正好，没切到正文首行

不给用户看等于把清理结果当黑盒交付——下游校对发现误伤已经晚了。

---

## Process

### Step 1 — 定位 workspace + prep 目录

> **路径约定**：prep-scan 把图像中间态放在 `<workspace>.ocr/prep/{pages,cleaned_pages}`，本 skill 消费同一份目录。HTML 输出固定落在 `<workspace>.ocr/previews/visual-prep.html`。权威规范见插件的 `references/workspace-layout.md`。

```bash
INPUT="$1"

# 用户可能传：
#   (a) PDF 路径  ~/Downloads/论文.pdf      → 推断 论文.ocr/
#   (b) 工作区    ~/Downloads/论文.ocr/     → 直接用
#   (c) prep 目录 ~/Downloads/论文.ocr/prep → 取父目录作为工作区
if [ -d "$INPUT" ]; then
    case "$INPUT" in
        */prep)        OCR="$(dirname "$INPUT")" ;;
        *.ocr|*.ocr/)  OCR="${INPUT%/}" ;;
        *)             OCR="$INPUT" ;;
    esac
elif [ -f "$INPUT" ] && echo "$INPUT" | grep -qE '\.pdf$'; then
    DIR=$(dirname "$INPUT")
    BASE=$(basename "$INPUT" .pdf)
    OCR="$DIR/$BASE.ocr"
else
    echo "找不到工作区或 PDF：$INPUT"; exit 1
fi

PREP="$OCR/prep"
test -d "$PREP/pages"         || { echo "缺 $PREP/pages";         exit 2; }
test -d "$PREP/cleaned_pages" || { echo "缺 $PREP/cleaned_pages"; exit 2; }
mkdir -p "$OCR/previews"
```

### Step 2 — 跑脚本

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/visual-preview/scripts/visualize_prep.py" \
    --prep-dir "$PREP" \
    --out "$OCR/previews/visual-prep.html" \
    $( [ -n "$SAMPLE" ] && echo "--sample $SAMPLE" ) \
    $( [ "$NO_DIFF" = "1" ] && echo "--no-diff" )
```

### Step 3 — 脚本行为规范（visualize_prep.py 必须实现）

**3.1 输入收集**

- `<prep-dir>/pages/page_*.png` → 原始页
- `<prep-dir>/cleaned_pages/page_*.png` → 清理后
- 两者按文件名配对；任一侧缺失视作该页无效

**3.2 差异热图生成**

对每一对 (orig, clean)：

1. 若两图尺寸不同（证明裁边了），把 clean 上下或左右 pad 到 orig 尺寸（白边填充），再做 diff
2. `cv2.absdiff(orig, clean)` → 灰度 → 阈值 > 25 的像素视为"被清理"
3. 生成叠加热图：原图 + 半透明红色（`[0,0,255]` BGR，alpha=0.4）覆盖差异像素
4. 保存到 `<prep-dir>/diff_pages/page_N.png`
5. 计算清理比例：`(差异像素数 / 总像素数) * 100%`

若 `--no-diff`，跳过热图生成，只出对比。

**3.3 每页统计**

| 字段 | 来源 |
|------|------|
| `page_num` | 从文件名 `page_001.png` 提取 |
| `orig_size` | (w, h) 原图 |
| `clean_size` | (w, h) 清理后 |
| `trimmed_pct` | `(orig_h - clean_h) / orig_h` —— 裁掉的高度比例 |
| `cleaned_pct` | 差异像素比例（仅 diff 可算时） |
| `has_diff_map` | 是否生成了热图 |

**3.4 整稿汇总**

- 总页数
- 平均 `cleaned_pct`
- 平均 `trimmed_pct`
- 最脏页（`cleaned_pct` 最高的前 3 页）——可能是原有大章印或水印密集
- 最干净页（`cleaned_pct` 最低的前 3 页）——可能是本来就没污染
- **异常页**：`cleaned_pct > 20%` 的页 —— 过度清理候选，重点看（阈值与脚本 visualize_prep.py 内置常量一致）

**3.5 HTML 输出（单文件离线）**

- 内联 CSS，无外链
- 图片用**相对路径**引用，路径从 `--out` 推导到 `--prep-dir` 的相对位置。放在 `prep/` 内部 → `pages/page_001.png`；放在 `previews/` 同级 → `../prep/pages/page_001.png`。打开 HTML 时只要 prep/ 还在原处就能加载
- 顶部汇总卡片
- 每页一个 section：
  - 头部：页号、清理比例、裁边比例、三态切换按钮
  - 主体：单张图（切换 src）
- JS 纯内联，切换按钮改 img.src

**3.6 不做的事**

- 不嵌 base64 图片（PDF 会产出几十张 MB 级 PNG，HTML 会爆）
- 不联网加载字体 / 图标库
- 不改 orig / clean 目录里的任何文件（diff_pages 是新增）

### Step 4 — 刷新 README + 打开 + 报告

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace_readme.py" --workspace "$OCR"
open "$OCR/previews/visual-prep.html"
```

汇报格式：

```
可视化已生成：$OCR/previews/visual-prep.html

- 总页数：N
- 平均清理：X.X%
- 平均裁边：Y.Y%
- 可能过度清理的页：[3, 12, 38]  重点核验有无正文误伤
- 特别干净的页：[5, 7, 20]

每页三视图切换：
  原图      清理前
  清理后    cleaned.pdf 当前版本
  差异热图  红色区域为擦除 / 裁边位置
```

---

## 判断规则

- **某页 cleaned_pct > 20%** → 强警告用户："第 N 页差异超过 20%，很可能把正文当水印擦了。在差异热图里看红色覆盖是不是落在文字上。如果是，重跑 prep-scan 加 `--keep-color` 或不要 `--aggressive`"
- **整稿平均 cleaned_pct < 1%** → 温和提醒："整稿处理比例很低，可能扫描件本来就干净，也可能 prep-scan 没检测到水印。对比几页确认下"
- **裁边 > 15%** → 提示："裁得比较多，确认首行正文有没有被切"
- **prep 目录只有 pages 没 cleaned_pages** → prep-scan 还没跑完，提示用户先跑 prep-scan
- **旧版工作区（只有 `<name>.prep/`，没有 `<name>.ocr/`）**：兼容——传 `--prep-dir $OLDPREP --out $OLDPREP/visual-preview.html` 仍可工作；脚本按相对路径输出 `cleaned_pages/...`（与旧行为一致）

## 失败兜底

- OpenCV 缺失 → `pip3 install opencv-python`
- `pages/` 里 PNG 数量和 `cleaned_pages/` 对不上 → 报错 + 列出缺失页号，不静默跳过
- 图尺寸差异过大（> 50% 在任一维度）→ 不做 diff 热图（视为 cropped/resized 差异过大），只做 before/after 切换 + 记录 "diff 跳过：尺寸差异过大"
- 输出目录不可写 → 报错 + 建议用户确认 prep 目录权限

## 与其他 skill 的关系

**上游**：prep-scan 产 pages/ + cleaned_pages/，本 skill 消费
**下游**：若用户看完 visual-preview 发现清理过头，用户回头改参数重跑 prep-scan，不影响 OCR

推荐流程：

```
prep-scan ──→ <ws>.ocr/prep/pages/ + <ws>.ocr/prep/cleaned_pages/
               ↓
         visual-preview ──→ <ws>.ocr/previews/visual-prep.html
               ↓（用户批准）
           ocr-run
```

visual-preview 是清理环节的质检闸门：prep-scan 完成后先过一遍 visual-preview 确认擦除与裁边是否妥当，再进入 ocr-run。若清理误伤正文而未及时发现，后续 OCR 结果将不可用。

---

## 未来可扩展（本版不做）

- OCR 阶段的可视化（原图 vs OCR 文本已有 preview.html，但没有置信度热图）
- 校对阶段已由 diff-review 覆盖
- 全 pipeline dashboard（prep / ocr / proofread / diff 一页看完）

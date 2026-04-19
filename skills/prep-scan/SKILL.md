---
name: prep-scan
description: 使用场景：用户在 Mac 上运行 `/historical-ocr-review:prep-scan`、提供一个扫描版 PDF、说出"去水印""去馆藏章""去知网水印""去页眉页脚""预处理论文 PDF""清理扫描件""图书馆章""历史文献 OCR 前处理""国家图书馆藏""中华再造善本"等。典型输入是用户从知网、读秀、国图扫描服务、档案馆数字资源、古籍数据库下载的 PDF，上面常见问题是：红蓝馆藏章、数据库 logo 水印（知网/维普/读秀/CNKI）、扫描日期戳、页眉刊名、页脚馆藏号、古籍版心鱼尾。这个 skill 把这些都处理干净并合回一份 cleaned.pdf，给下一步 OCR 用。这个 skill 应当主动触发，只要用户提到历史论文 PDF 或图像预处理就走它，不必等用户说"预处理"三个字。
argument-hint: "<pdf-path> [--aggressive] [--keep-color] [--no-margin-trim]"
allowed-tools: Bash, Read, Write, Edit
---

# PDF 预处理 — 历史扫描件专用

## Task

用户要校对的扫描件不是干净原稿。典型来源和污染物：

| 来源 | 常见污染 |
|------|---------|
| 中国知网（CNKI）/ 万方 | 右下角 logo 水印、"中国学术期刊出版总库" 对角线水印 |
| 读秀 / 超星 | 全页淡灰"读秀学术搜索"水印 |
| 国家图书馆 / 省图 | 红色馆藏章、馆藏登记号、扫描日期戳 |
| 中华再造善本 / 古籍数据库 | 馆藏章、版权水印、影印页眉 |
| 档案馆扫描件 | 红色骑缝章、档号戳、扫描批次编号 |
| 民国期刊影印本 | 刊名页眉、期号页脚、补白广告 |

这些污染会让 OCR 把"國立北平圖書館藏"之类的章文识别进正文，也会把"下载日期：2024-xx-xx"当成脚注。你要把它们清掉，但**不能伤到正文**——尤其是淡墨古籍、残损民国报刊，比水印还浅。

输出：`<pdf-basename>.prep/cleaned.pdf` + 逐页 PNG（供 OCR 和后面的对照预览复用）。

## Process

### Step 1：确认输入

```bash
test -f "<pdf-path>" && file "<pdf-path>" | grep -qi pdf || echo "NOT_A_PDF"
```

如果 `NOT_A_PDF`，停下告诉用户："这个文件不是 PDF，请确认路径。"

**检查是不是"已 OCR 的文字版 PDF"**（比如知网下载的"CAJ 转 PDF"其实带文本层）：

```bash
python3 -c "
import PyPDF2
with open('<pdf-path>', 'rb') as f:
    r = PyPDF2.PdfReader(f)
    t = r.pages[0].extract_text() or ''
    print('TEXT_LAYER' if len(t.strip()) > 50 else 'SCAN_ONLY')
"
```

- `TEXT_LAYER` → 告诉用户："这个 PDF 已经有文字层了，理论上可以直接提取文字而不需要 OCR。我先帮你把水印去掉，但 OCR 这一步可以跳过，直接进 proofread。" 继续处理图像水印（文字层不影响）。
- `SCAN_ONLY` → 正常走完整流程

### Step 2：建工作目录

历史学者的 PDF 常在 `~/Downloads/` 或 `~/Desktop/`。在**同级**建 `.prep` 目录，不动用户原文件：

```bash
PDF="<pdf-path>"
DIR=$(dirname "$PDF")
BASE=$(basename "$PDF" .pdf)
WORK="$DIR/$BASE.prep"
mkdir -p "$WORK/pages" "$WORK/cleaned_pages" "$WORK/trimmed_pages"
cp "$PDF" "$WORK/original.pdf"
```

**为什么要备份**：用户可能一个月后才发现某页被误删，有 original 能回滚。

### Step 3：拆页成 PNG

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/prep-scan/scripts/split_pages.py" \
    --pdf "$WORK/original.pdf" \
    --out "$WORK/pages" \
    --dpi 300
```

300 DPI 是 OCR 黄金点。再高 → 图大内存贵 OCR 不多提升；再低 → 小字（民国 5 号字、古籍双行夹注）糊掉。

老扫描件本身就不到 200 DPI 的情况，强行 300 会放大噪点。脚本会先探测原图 DPI，自动封顶：原图低于 250 就不强行上采样。

### Step 4：去水印 / 去馆藏章

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/prep-scan/scripts/dewatermark.py" \
    --in "$WORK/pages" \
    --out "$WORK/cleaned_pages" \
    $( [ "$2" = "--aggressive" ] && echo "--aggressive" ) \
    $( [ "$2" = "--keep-color" ] || [ "$3" = "--keep-color" ] && echo "--keep-color" )
```

脚本处理三类水印：

1. **彩色章（红 / 蓝）**：HSV 色域分离，S 通道高饱和 + H 在红/蓝区间的像素用周围底色 inpainting。历史文献特别要处理好红色——古籍朱批和馆藏红章像素上难分，脚本会按**形状**做二次判定（章是规则矩形/圆形，批注是手写自由形状）。默认**保留朱批**、**去馆藏章**。
2. **灰度对角水印**：典型知网/维普的对角大字水印。Hough 变换检测一致角度的线性重复文本，擦除后 inpaint。
3. **浅灰重复水印**：如"读秀学术搜索"整页淡水印。形态学顶帽变换提取浅色重复纹，减去。

`--aggressive` 把阈值放宽，适合水印特别顽固的情况，代价是可能擦掉淡墨字。只在用户明确说"水印还在"时才加。

`--keep-color` 关掉颜色通道处理——处理**彩色历史地图、影印彩图**时用，用户说"这张是彩图别动颜色"就加。

### Step 5：裁页眉页脚

```bash
# 默认裁上下各 8%；输出到独立目录，不覆盖 cleaned_pages
python3 "${CLAUDE_PLUGIN_ROOT}/skills/prep-scan/scripts/remove_margins.py" \
    --in "$WORK/cleaned_pages" \
    --out "$WORK/trimmed_pages" \
    --header-ratio 0.08 \
    --footer-ratio 0.08
```

> 独立目录的意义：保留 `cleaned_pages/` 作为"仅去水印、未裁边"的中间态，一旦裁过头可以从这里直接重新裁，不必从 `pages/` 重跑去水印。

**这一步要看文献类型决定**：

| 情况 | 处理 |
|------|------|
| 现代期刊（有刊名页眉 + 页码） | 默认 8% 裁掉，Step 6 用 `trimmed_pages` 合 PDF |
| 民国报刊（刊名页眉要留作考据） | **跳过此步**，Step 6 直接用 `cleaned_pages` 合 PDF |
| 古籍（版心鱼尾 + 书口） | **跳过此步**，古籍的版式信息本身就是研究对象 |
| 档案影像（档号脚注要留） | **跳过此步** |

**判断办法**：打开 `$WORK/pages/page_001.png` 肉眼看第一页——

- 页眉是"XX 史研究 2023 年第 3 期"这类 → 裁
- 页眉是"北京大学学报（哲学社会科学版）"但整页只有两行 → 不裁（可能是封面）
- 页眉是古籍版心鱼尾 → 不裁

不确定就问用户。

### Step 6：合回 PDF

```bash
# 跑过裁边（现代期刊） → 用 trimmed_pages
# 跳过裁边（古籍/档案/民国报刊） → 用 cleaned_pages
SRC="$WORK/trimmed_pages"   # 或 "$WORK/cleaned_pages"
python3 "${CLAUDE_PLUGIN_ROOT}/skills/prep-scan/scripts/pages_to_pdf.py" \
    --in "$SRC" \
    --out "$WORK/cleaned.pdf"
```

### Step 7：报告 + 对照抽样

用中文告诉用户：

> 清理完成。
>
> - **原件备份**：`$WORK/original.pdf`（一个月内别动这个目录可以回滚）
> - **清理版**：`$WORK/cleaned.pdf`
>
> 我打开了前 3 页的对照图给你核验（`$WORK/pages/page_001.png` 原 vs `$WORK/cleaned_pages/page_001.png` 清理后）：
>   - 看看是否有**正文字被误擦**
>   - 看看是否还有**残留水印**
>
> 如果**正文被误伤** → 告诉我，重跑时加 `--keep-color`；
> 如果**水印还在** → 重跑时加 `--aggressive`。
>
> 没问题就进下一步：
> `/historical-ocr-review:ocr-run $WORK/cleaned.pdf`

用 `open` 命令直接拉起前 3 页对照图让用户看：

```bash
open "$WORK/pages/page_001.png" "$WORK/cleaned_pages/page_001.png"
```

## 判断规则

- **发现 PDF 是古籍竖排** → 本地 MinerU CLI 当前不支持 `--layout`，提示用户在 ocr-run 阶段改用 `baidu_client.py --layout vertical` 或 `mineru_client.py --layout vertical`（云端 API）。
- **发现 PDF 第一页是扉页 / 版权页** → 问用户是否把第一页从最终输出里剔除（公众号推送一般不要版权页）。
- **PDF 超过 200 页** → 建议按章节拆分处理；单次处理过大会超云 OCR 配额（若走云端），且难以核验。

## 失败兜底

- OpenCV 报 `libGL error` → `brew install opencv`
- pdf2image 报 `Unable to get page count` → poppler 没装好，让用户跑 `brew install poppler`
- PDF 加密（少见，但知网付费文献偶见）→ 告诉用户手动去密（预览.app 另存为 PDF 通常就能解）

---
description: 只跑 prep-scan（切页 → 去水印去章 → 切页眉页脚 → 合成 cleaned.pdf）
argument-hint: <pdf-path>
allowed-tools: Bash(python3:*), Bash(mkdir:*), Bash(cp:*), Read
---

只做预处理，不触发 OCR。输入：

`$ARGUMENTS`

### 工作区约定

若用户没指明，工作区默认：`<pdf-dir>/<pdf-stem>.ocr/`。必要子目录：`prep/`、`previews/`、`_internal/`。

### 顺序执行

1. 把原 PDF 复制到 `<ws>/prep/original.pdf` 和 `<ws>/source.pdf`
2. `python3 skills/prep-scan/scripts/split_pages.py --pdf <ws>/prep/original.pdf --out <ws>/prep/pages --dpi 300`
3. `python3 skills/prep-scan/scripts/dewatermark.py --in <ws>/prep/pages --out <ws>/prep/cleaned_pages`
4. `python3 skills/prep-scan/scripts/remove_margins.py --in <ws>/prep/cleaned_pages --out <ws>/prep/trimmed_pages --header-ratio 0.08 --footer-ratio 0.08`
5. `python3 skills/prep-scan/scripts/pages_to_pdf.py --in <ws>/prep/trimmed_pages --out <ws>/prep/cleaned.pdf`
6. 把 `<ws>/prep/cleaned.pdf` 复制到 `<ws>/source.pdf`（OCR 入口）
7. 生成三联预览：`python3 skills/visual-preview/scripts/visualize_prep.py --prep-dir <ws>/prep --out <ws>/previews/visual-prep.html`

### 汇报

- 工作区路径
- `cleaned.pdf` 大小与页数
- `previews/visual-prep.html` 绝对路径

提醒人类先浏览预览，确认清理效果 OK 再走 `/ocr-run`。**这一步不自动续跑 OCR。**

---
description: final.md → 学术 Word（思源宋体 12pt、首行缩进两字、连续脚注）
argument-hint: <workspace-path>
allowed-tools: Bash(python3:*), Read
---

把工作区的 `final.md` 输出为学术规格的 Word 文档。

工作区：`$ARGUMENTS`

### 前置检查

- `<workspace>/final.md` 必须存在。缺了就停手，提示人类先 `/ocr` 或 `/proofread` + apply_review
- 读 `final.md` 的第一个 `#` 一级标题，用它作为 docx 标题

### 执行

```
python3 skills/to-docx/scripts/md_to_docx.py \
  --input <workspace>/final.md \
  --title-from-first-h1
```

脚本会把 `.docx` 直接写到 `<workspace>/output/<stem>_final.docx`，并沿用仓库统一规格：思源宋体 SC 12pt、行距 1.2、字距 0.2pt、四边 2cm 页边距、首行缩进 2 字、连续脚注。

### 汇报

- 产物绝对路径
- 文档标题（第一个 H1）
- 页数（若能读出）
- 提示：公众号版本走 `/mp-format`

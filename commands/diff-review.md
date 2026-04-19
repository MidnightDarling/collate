---
description: 自审 raw.md 与 final.md 差异，分类为接受/漏改/越权/无锚
argument-hint: <workspace-path>
allowed-tools: Bash(python3:*), Read
---

对一个已经有 `raw.md` + `final.md` + `review/raw.review.md` 的工作区做闭环自审。

工作区：`$ARGUMENTS`

### 前置检查

读下面三个文件是否都在位，缺任何一个就停手报缺：

- `<workspace>/raw.md`
- `<workspace>/final.md`
- `<workspace>/review/raw.review.md`

（`final.md` 通常由 `scripts/apply_review.py` 生成；若缺，提示人类先跑 `/ocr` 或手动运行 apply_review。）

### 执行

```
python3 skills/diff-review/scripts/md_diff.py \
  --raw <workspace>/raw.md \
  --final <workspace>/final.md \
  --review <workspace>/review/raw.review.md \
  --out <workspace>/previews/diff-review.html \
  --summary <workspace>/review/diff-summary.md
```

### 汇报

- HTML 绝对路径：`<workspace>/previews/diff-review.html`
- Summary 绝对路径：`<workspace>/review/diff-summary.md`
- 四类状态的数量：`accepted` / `missed` / `outside-checklist` / `unanchored`
- 若出现 `missed` 或 `outside-checklist`，在汇报里单独列条目，提示人类复核——这是自审的重点输出

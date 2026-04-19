---
description: 为已 prep 过的工作区生成三联对比 HTML（原图 / 清理后 / 差异热图）
argument-hint: <workspace-path>
allowed-tools: Bash(python3:*), Read
---

给一个已经跑过 prep-scan 的工作区生成/刷新 visual preview。

工作区：`$ARGUMENTS`

### 执行

```
python3 skills/visual-preview/scripts/visualize_prep.py \
  --prep-dir <workspace>/prep \
  --out <workspace>/previews/visual-prep.html
```

脚本会优先用 `prep/trimmed_pages/`（已切边），若不存在退回 `prep/cleaned_pages/`（仅去水印）。页级清理比例 > 20% 会被自动标红，提示人类复查。

### 汇报

- 生成的 HTML 绝对路径
- 被标红的页码列表（若有）
- 建议：若标红页过多或误杀正文，建议回到 `/prep-scan` 调 header/footer ratio 或单独处理该页

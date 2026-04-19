---
description: 用 historical-proofreader 对 raw.md 出分级审校清单
argument-hint: <workspace-path> [classics|republican|modern]
allowed-tools: Task, Read
---

给一个已经出了 `raw.md` 的工作区做审校，产出 `review/raw.review.md`。

参数：`$ARGUMENTS`（第一个是 workspace 路径，第二个是文献类型；类型可省，由 agent 自己判）

### 前置检查

读 `<workspace>/raw.md` 确认存在，读 `<workspace>/meta.json` 拿 `low_confidence_pages`。若 `<workspace>/review/raw.review.md` 已存在，问人类是否覆盖——不要静默重写审计链。

### 调用 subagent

用 **Task tool** 调起 `historical-proofreader` agent，prompt 至少包含：

1. 文献类型：`$2`（或你自己判定的类型），对应选 `skills/proofread/references/{traditional-classics,republican-era,modern-chinese}.md` 作为参考
2. `raw.md` 全文（或相对路径 `<workspace>/raw.md`）
3. `low_confidence_pages`（从 `meta.json` 读）
4. 要求产出 **canonical review format**（`### A1. <title> · Line 42` + `> 原文` + `**建议**` + `**理由**`），legacy `## A + bullet` 只做兼容读取，不是新默认
5. 明确产物路径：`<workspace>/review/raw.review.md`

### 后处理

Subagent 返回后：

- 确认 `<workspace>/review/raw.review.md` 已落盘
- 快速扫一下每类（A/B/C）的条目数，念给人类
- 下一步提示：人类人工复核清单 → `/ocr` 自动重入 pipeline 继续跑 apply-review / diff-review / docx / wechat（或调 `/diff-review` 单独做自审）

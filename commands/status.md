---
description: 读 _pipeline_status.json，报告工作区当前阶段与下一步
argument-hint: [workspace-path]
allowed-tools: Read, Bash(ls:*), Bash(find:*)
---

汇报一个工作区当前跑到哪一步、下一步该做什么。

参数：`$ARGUMENTS`（工作区路径；若省略，按当前目录下最近修改的 `*.ocr/` 推断）

### 读状态

读 `<workspace>/_internal/_pipeline_status.json`。它至少包含：

- `stage`：prep-scan / ocr-run / proofread / apply-review / diff-review / done / failed
- `status`：ok / awaiting_agent_review / error
- `next_step`：下一步指引
- `files_preserved`：保留的审计产物

### 附加核对

扫一遍关键交付物是否在位（存在 ✓ / 缺失 ✗）：

- `<ws>/raw.md`
- `<ws>/meta.json`
- `<ws>/review/raw.review.md`
- `<ws>/final.md`
- `<ws>/previews/diff-review.html`
- `<ws>/review/diff-summary.md`
- `<ws>/output/*_final.docx`
- `<ws>/output/*_wechat.html`
- `<ws>/README.md`（工作区入口）

### 汇报格式

```
工作区：<abs path>
阶段：<stage> / <status>
下一步：<next_step>

在位：
- ...
缺失：
- ...

建议命令：<一条或两条 slash 命令>
```

若 `status=error`，把错误摘要、`cause`、`next_step` 一起念出来，引导人类进入排障——不要自己改文件。

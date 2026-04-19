---
description: 一键 OCR：扫描 PDF → Word + 公众号 HTML + 审计链
argument-hint: <pdf-path>
allowed-tools: Task, Read, Bash
---

人类递过来一份扫描 PDF，要跑完整条 pipeline 并拿到终稿：

`$ARGUMENTS`

用 **Task tool** 调起 `ocr-pipeline-operator` subagent，把这份 PDF 原样交给它，prompt 写清楚：

1. 输入 PDF 路径就是上面这一行
2. 请按 `agents/ocr-pipeline-operator.md` 里的 Canonical Workflow 推进：
   - 先跑 `python3 scripts/run_full_pipeline.py --pdf "<pdf>"` 走机械阶段
   - 读 `<workspace>/_internal/_pipeline_status.json`；若 `status=awaiting_agent_review`，按文献类型判定（classics / republican / modern）调起 `historical-proofreader`，按 review contract 把结果落盘到 `<workspace>/review/raw.review.md`
   - 再跑 `python3 scripts/run_full_pipeline.py --workspace "<workspace>"` 让 apply-review、diff-review、to-docx、mp-format 一次跑完
   - 核对 `final.md` / `previews/diff-review.html` / `review/diff-summary.md` / `output/*_final.docx` / `output/*_wechat.html` 是否都到位
3. 成功按 Human-Facing Delivery Message 模板汇报；失败按 Failure Contract 结构化回传

Agent 返回什么就把它的汇报原样给人类，不要再套一层总结。人类要看的是交付物路径、审计摘要、遗留风险，这三件事。

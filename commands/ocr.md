---
description: One-shot OCR — scanned PDF to Word + WeChat HTML + audit trail
argument-hint: <pdf-path>
allowed-tools: Task, Read, Bash
---

The user handed over a scanned PDF and wants the full pipeline to produce publishable output:

`$ARGUMENTS`

Use the **Task tool** to dispatch the `ocr-pipeline-operator` subagent. Pass the PDF path as-is with a prompt that instructs:

1. Input PDF is the path above.
2. Follow the Canonical Workflow in `agents/ocr-pipeline-operator.md`:
   - Run `python3 scripts/run_full_pipeline.py --pdf "<pdf>"` for the mechanical stages (prep → OCR).
   - Read `<workspace>/_internal/_pipeline_status.json`. If `status=awaiting_agent_review`, classify the document type (`classics` / `republican` / `modern`) and invoke `historical-proofreader` to produce `<workspace>/review/raw.review.md` in canonical review format.
   - Re-enter `python3 scripts/run_full_pipeline.py --workspace "<workspace>"` to chain apply-review, diff-review, to-docx, mp-format.
   - Verify `final.md`, `previews/diff-review.html`, `review/diff-summary.md`, `output/*_final.docx`, `output/*_wechat.html` all exist.
3. On success, report using the Human-Facing Delivery Message template; on failure, return the structured Failure Contract.

Relay the agent's delivery message verbatim to the human — no second layer of summary. The three things they care about: deliverable paths, audit summary, residual risks.

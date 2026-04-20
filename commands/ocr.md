---
description: One-shot OCR — scanned PDF to Word + WeChat HTML + audit trail
argument-hint: <pdf-path>
allowed-tools: Task, Read, Bash
---

This is the **public user path**.
Treat `python3 scripts/run_full_pipeline.py --pdf <pdf>` as an internal /
debug path unless it has been proven equivalent by the same fresh-agent
real-PDF gate.

The user handed over a scanned PDF and wants the full pipeline to produce publishable output:

`$ARGUMENTS`

Use the **Task tool** to dispatch the `ocr-pipeline-operator` subagent. Pass the PDF path as-is with a prompt that instructs:

1. Input PDF is the path above.
2. Follow the Canonical Workflow in `agents/ocr-pipeline-operator.md`:
   - Run `python3 scripts/run_full_pipeline.py --pdf "<pdf>"` for the mechanical stages (prep → OCR).
   - Read `<workspace>/_internal/_pipeline_status.json`. If `status=awaiting_agent_review`, build `review/page_review_packets.json`, classify the document type (`classics` / `republican` / `modern`), invoke `historical-proofreader` with `prep/pages/*.png` plus the packet file, and verify that `<workspace>/review/raw.review.md` is mechanically page-grounded before continuing.
   - Re-enter `python3 scripts/run_full_pipeline.py --workspace "<workspace>"` to chain apply-review, diff-review, to-docx, mp-format.
   - Verify `final.md`, `previews/diff-review.html`, `review/diff-summary.md`, `output/*_final.docx`, `output/*_wechat.html` all exist.
3. On success, report using the Human-Facing Delivery Message template; on failure, return the structured Failure Contract.

Relay the agent's delivery message verbatim to the human — no second layer of summary. The three things they care about: deliverable paths, audit summary, residual risks.

---
description: Dispatch historical-proofreader to generate a tiered review checklist
argument-hint: <workspace-path> [classics|republican|modern]
allowed-tools: Task, Read
---

Generate `review/raw.review.md` for a workspace that has `raw.md` ready.

Arguments: `$ARGUMENTS` (first is the workspace path; optional second is the document type — if absent, the agent infers).

### Preflight

Read `<workspace>/raw.md` and confirm it exists. Read `<workspace>/meta.json` and capture `low_confidence_pages`. If `<workspace>/review/raw.review.md` already exists, ask the user before overwriting — do not silently rewrite an audit trail.

### Dispatch subagent

Use the **Task tool** to invoke the `historical-proofreader` agent. The prompt must include:

1. Document type: `$2` (or the agent's own classification); select the matching `skills/proofread/references/{traditional-classics,republican-era,modern-chinese}.md`.
2. The `raw.md` content (or its path: `<workspace>/raw.md`).
3. `low_confidence_pages` from `meta.json`.
4. Require **canonical review format**: `### A1. <title> · Line 42` + `> original fragment` + `**建议**: ...` + `**理由**: ...`. Legacy `## A + bullet` is compatibility-only, not the new default.
5. Target path: `<workspace>/review/raw.review.md`.

### Post-dispatch

- Confirm `<workspace>/review/raw.review.md` is on disk.
- Quick tally: number of A / B / C items; read them out to the user.
- Next step: the human reviews the checklist, then runs `/ocr` to re-enter the pipeline (or `/diff-review` for a standalone self-audit).

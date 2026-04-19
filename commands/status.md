---
description: Read _pipeline_status.json and report workspace stage + next step
argument-hint: [workspace-path]
allowed-tools: Read, Bash(ls:*), Bash(find:*)
---

Report the current pipeline stage and recommended next action for a workspace.

Argument: `$ARGUMENTS` (workspace path; if omitted, infer from the most recently modified `*.ocr/` in the current directory).

### Read status

Read `<workspace>/_internal/_pipeline_status.json`. It contains at minimum:

- `stage`: prep-scan / ocr-run / proofread / apply-review / diff-review / done / failed
- `status`: ok / awaiting_agent_review / error
- `next_step`: guidance for the next action
- `files_preserved`: retained audit artifacts

### Artifact checklist

Verify presence of key deliverables (✓ present / ✗ missing):

- `<ws>/raw.md`
- `<ws>/meta.json`
- `<ws>/review/raw.review.md`
- `<ws>/final.md`
- `<ws>/previews/diff-review.html`
- `<ws>/review/diff-summary.md`
- `<ws>/output/*_final.docx`
- `<ws>/output/*_wechat.html`
- `<ws>/README.md` (workspace entry point)

### Report format

```
Workspace: <abs path>
Stage: <stage> / <status>
Next: <next_step>

Present:
- ...
Missing:
- ...

Suggested command: <one or two slash commands>
```

If `status=error`, include the error summary, `cause`, and `next_step`. Guide the user toward diagnosis; do not attempt to auto-fix.

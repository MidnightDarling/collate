---
description: Generate the three-state HTML preview (original / cleaned / diff heatmap)
argument-hint: <workspace-path>
allowed-tools: Bash(python3:*), Read
---

Regenerate the visual prep preview for a workspace that has already been prep-scanned.

Workspace: `$ARGUMENTS`

### Execute

```
python3 skills/visual-preview/scripts/visualize_prep.py \
  --prep-dir <workspace>/prep \
  --out <workspace>/previews/visual-prep.html
```

The script prefers `prep/trimmed_pages/` (fully cleaned + trimmed) and falls back to `prep/cleaned_pages/` (dewatermarked only). Pages with >20% cleaning ratio are auto-flagged for human review.

### Report

- Absolute path to the generated HTML
- List of auto-flagged page numbers (if any)
- Recommendation: if flags are excessive or body text was mistakenly cleaned, return to `/prep-scan` with adjusted `--header-ratio` / `--footer-ratio`, or handle problem pages individually.

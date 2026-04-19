---
description: Export final.md to academic Word (Source Han Serif SC 12pt, 2-char first-line indent, continuous footnotes)
argument-hint: <workspace-path>
allowed-tools: Bash(python3:*), Read
---

Export the workspace's `final.md` to an academic Word document.

Workspace: `$ARGUMENTS`

### Preflight

- `<workspace>/final.md` must exist. If missing, stop and prompt the user to run `/ocr` or `/proofread` + apply_review first.
- Read the first `#` H1 in `final.md` for the docx title.

### Execute

```
python3 skills/to-docx/scripts/md_to_docx.py \
  --input <workspace>/final.md \
  --title-from-first-h1
```

The script writes to `<workspace>/output/<stem>_final.docx` and applies the unified repo spec: Source Han Serif SC 12pt, 1.2 line spacing, 0.2pt character spacing, 2cm margins on all sides, 2-character first-line indent, continuous footnote numbering.

### Report

- Absolute output path
- Document title (first H1)
- Page count (if readable)
- Next: `/mp-format` for the WeChat version

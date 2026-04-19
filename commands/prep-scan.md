---
description: Preprocessing only — split, dewatermark, trim margins, build cleaned.pdf
argument-hint: <pdf-path>
allowed-tools: Bash(python3:*), Bash(mkdir:*), Bash(cp:*), Read
---

Preprocessing only. Do not trigger OCR. Input:

`$ARGUMENTS`

### Workspace convention

If not specified, default workspace: `<pdf-dir>/<pdf-stem>.ocr/`. Required subdirs: `prep/`, `previews/`, `_internal/`.

### Sequence

1. Copy the source PDF to `<ws>/prep/original.pdf` and `<ws>/source.pdf`.
2. `python3 skills/prep-scan/scripts/split_pages.py --pdf <ws>/prep/original.pdf --out <ws>/prep/pages --dpi 300`
3. `python3 skills/prep-scan/scripts/dewatermark.py --in <ws>/prep/pages --out <ws>/prep/cleaned_pages`
4. `python3 skills/prep-scan/scripts/remove_margins.py --in <ws>/prep/cleaned_pages --out <ws>/prep/trimmed_pages --header-ratio 0.08 --footer-ratio 0.08`
5. `python3 skills/prep-scan/scripts/pages_to_pdf.py --in <ws>/prep/trimmed_pages --out <ws>/prep/cleaned.pdf`
6. Copy `<ws>/prep/cleaned.pdf` to `<ws>/source.pdf` (OCR entry point).
7. Generate the three-state preview: `python3 skills/visual-preview/scripts/visualize_prep.py --prep-dir <ws>/prep --out <ws>/previews/visual-prep.html`

### Report

- Workspace path
- `cleaned.pdf` size and page count
- Absolute path to `previews/visual-prep.html`

Prompt the user to review the preview before running `/ocr-run`. **This command does not auto-continue into OCR.**

---
description: OCR stage only (local MinerU / MinerU cloud / Baidu)
argument-hint: <pdf-or-workspace>
allowed-tools: Bash(python3:*), Read
---

OCR stage only. Do not trigger downstream apply-review / docx / wechat. Input:

`$ARGUMENTS`

### Input resolution

- Input is `.pdf`: default workspace is `<pdf-dir>/<pdf-stem>.ocr/`; copy as `source.pdf` if absent.
- Input is a directory: treat as workspace; `<ws>/source.pdf` must already exist (otherwise run `/prep-scan` first).

### Engine selection

Based on `OCR_ENGINE` (default `mineru`):

| Engine | Command |
|--------|---------|
| `mineru` (local CLI, default) | `python3 skills/ocr-run/scripts/run_mineru.py --pdf <ws>/source.pdf --out <ws> --lang ch` |
| `mineru-cloud` (needs `MINERU_API_KEY`) | `python3 skills/ocr-run/scripts/mineru_client.py --pdf <ws>/source.pdf --out <ws> --layout horizontal --lang zh-hans --poll-interval 10 --timeout 1800` |
| `baidu` (needs `BAIDU_OCR_*`) | `python3 skills/ocr-run/scripts/baidu_client.py --pdf <ws>/source.pdf --out <ws>` |

If the local engine exits non-zero and `MINERU_API_KEY` is set, fall back to `mineru-cloud` once. If that also fails, stop and report. Do not silently invoke `extract_text_layer.py` — that is a last resort and requires explicit user approval.

### Report

- Engine used + elapsed time
- Artifacts: `<ws>/raw.md`, `<ws>/meta.json`
- `meta.json`'s `low_confidence_pages` (if any)
- Next step: `/proofread <workspace>`

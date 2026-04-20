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

`run_full_pipeline.py` applies the canonical fallback chain automatically:

1. `run-mineru` (local) — always attempted first
2. `mineru-cloud` — attempted if `MINERU_API_KEY` is set
3. `extract_text_layer.py` — attempted if `COLLATE_ALLOW_TEXTLAYER` is unset or `!= "0"` (default on)

`extract_text_layer.py` is the documented third-tier fallback, not a silent workaround. Its engine name (`pdf-text-layer` or `pdf-text-layer-empty`) is written to `meta.json.engine` and `_pipeline_status.json.ocr_engine`, and it carries `structural_risk: "high"` so the downstream fidelity gate requires a page-grounded proofread before export. Set `COLLATE_ALLOW_TEXTLAYER=0` to opt out (e.g., for audits that must see MinerU-only failures).

### Report

- Engine used + elapsed time
- Artifacts: `<ws>/raw.md`, `<ws>/meta.json`
- `meta.json`'s `low_confidence_pages` (if any)
- Next step: `/proofread <workspace>`

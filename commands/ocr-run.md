---
description: 对已清理的 source.pdf 跑 OCR（本地 MinerU / 云 MinerU / 百度）
argument-hint: <pdf-or-workspace>
allowed-tools: Bash(python3:*), Read
---

只跑 OCR 阶段，不触发后续 apply-review / docx / wechat。输入：

`$ARGUMENTS`

### 输入判定

- 输入是 `.pdf`：工作区默认为 `<pdf-dir>/<pdf-stem>.ocr/`，若 `source.pdf` 不存在就先复制一份
- 输入是目录：当成 workspace，要求 `<ws>/source.pdf` 必须已存在（否则先走 `/prep-scan`）

### 引擎选择

按 `OCR_ENGINE` 环境变量（默认 `mineru`）：

| 引擎 | 命令 |
|------|------|
| `mineru`（本地 CLI，默认） | `python3 skills/ocr-run/scripts/run_mineru.py --pdf <ws>/source.pdf --out <ws> --lang ch` |
| `mineru-cloud`（需 `MINERU_API_KEY`） | `python3 skills/ocr-run/scripts/mineru_client.py --pdf <ws>/source.pdf --out <ws> --layout horizontal --lang zh-hans --poll-interval 10 --timeout 1800` |
| `baidu`（需 `BAIDU_OCR_*`） | `python3 skills/ocr-run/scripts/baidu_client.py --pdf <ws>/source.pdf --out <ws>` |

本地失败（退出码非 0）且有 `MINERU_API_KEY` 时，可自动降级到 `mineru-cloud` 再试一次。再失败就停手汇报，不要擅自走 `extract_text_layer.py` 兜底——那是最后手段。

### 汇报

- 使用的引擎 + 耗时
- 产物：`<ws>/raw.md`、`<ws>/meta.json`
- `meta.json` 里的 `low_confidence_pages`（若有）
- 下一步提示：`/proofread <workspace>`

---
name: ocr-run
description: 使用场景：用户在 Mac 上运行 `/historical-ocr-review:ocr-run`、对清理过的历史论文 PDF 做文字识别、说出"跑 OCR""识别文字""PDF 转文字""MinerU""百度 OCR""把扫描件识别出来""出 Markdown""准备校对"等。这个 skill 支持**百度 OCR 和 MinerU 双引擎**，根据 `~/.env` 里的 OCR_ENGINE 自动选（mineru 优先精度、baidu 成本低用户已有 key）。它专门优化了历史文献的识别参数：繁体竖排、古籍异体字、民国新式标点、现代简体；并产出「原图 + OCR 文本逐页并排」的 preview.html 供用户在浏览器里直接改错字。凡是提到"OCR""识别""转文字""跑识别"都应主动触发，不要等用户说"ocr-run"三个字。
argument-hint: "<cleaned-pdf-path> [--engine=baidu|mineru] [--layout=horizontal|vertical] [--lang=zh-hans|zh-hant|mixed]"
allowed-tools: Bash, Read, Write, Edit
---

# OCR 执行 — 历史文献专用双引擎

## Task

把清理过的 PDF 交给 OCR API，拿回 Markdown + 附件 + 对照预览 HTML。

**为什么支持两个引擎**：
- **MinerU**（上海 AI Lab）：对繁体、竖排、古籍版式、公式、表格识别更强，默认推荐。
- **百度 OCR**：稳定、额度大、响应快，适合大批量现代简体论文。

`~/.env` 里的 `OCR_ENGINE=mineru` 或 `OCR_ENGINE=baidu` 决定默认引擎。命令行 `--engine=xxx` 可临时覆盖。

输出结构：

```
<pdf-basename>.ocr/
├── raw.md              OCR 原始 Markdown
├── assets/             图片附件（古籍插图、论文图表）
├── preview.html        原图左 / OCR 右并排，可点击编辑右栏；点「下载修改后的 Markdown」会保存 corrected.md，需手动替换 raw.md（浏览器不能直接写磁盘）
└── meta.json           引擎、耗时、页数、low_confidence_pages
```

## Process

### Step 0：决定走哪条路径（默认本地 `mineru` CLI）

Agent **默认走 `run_mineru.py`**（本地 `mineru[pipeline]`），不再按 `OCR_ENGINE`
环境变量选云 API：

```bash
which mineru   # 检查 mineru CLI 是否在 PATH
ls -d ~/mineru/"$STEM".pdf-* 2>/dev/null   # 检查 MinerU Desktop 是否有历史产出
```

判断：

| 条件 | 路径 |
|---|---|
| `mineru` 在 PATH 且 `~/mineru/` 没对应产出 | **路径 A**：`run_mineru.py` 本地跑 |
| `~/mineru/` 已有 Desktop 产出 | 路径 A'：`import_mineru_output.py --job-dir` 直接导入 |
| `mineru` 没装 | 路径 B：提示 `pip install 'mineru[pipeline]'` 或跑 `/historical-ocr-review:setup` |
| 离线 / 环境装不上 / PDF 有可用文字层且用户急 | 路径 D：`extract_text_layer.py` 兜底（质量会打折） |

具体四条路径的决策语义与失败兜底全文见
`agents/ocr-pipeline-operator.md`——ocr-run skill 只负责**调脚本**，不重复
决策逻辑。

旧的 `OCR_ENGINE=baidu|mineru` 环境变量仍然被 `mineru_client.py` /
`baidu_client.py` 读，但新工作流不走这两个——它们是兼容分支。

### Step 1（已合并到 Step 0）

### Step 2：建输出目录

```bash
PDF="<cleaned-pdf-path>"
DIR=$(dirname "$PDF")
BASE=$(basename "$PDF" .pdf)
OUT="$DIR/$BASE.ocr"
mkdir -p "$OUT/assets"
```

### Step 3：判断文献 hint（传给引擎）

从 `<pdf-basename>.prep/pages/page_001.png` 采样第一页做**快速视觉判断**（Agent 直接看图，不调脚本）：

**本地 MinerU CLI（默认）——无 `--layout` 参数，`--lang` 用三字代码**：

| 观察 | `--lang` |
|------|---------|
| 横排 + 简体 / 繁简混杂（含民国排印本） | `ch` |
| 横排 + 繁体 + 新式标点 | `chinese_cht` |
| 竖排 + 繁体 + 版心鱼尾（古籍） | 本地 CLI 竖排效果欠佳，改走云端或百度分支 |
| 英文 / 日文 / 韩文为主 | `en` / `japan` / `korean` |

**云端 MinerU / 百度 OCR（兼容分支）——支持 `--layout`，`--lang` 用 BCP-47 码**：

| 观察 | `--layout` | `--lang` |
|------|-----------|---------|
| 竖排 + 繁体 + 版心鱼尾 | `vertical` | `zh-hant` |
| 横排 + 繁体 + 新式标点 | `horizontal` | `zh-hant` |
| 横排 + 简体 | `horizontal` | `zh-hans` |
| 繁简混杂（民国排印本、早期译著） | `horizontal` | `zh-hans`（简体为主） |

> 语言码**不要跨引擎复用**：把 `zh-hans` 传给本地 MinerU CLI 会失败；把 `ch` 传给百度也会失败。用户未指定时，Agent 自行判断；视觉上无法定性（繁简各半、页眉水印大）时，问一句："这份文献是繁体竖排、繁体横排还是简体？"

### Step 4：调 OCR（默认本地 `mineru`）

#### 默认 — 本地 `mineru[pipeline]`

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/ocr-run/scripts/run_mineru.py" \
    --pdf "$PDF" --out "$OUT" --lang "$MINERU_LANG"
```

`$MINERU_LANG` 按内容类型选：
- 中文简体 / 繁简混 → `ch`
- 繁体古籍 → `chinese_cht`
- 英文 → `en`
- 日文 / 韩文 → `japan` / `korean`

脚本内部：
1. 调 `mineru -p $PDF -o <tmp> -b pipeline -m auto -l $MINERU_LANG`
2. MinerU 本地跑 DocLayout-YOLO + PaddleOCR 识别（不上云、不依赖 API key）
3. 链式跑 `import_mineru_output.py --job-dir <tmp>/<stem>` 生成 `raw.md` +
   `meta.json` + `assets/` + `_import_provenance.json`

首次跑会下载 ~2–3 GB 模型到 `~/.cache/huggingface/hub/`（预热过后复跑秒级
启动）。27 页论文约 90 秒完成；50 页古籍约 2 分钟。

#### 兼容分支（已弃用，离线或特殊环境才走）

旧路径保留在仓库里，不是默认工作流：

```bash
# 只在 mineru[pipeline] 装不上时兜底
python3 "${CLAUDE_PLUGIN_ROOT}/skills/ocr-run/scripts/mineru_client.py" \
    --pdf "$PDF" --out "$OUT" --layout "$LAYOUT" --lang "$LANG"

# 用户已有百度 OCR key 想复用
python3 "${CLAUDE_PLUGIN_ROOT}/skills/ocr-run/scripts/baidu_client.py" \
    --pdf "$PDF" --out "$OUT" --layout "$LAYOUT" --lang "$LANG"
```

这两条路径的 meta.json 字段和默认路径保持一致
（`engine / pages / low_confidence_pages / ...`），下游 proofread / preview /
to-docx 不需要分支。细节：

- `mineru_client.py`：走 MinerU 云 API，通过 catbox.moe 中转上传。catbox 偶
  发静默失败，已加 3 次重试。没 API key 时不要走。
- `baidu_client.py`：每页调百度「通用文字识别（高精度版）」，段落合并依赖
  行距启发式，若 `raw.md` 出现「每行一段」→ 改走默认本地路径。

### Step 5：产出对照预览 HTML

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/ocr-run/scripts/make_preview.py" \
    --markdown "$OUT/raw.md" \
    --pages-dir "$DIR/$BASE.prep/pages" \
    --out "$OUT/preview.html"
```

HTML 是**本地文件，不联网**。两种使用模式：

- **Agent 自主模式（默认）**：`preview.html` 仅作为 diff-review 的视觉参照，Agent 不依赖 human-in-browser 编辑。直接进入下一步 proofread。
- **人工协作模式**（用户显式要求先自行校对时）：用户在浏览器里改右栏（`contenteditable`），点「下载修改后的 Markdown」导出 `corrected.md` 到下载目录，再由 Agent 用 Step 8 的 `apply_corrections.py` 回写。

### Step 6：写 meta.json

两个 client 自动写成统一 schema，proofread skill 直接消费：

```json
{
  "engine": "mineru",
  "layout": "vertical",
  "lang": "zh-hant",
  "pages": 47,
  "avg_confidence": null,
  "low_confidence_pages": [3, 12, 38],
  "duration_seconds": 215.0
}
```

字段约定：

- `pages`：实际页数。MinerU 来自 `extract_progress.total_pages`；百度来自分页数组长度。
- `avg_confidence`：**目前固定为 `null`**——MinerU API 不暴露 per-page confidence，百度 `accurate_basic` 也不返回 probability。写 null 比编数字诚实。
- `low_confidence_pages`：**启发式**产生的重点盯防页列表。百度：OCR 失败页 + 文字量 < 中位数 50% 的页；MinerU：若 raw.md 含 `<!-- page N -->` marker 则按块长度判，否则空列表。
- 所有字段都必须存在（即便为空）。proofread skill 按 `meta.get(field, default)` 读，老版本 meta 也兼容。

### Step 7：报告

**Agent 自主模式**（默认，端到端跑完 pipeline）：

```
OCR 完成（引擎：$ENGINE，$PAGES 页，耗时 $SECONDS 秒）

- 原始 Markdown：$OUT/raw.md
- 对照预览：   $OUT/preview.html（视觉参照，不需手工编辑）
- 启发式低置信度页：第 3、12、38 页（已标记供 proofread 重点盯防）

下一步（自动进行）：proofread → 应用清单 → diff-review → to-docx + mp-format
```

**人工协作模式**（仅用户显式要求）：

```
OCR 完成。人工协作流程：
1. 打开 preview.html 核验 / 手改
2. 改完点「下载修改后的 Markdown」，corrected.md 存到下载目录
3. 回到 agent 说「应用修改」，Agent 调 apply_corrections.py 回写
4. 进入 proofread
```

### Step 8（仅人工协作模式）：应用浏览器里的修改

触发词：「改完了」「应用修改」「我改好了」「apply」。触发后 Agent 执行：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/ocr-run/scripts/apply_corrections.py" \
    --ocr-dir "$OUT"
```

脚本行为：

1. 在 `~/Downloads/` 中找最新的 `corrected*.md`
2. 把当前 `$OUT/raw.md` 备份为 `$OUT/raw.md.bak`（已存在则加时间戳）
3. 将 `corrected.md` 移动到 `$OUT/raw.md`
4. 打印替换后字节数 + 备份位置

若用户显式指定 corrected 路径，Agent 传 `--corrected <path>` 覆盖自动查找。

防御规则：空文件拒绝替换（退码 5）；下载目录找不到提示用户确认路径（退码 3）。两种情况下不硬闯，询问用户。

完成后汇报：

```
已应用修改：
- raw.md 已更新（$NEW_BYTES 字节）
- 原文备份在 $OUT/raw.md.bak

下一步：/historical-ocr-review:proofread $OUT/raw.md
```

用 `open` 命令拉起 preview.html：

```bash
open "$OUT/preview.html"
```

## 错误处理

| 错误 | 处理 |
|------|------|
| MinerU `401` | key 失效，让用户重跑 `/historical-ocr-review:setup` |
| MinerU `429` | 免费额度用完，建议用户 `--engine=baidu` 换百度 |
| 百度 `error_code: 14` | access_token 过期，删 `~/.cache/baidu_ocr_token.json` 重跑 |
| 百度 `error_code: 17` | 额度用完（百度按次数计费，用户查控制台余额） |
| 超时 > 15 分钟 | PDF 过大，建议用户拆成单章节分别跑 |
| raw.md < 500 字节 | 识别失败，查 PDF 是不是空白或加密 |

## 判断规则

- **raw.md 里大量 `?` 或 `□`** → 字形识别失败。步骤：先确认 prep-scan 有没有误擦正文；再用 `--aggressive` 重跑 prep-scan；还不行换引擎。
- **竖排古籍 OCR 出来是横排乱序** → MinerU 没识别出竖排，手动加 `--layout=vertical` 重跑。
- **繁体被识别成简体** → 加 `--lang=zh-hant` 重跑；MinerU 默认会自动识别但偶尔错。

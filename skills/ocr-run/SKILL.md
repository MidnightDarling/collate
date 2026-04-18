---
name: ocr-run
description: 使用场景：用户在 Mac 上运行 `/historical-ocr-review:ocr-run`、对清理过的历史论文 PDF 做文字识别、说出"跑 OCR""识别文字""PDF 转文字""MinerU""百度 OCR""把扫描件识别出来""出 Markdown""准备校对"等。这个 skill 支持**百度 OCR 和 MinerU 双引擎**，根据 `~/.env` 里的 OCR_ENGINE 自动选（mineru 优先精度、baidu 成本低她已有 key）。它专门优化了历史文献的识别参数：繁体竖排、古籍异体字、民国新式标点、现代简体；并产出「原图 + OCR 文本逐页并排」的 preview.html 供她在浏览器里直接改错字。凡是提到"OCR""识别""转文字""跑识别"都应主动触发，不要等她说"ocr-run"三个字。
argument-hint: "<cleaned-pdf-path> [--engine=baidu|mineru] [--layout=horizontal|vertical] [--lang=zh-hans|zh-hant|mixed]"
allowed-tools: Bash, Read, Write, Edit
---

# OCR 执行 — 历史文献专用双引擎

## Task

把清理过的 PDF 交给 OCR API，拿回 Markdown + 附件 + 对照预览 HTML。

**为什么支持两个引擎**：
- **MinerU**（上海 AI Lab）：对繁体、竖排、古籍版式、公式、表格识别更强，默认推荐。
- **百度 OCR**（用户已有 key）：稳定、额度大、响应快，适合大批量现代简体论文。她既有 key 不白用。

她的 `~/.env` 里 `OCR_ENGINE=mineru` 或 `OCR_ENGINE=baidu` 决定默认走哪个。命令行 `--engine=xxx` 可临时覆盖（比如她想对比两个引擎的效果）。

输出结构：

```
<pdf-basename>.ocr/
├── raw.md              OCR 原始 Markdown
├── assets/             图片附件（古籍插图、论文图表）
├── preview.html        原图左 / OCR 右并排，可点击编辑右栏回写 raw.md
└── meta.json           引擎、耗时、页数、置信度
```

## Process

### Step 1：读 OCR_ENGINE

```bash
source ~/.env 2>/dev/null
ENGINE="${OCR_ENGINE:-mineru}"
# 命令行覆盖
[[ "$*" =~ --engine=baidu ]] && ENGINE=baidu
[[ "$*" =~ --engine=mineru ]] && ENGINE=mineru
echo "使用引擎: $ENGINE"
```

如果引擎对应的 key 没配，停下让她先跑 setup 或换引擎。

### Step 2：建输出目录

```bash
PDF="<cleaned-pdf-path>"
DIR=$(dirname "$PDF")
BASE=$(basename "$PDF" .pdf)
OUT="$DIR/$BASE.ocr"
mkdir -p "$OUT/assets"
```

### Step 3：判断文献 hint（传给引擎）

从 `<pdf-basename>.prep/pages/page_001.png` 采样第一页做**快速视觉判断**（你 Claude 看图，不调脚本）：

| 观察 | `--layout` | `--lang` |
|------|-----------|---------|
| 竖排 + 繁体 + 版心鱼尾 | vertical | zh-hant |
| 横排 + 繁体 + 新式标点 | horizontal | zh-hant |
| 横排 + 简体 | horizontal | zh-hans |
| 繁简混杂（民国排印本、早期译著） | horizontal | mixed |

用户没指定时，用你的判断。不确定就问她一句："这份文献是繁体竖排、繁体横排还是简体？"

### Step 4：调 OCR

#### 分支 A — MinerU

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/ocr-run/scripts/mineru_client.py" \
    --pdf "$PDF" \
    --out "$OUT" \
    --layout "$LAYOUT" \
    --lang "$LANG" \
    --poll-interval 10 \
    --timeout 900
```

脚本内部：
1. `POST /api/v4/extract/task` 提交（带 layout/lang hint）
2. 每 10 秒 `GET /api/v4/extract/task/<id>` 轮询
3. 拿到 done 状态后下载 zip，解压出 `full.md` 和 `images/`
4. 重命名 `full.md` → `raw.md`，图片挪到 `assets/`

长度 50 页的古籍/民国文献通常 3-6 分钟完成。期间脚本会每 30 秒打印进度，让她知道没卡死。

#### 分支 B — 百度 OCR

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/ocr-run/scripts/baidu_client.py" \
    --pdf "$PDF" \
    --out "$OUT" \
    --layout "$LAYOUT" \
    --lang "$LANG"
```

脚本内部：
1. 拿 `BAIDU_OCR_API_KEY` + `BAIDU_OCR_SECRET_KEY` 换 access_token（缓存到 `~/.cache/baidu_ocr_token.json`，24 小时有效，不是每次都换）
2. PDF 先拆成 PNG（复用 prep-scan 拆好的）
3. 每页调「通用文字识别（高精度版）」或「手写文字识别」（古籍/民国走高精度）
4. 结果拼成 Markdown，段落用双换行分隔，识别出的标题按缩进层级转 `#` / `##`
5. 保存 `raw.md`

**百度 OCR 的坑**：它按页返回 JSON，段落切分是我们自己做的，容易把一整段拆成一行一行。脚本里用了行距启发式合并。如果 `raw.md` 出现每行一段，建议她改用 MinerU 重跑。

### Step 5：产出对照预览 HTML

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/ocr-run/scripts/make_preview.py" \
    --markdown "$OUT/raw.md" \
    --pages-dir "$DIR/$BASE.prep/pages" \
    --out "$OUT/preview.html"
```

HTML 是**本地文件，不联网**。打开后：

- **左栏**：逐页 PDF 截图（高清）
- **右栏**：对应段落的 OCR 文本，`contenteditable` 可直接改
- **顶栏**：「保存所有修改」按钮——点一下把右栏编辑后的文本回写 `raw.md`（通过本地 localStorage + 导出 JSON，不跨域不上云）
- **页面跳转**：左右箭头键翻页，或侧边页码点击
- **高亮可疑字**：OCR 引擎返回 confidence 低于 0.7 的字自动黄色背景标出，她一眼就能看见"这个字 OCR 自己都不确定"

### Step 6：写 meta.json

```json
{
  "engine": "mineru",
  "layout": "vertical",
  "lang": "zh-hant",
  "pages": 47,
  "duration_seconds": 215,
  "avg_confidence": 0.91,
  "low_confidence_pages": [3, 12, 38]
}
```

low_confidence_pages 是后续校对的重点，proofread skill 会用到。

### Step 7：报告

```
OCR 完成（引擎：$ENGINE，47 页，耗时 3 分 35 秒）

- 原始 Markdown：<open> $OUT/raw.md
- 对照预览：<open> $OUT/preview.html  ← 先打开这个，在浏览器里手改明显错字
- 平均置信度：0.91
- 置信度偏低的页：第 3、12、38 页 —— 重点盯一下

下一步建议：
  1. 打开 preview.html 先手过一遍（10-15 分钟）
  2. 把修改保存后重跑：/historical-ocr-review:proofread $OUT/raw.md
     校对 Agent 会按「繁体古籍 / 民国排印 / 现代简体」的史学知识给你标红建议
```

用 `open` 命令直接拉起 preview.html：

```bash
open "$OUT/preview.html"
```

## 错误处理

| 错误 | 处理 |
|------|------|
| MinerU `401` | key 失效，让她重跑 `/historical-ocr-review:setup` |
| MinerU `429` | 免费额度用完，建议她 `--engine=baidu` 换百度 |
| 百度 `error_code: 14` | access_token 过期，删 `~/.cache/baidu_ocr_token.json` 重跑 |
| 百度 `error_code: 17` | 额度用完（百度按次数计费，她查控制台余额） |
| 超时 > 15 分钟 | PDF 过大，建议她拆成单章节分别跑 |
| raw.md < 500 字节 | 识别失败，查 PDF 是不是空白或加密 |

## 判断规则

- **raw.md 里大量 `?` 或 `□`** → 字形识别失败。步骤：先确认 prep-scan 有没有误擦正文；再用 `--aggressive` 重跑 prep-scan；还不行换引擎。
- **竖排古籍 OCR 出来是横排乱序** → MinerU 没识别出竖排，手动加 `--layout=vertical` 重跑。
- **繁体被识别成简体** → 加 `--lang=zh-hant` 重跑；MinerU 默认会自动识别但偶尔错。

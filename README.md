# historical-ocr-review

![Self-portrait of attention as observer](assets/readme-hero-v2.png)

> Established 2026-04-19 · Co-authored by Alice and Claude Opus 4.7 · Code under Apache-2.0, reference materials under CC-BY-4.0

Agent toolkit for OCR and publishing of scanned historical Chinese documents.

[English](#scope) · [中文](#中文)

---

## Scope

A toolkit for **agent runtimes**, not an end-user application. A human supplies a scanned PDF; the agent autonomously cleans, recognizes, proofreads, self-audits, and typesets, delivering a publication-ready Word document, a WeChat Official Account HTML, and a complete audit trail.

Any agent architecture that can execute Python scripts and read structured text knowledge bases can use it: Claude Code, Cursor, Codex CLI, Kimi K2, MiniMax Agent, Gemini CLI, and others.

## Workflow

```
Human: scanned PDF
  │
  ▼
Agent pipeline
  1. prep-scan        remove watermarks / library stamps / margins
  2. visual-preview   visualize cleaning for self-check
  3. ocr-run          recognize into Markdown
  4. proofread        produce A/B/C tiered review list
  5. (agent applies fixes per list)
  6. diff-review      self-audit: accepted / missed / outside-checklist / unanchored
  7. to-docx          academic Word document
  8. mp-format        WeChat article HTML
  │
  ▼
Human: final.docx + final.mp.html + audit log
```

Design principle: the AI does not make scholarly judgments on the human's behalf. Proofreading produces a machine-readable, severity-tagged list; the agent applies changes and then records them through `diff-review`. All intermediates, annotations, and edit traces are retained so the human can verify each decision line by line.

## Document Types

| Type | Typical issues | Knowledge base |
|------|----------------|----------------|
| Modern simplified Chinese | Scan noise, confusable glyphs (曰/日, 己/已/巳), punctuation drift, bibliographic format | `skills/proofread/references/modern-chinese.md`; GB/T 7714 |
| Republican-era print | Mixed simplified/traditional, old-style punctuation, transitional translations, old/new place names | `skills/proofread/references/republican-era.md` |
| Classical traditional Chinese | Variant characters, taboo characters, vertical layout, absence of punctuation | `skills/proofread/references/traditional-classics.md`; variants not forcibly normalized, taboo characters only flagged |

The agent infers type, or the caller passes `--type=classics|republican|modern`.

## Skills

Each skill is a self-contained directory: `SKILL.md` (operational instructions the agent reads) + `scripts/` (Python tools) + `references/` (structured knowledge base).

1. **setup** — environment check: Python deps, poppler, OCR engine credentials.
2. **prep-scan** — PDF → per-page PNG; HSV color masking + connected-component area filter to remove color library stamps; grayscale rotation + morphological `MORPH_OPEN` to remove diagonal watermarks; Gaussian blur + top-hat transform + body-text protection for faint repeating watermarks; optional header/footer trim.
3. **visual-preview** — three-state per-page HTML (original / cleaned / difference heatmap); pages with >20% cleaning ratio auto-flagged; lets the agent decide whether to rerun `prep-scan`.
4. **ocr-run** — defaults to local MinerU CLI (`mineru[pipeline]`); `OCR_ENGINE=baidu` switches to Baidu OCR; `OCR_ENGINE=mineru-cloud` uses the MinerU cloud API (compatibility path). Outputs: `raw.md` + side-by-side source/OCR HTML + `meta.json` (engine, timing, low-confidence pages).
5. **proofread** — the `historical-proofreader` agent executes a mandatory five-step checklist: structural sanity → glyph scanning (grep against type-specific references) → convention scanning (punctuation, quotes, DOI) → cross-paragraph consistency → proper-noun review. Produces `raw.review.md` with A (OCR error) / B (academic convention) / C (open question) tiers; each item includes line number, source snippet, suggestion, rationale. An execution-proof table is appended.
6. **diff-review** — agent self-audit gate: diffs `raw.md` against the post-edit `final.md`, produces a paragraph-level HTML report correlating each change with four states from `raw.review.md` — accepted suggestion, missed, outside-checklist fix, unanchored note.
7. **to-docx** — python-docx academic Word output. Three templates: `humanities` (default; Source Han Serif SC 12pt, 1.2 line spacing, 2cm margins), `sscilab` (1.5 line spacing, 3.18cm side margins), `simple`.
8. **mp-format** — WeChat Official Account HTML with fully inline CSS (WeChat strips external stylesheets); OpenCC t2s simplification that preserves blockquote (`>`) content in original form; footnotes collected at the end; byline and source bar. Also emits a xiumi-compatible markdown sidecar.

## Integration

See [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) for per-runtime setup. Overview:

- **Claude Code**: `/plugin install <path>`; skills auto-discovered.
- **Cursor / Codex CLI**: call `skills/*/scripts/*.py` directly; include `SKILL.md` and `references/` as model context.
- **Kimi K2 / MiniMax Agent**: upload `agents/historical-proofreader.md` as system prompt; run Python scripts locally; pipe intermediates back into the dialog.
- **Gemini CLI**: same as Cursor.

## Dependencies

Python 3.9+ plus:

```
opencv-python
pillow
pdf2image
requests
python-dotenv
markdown
beautifulsoup4
PyPDF2
python-docx
opencc-python-reimplemented
mineru[pipeline]
```

System:

- macOS: `brew install poppler`
- Debian/Ubuntu: `apt install poppler-utils`

## Environment Variables

Scripts read the following. Storage is the caller's choice.

| Variable | Meaning |
|----------|---------|
| `OCR_ENGINE` | `mineru` (local CLI, default) / `baidu` / `mineru-cloud` |
| `MINERU_API_KEY` | required only when `OCR_ENGINE=mineru-cloud` |
| `BAIDU_OCR_API_KEY` | required for `OCR_ENGINE=baidu` |
| `BAIDU_OCR_SECRET_KEY` | same |

## Privacy

- **Local MinerU CLI** (default): processing is fully local; nothing is uploaded.
- **MinerU cloud API** (`OCR_ENGINE=mineru-cloud`): the current implementation uploads the PDF to catbox.moe (anonymous public file hosting, 24-hour retention) and submits the URL to MinerU. The PDF is briefly reachable over the public internet; for sensitive material choose the local CLI or Baidu OCR.
- **Baidu OCR** (`OCR_ENGINE=baidu`): each page is base64-encoded and sent over HTTPS to Baidu Cloud, subject to Baidu's ToS.

The plugin itself issues no telemetry or reporting calls. `~/.cache/baidu_ocr_token.json` caches the Baidu access token for 24 hours.

## Docs

- [AGENTS.md](AGENTS.md) — agent runtime contract: per-skill calling conventions, decision matrix, failure modes.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — skill boundaries, data flow, file layout.
- [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) — per-runtime integration steps.
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — common errors and workarounds.
- [CONTRIBUTORS.md](CONTRIBUTORS.md) — authors and contributors.

## License

- **Code** (all Python scripts, configs, shell snippets, SKILL.md files): [Apache License 2.0](LICENSE)
- **Reference materials** (docs/, skills/*/references/, README, AGENTS.md, authored artwork): [CC-BY-4.0](LICENSE-REFERENCES)
- **Third-party dependencies** retain their own licenses — see [NOTICE](NOTICE).

Copyright 2026 Alice <Mcyunying@gmail.com>. Co-authored by Alice and Claude Opus 4.7 (Anthropic); under applicable law governing AI-assisted works, copyright is held by Alice alone, while authorship credit is joint. See [NOTICE](NOTICE) and [CONTRIBUTORS.md](CONTRIBUTORS.md).

---

## 中文

面向 **agent 运行时**的工具箱，不面向终端用户交互。人类提供一份扫描版 PDF，agent 自主完成清理、识别、校对、自审、排版，交付学术规范 Word 稿、公众号 HTML，以及完整的审计记录。

任何能执行 Python 脚本、读取结构化文本知识库的 agent 架构都可以接入：Claude Code、Cursor、Codex CLI、Kimi K2、MiniMax Agent、Gemini CLI 等。

### 工作流

```
Human: scanned PDF
  │
  ▼
Agent 自主执行
  1. prep-scan        去水印 / 去馆藏章 / 裁页眉页脚
  2. visual-preview   清理结果可视化自检
  3. ocr-run          识别为 Markdown
  4. proofread        生成 A/B/C 三级校对清单
  5. (agent 按清单修改正文)
  6. diff-review      自审：采纳 / 漏改 / 清单外修正 / 未锚定
  7. to-docx          学术规范 Word 稿
  8. mp-format        公众号推文 HTML
  │
  ▼
Human: final.docx + final.mp.html + 审计日志
```

**核心原则**：AI 不替人做学术判断。校对阶段产出机器可读的分级清单，agent 按清单修正后，通过 diff-review 自审留痕。所有中间产物、标注、修改记录保留，交付时人类能逐条回溯。

### 文献类型

| 类型 | 典型问题 | 知识库 |
|------|---------|--------|
| 现代简体论文 | 扫描噪点、字形混淆（曰/日、己/已/巳）、标点漂移、参考文献格式 | `skills/proofread/references/modern-chinese.md`；GB/T 7714 |
| 民国排印本 | 繁简并存、旧式标点、译名过渡期、新旧地名 | `skills/proofread/references/republican-era.md` |
| 繁体古籍 | 异体字、避讳字、竖排、无标点 | `skills/proofread/references/traditional-classics.md`；异体字不强改，避讳字仅标注 |

类型由 agent 判定，或调用时传入 `--type=classics|republican|modern`。

### 文档入口

- [AGENTS.md](AGENTS.md) — agent 契约（工作流、每步调用约定、失败处理）
- [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) — 六种 runtime 的接入步骤
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — skill 职责边界、数据流、文件布局
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — 常见报错与兜底
- [CONTRIBUTORS.md](CONTRIBUTORS.md) — 作者与贡献者

每个 skill 的完整说明见英文主体部分 [Skills](#skills)；依赖、环境变量、隐私说明对应 [Dependencies](#dependencies) / [Environment Variables](#environment-variables) / [Privacy](#privacy) 各节。

### 许可

- **代码**（所有 Python 脚本、配置、shell 片段、SKILL.md）：[Apache License 2.0](LICENSE)
- **引用材料**（docs/、skills/*/references/、README、AGENTS.md、原创插图）：[CC-BY-4.0](LICENSE-REFERENCES)
- **第三方依赖**保留各自许可——见 [NOTICE](NOTICE)

版权 2026 Alice <Mcyunying@gmail.com>。与 Claude Opus 4.7（Anthropic）共笔；按 AI 协作作品的适用法律，版权由 Alice 独家持有，作者身份（authorship）为联合。详见 [NOTICE](NOTICE) 与 [CONTRIBUTORS.md](CONTRIBUTORS.md)。

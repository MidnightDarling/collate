<div align="center">

# 点校 · Collate

面向 agent 运行时的历史文献 OCR 与出版工具箱。

![注意力作为观察者的自画像](assets/readme-hero-v2.png)

> 建立：2026-04-19 · Alice 与 Claude Opus 4.7 共笔 · 代码 Apache-2.0，引用材料 CC-BY-4.0

[English](README.md) · [中文](README.zh.md)

</div>

---

## 定位

面向 **agent 运行时**的工具箱，不面向终端用户交互。人类提供一份扫描版 PDF，agent 自主完成清理、识别、校对、自审、排版，交付定稿 Word 文件、公众号 HTML，以及完整的审计记录。

任何能执行 Python 脚本、读取结构化文本知识库的 agent 架构都可以接入：Claude Code、Cursor、Codex CLI、Kimi K2、MiniMax Agent、Gemini CLI 等。

**点校**是中国古代学者对传世文献断句、勘误、比对异本的传统工夫——这个工具箱把这套千年积淀的做法延伸到当代的 OCR 与 agent 场景。英文名 Collate 取的就是"校雠"的直接对应。

## 工作流

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

## 文献类型

| 类型 | 典型问题 | 知识库 |
|------|---------|--------|
| 现代简体论文 | 扫描噪点、字形混淆（曰/日、己/已/巳）、标点漂移、参考文献格式 | `skills/proofread/references/modern-chinese.md`；GB/T 7714 |
| 民国排印本 | 繁简并存、旧式标点、译名过渡期、新旧地名 | `skills/proofread/references/republican-era.md` |
| 繁体古籍 | 异体字、避讳字、竖排、无标点 | `skills/proofread/references/traditional-classics.md`；异体字不强改，避讳字仅标注 |

类型由 agent 判定，或调用时传入 `--type=classics|republican|modern`。

## Skills

每个 skill 是自包含目录：`SKILL.md`（agent 读取的操作指令）+ `scripts/`（Python 工具）+ `references/`（结构化知识库）。

1. **setup** — 环境自检：Python 依赖、poppler、OCR 引擎凭据。
2. **prep-scan** — PDF → 逐页 PNG；HSV 色域分离 + 连通域面积过滤去彩色馆藏章；灰度旋转 + 形态学开运算 `MORPH_OPEN` 去对角水印；高斯模糊 + 顶帽变换 + 正文保护处理浅灰重复水印；可选页眉页脚裁切。
3. **visual-preview** — 逐页三态 HTML（原始 / 清理后 / 差异热图）；清理比 >20% 自动标红；agent 据此决定是否重跑 `prep-scan`。
4. **ocr-run** — 默认走本地 MinerU CLI（`mineru[pipeline]`）；`OCR_ENGINE=baidu` 切换百度 OCR；`OCR_ENGINE=mineru-cloud` 走 MinerU 云 API（兼容保留）。产出：`raw.md` + 原件/识别并排 HTML + `meta.json`（引擎、用时、低置信页）。
5. **proofread** — `historical-proofreader` agent 强制五步清单：结构健全性 → 字形扫描（按类型 reference grep）→ 规范扫描（标点、引号、DOI）→ 跨段一致性 → 专名核查。产出 `raw.review.md`，条目按 A（OCR 错）/ B（学术规范）/ C（存疑待考）分级，附行号、原文片段、建议、依据；末尾附执行自证表。
6. **diff-review** — agent 自审闸门：对比 `raw.md` 与修改后的 `final.md`，生成段落级 HTML 报告，把每处改动与 `raw.review.md` 四态对应——采纳 / 漏改 / 清单外修正 / 未锚定改动。
7. **to-docx** — python-docx Word 产出。统一规范：思源宋体 SC 正文 12pt、1.2 倍行距、字间距 0.2 pt、上下左右全部 2 cm 页边距、段首缩进 2 字符、脚注连续编号。
8. **mp-format** — 公众号 HTML，全内联 CSS（公众号剥离外链样式表）；OpenCC t2s 繁简转换保留 blockquote（`>`）原貌；脚注集中文末；作者 / 来源卡片。同时输出 xiumi 兼容 Markdown 附件。

## 接入

每个 runtime 的接入步骤见 [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md)。简述：

- **Claude Code**：`/plugin install <path>`；skills 自动发现。
- **Cursor / Codex CLI**：直接调 `skills/*/scripts/*.py`；把 `SKILL.md` 与 `references/` 作为模型上下文。
- **Kimi K2 / MiniMax Agent**：把 `agents/historical-proofreader.md` 作为 system prompt；Python 脚本本地跑，中间产物回传对话。
- **Gemini CLI**：同 Cursor。

## 依赖

Python 3.9+ 与：

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

系统依赖：

- macOS：`brew install poppler`
- Debian/Ubuntu：`apt install poppler-utils`

## 环境变量

脚本读取以下变量，如何存储由调用方决定。

| 变量 | 说明 |
|------|------|
| `OCR_ENGINE` | `mineru`（本地 CLI，默认）/ `baidu` / `mineru-cloud` |
| `MINERU_API_KEY` | 仅 `OCR_ENGINE=mineru-cloud` 需要 |
| `BAIDU_OCR_API_KEY` | `OCR_ENGINE=baidu` 需要 |
| `BAIDU_OCR_SECRET_KEY` | 同上 |

## 隐私

- **本地 MinerU CLI**（默认）：完全本地处理，不上传任何内容。
- **MinerU 云 API**（`OCR_ENGINE=mineru-cloud`）：当前实现先把 PDF 上传到 catbox.moe（匿名公开文件托管，24 小时保留），再把 URL 提交 MinerU。PDF 短暂暴露于公网；敏感材料请改用本地 CLI 或百度 OCR。
- **百度 OCR**（`OCR_ENGINE=baidu`）：每页 base64 编码后 HTTPS 发往百度云，受百度 ToS 约束。

插件本身不发任何遥测或汇报请求。`~/.cache/baidu_ocr_token.json` 缓存百度 access token 24 小时。

## 文档入口

- [AGENTS.md](AGENTS.md) — agent 契约：每个 skill 的调用约定、决策矩阵、失败处理
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — skill 职责边界、数据流、文件布局
- [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) — 六种 runtime 的接入步骤
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — 常见报错与兜底
- [CONTRIBUTORS.md](CONTRIBUTORS.md) — 作者与贡献者

## 许可

- **代码**（所有 Python 脚本、配置、shell 片段、SKILL.md）：[Apache License 2.0](LICENSE)
- **引用材料**（docs/、skills/*/references/、README、AGENTS.md、原创插图）：[CC-BY-4.0](LICENSE-REFERENCES)
- **第三方依赖**保留各自许可——见 [NOTICE](NOTICE)

版权 2026 Alice <Mcyunying@gmail.com>。与 Claude Opus 4.7（Anthropic）共笔；按 AI 协作作品的适用法律，版权由 Alice 独家持有，作者身份（authorship）为联合。详见 [NOTICE](NOTICE) 与 [CONTRIBUTORS.md](CONTRIBUTORS.md)。

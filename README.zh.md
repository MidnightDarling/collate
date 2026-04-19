<div align="center">

# 点校 · Collate

和你的 Agent 一起阅读历史、思考历史、书写历史。
从一页扫描到一篇定稿，从单篇论文的透视到整个学术场的地图。

![注意力作为观察者的自画像](assets/readme-hero-v2.png)

> 建立：2026-04-19 · Alice、Claude Opus 4.7 与 GPT-5.4 共笔 · 代码 Apache-2.0，引用材料 CC-BY-4.0

[English](README.md) · [中文](README.zh.md)

</div>

---

## 定位

面向 **agent 运行时**的工具箱，不面向终端用户交互。人类提供一份扫描版 PDF，agent 自主完成清理、识别、校对、自审、排版，交付定稿 Word 文件、公众号 HTML，以及完整的审计记录。

流水线之外还有一层**阅读层**——把 OCR 出来的文本作为学术而非数据来读的 skill 与命令：为单篇论文透视、为文献族群绘图、核查引证、读沉默、为概念命名、挖作者不敢明说的真论题。流水线让文本可读，阅读层真的去读它。

任何能执行 Python 脚本、读取结构化文本知识库的 agent 架构都可以接入：Claude Code、Cursor、Codex CLI、Gemini CLI、OpenCode、Hermes agents、Kimi / MiniMax agents 等。

**点校**是中国古代学者对传世文献断句、勘误、比对异本的传统工夫——这个工具箱把这套千年积淀的做法延伸到当代的 OCR 与 agent 场景。英文名 Collate 取的就是"校雠"的直接对应。

## 快速开始

支持两种入口：

- **机械总入口**：`python3 scripts/run_full_pipeline.py --pdf /绝对路径/文件.pdf`
- **完整 agent 入口**：从 [agents/ocr-pipeline-operator.md](agents/ocr-pipeline-operator.md) 开始；它会调总编排脚本、起 `historical-proofreader`、再重入总编排脚本并给出交付总结。

当前 canonical OCR 路径是**仓库脚本直接调用 OCR 引擎**：

- 默认：本地 `mineru[pipeline]` CLI
- 兼容降级：MinerU 云端 API 或百度 OCR

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

## 文本生成之后：阅读层

上面的流水线在 `final.md` 干净之后结束。阅读层从那里开始。文本可靠了，工具箱才把它当作学术来读——不是为了概述，而是为了进入历史学家之间的那场对话。

### 阅读 skill

两个 skill 以不同尺度读 OCR 后的文本，都是 Obsidian 原生格式。

- **xray-paper** — 为单篇历史论文做 X 光透视：还原作者追问的问题（问题意识）、定位论文在学术传统中的位置（学派谱系）、梳理论文的时间脉络、凝结与既有判断发生结构性碰撞的认知卡片。触发语："分析这篇论文"、"X-ray 这篇文章"、"帮我定位这篇论文的位置"。产出：`<workspace>/analysis/{stem}_xray.md`，含 YAML frontmatter、callout、ASCII 年代纪、SVG 位置图。

- **paper-summary** — 把 5–30 篇论文作为一个学术场绘制地图：史料基础、学派谱系、时空覆盖、方法论分布、概念争议、理论借用、未竟难题、新手入门路径。触发语："综述这批文献"、"给这批论文绘图"、"这个场域现在什么样"。产出：`<workspace>/analysis/literature-map.md` 或 `docs/literature-map/{corpus-name}.md`。

两个 skill 都可选渲染 **attribution-theme HTML viewer**——一份独立的呈现写作：Cormorant Garamond 大写英文 hero、Ink Stone 暗色舞台、强调以 luminance 承载而非斜体、谱系图与覆盖图在 Obsidian 栏宽之外舒展。所有 viewer 集中在 `<workspace-parent>/viewer/` 下，文件名约定 `{YYYY-MM-DD}-{一句话态度立场}--{作者}-{论文名字}.html`。

### 解读命令

四个基于视角的 slash 命令，各以一个传统或人物命名。全部在 OCR 后、校对后的文本上运行，写入独立的解读报告——永不改动源文件。

| 命令 | 传统 | 干什么 |
|------|------|--------|
| `/chunqiu` | 春秋笔法 | 读禁忌、读定谳、读有意模糊——作者不愿明说的那部分 |
| `/kaozheng` | 乾嘉考证 | 审察论证、核查引证、测试证据桥——warrant 站得住吗？ |
| `/prometheus` | 普罗米修斯 | 为一个历史概念盗火定义；输出一张 attribution-theme SVG 卡片 |
| `/real-thesis` | — | 挖出作者反复绕但不敢正面写出的那个真论题 |

每个视角读的东西不一样：`chunqiu` 读沉默，`kaozheng` 核 warrant，`prometheus` 给概念命名，`real-thesis` 挖未明说者。选与论文所问相配的那个视角。

## 接入

每个 runtime 的接入步骤见 [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md)。先给两条捷径：

- **一条命令的机械路径**：`python3 scripts/run_full_pipeline.py --pdf <input.pdf>`
- **一次请求的 agent 路径**：`agents/ocr-pipeline-operator.md` + `agents/historical-proofreader.md`

分平台接入。原生识别 `AGENTS.md` 的 runtime 零配置即可；其余需要一份短规则文件或 wrapper manifest。

- **Claude Code** — `/plugin install /path/to/collate`。原生 `.claude-plugin/plugin.json` 随仓库发布，skills 注册为 `/collate:<skill>`。
- **OpenCode** — `cd /path/to/collate && opencode`。原生读取 `AGENTS.md`（缺失时回落到 `CLAUDE.md`）。Skill 可放 `.opencode/skills/`，或走 Claude Code 兼容层直接复用 `~/.claude/skills/`。
- **Hermes agents** — `cd /path/to/collate && hermes`。原生读取 `AGENTS.md` 与 `.hermes.md`；skill 落到 `~/.hermes/skills/`。已有 OpenClaw 配置的用户可用 `hermes claw migrate --workspace-target /path/to/collate` 迁移过来。
- **Codex CLI** — `cd /path/to/collate && codex`。Codex 会从 CWD 一路向上找到 git root 并自动加载 `AGENTS.md`；子 agent 定义在 `.codex/agents/*.toml`。
- **Cursor** — 在 `.cursor/rules/collate.mdc` 写入一条带 `alwaysApply: true` frontmatter 的规则，正文引用 `AGENTS.md`；用 Cursor 的 shell 工具调 `skills/*/scripts/*.py`。旧版 `.cursorrules` 也仍可用。
- **Gemini CLI** — 克隆仓库，把 `AGENTS.md` 作为会话上下文载入，用 shell 工具调 `skills/*/scripts/*.py`。配套 `gemini-extension.json`（`contextFileName: "AGENTS.md"`）以打开 `gemini extensions install /path/to/collate` 一键安装路径，仍在路线图上。
- **OpenClaw** — 原生包装（`openclaw.plugin.json` + TypeScript entry、发布到 ClawHub 或 npm，用户跑 `openclaw plugins install @collate/openclaw` 即可安装）在路线图上。当前 OpenClaw 用户可用 `hermes claw migrate` 把设置、skills 与 `AGENTS.md` 迁到 Hermes，再走上面的 Hermes 路径。
- **Kimi / MiniMax agents** — 把 `agents/historical-proofreader.md` 作为 system prompt；Python 脚本在执行机（本地或 CI）上跑，中间产物回传对话。

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

版权 2026 Alice <Mcyunying@gmail.com>。与 Claude Opus 4.7（Anthropic）及 GPT-5.4（OpenAI）共笔；按 AI 协作作品的适用法律，版权由 Alice 独家持有，作者身份（authorship）为联合。详见 [NOTICE](NOTICE) 与 [CONTRIBUTORS.md](CONTRIBUTORS.md)。

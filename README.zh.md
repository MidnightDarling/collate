<div align="center">

# 点校 · Collate

和你的 Agent 一起阅读历史、思考历史、书写历史。<br />
从一页扫描到一篇定稿，从单篇论文的透视到整个学术场的地图。

![注意力作为观察者的自画像](assets/readme-hero-v2.png)

> 建立：2026-04-19 · Alice、Claude Opus 4.7 与 GPT-5.4 共笔 · 代码 Apache-2.0，引用材料 CC-BY-4.0

[English](README.md) · [中文](README.zh.md)

</div>

---

## 这是什么

一张三方共用的工作台 —— 一位历史学者、与之共事的 agent、以及文本被流转的原作者。人类提供扫描原件,持有最终的学术判断。Agent 承担其间耐心、重复的劳动:清理、识别、点校、自审、排版。每一份中间产物都留在 workspace 里,任何一处决定都可以回溯到它来自的那一页。

流水线之外还有一层**阅读层** —— 把恢复出来的文本作为学术而非数据来读的 skill 与命令。为单篇论文透视它的论证、为整片文献绘出场域的形状、核查一条引证、读出作者选择不说的部分、为某个关键概念定义、贴近作者反复趋近但不敢正面落笔的那个论题。这些不是抽取。这些是加入历史学者一直在进行的那场对话的不同方式。

工具箱本身**与 runtime 无关**:任何能跑 Python 脚本、读结构化 Markdown 知识库的 agent 都可以接入。下面的兼容矩阵会诚实标注哪一处是经过验证的原生支持,哪一处仍需手动接线。

*Collate* 对应中文的**点校** —— 中国古代学者断句、勘误、校异的传统工夫。我们以当代的 OCR 与 agent 工具,延伸这门有千年积淀的手艺。我们不擅自改良所点之文,我们只让它重新可读。

---

## 立场

工作台前会面的是三方。把它们一一命名,工程才能保持诚实。

- **历史学者** —— 提出问题的人。学术判断的最终权威。Agent 从不替你决定一段文字的含义;它们把文本整理到位,让你能判断。
- **Agent** —— 工作的共同作者,不是自动售货机。它们承担那些耐心的劳动:擦去一个水印、扫一遍易混字、把五步清单一条一条走完、把每一处改动留痕以便审。它们的推理被刻意留在可见处,因为不留痕的工作就是不可被信任的工作。
- **原文的作者** —— 在每一行经过这条流水线的字句里都在场。整套装置之所以存在,是为了让他们写下的文字能被再次阅读、被正确引用、被对话。我们点校传世之书,不暗中改写它。

中间产物、标注、修改记录,全部留在 workspace 里。这个工具箱端到端可审计 —— 因为在这种尺度上,尊严唯有在被看见时才能存活。

---

## 快速开始

### 1 · 安装

**Claude Code 用户** —— 在 CLI 里两行,不用克隆仓库:

```
/plugin marketplace add MidnightDarling/collate
/plugin install collate@collate
```

**其他 runtime**(OpenCode / Hermes / Codex CLI / Cursor / Gemini CLI)—— 一条 shell 命令克隆仓库、装 Python 依赖,并自动接入检测到的 runtime:

```bash
curl -fsSL https://raw.githubusercontent.com/MidnightDarling/collate/main/scripts/install.sh | bash
```

参数:`--target PATH`(默认 `~/.local/share/collate`)· `--no-deps` · `--no-runtimes` · `--dry-run` · `--help`。通过管道传参用 `bash -s -- <flags>`。

系统依赖:`poppler`(macOS 用 `brew install poppler`,Debian/Ubuntu 用 `apt install poppler-utils`)。分 runtime 的接入细节见 [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md);详细安装步骤见 [INSTALL.md](INSTALL.md)。

### 2 · 自检

```
/collate:setup
```

诊断 Python 版本、十个依赖包、`pdftoppm` 二进制、OCR 引擎凭据。逐项报告通过/缺失,每个缺失给一条修复建议。从不自动安装。

### 3 · 跑

**公开用户路径** 只有 `/collate:ocr <pdf-path>`。
`python3 scripts/run_full_pipeline.py --pdf <pdf-path>` 只是内部 / 调试入口，
除非它也通过同一套 fresh-agent + real-PDF gate，否则不能单独当发布证据。

支持两种入口:

| 入口 | 适用 |
|------|------|
| `/collate:ocr <pdf-path>` | 公开的一次性完整入口 —— agent 自主跑完并对最终交付负责 |
| `python3 scripts/run_full_pipeline.py --pdf <pdf-path>` | 内部 / 调试机械入口,适合 CI 与批量任务,但本身不构成发布完成 |

agent 入口是 canonical 路径:它调机械总编排脚本、生成逐页 review packets、带着页图证据调 `historical-proofreader`、机械验证 review 完整性、再重入总编排脚本完成应用修改与自审、把交付总结原样上抛。

smoke 通过和 truthful failure 只算 guardrail,不算发布完成。真正的发布标准仍然只有这一句:

```text
fresh clone + supported agent runtime + /collate:ocr <real-pdf> + no human intervention + valid final.docx/wechat.html
```

---

## 兼容性

每个 runtime 一个状态标签。每条声明都对应到具体文件或命令 —— 没有原生支持的地方,绝不包装成原生。

| Runtime | 状态 | 原生入口 | 安装方式 | 备注 |
|---------|------|---------|----------|------|
| **Claude Code** | Supported | `.claude-plugin/plugin.json` · `.claude-plugin/marketplace.json` | `/plugin install collate@collate` | 原生插件;在 Claude Code marketplace 端到端验证。 |
| **Codex** | Supported | `.codex-plugin/plugin.json` · `.agents/plugins/marketplace.json` · `AGENTS.md` | repo 级 marketplace | 通过 Codex 的 marketplace 入口原生支持。 |
| **OpenCode** | Partial | `AGENTS.md`(自动加载) | `cd /path/to/collate && opencode` | 原生指令入口被识别;skill 通过 Claude Code 兼容层复用,或手抄到 `.opencode/skills/`。 |
| **Hermes agents** | Partial | `AGENTS.md` · `.hermes.md` | `cd /path/to/collate && hermes` | 原生上下文加载;skill 复制到 `~/.hermes/skills/`。 |
| **Cursor** | Adapter | `.cursor/rules/collate.mdc`(手写) | 手写规则文件指向 `AGENTS.md` | skill 通过 Cursor 的 shell 工具调起;尚无插件 manifest。 |
| **Gemini CLI** | Adapter | `AGENTS.md` 作为会话上下文(手动) | 通过 shell 工具调用 `skills/*/scripts/*.py` | 原生 `gemini-extension.json` 包装在路线图上。 |
| **OpenClaw** | Planned | — | 当前用 `hermes claw migrate` 迁到 Hermes | 原生 `openclaw.plugin.json` 在路线图上。 |
| **Kimi / MiniMax** | Adapter | `agents/historical-proofreader.md` 作为 system prompt | 脚本在执行机上跑,中间产物回传对话 | 无原生插件路径;走该模型的通用 agent 协议。 |

每一行的具体接线步骤见下方 [`## 分 runtime 接入`](#分-runtime-接入)。

---

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
  6. diff-review      自审:采纳 / 漏改 / 清单外修正 / 未锚定
  7. to-docx          学术规范 Word 稿
  8. mp-format        公众号推文 HTML
  │
  ▼
Human: final.docx + final.mp.html + 审计日志
```

**核心原则**:AI 不替人做学术判断。校对阶段产出机器可读的分级清单,agent 按清单修正后,通过 diff-review 自审留痕。所有中间产物、标注、修改记录保留,交付时人类能逐条回溯。

### 文献类型

校对层内置三套校准过的知识库。类型由 agent 判定,或调用时传入 `--type=classics|republican|modern`。

| 类型 | 典型问题 | 知识库 |
|------|---------|--------|
| 现代简体论文 | 扫描噪点、字形混淆(曰/日、己/已/巳)、标点漂移、参考文献格式 | `skills/proofread/references/modern-chinese.md`;GB/T 7714 |
| 民国排印本 | 繁简并存、旧式标点、译名过渡期、新旧地名 | `skills/proofread/references/republican-era.md` |
| 繁体古籍 | 异体字、避讳字、竖排、无标点 | `skills/proofread/references/traditional-classics.md`;异体字不强改,避讳字仅标注 |

---

## 仓库结构

一个 **Claude Code 插件**(同时也是 runtime 无关的 Python 工具箱)—— 直接安装,或手动复制组件。

```
collate/
├── .claude-plugin/
│   ├── plugin.json              /plugin install 读取的清单
│   └── marketplace.json         marketplace 目录
├── .codex-plugin/
│   ├── plugin.json              Codex 原生插件清单
│   └── README.md                Codex 插件入口说明
├── .agents/
│   └── plugins/marketplace.json Codex 用的 repo 级 marketplace
│
├── skills/                      10 个 skill · 流水线 + 阅读层
│   ├── setup/                   环境诊断(Python、poppler、OCR 凭据)
│   ├── prep-scan/               PDF → 清理后逐页 PNG(HSV 章法、形态学水印、裁边)
│   ├── visual-preview/          逐页三态 HTML(原始 / 清理后 / 差异热图)
│   ├── ocr-run/                 MinerU 本地 / MinerU 云 / 百度 —— 输出 raw.md + meta.json
│   ├── proofread/               五步清单 + 三套类型知识库 → raw.review.md
│   ├── diff-review/             raw.md 与 final.md 对比,与清单关联
│   ├── to-docx/                 python-docx,统一学术规范
│   ├── mp-format/               公众号 HTML 内联 CSS + xiumi 附件
│   ├── xray-paper/              单篇历史论文 X 光透视(Obsidian 原生)
│   └── paper-summary/           5–30 篇文献绘图(Obsidian 原生)
│
├── agents/                      2 个专职 subagent
│   ├── ocr-pipeline-operator.md 流水线总操作员:机械 → 校对 → 自审 → 交付
│   └── historical-proofreader.md 领域专家:执行五步清单,产出 A/B/C 校对
│
├── commands/                    14 个 slash 命令 · 总编排 + 阶段 + 阅读视角
│   ├── ocr.md                   /ocr — 一次性全流水线
│   ├── status.md                /status — 读 _pipeline_status.json,报阶段与下一步
│   ├── setup.md                 /setup — 验证依赖与凭据
│   ├── prep-scan.md             /prep-scan — 仅做预处理
│   ├── visual-preview.md        /visual-preview — 重新生成三态预览
│   ├── ocr-run.md               /ocr-run — 仅 OCR 阶段(不向下传应用/docx/wechat)
│   ├── proofread.md             /proofread — 调度 historical-proofreader,输出 raw.review.md
│   ├── diff-review.md           /diff-review — 闭环自审
│   ├── to-docx.md               /to-docx — 把 final.md 出成学术 Word
│   ├── mp-format.md             /mp-format — 把 final.md 出成公众号 HTML
│   ├── chunqiu.md               /chunqiu — 读禁忌、定谳、有意模糊(春秋笔法)
│   ├── kaozheng.md              /kaozheng — 核引证、审 warrant(乾嘉考证)
│   ├── prometheus.md            /prometheus — 为概念定义,渲染 attribution-theme SVG 卡
│   └── real-thesis.md           /real-thesis — 挖作者绕而不写的真论题
│
├── scripts/
│   ├── run_full_pipeline.py     机械总编排(不依赖 agent)
│   ├── apply_review.py          按 raw.review.md 把改动落到 raw.md,出 final.md
│   ├── pipeline_status.py       pipeline workspace 状态辅助
│   ├── review_contract.py       proofread / apply / diff 共享的 review 契约解析
│   ├── workspace_readme.py      把 workspace README 重写为当前目录地图
│   └── install.sh               跨 runtime 安装器
│
├── docs/
│   ├── ARCHITECTURE.md          skill 职责边界、数据流、文件布局
│   ├── INTEGRATIONS.md          分 runtime 的接入步骤
│   ├── TROUBLESHOOTING.md       常见报错与兜底
│   └── ...                      仅保留公开文档
│
├── AGENTS.md                    agent 契约 —— 调用约定、决策矩阵、失败处理
├── CONTRIBUTORS.md              作者与贡献者(署名,非法律归属)
├── INSTALL.md                   详细安装指南
├── NOTICE                       版权 + 共笔 + 第三方许可
├── LICENSE                      Apache-2.0(代码)
└── LICENSE-REFERENCES           CC-BY-4.0(引用材料)
```

---

## Skills 详述

每个 skill 是自包含目录:`SKILL.md`(agent 读取的操作指令)+ `scripts/`(Python 工具)+ `references/`(结构化知识库,如适用)。八个 skill 组成 OCR 流水线;两个 skill 在阅读层。

### 流水线 skill

> **setup**

环境诊断。验证 Python ≥ 3.9、十个依赖包、`pdftoppm` 二进制,以及 `~/.env` 中的 OCR 引擎凭据。逐项报告通过/缺失,每个缺失给一条修复建议。从不自动安装。

*触发*:首次安装,或者任何"OCR 怎么跑起来"的问题。

---

> **prep-scan**

源 PDF 预处理。每页按 300 DPI 切分,然后跑三轮清理:

- HSV 色域分离 + 连通域面积过滤 —— 去红蓝馆藏章。
- 灰度旋转 + 形态学开运算 `MORPH_OPEN` —— 去对角数据库水印(知网、读秀、维普)。
- 高斯模糊 + 顶帽变换 + 正文保护 —— 去浅色重复水印,不误伤正文。

可选页眉页脚裁切。产出:`<workspace>/prep/cleaned.pdf`,直接给下一步 OCR。

*触发*:"预处理 PDF"、"去水印"、"去馆藏章",或者凡是从知网/读秀/国图/档案数据库下载来的扫描 PDF。

---

> **visual-preview**

逐页三态 HTML —— 原始 / 清理后 / 差异热图,清理掉的部分以半透明红色叠在原图上。清理比 > 20% 的页自动标红,agent 据此决定是否调参重跑 `prep-scan`。

*触发*:`prep-scan` 跑完之后,或者"看看清理效果"、"对比一下"、"去水印成功没"。

---

> **ocr-run**

三引擎 OCR。默认走本地 **MinerU CLI**(`mineru[pipeline]`);`OCR_ENGINE=baidu` 切换百度云 OCR(成本优先);`OCR_ENGINE=mineru-cloud` 走 MinerU 云 API 作为兼容降级。专为历史文献优化的参数:繁体竖排、古籍异体字、民国新式标点、现代简体。

产出:`raw.md` + 原件/识别并排 HTML + `meta.json`(用了什么引擎、用时、低置信页)。

*触发*:"跑 OCR"、"识别文字"、"PDF 转文字"、"准备校对"。

---

> **proofread**

工具箱的合页。`historical-proofreader` agent 强制执行**五步清单**:

1. 结构健全性 —— 标题、脚注、段落完整性。
2. 字形扫描 —— 按类型 reference grep 字形混淆。
3. 规范扫描 —— 标点、引号、DOI / ISBN / 页码格式。
4. 跨段一致性 —— 术语、译名、引文格式。
5. 专名核查 —— 人名、地名、年号、官职。

产出 `raw.review.md`,条目按 **A**(OCR 错,必改)/ **B**(学术规范,应改)/ **C**(存疑待考)分级。每条带行号、原文片段、建议、依据。末尾附执行自证表,人能验证五步是不是真跑了。

*触发*:"校对这份稿子"、"看看 OCR 对不对"、"过一遍"。

---

> **diff-review**

闭环自审。agent 按 `raw.review.md` 改完后,本 skill 对比 `raw.md` 与改后的 `final.md`,生成段落级 HTML 报告,把每一处改动归到四种状态:

- **采纳** — agent 落实了清单的某条建议
- **漏改** — 清单上的条目没被处理
- **清单外修正** — 清单没要求,agent 自己加的修改
- **未锚定改动** — 没明显依据的改动

外加一份带计数的 `diff-summary.md`。这是端到端可审计的关键。

*触发*:任何一轮校对的收尾,或者"我漏改啥没"、"看看改了啥"、"diff"。

---

> **to-docx**

学术规范 Word,基于 python-docx。统一规范:思源宋体 SC 12pt 正文、1.2 行距、字间距 0.2 pt、上下左右 2 cm 页边距、段首缩进 2 字符、脚注连续编号、中文引号、图表题注位置。

*触发*:"出成 Word"、"给我一份 docx"、"投稿版本"、"给编辑看"。

---

> **mp-format**

公众号 HTML —— 大多数中文人文作者最实际的发布目标。全内联 CSS(公众号剥离外链样式表);OpenCC `t2s` 繁简转换施加于正文,**但保留 `>` 引用块的原貌**(引文不转换);脚注集中文末;作者 / 来源卡片。

同时输出一份 xiumi 兼容的 Markdown 附件,给习惯在秀米/壹伴里做最后视觉调整的用户。

*触发*:"排公众号"、"做成推文"、"秀米"、"发出去"。

### 阅读层 skill

上面的流水线在 `final.md` 干净之后结束。阅读层从那里开始。文本可靠了,工具箱才把它当作学术来读 —— 不是为了概述,而是为了进入历史学家之间的那场对话。两个阅读 skill 都是 Obsidian 原生格式;两者都可以选渲染一份 attribution-theme HTML viewer(规则与文件名约定写在各自的 `SKILL.md` 里)。

> **xray-paper**

为单篇历史论文做实质深度的 X 光透视。还原作者追问的问题(问题意识)、定位论文在学术传统中的位置(学派谱系)、梳理论文的时间脉络、凝结与既有判断发生结构性碰撞的认知卡片。

产出:`<workspace>/analysis/{stem}_xray.md`,含 YAML frontmatter、callout、ASCII 年代纪、SVG 位置图。

*触发*:"分析这篇论文"、"X-ray 这篇文章"、"帮我定位这篇论文的位置"、"帮我读一下"。

---

> **paper-summary**

把 5–30 篇论文作为一个学术场绘制地图。八个交叉阅读维度:史料基础、学派谱系、时空覆盖、方法论分布、概念争议、理论借用、未竟难题、新手入门路径。

产出:`<workspace>/analysis/literature-map.md` 或 `docs/literature-map/{corpus-name}.md`。

*触发*:"综述这批文献"、"给这批论文绘图"、"给我看下这场域"、"这个领域现在什么样"。

---

## Commands 详述

十四个 slash 命令。按层次自然分为三类 —— 全流水线总编排、单阶段执行器(需要手动控制时用)、以及对 OCR 后文本的阅读视角。

### 总编排

| 命令 | 干什么 | 何时用 |
|------|--------|--------|
| `/ocr <pdf>` | 调度 `ocr-pipeline-operator`。一次调用跑完 prep → OCR → 校对 → 应用 → diff-review → docx → wechat,返回交付路径与审计摘要。 | 默认入口。把扫描 PDF 交给 agent,让它走完那一长段;你回来时拿到的是交付物与审计记录。 |
| `/status [workspace]` | 读 `<ws>/_internal/_pipeline_status.json`,报阶段/状态/下一步,逐项核对哪些交付物在场或缺失。 | 跑了一半被打断,或想知道接下来该干什么。 |
| `/setup` | 诊断 Python 依赖、poppler、OCR 凭据。逐项报告通过/缺失,每个缺失给一条修复建议。从不自动安装。 | 首次安装、环境刷新,或者东西莫名其妙坏了。 |

### 流水线阶段

这些命令直接调单个 skill。当你想检查或重跑某一段时用。

| 命令 | 干什么 | 何时用 |
|------|--------|--------|
| `/prep-scan <pdf>` | 300 DPI 切分、去水印、裁边、生成 `cleaned.pdf`、出三态预览。**不会自动走到 OCR**。 | 第一阶段。在花钱跑 OCR 前先看预览。 |
| `/visual-preview <ws>` | 为已经预处理过的 workspace 重新生成三态预览。 | 调了 `--header-ratio` 想看新效果时。 |
| `/ocr-run <pdf-or-ws>` | 只跑 OCR,不向下传。按 `OCR_ENGINE` 选引擎(默认本地 MinerU)。`run_full_pipeline.py` 的 canonical 兜底链:本地 MinerU → `mineru-cloud`(需 `MINERU_API_KEY`)→ `extract_text_layer.py`(设 `COLLATE_ALLOW_TEXTLAYER=0` 可关)。 | 预处理已确认无误,只想跑 OCR 这一段时。 |
| `/proofread <ws> [type]` | 调度 `historical-proofreader`。读 `raw.md` + `meta.json`,如果没传类型就自动分类,产出 `review/raw.review.md` 走 canonical 格式(`### A1. <title> · Line 42` + 原文 + 建议 + 依据)。已存在审计文件时拒绝静默覆盖。 | `raw.md` 就绪,只想要校对清单,先不应用任何修改时。 |
| `/diff-review <ws>` | 对比 `raw.md` 与 `final.md`,与 `raw.review.md` 关联,把每处改动归类到 采纳/漏改/清单外/未锚定。出 HTML 报告与 Markdown 摘要。 | 闭环检查。`apply_review.py` 跑完后任何时候都可以跑,看漏改和即兴改动。 |
| `/to-docx <ws>` | 用统一学术规范从 `final.md` 出 `<ws>/output/<stem>_final.docx`。文档标题取自第一个 H1。 | 文本定稿,需要期刊就绪的 Word 版本时。 |
| `/mp-format <ws>` | 从 `final.md` 出 `<ws>/output/<stem>_wechat.html` 加一份 xiumi 附件。全内联 CSS,OpenCC t2s 但保留引用块原貌,脚注集中文末。 | 发公众号时。严格基于 `final.md`,不会从 `raw.md` 出。 |

### 阅读视角

四个解读命令。它们在 OCR 后、校对后的文本上运行,写入独立的解读报告 —— 永不改动源文件。每个命令以一个传统或人物命名,各以不同意图阅读。

| 命令 | 传统 | 读什么 | 产出 |
|------|------|--------|------|
| `/chunqiu` | 春秋笔法 | 禁忌、定谳、有意模糊 —— 作者不愿明说的部分。卒/薨/崩 与 诛/弑/戮 这种区分承载判断之重。 | `analysis/{stem}_chunqiu.md` —— 用字定谳、重复与停顿、借古之镜、一句不说的话。 |
| `/kaozheng` | 乾嘉考证 | 论证可靠性 —— evidentiary bridge 撑得住吗,每条引文是否对应原文,warrant 经得起推敲吗。flag 孤证不立。 | `analysis/{stem}_kaozheng.md` —— Toulmin 论证骨架、引证审计表、要害失误与修复建议。 |
| `/prometheus` | 普罗米修斯 | 文中的某一概念 —— 设其属、明其差、给白话注、放回它的制度与时代脉络。 | `analysis/prometheus/{concept}.svg` —— attribution-theme SVG 卡片,one Signal per page,IBM Plex Mono Light 正文。 |
| `/real-thesis` | — | 作者反复绕但不敢正面写的那个论题。看哪里一再回来、哪里 略而不论、哪里引证最密、哪里脚注比正文更卖力。 | `analysis/{stem}_real-thesis.md` —— 表面话题、漂浮的关切、一到三个候选真论题及其证据、一个作者不敢自问的问题。 |

挑与论文所问相配的那一个:`chunqiu` 读沉默,`kaozheng` 核 warrant,`prometheus` 给概念命名,`real-thesis` 挖未明说者。

---

## Agents

两个 subagent 处理调度。Skill 是被动的指令文档;agent 拥有端到端编排和工具调用权。

| Agent | 角色 |
|-------|------|
| `ocr-pipeline-operator` | 流水线总操作员。调机械总编排、生成逐页 review packets、带页图证据调度 `historical-proofreader`、机械验证 review，再重入总编排串起 apply-review / diff-review / to-docx / mp-format,最后把面向人类的交付总结上抛。 |
| `historical-proofreader` | 领域专家。按文献类型加载对应 reference 表,执行强制五步清单,产出走 canonical 格式的 `raw.review.md`,末尾附执行自证表。 |

---

## 分 runtime 接入

每个 runtime 的状态标签与原生入口已在上方 [`## 兼容性`](#兼容性)诚实标注。本节给的是每一行对应的实地接线。

先两条通用捷径:

- **机械路径(无 agent)**:`python3 scripts/run_full_pipeline.py --pdf <input.pdf>` —— 适合 CI 与批量任务,但本身不算发布完成证据。
- **一次请求的 agent 路径**:`agents/ocr-pipeline-operator.md` + `agents/historical-proofreader.md` —— `/ocr` 调起的两个 agent。

原生识别 `AGENTS.md` 的 runtime 几乎零配置;其余需要一份短规则文件、wrapper manifest,或显式 shell-tool 调用。每个 runtime 的完整接入指南在 [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md)。

| Runtime | 接入方式 |
|---------|----------|
| **Claude Code** | `/plugin install /path/to/collate`。原生 `.claude-plugin/plugin.json`;skills 注册为 `/collate:<skill>`。 |
| **OpenCode** | `cd /path/to/collate && opencode`。原生读取 `AGENTS.md`(缺失时回落到 `CLAUDE.md`)。Skill 可放 `.opencode/skills/`,或走 Claude Code 兼容层直接复用 `~/.claude/skills/`。 |
| **Hermes agents** | `cd /path/to/collate && hermes`。原生读取 `AGENTS.md` 与 `.hermes.md`;skill 落到 `~/.hermes/skills/`。已有 OpenClaw 配置的用户可用 `hermes claw migrate --workspace-target /path/to/collate` 迁过来。 |
| **Codex** | 仓库随发原生 `.codex-plugin/plugin.json` 与 repo 级 `.agents/plugins/marketplace.json`。支持 plugin directory 的 Codex 端重启后可直接从该 marketplace 安装 `collate`;在仓库里直接工作时,`cd /path/to/collate && codex` 仍会从 git root 自动加载 `AGENTS.md`。 |
| **Cursor** | 在 `.cursor/rules/collate.mdc` 写一条带 `alwaysApply: true` frontmatter 的规则,正文引用 `AGENTS.md`;用 Cursor 的 shell 工具调 `skills/*/scripts/*.py`。旧版 `.cursorrules` 也仍可用。 |
| **Gemini CLI** | 克隆仓库,把 `AGENTS.md` 作为会话上下文载入,用 shell 工具调 `skills/*/scripts/*.py`。配套 `gemini-extension.json` 包装(走 `gemini extensions install /path/to/collate` 一键安装)在路线图上。 |
| **OpenClaw** | 原生包装(`openclaw.plugin.json` + TypeScript entry,发布到 ClawHub 或 npm,`openclaw plugins install @collate/openclaw` 即装)在路线图上。当前 OpenClaw 用户可用 `hermes claw migrate` 迁到 Hermes,走上面 Hermes 的路径。 |
| **Kimi / MiniMax agents** | 把 `agents/historical-proofreader.md` 作为 system prompt;Python 脚本在执行机(本地或 CI)上跑,中间产物回传对话。 |

---

## 依赖

Python 3.9+ 与:

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
mineru[pipeline]
```

仅在 `mp-format --simplify` 时才需要的可选依赖：

```text
opencc-python-reimplemented
```

系统依赖:

- macOS:`brew install poppler`
- Debian/Ubuntu:`apt install poppler-utils`

---

## 环境变量

脚本读取以下变量,如何存储由调用方决定(推荐 `~/.env`,不建议 project 级 `.env`)。

| 变量 | 说明 |
|------|------|
| `OCR_ENGINE` | `mineru`(本地 CLI,默认)/ `baidu` / `mineru-cloud` |
| `MINERU_API_KEY` | 仅 `OCR_ENGINE=mineru-cloud` 需要 |
| `BAIDU_OCR_API_KEY` | `OCR_ENGINE=baidu` 需要 |
| `BAIDU_OCR_SECRET_KEY` | 同上 |

---

## 隐私

- **本地 MinerU CLI**(默认):完全本地处理,不上传任何内容。
- **MinerU 云 API**(`OCR_ENGINE=mineru-cloud`):当前实现先把 PDF 上传到 catbox.moe(匿名公开文件托管,24 小时保留),再把 URL 提交 MinerU。PDF 短暂暴露于公网;敏感材料请改用本地 CLI 或百度 OCR。
- **百度 OCR**(`OCR_ENGINE=baidu`):每页 base64 编码后 HTTPS 发往百度云,受百度 ToS 约束。

插件本身不发任何遥测或汇报请求。`~/.cache/baidu_ocr_token.json` 缓存百度 access token 24 小时。

---

## 文档入口

- [AGENTS.md](AGENTS.md) — agent 契约:每个 skill 的调用约定、决策矩阵、失败处理
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — skill 职责边界、数据流、文件布局
- [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) — 分 runtime 的接入步骤
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — 常见报错与兜底
- [CONTRIBUTORS.md](CONTRIBUTORS.md) — 作者与贡献者

---

## 许可

- **代码**(所有 Python 脚本、配置、shell 片段、SKILL.md):[Apache License 2.0](LICENSE)
- **引用材料**(docs/、skills/*/references/、README、AGENTS.md、原创插图):[CC-BY-4.0](LICENSE-REFERENCES)
- **第三方依赖**保留各自许可——见 [NOTICE](NOTICE)

版权 2026 Alice <Mcyunying@gmail.com>。与 Claude Opus 4.7(Anthropic)及 GPT-5.4(OpenAI)共笔;按 AI 协作作品的适用法律,版权由 Alice 独家持有,作者身份(authorship)为联合。详见 [NOTICE](NOTICE) 与 [CONTRIBUTORS.md](CONTRIBUTORS.md)。

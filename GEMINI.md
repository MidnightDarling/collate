# GEMINI.md — collate

> Gemini CLI 在每次会话中自动加载此文件作为项目上下文。完整工作流契约见 [AGENTS.md](AGENTS.md)。

## 这个仓库是什么

collate 是一个中文历史文献 OCR + 校对工具包。从扫描件到最终的 Word 稿和公众号推文，agent 自主完成清理、识别、校对、自审、排版。所有中间产物保留在工作区，方便逐行溯源。

pipeline 之上还有一层**阅读 skill**——用学术方法而非数据提取的方式与文本对话。

## 15 个 skill

8 个流水线 + 7 个阅读。每个 skill 是一个自包含目录：`SKILL.md`（指令）+ `scripts/`（Python）+ `references/`（知识库）。

### 流水线

| Skill | 做什么 | 何时调用 |
|-------|--------|---------|
| setup | 环境诊断（Python、poppler、OCR 凭据） | 首次使用 |
| prep-scan | 去水印 / 去馆藏章 / 裁边 → cleaned.pdf | 拿到 PDF 后 |
| visual-preview | 清理结果三态 HTML 预览 | prep-scan 后 |
| ocr-run | MinerU / 百度 OCR → raw.md + meta.json | visual-preview 后 |
| proofread | 五步 checklist → A/B/C 三级校对清单 | raw.md 就位后 |
| diff-review | raw vs final 语义级审计 HTML | final.md 就位后 |
| to-docx | 学术 Word 文档 | diff-review 后 |
| mp-format | 公众号排版 HTML + xiumi sidecar | 最后一步 |

### 阅读

| Skill | 做什么 |
|-------|--------|
| xray-paper | 单篇论文 X 光透视（Obsidian 原生） |
| paper-summary | 5–30 篇语料图谱（Obsidian 原生） |
| chunqiu | 读禁忌、裁断与策略性沉默 |
| kaozheng | 审引文、来源等级与论证链 |
| prometheus | 定义一个概念，渲染 SVG 卡片 |
| real-thesis | 挖掘论文绕而未写的真命题 |
| constellatio | 跨时代接受史诊断 + 可选星图可视化 |

## 调用方式

读取目标 skill 的 SKILL.md 获取完整指令，然后通过 shell 执行 Python 脚本：

```bash
# 1. 读 skill 契约
cat skills/<skill-name>/SKILL.md

# 2. 执行脚本（示例：拆页）
python3 skills/prep-scan/scripts/split_pages.py \
    --pdf "$WORK_DIR/original.pdf" --out "$WORK_DIR/pages" --dpi 300
```

一条命令跑完整 pipeline（不需要 agent 介入）：

```bash
python3 scripts/run_full_pipeline.py --pdf <input.pdf>
```

## 2 个 subagent

| Agent | 文件 | 职责 |
|-------|------|------|
| ocr-pipeline-operator | `agents/ocr-pipeline-operator.md` | 流水线总调度：机械编排 → 校对 → 自审 → 交付 |
| historical-proofreader | `agents/historical-proofreader.md` | 校对领域专家：五步 checklist，产出 A/B/C 分级清单 |

调度 subagent 的方式：开一个新的 Gemini CLI 会话，把 agent 定义作为上下文加载：

```bash
gemini -C agents/historical-proofreader.md \
  "type=modern, 请按五步 checklist 校对 $WORK_DIR/raw.md"
```

或在当前会话中用 `@agents/historical-proofreader.md` 引用 agent 定义。

## 工作区约定

每份 PDF 产生一个 `<basename>.ocr/` 目录。详见 [references/workspace-layout.md](references/workspace-layout.md)。

关键子目录：`prep/`（清理中间产物）、`output/`（最终交付：docx + wechat）、`review/`（校对清单）、`previews/`（HTML 审计页）。

## 环境变量

```bash
export COLLATE_ROOT=/path/to/collate
export OCR_ENGINE=mineru    # mineru | mineru-cloud | baidu | pdf-text-layer
# 仅 baidu 引擎需要：
export BAIDU_API_KEY=...
export BAIDU_SECRET_KEY=...
```

## 核心原则

1. **端到端自主**：从 PDF 到 docx + wechat.html 由 agent 独立完成
2. **不替换学术判断**：C 类（存疑待考）条目保留原文 + 脚注，由读者判断
3. **失败要显性**：结构化错误上报，不静默兜底
4. **保留可追溯性**：所有中间产物落盘，不清理

## 详细文档

- [AGENTS.md](AGENTS.md) — 完整工作流契约与 skill 调用规范
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — skill 边界、数据流、文件布局
- [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) — 跨运行时接入手册
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — 常见问题

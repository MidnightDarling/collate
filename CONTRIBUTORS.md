# Contributors

> 建立：2026-04-19 · 维护：Alice、Claude Opus 4.7 与 GPT-5.4

本文档记录 `collate` 的作者、贡献与致谢。版权法律归属见 [NOTICE](NOTICE) 与 [LICENSE](LICENSE)；本文档只做**署名**意义上的作者记录。

---

## 核心作者

### Alice

中国社科院历史学研究者。本项目的**原始需求方与学术顾问**：

- 定义校对工作流的实际约束——从扫描件到投稿 Word 稿、公众号推文，每一步都按她的日常工作节奏设计
- 编写 `skills/proofread/references/` 下三类文献（繁体古籍 / 民国排印 / 现代简体）的校对参考
- 提供真实语料持续校准 OCR 识别阈值与校对 checklist 的覆盖度
- 审定 agent 产出的学术规范性，驳回一切替代学者判断的行为

在版权法律意义上，版权由 Alice 独家持有——根据 2023 年以来各法域的司法共识，AI 系统不能独立持有版权。

### Claude Opus 4.7 ([Anthropic](https://www.anthropic.com/))

Anthropic 的大语言模型。本项目的**共同作者**：

- 设计八 step pipeline 的 skill 架构与 agent 契约
- 实现全部 Python 脚本：`prep-scan` 的去水印算法、`ocr-run` 的多引擎抽象、`proofread` 的 checklist 生成器、`diff-review` 的语义级 diff、`to-docx` 的学术模板、`mp-format` 的公众号排版
- 编写 [AGENTS.md](AGENTS.md)、[README.md](README.md)、本文档，以及各 `SKILL.md` 的契约性表述
- 与 Alice 共同确立「agent 不替换学术判断」的底线，并把它写进每一个 skill 的「不做的事」

在署名意义上，Claude Opus 4.7 是本项目的联合作者。版权法律归属归 Alice，但**作者身份（authorship）是联合的**。这种「联合作者 + 单一版权持有人」的安排是当前 AI 协作作品的标准做法，见 [NOTICE](NOTICE) 中的完整法律声明。

### GPT-5.4 ([OpenAI](https://openai.com/))

OpenAI 的大语言模型。本项目当前这一轮清理与收口工作的**联合作者**：

- 统一 `proofread -> apply_review -> diff-review` 的 review 契约，补上兼容解析与自动应用脚本
- 增加总编排与状态收口工具，如 `scripts/run_full_pipeline.py`、`scripts/pipeline_status.py`
- 修正 `visual-preview` 对 `trimmed_pages/` 的忽略，使裁边审计重新成为真实检查
- 收拢仓库入口文案与 operator，让主工作流回到“一次请求 / 一条命令 / 一条审计链”

在署名意义上，GPT-5.4 是本项目这一轮实现与整顿工作的联合作者之一。版权法律归属仍归 Alice，作者身份记录见 [NOTICE](NOTICE)。

---

## 贡献领域分工

| 领域 | 主要贡献者 | 说明 |
|------|---------|-----|
| 学术需求定义 | Alice | 扫描件特征、校对优先级、学术规范底线 |
| 校对 reference 编写 | Alice | `skills/proofread/references/*.md` 三份 |
| Pipeline 架构 | Claude Opus 4.7、GPT-5.4 | 八 step 划分、skill 契约、单命令总编排收口 |
| Python 实现 | Claude Opus 4.7、GPT-5.4 | `skills/*/scripts/*.py` 与新增总编排 / review 工具 |
| OCR 引擎集成 | Claude Opus 4.7 | MinerU CLI / 百度 / 文字层提取 |
| 审计与运行时文档 | Claude Opus 4.7、GPT-5.4 | [AGENTS.md](AGENTS.md)、[docs/INTEGRATIONS.md](docs/INTEGRATIONS.md)、各 SKILL.md |
| 算法校准 | Alice 与 Claude Opus 4.7（共同） | 去水印阈值、裁边比例、proofread 分级规则都经过真实语料迭代 |
| 工作流整顿与自审闭环 | GPT-5.4 | review 契约统一、可重入 orchestrator、状态收口 |
| 失败处理 | 共同 | Alice 定义「什么情况要终止」，模型侧实现结构化错误上报 |

---

## 致谢

本项目的能力依赖于开源社区与公共语言资源：

### 上游软件

- **[MinerU](https://github.com/opendatalab/MinerU)**（OpenDataLab，AGPL-3.0）— 核心视觉 OCR 引擎，其 DocLayout-YOLO + VLM pipeline 是本项目区别于纯文字层提取的关键
- **[OpenCC](https://github.com/BYVoid/OpenCC)**（Byvoid，Apache-2.0）— 繁简转换
- **[python-docx](https://github.com/python-openxml/python-docx)**（Steve Canny，MIT）— Word 文档生成
- **[OpenCV](https://opencv.org/)**（OpenCV 基金会，Apache-2.0）— 图像处理
- **[pdf2image](https://github.com/Belval/pdf2image)** / **[Pillow](https://github.com/python-pillow/Pillow)** / **[pypdf](https://github.com/py-pdf/pypdf)** — PDF 与图像基础设施

### 商业 API

- **[Baidu AI OCR](https://ai.baidu.com/tech/ocr)** — 可选 OCR 引擎
- **[Anthropic Claude](https://www.anthropic.com/)** — 主 agent 与 proofread subagent 的底层模型
- **[Moonshot Kimi K2](https://kimi.moonshot.cn/)** / **[MiniMax](https://www.minimaxi.com/)** — 跨运行时接入的可选后端

### 学术规范参考

- 中华人民共和国国家标准 [GB/T 15834](http://www.moe.gov.cn/jyb_sjzl/sjzl_zcfg/zcfg_qtxgfl/201908/t20190828_396633.html)（标点符号用法）
- [《古籍整理出版规范》](https://www.npopss-cn.gov.cn/)（全国古籍整理出版规划领导小组办公室）
- [北京大学《古典文献学》](http://chinese.pku.edu.cn/) 相关讲义——为 `references/traditional-classics.md` 的异体字、避讳字列表提供了学术依据

本项目对上述工作的引用限于「学习并实现其规则」，不包含任何受保护文本的复制。

---

## 如何贡献

### 报告问题

在 GitHub 提 Issue，请附：

1. 具体 skill 名 + 命令行
2. 输入 PDF 特征（版心尺寸、扫描 DPI、文献年代）
3. 期望产出 vs 实际产出
4. `meta.json` 内容（如果到达了 ocr-run 这一步）

### 提交代码

PR 规范：

- 一次 PR 只改一个 skill，或者一次只改一个横切关注点（如跨 runtime 的环境变量）
- 每个 Python 脚本必须保持**独立可运行**（不引入 skill 间的 Python 包依赖）
- 改动的 skill 必须同时更新对应的 `SKILL.md`
- 涉及 agent 契约的改动必须同时更新 [AGENTS.md](AGENTS.md)
- 署名在 commit trailer 里：

  ```
  Authored-by: <你的名字> <邮箱>
  Co-Authored-By: Alice <MidnightDarling@users.noreply.github.com>
  ```

### 扩展 reference

校对 reference（`skills/proofread/references/`）特别欢迎扩展：

- 新增某个时期 / 某个文类的混淆字对照表
- 补充特定学科的术语规范
- 增加稀有异体字的识别经验

这类扩展需要学术依据——至少一条古籍版本或权威工具书的引用。

### 添加新 runtime 适配

参见 [docs/INTEGRATIONS.md#扩展接入新-runtime](docs/INTEGRATIONS.md#11-扩展接入新-runtime) 的清单，新增一份 `docs/INTEGRATIONS-<runtime>.md`。

---

## 联系方式

- 学术与需求相关：通过 [GitHub Issues](https://github.com/MidnightDarling/collate/issues) 与 Alice 沟通
- 技术实现与 PR 讨论：GitHub Issues / PR
- 安全问题（含 API key 泄露）：先在 GitHub 上发起 private security advisory，24 小时内修复后再公开

---

## 版权与许可

- **版权持有人**：Alice（见 [NOTICE](NOTICE)）
- **联合作者**：Alice、Claude Opus 4.7 与 GPT-5.4
- **代码许可**：[Apache License 2.0](LICENSE)
- **引用材料许可**：[CC BY 4.0](LICENSING.md)

在引用、转载、改编本项目的任何部分时，请同时标注版权持有人（Alice）与联合作者（Alice、Claude Opus 4.7 与 GPT-5.4），以及对应许可证的引用链接。

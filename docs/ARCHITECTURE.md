---
title: Architecture
description: collate 插件的内部架构、数据流、skill 职责边界、设计决策
author: [Alice, Claude Opus 4.7, GPT-5.4]
date: 2026-04-19
status: v0.1.0
---

# Architecture

本文档面向需要读懂插件内部、扩展、修改或调试的开发者；面向最终用户的使用指南见 [README.md](../README.md)。

当前仓库同时发布两层宿主包装：

- `.claude-plugin/`：Claude Code 原生插件入口
- `.codex-plugin/` + `.agents/plugins/marketplace.json`：Codex 原生插件入口

两者都直接指向仓库根的 `skills/`，不再维护第二份运行时专用 skill 副本。命令层也已收敛：`commands/` 只保留 `ocr` 与 `status` 两个独立入口，其余能力统一回收到 skill 本体。

---

## 顶层结构

```
collate/
├── .agents/plugins/marketplace.json  Codex repo marketplace
├── .claude-plugin/plugin.json      插件 manifest（name / version / author）
├── .codex-plugin/plugin.json       Codex plugin manifest
├── README.md                       用户入口
├── AGENTS.md                       给未来接管的 agent 看
├── INSTALL.md                      三个宿主的装法
├── commands/
│   ├── ocr.md                      公共一键入口（总编排）
│   └── status.md                   状态 / 闭环检查
├── scripts/
│   ├── run_full_pipeline.py        机械总编排入口
│   ├── apply_review.py             review 清单保守应用器
│   ├── review_contract.py          proofread / diff-review 共用解析契约
│   ├── pipeline_status.py          `_pipeline_status.json` 读写
│   └── workspace_readme.py         工作区 README 刷新
├── docs/
│   ├── ARCHITECTURE.md             本文
│   └── TROUBLESHOOTING.md          常见报错
├── agents/
│   ├── historical-proofreader.md   唯一的 subagent（校对专家）
│   └── ocr-pipeline-operator.md    一次请求的总操作员入口
└── skills/
    ├── setup/                      首次配置
    ├── prep-scan/                  PDF 预处理
    ├── visual-preview/             清理效果可视化
    ├── ocr-run/                    OCR 识别
    ├── proofread/                  校对（调 agent）
    ├── diff-review/                校对核对
    ├── to-docx/                    Word 生成
    ├── mp-format/                  公众号 HTML
    ├── xray-paper/                 单篇论文 X 光透视
    ├── paper-summary/              文献场全景地图
    ├── chunqiu/                    读禁忌、定谳与沉默
    ├── kaozheng/                   审引证与 warrant
    ├── prometheus/                 概念定义卡
    └── real-thesis/                挖真论题
```

每个 skill 目录结构：

```
skills/<name>/
├── SKILL.md                        触发词 + 工作流规范（给 agent / 用户看）
├── scripts/                        Python 可执行工具
│   └── *.py
└── references/                     知识库（如适用）
    └── *.md
```

---

## 数据流

一份扫描 PDF 从头到尾产生的文件（权威规范：[references/workspace-layout.md](../references/workspace-layout.md)）：

```
~/Downloads/
└── 论文.pdf                               [原件，永不动]
    └── 论文.ocr/                          [唯一工作区，自描述]
        ├── README.md                       [每次 skill 结束自动刷新，人类入口]
        ├── source.pdf                      [进入 OCR 阶段的 PDF 副本]
        ├── raw.md                          [OCR 原始 Markdown]
        ├── final.md                        [agent 校对后定稿]
        ├── meta.json                       [OCR 元信息 + 标题/作者/年份]
        ├── prep/                           [prep-scan 过程产物]
        │   ├── original.pdf                [原件拷贝]
        │   ├── pages/page_*.png            [split_pages.py 拆页]
        │   ├── cleaned_pages/page_*.png    [dewatermark 后]
        │   ├── trimmed_pages/page_*.png    [remove_margins 后，可选]
        │   ├── diff_pages/page_*.png       [visualize_prep.py 差异热图]
        │   └── cleaned.pdf                 [pages_to_pdf.py 合回]
        ├── previews/                        [所有 HTML 预览 / 核验入口]
        │   ├── visual-prep.html            [prep 清理效果]
        │   ├── ocr-preview.html            [左图右文对照]
        │   └── diff-review.html            [raw.md vs final.md]
        ├── review/                          [校对过程产物]
        │   ├── raw.review.md               [proofread 的 A/B/C 清单]
        │   └── diff-summary.md             [diff-review 摘要]
        ├── output/                          [最终交付]
        │   ├── <title>_<author>_<year>_final.docx
        │   ├── <title>_<author>_<year>_wechat.html
        │   └── <title>_<author>_<year>_wechat.md
        ├── assets/                          [OCR 提取的插图]
        │   └── figN.png
        └── _internal/                       [调试 / 起源数据，前缀示意"别动"]
            ├── mineru_full.md              [MinerU 原始 markdown]
            ├── _import_provenance.json     [来源元信息]
            └── _pipeline_status.json       [总编排状态机]
```

**命名约定**：
- `.ocr/` = 唯一工作区（取代早期设计的 `.prep/ + .ocr/` 双目录）
- `prep/ / previews/ / review/ / _internal/` = 过程文档，用户偶尔核验
- `output/` = 最终交付，文件名内嵌 `<title>_<author>_<year>`，易找易寄
- `raw.*` = 原始 / 自动产出
- `final.*` = 定稿

**不变原则**：原 PDF 永不动；整个 `.ocr/` 工作区使用相对路径引用内部资源，可以整体打包或拷贝到任何地方直接离线浏览。

---

## Skill 依赖关系

```
         agent / shell entry
               │
               ▼
   scripts/run_full_pipeline.py
               │
               ├── prep-scan
               ├── visual-preview
               ├── ocr-run
               │       └── raw.md + meta.json + assets/
               │
               ├── (pause when review/raw.review.md missing)
               │
               ▼
   historical-proofreader agent
               │
               ▼
      review/raw.review.md
               │
               ▼
   scripts/run_full_pipeline.py  (re-enter)
               │
               ├── apply_review.py -> final.md
               ├── diff-review -> previews/diff-review.html + review/diff-summary.md
               ├── to-docx
               └── mp-format
               │
               ▼
      output/<title>_<author>_<year>_{final,wechat}.*
```

**三个质检闸门**是设计要点：

1. **visual-preview**（prep 之后）——验证清理过程未误伤正文
2. **proofread 的 Checklist 执行证明表**——确认 agent 已执行字形扫描
3. **diff-review**（改完之后）——核对采纳与漏改条目

任一闸门失效即退化为黑盒交付。插件的定位不是神秘自动化，而是**可重入、可核查、可解释的自动化**。

---

## 核心设计决策

### 0.5 Skill-first interface

能力的唯一权威定义在 `skills/`。

- skill 可以被 runtime 直接暴露成 `/collate:<skill>`
- 独立 command 只保留需要额外编排的 `ocr` 与需要额外收口的 `status`
- 如果某个 command 出现了 skill 没有的能力，这说明能力放错层了，应该并回 skill，再删掉 command 壳

这样做的目的不是“少几个文件”，而是消灭双轨 drift：同一能力不再由 command 和 skill 各写一套规范。

### 1. SKILL.md 写契约，脚本遵守契约

每个 SKILL.md 明确声明"脚本必须实现 X / Y / Z"。脚本是契约的实现，而非 SKILL 的另一种表述，以此防止文档与代码长期漂移——这是插件类项目常见的失修模式（SKILL 声称支持，脚本实际未实现）。

### 2. Agent 走强制 checklist 而非自由通读

早期版本的 `historical-proofreader` agent 工作流是"按顺序通读全文，遇到以下模式即标注一条"。实际测试中会漏掉 reference 已明确列出的经典错误（如"曰/日"），原因是 agent 依赖印象式抽样。

现改为 **Step 1-4 每步列出具体 `grep` 命令，报告必须附 Checklist 执行证明表**（逐项命中数）。该表为 agent 的执行审计——漏跑任一步骤均可从报告中追溯。

### 3. 路径编码兜底

macOS 上 `cv2.imread` 对含中文路径的部分 PNG 会返回 None，且同一目录下行为不一致。所有脚本的图像 I/O 改走 `cv2.imdecode(np.fromfile(...))` / `cv2.imencode + tofile` 以绕过路径编码问题。参见 [skills/visual-preview/scripts/visualize_prep.py](../skills/visual-preview/scripts/visualize_prep.py) 的 `imread_unicode` / `imwrite_unicode`。

### 4. OCR 主线与兼容降级

当前主线是本地 `mineru[pipeline]` CLI。云端 MinerU 与百度 OCR 保留为兼容分支，用于本地 CLI 不可用时的降级与对比，而不是文档层的默认入口。

### 5. diff-review 的"接近"判定

判定用户是否接受 agent 建议时，**不做精确字符串匹配**。策略：从建议中抽取关键字符（如"研完 → 研究"中的"究"），若 final 段落包含这些字符且 raw 不包含，则判为接受。理由：用户常采纳建议方向但以自己的措辞改写，精确匹配会将"同向换词"误判为拒绝。

### 6. 所有 HTML 单文件离线

preview.html / diff.html / visual-preview.html 均为单文件：

- 内联 CSS，无外链样式表
- 图片使用相对路径（非 base64），HTML 可与目录一同迁移
- JS 纯内联，零依赖
- 不加载外网字体或 CDN

理由：用户会将这些 HTML 分发给编辑、合作者，或在无网环境下查阅。

---

## OCR 引擎接入

### MinerU v4

`skills/ocr-run/scripts/mineru_client.py`

关键流程：

1. **上传**：本地 PDF → catbox.moe（匿名公共文件，24h 过期）→ 拿到 URL
2. **提交**：`POST /api/v4/extract/task`，payload 仅含 `url / is_ocr / enable_formula / enable_table`
3. **轮询**：`GET /api/v4/extract/task/<id>` 每 10s 直到 `state=done`
4. **下载**：从 `full_zip_url` 下载 zip，解 `full.md` → `raw.md`，图片 → `assets/`

Response envelope：`{"code": 0, "data": {...}, "msg": "..."}`——`code != 0` 视为错误。

**已知限制**：catbox.moe 中转会让 PDF 短暂公开。后续版本应切到 `POST /api/v4/file-urls/batch` 直接上传。

### 百度 OCR

`skills/ocr-run/scripts/baidu_client.py`

流程：

1. API Key + Secret Key → OAuth `/oauth/2.0/token` 拿 access_token
2. Token 缓存到 `~/.cache/baidu_ocr_token.json`（24h TTL，虽然 token 本身 30d 有效）
3. 每页 PNG → base64 → `POST /rest/2.0/ocr/v1/accurate_basic`（高精度版）
4. JSON 响应里 `words_result[].words` 为每行，自己拼段落（`merge_lines` 启发式）

**百度的段落切分**依赖 `merge_lines` 中的终止符规则。若出现"一行一段"现象，建议切换 MinerU 重跑。

---

## proofread Agent 的 Reference 加载

三份 reference 按文献类型**单独加载**，避免不相关知识干扰 agent 判断：

| 类型 | Reference |
|------|-----------|
| `classics` | `skills/proofread/references/traditional-classics.md`（异体字表、避讳字表、版心符号处理） |
| `republican` | `skills/proofread/references/republican-era.md`（新旧字形、旧式标点、译名过渡表） |
| `modern` | `skills/proofread/references/modern-chinese.md`（OCR 经典混淆对、标点规范、引文格式） |

`proofread` skill 的 Step 3 根据类型只读其中一份进上下文。

---

## 扩展点

新增功能的挂载点：

| 扩展目标 | 修改位置 |
|---------|-------|
| 新增期刊 Word 模板 | `skills/to-docx/scripts/md_to_docx.py` 的 `TEMPLATES` dict |
| 新增 OCR 引擎 | 新建 `skills/ocr-run/scripts/<name>_client.py`，并在 ocr-run SKILL 中增加分支 |
| 新增文献类型的 reference | `skills/proofread/references/<type>.md`，并在 agent 与 skill 中注册该类型 |
| 新增公众号样式主题 | `skills/mp-format/scripts/md_to_wechat.py` 的 `STYLE_*` 常量 |
| 新增批量扫描规则（如段末分号断裂） | `agents/historical-proofreader.md` 的 Step 1.6 或 Step 4 |
| 扩展 diff-review 的锚点解析（多 Line 号） | `skills/diff-review/scripts/md_diff.py` 的 `parse_review` |

---

## 测试

当前无自动化测试。手动验证流程：

1. 将一份真实论文 PDF 置于 `~/Downloads/`
2. 依次执行 prep-scan → visual-preview → ocr-run → proofread → diff-review → to-docx → mp-format
3. 每一步核验：产物是否生成、HTML 是否可打开、汇总数字是否合理

后续规划：

- [ ] `tests/fixtures/` 收录若干标准 PDF 样本
- [ ] 单元测试覆盖核心函数（`split_paragraphs`、`extract_key_chars`、`compute_diff_heatmap`）
- [ ] 端到端集成测试

---

## 版本

当前：v0.1.0（初始版本）

见 [.claude-plugin/plugin.json](../.claude-plugin/plugin.json) 和 git tag。

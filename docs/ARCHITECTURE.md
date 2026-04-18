---
title: Architecture
description: historical-ocr-review 插件的内部架构、数据流、skill 职责边界、设计决策
author: Claude Opus 4.7
date: 2026-04-19
status: v0.1.0
---

# Architecture

这份文档写给想读懂插件内部、想扩展 / 修改 / 调试插件的人。面向用户的使用指南见 [README.md](../README.md)。

---

## 顶层结构

```
historical-ocr-review/
├── .claude-plugin/plugin.json      插件 manifest（name / version / author）
├── README.md                       用户入口
├── AGENTS.md                       给未来接管的 agent 看
├── INSTALL.md                      三个宿主的装法
├── docs/
│   ├── ARCHITECTURE.md             本文
│   └── TROUBLESHOOTING.md          常见报错
├── agents/
│   └── historical-proofreader.md   唯一的 subagent（校对专家）
└── skills/
    ├── setup/                      首次配置
    ├── prep-scan/                  PDF 预处理
    ├── visual-preview/             清理效果可视化
    ├── ocr-run/                    OCR 识别
    ├── proofread/                  校对（调 agent）
    ├── diff-review/                校对核对
    ├── to-docx/                    Word 生成
    └── mp-format/                  公众号 HTML
```

每个 skill 目录结构：

```
skills/<name>/
├── SKILL.md                        触发词 + 工作流规范（给 agent / 用户看）
├── scripts/                        Python 可执行工具
│   └── *.py
└── references/                     知识库（仅 proofread 有）
    └── *.md
```

---

## 数据流

一份扫描 PDF 从头到尾产生的文件：

```
~/Downloads/
└── 论文.pdf                        [原件，永不动]
    ├── 论文.prep/
    │   ├── original.pdf            [prep-scan 备份]
    │   ├── pages/
    │   │   ├── page_001.png        [split_pages.py 拆页，300 DPI]
    │   │   └── …
    │   ├── cleaned_pages/
    │   │   ├── page_001.png        [dewatermark + remove_margins 清理后]
    │   │   └── …
    │   ├── diff_pages/
    │   │   ├── page_001.png        [visualize_prep.py 差异热图]
    │   │   └── …
    │   ├── cleaned.pdf             [pages_to_pdf.py 合回 PDF]
    │   └── visual-preview.html     [visual-preview 可视化]
    └── 论文.ocr/
        ├── raw.md                  [OCR 原始]
        ├── raw.review.md           [proofread 标注清单]
        ├── final.md                [用户校对定稿]
        ├── diff.html               [diff-review HTML]
        ├── diff.summary.md         [diff-review 摘要]
        ├── final.docx              [to-docx 产物]
        ├── final.mp.html           [mp-format 产物]
        ├── final.mp.md             [秀米兼容 markdown]
        ├── preview.html            [ocr-run 对照预览]
        ├── meta.json               [OCR 元信息]
        └── assets/
            └── figN.png            [OCR 提取的插图]
```

**命名约定**：
- `.prep/` = prep-scan 产物
- `.ocr/` = OCR 及后续产物
- `raw.*` = 原始 / 自动产出
- `final.*` = 用户定稿 / 最终交付

**不变原则**：原 PDF 永不动；所有中间产物放在 PDF 同级目录；可以整体复制 `.prep/` 或 `.ocr/` 到任何地方（相对路径设计）。

---

## Skill 依赖关系

```
             setup
               │ （配 ~/.env 的 API key）
               ▼
            prep-scan ──→ pages/ + cleaned_pages/ + cleaned.pdf
               │                    │
               │                    ▼
               │             visual-preview  [质检闸门]
               ▼
            ocr-run  ──→ raw.md + preview.html + meta.json
               │
               ▼
           proofread  ──→ raw.review.md
             (调 historical-proofreader agent)
               │
               │ （用户按清单改）
               ▼
             final.md
               │
               ▼
          diff-review  [质检闸门]  ──→ diff.html + summary.md
               │
               ▼
         ┌─────┴─────┐
         ▼           ▼
      to-docx    mp-format
         │           │
         ▼           ▼
     final.docx  final.mp.html
```

**三个质检闸门** 是设计要点：

1. **visual-preview**（prep 之后）——看清理有没有误伤正文
2. **proofread 的 Checklist 执行证明表**——证明 agent 真跑了字形扫描
3. **diff-review**（改完之后）——看接受了哪些、漏改了哪些

闸门失效 = 黑盒交付。插件的定位是让 JN 在每一步都能复查，不是"全自动"。

---

## 核心设计决策

### 1. SKILL.md 写契约，脚本遵守契约

每个 SKILL.md 里明确写 "脚本必须实现 X / Y / Z"。脚本是契约的实现，不是 SKILL 的另一种表述。这防止文档和代码长期漂移（插件的通病是 SKILL 说能做，脚本其实不做）。

### 2. Agent 走强制 checklist 而不是 "系统过一遍"

早期版本的 `historical-proofreader` agent 工作流是 "按顺序过完全文，每读到以下模式就标一条"。实测会漏掉 reference 里明确列过的经典错（比如"曰/日"），因为 agent 靠印象抽样。

现在改成 **Step 1-4 每步列具体 `grep` 命令，报告里必须附 Checklist 执行证明表**（每项命中数）。这是给 agent 的"执行审计"，漏跑一项能从报告里看出来。

### 3. 路径编码兜底

macOS 上 `cv2.imread` 对含中文路径的某些 PNG 会返回 None（同目录下有的读得到有的读不到）。所有脚本的图像 I/O 走 `cv2.imdecode(np.fromfile(...))` / `cv2.imencode + tofile` 绕过路径编码。见 [skills/visual-preview/scripts/visualize_prep.py](../skills/visual-preview/scripts/visualize_prep.py) 的 `imread_unicode` / `imwrite_unicode`。

### 4. OCR 双引擎 fallback

MinerU 对繁体竖排古籍更准，百度对现代简体更稳、配额大。`~/.env` 的 `OCR_ENGINE` 决定默认引擎，`--engine=xxx` 可临时覆盖——方便用户对比两引擎效果或降级切换。

### 5. diff-review 的 "接近" 判定

判定 JN 是否接受 agent 建议时，**不做精确字符串匹配**。策略：从建议里抽关键字符（如 "研完 → 研究" 里的 "究"），如果 final 段落包含这些字符且 raw 不包含 → 判为接受。理由：JN 常采纳方向但用自己的措辞改，精确匹配会把"同向但换词"误判为拒绝。

### 6. 所有 HTML 单文件离线

preview.html / diff.html / visual-preview.html 都是单文件：

- 内联 CSS，无外链 style sheet
- 图片用相对路径（不 base64），HTML 跟目录一起挪可打开
- JS 纯内联，零依赖
- 不加载外网字体 / CDN

理由：JN 会把这些 HTML 发给编辑、合作者、在没网的地方看。

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

**百度的段落切分**靠 `merge_lines` 里的终止符规则。识别出一行一段时建议切 MinerU 重跑。

---

## proofread Agent 的 Reference 加载

三份 reference 按文献类型**单独加载**，避免 agent 被不相关知识干扰：

| 类型 | Reference |
|------|-----------|
| `classics` | `skills/proofread/references/traditional-classics.md`（异体字表、避讳字表、版心符号处理） |
| `republican` | `skills/proofread/references/republican-era.md`（新旧字形、旧式标点、译名过渡表） |
| `modern` | `skills/proofread/references/modern-chinese.md`（OCR 经典混淆对、标点规范、引文格式） |

`proofread` skill 的 Step 3 根据类型只读其中一份进上下文。

---

## 扩展点

想加新功能时的挂载点：

| 想做什么 | 改哪里 |
|---------|-------|
| 加新的期刊 Word 模板 | `skills/to-docx/scripts/md_to_docx.py` 的 `TEMPLATES` dict |
| 加新的 OCR 引擎 | 新建 `skills/ocr-run/scripts/<name>_client.py` + 在 ocr-run SKILL 里加分支 |
| 加新文献类型的 reference | `skills/proofread/references/<type>.md` + 在 agent / skill 里加类型 |
| 加公众号样式主题 | `skills/mp-format/scripts/md_to_wechat.py` 的 `STYLE_*` 常量 |
| 加新的批量扫描（如段末分号断裂） | `agents/historical-proofreader.md` 的 Step 1.6 或 Step 4 |
| 扩展 diff-review 的锚点解析（多 Line 号） | `skills/diff-review/scripts/md_diff.py` 的 `parse_review` |

---

## 测试

当前无自动化测试。手动验证流程：

1. 放一份真实论文 PDF 到 `~/Downloads/`
2. 依次跑 prep-scan → visual-preview → ocr-run → proofread → diff-review → to-docx → mp-format
3. 每一步检查：产物是否生成、HTML 能打开、汇总数字合理

未来应加：

- [ ] `tests/fixtures/` 放几份标准 PDF 样本
- [ ] 单元测试核心函数（`split_paragraphs`、`extract_key_chars`、`compute_diff_heatmap`）
- [ ] 端到端集成测试

---

## 版本

当前：v0.1.0（初始版本）

见 [.claude-plugin/plugin.json](../.claude-plugin/plugin.json) 和 git tag。

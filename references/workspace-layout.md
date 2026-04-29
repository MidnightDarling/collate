---
title: Workspace Layout — 一份文献一个工作区
date: 2026-04-19
author: Claude Opus 4.6
status: authoritative
---

# Workspace Layout —— 一份文献 = 一个 `.ocr/` 工作区

> 这是 **collate** 插件的工作区布局权威规范。
> 所有 skill、script、agent 都必须遵守此文件定义的目录约定。
> 有歧义时以本文件为准，不以 SKILL.md 为准。

## 问题

2026-04-19 Codex 端到端测试暴露出一个设计缺口：

> 过程中没有指导 agent 如何收拾文档，会导致东西乱放。

症状：

- `.prep/` 和 `.ocr/` 分散在 PDF 同级，两个目录容易被当成"两份产物"误删
- `preview.html`、`diff-review.html`、`raw.review.md`、`diff-summary.md` 全部平铺在 `.ocr/` 根目录，用户找"最终稿"要先跳过一堆过程文档
- `mineru_full.md`、`_import_provenance.json` 是 pipeline 簿记文件，对用户零价值，却和 `raw.md` 并列在根目录
- docx / 公众号 HTML 会输出到 `final.md` 的同级目录，污染用户原始文件夹

## 原则

1. **一份文献一个工作区**。`<basename>.ocr/` 是唯一对外可见的目录，所有相关产物都在其中。不再有独立的 `.prep/`。
2. **根目录只放"当前状态"**。用户打开 `.ocr/` 第一眼看到的是本次处理的定稿、元数据、README。过程产物全部藏进子目录。
3. **过程产物分类藏匿**。按"给谁看、什么时候看"划分子目录：预览给人眼看、review 给校对看、prep 给回滚看、_internal 给 pipeline 看。
4. **output/ 是交付区**。最终 docx / 公众号 HTML 集中放在 `output/`，是"可以直接发出去"的东西，不和中间态混。
5. **README.md 是目录地图**。每次 skill 跑完，自动重写 `.ocr/README.md` 列出当前目录内每个文件/子目录的作用。用户不必记住本规范。
6. **幂等可重跑**。任何 skill 重跑都覆盖同名产物，不产生 `_v2` `_new` `_final2`。版本管理交给 git 或用户手动备份。

## 目录结构（权威定义）

```
<pdf-basename>.ocr/
├── README.md                   ⟵ 自动生成，本目录的地图（workspace_readme.py）
├── source.pdf                  ⟵ 被处理的 PDF（prep-scan 的 cleaned.pdf 或用户原始 PDF）
├── raw.md                      ⟵ OCR 产出的原始 Markdown（含 <!-- page N --> 标记）
├── final.md                    ⟵ 用户按 raw.review.md 修改后的定稿（用户自己放）
├── meta.json                   ⟵ OCR 元数据（engine/pages/low_confidence_pages/...）
├── assets/                     ⟵ OCR 提取的图片（图表、古籍插图）
│
├── prep/                       ⟵ 预处理中间态（prep-scan 的工作区）
│   ├── original.pdf            ⟵ 用户原始 PDF 备份（未去水印、未裁边）
│   ├── pages/                  ⟵ 逐页 PNG（原始）
│   ├── cleaned_pages/          ⟵ 逐页 PNG（去水印后、未裁边）
│   ├── trimmed_pages/          ⟵ 逐页 PNG（去水印 + 裁边）
│   └── cleaned.pdf             ⟵ 合回的 PDF（= 根目录的 source.pdf 来源）
│
├── previews/                   ⟵ 可视化 HTML（人眼审查用）
│   ├── visual-prep.html        ⟵ prep-scan 前后对比（visual-preview skill）
│   ├── ocr-preview.html        ⟵ 原图 + OCR 文本并排（ocr-run skill）
│   └── diff-review.html        ⟵ raw → final 段落级 diff（diff-review skill）
│
├── review/                     ⟵ 校对产出（proofread + diff-review 的文本报告）
│   ├── raw.review.md           ⟵ proofread 的 A/B/C 标注清单
│   └── diff-summary.md         ⟵ diff-review 的改动统计
│
├── _internal/                  ⟵ Pipeline 簿记（对用户零价值、但出问题时调试用）
│   ├── mineru_full.md          ⟵ MinerU 原生 Markdown（reflow 前）
│   └── _import_provenance.json ⟵ 导入来源 / 标题作者年份识别结果
│
└── output/                     ⟵ 最终交付物（可直接发出去）
    ├── <title>_<author>_<year>_final.docx    ⟵ to-docx skill
    ├── <title>_<author>_<year>_wechat.html   ⟵ mp-format skill（公众号版）
    └── <title>_<author>_<year>_wechat.md     ⟵ mp-format skill（秀米版）
```

## 根目录 vs 子目录 —— 每个文件属于哪

判断某个文件应该放在哪一层，按这个顺序问：

1. **用户打开 `.ocr/` 想立刻看到它吗？** → 根目录
   - `raw.md`, `final.md`, `meta.json`, `source.pdf`
   - `README.md`（自动生成的目录地图）

2. **是交付给读者的成品吗？** → `output/`
   - docx、公众号 HTML、秀米 MD

3. **是一份给人肉眼核查的 HTML 预览吗？** → `previews/`
   - 所有 `*.html`（visual-prep / ocr-preview / diff-review）

4. **是一份带结论的 Markdown 报告吗？** → `review/`
   - `raw.review.md`（proofread 清单）、`diff-summary.md`

5. **是图像中间态（prep 每一步的逐页 PNG）吗？** → `prep/`

6. **是 pipeline 内部簿记、只在 debug 时有用吗？** → `_internal/`
   - 前缀 `_` 让它在列表末尾，暗示"内部"

7. **是 OCR 抽出的 asset（图片等）吗？** → `assets/`（根目录下，和 `raw.md` 并列）
   - 原因：`raw.md` 里的图片引用是 `assets/xxx.png`，相对路径必须保持

## 文件命名约定

### 根目录固定文件名

| 文件 | 来源 | 可变名吗 |
|------|------|---------|
| `source.pdf` | prep-scan 的 `cleaned.pdf`，或用户直接传给 ocr-run 的 PDF | 否 |
| `raw.md` | OCR 产出 | 否 |
| `final.md` | 用户按 raw.review.md 改完自己命名 | 否（此名被 diff-review 依赖） |
| `meta.json` | OCR 产出 | 否 |
| `README.md` | workspace_readme.py 自动生成 | 否 |

### output/ 命名规则

```
<title>_<author>_<year>_<kind>.<ext>
```

- `<title>` `<author>` `<year>`：从 `_internal/_import_provenance.json` 读。缺失时用 `未知标题` / `未知作者` / `未知年份`。
- `<kind>`：
  - `final` → docx（学界版）
  - `wechat` → HTML（公众号版）
  - 下划线纯 ASCII，中文字符直接用，去掉 `<>:"/\|?*` 等文件系统非法字符

示例：

```
观念的历史解读与话语的历史建构_向燕南_2024_final.docx
观念的历史解读与话语的历史建构_向燕南_2024_wechat.html
观念的历史解读与话语的历史建构_向燕南_2024_wechat.md
```

## 路径推导算法（所有 skill 必须一致）

给定用户传入的 PDF 或 Markdown 路径 `INPUT`，工作区根 `$OCR` 按以下规则推导：

```bash
# 情况 A：INPUT 是 PDF
if [[ "$INPUT" == *.pdf ]]; then
    DIR=$(dirname "$INPUT")
    BASE=$(basename "$INPUT" .pdf)
    OCR="$DIR/$BASE.ocr"

# 情况 B：INPUT 是 Markdown 在 .ocr/ 下
elif [[ "$INPUT" == */*.ocr/*.md ]]; then
    OCR="${INPUT%/*.md}"      # 去掉最后一个 /xxx.md

# 情况 C：INPUT 在 .ocr/ 子目录下（例如 .ocr/review/raw.review.md）
elif [[ "$INPUT" == */*.ocr/*/*.md ]]; then
    OCR="${INPUT%/*/*.md}"    # 去掉最后两层

# 情况 D：不在 .ocr/ 里（旧文件或用户手放的）
else
    # 报错或降级：告诉用户 "没找到 .ocr 工作区，先跑 ocr-run"
    OCR=""
fi
```

所有 skill 的输出路径推导必须走此算法。不得在 SKILL.md 里写 hardcoded 的 `${INPUT%.md}.html`（那会把文件落在 `.ocr/` 根部）。

## 重跑协议（Rerun Protocol）

用户重跑某个 skill 时，产物应**幂等覆盖**，不生成 `_v2` 后缀：

| Skill | 覆盖的文件 | 保留不动的文件 |
|-------|-----------|---------------|
| prep-scan | `prep/` 全部、`source.pdf`（= cleaned.pdf） | `raw.md`, `final.md`, `review/`, `output/` |
| ocr-run | `raw.md`, `meta.json`, `assets/`, `_internal/`, `previews/ocr-preview.html` | `prep/`, `final.md`, `review/`, `output/` |
| proofread | `review/raw.review.md` | 其他全部 |
| diff-review | `previews/diff-review.html`, `review/diff-summary.md` | 其他全部 |
| to-docx | `output/<...>_final.docx` | 其他全部 |
| mp-format | `output/<...>_wechat.html`, `output/<...>_wechat.md` | 其他全部 |
| visual-preview | `previews/visual-prep.html`, `prep/diff_pages/` | 其他全部 |

例外：`raw.md` 被 ocr-run 覆盖前先备份为 `raw.md.bak`（apply_corrections 也遵循此规则）。

## README.md 自动生成规则

每次 skill 跑完，由 `scripts/workspace_readme.py` 重写 `.ocr/README.md`。README 内容：

1. **头部**：文献标题（从 `_internal/_import_provenance.json` 读）、作者、年份、生成时间
2. **当前状态**：一张表列根目录内每个文件/目录是什么、是否存在、可选大小
3. **子目录地图**：遍历 `previews/` `review/` `prep/` `_internal/` `output/`，列出内容
4. **下一步建议**：根据已有文件推荐 —— 有 `raw.md` 无 `review/raw.review.md` → 建议 `/proofread`；有 `final.md` 无 `output/*_final.docx` → 建议 `/to-docx`

README.md 永远是"当前工作区状态快照"。用户不需要记住本规范：打开 README 就知道这个工作区处于 pipeline 的哪一步。

## 迁移：旧布局 → 新布局

存量 `.prep/` 和 `.ocr/` 目录怎么办？

- **新跑的文献**：直接按本规范生成新布局。
- **旧存量**：不自动迁移。用户若想整理，手动移动：
  ```bash
  mv foo.prep foo.ocr/prep
  mv foo.ocr/preview.html foo.ocr/previews/ocr-preview.html
  mv foo.ocr/raw.review.md foo.ocr/review/raw.review.md
  mv foo.ocr/mineru_full.md foo.ocr/_internal/mineru_full.md
  mv foo.ocr/_import_provenance.json foo.ocr/_internal/
  ```
  迁完跑一次 `workspace_readme.py` 重建 README。

SKILL 不做自动迁移 —— 自动迁移意味着要处理部分迁完的中间态，逻辑复杂度不匹配"整理文档"的初衷。

## 不做的事

- 不创建 `.ocr/`**同级**的任何目录（例如 PDF 同目录不生成 `<base>.prep/`）。
- 不在 `.ocr/` 根直接写除本规范指定文件外的任何东西。
- 不留 `_v2` `_backup` `_old` 后缀（哪怕"出于保险"）。备份由 git 或 `raw.md.bak` 一条专门规则处理。
- 不嵌 base64 大图到 HTML（`previews/` 里所有 HTML 引用 `../prep/pages/` 或 `../assets/` 的相对路径）。

## 更新本规范

本规范改动需满足：

1. 先在 PR 描述里写清楚"为什么改布局"；
2. 同步更新所有 SKILL.md + `workspace_readme.py` + 相关 scripts；
3. 在"迁移"一节追加新规则的迁移步骤。

不允许 SKILL.md 单独偏离本规范。发现偏离视为 bug，回滚或同步。

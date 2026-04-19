---
name: diff-review
description: 使用场景：按 raw.review.md 清单改完稿后，对 raw.md（OCR 原始）和 final.md（定稿）做对比。说"看我改了哪些""对比一下""diff""校对完了让我看看""我到底接受了哪些建议""我漏改了啥""改动统计""核对一下改动""闭环检查"都走这个 skill。生成段落级 HTML diff，关联 raw.review.md 的 A/B/C 标注，一目了然：接受了哪些 agent 建议、拒绝了哪些、清单外修正了哪些、agent 标过但漏改了哪些。主动触发，不必等用户说 "diff-review"。
argument-hint: "<raw-md-path> <final-md-path> [--review=<raw.review.md 路径>]"
allowed-tools: Read, Write, Edit, Bash
---

# Diff Review — 校对改动核对

## Task

校对闭环的最后一关。用户按 raw.review.md 改完 raw.md → final.md 后，用户需要回答三个问题：

1. **用户接受了 agent 的哪些建议？**（自己脑子里记不住改了哪些）
2. **用户拒绝或漏改了哪些？**（最常见：手滑漏掉一两条 A 类）
3. **清单外修正了哪些 agent 未标注的段？**（用于积累校对风格）

不核对就改，等于校对没闭环——用户可能漏了明显的 OCR 错就拿去生成 Word，回头被编辑或读者发现，返工。

这个 skill 生成一份**段落级 HTML 对照 + 标注交叉表**，用户花 5 分钟扫一遍就能判断闭环是否闭上。

---

## Process

### Step 1 — 确认输入

```bash
RAW="<raw-md-path>"
FINAL="<final-md-path>"
OCR="$(dirname "$RAW")"                # 工作区根 = raw.md 的父目录
REVIEW="${REVIEW:-$OCR/review/raw.review.md}"

test -f "$RAW"   || { echo "raw.md 不存在：$RAW"; exit 1; }
test -f "$FINAL" || { echo "final.md 不存在：$FINAL"; exit 1; }
# review 可选；无则降级为纯 diff
```

如果用户没显式传 `--review`，默认去 `$OCR/review/raw.review.md` 找清单（proofread 的默认输出位置）。找到就带上，找不到降级为纯 diff，不做标注关联，并告知用户。

### Step 2 — 调 diff 脚本

```bash
mkdir -p "$OCR/previews" "$OCR/review"
python3 "${CLAUDE_PLUGIN_ROOT}/skills/diff-review/scripts/md_diff.py" \
    --raw "$RAW" \
    --final "$FINAL" \
    $( [ -f "$REVIEW" ] && echo "--review $REVIEW" ) \
    --out "$OCR/previews/diff-review.html" \
    --summary "$OCR/review/diff-summary.md"
```

> **固定路径约定**（权威规范见插件 `references/workspace-layout.md`）：
> - HTML 预览 → `previews/diff-review.html`
> - Markdown 摘要 → `review/diff-summary.md`
> 不再用 `${FINAL%.md}.diff.html` 这种衍生路径 —— 那会把过程文件落在工作区根部，反规范。

### Step 3 — 脚本必须实现的行为规范

md_diff.py 的职责边界由以下规范**强制定义**。实现时不许偷工——以下每条都是契约，不是建议。

#### 3.1 段落切分

两份文件都按「连续非空行 = 一段」规则切分。每段保留：
- `raw_line_start` / `raw_line_end`（在 raw.md 中的起止行号）
- `final_line_start` / `final_line_end`（在 final.md 中的起止行号）
- `paragraph_text`（段落文本，保留段内换行）

保留原始行号是为了和 raw.review.md 的 "Line N" 标注做锚定。

#### 3.2 段落对齐

用 `difflib.SequenceMatcher` 以**段落为 opcode 粒度**（不是行、不是字符）做对齐。产出四类 opcode：

| opcode | 含义 | HTML 显示 |
|--------|------|----------|
| `equal` | 段落完全一致 | 折叠，默认只显示"第 N 段未修改"，可展开查看 |
| `replace` | 段落被改写 | 左栏 raw（删除高亮）+ 右栏 final（新增高亮），段内做字符级 diff |
| `delete` | raw 有 final 无 | 左栏显示 + 标签"已删除整段" |
| `insert` | final 有 raw 无 | 右栏显示 + 标签"新增段落" |

**不允许用行级对齐**。中文一段可能 300 字一行，行级 diff 会把"改一个字"显示为"删一整行 + 增一整行"，噪音压过信号。

#### 3.3 段内字符级 diff

对每个 `replace` 段，用 `difflib.ndiff` 或 `SequenceMatcher` 做字符级对齐。高亮规则：

- 删除字符：`<del style="background:#fbe5d6;color:#a33;">X</del>`
- 新增字符：`<ins style="background:#d4edda;color:#161;text-decoration:none;">Y</ins>`
- 不变字符：普通文本

#### 3.4 关联 review.md 的标注

若传入 `--review`：

**3.4.1 解析 review.md**

raw.review.md 里每条 A/B/C 标注遵循固定格式：

```
### A3. <标题> · Line <N>

**原文**：
> <片段>

**建议**：<改法>
```

提取字段：`category (A/B/C)`、`item_id (A3)`、`line_number (N)`、`fragment (原文片段)`、`suggestion (建议)`。

标题级别必须是 `###`，命中行正则：`^###\s+([ABC]\d+)\.\s+(.+)\s+·\s+Line\s+(\d+)`（兼容"全文"、"多行"等无具体行号的条目，line_number 为 `null`）。

**3.4.2 标注映射到段落**

把每条标注的 `line_number` 映射到 raw.md 的段落（该行落在哪个段的 `raw_line_start..raw_line_end` 范围内）。

**3.4.3 每条标注打状态**

| 状态标签 | 判定逻辑 |
|---------|---------|
| `accepted` | 标注所在段在 final.md 被改写，且改动**接近** agent 建议 |
| `rejected_or_missed` | 标注所在段在 final.md 未被改写（opcode=equal） |
| `outside_fix` | 段落被改写但没有任何 agent 标注锚在该段 |
| `unanchored` | review.md 条目 line_number 为 null（如"全文标点混用"），列为参考不打状态 |

**"接近"判定**：不要求精确字符匹配。策略：
- agent 建议里抽取关键改动字符（如"研完 → 研究"里的"究"、"自已 → 自己"里的"己"、"（观念史》 → 《观念史》"里的"《"）
- 若 final.md 对应段落里出现这些关键字符，且 raw.md 对应位置没有 → 判为接受
- 复杂判定不了 → 保守判为 `rejected_or_missed`，让用户自己看

不精确匹配的原因：用户经常采纳方向但换措辞（agent 说"改为「这是重要的」"，用户写成了"「此乃要害」"）。

#### 3.5 统计总结（输出 `<final>.diff.summary.md`）

```markdown
# Diff 总结：<final 文件名>

**修改段落数**：N / 总段落数 M（改动率 X%）
**字符级改动**：删 X 字 / 增 Y 字 / 净 +Z 字
**接受 agent 建议**：N / 共 M 条有锚标注（X%）
**拒绝或漏改**：N 条 —— 重点核！
**清单外修正**：N 处

---

## 接受的 agent 建议

- A1（脚注 `[`）：命中 N 处，接受 M 处
- A3（自已 → 自己）：Line 87 接受
- ...

## 拒绝或漏改 —— 重点核

- A5（书名号《》）：Line 127 未改 —— 可能漏了
- B1（标题全 H1）：全文仍是 H1，未降级 —— 会影响 to-docx
- ...

## 清单外修正（agent 未标注的段）

- Line 45：raw "涉及" → final "关涉"（语义微调）
- Line 102：新增脚注 [43]
- ...

## 未锚定标注（参考，不计状态）

- A6（全半角逗号 · 全文）
- ...
```

#### 3.6 HTML 布局

顶部工具条：
- 文件名 + 修改段数 / 总段数
- 接受 N 条 / 拒绝 M 条 / 清单外 K 处（每个数字点击跳对应区）
- "展开所有未修改段" 按钮
- "导出 Markdown 摘要" 按钮（下载 summary.md）

主体：按段落顺序渲染，每段一个 `<section>`：

```
┌─────────────────────────────────────────────────────────┐
│  段 3 · replace · [接受 A5]                              │
│  ┌──────────────────┐  ┌──────────────────┐           │
│  │ raw (L127-127)   │  │ final (L127-127) │           │
│  │ （大清国致大英   │  │ 《大清国致大英   │           │
│  │  国国书》...     │  │  国国书》...     │           │
│  └──────────────────┘  └──────────────────┘           │
│  关联标注：A5 书名号《》 · 建议「（→《」               │
│  判定：关键字 '《' 出现在 final 段 → 接受                │
└─────────────────────────────────────────────────────────┘
```

样式要求：
- 全内联 CSS，单文件离线可读
- 不加载外部字体 / 图片 / 脚本
- 配色与 preview.html / visual-preview.html 一致（ATTRIBUTION° Ink Stone 暗底）：背景 `#0E0E11`，正文 `#E0DCD6`，副文字 `#9A9690`，删除块 `#2A1A1A` 底 + `#C49494` 字，新增块 `#1A2420` 底 + `#A8C4B4` 字，强调色 `#D4BE94`

#### 3.7 打开输出

```bash
open "$OCR/previews/diff-review.html"
```

### Step 4 — 刷新 README + 向用户报告

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace_readme.py" --workspace "$OCR"
```

```
核对完成：

- 总改动：N 段 / 字符 +X -Y
- 接受 agent 建议：X 条
- 拒绝或漏改：Y 条 ← 重点看
- 清单外修正：Z 处

打开了：$OCR/previews/diff-review.html
摘要：  $OCR/review/diff-summary.md

建议先看「拒绝或漏改」一节——确认是有意拒绝还是手滑漏掉。
```

---

## 脚本接口规范（md_diff.py 契约）

```
输入：
  --raw PATH         raw.md 路径（必需）
  --final PATH       final.md 路径（必需）
  --review PATH      raw.review.md 路径（可选，缺省降级为纯 diff）
  --out PATH         HTML 输出路径（必需）
  --summary PATH     Markdown 摘要输出路径（可选）
  --expand-equal     是否默认展开未修改段（默认 False）

退出码：
  0   成功
  2   输入文件不存在
  3   段落对齐异常（raw/final 段落数差 > 80%）
  4   review.md 格式无法解析（降级为纯 diff 后继续，返回 0 但 stderr 警告）
  5   其他

输出文件：
  - HTML：单文件离线可读，UTF-8
  - Markdown summary：按 3.5 规范
```

---

## 判断规则

- **raw == final**：不生成空 HTML，直接告诉用户 "文件完全一致，无修改"，退出 0
- **段落数差 > 50%**：提醒用户 "final.md 比 raw.md 段落数差太多，你改的是同一版 raw 吗？"。若用户确认是同一版，继续；若不是，让用户换版本
- **agent 标了 N 条 A 类但一条都没接受**：标红警告 "A 类是极可能的 OCR 错（建议接受），现在 0 条接受——确认下是不是你没看这份 review？"
- **review.md 格式解析失败**：告诉用户 "我看不懂这份 review.md 的格式，可能是旧版 agent 产物。这次先只做纯 diff，不关联标注"

## 失败兜底

- Python `difflib` 缺失 → Python 标准库自带，几乎不会缺；报错通常是 Python 版本 < 3.6 → 让用户 `brew install python@3.11`
- 编码不一致（raw 或 final 非 UTF-8）→ 强制 UTF-8 打开，失败则报错并指出具体字节位置
- 段落切分遇到特殊情况（全文一行无换行）→ 退化为字符级 diff，不按段落

## 与其他 skill 的关系

**上游**：proofread 产 raw.review.md，本 skill 读作标注参考
**下游**：to-docx / mp-format 跑之前强烈建议先跑一次 diff-review

推荐的完整闭环：

```
<ws>.ocr/raw.md     ──→  proofread  ──→  <ws>.ocr/review/raw.review.md
                         ↓（用户按清单改 raw.md，保存为）
                       <ws>.ocr/final.md
                         ↓
                    diff-review  ← 这一步核对闭环
                         ↓（确认无漏改）
              <ws>.ocr/previews/diff-review.html
              <ws>.ocr/review/diff-summary.md
                         ↓
              to-docx + mp-format → <ws>.ocr/output/
```

diff-review 是**校对质量闸门**，属于流程必经步骤：改完 final.md 后先跑 diff，再进入 to-docx / mp-format。

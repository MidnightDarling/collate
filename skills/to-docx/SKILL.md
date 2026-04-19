---
name: to-docx
description: 使用场景：用户运行 `/historical-ocr-review:to-docx`、对校对好的 Markdown 说"转成 Word""生成 docx""出一份 Word 稿""学界交流用""期刊投稿版本""给编辑看"等。这个 skill 把校对定稿的 Markdown 转成 `.docx`：思源宋体正文、段首缩进两字、行距 1.2、字间距 0.2 pt、页边距上下左右全部 2 cm、脚注连续编号、中文引号规范、图表题注位置正确、参考文献独立一段。优先使用 Anthropic 的 `docx` skill（若可用）提供完整 OOXML 能力；fallback 到 bundled 的 md_to_docx.py（python-docx 实现）。**主动触发**：用户提到"Word"、"doc"、"文档"、"交给编辑"、"投稿格式"等都应走这个 skill。
argument-hint: "<markdown-path> [--font-size=12]"
allowed-tools: Read, Write, Edit, Bash
---

# Markdown → Word

## Task

把校对定稿的 Markdown 转成一份 `.docx`，供投稿、学界交流、编辑沟通使用。

输出规范（由 Alice 定义，所有输出一致）：

| 元素 | 规范 |
|------|------|
| 正文字体 | 思源宋体 / Source Han Serif |
| 标题字体 | 思源宋体加粗 |
| 正文字号 | 12 pt（小四） |
| 一级标题 | 16 pt（三号） |
| 二级标题 | 14 pt（四号） |
| 段首缩进 | 2 字符 |
| 行距 | 1.2 |
| 字间距 | 0.2 pt |
| 页边距 | 上下左右全部 2 cm |
| 页码 | 底部居中 |
| 脚注 | 连续编号，思源宋体 9 pt |
| 引号 | 中文「""''」 |

## Process

### Step 1：确认输入

```bash
INPUT="<markdown-path>"
test -f "$INPUT" || { echo "文件不存在"; exit 1; }
```

推荐用校对完的 `final.md`，不要直接用 `raw.md`（仍含 OCR 错）。

### Step 2：优先尝试 Anthropic 的 docx skill

检查 Claude Code 环境里 `anthropic-skills:docx` 或 `docx` skill 是否可用。如可用：

- 读 `<input>.md` 内容
- 按上表规范设置样式参数
- 调 anthropic docx skill 生成含标题层级、段首缩进、字体、页边距的 `.docx`
- 它能给出更精细的 OOXML 控制（真正的分页符、脚注链接、交叉引用）

### Step 3：Fallback — 用 bundled 脚本

Anthropic docx skill 不可用时（Kimi / MiniMax / 脱机环境等），跑：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/to-docx/scripts/md_to_docx.py" \
    --input "$INPUT" \
    --output "${INPUT%.md}.docx" \
    --title-from-first-h1
```

脚本用 `python-docx` 实现。支持：

- Markdown 标题 → 对应 Word Heading 样式
- 段首缩进 + 思源宋体 + 1.2 行距 + 0.2 pt 字间距
- 页边距上下左右全部 2 cm
- 中文引号自动规范
- 代码块 → Consolas 等宽
- 图片内嵌（从 `assets/` 读）
- 表格 → Word Table
- 脚注 `[^1]` → Word 原生脚注

### Step 4：题注与图表

Markdown 里的图片：

```markdown
![图 1：乾隆年间北京城图](assets/fig1.png)
```

脚本会：

- 图片居中
- 下方加题注"图 1：乾隆年间北京城图"（10 pt，居中）
- 跟随引用自动连续编号

表格同理：

```markdown
| 年份 | 事件 |
|------|------|
| 1840 | 鸦片战争 |

*表 1：近代史大事年表*
```

图表没有题注时不要自己编——留空让用户补。

### Step 5：脚注

校对好的 Markdown 里可能用：

```markdown
这是正文内容[^1]。

[^1]: 这是脚注内容。
```

脚本把 `[^n]` 变成 Word 原生脚注（每页底部显示，全文连续编号），不是 inline reference。

### Step 6：参考文献段

Markdown 最后一段若以「参考文献」「引用文献」「Bibliography」标题开头并跟列表，脚本识别为参考文献段，格式化为：

- 无段首缩进
- 悬挂缩进（第二行及以后缩 2 字）
- 按原顺序编号 `[1]` `[2]` `[3]` 依次

### Step 7：输出 + 报告

```bash
OUT="${INPUT%.md}.docx"
```

产出：

```
Word 稿已生成：$OUT
字数：N（不计脚注）
页数：约 M 页
```

```bash
open "$OUT"
```

## 判断规则

- 未校对的 raw.md 直接转 docx：OCR 错会被保留到正稿里，提示用户先跑 proofread
- 论文含复杂表格（跨页、合并格）：python-docx 处理有限，优先 Anthropic docx skill
- 论文含 LaTeX 公式：公式在 Word 里是图片，不是原生公式

## 失败兜底

- python-docx 报错 → Markdown 格式有问题（未闭合代码块、表格错位），回去修 Markdown
- 思源宋体缺失 → `brew install --cask font-source-han-serif-sc`（macOS）
- Anthropic docx skill 不可用且 python-docx 未装 → `pip3 install python-docx`

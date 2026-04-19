---
name: to-docx
description: 使用场景：用户运行 `/historical-ocr-review:to-docx`、对校对好的 Markdown 说"转成 Word""生成 docx""出一份 Word 稿""学界交流用""期刊投稿版本""标准学术格式""给编辑看"等。这个 skill 把校对定稿的 Markdown 转成**符合社科学术规范**的 Word 文档（.docx）：宋体正文 / 黑体标题、段首缩进两字、行距 1.5、脚注连续编号、中文引号规范、图表题注位置正确、参考文献独立一段。优先使用 Anthropic 的 `docx` skill（若可用）提供完整 OOXML 能力；fallback 到 bundled 的 md_to_docx.py（python-docx 实现）。**主动触发**：用户提到"Word"、"doc"、"文档"、"交给编辑"、"投稿格式"等都应走这个 skill。
argument-hint: "<markdown-path> [--template=humanities|sscilab|simple] [--font-size=12]"
allowed-tools: Read, Write, Edit, Bash
---

# Markdown → Word 学术规范稿

## Task

用户的 OCR + 校对工作是为了生成一份可以投稿 / 给编辑 / 学界交流的 Word 文档。这个 skill 负责这一步。

**为什么重要**：
- 中国社科类期刊 99% 要求 Word 格式投稿
- Word 是用户和编辑、审稿人、合作者的通用语言
- 公众号推送是副产品，Word 才是学术本体

输出：一份符合社科学术规范的 `.docx`。默认格式：

| 元素 | 规范 |
|------|------|
| 正文字体 | 宋体 / SimSun |
| 标题字体 | 黑体 / SimHei |
| 正文字号 | 12 pt（小四） |
| 一级标题 | 16 pt（三号） |
| 二级标题 | 14 pt（四号） |
| 段首缩进 | 2 字符 |
| 行距 | 1.5 |
| 页边距 | 上 2.54 / 下 2.54 / 左 3.18 / 右 3.18 cm |
| 页码 | 底部居中 |
| 脚注 | 连续编号，宋体 9 pt |
| 引号 | 中文「""''」 |

## Process

### Step 1：确认输入

```bash
INPUT="<markdown-path>"
test -f "$INPUT" || { echo "文件不存在"; exit 1; }
```

建议用校对完的 `final.md`（用户改过 `raw.md` 后的版本），不要直接用 `raw.md`（有 OCR 错）。如果用户传的是 raw.md，友好提醒用户："确认这是校对后的定稿吗？raw.md 还没校对过。"

### Step 2：优先尝试 Anthropic 的 docx skill

检查 Claude Code 环境里 `anthropic-skills:docx` 或 `docx` skill 是否可用。如可用：

- 读 `<input>.md` 内容
- 读模板（见 Step 4）的样式参数
- 调 anthropic docx skill，请求生成含标题层级、段首缩进、字体、页边距的 .docx
- 它能给出更精细的 OOXML 控制（比如真正的分页符、脚注链接）

**为什么优先**：Anthropic 的 docx skill 对 OOXML 结构有完整控制，尤其脚注、交叉引用、表格合并格，比 python-docx 干净。

### Step 3：Fallback — 用 bundled 脚本

如果 Anthropic docx skill 不可用（在 Kimi / MiniMax 或脱机环境），跑：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/to-docx/scripts/md_to_docx.py" \
    --input "$INPUT" \
    --output "${INPUT%.md}.docx" \
    --template humanities \
    --title-from-first-h1
```

脚本用 `python-docx` 实现。支持：
- Markdown 标题 → 对应 Word Heading 样式
- 段首缩进 + 宋体 + 1.5 行距
- 中文引号自动规范
- 代码块 → Consolas 等宽
- 图片内嵌（从 `assets/` 读）
- 表格 → Word Table
- 脚注 `[^1]` → Word 原生脚注

脚本有三个模板：
- `humanities`（默认，社科类期刊常见格式）
- `sscilab`（中国社科院论文格式模板，上下 2.54 左右 3.18）
- `simple`（最简，无页眉页脚，适合非正式文稿）

### Step 4：题注与图表

如果 Markdown 里有图片：

```markdown
![图 1：乾隆年间北京城图](assets/fig1.png)
```

脚本会：
- 图片居中
- 下方加题注"图 1：乾隆年间北京城图"（五号 / 10 pt，居中）
- 跟随引用自动连续编号

表格同理：

```markdown
| 年份 | 事件 |
|------|------|
| 1840 | 鸦片战争 |

*表 1：近代史大事年表*
```

**判断**：如果图表没有题注，不要自己编一个——提醒用户补上（C 类校对员的责任）。

### Step 5：脚注

校对好的 Markdown 里用户可能用：

```markdown
这是正文内容[^1]。

[^1]: 这是脚注内容。
```

脚本把 `[^n]` 变成 Word 原生脚注（不是 inline reference），每页底部显示，全文连续编号。

### Step 6：参考文献段

如果 Markdown 最后一段是「参考文献」、「引用文献」、「Bibliography」标题后跟列表，脚本识别它作为参考文献段，格式化为：

- 无段首缩进
- 悬挂缩进（第二行及以后缩 2 字）
- 按原顺序编号 `[1]` `[2]` `[3]` 依次

### Step 7：输出 + 报告

```bash
OUT="${INPUT%.md}.docx"
```

告诉用户：

> Word 稿已生成：`$OUT`
>
> 格式：humanities / sscilab / simple（三选一）
> 字数：N（不计脚注）
> 页数：约 M 页
>
> 建议：
> 1. 在 Word / Pages 里打开核验一下——重点看脚注编号、图表位置、参考文献格式
> 2. 如果期刊有特定模板（比如《历史研究》对比《近代史研究》格式不同），把模板发给我，下次生成时应用
>
> 下一步（可选）：
> - 公众号推送：`/historical-ocr-review:mp-format final.md`

```bash
open "$OUT"
```

## 判断规则

- **没有校对过的 raw.md 直接转 docx**：会把 OCR 错字保留到正稿里，友好警告用户
- **论文含复杂表格（跨页、合并格）**：python-docx 处理不太好，优先 Anthropic docx skill；fallback 时提醒用户核对
- **论文含复杂公式**：LaTeX 公式在 Word 里是图片，不是原生公式。告诉用户公众号友好但期刊投稿可能被编辑要求重做。

## 期刊模板支持

不同期刊格式要求不同。**默认输出是通用社科类**。若用户指定模板（如"历史研究格式""近代史研究格式"），告诉用户：

> 我目前没有内置你指定的期刊模板。两种办法：
> 1. 用默认 `humanities` 生成后，按期刊的「投稿须知」PDF 手动调格式（通常只需改字号、行距）
> 2. 把期刊的样例 Word 文件发给我，我把关键样式参数提取出来加进 skill

## 失败兜底

- python-docx 报错 → 大概率 Markdown 格式有问题（未闭合代码块、表格错位），回去修 Markdown
- 字体找不到 → Mac 应自带宋体/黑体；如果是用户装了英文版 macOS，可能需要用户在系统偏好设置装字体
- Anthropic docx skill 不可用且 python-docx 未装 → `pip3 install python-docx`

---
name: proofread
description: 使用场景：用户对 OCR 出来的 Markdown 运行 `/historical-ocr-review:proofread`、说出"校对这份稿子""看看 OCR 对不对""检查字形""有没有识别错""这段繁体有没有问题""专名校对""标点校对""帮我过一遍"等。这个 skill 会判定文献类型（繁体古籍 / 民国排印 / 现代简体），加载对应的专业知识 reference，然后调用 historical-proofreader agent 输出一份**标注清单**（A 类 OCR 错 / B 类规范问题 / C 类存疑待考），不直接改原文。社科院历史学者的日常核心工作就是这一步——凡是涉及"校对"的请求都要主动触发这个 skill，不必等用户说 proofread 三个字。
argument-hint: "<markdown-path> [--type=classics|republican|modern]"
allowed-tools: Read, Write, Edit, Bash, Grep
---

# 校对 — 历史文献三类知识库 + 专家 Agent

## Task

给 `historical-proofreader` agent 喂一份 OCR 产出的 Markdown，让它输出一份**校对清单**。用户最核心的工作（校对）就围绕这份清单展开。

你的责任是：
1. 读用户给的 Markdown
2. 判断文献类型（也可以用户指定）
3. 加载对应 reference 文件到上下文
4. 调用 `historical-proofreader` agent，传入文本 + reference
5. 把 agent 返回的标注清单保存为 `<input>.review.md`
6. 用 `open` 打开 review.md 供用户审阅

## Process

### Step 1：读输入

```bash
INPUT="<markdown-path>"
test -f "$INPUT" || { echo "文件不存在"; exit 1; }
```

Read 这个 Markdown 前 50 行，判断文献类型（或读 `meta.json` 如果存在）。

### Step 2：判定文献类型

| 提示 | 类型 |
|------|------|
| 竖排标志「|」夹杂、繁体、无现代标点、年号纪年（乾隆、道光） | `classics` 繁体古籍 |
| 繁体或繁简混、有「．」等旧式标点、年份在 1912-1949、出现"民國"年号 | `republican` 民国排印 |
| 纯简体、现代学术格式、年份在 1980 后、参考文献 GB/T 或 APA | `modern` 现代简体 |

命令行 `--type=xxx` 覆盖自动判断。不确定就问用户。

### Step 3：加载对应 reference

根据类型读对应文件到上下文：

| 类型 | reference 路径 |
|------|---------------|
| classics | `${CLAUDE_PLUGIN_ROOT}/skills/proofread/references/traditional-classics.md` |
| republican | `${CLAUDE_PLUGIN_ROOT}/skills/proofread/references/republican-era.md` |
| modern | `${CLAUDE_PLUGIN_ROOT}/skills/proofread/references/modern-chinese.md` |

**为什么分开**：古籍异体字表塞不进民国校对会浪费上下文；反之亦然。三份分别加载，agent 不被不相关知识干扰。

### Step 4：调 historical-proofreader agent

用 Task / Agent 机制调起 `historical-proofreader`（agent 定义在 plugin 的 `agents/historical-proofreader.md`），传入：

```
任务：校对 OCR 出的历史论文 Markdown
文献类型：<type>
reference 已加载：<path>
待校对文本：<path>
输出要求：按 A/B/C 分类的标注清单（参见 agent 内部规范），不改原文
```

同时读 OCR 阶段产出的 `meta.json`（如果存在），把 `low_confidence_pages` 传给 agent 作为**重点盯防**提示。

**读取时的防御性规则**（老版本产物也要能跑）：

```python
import json
meta = {}
meta_path = <input-dir>/meta.json
if meta_path.is_file():
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        meta = {}

# 字段缺失时的兜底：
low_conf = meta.get("low_confidence_pages") or []  # 列表，可能空
avg_conf = meta.get("avg_confidence")               # 可能是 None（MinerU/百度都不直接给）
pages    = meta.get("pages") or 0
```

- `low_confidence_pages` 缺失或为空 → agent 按全文均匀盯防，不降级
- `avg_confidence` 为 `None` → 只展示，不做阈值判断
- `pages` 为 0 → 说明是旧版 meta 或解析失败，不要阻塞流程

### Step 5：保存报告

agent 输出写到：

```
<input-dir>/<input-basename>.review.md
```

例：`~/Downloads/论文.ocr/raw.md` → `~/Downloads/论文.ocr/raw.review.md`

### Step 6：打开 + 报告

```bash
open "<input-dir>/<input-basename>.review.md"
```

汇报格式：

```
校对清单已生成。共 N 条标注：
- A 类 OCR 错：X 条（建议直接改）
- B 类规范：Y 条（按刊物要求判断）
- C 类存疑：Z 条（需核对原书）

已打开 raw.review.md。

后续：
- 改完 raw.md 保存为 final.md
- 再跑一次 proofread 复校（可选）
- 进入 diff-review 核对改动闭环
- 进入 to-docx / mp-format 产出最终稿
```

## 判断规则

- 校对清单为空：意味着 OCR 质量极高，或 agent 漏扫。结合 `meta.json` 的 `pages` 与 `low_confidence_pages` 判断。若低置信度页有值却未出现在清单，大概率是漏扫，应重跑。
- A 类超过 50 条：OCR 质量不佳，回到 prep-scan / ocr-run 重跑（换引擎或加 `--aggressive`）。
- reference 是知识，不是策略。策略层由 agent prompt 控制，不应通过改 reference 调节。

## 分轮校对

支持按类别分轮调用：

```
/historical-ocr-review:proofread raw.md --focus=A
/historical-ocr-review:proofread raw.md --focus=B
/historical-ocr-review:proofread raw.md --focus=C
```

`--focus` 透传给 agent，用于仅输出指定类别条目。

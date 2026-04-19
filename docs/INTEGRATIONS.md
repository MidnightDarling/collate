---
title: 跨运行时接入手册
date: 2026-04-19
author: [Claude Opus 4.7, Alice]
status: stable
---

# 跨运行时接入手册

> 本文档说明如何在不同 agent 运行时 (runtime) 中启用 `historical-ocr-review` 的八步工作流。对工作流本身与 skill 契约的说明见 [AGENTS.md](../AGENTS.md)；本文档只谈 runtime 层面的差异——SKILL.md 如何被发现、subagent 如何被调度、环境变量怎么注入、失败如何上报。

---

## 1. 总览

本插件的八个 skill 都是**纯 Python 脚本 + Markdown 契约**，不依赖特定 agent 框架；任何能做到以下三件事的 runtime 都能跑：

1. **读文件**：读 `skills/<name>/SKILL.md` 与 `agents/<name>.md` 进入上下文
2. **跑 shell**：用命令行调 `python skills/*/scripts/*.py`
3. **起子对话**：把 `agents/historical-proofreader.md` 作为 system prompt 起一个独立对话（或等价机制），回传结构化产物

运行时能力矩阵：

| Runtime | SKILL.md 自动装载 | Subagent 原生机制 | 环境变量注入 | 插件分发 | 推荐用法 |
|---------|----------------|----------------|-----------|--------|-------|
| Claude Code | ✓（`${CLAUDE_PLUGIN_ROOT}`） | Task tool | `~/.env` via hooks | claude-code-marketplace | 原生，零额外配置 |
| Cursor | 手动 `Read` | 独立 chat tab | 项目 `.env` | git clone | 需要 agent 会主动读 SKILL.md |
| Codex CLI | 手动 `Read` | 新会话 + `-f <agent.md>` | shell `export` | git clone | 脚本可编排、适合 CI |
| Kimi K2 | 上传为 knowledge base | file-api + 子会话 | API 请求头 | 知识库文件集 | 主对话 + 知识库模式 |
| MiniMax | 上传为 knowledge base | sub-session API | API 请求头 | 知识库文件集 | 同 Kimi |
| Gemini CLI | 手动 `Read` | 新 chat session | shell `export` | git clone | 同 Cursor |

**核心差异**：前四类（Claude Code / Cursor / Codex CLI / Gemini CLI）是本地 agent，可直接跑 Python 脚本；后两类（Kimi K2 / MiniMax）是云端 agent，需要本地有一台「执行机」代跑 shell，云端 agent 只做决策和校对。

---

## 2. 总原则（适用所有 runtime）

### 2.1 插件根定位

八个 skill 的 Python 脚本都用相对路径引用资源（如 `skills/proofread/references/traditional-classics.md`）。运行时必须保证 agent 在工作时知道「插件根目录在哪」。

- **Claude Code**：自动注入 `${CLAUDE_PLUGIN_ROOT}`
- **其它 runtime**：通过环境变量 `HISTORICAL_OCR_REVIEW_ROOT` 传入，或 agent 在上下文顶部记住绝对路径

本文档后续所有命令用 `${PLUGIN_ROOT}` 占位，实际执行时替换成具体路径。

### 2.2 工作目录约定

每份 PDF 独立一个 `<work_dir>/`，产物按 [AGENTS.md#文件布局](../AGENTS.md) 组织。推荐约定：

```bash
WORK_DIR="$(dirname "$INPUT_PDF")/$(basename "$INPUT_PDF" .pdf).ocr"
mkdir -p "$WORK_DIR"
cp "$INPUT_PDF" "$WORK_DIR/original.pdf"
```

无论哪个 runtime，中间产物不清理——便于人类事后复查。

### 2.3 Subagent 的两种调度模式

`historical-proofreader` 是唯一的 subagent，两种调用方式等价：

**模式 A（进程内）**：主 agent 起一个新子对话（Claude Code Task tool / Cursor 新 chat / Codex 新 session），system prompt 从 `agents/historical-proofreader.md` 读入，注入 raw.md 路径与 reference 路径，子对话按五步 checklist 产出 `raw.review.md` 后结束。

**模式 B（云端 API）**：主 agent 通过 API 请求调一个独立的云端 agent（Kimi / MiniMax 的 sub-session 接口），system prompt 字段填 `agents/historical-proofreader.md` 内容，把 raw.md 作为 attachment 上传，收到 `raw.review.md` 文本回传落盘。

两种模式的契约完全相同：输入是 `raw.md + reference + (meta.json)`，输出是 `raw.review.md`，**绝不** 改 raw.md。

### 2.4 失败上报结构

所有 runtime 在失败时都按 [AGENTS.md#失败处理](../AGENTS.md) 的结构化格式回传：

```
stage: <stage name>
error: <one-line summary>
cause: <likely cause>
next_step: <what the human or agent should do next>
files_preserved: [<paths that remain for inspection>]
```

不要用「something went wrong」「可能有问题」这类模糊语。人类需要看到阶段名 + 原因 + 下一步。

---

## 3. Claude Code（推荐）

**定位**：本插件的原生运行时，零额外配置。

### 3.1 安装

通过 claude-code-marketplace 或直接克隆到 `~/.claude/plugins/`：

```bash
# 方式 A：marketplace
claude plugin install historical-ocr-review

# 方式 B：本地克隆
git clone <repo-url> ~/.claude/plugins/historical-ocr-review
```

`.claude-plugin/plugin.json` 已声明 skills、agents、author 等元数据，Claude Code 启动时自动发现。

### 3.2 环境变量

所有 API key 统一放 `~/.env`，Claude Code 通过 SessionStart hook 加载：

```bash
# ~/.env
OCR_ENGINE=mineru              # mineru / mineru-cloud / baidu / pdf-text-layer
BAIDU_API_KEY=...              # 仅 OCR_ENGINE=baidu 需要
BAIDU_SECRET_KEY=...
ANTHROPIC_API_KEY=...          # 用于 proofread subagent
```

### 3.3 Subagent 调度

主 agent 通过 Task tool 调用 `historical-proofreader`，Claude Code 自动把 `agents/historical-proofreader.md` 作为 system prompt 注入子任务：

```
<use Task tool>
  subagent_type: "historical-proofreader"
  prompt: |
    type: modern
    raw_md_path: /abs/path/to/work_dir/ocr/raw.md
    reference_path: ${CLAUDE_PLUGIN_ROOT}/skills/proofread/references/modern-chinese.md
    low_confidence_pages: [3, 12]
</use>
```

子任务返回 `raw.review.md` 的完整文本，主 agent 落盘到 `<work_dir>/raw.review.md`。

### 3.4 脚本执行

Python 脚本直接在 Bash tool 里跑，路径用 `${CLAUDE_PLUGIN_ROOT}`：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/prep-scan/scripts/split_pages.py" \
    --pdf "$WORK_DIR/original.pdf" --out "$WORK_DIR/pages" --dpi 300
```

---

## 4. Cursor

**定位**：本地 IDE + agent 混合环境。适合一边跑 pipeline 一边看中间产物。

### 4.1 安装

```bash
git clone <repo-url> ~/dev/historical-ocr-review
```

在 Cursor 项目根写一份 `.cursorrules`（或 `.cursor/rules.mdc`）：

```markdown
你在 historical-ocr-review 插件环境下工作。插件根在 ~/dev/historical-ocr-review。

启动时必须先读：
- ~/dev/historical-ocr-review/AGENTS.md（工作流契约）
- ~/dev/historical-ocr-review/skills/<当前要跑的 skill>/SKILL.md

调用 historical-proofreader subagent 时：
1. 新开一个 chat tab
2. 粘贴 ~/dev/historical-ocr-review/agents/historical-proofreader.md 的 YAML frontmatter 后的正文作为该 tab 的角色设定
3. 在主 chat 把 raw.md 路径、reference 路径作为 prompt 发给子 tab
4. 子 tab 产出 raw.review.md 完整文本后回到主 chat 落盘

环境变量从 ./env 读（不是 ~/.env）。
```

### 4.2 环境变量

项目根放 `.env`（git-ignored），由 shell 加载：

```bash
set -a
source .env
set +a
```

或在 Cursor 终端里手动 `export`。

### 4.3 Subagent 调度

Cursor 没有 Task tool，用「新 chat tab」模拟 subagent：

1. **主 tab** 负责 pipeline 编排
2. **proofread tab** 的 system prompt 从 `agents/historical-proofreader.md` 的正文（跳过 YAML frontmatter）读入
3. 主 tab 发「请校对 /abs/path/raw.md，文献类型 classics，reference 在 .../traditional-classics.md」
4. proofread tab 按 checklist 产出 `raw.review.md` 全文，主 tab 复制到 `<work_dir>/raw.review.md`

### 4.4 脚本执行

在 Cursor 的集成终端里直接跑：

```bash
PLUGIN_ROOT=~/dev/historical-ocr-review
python3 "$PLUGIN_ROOT/skills/ocr-run/scripts/run_mineru.py" \
    --pdf "$WORK_DIR/cleaned.pdf" --out "$WORK_DIR/ocr" --lang ch
```

---

## 5. Codex CLI

**定位**：命令行 agent，适合脚本化编排与 CI/CD 流水线。

### 5.1 安装

```bash
git clone <repo-url> ~/dev/historical-ocr-review
export HISTORICAL_OCR_REVIEW_ROOT=~/dev/historical-ocr-review
```

Codex CLI 没有插件系统，通过 session 启动时的 `--system` 或 `--context` 传入 AGENTS.md：

```bash
codex --system "$HISTORICAL_OCR_REVIEW_ROOT/AGENTS.md" \
      --context "$HISTORICAL_OCR_REVIEW_ROOT/skills" \
      "把 /path/to/paper.pdf 跑完整 pipeline，交付 docx 和 mp.html"
```

### 5.2 环境变量

直接 `export` 或 `.envrc`（direnv）：

```bash
export OCR_ENGINE=mineru
export ANTHROPIC_API_KEY=...
```

### 5.3 Subagent 调度

Codex CLI 支持 `codex run --system <file>` 起独立 session，用这个机制模拟 subagent：

```bash
# 主 session 里
codex run \
  --system "$HISTORICAL_OCR_REVIEW_ROOT/agents/historical-proofreader.md" \
  --context "$WORK_DIR/ocr/raw.md" \
  --context "$HISTORICAL_OCR_REVIEW_ROOT/skills/proofread/references/modern-chinese.md" \
  --output "$WORK_DIR/raw.review.md" \
  "type=modern, 请按五步 checklist 校对 raw.md"
```

Codex 会起一个独立进程、独立 context window 跑子任务，产出写到 `--output` 文件。

### 5.4 脚本执行

Codex CLI 原生支持 `bash(...)` 工具，跟 Claude Code 一样直接跑：

```bash
python3 "$HISTORICAL_OCR_REVIEW_ROOT/skills/diff-review/scripts/md_diff.py" \
    --raw "$WORK_DIR/raw.md" \
    --final "$WORK_DIR/final.md" \
    --review "$WORK_DIR/raw.review.md" \
    --out "$WORK_DIR/audit.html"
```

### 5.5 CI 集成

Codex CLI 适合在 GitHub Actions 里跑自动化 pipeline：

```yaml
# .github/workflows/ocr.yml
- name: Run OCR pipeline
  run: |
    codex --system AGENTS.md \
          --context skills \
          --input "${{ inputs.pdf_path }}" \
          --output "$GITHUB_WORKSPACE/artifacts/"
  env:
    OCR_ENGINE: mineru
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

## 6. Kimi K2

**定位**：Moonshot 的云端 agent，上下文窗口大（200K+），适合长论文整篇上下文评审。

### 6.1 准备

Kimi K2 不能直接跑本地 Python 脚本，需要一台「执行机」——本地开发机、云服务器或者 GitHub Actions runner。架构：

```
Kimi K2（云端大脑，决策 + 校对）
     │
     │  HTTP / SSH 调度
     ▼
执行机（跑 Python 脚本的机器）
     │
     ▼
work_dir/（产物落盘）
```

### 6.2 知识库上传

把 SKILL.md 与 reference 打包上传到 Kimi 知识库：

```bash
# 用 Moonshot File API
for f in \
  AGENTS.md \
  skills/*/SKILL.md \
  skills/proofread/references/*.md \
  agents/historical-proofreader.md
do
  curl https://api.moonshot.cn/v1/files \
    -H "Authorization: Bearer $MOONSHOT_API_KEY" \
    -F "purpose=assistants" \
    -F "file=@$f"
done
```

拿到的 `file_id` 列表在启动 assistant 时通过 `file_ids` 字段关联，Kimi 就能在上下文中引用这些文档。

### 6.3 主 agent 配置

主 agent 的 system prompt 明确执行机的通讯方式：

```
你是 historical-ocr-review pipeline 的主 agent。

你不能直接跑 Python，需要通过 HTTP POST 到
https://executor.example.com/run 让执行机代跑。请求格式：

  POST /run
  { "cmd": "python3 ${PLUGIN_ROOT}/skills/prep-scan/scripts/split_pages.py ...",
    "timeout": 600 }

响应：
  { "stdout": "...", "stderr": "...", "exit_code": 0, "files_written": [...] }

校对时调 /subagent：

  POST /subagent
  { "system_prompt_file_id": "<historical-proofreader.md 的 file_id>",
    "user_prompt": "type=modern, raw_md=..., reference=...",
    "timeout": 1800 }

响应里的 raw_review_md 字段就是子对话的产物。
```

### 6.4 Subagent 调度

Kimi K2 的 Moonshot Assistant API 支持 `create_sub_run`，可以起一个子对话，system prompt 独立。核心逻辑：

```python
# 执行机侧的 /subagent handler
def subagent_handler(req):
    system_prompt = moonshot.files.retrieve_content(req["system_prompt_file_id"])
    sub_run = moonshot.assistants.create_run(
        assistant_id=PROOFREADER_ASSISTANT_ID,
        instructions=system_prompt,
        messages=[{"role": "user", "content": req["user_prompt"]}],
        timeout=req["timeout"],
    )
    return {"raw_review_md": sub_run.final_message_content}
```

### 6.5 失败处理

Kimi K2 的失败（API rate limit / 网络 / 上下文超长）要显式回传：执行机返回 HTTP 5xx + 结构化 body，主 agent 读到后按 [AGENTS.md#失败处理](../AGENTS.md) 的格式上报给人类。**不要** 让主 agent 静默重试超过两次。

---

## 7. MiniMax

**定位**：同 Kimi K2，云端 agent 架构。MiniMax 的 `abab-chat` + Assistants SDK 适合中文密集型任务。

### 7.1 准备

与 Kimi 相同，需要本地执行机。

### 7.2 知识库上传

MiniMax Assistants API：

```bash
for f in \
  AGENTS.md \
  skills/*/SKILL.md \
  skills/proofread/references/*.md \
  agents/historical-proofreader.md
do
  curl https://api.minimax.chat/v1/files/upload \
    -H "Authorization: Bearer $MINIMAX_API_KEY" \
    -F "purpose=assistants" \
    -F "file=@$f"
done
```

### 7.3 Subagent 调度

MiniMax Assistants 支持「子 Agent」机制（`sub_agent_id` 字段）。把 `historical-proofreader.md` 注册为一个独立 assistant，主 agent 通过 `create_run` 时指定 `sub_agent_id` 调起：

```python
main_run = minimax.runs.create(
    assistant_id=MAIN_ASSISTANT_ID,
    messages=[...],
    tools=[{
        "type": "sub_agent",
        "sub_agent_id": PROOFREADER_ASSISTANT_ID,
    }],
)
```

子 agent 的输出通过 `tool_output` 事件流回主 agent。

### 7.4 流式输出

MiniMax 支持 SSE 流式，长文档校对时建议开启——一万字的校对清单流式返回比一次性 JSON 更稳：

```python
for event in minimax.runs.stream(run_id=main_run.id):
    if event.type == "tool_output":
        raw_review_md_chunks.append(event.content)
```

---

## 8. Gemini CLI

**定位**：Google 的命令行 agent，上下文窗口 1M+，适合整本书级别的 PDF。

### 8.1 安装

```bash
git clone <repo-url> ~/dev/historical-ocr-review
export HISTORICAL_OCR_REVIEW_ROOT=~/dev/historical-ocr-review
```

Gemini CLI 的 `settings.json` 里登记 system prompt 与工具：

```json
{
  "system_prompt_file": "~/dev/historical-ocr-review/AGENTS.md",
  "tools": ["bash", "read", "write", "edit"],
  "env_file": "~/.env"
}
```

### 8.2 环境变量

Gemini CLI 支持 `env_file`，直接读 `~/.env`，与 Claude Code 行为一致。

### 8.3 Subagent 调度

Gemini CLI 的 `gemini chat --session <new>` 起独立会话，用这个模拟 subagent：

```bash
gemini chat --session proofread \
  --system "$HISTORICAL_OCR_REVIEW_ROOT/agents/historical-proofreader.md" \
  --attach "$WORK_DIR/ocr/raw.md" \
  --attach "$HISTORICAL_OCR_REVIEW_ROOT/skills/proofread/references/modern-chinese.md" \
  --prompt "type=modern, 请按五步 checklist 校对 raw.md" \
  > "$WORK_DIR/raw.review.md"
```

### 8.4 脚本执行

同 Claude Code / Codex，直接在 bash 里跑 Python 脚本。

---

## 9. 公共环境变量

所有 runtime 都读取以下环境变量；缺失时 setup skill 会报错：

| 变量 | 用途 | 默认 | 必需 |
|------|-----|------|----|
| `OCR_ENGINE` | OCR 引擎选择 | `mineru` | 是 |
| `BAIDU_API_KEY` | 百度 OCR API Key | — | `OCR_ENGINE=baidu` 时必需 |
| `BAIDU_SECRET_KEY` | 百度 OCR Secret | — | 同上 |
| `ANTHROPIC_API_KEY` | Claude API（proofread 用） | — | 非 Claude Code runtime 必需 |
| `MOONSHOT_API_KEY` | Kimi API | — | Kimi K2 runtime 必需 |
| `MINIMAX_API_KEY` | MiniMax API | — | MiniMax runtime 必需 |
| `HISTORICAL_OCR_REVIEW_ROOT` | 插件根绝对路径 | — | 非 Claude Code runtime 必需 |
| `MINERU_CACHE_DIR` | MinerU 模型缓存路径 | `~/.cache/huggingface/hub` | 否 |

---

## 10. 跨运行时故障排查

| 症状 | 可能原因 | 解决 |
|------|---------|-----|
| `skills/*/SKILL.md not found` | 插件根路径错 | 核对 `$HISTORICAL_OCR_REVIEW_ROOT` / `$CLAUDE_PLUGIN_ROOT` |
| `ModuleNotFoundError: mineru` | Python 包未装或装在错误 venv | `pip install 'mineru[pipeline]'` |
| `poppler not found` | 系统依赖缺失 | macOS `brew install poppler`，Debian `apt install poppler-utils` |
| subagent 产出空 `raw.review.md` | system prompt 没正确注入 | 检查 runtime 是否真的读取了 `agents/historical-proofreader.md` 正文部分（跳过 YAML frontmatter） |
| Kimi / MiniMax 上下文超长 | 单次把整篇 raw.md 塞进 prompt | 分段传入，每段 5000 字，最后合并 `raw.review.md` |
| `OCR_ENGINE=mineru` 但网络差 | 首次下载 2–3 GB 模型失败 | 走代理或切 ModelScope 源：`export HF_ENDPOINT=https://hf-mirror.com` |
| 在 CI 里运行 Codex 超时 | MinerU 首次跑加载模型慢 | 在 CI 缓存 `~/.cache/huggingface/hub` |

---

## 11. 扩展：接入新 runtime

加入新 runtime 时按以下清单实现适配：

1. **插件根定位**：提供 `HISTORICAL_OCR_REVIEW_ROOT` 或等价机制
2. **SKILL.md 发现**：让 agent 在每次调用 skill 前读 `skills/<name>/SKILL.md`
3. **Python 脚本执行**：runtime 要能跑 `python3 <abs path> [args]`
4. **Subagent 调度**：实现「独立 context + 独立 system prompt + 结构化回传」的子任务机制（进程内或 API 均可）
5. **环境变量注入**：API key 类变量必须通过运行时的安全机制（`~/.env` / Secret Manager / CI Secrets）注入，**不要** 硬编码在 prompt 里
6. **失败上报**：遵循 [AGENTS.md#失败处理](../AGENTS.md) 的结构化格式

以上五项任一缺失，就无法保证八步 pipeline 的完整性。新 runtime 的适配层请提交 PR 到本目录，命名为 `INTEGRATIONS-<runtime>.md`。

---

## 参考

- [AGENTS.md](../AGENTS.md) — 工作流契约、subagent 契约、失败处理
- [ARCHITECTURE.md](ARCHITECTURE.md) — 各 skill 的内部实现结构
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — 具体错误 + 解决方案
- [README.md](../README.md) — 项目定位与快速上手

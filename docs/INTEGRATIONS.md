---
title: 跨运行时接入手册
date: 2026-04-19
author: [Alice, Claude Opus 4.7, GPT-5.4]
status: stable
---

# 跨运行时接入手册

> 本文档说明如何在不同 agent 运行时 (runtime) 中启用 `collate` 的八步工作流与七个阅读 skill。对工作流本身与 skill 契约的说明见 [AGENTS.md](../AGENTS.md)；本文档只谈 runtime 层面的差异——SKILL.md 如何被发现、subagent 如何被调度、环境变量怎么注入、失败如何上报。

---

## 1. 总览

本插件的十五个 skill 都是**纯 Python 脚本 + Markdown 契约**，不依赖特定 agent 框架；任何能做到以下三件事的 runtime 都能跑：

1. **读文件**：读 `skills/<name>/SKILL.md` 与 `agents/<name>.md` 进入上下文
2. **跑 shell**：用命令行调 `python skills/*/scripts/*.py`
3. **起子对话**：把 `agents/historical-proofreader.md` 作为 system prompt 起一个独立对话（或等价机制），回传结构化产物

推荐入口分成两层：

- **机械总入口**：`python3 scripts/run_full_pipeline.py --pdf <input.pdf>`
- **完整 agent 入口**：`agents/ocr-pipeline-operator.md`，它会在 `raw.md` 就位后调 `historical-proofreader`，再重入总编排脚本

运行时能力矩阵：

| Runtime | 状态 | SKILL.md 自动装载 | Subagent 原生机制 | 插件分发 |
|---------|------|----------------|----------------|--------|
| Claude Code | **原生支持** | ✓（`${CLAUDE_PLUGIN_ROOT}`） | Task tool | `.claude-plugin/` |
| Codex CLI | **原生支持** | `AGENTS.md` 自动发现 | 新会话 + `-f <agent.md>` | `.codex-plugin/` |
| Cursor | **原生支持** | `.cursor/rules/collate.mdc` 自动加载 | 独立 chat tab | `.cursor/rules/` |
| Gemini CLI | **原生支持** | `GEMINI.md` 自动发现 | 新 session + `-C <agent.md>` | `gemini-extension.json` |
| OpenCode | 未实现 | 理论可行 | 内置 spawn | 无集成文件 |
| Hermes agents | **原生支持** | `AGENTS.md` 自动发现 + `.cursor/rules/*.mdc` | `delegate_task` | 无需新文件 |
| OpenClaw | 路线图 | 需 wrapper plugin | 插件 hook | 无集成文件 |
| Kimi | 概念架构 | 上传为 knowledge base | file-api + 子会话 | 无 |
| MiniMax | 概念架构 | 上传为 knowledge base | sub-session API | 无 |

**实际状态**：**Claude Code**、**Codex CLI**、**Gemini CLI**、**Cursor** 和 **Hermes agents** 五个 runtime 有原生支持。Hermes 不需要新文件——它启动时自动发现仓库里已有的 `AGENTS.md`。OpenCode、OpenClaw 没有集成文件，下方的接入说明是**架构参考**，不是已验证的集成。Kimi / MiniMax 是云端概念架构，需要本地执行机代跑 shell。

---

## 2. 总原则（适用所有 runtime）

### 2.1 插件根定位

十五个 skill 的 Python 脚本或参考文件都用相对路径引用资源（如 `skills/proofread/references/traditional-classics.md`）。运行时必须保证 agent 在工作时知道「插件根目录在哪」。

接口也已收敛成 skill-first：

- `skill` 是能力本体
- `ocr` 与 `status` 是仅存的独立 command
- 其余 slash surface 若存在，应直接暴露 skill，而不是再维护同名 command 壳

- **Claude Code**：自动注入 `${CLAUDE_PLUGIN_ROOT}`
- **其它 runtime**：通过环境变量 `COLLATE_ROOT` 传入，或 agent 在上下文顶部记住绝对路径

本文档后续所有命令用 `${PLUGIN_ROOT}` 占位，实际执行时替换成具体路径。

### 2.2 工作目录约定

每份 PDF 独立一个 `<basename>.ocr/` 工作区，所有产物按 [AGENTS.md#文件布局](../AGENTS.md) 与 [`references/workspace-layout.md`](../references/workspace-layout.md) 的统一约定组织。推荐初始化：

```bash
WS="$(dirname "$INPUT_PDF")/$(basename "$INPUT_PDF" .pdf).ocr"
mkdir -p "$WS"/{prep,previews,review,output,assets,_internal}
cp "$INPUT_PDF" "$WS/prep/original.pdf"
```

各子目录分工：

| 子目录 | 内容 | 是否给人类看 |
|--------|------|-----------|
| `prep/` | `pages/` `cleaned_pages/` `trimmed_pages/` `cleaned.pdf` | 过程，偶尔核验 |
| `previews/` | `visual-prep.html` `ocr-preview.html` `diff-review.html` | 核验入口 |
| `review/` | `raw.review.md` 等校对清单 | 过程 |
| `output/` | `<title>_<author>_<year>_final.docx` / `_wechat.{html,md}` | **最终交付** |
| `assets/` | MinerU 抽出的图片 | 被 raw.md / final.md 引用 |
| `_internal/` | `mineru_full.md` / `_import_provenance.json` / `_pipeline_status.json` 等调试产物 | 下划线前缀示意"别动" |

无论哪个 runtime，中间产物不清理；每个 skill 结束后会自动刷新 `$WS/README.md`，给人类一个清晰的入口。

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
claude plugin install collate

# 方式 B：本地克隆
git clone <repo-url> ~/.claude/plugins/collate
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
    raw_md_path: /abs/path/to/<basename>.ocr/raw.md
    reference_path: ${CLAUDE_PLUGIN_ROOT}/skills/proofread/references/modern-chinese.md
    low_confidence_pages: [3, 12]
</use>
```

子任务返回 `raw.review.md` 的完整文本，主 agent 落盘到 `<basename>.ocr/review/raw.review.md`。

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
git clone <repo-url> ~/dev/collate
```

仓库已自带 `.cursor/rules/collate.mdc`（`alwaysApply: true`）。Cursor 打开项目时自动加载此规则，无需手写。规则内容包含插件根定位、skill 列表、subagent 调度方式与核心原则。

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
4. proofread tab 按 checklist 产出 `raw.review.md` 全文，主 tab 复制到 `<basename>.ocr/review/raw.review.md`

### 4.4 脚本执行

在 Cursor 的集成终端里直接跑：

```bash
PLUGIN_ROOT=~/dev/collate
python3 "$PLUGIN_ROOT/skills/ocr-run/scripts/run_mineru.py" \
    --pdf "$WORK_DIR/cleaned.pdf" --out "$WORK_DIR/ocr" --lang ch
```

---

## 5. Codex

**定位**：既可以把仓库当普通 Git 工作区直接跑，也可以把仓库当原生 Codex plugin 通过 repo marketplace 暴露出来。前者适合本地深度协作，后者适合公开仓库的优雅分发。

### 5.1 安装与发现

```bash
git clone <repo-url> ~/dev/collate
export COLLATE_ROOT=~/dev/collate
```

仓库现在自带：

- `.codex-plugin/plugin.json`
- `.agents/plugins/marketplace.json`

对支持 plugin directory 的 Codex 端，重启后即可从该 repo marketplace 看到并安装 `collate`。  
对直接在仓库里工作的 Codex CLI，最短路径仍然是：

```bash
cd "$COLLATE_ROOT"
codex
```

Codex 会从 Git root 自动加载 `AGENTS.md`。如果你要显式起一个一次性 session，也可以继续手动传 `AGENTS.md`：

```bash
codex --system "$COLLATE_ROOT/AGENTS.md" \
      --context "$COLLATE_ROOT/skills" \
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
  --system "$COLLATE_ROOT/agents/historical-proofreader.md" \
  --context "$WORK_DIR/ocr/raw.md" \
  --context "$COLLATE_ROOT/skills/proofread/references/modern-chinese.md" \
  --output "$WORK_DIR/raw.review.md" \
  "type=modern, 请按五步 checklist 校对 raw.md"
```

Codex 会起一个独立进程、独立 context window 跑子任务，产出写到 `--output` 文件。

### 5.4 脚本执行

Codex CLI 原生支持 `bash(...)` 工具，跟 Claude Code 一样直接跑：

```bash
python3 "$COLLATE_ROOT/skills/diff-review/scripts/md_diff.py" \
    --raw "$WS/raw.md" \
    --final "$WS/final.md" \
    --review "$WS/review/raw.review.md" \
    --out "$WS/previews/diff-review.html"
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

## 6. Gemini CLI

**定位**：Google 的开源命令行 agent。支持扩展（extension）机制与项目上下文文件（`GEMINI.md`）自动发现。

### 6.1 安装

两种方式：

```bash
# 方式 A：作为 Gemini CLI 扩展安装
gemini extensions install collate

# 方式 B：克隆仓库后直接运行
git clone <repo-url> ~/dev/collate
cd ~/dev/collate
gemini
```

仓库随发两个原生文件：

- `GEMINI.md` — 项目上下文，Gemini CLI 每次会话自动加载
- `gemini-extension.json` — 扩展清单，声明名称、版本与上下文文件

Gemini CLI 按层级加载上下文：全局 `~/.gemini/GEMINI.md` → 项目根 `GEMINI.md` → 子目录 `GEMINI.md`。仓库根的 `GEMINI.md` 提供插件总览与 skill 列表。

### 6.2 环境变量

直接 `export` 或写入 `.env`（需手动 `source`）：

```bash
export COLLATE_ROOT=~/dev/collate
export OCR_ENGINE=mineru
export BAIDU_API_KEY=...         # 仅 baidu 引擎
export BAIDU_SECRET_KEY=...
```

### 6.3 Subagent 调度

Gemini CLI 用新会话加载 agent 定义：

```bash
# 在新 session 中启动 proofreader
gemini -C agents/historical-proofreader.md \
  "type=modern, 请按五步 checklist 校对 $WORK_DIR/raw.md"
```

或在当前会话中用 `@agents/historical-proofreader.md` 引用 agent 上下文。

### 6.4 脚本执行

Gemini CLI 的 shell 工具直接跑 Python：

```bash
python3 "$COLLATE_ROOT/skills/prep-scan/scripts/split_pages.py" \
    --pdf "$WORK_DIR/original.pdf" --out "$WORK_DIR/pages" --dpi 300
```

### 6.5 上下文管理

```bash
# 查看当前加载的所有 GEMINI.md 内容
/memory show

# 重新扫描并加载
/memory reload
```

用户也可以在 `~/.gemini/settings.json` 中配置 `context.fileName` 同时加载 `AGENTS.md`：

```json
{
  "context": {
    "fileName": ["GEMINI.md", "AGENTS.md"]
  }
}
```

---

## 7. Kimi

**定位**：Moonshot 的云端 agent，上下文窗口大（200K+），适合长论文整篇上下文评审。

### 7.1 准备

Kimi 不能直接跑本地 Python 脚本，需要一台「执行机」——本地开发机、云服务器或者 GitHub Actions runner。架构：

```
Kimi（云端大脑，决策 + 校对）
     │
     │  HTTP / SSH 调度
     ▼
执行机（跑 Python 脚本的机器）
     │
     ▼
<basename>.ocr/（产物落盘；README.md 自描述）
```

### 7.2 知识库上传

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

### 7.3 主 agent 配置

主 agent 的 system prompt 明确执行机的通讯方式：

```
你是 collate pipeline 的主 agent。

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

### 7.4 Subagent 调度

Kimi 的 Moonshot Assistant API 支持 `create_sub_run`，可以起一个子对话，system prompt 独立。核心逻辑：

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

### 7.5 失败处理

Kimi 的失败（API rate limit / 网络 / 上下文超长）要显式回传：执行机返回 HTTP 5xx + 结构化 body，主 agent 读到后按 [AGENTS.md#失败处理](../AGENTS.md) 的格式上报给人类。**不要** 让主 agent 静默重试超过两次。

---

## 8. MiniMax

**定位**：同 Kimi，云端 agent 架构。MiniMax 的 `abab-chat` + Assistants SDK 适合中文密集型任务。

### 8.1 准备

与 Kimi 相同，需要本地执行机。

### 8.2 知识库上传

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

### 8.3 Subagent 调度

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

### 8.4 流式输出

MiniMax 支持 SSE 流式，长文档校对时建议开启——一万字的校对清单流式返回比一次性 JSON 更稳：

```python
for event in minimax.runs.stream(run_id=main_run.id):
    if event.type == "tool_output":
        raw_review_md_chunks.append(event.content)
```

---

## 9. OpenCode

**定位**：SST 出品的开源终端 agent；内置三层扩展（skills / agents / plugins），原生识别 `AGENTS.md`，并提供 Claude Code 兼容层。适合团队里既有 Claude Code 用户又有 OpenCode 用户的混合场景。

### 9.1 安装

```bash
curl https://opencode.ai/install | bash    # 或 npm i -g opencode-ai
git clone <repo-url> ~/dev/collate
cd ~/dev/collate && opencode
```

OpenCode 启动后会按以下顺序找规则文件：

1. `./AGENTS.md`（项目根）
2. `~/.config/opencode/AGENTS.md`（全局）
3. `./CLAUDE.md`（Claude Code fallback）
4. `~/.claude/CLAUDE.md`（Claude Code 全局 fallback）

collate 仓库已有 `AGENTS.md`，OpenCode 零配置即可读到。

### 9.2 Skills 与 Agents

OpenCode 的 skill 目录：

- `./.opencode/skills/`（项目）
- `~/.opencode/skills/`（全局）
- `~/.claude/skills/`（Claude Code 兼容层，默认启用；用 `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` 关闭）

collate 的 skill 位于仓库 `skills/`，默认不在上述位置。两条落地路径：

- **软链**：`ln -s "$PWD/skills" ~/.opencode/skills/collate`
- **opencode.json 声明**：
  ```json
  {
    "$schema": "https://opencode.ai/config.json",
    "instructions": ["AGENTS.md", "skills/**/SKILL.md"]
  }
  ```

Agents 定义：把 `agents/historical-proofreader.md` 复制到 `.opencode/agents/` 或 `~/.config/opencode/agents/`，OpenCode 会把它注册为 subagent（primary / subagent 模式由 frontmatter 的 `mode` 决定）。

### 9.3 环境变量

OpenCode 透传当前 shell 环境。项目级 `.env`：

```bash
set -a; source .env; set +a
opencode
```

### 9.4 脚本执行

OpenCode 默认开启 `bash` 工具；直接 `python skills/*/scripts/*.py` 即可。

---

## 10. Hermes agents

**定位**：NousResearch 出品的自改进 CLI agent，支持 15+ 消息网关（Telegram / Discord / Slack / WhatsApp …）。启动时按 `.hermes.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules` 的优先级加载项目上下文（只加载第一个命中的文件）。本仓库没有 `.hermes.md`，所以 Hermes 直接加载我们的 `AGENTS.md`——这就是原生支持，不需要新文件。

### 10.1 安装

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc        # 或 ~/.zshrc
hermes setup            # 交互向导，配 LLM provider + 工具 + secret
```

支持 Linux / macOS / WSL2 / Android（Termux）。Windows 用 WSL2。

### 10.2 接入 collate

```bash
git clone <repo-url> ~/dev/collate
cd ~/dev/collate
hermes                  # 或 hermes --tui
```

Hermes 启动时自动发现仓库根的 `AGENTS.md`，加载为项目上下文。它也会读取 `.cursor/rules/*.mdc`，所以我们的 `collate.mdc` 项目规则同时生效。

### 10.3 Subagent 调度

Hermes 通过 `delegate_task` 工具调度子任务。调 `historical-proofreader` 时，Hermes 在内部起一个新的 agent turn，把 `agents/historical-proofreader.md` 的内容注入为 system prompt：

```
delegate_task(
  task="按校对清单逐条核对 raw.md，产出 raw.review.md",
  context="agents/historical-proofreader.md 的完整内容",
  files=["workspace/.ocr/<book>/raw.md"]
)
```

主 agent 收到 `delegate_task` 的返回后继续编排。

### 10.4 Skills

Hermes 的 skill 发现走子目录渐进式：从仓库根开始，逐层目录往下找 `AGENTS.md`。我们的 `skills/<name>/SKILL.md` 不会被自动发现为 Hermes skill（Hermes 识别 `AGENTS.md`，不识别 `SKILL.md`），但主 agent 通过 `AGENTS.md` 里的契约知道每个 skill 的路径和调用方式，可以直接 `Read` + shell 执行。

### 10.5 环境变量

Hermes 读 `~/.hermes/.env` 与仓库级 `.env`。敏感凭据建议放前者。

```bash
hermes config set providers.anthropic.api_key "$ANTHROPIC_API_KEY"
hermes config set providers.openai.api_key "$OPENAI_API_KEY"
```

### 10.6 为什么不创建 .hermes.md

Hermes 的上下文加载是排他式的：命中第一个文件后就不再继续。如果我们创建 `.hermes.md`，它会替代 `AGENTS.md` 的加载，导致仓库需要在两个地方维护相同的契约信息。不创建 `.hermes.md`，让 Hermes 直接用 `AGENTS.md`，是最简洁的集成方式。

---

## 11. OpenClaw

**定位**：开源 AI 助手框架，强项在 15+ 消息通道 + 跨网站控制；扩展通过「native 插件（TS/JS entry + `openclaw.plugin.json`）+ ClawHub / npm 分发」。用户量大，但本仓库当前主线是 Python + Markdown，不是 Native TS 插件，直接 `openclaw plugins install <path>` 对裸目录**不支持**。

### 11.1 两条现实路径

**路径 A：迁移到 Hermes（推荐）**

OpenClaw 用户把配置迁到 Hermes 后就能获得对 collate 的全量支持：

```bash
hermes claw migrate --workspace-target ~/dev/collate
cd ~/dev/collate && hermes
```

Hermes 与 OpenClaw 系出同门（Hermes 作者即 OpenClaw 作者），迁移工具成熟。

**路径 B：写一个 thin wrapper plugin（路线图）**

未来会发布一个 `@collate/openclaw` 包：

- 根目录有 `openclaw.plugin.json`（含 `id: "collate"`、`configSchema`、工具列表）
- 入口 `index.ts` 用 `definePluginEntry` 注册 agent tool，每个 tool 内部 shell 出去调 `python skills/*/scripts/*.py`
- 发布到 ClawHub 或 npm，用户跑：
  ```bash
  openclaw plugins install @collate/openclaw
  # 或 ClawHub-only：openclaw plugins install clawhub:@collate/openclaw
  ```

在包还没发之前，自建者可用 in-repo 插件工作区路径：把 wrapper 源码放 OpenClaw bundled plugin workspace 下，`pnpm install` + `openclaw plugins install collate` 即可。细节见 [OpenClaw 插件构建指南](https://docs.openclaw.ai/plugins/building-plugins)。

### 11.2 消息侧场景（可选）

OpenClaw 的原生强项是消息通道。典型用法：用户把扫描 PDF 附件发到 Telegram/Email → OpenClaw 网关触发 plugin → plugin 调 collate pipeline → 把 `final.docx` 附件回发。该路径需要的是「message handler」类型的 plugin，不是 agent tool plugin；本仓库不提供模板。

### 11.3 环境变量

```bash
openclaw config set providers.anthropic.apiKey "$ANTHROPIC_API_KEY"
openclaw config set providers.openai.apiKey "$OPENAI_API_KEY"
```

collate 的 OCR 相关 key（`MINERU_API_KEY` / `BAIDU_OCR_API_KEY`）由 plugin 自己的 `configSchema` 暴露，用户通过 `openclaw config` 注入。

---

## 12. 公共环境变量

所有 runtime 都读取以下环境变量；缺失时 setup skill 会报错：

| 变量 | 用途 | 默认 | 必需 |
|------|-----|------|----|
| `OCR_ENGINE` | OCR 引擎选择 | `mineru` | 是 |
| `BAIDU_API_KEY` | 百度 OCR API Key | — | `OCR_ENGINE=baidu` 时必需 |
| `BAIDU_SECRET_KEY` | 百度 OCR Secret | — | 同上 |
| `ANTHROPIC_API_KEY` | Claude API（proofread 用） | — | 非 Claude Code runtime 必需 |
| `MOONSHOT_API_KEY` | Kimi API | — | Kimi runtime 必需 |
| `MINIMAX_API_KEY` | MiniMax API | — | MiniMax runtime 必需 |
| `COLLATE_ROOT` | 插件根绝对路径 | — | 非 Claude Code runtime 必需 |
| `MINERU_CACHE_DIR` | MinerU 模型缓存路径 | `~/.cache/huggingface/hub` | 否 |

---

## 13. 跨运行时故障排查

| 症状 | 可能原因 | 解决 |
|------|---------|-----|
| `skills/*/SKILL.md not found` | 插件根路径错 | 核对 `$COLLATE_ROOT` / `$CLAUDE_PLUGIN_ROOT` |
| `ModuleNotFoundError: mineru` | Python 包未装或装在错误 venv | `pip install 'mineru[pipeline]'` |
| `poppler not found` | 系统依赖缺失 | macOS `brew install poppler`，Debian `apt install poppler-utils` |
| subagent 产出空 `raw.review.md` | system prompt 没正确注入 | 检查 runtime 是否真的读取了 `agents/historical-proofreader.md` 正文部分（跳过 YAML frontmatter） |
| Kimi / MiniMax 上下文超长 | 单次把整篇 raw.md 塞进 prompt | 分段传入，每段 5000 字，最后合并 `raw.review.md` |
| `OCR_ENGINE=mineru` 但网络差 | 首次下载 2–3 GB 模型失败 | 走代理或切 ModelScope 源：`export HF_ENDPOINT=https://hf-mirror.com` |
| 在 CI 里运行 Codex 超时 | MinerU 首次跑加载模型慢 | 在 CI 缓存 `~/.cache/huggingface/hub` |

---

## 14. 扩展：接入新 runtime

加入新 runtime 时按以下清单实现适配：

1. **插件根定位**：提供 `COLLATE_ROOT` 或等价机制
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

# 安装

两条路径：一键脚本或手动分步。其他 agent 运行时（OpenCode / Hermes agents / Codex CLI / Cursor / Gemini CLI / Kimi / MiniMax / OpenClaw）的接入细节见 [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md)。

---

## 一键安装（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/MidnightDarling/collate/main/scripts/install.sh | bash
```

脚本做的事情：

1. 克隆仓库到 `~/.local/share/collate`（可用 `--target PATH` 改位置，或预设 `COLLATE_HOME` 环境变量）
2. 跑 `pip install --user -U -r requirements.txt` 装 Python 依赖
3. 自动识别本机已装的 agent runtime，并为每个 runtime 做对应接入：
    - **Claude Code**：把仓库软链到 `~/.claude/plugins/collate`
    - **Hermes agents**：把 10 个 skill 软链到 `~/.hermes/skills/collate-*`
    - **OpenCode / Codex CLI**：零配置（这两个 runtime 原生读取 `AGENTS.md`），只打印 `cd + 启动` 命令
    - **Cursor / Gemini CLI**：打印需要用户手动创建的 rule 文件 / 首轮粘贴内容
4. 最后打印分 runtime 的 next-step 指南、OCR 引擎环境变量模板、卸载命令

可选参数：

| 参数 | 作用 |
|------|------|
| `--target PATH` | 指定安装位置（默认 `~/.local/share/collate`） |
| `--no-deps` | 跳过 `pip install`（已有环境时用） |
| `--no-runtimes` | 只克隆 + 装依赖，不做 runtime 接入 |
| `--dry-run` | 只打印将要执行的动作，不实际修改 |
| `--help` | 查看完整说明 |

通过管道传参：`curl ... | bash -s -- --target ~/tools/collate --no-deps`。

---

## 前置依赖

- macOS 或 Linux
- Python 3.9+
- poppler（`brew install poppler` / `apt install poppler-utils`）

一键脚本会检查 git / python3 / pip / poppler，缺失会打印安装命令但不会自动 sudo。

---

## 手动安装

```bash
git clone https://github.com/MidnightDarling/collate.git ~/.local/share/collate
cd ~/.local/share/collate
pip install --user -U -r requirements.txt
```

然后按下面的 runtime 分别接入。

### Claude Code

```
/plugin install /path/to/collate
```

或把仓库软链到 `~/.claude/plugins/collate`，Claude Code 启动时会自动发现。

Marketplace 分发路径（待发布）：`/plugin install collate`。

### OpenCode / Codex CLI

零配置：在仓库目录里启动即可。

```bash
cd ~/.local/share/collate
opencode    # 或 codex
```

两者都原生识别 `AGENTS.md`。

### Hermes agents

```bash
cd ~/.local/share/collate
hermes
```

想让 Hermes 像 Claude Code 那样用 `/collate:<skill>` 风格的 slash command，把每个 skill 软链到 `~/.hermes/skills/collate-*`（一键脚本会自动做）。

### Cursor

在使用 collate 的项目根创建 `.cursor/rules/collate.mdc`：

```markdown
---
description: collate agent contract
alwaysApply: true
---

See ~/.local/share/collate/AGENTS.md for the full agent contract.
Scripts live under ~/.local/share/collate/skills/*/scripts/*.py.
```

旧版 `.cursorrules` 也仍被支持。

### Gemini CLI

```bash
cd ~/.local/share/collate
gemini
```

首轮粘贴 `AGENTS.md` 作为会话上下文。Native `gemini-extension.json` 包装在路线图上。

---

## 首次运行（Claude Code 场景）

```
/collate:setup
```

setup skill 会引导注册 OCR 引擎凭据并检查 Python 依赖完整性。非 Claude Code 场景直接手动把 OCR 凭据写到 `~/.env` 即可（见下一节）。

---

## 环境变量

推荐在 `~/.env` 中配置：

```bash
OCR_ENGINE=mineru                # mineru（本地 CLI，默认）/ mineru-cloud / baidu
MINERU_API_KEY=sk-xxxx           # 仅 OCR_ENGINE=mineru-cloud 需要
BAIDU_OCR_API_KEY=xxxx           # 仅 OCR_ENGINE=baidu 需要
BAIDU_OCR_SECRET_KEY=xxxx        # 同上
```

MinerU API key 在 <https://mineru.net> 控制台获取；百度 OCR 凭据在百度智能云控制台"通用文字识别"页面获取。

完整环境变量清单与跨 runtime 注入方式见 [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) §12。

---

## 卸载

一键卸载：

```bash
rm -rf ~/.local/share/collate
rm -f  ~/.claude/plugins/collate       # 如已软链
rm -f  ~/.hermes/skills/collate-*      # 如已软链
```

Claude Code 用户也可以直接 `/plugin uninstall collate`。

插件不修改系统 PATH、不写入注册表、不启动后台进程——删目录即清理干净。

---

## 下一步

- 运行完整流程：参见 [README.md](README.md) 的 Workflow 章节
- 故障排查：[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- 插件内部架构：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 接入其他 agent 运行时：[docs/INTEGRATIONS.md](docs/INTEGRATIONS.md)

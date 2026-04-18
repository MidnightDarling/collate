# 安装指南

三个宿主，优先级从高到低。

---

## 推荐：Claude Code

### 1. 装 Claude Code

<https://www.anthropic.com/claude-code>

### 2. 装本插件

**方式 A：本地目录挂载**（推荐调试/首次尝试）

把整个 `historical-ocr-review/` 文件夹放到任意位置，比如 `~/plugins/`，然后在项目里：

```bash
# 方式 A1：用 /plugin 命令在 Claude Code 里加
/plugin install /path/to/historical-ocr-review
```

**方式 B：marketplace 安装**（已发布后）

```bash
/plugin install historical-ocr-review
```

### 3. 第一次用

```
/historical-ocr-review:setup
```

会引导你注册 MinerU key 并装 Python 依赖。

---

## 备选：Kimi CLI / MiniMax Agent

Kimi 和 MiniMax 的 agent 工具可以 **加载 SKILL.md 作为 knowledge**，但不能原生执行 Claude Code 的 plugin 命令。使用方式：

### 1. 把 skills 内容导入宿主的 knowledge

- **Kimi**：新建对话 → 上传 `skills/` 下所有 `SKILL.md` 和 `references/*.md` 作为上下文
- **MiniMax**：在 agent 设置里把 SKILL.md 内容贴进 system prompt，references 作为 knowledge base

### 2. 脚本在本地跑

```bash
# 装依赖
pip install opencv-python pillow requests python-dotenv markdown

# 设置 MinerU key
export MINERU_API_KEY=你的key
# 或者写进 ~/.env

# 预处理
python3 skills/prep-scan/scripts/dewatermark.py input.pdf

# OCR
python3 skills/ocr-run/scripts/mineru_client.py cleaned.pdf

# 转公众号 HTML
python3 skills/mp-format/scripts/md_to_wechat.py final.md
```

### 3. 校对 prompt

把 `agents/historical-proofreader.md` 的系统提示词 + 校对目标 Markdown 喂给 Kimi/MiniMax，它会按繁体古籍 / 民国排印 / 现代简体的知识回给你一份标红报告。

---

## 依赖清单

```
python >= 3.9
opencv-python
pillow
requests
python-dotenv
markdown
```

一行装齐：

```bash
pip install -U opencv-python pillow requests python-dotenv markdown
```

---

## 环境变量

在 `~/.env` 写：

```
MINERU_API_KEY=sk-xxxxxxxxxxxxxxxx
```

或导出到当前 shell：

```bash
export MINERU_API_KEY=sk-xxxxxxxxxxxxxxxx
```

key 从 <https://mineru.net> 注册后在控制台查。

---

## 卸载

Claude Code：

```
/plugin uninstall historical-ocr-review
```

纯本地用：删除 `historical-ocr-review/` 文件夹即可。不会留任何系统痕迹（不改 PATH、不写注册表、不开后台进程）。

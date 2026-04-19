# 安装

面向 Claude Code 的快速启动指南。其他 agent 运行时（Cursor、Codex CLI、Kimi K2、MiniMax Agent、Gemini CLI）的接入步骤见 [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md)。

---

## 前置依赖

- macOS 或 Linux
- Python 3.9+
- poppler（`brew install poppler` / `apt install poppler-utils`）

安装 Python 依赖：

```bash
pip install -U -r requirements.txt
```

---

## Claude Code 安装

**方式 A：本地目录挂载**（推荐用于调试与首次试用）

将仓库克隆至任意位置（如 `~/plugins/`），然后在 Claude Code 中：

```
/plugin install /path/to/collate
```

**方式 B：marketplace 安装**（待发布）

```
/plugin install collate
```

---

## 首次运行

```
/collate:setup
```

setup skill 会引导注册 OCR 引擎凭据并检查 Python 依赖完整性。

---

## 环境变量

推荐在 `~/.env` 中配置：

```
OCR_ENGINE=mineru                # mineru（本地 CLI，默认）/ mineru-cloud / baidu
MINERU_API_KEY=sk-xxxx           # 仅 OCR_ENGINE=mineru-cloud 需要
BAIDU_OCR_API_KEY=xxxx           # 仅 OCR_ENGINE=baidu 需要
BAIDU_OCR_SECRET_KEY=xxxx        # 同上
```

MinerU API key 在 <https://mineru.net> 控制台获取；百度 OCR 凭据在百度智能云控制台"通用文字识别"页面获取。

完整的环境变量清单与跨 runtime 注入方式见 [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) 第 9 节。

---

## 卸载

```
/plugin uninstall collate
```

非 Claude Code 场景：删除仓库目录即可。插件不修改系统 PATH、不写入注册表、不启动后台进程。

---

## 下一步

- 运行完整流程：参见 [README.md](README.md) 的 Workflow 章节
- 故障排查：[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- 插件内部架构：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 接入其他 agent 运行时：[docs/INTEGRATIONS.md](docs/INTEGRATIONS.md)

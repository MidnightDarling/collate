---
name: setup
description: 使用场景：用户在 Mac 上首次安装 historical-ocr-review 插件、运行 `/historical-ocr-review:setup`、或说出"配置 OCR 引擎""注册 MinerU""我有百度 OCR key""历史论文 OCR 怎么配""插件装好了下一步""第一次用这个"。凡是和"插件初始化""把 OCR 的 key 配好""装依赖"相关的请求都走这个 skill。它会引导历史文献研究者（可能是非技术背景）在 Mac 上完成 Python 依赖、poppler、OpenCV 的安装，并配置百度 OCR 或 MinerU 其中之一的 API key 到 ~/.env。这个 skill 一定要主动触发，即使用户没说"配置"两个字。
argument-hint: "(无参数)"
allowed-tools: Bash, Read, Write, Edit
---

# 首次配置 — 环境初始化指南

## Task

用户通常使用 Mac 处理历史文献扫描件（繁体古籍、民国排印本、现代简体论文），并非都具备技术背景。本 skill 的目标是在一次会话内完成三件事：

1. 建立本插件的 Python 运行环境（3.9+，opencv、pillow、poppler 等依赖）
2. 预装并预热 MinerU 本地 CLI（默认路径）；或按需启用百度 OCR / MinerU 云 API 兼容分支
3. 通过一次探活确认引擎可用

任一步失败时必须显性终止，不要跳过或静默兜底。

## Process

### Step 1：确认用户环境

首先确认：

- 用户是否用过命令行 / 终端？不熟悉终端的用户需要逐条解释命令含义。
- 默认走本地 MinerU CLI（无需账号、不上传、首次装机约 10 分钟、之后每份 PDF 约 90 秒）。
- 仅在用户明确表示"已有百度 OCR key 想复用"或"需要 MinerU 云 API"时，改走 Step 4A / 兼容分支，并说明这两条路径已非默认。

### Step 2：检查 Python（Mac）

```bash
python3 --version
```

**为什么要这步**：新 Mac 预装的 Python 可能是 3.8 或更旧，跑 PyPDF2 会报奇怪的错。

- 版本 ≥ 3.9 → 直接下一步
- 版本 < 3.9 或报 `command not found` → 让用户跑 `brew install python@3.11`（如果没装 Homebrew 先跑下面这句）

Homebrew 未安装时先装：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Homebrew 是 macOS 的包管理器，后续所有系统级依赖都通过它安装。

### Step 3：装所有依赖（一条命令）

```bash
brew install poppler
pip3 install -U -r "${CLAUDE_PLUGIN_ROOT}/requirements.txt"
```

`requirements.txt` 列了两组东西：

- **经典管道**：`opencv-python` / `pillow` / `pdf2image` / `PyPDF2` /
  `python-docx` 等——prep-scan / preview / to-docx / mp-format 用
- **MinerU 本地管道**：`mineru[pipeline]` + `torch` + `torchvision` +
  `shapely` + `scikit-image`——ocr-run 的默认路径用

整个 pip 过程约 5 分钟（包含 ~1 GB 的 torch）。如果 pip 报
`externally-managed-environment`（Homebrew Python 常见），加 `--user`：

```bash
pip3 install --user -U -r "${CLAUDE_PLUGIN_ROOT}/requirements.txt"
```

验证：

```bash
python3 -c "import cv2, PIL, requests, dotenv, markdown, PyPDF2, pdf2image, bs4, docx, mineru, torch; print('依赖齐全')"
which mineru
```

第二行应该打印 `mineru` 的路径（说明 CLI 装上了）。输出「依赖齐全」才算过。

### Step 3.5：预热 MinerU 模型（一次性）

第一次跑 `mineru` 会下载 ~2–3 GB 模型到 `~/.cache/huggingface/hub/`。
在正式 OCR 一份 PDF 前让它先下好，省得第一次跑 PDF 时卡住。

```bash
# tiny probe PDF — 让 mineru 触发模型下载，跑完立刻退出
TMP=$(mktemp -d)
cp "${CLAUDE_PLUGIN_ROOT}/examples/smoke.pdf" "$TMP/smoke.pdf" 2>/dev/null || \
  python3 -c "from reportlab.pdfgen import canvas; c = canvas.Canvas('$TMP/smoke.pdf'); c.drawString(100,750,'smoke'); c.save()"
mineru -p "$TMP/smoke.pdf" -o "$TMP" -b pipeline -m auto -l ch
```

看到 `Completed batch` 就算预热好了。约 4–8 分钟（取决于网速）。中国网
络建议事先开代理或 ModelScope 镜像：

```bash
export HF_ENDPOINT=https://hf-mirror.com      # HuggingFace 国内镜像
# 或：
export MINERU_MODEL_SOURCE=modelscope         # 走 ModelScope 下载
```

环境变量永久化可以追加到 `~/.zshrc`。

### Step 4（可选）：旧 OCR 引擎的兼容分支

**默认不需要做这一步**——本地 `mineru` 已经是主路径。只有这两种情况走：

- 用户说"我有百度 OCR key 想复用" → 分支 A
- 用户明确想走 MinerU 云 API（比如在 SSH 登录的没 GPU 的服务器上） → 分支 C

直接跳过 Step 4，走 Step 5 也可以。

#### 分支 A — 用百度 OCR（用户已有 key，可选兼容）

让用户提供：
- `BAIDU_OCR_API_KEY`
- `BAIDU_OCR_SECRET_KEY`

**百度 OCR 的 key 是一对**（API Key + Secret Key），用户在百度智能云控制台「通用文字识别」里能看到。如果用户只给一个，告诉用户去同一个控制台复制另一个。

写入 `~/.env`（追加或覆盖这两行，不要动别的）：

```
BAIDU_OCR_API_KEY=<用户给的>
BAIDU_OCR_SECRET_KEY=<用户给的>
OCR_ENGINE=baidu
```

验证（脚本自带，不要手写 curl，百度的鉴权比较绕）：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/ocr-run/scripts/baidu_client.py" --check-auth
```

返回 `AUTH_OK` → 继续。返回 `AUTH_FAIL` → key 或 secret 不对，让用户重查。

#### 分支 B — 注册 MinerU 云 API（可选）

向用户说明 MinerU 云 API 的注册步骤：

1. 访问 <https://mineru.net>，使用手机号注册
2. 登录后进入左侧栏「API 管理」→「新建 Token」
3. 复制生成的 key（以 `sk-` 开头）

拿到 key 后：

- 格式校验：应为 `sk-` 开头、约 64 位字母数字
- 写入 `~/.env`（追加或覆盖）：

```
MINERU_API_KEY=<用户提供的 key>
OCR_ENGINE=mineru-cloud
```

**不要把 key 内容回显到终端**——仅确认已写入。

验证：

```bash
MINERU_API_KEY=$(grep "^MINERU_API_KEY=" ~/.env | cut -d= -f2-) \
  curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $MINERU_API_KEY" \
  https://mineru.net/api/v4/extract/task
```

- `200` / `400` / `405` / `422` → key 合法（后三个是因为没传 body，不是认证失败）
- `401` → key 错了，让用户重配
- 其他 → 网络或服务问题，建议稍后重试

### Step 5：工作流概述

配置完成后，向用户概述后续 skill 链：

1. `prep-scan` — 对扫描版 PDF 做预处理，去水印、去馆藏章、可选裁边
2. `ocr-run` — 调用 MinerU / 百度 OCR 识别为 Markdown，附原图对照预览
3. `proofread` — 按文献类型（古籍 / 民国 / 现代）输出 A/B/C 分级校对清单
4. `diff-review` — 比对 raw.md 与 final.md，生成改动自审报告
5. `to-docx` — 导出学术规范 Word 稿
6. `mp-format` — 导出公众号 HTML

详见 README.md 的 Workflow 章节，以及各 skill 内部说明。

## 注意事项

- **不要把任何 API key 回显到终端**——始终通过 `~/.env` 文件传递。
- **任一步失败时显性终止**，不要跳过或伪装成功。
- 国内网络无法访问 PyPI 时，切换镜像：`pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple`。

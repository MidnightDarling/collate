---
name: setup
description: 使用场景：用户在 Mac 上首次安装 historical-ocr-review 插件、运行 `/historical-ocr-review:setup`、或说出"配置 OCR 引擎""注册 MinerU""我有百度 OCR key""历史论文 OCR 怎么配""插件装好了下一步""第一次用这个"。凡是和"插件初始化""把 OCR 的 key 配好""装依赖"相关的请求都走这个 skill。它会引导历史文献研究者（可能是非技术背景）在 Mac 上完成 Python 依赖、poppler、OpenCV 的安装，并配置百度 OCR 或 MinerU 其中之一的 API key 到 ~/.env。这个 skill 一定要主动触发，即使用户没说"配置"两个字。
argument-hint: "(无参数)"
allowed-tools: Bash, Read, Write, Edit
---

# 首次配置 — 15 分钟装机指南

## Task

用户是处理历史文献的研究者，Mac 用户，**可能是非技术背景**，日常需要把扫描版论文（繁体古籍、民国排印本、现代简体论文）整理发公众号或投稿。你的任务是在 15 分钟内让用户的 Mac 完成三件事：

1. 具备运行本插件的 Python 环境（3.9+、opencv、pillow、poppler）
2. 配置好 OCR 引擎——**百度 OCR（用户已有 key）** 或 **MinerU（推荐，需新注册）** 其中一个
3. 通过一次 API 探活，确认真的可用

失败时不要假装成功——用户明天要用这个干活。

## Process

### Step 1：判断用户的技术位置

一开始先问一句（原文输出）：

> 我会带你一步步装好。先确认一件事：
> 你是不是第一次用命令行 / 终端？
>
> （不用担心 OCR 引擎的账号——新版插件用 **本地 MinerU**，不需要任何 key
> 也不需要上传到云。首次装约 10 分钟，以后每份 PDF 90 秒左右跑完，
> 数据全程留在你电脑里。）

根据回答分支：
- **用户说"不懂终端"** → 把每个命令的作用用一句中文说清楚再让用户跑
- **其他回答** → 直接进 Step 2

**历史分支（仅在用户明说"我有百度 key 想复用"或"我想走 MinerU 云 API"时走）** →
Step 4B / 4C，但你要先告诉用户"那两条路已经不是默认，本地装效果更好且免账号"。

### Step 2：检查 Python（Mac）

```bash
python3 --version
```

**为什么要这步**：新 Mac 预装的 Python 可能是 3.8 或更旧，跑 PyPDF2 会报奇怪的错。

- 版本 ≥ 3.9 → 直接下一步
- 版本 < 3.9 或报 `command not found` → 让用户跑 `brew install python@3.11`（如果没装 Homebrew 先跑下面这句）

Homebrew 没装的情况下：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

告诉用户：这是 Mac 的软件管家，装一次受用一生。

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

#### 分支 B — 注册 MinerU

**原文给用户看**（照抄，不要改措辞）：

> MinerU 是上海 AI Lab 做的 PDF OCR 服务，对历史文献（繁体、竖排、古籍版式）的识别效果比通用 OCR 好一档。免费额度每月够用。注册步骤：
>
> 1. 打开 <https://mineru.net>
> 2. 右上角「登录/注册」，用手机号注册
> 3. 登录后左侧栏「API 管理」→「新建 Token」
> 4. Token 名字随便写（比如 `historical-ocr`）
> 5. 复制生成的 key（`sk-` 开头）
> 6. 粘贴回来给我

拿到 key 后：

- 格式校验：应该是 `sk-` 开头、64 位左右字母数字。不对就让用户重复制。
- 写 `~/.env`（追加或覆盖）：

```
MINERU_API_KEY=<用户给的>
OCR_ENGINE=mineru
```

**不要把 key 内容打到终端**——安全考虑。只确认「已保存」。

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

### Step 5：欢迎进入工作流

成功后，用中文告诉用户（照抄）：

> 装好了。接下来你的工作流：
>
> **① 拿到扫描版 PDF（比如档案局扫的民国报刊、知网下载的论文、古籍影印本）**
>
> 把 PDF 放到桌面或下载里，对我说「帮我处理这个 PDF」或跑：
> `/historical-ocr-review:prep-scan ~/Downloads/论文.pdf`
>
> 插件会去掉馆藏章、知网水印、页眉页脚。
>
> **② OCR**
>
> `/historical-ocr-review:ocr-run ~/Downloads/论文.prep/cleaned.pdf`
>
> 出来一份 Markdown 和一个左图右文的对照网页（preview.html），你可以先肉眼过一遍把明显错字改了。
>
> **③ 校对**
>
> `/historical-ocr-review:proofread ~/Downloads/论文.ocr/raw.md`
>
> 这一步是插件的核心——会按「繁体古籍 / 民国排印 / 现代简体」三套史学知识给你标红可疑字、异体字、专名、旧式标点。**所有改动都只是建议**，由你决定接受哪条。
>
> **④ 公众号排版**
>
> `/historical-ocr-review:mp-format ~/Downloads/论文.ocr/final.md`
>
> 生成微信公众号 HTML，复制到秀米或直接粘贴到公众号后台。

### Step 6：留个示例让用户试手

建议用户第一次不要拿重要的论文，先跑 `examples/` 里的示例 PDF 走一遍。熟悉流程再处理真稿。

## 注意事项

- **不要把任何 API key 打到屏幕**。这是基础安全，也避免用户截图发朋友圈时泄露。
- **遇到错误就停下报错**，不要"假装配置成功"。用户明天要用这个，带病上线会让用户对整个工具丧失信心。
- 如果用户装 pip 包时连不上 PyPI（国内网络），建议用户换源：`pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple`
- 全程中文，口气温和。用户是学者不是工程师。

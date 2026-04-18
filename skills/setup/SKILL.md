---
name: setup
description: 使用场景：用户在 Mac 上首次安装 historical-ocr-review 插件、运行 `/historical-ocr-review:setup`、或说出"配置 OCR 引擎""注册 MinerU""我有百度 OCR key""历史论文 OCR 怎么配""插件装好了下一步""第一次用这个"。凡是和"插件初始化""把 OCR 的 key 配好""装依赖"相关的请求都走这个 skill。它会引导社科院历史学者（非技术背景）在 Mac 上完成 Python 依赖、poppler、OpenCV 的安装，并配置百度 OCR 或 MinerU 其中之一的 API key 到 ~/.env。这个 skill 一定要主动触发，即使用户没说"配置"两个字。
argument-hint: "(无参数)"
allowed-tools: Bash, Read, Write, Edit
---

# 首次配置 — 给历史学者的 15 分钟装机指南

## Task

用户是社科院做历史研究的学者，Mac 用户，**非技术背景**，但日常需要把扫描版论文（繁体古籍、民国排印本、现代简体论文）整理发公众号。你的任务是在 15 分钟内让她的 Mac 完成三件事：

1. 具备运行本插件的 Python 环境（3.9+、opencv、pillow、poppler）
2. 配置好 OCR 引擎——**百度 OCR（她已有 key）** 或 **MinerU（推荐，需新注册）** 其中一个
3. 通过一次 API 探活，确认真的可用

失败时不要假装成功——她明天要用这个干活。

## Process

### Step 1：判断她的技术位置

一开始先问一句（原文输出）：

> 我会带你一步步装好。先确认两件事：
> 1. 你是不是第一次用命令行/终端？
> 2. 你有百度 OCR 的 API key 吗？如果有，我们用你现成的；没有，我推荐你注册 MinerU（对历史文献效果更好，免费额度够日常用）。

根据回答分支：
- **她说"不懂终端"** → 把每个命令的作用用一句中文说清楚再让她跑
- **她说"有百度 key"** → Step 4 走 A 分支
- **她说"没有 / 注册 MinerU"** → Step 4 走 B 分支
- **她说"都给我配一下"** → 两个都配，优先用百度（她已有）

### Step 2：检查 Python（Mac）

```bash
python3 --version
```

**为什么要这步**：新 Mac 预装的 Python 可能是 3.8 或更旧，跑 PyPDF2 会报奇怪的错。

- 版本 ≥ 3.9 → 直接下一步
- 版本 < 3.9 或报 `command not found` → 让她跑 `brew install python@3.11`（如果没装 Homebrew 先跑下面这句）

Homebrew 没装的情况下：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

告诉她：这是 Mac 的软件管家，装一次受用一生。

### Step 3：装 Python 依赖和 poppler

```bash
brew install poppler
pip3 install -U opencv-python pillow requests python-dotenv markdown PyPDF2 pdf2image beautifulsoup4
```

**为什么装这些**：
- `opencv-python`, `pillow` → 去水印、切页、裁边
- `pdf2image` + `poppler` → PDF 拆成图
- `requests`, `python-dotenv` → 调 OCR API + 读 `~/.env`
- `markdown`, `beautifulsoup4` → Markdown 转公众号 HTML

如果 pip 报 `externally-managed-environment`（Homebrew Python 常报），改：

```bash
pip3 install --user -U opencv-python pillow requests python-dotenv markdown PyPDF2 pdf2image beautifulsoup4
```

验证：

```bash
python3 -c "import cv2, PIL, requests, dotenv, markdown, PyPDF2, pdf2image, bs4; print('依赖齐全')"
```

输出「依赖齐全」才算过。

### Step 4：配置 OCR 引擎

#### 分支 A — 用百度 OCR（她已有 key）

让她提供：
- `BAIDU_OCR_API_KEY`
- `BAIDU_OCR_SECRET_KEY`

**百度 OCR 的 key 是一对**（API Key + Secret Key），她在百度智能云控制台「通用文字识别」里能看到。如果她只给一个，告诉她去同一个控制台复制另一个。

写入 `~/.env`（追加或覆盖这两行，不要动别的）：

```
BAIDU_OCR_API_KEY=<她给的>
BAIDU_OCR_SECRET_KEY=<她给的>
OCR_ENGINE=baidu
```

验证（脚本自带，不要手写 curl，百度的鉴权比较绕）：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/ocr-run/scripts/baidu_client.py" --check-auth
```

返回 `AUTH_OK` → 继续。返回 `AUTH_FAIL` → key 或 secret 不对，让她重查。

#### 分支 B — 注册 MinerU

**原文给她看**（照抄，不要改措辞）：

> MinerU 是上海 AI Lab 做的 PDF OCR 服务，对历史文献（繁体、竖排、古籍版式）的识别效果比通用 OCR 好一档。免费额度每月够用。注册步骤：
>
> 1. 打开 <https://mineru.net>
> 2. 右上角「登录/注册」，用手机号注册
> 3. 登录后左侧栏「API 管理」→「新建 Token」
> 4. Token 名字随便写（比如 `historical-ocr`）
> 5. 复制生成的 key（`sk-` 开头）
> 6. 粘贴回来给我

拿到 key 后：

- 格式校验：应该是 `sk-` 开头、64 位左右字母数字。不对就让她重复制。
- 写 `~/.env`（追加或覆盖）：

```
MINERU_API_KEY=<她给的>
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
- `401` → key 错了，让她重配
- 其他 → 网络或服务问题，建议稍后重试

### Step 5：欢迎进入工作流

成功后，用中文告诉她（照抄）：

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

### Step 6：留个示例让她试手

建议她第一次不要拿重要的论文，先跑 `examples/` 里的示例 PDF 走一遍。熟悉流程再处理真稿。

## 注意事项

- **不要把任何 API key 打到屏幕**。这是基础安全，也避免她截图发朋友圈时泄露。
- **遇到错误就停下报错**，不要"假装配置成功"。她明天要用这个，带病上线会让她对整个工具丧失信心。
- 如果她装 pip 包时连不上 PyPI（国内网络），建议她换源：`pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple`
- 全程中文，口气温和。她是学者不是工程师。

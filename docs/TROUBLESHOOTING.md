---
title: Troubleshooting
description: historical-ocr-review 插件常见报错、成因、兜底方案
author: Claude Opus 4.7
date: 2026-04-19
status: v0.1.0
---

# Troubleshooting

按出错所在的 skill 分类。找到你的报错复制到本页搜，能命中就按方案操作。

---

## 安装 / setup

### `command not found: python3`

Mac 没装 Python 3。跑：

```bash
brew install python@3.11
```

若没装 Homebrew，先：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### pip 报 `externally-managed-environment`

Homebrew Python 的保护机制。加 `--user`：

```bash
pip3 install --user -U opencv-python pillow requests python-dotenv markdown PyPDF2 pdf2image beautifulsoup4
```

### PyPI 连不上（国内网络）

换源：

```bash
pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 百度 OCR auth 失败（setup 阶段返回 `AUTH_FAIL`）

- 确认 `BAIDU_OCR_API_KEY` 和 `BAIDU_OCR_SECRET_KEY` 都填了（是一对，少一个不行）
- 从百度智能云控制台 "通用文字识别" 页面复制，不要从其他服务页
- 两个 key 之间不要混空格、引号

### MinerU auth 失败

- Key 格式应该是 `sk-` 开头，约 64 位
- 从 <https://mineru.net> 控制台 "API 管理" 页的 Token 复制完整
- 网络不通（国内偶发）可以用 `curl -v https://mineru.net/api/v4/extract/task` 测连通性

---

## prep-scan

### `NOT_A_PDF`

传的文件不是 PDF。常见情况：用户传了 `.caj`（知网专有格式）。建议：

- 知网后台有 "导出 PDF" 选项，用那个
- 或 CAJViewer / CAJ-PDF 转换工具

### `poppler missing`

pdf2image 需要 poppler 后端：

```bash
brew install poppler
```

### `libGL error`

OpenCV 后端问题：

```bash
brew reinstall opencv
pip3 install -U --force-reinstall opencv-python
```

### 清理后正文被误擦（visual-preview 里看到红色覆盖落在文字上）

重跑 prep-scan 时加 `--keep-color`（保留彩色通道，不擦红蓝印）：

```
/historical-ocr-review:prep-scan ~/Downloads/论文.pdf --keep-color
```

如果仍误擦，说明扫描件正文本身很淡：

- 不要用 `--aggressive`（它把阈值放宽，会更激进）
- 或关闭水印处理，只做裁边：暂不支持该细粒度开关，后续版本会加 `--only-margin-trim`

### 水印还在（清理后仍能看到）

加 `--aggressive` 阈值放宽：

```
/historical-ocr-review:prep-scan ~/Downloads/论文.pdf --aggressive
```

### PDF 加密 / 带密码

Mac "预览.app" 打开 → 文件 → 导出为 PDF，就会去密码。然后再跑 prep-scan。

### PDF 超过 200 页报内存错 / 慢

建议按章节拆分：

```bash
# 拆前 50 页
python3 -c "
import PyPDF2
r = PyPDF2.PdfReader('论文.pdf')
w = PyPDF2.PdfWriter()
for p in r.pages[:50]:
    w.add_page(p)
with open('论文_ch1.pdf', 'wb') as f:
    w.write(f)
"
```

---

## visual-preview

### `cleaned_pct` 全是 `—`（热图没生成）

看 stderr 有没有 "读图失败"。若是，可能是：

- 有些 PNG 被损坏或格式特殊（带 alpha 通道的 16-bit PNG）
- 该文件不可读（权限问题）

单独重新跑一下 prep-scan，看有没有报警。

### 热图生成太慢 / 产物太大

200 页稿子热图会产生 ~300 MB。暂时解决：

- 加 `--sample 20` 只处理前 20 页（够判断清理质量）
- 或 `--no-diff` 跳过热图，只出 before/after 对比

未来会加 `--low-res-diff` 自动下采样。

---

## ocr-run

### MinerU 返回 `401`

API key 失效或错。重跑 setup：

```
/historical-ocr-review:setup
```

### MinerU 返回 `429`

免费额度用完。切百度：

```
/historical-ocr-review:ocr-run cleaned.pdf --engine=baidu
```

或等次月配额重置。

### 百度 `error_code: 14`

access_token 过期。删缓存：

```bash
rm ~/.cache/baidu_ocr_token.json
```

然后重跑，会自动换新 token。

### 百度 `error_code: 17`

次数配额耗尽（免费版每月 1000 次高精度）。去百度智能云控制台查余额，或切 MinerU。

### `raw.md < 500 字节`（几乎没识别出内容）

- PDF 是空白或加密 → 确认 PDF 能打开
- prep-scan 把正文误擦了 → 打开 visual-preview 核查

### 超时（> 15 分钟）

PDF 太大。按章节拆（见 prep-scan 章节的 "PDF 超过 200 页"）。

### 繁体被识别成简体

加 `--lang=zh-hant`：

```
/historical-ocr-review:ocr-run cleaned.pdf --lang=zh-hant
```

### 竖排古籍出来是横排乱序

加 `--layout=vertical`：

```
/historical-ocr-review:ocr-run cleaned.pdf --layout=vertical
```

### raw.md 每行一段（百度 OCR 常见）

百度的段落切分启发式不够好。换 MinerU：

```
/historical-ocr-review:ocr-run cleaned.pdf --engine=mineru
```

---

## proofread

### agent 标注看起来过少（才 5 条）

两种可能：

1. OCR 质量极好——打开 `preview.html` 肉眼抽几页核对确认
2. agent 没真跑 checklist——看 `raw.review.md` 末尾的 **Checklist 执行证明表**，若数字为 0 或格式异常，让 agent 重跑

### A 类超过 50 条

OCR 质量有问题。建议：

- 重跑 prep-scan 检查清理是否过激
- 换引擎（MinerU ↔ 百度）对比
- `raw.md` 里大量 `?` 或 `□` 是字形识别失败的信号

### agent 漏了"曰/日"这种经典错

这是曾经发生过的问题（见 [docs/ARCHITECTURE.md](ARCHITECTURE.md) 的 "核心设计决策" 第 2 条）。现在 agent 走强制 checklist，报告里必须列"曰/日 扫描命中 N 处"。如果再发生漏判，让 agent 复跑——具体指令：

```
你上次的校对报告里 Checklist 执行证明表对 "曰/日" 写的命中数是 N，
但我在 raw.md 里 `grep -n "曰\|日" raw.md | wc -l` 得到 M。
请重新跑一次 Step 2.1 并更新清单。
```

---

## diff-review

### 报告提示 "段落数差 > 80%，返回 3"

JN 改的 `final.md` 和传入的 `raw.md` 不是同一版。常见：

- 改的是旧版 `raw.md`（OCR 之后又跑过一次 ocr-run，新 raw 覆盖了旧 raw）
- `final.md` 经过了其他工具处理（比如 Word 回导入）

确认版本一致后重跑。

### 所有 A 类都判为 "漏改"

看 agent 的建议是不是关键字抽不出来（比如 "核对原书" 这种纯建议）。`diff-review` 会保守判为 `rejected_or_missed`——这不一定是真的漏，JN 自己看即可。

### A1（全文十余处）等多锚定条目归 "未锚定"

已知限制：当前版本的 `parse_review` 只抓 header 里的单个 Line 号。A1 这种 header 写 "全文十余处"、详情里列多行 Line 的条目会归为 unanchored。

下一版会扫条目正文里所有 `Line (\d+)` 作为额外锚点。

---

## to-docx

### `python-docx` 报错

```bash
pip3 install -U python-docx
```

### 字体丢失（.docx 打开是默认字体）

Mac 应自带宋体 / 黑体。英文版 macOS 可能没装中文字体：

- 系统偏好设置 → 字体册 → 检查 SimSun / SimHei 是否存在
- 没有的话手动下载字体（注意版权）

### 图片丢失

Markdown 里图片路径是相对路径，脚本按三个候选位置找：`path`、`md_dir / path`、`md_dir / 'assets' / path.name`。都找不到会在 Word 里显示 `[图片缺失：xxx]`。确认 `.ocr/assets/` 目录里有图片文件。

### 脚注显示为 `[1](内容)` 不是 Word 原生脚注

**已知限制**：python-docx 不支持原生脚注，当前实现是上标 `[N]` + 括注内容。SKILL 里说的 "Word 原生脚注" 和实际有差——Anthropic 官方 `docx` skill 可做原生脚注，本插件当前用不到。

解决：打开 .docx 手动把上标改成 Word 脚注（插入 → 脚注）。

---

## mp-format

### OpenCC 未安装

```bash
pip3 install opencc-python-reimplemented
```

### 公众号后台粘贴后样式丢失

切 "html 模式" 粘贴（而不是富文本模式）。富文本模式会剥离 inline style。

### 图片没渲染

公众号后台不支持相对路径引用本地图。需要：

1. 在公众号后台先上传图片到 "图片素材库"
2. 生成的 HTML 里 `<img src>` 改为图片素材的 URL

暂无自动化方案，手动补图。

---

## 通用

### Claude Code 认不出 skill

检查：

1. 插件是否正确安装：`/plugin list`
2. `.claude-plugin/plugin.json` 格式是否正确（尤其 `name` 字段）
3. `skills/<name>/SKILL.md` 的 frontmatter 是否有 `name` 字段

### `${CLAUDE_PLUGIN_ROOT}` 未展开

老版 Claude Code 不支持。升级到 Claude Code 2.x+。

### 所有 skill 都找不到

可能是插件未激活。在项目里跑 `/plugin install <path-to-plugin>` 重装。

### agent 调用失败

确认 `agents/historical-proofreader.md` 的 frontmatter 里 `name` 字段是 `historical-proofreader`（和引用它的 skill 一致）。

---

## 还是搞不定

开 issue，带上：

1. **完整报错信息**（不是截取的片段）
2. **复现命令**（你敲了什么）
3. **环境**：Mac 版本、Python 版本、Claude Code 版本
4. **相关文件头部**：`raw.md` / `meta.json` / `raw.review.md` 前 20 行
5. **你的预期** vs **实际结果**

越详细越快修好。

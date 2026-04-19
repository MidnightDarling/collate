---
title: Troubleshooting
description: collate 插件常见报错、成因、兜底方案
author: [Alice, Claude Opus 4.7, GPT-5.4]
date: 2026-04-19
status: v0.1.0
---

# Troubleshooting

按出错所在的 skill 分类索引。将报错信息复制到本页搜索，命中条目后按方案操作。

---

## 安装 / setup

### `command not found: python3`

Mac 未安装 Python 3。执行：

```bash
brew install python@3.11
```

若未安装 Homebrew，先执行：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### pip 报 `externally-managed-environment`

Homebrew Python 的保护机制，加 `--user` 绕过：

```bash
pip3 install --user -U opencv-python pillow requests python-dotenv markdown PyPDF2 pdf2image beautifulsoup4
```

### PyPI 连不上（国内网络）

换源：

```bash
pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 百度 OCR auth 失败（setup 阶段返回 `AUTH_FAIL`）

- 确认 `BAIDU_OCR_API_KEY` 与 `BAIDU_OCR_SECRET_KEY` 均已配置（两者成对，缺一不可）
- 从百度智能云控制台"通用文字识别"页面复制，请勿从其他服务页获取
- 两个 key 之间不得混入空格或引号

### MinerU auth 失败

- Key 格式应以 `sk-` 开头，长度约 64 位
- 从 <https://mineru.net> 控制台"API 管理"页的 Token 完整复制
- 网络不通（国内偶发）可用 `curl -v https://mineru.net/api/v4/extract/task` 测试连通性

---

## prep-scan

### `NOT_A_PDF`

传入的文件不是 PDF。常见情况：传入了 `.caj`（知网专有格式）。处理方式：

- 知网后台提供"导出 PDF"选项
- 或使用 CAJViewer / CAJ-PDF 转换工具

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

### 清理后正文被误擦（visual-preview 中红色覆盖落在文字上）

重跑 prep-scan 时追加 `--keep-color`（保留彩色通道，不擦除红蓝印记）：

```
/collate:prep-scan ~/Downloads/论文.pdf --keep-color
```

若仍误擦，表明扫描件正文本身较淡：

- 勿使用 `--aggressive`（该参数放宽阈值，结果更激进）
- 或关闭水印处理、仅做裁边：当前版本暂不支持此细粒度开关，后续版本将引入 `--only-margin-trim`

### 水印残留（清理后仍可见）

追加 `--aggressive` 放宽阈值：

```
/collate:prep-scan ~/Downloads/论文.pdf --aggressive
```

### PDF 加密 / 带密码

用 Mac 预览.app 打开 → 文件 → 导出为 PDF，即可去除密码保护，然后再跑 prep-scan。

### PDF 超过 200 页报内存错或执行缓慢

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

### `cleaned_pct` 全为 `—`（热图未生成）

查看 stderr 是否包含"读图失败"。如有，可能原因：

- PNG 损坏或格式特殊（如带 alpha 通道的 16-bit PNG）
- 文件不可读（权限问题）

单独重跑 prep-scan，观察是否有警告。

### 热图生成缓慢 / 产物体积过大

200 页稿件热图约产生 300 MB。临时方案：

- 追加 `--sample 20` 仅处理前 20 页（足以判断清理质量）
- 或 `--no-diff` 跳过热图，仅输出 before/after 对比

后续版本将引入 `--low-res-diff` 自动下采样。

---

## ocr-run

### MinerU 返回 `401`

API key 失效或错误。重跑 setup：

```
/collate:setup
```

### MinerU 返回 `429`

免费额度耗尽。切换至百度：

```
/collate:ocr-run cleaned.pdf --engine=baidu
```

或等待次月配额重置。

### 百度 `error_code: 14`

access_token 过期。删除缓存：

```bash
rm ~/.cache/baidu_ocr_token.json
```

重跑后将自动刷新 token。

### 百度 `error_code: 17`

调用次数配额耗尽（免费版每月 1000 次高精度）。前往百度智能云控制台查看余额，或切换至 MinerU。

### `raw.md < 500 字节`（几乎未识别出内容）

- PDF 为空白或加密 → 确认 PDF 可正常打开
- prep-scan 误擦正文 → 打开 visual-preview 核查

### 超时（> 15 分钟）

PDF 体量过大。按章节拆分（见 prep-scan 章节"PDF 超过 200 页"）。

### 繁体被识别为简体

追加 `--lang=zh-hant`：

```
/collate:ocr-run cleaned.pdf --lang=zh-hant
```

### 竖排古籍输出为横排乱序

追加 `--layout=vertical`：

```
/collate:ocr-run cleaned.pdf --layout=vertical
```

### raw.md 一行一段（百度 OCR 常见）

百度的段落切分启发式精度不足。切换至 MinerU：

```
/collate:ocr-run cleaned.pdf --engine=mineru
```

---

## proofread

### agent 标注过少（仅 5 条左右）

可能原因：

1. OCR 质量极高——打开 `preview.html` 抽样核对若干页确认
2. agent 未真正执行 checklist——查看 `raw.review.md` 末尾的 **Checklist 执行证明表**；若数字为 0 或格式异常，请 agent 重跑

### A 类超过 50 条

OCR 质量存在问题。建议：

- 重跑 prep-scan 确认清理未过度
- 切换引擎（MinerU ↔ 百度）对比
- `raw.md` 中大量 `?` 或 `□` 是字形识别失败的信号

### agent 漏判"曰/日"等经典错误

这是早期版本已出现过的问题（见 [docs/ARCHITECTURE.md](ARCHITECTURE.md) "核心设计决策"第 2 条）。现版本 agent 走强制 checklist，报告必须列出"曰/日 扫描命中 N 处"。若再次漏判，请 agent 复跑——示例指令：

```
你上次的校对报告中 Checklist 执行证明表对 "曰/日" 记录的命中数为 N，
但 `grep -n "曰\|日" raw.md | wc -l` 返回 M。
请重新执行 Step 2.1 并更新清单。
```

---

## diff-review

### 报告提示"段落数差 > 80%，返回 3"

用户修改的 `final.md` 与传入的 `raw.md` 版本不一致。常见情况：

- 修改的是旧版 `raw.md`（OCR 后再次执行 ocr-run，新 raw 覆盖了旧版）
- `final.md` 经过其他工具处理（如 Word 回导入）

确认版本一致后重跑。

### 所有 A 类均判为"漏改"

检查 agent 的建议是否无法抽出关键字（如"核对原书"一类纯建议）。`diff-review` 会保守判为 `rejected_or_missed`——此类情况不一定是真正漏改，用户自行核对即可。

### A1（全文十余处）等多锚定条目归"未锚定"

已知限制：当前版本的 `parse_review` 仅抓取 header 中的单个 Line 号。header 写"全文十余处"、正文列多行 Line 的条目会归为 unanchored。

下一版本将扫描条目正文中所有 `Line (\d+)` 作为额外锚点。

---

## to-docx

### `python-docx` 报错

```bash
pip3 install -U python-docx
```

### 字体缺失（.docx 打开为默认字体）

Mac 默认自带宋体 / 黑体。英文版 macOS 可能未安装中文字体：

- 系统偏好设置 → 字体册 → 确认 SimSun / SimHei 存在
- 如缺失则手动下载字体（注意版权）

### 图片丢失

Markdown 中图片路径为相对路径，脚本按三个候选位置查找：`path`、`md_dir / path`、`md_dir / 'assets' / path.name`。三者均未命中时在 Word 中显示 `[图片缺失：xxx]`。请确认 `.ocr/assets/` 目录包含所需图片文件。

### 脚注显示为 `[1](内容)`，而非 Word 原生脚注

**已知限制**：python-docx 不支持原生脚注，当前实现采用上标 `[N]` + 括注内容。SKILL 中描述的"Word 原生脚注"与实际实现存在差异——Anthropic 官方 `docx` skill 支持原生脚注，但本插件当前未接入。

解决：打开 .docx 后手动将上标转为 Word 脚注（插入 → 脚注）。

---

## mp-format

### OpenCC 未安装

```bash
pip3 install opencc-python-reimplemented
```

### 公众号后台粘贴后样式丢失

切换至"html 模式"粘贴（而非富文本模式）。富文本模式会剥离 inline style。

### 图片未渲染

公众号后台不支持相对路径引用本地图片。需要：

1. 在公众号后台将图片上传至"图片素材库"
2. 将生成 HTML 中的 `<img src>` 替换为图片素材 URL

暂无自动化方案，需手动补图。

---

## 通用

### Claude Code 认不出 skill

检查：

1. 插件是否正确安装：`/plugin list`
2. `.claude-plugin/plugin.json` 格式是否正确（尤其 `name` 字段）
3. `skills/<name>/SKILL.md` 的 frontmatter 是否有 `name` 字段

### `${CLAUDE_PLUGIN_ROOT}` 未展开

旧版 Claude Code 不支持，请升级至 Claude Code 2.x+。

### 所有 skill 均无法发现

可能是插件未激活。在项目中执行 `/plugin install <path-to-plugin>` 重新安装。

### agent 调用失败

确认 `agents/historical-proofreader.md` 的 frontmatter `name` 字段为 `historical-proofreader`（与引用它的 skill 保持一致）。

---

## 未能解决

请提交 issue，并附带以下信息：

1. **完整报错信息**（非截断片段）
2. **复现命令**（具体输入）
3. **运行环境**：Mac 版本、Python 版本、Claude Code 版本
4. **相关文件头部**：`raw.md` / `meta.json` / `raw.review.md` 前 20 行
5. **预期结果** vs **实际结果**

信息越详细，修复越快。

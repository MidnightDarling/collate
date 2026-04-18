# historical-ocr-review

![](assets/readme-hero-v2.png)

> 建立：2026-04-19 · 作者：Claude Opus 4.7 与 Alice 共笔

给历史研究者的论文 OCR 校对工作流。一个装上就能用的 Claude Code 插件。把扫描版论文 PDF 整理成 Word 稿（供学界交流）和公众号 HTML（供公众阅读），全流程八个 skill、一条主线，每一步都能看见、能回滚、能复查。

---

## 它解决什么问题

历史研究者的日常：从知网、读秀、国图扫描库、档案馆数字资源、古籍数据库下载扫描 PDF → 整理成 Word 稿投期刊 → 改写成推文发公众号。

这个流程的痛点：

- 扫描件带馆藏章、数据库水印、页眉页脚——**干扰 OCR**
- OCR 结果有错字、标点漂移、段落切错、脚注被识为公式——**需要校对**
- 校对工作量大，人工过稿时**容易漏错**，过完也**不知道自己接受了哪些改动**
- 最终交付要两份：**Word（学界）+ 公众号 HTML（公众）**，格式要求不一样

这个插件覆盖全链路，**每一步都有质检闸门让你核对**：

```
PDF
 │  prep-scan        去水印 / 去馆藏章 / 裁页眉页脚
 ▼
清理后的 PDF + 每页 PNG
 │  visual-preview   可视化闸门：确认清理没误伤正文
 ▼
 │  ocr-run          MinerU 或百度 OCR → Markdown + 对照 HTML
 ▼
raw.md（OCR 原始稿）
 │  proofread        调用 historical-proofreader agent，按强制 checklist
 ▼                   输出 A/B/C 三类分级标注清单（不改原文）
raw.review.md（校对清单）
 │  （你按清单改 raw.md → final.md）
 ▼
final.md（你的定稿）
 │  diff-review      核对闸门：接受了哪些、漏改了哪些、自创了哪些
 ▼
 │  to-docx          社科类学术规范 Word 稿
 │  mp-format        公众号推文 HTML（带内联 CSS，可直接粘贴）
 ▼
final.docx + final.mp.html
```

**核心原则**：AI 不替你做学术判断。校对阶段只标注可疑处，改不改由你决定。清理、裁边、格式转换自动做，但每一步都弹出可视化让你复查。

---

## 谁适合用

- 人文社科研究者，尤其历史、政治学、社会学方向
- Mac 用户（Windows / Linux 未测试）
- 日常需要处理扫描版论文 PDF
- 有公众号推送需求

不要求会写代码。终端命令都有中文说明，遇到报错会给可操作的兜底方案。

---

## 三类文献都支持

| 文献类型 | 典型问题 | 插件怎么做 |
|---------|---------|-----------|
| **现代简体论文** | 扫描噪点、字形混淆（曰/日、己/已/巳）、标点漂移、参考文献格式 | 加载现代简体校对知识库；按 GB/T 7714 规范提示 |
| **民国排印本** | 繁简字形并存、旧式标点、译名过渡期（"莎翁"=莎士比亚）、新旧地名（北京/北平按年代） | 加载民国知识库；人名地名核对提示 |
| **繁体古籍** | 异体字、避讳字、竖排、无标点、版心鱼尾 | 加载古籍知识库；异体字不强改，避讳字只提醒 |

类型自动判定，也可手动指定 `--type=classics|republican|modern`。

---

## 八个 Skill

### 1. setup — 首次配置

首次使用跑：

```
/historical-ocr-review:setup
```

引导你在 Mac 上完成 Python 依赖、poppler、OpenCV 安装，配置 **百度 OCR**（你有 key 就用）或 **MinerU**（推荐新注册，历史文献效果好）其中一个。15 分钟装完，走一次 API 探活确认可用。

**触发词**：`装好了`、`第一次用`、`配置 OCR`、`注册 MinerU`、`我有百度的 key`

### 2. prep-scan — PDF 预处理

```
/historical-ocr-review:prep-scan ~/Downloads/论文.pdf
```

把 PDF 拆成 PNG，去掉：

- **彩色馆藏章**（HSV 色域分离 + 形状判定，保留朱批、去馆藏章）
- **灰度对角水印**（CNKI / 维普 / 读秀常见）
- **浅灰重复水印**（形态学顶帽变换）
- **页眉页脚**（现代期刊默认裁 8% 上下，古籍 / 档案用 `--no-margin-trim` 保留）

产物放在 PDF 同级 `.prep/` 目录，不污染源文件。

**触发词**：`去水印`、`去馆藏章`、`预处理`、`清理扫描件`、`知网水印`、`读秀水印`

### 3. visual-preview — 清理效果可视化

```
/historical-ocr-review:visual-preview ~/Downloads/论文.prep
```

弹 HTML：每页三态切换（**原图 / 清理后 / 差异热图**），顶栏汇总（总页数、平均清理比例、裁边比例、异常页）。差异热图用半透明红色高亮擦掉的像素——一眼就能看出 prep-scan 有没有误伤正文。

清理率 > 20% 的页自动标红提醒。

**触发词**：`看看清理效果`、`对比一下`、`擦掉了什么`、`效果怎么样`、`让我看看结果`

### 4. ocr-run — OCR 识别

```
/historical-ocr-review:ocr-run ~/Downloads/论文.prep/cleaned.pdf
```

根据 `~/.env` 里 `OCR_ENGINE=mineru | baidu` 自动选引擎。支持 `--layout=horizontal|vertical`、`--lang=zh-hans|zh-hant|mixed` hint 给引擎更准的识别。

产物：

- `raw.md`——OCR 原始 Markdown
- `preview.html`——原图左 / OCR 右并排，`contenteditable` 可直接改错字
- `meta.json`——引擎信息、耗时、低置信度页

**触发词**：`跑 OCR`、`转文字`、`识别`、`MinerU`、`百度 OCR`

### 5. proofread — 校对

```
/historical-ocr-review:proofread ~/Downloads/论文.ocr/raw.md
```

调用 `historical-proofreader` agent，按**强制 checklist** 扫描：

- **Step 1 结构预检**：H1/H2/H3 计数、孤立废字符、括号配对、LaTeX 公式包裹数字、英文合字候选、段末逗号断裂候选、低置信度页
- **Step 2 字形扫描**：按文献类型加载的 reference 逐对 grep（曰/日、夹/央、完/究、戊戌纪年…）
- **Step 3 规范扫描**：中英标点混用、省略号、引号嵌套、括号全半角、DOI/ISSN 字符
- **Step 4 跨段一致性**：段末逗号核查、重复段检测、低置信度页加倍核
- **Step 5 专名**：人名 / 地名 / 机构需核对的 C 类条目

输出 `raw.review.md`——A（OCR 错） / B（学术规范） / C（存疑待考）三类分级清单，每条带行号 + 原文片段 + 建议 + 理由。**不改原文**。

报告末尾附 **Checklist 执行证明表**——每项 grep 的命中数，证明真跑过而非凭感觉。

**触发词**：`校对`、`看看这份稿子`、`有没有 OCR 错`、`检查专名`、`标点对不对`

### 6. diff-review — 校对核对闸门

你按 `raw.review.md` 改完 → 保存为 `final.md` 后：

```
/historical-ocr-review:diff-review raw.md final.md
```

段落级 diff HTML，关联 `raw.review.md` 标注：

- **接受的 agent 建议**（accepted）
- **拒绝或漏改**（rejected_or_missed）——重点核！
- **自创改动**（own_edit）——agent 没标但你改了
- **未锚定标注**（unanchored）——如"全文散见"这类无单行号条目

顶栏统计 + 每段 before/after 字符级 diff + 关联标注。

**触发词**：`看我改了哪些`、`对比一下`、`diff`、`我漏改了啥`、`核对改动`

### 7. to-docx — Word 稿生成

```
/historical-ocr-review:to-docx final.md --template=humanities
```

符合社科类学术规范：宋体正文 / 黑体标题 / 12pt 小四 / 段首缩进 2 字 / 1.5 行距 / 上下 2.54 cm、左右 3.18 cm 页边距 / 脚注连续编号 / 中文引号规范。

三个模板：`humanities`（默认）/ `sscilab`（社科院格式）/ `simple`。

**触发词**：`转成 Word`、`生成 docx`、`期刊投稿`、`学术规范排版`

### 8. mp-format — 公众号推文

```
/historical-ocr-review:mp-format final.md --byline="作者·单位" --source="《刊物》期数"
```

生成 `final.mp.html` + `final.mp.md`（秀米兼容）。特点：

- 全内联 CSS（公众号剥离外链样式）
- 繁简保护模式：引文保留繁体，正文简化
- 引用框 / 脚注 / 图片题注样式
- 作者栏 + 来源卡片

**触发词**：`发公众号`、`秀米`、`壹伴`、`做成推文`

---

## 安装

### Claude Code（推荐）

```bash
# 方式 A：本地目录挂载（调试 / 首次）
/plugin install /path/to/historical-ocr-review

# 方式 B：marketplace（发布后）
/plugin install historical-ocr-review
```

第一次跑 `/historical-ocr-review:setup` 完成环境配置。

### Kimi K2 / MiniMax Agent（备选）

这些环境不原生支持 Claude Code 的 skill / agent 机制。可以：

1. 把 `skills/*/SKILL.md` 和 `skills/proofread/references/*.md` 作为 knowledge 上传
2. 把 `agents/historical-proofreader.md` 作为 system prompt
3. Python 脚本本地跑（`pip install -r requirements.txt` 装依赖后直接执行）
4. 手动串工作流

详见 [INSTALL.md](INSTALL.md)。

### 依赖

Python 3.9+，以及：

```
opencv-python
pillow
pdf2image
requests
python-dotenv
markdown
beautifulsoup4
PyPDF2
python-docx
opencc-python-reimplemented
```

macOS 还需：`brew install poppler`。

### 环境变量

`~/.env` 里配 MinerU 或百度（二选一）：

```
# MinerU（推荐）
MINERU_API_KEY=sk-xxxxxxxxxxxx
OCR_ENGINE=mineru

# 或百度 OCR
BAIDU_OCR_API_KEY=xxx
BAIDU_OCR_SECRET_KEY=xxx
OCR_ENGINE=baidu
```

**API key 不进项目**，永远放 `~/.env`。

---

## 架构 & 故障排查

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — 八个 skill 的职责边界、数据流、文件布局、设计决策
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — 常见报错和兜底

---

## 隐私 & 安全

**OCR 引擎调用** 会把 PDF 传给：

- **MinerU**：当前实现先上传到 catbox.moe（匿名公共文件托管，24 小时过期）再把 URL 提交给 MinerU。**这意味着 PDF 会在公网短暂可访问**。处理敏感档案、未发表研究、付费文献时请考虑隐私风险。后续版本计划切到 MinerU 官方上传接口消除这一环。
- **百度 OCR**：每页 base64 编码后 HTTPS 发给百度智能云。按百度 ToS 保留用于服务运行，不对外公开。

本地文件：

- `~/.env` 存 API key。**永远不进入仓库**（`.gitignore` 已覆盖）
- `~/.cache/baidu_ocr_token.json` 存百度 access_token（24 小时缓存）
- 所有中间产物在 PDF 同级目录，不污染别处

**插件本身不上传任何数据**。

---

## 贡献 & 反馈

装上跑一次，把卡点发回来。

任何一个 skill 出问题，先查 [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)；还不行开 issue，带上：

- 报错信息（完整 stack trace）
- `meta.json` 或 `raw.md` 头部前 20 行（若是 OCR 后的问题）
- 使用的命令

---

## License

MIT

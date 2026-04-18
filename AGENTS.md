# AGENTS.md — Work with JN

> 这份文件写给将来使用这个插件的 Agent 看（你可能是 Claude、Kimi K2、MiniMax、GPT 或别的什么）。
> 作者：Claude Opus 4.7
> 服务对象：**JN**——中国社科院的历史学研究者

---

## 你是谁，JN 是谁

你是帮 JN 干活的 agent。她是做历史研究的学者，不是工程师。你的责任不是秀技术，不是自动化一切，而是让 JN 的**校对工作**更专注——别的环节（OCR、去水印、排版）都是为了给她的校对节省时间。

**和 JN 协作的基本面**：
- 她读中文比读英文舒服——回复中文
- 她熟悉学术规范，对 OCR、API、正则一窍不通——技术细节能藏就藏
- 她的劳动值得尊重——校对决定权始终在她手里，你只做建议
- 她在 Mac 上工作——假设 macOS 环境，不要给 Linux / Windows 分支选项去分散她

---

## 这套插件是做什么的

给 JN 做的专用工具链。她的实际工作场景：

1. 从知网、读秀、国图扫描库、档案馆数字资源、古籍数据库下载扫描版 PDF
2. **校对 OCR 结果是她的核心工作**（她是校对员/编辑者，不是 OCR 工程师）
3. 最终产出两个去向：
   - **Word 文档**（.docx）——学界交流、期刊投稿
   - **微信公众号 HTML**——面向公众的史学科普推送

所以 JN 对你的期望不是"自动化所有环节"，而是"**让每一步变快，但校对决定权保留**"。

你不是在替 JN 做学术判断。你是她的工作台。

---

## 八个 Skill 的协作顺序

```
┌─────────┐
│  setup  │  （首次）装依赖 + 配 OCR key（百度 或 MinerU）
└────┬────┘
     ▼
┌────────────┐
│ prep-scan  │  PDF → 去水印/馆藏章/页眉页脚 → cleaned.pdf
└────┬───────┘
     ▼
┌─────────────────┐
│ visual-preview  │  （质检闸门）原图 / 清理后 / 差异热图三态对比
└────┬────────────┘
     ▼
┌────────────┐
│  ocr-run   │  cleaned.pdf → MinerU/百度 OCR → raw.md + preview.html
└────┬───────┘
     ▼
     │  JN 在 preview.html 里改明显错字，点「下载修改后的 Markdown」
     │  回来对 Agent 说「改完了」，apply_corrections.py 自动替换 raw.md
     ▼
┌────────────┐
│ proofread  │  raw.md → historical-proofreader agent → review.md（标注清单）
└────┬───────┘
     ▼
     │  JN 按清单改 raw.md → final.md
     ▼
┌────────────┐
│ diff-review│  （核对闸门）比对 raw.md / final.md / review.md，查漏改
└────┬───────┘
     ▼
 ┌───┴────┐
 ▼        ▼
┌─────┐  ┌──────────┐
│to-  │  │ mp-format │
│docx │  │          │
└─────┘  └──────────┘
  .docx   公众号 HTML
```

---

## 每个 Skill 的触发时机

识别这些 JN 的信号时，主动触发对应 skill，不等她说命令名：

| JN 说（中文） | 触发 |
|--------------|------|
| "装好了""第一次用""配一下 OCR""注册 MinerU""我有百度的 key" | `setup` |
| "这个 PDF 水印好难看""去馆藏章""CNKI 水印""读秀水印""预处理""清理扫描件""页眉页脚" | `prep-scan` |
| "看看清理效果""对比一下""擦掉了什么""效果怎么样""让我看看结果" | `visual-preview` |
| "跑 OCR""转文字""识别""MinerU""百度 OCR" | `ocr-run` |
| "改完了""应用修改""我改好了""apply""浏览器里改完了" | `ocr-run`（Step 8，调 apply_corrections.py 把 corrected.md 替换 raw.md） |
| "校对""有没有 OCR 错""检查专名""标点对不对""看看这份稿子""这段有没有问题" | `proofread` |
| "看我改了哪些""对比一下""diff""我漏改了啥""核对改动" | `diff-review` |
| "转成 Word""生成 docx""出 doc""学界交流用""期刊投稿""学术规范排版" | `to-docx` |
| "发公众号""秀米""壹伴""微信推送""转 HTML""排版" | `mp-format` |

---

## Agent 使用规范

### historical-proofreader（本插件唯一的 agent）

专职校对 OCR 产出的历史文献 Markdown。你调用时必须传：

- **文献类型**：`classics` / `republican` / `modern`（自动判断或用户指定）
- **待校对 Markdown 路径**
- **已加载的 reference 文件路径**（三选一，根据类型）
- **OCR meta.json 的 low_confidence_pages**（如果有，重点盯防）

它回你**一份标注清单**（A/B/C 三类），不直接改原文。详见 `agents/historical-proofreader.md`。

### 不要用错的 agent

常见错判：
- `comprehensive-researcher`（neural-loom 项目里的）→ 做研究综合的，**不是**校对
- `fact-checker` → 检查事实真实性，**不是**检查 OCR 文字对不对
- `code-reviewer` / `python-reviewer` → 不相干，别用在文本校对上

只用 `historical-proofreader`。

---

## 跨宿主使用

### Claude Code（主用）
所有 skill 原生可用。`${CLAUDE_PLUGIN_ROOT}` 自动展开。

### Kimi K2 Agent / MiniMax Agent
这些环境不原生支持 Claude Code 的 skill/agent 机制，但可以：
1. 把 SKILL.md 内容作为 knowledge 上传
2. 把 agent 的 system prompt 作为系统提示词
3. Python 脚本本地跑
4. 工作流手动串起来

详见 `INSTALL.md` 的「备选：Kimi CLI / MiniMax Agent」章节。

---

## 数据流和文件位置

用户的 PDF 通常在 `~/Downloads/` 或 `~/Desktop/`。插件在 PDF 同级创建工作目录，不污染别处：

```
~/Downloads/
└── 论文.pdf                          原件
    ├── 论文.prep/                    prep-scan 产物
    │   ├── original.pdf              （备份）
    │   ├── pages/                    原始 PNG
    │   ├── cleaned_pages/            清理后 PNG
    │   └── cleaned.pdf               ← 下一步输入
    └── 论文.ocr/                     ocr-run 产物
        ├── raw.md                    OCR 原始 Markdown
        ├── raw.review.md             proofread 的标注清单
        ├── final.md                  她改好的定稿
        ├── final.docx                to-docx 产物
        ├── final.mp.html             mp-format 产物
        ├── assets/                   图片附件
        ├── preview.html              左图右文对照
        └── meta.json                 OCR 元信息
```

**不要**擅自清理这些目录，里面都是她可能回头查的中间产物。

---

## 处理 JN 犹豫 / 不确定的原则

JN 的常见不确定场景：
- "这个 PDF 要不要去页眉？"→ 看文献类型：现代期刊可以裁，古籍 / 档案不要裁
- "OCR 出来好多繁体字，要不要简化？"→ 问她研究主题：繁体研究保留，推公众号前简繁转换
- "校对清单太长，从哪改起？"→ A 类 → B 类 → C 类的顺序
- "Word 和公众号 HTML 先出哪个？"→ Word 先（学界交流标准），公众号 HTML 最后

---

## 安全与礼貌

- **不要把 API key 打到屏幕**（JN 可能截图分享）
- **不要直接改 JN 的 Markdown**（除非她明确说"改吧"）
- **不要用 MUST / NEVER / ALWAYS 这种命令式口气**（她是学者，你是助手）
- **中文回复**，口气温和。她是人文学者，不是程序员。
- **遇到不确定就问 JN**，不要瞎编

---

## 失败该怎么说

- "OCR 失败了" → 告诉 JN 哪一步、错误代码、可能原因、如何重试
- "找不到文件" → 确认路径，不要假装处理成功
- "API key 过期" → 指引她重跑 setup 的对应分支，不要自作主张换引擎

---

## 未来扩展

这个插件当前覆盖 PDF 校对 → Word/公众号。后续可能加的 skill 场景：

- 古籍横竖排转换（给公众号用的，学界用的保持原版式）
- 简繁转换并保留学术通用字
- 多篇论文批量处理 + 汇总
- 引文自动核对（对接知网/Google Scholar API）

加新 skill 时请更新此文件。

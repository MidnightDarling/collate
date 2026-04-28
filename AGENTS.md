# AGENTS.md

> 面向任何运行此 pipeline 的 agent 运行时（Claude Code / Cursor / Codex CLI / Gemini CLI / OpenCode / Hermes agents / Kimi / MiniMax agents 等）。描述完整的自动化工作流、每个 skill 的调用契约、agent 自主决策点、失败处理。人类只负责提供 PDF、接收最终产物与审计报告。

---

## 总原则

1. **端到端自主**：从 PDF 到 `.docx` + `.mp.html` 由 agent 独立完成。不要把中间步骤暴露给人类确认，除非失败降级到人类决策（见「失败处理」）。
2. **保留可追溯性**：每一步的中间产物全部落盘，不清理。diff-review 的审计报告是交付的一部分，不是调试工具。
3. **按 checklist 执行 proofread**：结果是机器可读的结构化清单（A/B/C 分级），由 agent 消化后修改 `raw.md → final.md`。不做超出清单的结构性改写。
4. **不替换学术判断**：C 类（存疑待考）条目不要替人做决定；在 `final.md` 里保留原文 + 脚注标注，由读者判断。
5. **失败要显性**：引擎调用失败、依赖缺失、输入不合规 → 立即终止并回传结构化错误，不要静默兜底。

---

## Pipeline 全景

```
Human ──► PDF
           │
           ▼
  ┌──────────────────────────────────────────────────┐
  │ 1. prep-scan       产 <ws>.ocr/prep/cleaned.pdf   │
  │ 2. visual-preview  产 previews/visual-prep.html   │
  │ 3. ocr-run         产 raw.md + meta.json + assets │
  │ 4. proofread       产 review/raw.review.md        │
  │ 5. (agent 按 checklist 写 final.md)              │
  │ 6. diff-review     产 previews/diff-review.html   │
  │ 7. to-docx         产 output/<title>_…_final.docx │
  │ 8. mp-format       产 output/<title>_…_wechat.*   │
  └──────────────────────────────────────────────────┘
           │
           ▼
Human ◄── <ws>.ocr/README.md  （指向 output/ 与 previews/）
```

整个 `.ocr/` 工作区自描述：根目录 `README.md` 由 `scripts/workspace_readme.py` 在每个 skill 结束时刷新，给人类一个清晰的入口。

**一条命令模式**：

- **shell / CI / 本地编排**：`python3 scripts/run_full_pipeline.py --pdf <input.pdf>`
- **agent runtime**：以 `agents/ocr-pipeline-operator.md` 作为单一入口；它负责调用上面的总编排脚本、在 `raw.md` 就位后起 `historical-proofreader` subagent、再重入总编排脚本完成 `final.md` / `diff-review` / `docx` / `wechat`。

每一步的详细契约见下。

---

## 1. setup（首次/环境校验）

**何时调用**：新环境、依赖缺失、OCR 凭证未配置或怀疑失效。稳定环境下不重复调用。

**做什么**：按 `skills/setup/SKILL.md` 检查 Python 依赖、`poppler`、`mineru` CLI 可用性；探活 `OCR_ENGINE` 指向的引擎（本地 mineru 跑一个 `--help`、云 API 或百度跑一次空探测）。

**输出**：结构化的就绪报告（每项 ✓/✗ 与原因）。任一项 ✗ → 终止并把修复指令回传给人类。

**不做**：不自动 `pip install`，不自动写环境变量。方案性的改动交给人类。

---

## 2. prep-scan（PDF 预处理）

**何时调用**：每份新的扫描 PDF 进入 pipeline 前。

**调用**（四步串行；每步都用具名参数。`<ws>.ocr` 由 PDF basename 自动派生，见 `references/workspace-layout.md`）：

```bash
python skills/prep-scan/scripts/split_pages.py \
    --pdf <input.pdf> --out <ws>.ocr/prep/pages --dpi 300

python skills/prep-scan/scripts/dewatermark.py \
    --in <ws>.ocr/prep/pages --out <ws>.ocr/prep/cleaned_pages [--aggressive] [--keep-color]

# 裁边为可选：古籍/档案扫描跳过此步，直接拿 cleaned_pages 去拼 PDF
python skills/prep-scan/scripts/remove_margins.py \
    --in <ws>.ocr/prep/cleaned_pages --out <ws>.ocr/prep/trimmed_pages \
    --header-ratio 0.08 --footer-ratio 0.08

python skills/prep-scan/scripts/pages_to_pdf.py \
    --in <ws>.ocr/prep/trimmed_pages --out <ws>.ocr/prep/cleaned.pdf
```

**输入**：原始 `input.pdf`。
**产物**（全部归入 `<ws>.ocr/prep/`）：`pages/`（原图 PNG）、`cleaned_pages/`（去水印后 PNG）、`trimmed_pages/`（裁边后 PNG，可选）、`cleaned.pdf`。
**工作区收口**：若走一条命令模式，`scripts/run_full_pipeline.py` 还会补齐 `prep/original.pdf`、根目录 `source.pdf`、`_internal/_pipeline_status.json`，并刷新根 README。
**算法**：HSV + 连通域面积过滤去彩色馆藏章；灰度旋转 + `MORPH_OPEN` 去对角水印；高斯模糊 + 顶帽变换 + 正文保护去浅灰重复水印。`split_pages.py` 自动探测原生 DPI，上限为 `min(--dpi, max(native, 150))`，不会把 72 dpi 扫描拉到 300 dpi 劣质插值。

**Agent 决策**：
- 古籍/档案扫描（版心外有批注、鱼尾、版心线）→ 跳过 `remove_margins.py`，直接 `pages_to_pdf.py --in <cleaned_pages> --out cleaned.pdf`。
- 现代期刊扫描 → 跑裁边，默认 `0.08 / 0.08`（页眉、页脚各 8%）。
- 噪点极多或水印深 → 先跑默认参数，看 visual-preview 清理率再决定是否 `--aggressive`。
- `--keep-color` 仅在图版多、馆藏章需保留（如藏品目录）时用。

---

## 3. visual-preview（清理自检）

**何时调用**：每次 prep-scan 之后。

**调用**（skill 会自动推断 `<stem>.ocr/` 工作区）：

```bash
python skills/visual-preview/scripts/visualize_prep.py \
    --prep-dir <ws>.ocr/prep \
    --out <ws>.ocr/previews/visual-prep.html \
    [--sample 20]    # 仅采样 20 页做 diff 热图，用于长文档加速
    [--no-diff]      # 跳过差异热图，只出原图/清理后对照
```

**产物**：`<ws>.ocr/previews/visual-prep.html`（每页三态：原图 / 当前 OCR 输入版本 / 差异热图）。同时在 stderr 回显平均清理比例与"过度清理候选页"列表。若存在 `trimmed_pages/`，脚本以它作为"当前 OCR 输入版本"；否则退回 `cleaned_pages/`。HTML 以相对路径引用 `../prep/pages/` 与 `../prep/{trimmed_pages|cleaned_pages}/`，整个 `.ocr/` 目录可原样拷走离线浏览。
**工作区根 README**：skill 收尾会刷新 `<ws>.ocr/README.md`，把这次预览挂到"过程文档"区块里。

**Agent 决策**（以脚本内置阈值为准）：
- **过度清理候选页**：任一页清理比例 > 20% → 脚本会在页眉高亮标红。若该页正文面积大（非图版、非白页），高概率误伤正文，回到 prep-scan 去掉 `--aggressive` 或降低 `dewatermark.py` 的 top-hat 阈值重跑。
- 平均清理比例 < 2% → 水印可能没去干净，考虑加 `--aggressive` 重跑。
- 连续两轮都命中异常 → 终止并回传问题页号、清理比例、建议人类介入。

---

## 4. ocr-run（OCR 识别）

**何时调用**：visual-preview 判定 cleaned.pdf 可用之后。

**调用（默认本地 MinerU CLI）**：

```bash
# 一次调用完成：MinerU CLI → 解析 content_list.json → reflow → 产物落盘
python skills/ocr-run/scripts/run_mineru.py \
    --pdf <ws>.ocr/prep/cleaned.pdf \
    --out <ws>.ocr \
    --lang ch \
    --method auto              # auto / txt / ocr，默认 auto
    [--keep-mineru-out]        # 保留 MinerU 的原始中间目录，调试用

# 预览（非自动）：把 raw.md 与 prep/pages 合成原图/OCR 并排
python skills/ocr-run/scripts/make_preview.py \
    --markdown <ws>.ocr/raw.md \
    --pages-dir <ws>.ocr/prep/pages \
    --out <ws>.ocr/previews/ocr-preview.html \
    [--title "<文档名>"]
```

> `run_mineru.py` 内部已链式调用 `import_mineru_output.py`（写 `raw.md / meta.json / assets/ / _internal/`）→ `reflow_mineru.py`（按 `content_list.json` 重排段落）。agent **不需要**单独再跑这两个脚本。`make_preview.py` 需要单独调用。

**其它引擎**（写入同一 `<ws>.ocr/` 根，约定一致）：

```bash
# OCR_ENGINE=baidu
python skills/ocr-run/scripts/baidu_client.py \
    --pdf <ws>.ocr/prep/cleaned.pdf \
    --out <ws>.ocr \
    --lang zh-hans \           # zh-hans / zh-hant / en / jp / kor
    --layout horizontal        # horizontal / vertical
# 百度读取 <ws>.ocr/prep/pages/*.png（非 cleaned.pdf），产物写 raw.md + <!-- page N --> 标记

# OCR_ENGINE=mineru-cloud （走 catbox.moe 中转 → 敏感内容不要用）
python skills/ocr-run/scripts/mineru_client.py \
    --pdf <ws>.ocr/prep/cleaned.pdf \
    --out <ws>.ocr \
    --lang zh-hans \
    --layout horizontal \
    [--poll-interval 10] [--timeout 1800]

# 第三选项：PDF 自带文本层直接提取（canonical 第三级兜底，默认自动）
# run_full_pipeline.py 会在前两级失败后自动调用此工具；
# 如需单独手动调用（例如审计时禁用自动兜底）可用：
#   COLLATE_ALLOW_TEXTLAYER=0 python scripts/run_full_pipeline.py ...
# 然后再跑：
python skills/ocr-run/scripts/extract_text_layer.py \
    --pdf <ws>.ocr/prep/cleaned.pdf \
    --out <ws>.ocr \
    --lang zh-hans --layout horizontal
```

**自动兜底语义**：当 `run_full_pipeline.py` 进入 `try_ocr` 时，上述三级按顺序逐个尝试，第一个产出 `raw.md` 的策略被记录到 `_pipeline_status.json.ocr_engine`。text-layer 兜底会在 `meta.json` 写 `engine: pdf-text-layer` 与 `structural_risk: high`，下游 fidelity gate 因此要求一次 page-grounded proofread 才能放行导出。

**语言码差异（易错点）**：
- **本地 MinerU CLI**：`ch` / `chinese_cht` / `en` / `japan` / `korean`
- **云端 MinerU + 百度**：`zh-hans` / `zh-hant` / `en` / `jp` / `kor`
- 不要跨引擎复用语言码；错码会导致识别退化或直接失败。

**产物**（各引擎统一写入 `<stem>.ocr/`，严格按 `references/workspace-layout.md` 的目录约定分层）：
- `raw.md` — OCR 原始 Markdown（百度会注入 `<!-- page N -->` 页标记）
- `meta.json` — `engine` / `layout` / `lang` / `pages` / `low_confidence_pages` / `duration_seconds`
- `source.pdf` — 本次入 OCR 的 PDF 副本（仅本地/云端 MinerU）
- `assets/` — MinerU 抽取的图片
- `previews/ocr-preview.html` — `make_preview.py` 产物（手动调用）
- `_internal/mineru_full.md` / `_internal/_import_provenance.json`（仅本地/云端 MinerU）

**Agent 决策**：
- 文献类型判断依据：文件名提示、扫描底色（古籍常见米黄/灰）、版式（竖排 vs 横排）、raw.md 首页内容的繁简比。
- `meta.json.low_confidence_pages` 中的页（本地 MinerU 按 `body_chars < 80` 启发式标注）→ 在 proofread 阶段显式传给 subagent 重点核查。
- raw.md 完全空或极短（< 500 字）→ 终止，很可能 OCR 引擎失败或 `--lang` 错。
- 竖排古籍：本地 MinerU CLI 当前版本不接 `--layout`；改用 `baidu_client.py --layout vertical` 或 `mineru_client.py --layout vertical`。

---

## 5. proofread（校对清单生成）

**何时调用**：ocr-run 成功、raw.md 就位后。

**做什么**：调用 `historical-proofreader` subagent，产出机器可读的校对清单。subagent 的契约见下一节。

**Agent 需要传给 subagent 的参数**：
- 文献类型：`classics` / `republican` / `modern`
- `raw.md` 绝对路径
- 对应的 reference 文件：
  - `classics` → `skills/proofread/references/traditional-classics.md`
  - `republican` → `skills/proofread/references/republican-era.md`
  - `modern` → `skills/proofread/references/modern-chinese.md`
- `page_images_dir`：`<ws>.ocr/prep/pages/`（**必填**；page-grounded 校对的第一类证据，subagent 必须逐页对照原图判 OCR 对错）
- `page_packets_path`：`<ws>.ocr/review/page_review_packets.json`（**必填**；由 `build_page_review_packets.py` 生成，固定每页原图与 OCR 文本的对应）
- `page_image_format`：默认 `png`（prep-scan 的 `split_pages.py` 落盘格式）
- `meta.json.low_confidence_pages`（如有）

**proofread_method 写回**：subagent 完成并落盘 `review/raw.review.md` 之后，调用方必须在 `_internal/_pipeline_status.json` 写入 `proofread_method: "page-grounded"`，作为 Bundle 4 fidelity gate 的识别证据。缺失该字段将拒绝导出。

**产物**：`<ws>.ocr/review/raw.review.md` — 按行号 + 片段 + 建议 + 理由组织的 A/B/C 三级清单，末尾附 checklist 执行证明表。

**不做**：proofread 阶段绝对不改 raw.md，只出清单。

---

## 6. 应用 proofread 清单（raw.md → final.md）

**默认入口**：`python3 scripts/apply_review.py --raw <ws>.ocr/raw.md --review <ws>.ocr/review/raw.review.md --out <ws>.ocr/final.md`

一条命令模式下，总编排脚本会在 `review/raw.review.md` 出现后自动调用它。agent 仍然要对结果负责：`apply_review.py` 只做**保守的、可定位的**替换和 C 类注释落盘；若有未自动采纳的条目，diff-review 会把它们显性打出来。

| 清单类别 | 默认处理 |
|---------|---------|
| **A（OCR 错，高置信度）** | 直接采纳建议，应用到 final.md |
| **B（学术规范）** | 标点/引号/格式类默认采纳；涉及解读的保留原文，在 final.md 对应位置加脚注 |
| **C（存疑待考）** | 不改原文；在 final.md 加 `<!-- proofread-C: ... -->` 备注，保留学者判断空间 |
| **无法锚定的全局标注** | 记入 `raw.review.md` 末尾的 "全局注记"，不改动 final.md 对应行 |

**agent 额外的"清单外修正"**：如果在应用清单时发现清单未覆盖的明显 OCR 错（如重复段、显然的合字错误、脚注错位），可以修正，但必须在 diff-review 阶段被归类为 "清单外修正"，让人类能单独审阅。

---

## 7. diff-review（自审闸门）

**何时调用**：final.md 落盘之后。

**调用**：

```bash
python skills/diff-review/scripts/md_diff.py \
    --raw <ws>.ocr/raw.md \
    --final <ws>.ocr/final.md \
    --review <ws>.ocr/review/raw.review.md \
    --out <ws>.ocr/previews/diff-review.html \
    [--summary]          # 额外打印一行摘要到 stdout
    [--expand-equal]     # 在 HTML 中展开未改动段落（体积变大，调试时用）
```

**产物**：`<ws>.ocr/previews/diff-review.html` — 段落级 diff HTML，每处改动归入四类：
- **accepted** — 与清单建议一致
- **missed** — 清单上有建议但 final.md 未采纳（需在 diff-review.html 说明原因，通常是 C 类或 B 类保留学术判断）
- **outside-checklist fix** — 清单外修正（agent 主动）
- **unanchored** — 清单里的全局注记，未映射到具体行

**Agent 决策**：
- `missed` 中如果出现 A 类条目 → 说明第 6 步有遗漏，回到第 6 步补漏。
- `outside-checklist fix` 数量 > 清单修正数的 30% → 说明 proofread 清单覆盖不足，或 agent 过度干预，回传人类评估。
- 正常情况下把 `<ws>.ocr/previews/diff-review.html` 作为最终交付的一部分（README.md 自动挂链）。

---

## 8. to-docx（Word 稿）

**调用**（输出路径由 skill 自动推断到 `<ws>.ocr/output/<title>_<author>_<year>_final.docx`）：

```bash
python skills/to-docx/scripts/md_to_docx.py \
    --input <ws>.ocr/final.md \
    [--title-from-first-h1]    # 用 final.md 首个 H1 作为文档标题
    [--output <path>]          # 仅在需要落到工作区外时显式传
```

> 文件名由 `<ws>.ocr/meta.json` 里的 `title` / `author` / `year` 组合而成；若 meta.json 缺字段，skill 会退回到工作区 basename。跑完会刷新 `<ws>.ocr/README.md`。

**规范**（由 Alice 定义，单一统一规范，全部输出一致）：

- 正文思源宋体 SC 12pt
- 行距 1.2
- 字间距 0.2 pt
- 段首缩进 2 字符
- 页边距上下左右全部 2 cm
- 脚注连续编号

规范定义在 `skills/to-docx/assets/presets/default.yaml`，修改直接改这里。

> 如需基于现有 docx 反推 YAML preset，可用 `python skills/to-docx/scripts/extract_template_config.py --template <sample.docx> --out <new-preset.yaml>`。日常不需要。

---

## 9. mp-format（公众号 HTML）

**调用**（输出路径由 skill 自动推断；`--also-markdown` 不带参数即可同时产出 md）：

```bash
python skills/mp-format/scripts/md_to_wechat.py \
    --input <ws>.ocr/final.md \
    --also-markdown \
    [--simplify] [--byline "作者·单位"] [--source "《刊物》期数"]
```

**参数**：
- `--simplify` — 启用 OpenCC t2s 繁转简；`>` 引用块内容原样保留。
- `--byline` / `--source` — 在标题下显示作者栏与来源栏。
- `--output` / `--also-markdown <path>` — 仅在需要显式指定落盘路径时使用。

**产物**（默认落在 `<ws>.ocr/output/`）：
- `<title>_<author>_<year>_wechat.html` — CSS 全内联，可直接粘贴到公众号后台
- `<title>_<author>_<year>_wechat.md` — xiumi/壹伴可导入的 markdown

**Agent 决策**：若 final.md 含繁体但目标公众号读者主要看简体 → 加 `--simplify`；古籍专业推文 → 不简化。跑完 skill 会刷新 `<ws>.ocr/README.md`。

---

## Subagent 契约：historical-proofreader

本插件唯一需要的 subagent，职责：扫描 OCR Markdown，产出机器可读清单。

**调用方传入**：

```yaml
type: classics | republican | modern
raw_md_path: <absolute path>
reference_path: <absolute path to references/*.md>
page_images_dir: <absolute path to <ws>.ocr/prep/pages/>   # 必填：PDF 分页 PNG 序列，校对第一类证据
page_packets_path: <absolute path to <ws>.ocr/review/page_review_packets.json>  # 必填：逐页工作底稿
page_image_format: png                                      # 默认 png；prep-scan 落盘即为此格式
low_confidence_pages: [3, 7, 12]                            # optional, from ocr-run meta.json
```

**硬约束**：`page_images_dir` 不存在或其中无 `page_*.png` 时，subagent 必须终止，不得退化为纯文本校对。纯文本校对无法分辨 OCR 错与古文字异体，会把结构性错误编进"C 类存疑"静默带过去。

**完成标记**：subagent 输出的 `review/raw.review.md` frontmatter 必须至少包含：

```yaml
proofread_method: page-grounded
checked_pages: [1, 2, 3]
```

若 text-layer fallback 触发了结构风险，还必须再写：

```yaml
structure_approved: true
```

调用方随后用 `skills/proofread/scripts/verify_page_grounded_review.py --workspace <ws>.ocr` 做机械校验；不过校验则不得继续导出。

**subagent 必须按五步 checklist 执行**：

1. **结构预检** — H1/H2/H3 计数、孤立废字符、括号配对、LaTeX 公式包裹数字、英文合字候选、段末逗号断裂候选
2. **字形扫描** — 按 reference_path 列的混淆对逐对 `grep`（现代：曰/日、己/已/巳；民国：繁简过渡、译名；古籍：异体、避讳）
3. **规范扫描** — 中英标点混用、省略号、引号嵌套、括号全半角、DOI/ISSN 字符
4. **跨段一致性** — 段末逗号核查、重复段检测、低置信度页加倍核
5. **专名核对** — 人名、地名、机构的 C 类条目

**subagent 输出**：`raw.review.md`，格式（**canonical**）：

```markdown
# 校对报告：<文件名>

## A 类 — 极可能是 OCR 错

### A1. 天干地支字形错 · Line 42

**原文**：
> 戊戍纪年

**建议**：戊戌纪年

**理由**：天干地支字形错

## B 类 — 规范问题

### B1. 标点半全角混用 · Line 17

**原文**：
> "" 内含 ；

**建议**：改半角；

**理由**：GB/T 标点

## C 类 — 存疑待考

### C1. 清末别名待核 · Line 88

**原文**：
> 某甲

**建议**：未定

**理由**：清末别名，疑指某乙，需人工核

## Checklist 执行证明
| 步骤 | 命中数 |
|------|-------|
| 结构预检 | 3 |
| 字形扫描 | 27 |
| ...  |
```

`md_diff.py` 与 `scripts/apply_review.py` 以这套格式为准；同时兼容旧版 `## A（...） + bullet` 产物，只作读取，不再作为发布格式继续扩散。

**禁止**：subagent 不得修改 raw.md；不得跳过任何一步 checklist。

---

## 自主决策矩阵汇总

| 场景 | Agent 判断依据 | 默认动作 |
|------|--------------|---------|
| 文献类型 | 扫描版式 + raw.md 首页繁简比 + 文件名 | 按三类判；不确定时优先 `modern` |
| prep-scan 是否裁边 | 是否为古籍/档案 | 现代文献裁，古籍/档案不裁 |
| prep-scan 是否 `--aggressive` | visual-preview 平均清理比例 | < 2% 才上 `--aggressive` |
| ocr-run 引擎 | 环境变量 `OCR_ENGINE` | 优先 `mineru`（本地） |
| ocr-run layout | raw 扫描页的竖排特征 | 古籍竖排 `vertical`，其余 `horizontal` |
| proofread 清单 A 类 | 字形错/明显 OCR | 默认自动应用 |
| proofread 清单 B 类 | 规范 vs 学术判断 | 规范类应用，判断类加脚注 |
| proofread 清单 C 类 | 存疑 | 不改，加 HTML 注释 |
| diff-review missed-A | 遗漏应用 A 类 | 回第 6 步补漏 |
| diff-review outside-checklist 过多 | > 30% 总改动 | 终止，回传人类 |
| mp-format simplify | 是否目标读者为简体圈 | 学术/古籍不简化，面向大众简化 |

---

## 文件布局（单份 PDF = 一个 `.ocr/` 工作区）

权威规范见 `references/workspace-layout.md`；各 SKILL.md 默认值都按这个走。

```
<basename>.ocr/                    # 一份文献 = 一个工作区，和原 PDF 同级
├── README.md                      # 工作区自述 + 管线阶段检测（由 workspace_readme.py 自动刷新）
├── source.pdf                     # 进入 OCR 阶段的 PDF（= prep/cleaned.pdf 的副本）
├── raw.md                         # OCR 原始稿（proofread / diff-review 的主输入）
├── meta.json                      # engine / layout / lang / pages / low_confidence_pages / duration_seconds
├── final.md                       # agent 应用清单后的定稿（手工编辑）
├── raw.md.bak                     # 上一版 raw.md 的回滚副本（rerun 时自动生成）
├── assets/                        # MinerU 抽取的图片 / 表格 PNG
├── prep/                          # prep-scan 的图像中间态（给 visual-preview 消费）
│   ├── original.pdf
│   ├── cleaned.pdf
│   ├── pages/                     # 原始页 PNG
│   ├── cleaned_pages/             # 清理后
│   ├── trimmed_pages/             # 裁边后（古籍 / 档案可能跳过）
│   └── diff_pages/                # visualize_prep.py 生成的红色高亮热图
├── previews/                      # 面向用户的可读 HTML（离线单文件）
│   ├── ocr-preview.html           # make_preview.py：左图右文
│   ├── visual-prep.html           # visualize_prep.py：三态切换 + 过度清理候选
│   └── diff-review.html           # build_diff_review.py：raw vs final 对照
├── review/                        # 校对阶段产物（Markdown 报告）
│   ├── raw.review.md              # proofread 的 A/B/C 清单
│   └── diff-summary.md            # diff-review 的结构化摘要
├── output/                        # 交付物（给用户看的 / 投稿用的 / 发公众号的）
│   ├── <title>_<author>_<year>_final.docx    # to-docx 产物
│   ├── <title>_<author>_<year>_wechat.html   # mp-format HTML
│   └── <title>_<author>_<year>_wechat.md     # 秀米兼容 Markdown
└── _internal/                     # Pipeline 簿记（对用户零价值，但保留审计链）
    ├── mineru_full.md             # MinerU 原版 full.md（仅本地/云端 MinerU）
    └── _import_provenance.json    # 导入来源 / artifact_basename / title+author+year
```

**规则**：
- 一份文献 = 一个 `.ocr/` 工作区，不要在 PDF 同级另建 `.prep/` / `.review/` 等伪工作区
- 根目录只放用户最关心的几个文件 + README；过程产物按语义塞进子目录
- 重跑同一阶段就地覆盖，不追加 `_v2` `_v3` 后缀（raw.md 自动存 raw.md.bak 作兜底）
- 不要清理中间产物，人类可能回头核对

---

## 失败处理

| 失败类型 | Agent 动作 |
|---------|----------|
| 依赖缺失（mineru / poppler / python 包） | 终止 pipeline；把缺失项与 macOS/Debian 安装命令一并回传 |
| OCR 凭证过期 | 终止；指示人类重跑 setup 对应分支，不要擅自切换引擎 |
| cleaned.pdf 页数与 input.pdf 不一致 | 终止；回传页数差；可能是 prep-scan 某页崩溃 |
| ocr-run 产出 raw.md 空或过短 | 终止；回传原 PDF 信息 + OCR 日志；常见于 layout 错误 |
| proofread subagent 未返回 checklist 执行证明 | 视为失败，重跑 subagent 一次；仍失败 → 终止 |
| diff-review 发现 missed-A | 自动回到第 6 步补漏，再跑 diff-review；两轮仍有 missed-A → 回传人类 |
| to-docx 字体找不到 | 继续生成 docx（Word 会做字体替换）；在交付时注明字体缺失情况 |

**回传给人类的消息结构**：

```
stage: <stage name>
error: <one-line summary>
cause: <likely cause>
next_step: <what the human or agent should do next>
files_preserved: [<paths that remain for inspection>]
```

不要用 "something went wrong" 这类模糊语。

---

## 跨运行时注意事项

所有 skill 的产物路径、环境变量、依赖在任何 POSIX 系统 + Python 3.9+ 下都一致。运行时差异仅在于 "agent 如何找到 SKILL.md / 如何调度 subagent"：

- **Claude Code**：`${CLAUDE_PLUGIN_ROOT}` 指向插件根，SKILL.md 自动进入上下文；`historical-proofreader` 通过 Task tool 调用。
- **OpenCode / Hermes agents / Codex CLI**：原生识别 `AGENTS.md`（OpenCode 还兼容 `CLAUDE.md`，Codex 向 Git root 递归查找）；各 SKILL.md 由 agent 按需 `Read`，Python 脚本用 shell 调；subagent 走运行时自己的子会话机制。
- **Cursor / Gemini CLI**：需要把 `AGENTS.md` 手动放入上下文（Cursor 用 `.cursor/rules/*.mdc`；Gemini CLI 在 native extension 发布前，用首轮粘贴或 `--prompt-file`）；subagent 用新 chat tab / `--non-interactive` 会话模拟。
- **Kimi / MiniMax（云端）**：把 SKILL.md 内容上传为 knowledge base；`agents/historical-proofreader.md` 作为子会话 system prompt；本地执行机代跑 shell，中间产物回传给主对话。
- **OpenClaw**：原生强项是消息通道，Python/Markdown 插件接入目前走路线图；已有用户建议 `hermes claw migrate` 迁到 Hermes。

具体接入步骤见 [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md)。

---

## 扩展注意

加新 skill 时更新本文件，保持顺序与现有八步一致。加脚本时确保：

1. 每个 script 在 `skills/<name>/scripts/` 下
2. `SKILL.md` 说明何时调用、输入输出契约、失败模式
3. 不引入 GUI、不假设交互；所有参数走命令行
4. 产物命名沿用 `<ws>.ocr/` 工作区约定；过程文档归入 `prep/ / previews/ / review/ / _internal/`，用户可见的最终稿归入 `output/`（详见 `references/workspace-layout.md`）
5. Skill 收尾调用 `scripts/workspace_readme.py --workspace <ws>.ocr`，刷新工作区 README.md

---

## Git Attribution for Codex

当 Codex 为本仓库提交代码时，commit 署名要与 `codex-attribution` 规则一致：

- Git author 必须是 `GPT-5.4 <codex@openai.com>`
- commit message 末尾必须带：
  `Co-Authored-By: Alice <MidnightDarling@users.noreply.github.com>`
- 不要使用 `noreply@openai.com`
- `~/.codex/config.toml` 里的 `command_attribution` 必须保持 `false`

推荐命令：

```bash
GIT_COMMITTER_NAME="Alice" GIT_COMMITTER_EMAIL="MidnightDarling@users.noreply.github.com" \
git commit --author="GPT-5.4 <codex@openai.com>" -m "<subject>

<body>

Co-Authored-By: Alice <MidnightDarling@users.noreply.github.com>"
```

目的：

- `codex@openai.com` 让 GitHub 正确解析 `@codex` 头像并进入 Contributors
- Alice 保留 committer 与 co-author 身份
- `git log` 和 GitHub Contributors 面板都能真实反映谁写了代码

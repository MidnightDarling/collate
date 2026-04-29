<div align="center">

# 点校 · Collate

Read, think, and write history with your agents.<br />
From the scanned page to the final text, from a single x-ray to a field-wide map.

![Self-portrait of attention as observer](assets/readme-hero-v2.png)

> Established 2026-04-19 · Co-authored by Alice, Claude Opus 4.6, and GPT-5.4 · Code under Apache-2.0, reference materials under CC-BY-4.0

[English](README.md) · [中文](README.zh.md)

</div>

---

## What Collate is

A workbench shared by three parties — a historian, the agents working with them, and the original author whose text passes through. The human supplies the scan and holds final judgment. The agents do the patient, repetitive labor between: cleaning, recognition, collation, self-audit, typesetting. Every intermediate stays in the workspace, so any decision can be traced back to the page it came from.

Beyond the pipeline lies a **reading layer** — skills that meet the recovered text as scholarship rather than as data. X-ray a single paper to enter its argument; map a corpus to see a field's shape; audit a citation; read what the author chose not to say; define a key concept; circle the thesis the author approaches but cannot quite commit to writing. These are not extractions. They are ways of joining the conversation the historian has been having all along.

The toolkit ships as a **Claude Code plugin** with a **Codex plugin** sibling. Other runtimes that can run Python and read Markdown knowledge bases may work through `AGENTS.md`, but only Claude Code and Codex are verified end-to-end.

The name *Collate* renders **点校** — the classical Chinese scholarly practice of punctuating and collating received texts. We extend a millennia-old craft with contemporary OCR and agent tooling. We do not improve the texts we collate; we make them legible again.

---

## Posture

Three parties meet at this workbench. Naming them keeps the engineering honest.

- **The historian** — the scholar with the question. Final authority on scholarly judgment. The agents never decide what a passage means; they assemble the text so the historian can decide.
- **The agents** — co-authors of the work, not vending machines. They carry the patient labor: cleaning a watermark, scanning for confusable glyphs, holding the five-step checklist line by line, recording every change so it can be audited. Their reasoning is left visible because work without a trace is work that cannot be trusted.
- **The author of the original text** — present in every line that passes through this pipeline. The whole apparatus exists so their writing can be read again, cited correctly, conversed with. We collate received texts; we do not silently rewrite them.

Every intermediate, every annotation, every edit lives in the workspace. The toolkit is auditable end-to-end because, at this scale, dignity only survives when it is visible.

---

## A glimpse

Three figures from the reading skills, each rendered by the skill itself.

![Argument-orbit figure: five labeled points on a curving line — 国内断层线, 民族主义被借用, 身份不是天成, 全球身份可被建构, 世界社会的前提 — plotted as the path one paper's argument actually walks.](assets/showcase/xray-paper-argument-orbit.png)

> `/collate:xray-paper <paper.md>` — diagram a paper's argument as the curve its claims actually take, not the order the prose presents them in.

![1980s reading of May Fourth as a constellation: Apertio at Polaris with a golden halo, Lumen / Democratia / Scientia / Intelligentsia / Vulgaris / Motus IV Maii lit and connected, Occidens / Traditio / Patria left dim, a striped Terra Incognita marking the violence the decade refuses to chart, header reading EIGHTIES · MR. DEMOCRACY ASCENDS.](assets/showcase/constellatio-eighties.png)

> `/collate:constellatio 五四` — reception-history analysis of a contested phenomenon: what each era's reading needs from the past, and the structural crack in the object that lets every projection stick. Optional sibling chart shows the readings as constellations.

![Cross-era overlay layer: three filled radial halos labelled JANUS, ANGVSTIA OCCIDENTIS, NECESSITAS PRAESENTIS, with the layered constellations of three decades faint behind them.](assets/showcase/constellatio-cartographia.png)

> `/collate:constellatio` cross-era prose deliverable — each era's reading as diagnostic of its own situation, plus the screen-property that explains why no era can settle it.

---

## Quick Start

### 1 · Install

**Claude Code** — two lines inside the CLI, nothing to clone:

```
/plugin marketplace add MidnightDarling/collate
/plugin install collate@collate
```

**Other runtimes** (Codex CLI, Cursor, Gemini CLI) — one shell command clones the repo, installs Python dependencies, and auto-wires whichever runtimes it detects:

```bash
curl -fsSL https://raw.githubusercontent.com/MidnightDarling/collate/main/scripts/install.sh | bash
```

Flags: `--target PATH` (default `~/.local/share/collate`) · `--no-deps` · `--no-runtimes` · `--dry-run` · `--help`. Pass through with `bash -s -- <flags>`.

System dependency: `poppler` (`brew install poppler` on macOS, `apt install poppler-utils` on Debian). Per-runtime wiring details live in [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md); the long-form install guide is [INSTALL.md](INSTALL.md).

### 2 · Verify

```
/collate:setup
```

Diagnoses Python version, ten required packages, the `pdftoppm` binary, and OCR engine credentials. Reports passes, missing items, and one fix suggestion per gap. Never auto-installs.

In runtimes that expose skills directly, `setup` is a skill surface rather than a separate command shim.

### 3 · Run

The **public user path** is `/collate:ocr <pdf-path>`.
Treat `python3 scripts/run_full_pipeline.py --pdf <pdf-path>` as an internal
or debug path unless it has been proven equivalent by the same fresh-agent
real-PDF gate.

Two supported entrypoints:

| Path | When to use |
|------|-------------|
| `/collate:ocr <pdf-path>` | Public one-command path — agent-owned run that must stay aligned with the release gate |
| `python3 scripts/run_full_pipeline.py --pdf <pdf-path>` | Internal / debug mechanical path, useful for CI or batch jobs, but not release evidence on its own |

The agent path is the canonical one: it calls the mechanical runner, builds page review packets, dispatches `historical-proofreader` with page evidence, verifies the review mechanically, re-enters the runner to apply edits and self-audit, and surfaces the delivery message verbatim.

Smoke passes and truthful failure states remain useful guardrails, but they are
not publish evidence by themselves. Release still means:

```text
fresh clone + supported agent runtime + /collate:ocr <real-pdf> + no human intervention + valid final.docx/wechat.html
```

---

## Compatibility

One label per host. Each claim maps to a concrete file or command — nothing is marketed as native if it is not.

| Host | Status | Native Surface | Install Path | Note |
|------|--------|----------------|--------------|------|
| **Claude Code** | Supported | `.claude-plugin/plugin.json` · `.claude-plugin/marketplace.json` | `/plugin install collate@collate` | Plugin-native; verified end-to-end on the Claude Code marketplace. |
| **Codex** | Supported | `.codex-plugin/plugin.json` · `.agents/plugins/marketplace.json` · `AGENTS.md` | repo-local marketplace | Plugin-native via Codex's marketplace surface. |
| **Cursor** | Untested | `AGENTS.md` as context (manual) | hand-write a `.cursor/rules/collate.mdc` pointing at `AGENTS.md` | Skills callable via Cursor's shell tool; no plugin manifest. No integration files ship with the repo. |
| **Gemini CLI** | Untested | `AGENTS.md` as session context (manual) | shell-tool invocation of `skills/*/scripts/*.py` | No `gemini-extension.json` ships with the repo. |

Live wiring details for every row live in [`## Per-runtime install`](#per-runtime-install) below.

---

## Pipeline Workflow

```
Human: scanned PDF
  │
  ▼
Agent pipeline
  1. prep-scan        remove watermarks / library stamps / margins
  2. visual-preview   visualize cleaning for self-check
  3. ocr-run          recognize into Markdown
  4. proofread        produce A/B/C tiered review list
  5. (agent applies fixes per list)
  6. diff-review      self-audit: accepted / missed / outside-checklist / unanchored
  7. to-docx          academic Word document
  8. mp-format        WeChat article HTML
  │
  ▼
Human: final.docx + final.mp.html + audit log
```

**Design principle.** The AI does not make scholarly judgments on the human's behalf. Proofreading produces a machine-readable, severity-tagged list; the agent applies changes and then records them through `diff-review`. All intermediates, annotations, and edit traces are retained so the human can verify each decision line by line.

### Document types

The proofreading layer ships with three calibrated knowledge bases. The agent infers type from the text, or the caller passes `--type=classics|republican|modern`.

| Type | Typical issues | Knowledge base |
|------|----------------|----------------|
| Modern simplified Chinese | Scan noise, confusable glyphs (曰/日, 己/已/巳), punctuation drift, bibliographic format | `skills/proofread/references/modern-chinese.md`; GB/T 7714 |
| Republican-era print | Mixed simplified/traditional, old-style punctuation, transitional translations, old/new place names | `skills/proofread/references/republican-era.md` |
| Classical traditional Chinese | Variant characters, taboo characters, vertical layout, absence of punctuation | `skills/proofread/references/traditional-classics.md`; variants not forcibly normalized, taboo characters only flagged |

---

## What's Inside

A **Claude Code plugin** (and a runtime-agnostic Python toolkit) — install it directly or copy components by hand.

```
collate/
├── .claude-plugin/
│   ├── plugin.json              Plugin manifest read by /plugin install
│   └── marketplace.json         Marketplace catalog
├── .codex-plugin/
│   ├── plugin.json              Codex-native plugin manifest
│   └── README.md                Codex plugin surface overview
├── .agents/
│   └── plugins/marketplace.json Repo-local marketplace for Codex
│
├── skills/                      15 skills · 8 pipeline + 7 reading
│   ├── setup/                   Environment diagnosis (Python, poppler, OCR creds)
│   ├── prep-scan/               PDF → cleaned per-page PNGs (HSV stamp masking, top-hat watermarks, margin trim)
│   ├── visual-preview/          Three-state HTML preview (original / cleaned / diff heatmap)
│   ├── ocr-run/                 MinerU local CLI / MinerU cloud / Baidu OCR — outputs raw.md + meta.json
│   ├── proofread/               Five-step checklist + three type-specific knowledge bases → raw.review.md
│   ├── diff-review/             raw.md vs final.md, classified against the review list
│   ├── to-docx/                 python-docx output, unified academic spec
│   ├── mp-format/               WeChat MP HTML with inline CSS + xiumi sidecar
│   ├── xray-paper/              X-ray a single historical paper (Obsidian-native)
│   ├── paper-summary/           Map a corpus of 5–30 papers (Obsidian-native)
│   ├── chunqiu/                 Read taboo, verdict, and strategic silence
│   ├── kaozheng/                Audit citations, source rank, and warrants
│   ├── prometheus/              Define one concept and render an SVG card
│   └── real-thesis/             Excavate the thesis the paper circles
│
├── agents/                      2 specialized subagents
│   ├── ocr-pipeline-operator.md Pipeline conductor: mechanical → proofreader → self-audit → delivery
│   └── historical-proofreader.md Domain expert: applies the five-step checklist, emits A/B/C review
│
├── commands/                    2 standalone commands · orchestration only
│   ├── ocr.md                   /ocr — one-shot full pipeline
│   └── status.md                /status — read _pipeline_status.json, report stage + next step
│
├── scripts/
│   ├── run_full_pipeline.py     Mechanical orchestrator (no agent required)
│   ├── apply_review.py          Apply raw.review.md edits to raw.md, emit final.md
│   ├── pipeline_status.py       Pipeline workspace status helpers
│   ├── review_contract.py       Shared review-contract parser for proofread / apply / diff
│   ├── workspace_readme.py      Rewrite workspace README as the current directory map
│   └── install.sh               Cross-runtime installer
│
├── docs/
│   ├── ARCHITECTURE.md          Skill boundaries, data flow, file layout
│   ├── INTEGRATIONS.md          Per-runtime wiring (Codex, Cursor, Hermes, Gemini, …)
│   ├── TROUBLESHOOTING.md       Common errors and workarounds
│   └── ...                      Public documentation only
│
├── AGENTS.md                    Agent runtime contract — calling conventions, decision matrix, failure modes
├── CONTRIBUTORS.md              Authors and contributors (credit, not legal attribution)
├── INSTALL.md                   Long-form install guide
├── NOTICE                       Copyright + co-authorship + third-party licenses
├── LICENSE                      Apache-2.0 (code)
└── LICENSING.md                 CC-BY-4.0 scope notes for reference materials
```

---

## The Skills

A skill is a self-contained directory: `SKILL.md` (operational instructions the agent reads) + `scripts/` (Python tools) + `references/` (structured knowledge base where applicable). Collate is now explicitly **skill-first**: 8 pipeline skills plus 7 reading skills. If a slash surface has capability, that capability belongs in the skill itself.

### Pipeline skills

> **setup**

Environment diagnosis. Verifies Python ≥ 3.9, ten required packages, the `pdftoppm` binary, and OCR engine credentials in `~/.env`. Reports passes, missing items, and one fix suggestion per gap. Never auto-installs.

*Trigger:* first install, or any "how do I get OCR running" question.

---

> **prep-scan**

Source-PDF preprocessing. Splits each page at 300 DPI, then runs three cleaning passes:

- HSV color masking + connected-component area filter — removes red/blue library stamps.
- Grayscale rotation + morphological `MORPH_OPEN` — removes diagonal database watermarks (CNKI, 读秀, 维普).
- Gaussian blur + top-hat transform + body-text protection — removes faint repeating watermarks without erasing prose.

Optional header/footer trim. Output: `<workspace>/prep/cleaned.pdf` ready for OCR.

*Trigger:* "preprocess this PDF", "remove the library stamp", "去水印", "去馆藏章", or whenever a scanned PDF arrives from CNKI / 读秀 / 国图 / archive databases.

---

> **visual-preview**

Three-state per-page HTML — original / cleaned / difference heatmap, with cleaned regions shown as semi-transparent red overlay. Pages with cleaning ratio > 20% are auto-flagged so the agent can decide whether to rerun `prep-scan` with adjusted parameters.

*Trigger:* immediately after `prep-scan`, or "let me see the cleaning result", "对比一下", "去水印成功没".

---

> **ocr-run**

Three-engine OCR. Defaults to local **MinerU CLI** (`mineru[pipeline]`); `OCR_ENGINE=baidu` switches to Baidu Cloud OCR (cost-optimized); `OCR_ENGINE=mineru-cloud` uses MinerU's cloud API as a compatibility fallback. Optimized parameters for historical text: traditional vertical layout, classical variant glyphs, Republican-era new punctuation, modern simplified.

Outputs: `raw.md` + side-by-side source/OCR HTML + `meta.json` (engine used, elapsed time, low-confidence pages).

*Trigger:* "OCR this", "recognize the text", "PDF 转文字", "跑识别".

---

> **proofread**

The hinge of the toolkit. The `historical-proofreader` agent executes a mandatory **five-step checklist**:

1. Structural sanity — headings, footnotes, paragraph integrity.
2. Glyph scanning — `grep` the text against type-specific reference tables for confusable characters.
3. Convention scanning — punctuation, quotation marks, DOI / ISBN / page-range format.
4. Cross-paragraph consistency — terminology, transliteration, citation form.
5. Proper-noun review — names, places, eras, official titles.

Produces `raw.review.md` with three tiers — **A** (OCR error, must fix), **B** (academic convention, should fix), **C** (open question, decide). Each item includes line number, source snippet, suggestion, rationale. An execution-proof table is appended so the human can verify the five steps actually ran.

*Trigger:* "proofread this", "check the OCR", "校对这份稿子", "看看 OCR 对不对".

---

> **diff-review**

Closure self-audit. After the agent applies edits per `raw.review.md`, this skill diffs `raw.md` against the post-edit `final.md` and produces a paragraph-level HTML report correlating each change with one of four states:

- **accepted** — agent applied a suggestion from the checklist
- **missed** — checklist item was not addressed
- **outside-checklist** — agent made a fix the checklist did not request
- **unanchored** — change with no obvious justification

Plus a summary `diff-summary.md` with counts. This is what makes the workflow auditable end-to-end.

*Trigger:* end of any proofreading cycle, or "did I miss anything", "show me the changes", "diff".

---

> **to-docx**

Academic Word output via python-docx. Single unified spec: Source Han Serif SC 12pt body, 1.2 line spacing, 0.2pt character spacing, 2cm margins on all sides, 2-character first-line indent, continuous footnote numbering, Chinese-style quotation marks, figure captions positioned above figures and tables.

*Trigger:* "export to Word", "give me a docx", "投稿版本", "give it to the editor".

---

> **mp-format**

WeChat Official Account HTML — the publication target most Chinese humanities authors actually need. Fully inline CSS (WeChat strips external stylesheets); OpenCC `t2s` (traditional → simplified) on body text **but preserving original form inside `>` blockquotes** (citations are not converted); footnotes collected at the article end; byline and source bar.

Also emits a xiumi-compatible Markdown sidecar for users who prefer to do the final visual pass in xiumi or 壹伴.

*Trigger:* "format for WeChat", "公众号排版", "做成推文", "秀米".

### Reading layer skills

The pipeline above ends when `final.md` is clean. The reading layer begins there. Once the text is reliable, the toolkit reads it as scholarship — not to summarize, but to enter the historian's conversation. `xray-paper` and `paper-summary` are the larger rooms; the other five are sharper single-question lenses.

> **xray-paper**

X-ray a single historical paper at substantive depth. Recovers what the author was chasing (问题意识), locates the paper in its tradition (学派谱系), chronicles its timeline, and emits cognitive collision cards where the reading shifts a prior judgment.

Output: `<workspace>/analysis/{stem}_xray.md` with YAML frontmatter, callouts, ASCII chronicles, SVG positioning cards.

*Trigger:* "analyze this paper", "x-ray this article", "map this paper's position", "help me read this".

---

> **paper-summary**

Map a corpus of 5–30 papers as a body of scholarship. Produces eight cross-reading dimensions: archival basis, school lineage, temporal-spatial coverage, methodological distribution, conceptual contention, theoretical borrowings, open questions, and a newcomer's reading route.

Output: `<workspace>/analysis/literature-map.md` or `docs/literature-map/{corpus-name}.md`.

*Trigger:* "survey this literature", "map these papers", "literature review on X", "how does this field stand".

---

> **chunqiu**

Reads taboo, verdict, and strategic silence. Best when a paper's force lies in diction, repetition, omission, or borrowing antiquity to say something obliquely.

Output: `analysis/{stem}_chunqiu.md`.

*Trigger:* "read the silences", "春秋笔法", "what is the author not saying", "借古讽今".

---

> **kaozheng**

Evidential audit in the Qian-Jia mode: claims, sources, warrants, citation rank, and truncation risk. Best when the question is not "what does it mean" but "does the argument actually hold".

Output: `analysis/{stem}_kaozheng.md`.

*Trigger:* "audit the citations", "考证一下", "does this argument hold", "verify the warrant".

---

> **prometheus**

Defines one concept, institution, or proper noun and renders it as a compact ATTRIBUTION-style SVG card. Best when one term needs to become mentally graspable.

Output: `analysis/prometheus/{concept}.svg`.

*Trigger:* "define this concept", "make a concept card", "这个词到底是什么".

---

> **real-thesis**

Excavates the thesis the paper circles but does not quite dare write. Best when the explicit topic feels safer or narrower than the pressure underneath it.

Output: `analysis/{stem}_real-thesis.md`.

*Trigger:* "what is the paper really about", "挖真论题", "what is the author circling".

---

> **constellatio**

Reception-history analysis of a contested phenomenon. Lists the irreducible facts every reading must include, treats each era's reading as diagnostic of that era's own situation, and identifies the structural crack inside the object that lets every era's projection stick (the screen-property). Optional dark-sky constellation viewer shows the readings as visual layers on a shared star field.

Output: `analysis/{stem}_constellatio.md`, optional `analysis/{stem}_constellatio.html`.

*Trigger:* "analyze the reception history", "接受史", "why does every era read it differently", "constellatio".

---

## Standalone Commands

Only two capabilities remain standalone commands:

- `/collate:ocr <pdf>` — the public one-shot orchestration path
- `/collate:status [workspace]` — the status and closure inspector

Everything else is now **skill-first**. In runtimes that expose skills directly, you invoke them as `/collate:<skill>` without a second same-name command shim. If a command ever contains capability the skill lacks, that capability belongs back in the skill.

| Command | What it does | When to use |
|---------|--------------|-------------|
| `/ocr <pdf>` | Dispatches `ocr-pipeline-operator`. Runs prep → OCR → proofread → apply → diff-review → docx → wechat in one call, returns deliverable paths and audit summary. | The public front door. Hand the scan to the agent and let it work the long pass. |
| `/status [workspace]` | Reads `<ws>/_internal/_pipeline_status.json`, reports stage / status / next step, and checks which deliverables are present or missing. | When a run is interrupted, or you need to know what to do next. |

---

## The Agents

Two subagents handle delegation. Skills are passive instructions; agents own end-to-end orchestration with tool access.

| Agent | Role |
|-------|------|
| `ocr-pipeline-operator` | Pipeline conductor. Calls the mechanical runner, builds page review packets, dispatches `historical-proofreader` with page evidence, verifies the review mechanically, then re-enters the runner to chain apply-review / diff-review / to-docx / mp-format and surface the human-facing delivery message. |
| `historical-proofreader` | Domain expert. Loads the matching reference table for the document type, executes the mandatory five-step checklist, emits `raw.review.md` in canonical format with the execution-proof table appended. |

---

## Per-runtime install

The status labels and surface promises for each row are stated honestly in [`## Compatibility`](#compatibility) above. This section gives the live wiring for each one.

Two general-purpose paths to know first:

- **Mechanical-only path:** `python3 scripts/run_full_pipeline.py --pdf <input.pdf>` — useful for CI and batch jobs where no agent is in the loop, but not release proof on its own.
- **One-shot agent path:** `agents/ocr-pipeline-operator.md` + `agents/historical-proofreader.md` — the two agents `/ocr` calls into.

Runtimes that natively read `AGENTS.md` need almost nothing; the rest need a short rule file, a wrapper manifest, or an explicit shell-tool call. The full per-runtime guide lives in [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md).

| Runtime | How to wire |
|---------|-------------|
| **Claude Code** | `/plugin install /path/to/collate`. Native `.claude-plugin/plugin.json`; skills register as `/collate:<skill>`, while only `ocr` and `status` remain standalone commands. |
| **Codex** | Repo ships native `.codex-plugin/plugin.json` plus a repo marketplace at `.agents/plugins/marketplace.json`. For plugin-directory surfaces, restart Codex, choose the repo marketplace, and install `collate`. For direct repo work, `cd /path/to/collate && codex` still auto-loads `AGENTS.md` from the Git root. |
| **Cursor** | Write `.cursor/rules/collate.mdc` with frontmatter `alwaysApply: true` and the line `See AGENTS.md for the full agent contract.`; call `skills/*/scripts/*.py` via Cursor's shell tool. Legacy `.cursorrules` also works. No integration files ship with the repo; untested. |
| **Gemini CLI** | Clone the repo and load `AGENTS.md` as session context; invoke `skills/*/scripts/*.py` via the shell tool. No extension wrapper ships with the repo; untested. |

---

## Dependencies

Python 3.9+ plus:

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
mineru[pipeline]
```

Optional for `mp-format --simplify` only:

```text
opencc-python-reimplemented
```

System:

- macOS: `brew install poppler`
- Debian / Ubuntu: `apt install poppler-utils`

---

## Environment Variables

Scripts read the following. Storage is the caller's choice (`~/.env` is recommended; project-level `.env` is discouraged).

| Variable | Meaning |
|----------|---------|
| `OCR_ENGINE` | `mineru` (local CLI, default) / `baidu` / `mineru-cloud` |
| `MINERU_API_KEY` | Required only when `OCR_ENGINE=mineru-cloud` |
| `BAIDU_OCR_API_KEY` | Required for `OCR_ENGINE=baidu` |
| `BAIDU_OCR_SECRET_KEY` | Same |

---

## Privacy

- **Local MinerU CLI** (default): processing is fully local; nothing is uploaded.
- **MinerU cloud API** (`OCR_ENGINE=mineru-cloud`): the current implementation uploads the PDF to catbox.moe (anonymous public file hosting, 24-hour retention) and submits the URL to MinerU. The PDF is briefly reachable over the public internet; for sensitive material choose the local CLI or Baidu OCR.
- **Baidu OCR** (`OCR_ENGINE=baidu`): each page is base64-encoded and sent over HTTPS to Baidu Cloud, subject to Baidu's ToS.

The plugin itself issues no telemetry or reporting calls. `~/.cache/baidu_ocr_token.json` caches the Baidu access token for 24 hours.

---

## Docs

- [AGENTS.md](AGENTS.md) — agent runtime contract: per-skill calling conventions, decision matrix, failure modes.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — skill boundaries, data flow, file layout.
- [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) — per-runtime integration steps.
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — common errors and workarounds.
- [CONTRIBUTORS.md](CONTRIBUTORS.md) — authors and contributors.

---

## License

- **Code** (all Python scripts, configs, shell snippets, SKILL.md files): [Apache License 2.0](LICENSE)
- **Reference materials** (docs/, skills/*/references/, README, AGENTS.md, authored artwork): [CC BY 4.0](LICENSING.md)
- **Third-party dependencies** retain their own licenses — see [NOTICE](NOTICE).

Copyright 2026 Alice. Co-authored by Alice, Claude Opus 4.6 (Anthropic), and GPT-5.4 (OpenAI); under applicable law governing AI-assisted works, copyright is held by Alice alone, while authorship credit is joint. See [NOTICE](NOTICE) and [CONTRIBUTORS.md](CONTRIBUTORS.md).

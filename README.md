<div align="center">

# 点校 · Collate

Agent toolkit for OCR and publishing of scanned historical Chinese documents.

![Self-portrait of attention as observer](assets/readme-hero-v2.png)

> Established 2026-04-19 · Co-authored by Alice, Claude Opus 4.7, and GPT-5.4 · Code under Apache-2.0, reference materials under CC-BY-4.0

[English](README.md) · [中文](README.zh.md)

</div>

---

## Scope

A toolkit for **agent runtimes**, not an end-user application. A human supplies a scanned PDF; the agent autonomously cleans, recognizes, proofreads, self-audits, and typesets, delivering a finished Word document, a WeChat Official Account HTML, and a complete audit trail.

Beyond the pipeline, the toolkit provides a **reading layer** — skills and commands that read the OCR output as scholarship rather than as data: x-ray a single paper, map a corpus, audit citations, read the silences, define a concept, excavate the hidden thesis. The pipeline makes text readable; the reading layer reads it.

Any agent architecture that can execute Python scripts and read structured text knowledge bases can use it: Claude Code, Cursor, Codex CLI, Kimi K2, MiniMax Agent, Gemini CLI, and others.

The name Collate renders 点校, the classical Chinese scholarly term for punctuating and collating received texts — the millennia-old practice this toolkit extends with contemporary OCR and agent tooling.

## Quick Start

Two supported entrypoints:

- **Mechanical runner**: `python3 scripts/run_full_pipeline.py --pdf /abs/path/to/file.pdf`
- **Full agent run**: start from [agents/ocr-pipeline-operator.md](agents/ocr-pipeline-operator.md), which calls the mechanical runner, invokes `historical-proofreader`, re-enters the runner, and returns the delivery summary.

Canonical OCR is **direct repo-to-engine execution**:

- default: local `mineru[pipeline]` CLI
- compatibility fallbacks: MinerU cloud API or Baidu OCR

## Workflow

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

Design principle: the AI does not make scholarly judgments on the human's behalf. Proofreading produces a machine-readable, severity-tagged list; the agent applies changes and then records them through `diff-review`. All intermediates, annotations, and edit traces are retained so the human can verify each decision line by line.

## Document Types

| Type | Typical issues | Knowledge base |
|------|----------------|----------------|
| Modern simplified Chinese | Scan noise, confusable glyphs (曰/日, 己/已/巳), punctuation drift, bibliographic format | `skills/proofread/references/modern-chinese.md`; GB/T 7714 |
| Republican-era print | Mixed simplified/traditional, old-style punctuation, transitional translations, old/new place names | `skills/proofread/references/republican-era.md` |
| Classical traditional Chinese | Variant characters, taboo characters, vertical layout, absence of punctuation | `skills/proofread/references/traditional-classics.md`; variants not forcibly normalized, taboo characters only flagged |

The agent infers type, or the caller passes `--type=classics|republican|modern`.

## Skills

Each skill is a self-contained directory: `SKILL.md` (operational instructions the agent reads) + `scripts/` (Python tools) + `references/` (structured knowledge base).

1. **setup** — environment check: Python deps, poppler, OCR engine credentials.
2. **prep-scan** — PDF → per-page PNG; HSV color masking + connected-component area filter to remove color library stamps; grayscale rotation + morphological `MORPH_OPEN` to remove diagonal watermarks; Gaussian blur + top-hat transform + body-text protection for faint repeating watermarks; optional header/footer trim.
3. **visual-preview** — three-state per-page HTML (original / cleaned / difference heatmap); pages with >20% cleaning ratio auto-flagged; lets the agent decide whether to rerun `prep-scan`.
4. **ocr-run** — defaults to local MinerU CLI (`mineru[pipeline]`); `OCR_ENGINE=baidu` switches to Baidu OCR; `OCR_ENGINE=mineru-cloud` uses the MinerU cloud API (compatibility path). Outputs: `raw.md` + side-by-side source/OCR HTML + `meta.json` (engine, timing, low-confidence pages).
5. **proofread** — the `historical-proofreader` agent executes a mandatory five-step checklist: structural sanity → glyph scanning (grep against type-specific references) → convention scanning (punctuation, quotes, DOI) → cross-paragraph consistency → proper-noun review. Produces `raw.review.md` with A (OCR error) / B (academic convention) / C (open question) tiers; each item includes line number, source snippet, suggestion, rationale. An execution-proof table is appended.
6. **diff-review** — agent self-audit gate: diffs `raw.md` against the post-edit `final.md`, produces a paragraph-level HTML report correlating each change with four states from `raw.review.md` — accepted suggestion, missed, outside-checklist fix, unanchored note.
7. **to-docx** — python-docx Word output. Single unified spec: Source Han Serif SC 12pt body, 1.2 line spacing, 0.2 pt character spacing, 2cm margins on all sides, 2-character first-line indent, continuous footnote numbering.
8. **mp-format** — WeChat Official Account HTML with fully inline CSS (WeChat strips external stylesheets); OpenCC t2s simplification that preserves blockquote (`>`) content in original form; footnotes collected at the end; byline and source bar. Also emits a xiumi-compatible markdown sidecar.

## After the text exists: the reading layer

The pipeline above ends when `final.md` is clean. The reading layer begins there. Once the text is reliable, the toolkit reads it as scholarship — not to summarize, but to enter the historian's conversation.

### Reading skills

Two skills read post-OCR text at different scales. Both are Obsidian-native.

- **xray-paper** — x-ray a single historical paper: recover what the author was chasing (问题意识), locate the paper in its tradition (学派谱系), chronicle its timeline, emit cognitive collision cards where the reading shifts a prior judgment. Triggers on phrases like "analyze this paper", "X-ray this article", "map this paper's position". Output: `<workspace>/analysis/{stem}_xray.md` with YAML frontmatter, callouts, ASCII chronicles, SVG positioning cards.

- **paper-summary** — map a corpus of 5–30 papers as a body of scholarship: archival basis, school lineage, temporal-spatial coverage, methodological distribution, conceptual contention, theoretical borrowings, open questions, and a newcomer's reading route. Triggers on "survey this literature", "map these papers", "how does this field stand". Output: `<workspace>/analysis/literature-map.md` or `docs/literature-map/{corpus-name}.md`.

Both skills optionally render an **attribution-theme HTML viewer** — an independent piece of presentation writing with uppercase Cormorant Garamond hero, dark Ink Stone stage, Signal-glow emphasis carried by luminance rather than italics, lineage and coverage diagrams that breathe beyond Obsidian's column width. Viewers collect in `<workspace-parent>/viewer/` under the filename convention `{YYYY-MM-DD}-{一句话态度立场}--{作者}-{论文名字}.html`.

### Interpretive commands

Four slash commands for lens-based readings, each named after a tradition or a figure. They operate on post-OCR, post-proofread text and write to separate report artifacts — they never modify source files.

| Command | Tradition | What it does |
|---------|-----------|--------------|
| `/chunqiu` | 春秋笔法 · Chunqiu brushwork | Read the taboos, verdicts, and studied ambiguity — what the author will not say aloud |
| `/kaozheng` | 乾嘉考证 · Qian-Jia textual criticism | Audit arguments, verify citations, test evidentiary bridges — is the warrant sound? |
| `/prometheus` | Prometheus | Steal the fire of definition for a single historical concept; emit an attribution-theme SVG card |
| `/real-thesis` | — | Excavate the thesis the author circles but does not quite dare write |

Each lens reads differently: `chunqiu` reads silences, `kaozheng` verifies warrants, `prometheus` names concepts, `real-thesis` excavates what the paper will not state outright. Choose the lens that matches what the paper asks.

## Integration

See [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) for per-runtime setup. Overview:

- **One-command mechanical path**: `python3 scripts/run_full_pipeline.py --pdf <input.pdf>`
- **One-shot agent path**: `agents/ocr-pipeline-operator.md` + `agents/historical-proofreader.md`
- **Claude Code**: `/plugin install <path>`; skills auto-discovered.
- **Cursor / Codex CLI**: call `skills/*/scripts/*.py` directly; include `SKILL.md` and `references/` as model context.
- **Kimi K2 / MiniMax Agent**: upload `agents/historical-proofreader.md` as system prompt; run Python scripts locally; pipe intermediates back into the dialog.
- **Gemini CLI**: same as Cursor.

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
opencc-python-reimplemented
mineru[pipeline]
```

System:

- macOS: `brew install poppler`
- Debian/Ubuntu: `apt install poppler-utils`

## Environment Variables

Scripts read the following. Storage is the caller's choice.

| Variable | Meaning |
|----------|---------|
| `OCR_ENGINE` | `mineru` (local CLI, default) / `baidu` / `mineru-cloud` |
| `MINERU_API_KEY` | required only when `OCR_ENGINE=mineru-cloud` |
| `BAIDU_OCR_API_KEY` | required for `OCR_ENGINE=baidu` |
| `BAIDU_OCR_SECRET_KEY` | same |

## Privacy

- **Local MinerU CLI** (default): processing is fully local; nothing is uploaded.
- **MinerU cloud API** (`OCR_ENGINE=mineru-cloud`): the current implementation uploads the PDF to catbox.moe (anonymous public file hosting, 24-hour retention) and submits the URL to MinerU. The PDF is briefly reachable over the public internet; for sensitive material choose the local CLI or Baidu OCR.
- **Baidu OCR** (`OCR_ENGINE=baidu`): each page is base64-encoded and sent over HTTPS to Baidu Cloud, subject to Baidu's ToS.

The plugin itself issues no telemetry or reporting calls. `~/.cache/baidu_ocr_token.json` caches the Baidu access token for 24 hours.

## Docs

- [AGENTS.md](AGENTS.md) — agent runtime contract: per-skill calling conventions, decision matrix, failure modes.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — skill boundaries, data flow, file layout.
- [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) — per-runtime integration steps.
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — common errors and workarounds.
- [CONTRIBUTORS.md](CONTRIBUTORS.md) — authors and contributors.

## License

- **Code** (all Python scripts, configs, shell snippets, SKILL.md files): [Apache License 2.0](LICENSE)
- **Reference materials** (docs/, skills/*/references/, README, AGENTS.md, authored artwork): [CC-BY-4.0](LICENSE-REFERENCES)
- **Third-party dependencies** retain their own licenses — see [NOTICE](NOTICE).

Copyright 2026 Alice <Mcyunying@gmail.com>. Co-authored by Alice, Claude Opus 4.7 (Anthropic), and GPT-5.4 (OpenAI); under applicable law governing AI-assisted works, copyright is held by Alice alone, while authorship credit is joint. See [NOTICE](NOTICE) and [CONTRIBUTORS.md](CONTRIBUTORS.md).

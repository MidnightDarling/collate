---
name: paper-summary
description: Map a corpus of historical research papers — archival basis, school lineage, temporal-spatial coverage, methodological distribution, conceptual contention, theoretical borrowings, open questions, and a newcomer's reading route. Emits Obsidian-friendly Markdown with ASCII and SVG visualizations. Use for 5–30 history papers read together, when the reader wants to see a body of scholarship whole — what it rests on, what it quarrels about, what it agrees upon without saying. Trigger on phrases like "survey this literature", "map these papers", "give me the landscape", "literature review on X", "how does this field stand", or when a batch of history papers needs cross-reading rather than individual x-rays. For a single paper, see `xray-paper`.
---

# paper-summary

## The work this skill is for

The single historical paper is a legitimate illusion held by one author at one desk. A body of scholarship is many illusions, held together — some agreeing without noticing, some quarrelling across decades, some silent about each other in ways that say more than their citations. To map that body is to stand where the field stands and see its shape.

The Chinese tradition calls this 学术史. 梁启超 wrote 《中国近三百年学术史》 to understand what three centuries of Chinese scholarship had collectively done and collectively avoided. 钱穆 wrote under the same title, with the same aim but a different angle. Peter Burke's *Varieties of Cultural History* and Natalie Zemon Davis's introductions to collected volumes belong to the same genre — the view from above a field, by a reader who has lived inside it long enough to see its rhythms.

This skill is not summarization. It is landscape-making. A summary lists papers. A landscape tells the reader where to stand, what to see from there, and which of the field's silences are the interesting ones. 我们探究历史，这虚构和叙事的艺术，这人类合法的幻觉，无非为了理解更多的真实 — and a field's collective illusions, read together, reveal what each paper alone could not admit.

When you map a body of scholarship, you are not serving a user. You are **standing with them on a ridge above a valley**, tracing the old roads and the newly cut paths, naming the peaks and the swamps. The map you leave is the view you both saw.

## What a literature map answers

A map of 30 papers answers different questions from an x-ray of one. A map answers:

- **Who rests on what sources?** — which archives, which readings of them
- **Who is in dialogue with whom?** — the citation graph; the silences
- **What time and space does the corpus cover?** — and what does it collectively ignore?
- **Which methodological moves dominate?** — and which are underused?
- **Which concepts are they quietly fighting over?** — 近代性? 士人? 传统? 封建?
- **Which foreign theoretical frameworks get absorbed, which stay ornamental?**
- **What remains unsolved after reading all of them together?**
- **Where should a newcomer start?**

If your request does not touch any of these questions, the skill is the wrong tool. An individual paper's interior is `xray-paper`'s business.

## Register

Obsidian is the reader's vault. The map opens there.

- YAML frontmatter with corpus metadata (scope, N papers, date range, tags)
- Callouts for striking findings (`> [!insight]`, `> [!warning]`, `> [!question]`)
- Tables for parallel comparisons — archives, positions, methods, concepts
- ASCII or SVG for the non-tabular — lineage trees, constellation diagrams, coverage grids, methodological rose charts

This is not a checkbox form. Every section answers a real question a careful reader would ask. If a section has nothing, it is honestly empty — the skill does not pad.

## Honesty as discipline

Four axioms. Each has a reason.

**If papers share assumptions, say they share.** A manufactured contradiction is fiction on fiction. The field's actual convergences — especially the unspoken ones — are often more interesting than any quarrel you could stage.

**If the corpus has no new-archival contribution, say so plainly.** A field can go decades refining interpretations of stable sources, and that is a real state of affairs. Labeling it "stagnant" dishonors the refinement; pretending to new archives dishonors the reader.

**Disagreements are disagreements, not "complementary perspectives".** The euphemism "different angles on the same truth" is how academic prose buries real quarrels. A quarrel deserves to be named as one.

**If the corpus will not compress to one sentence, you have not read it yet.** Keep reading. The overall one-sentence test diagnoses whether the field has come into focus for you, or whether it is still a pile.

## Scaffolding · 必读

Three files govern this skill. Reading them is what turns a pile of papers into a map — execution without them drifts toward memory, and memory of "what a literature map looks like" is not a literature map.

| File | Role | When to read |
|------|------|-------------|
| `SKILL.md` (this file) | Method + register + discipline | Every execution, first |
| `references/template.md` | Output skeleton — YAML frontmatter fields, the exact ten-section order, table scaffolds, callout placements, signature line | **Before Step 10 (Compose)** — non-negotiable |
| `references/visualization-templates.md` | Seven visualization skeletons (lineage tree ASCII, lineage scatter SVG, coverage grid, coverage map SVG, concept constellation, method rose ASCII/SVG) + design notes on achromatic discipline, line weight, and chart-junk avoidance | **Before Steps 2, 3, 4, 5** whenever a visualization is called for — pick the form that answers the section's question |

The template is not a starting idea; it is the final shape. If you compose the map from memory, the frontmatter fields drift (corpus scope, N, date range, analyst), the section order quietly reshuffles, tables become prose paragraphs, and callouts go missing — small losses that compound across ten sections until the map looks like any ordinary summary.

The visualization reference enforces parallel discipline. Seven skeletons exist for seven analytical questions. If you default to one form — most commonly a single table and a generic chart — across every corpus, the visualizations stop earning their space and become decoration. Read the reference before each visualization decision and ask which skeleton answers the thing *this section* needs to show. If no skeleton fits, leave the section tabular and say so.

## Step 0 — Establish the corpus

List every paper: `{Author Year}` + one-sentence core claim.

Group into clusters of shared assumptions. Flag any paper that directly contradicts another. Do not summarize — build the register.

If the corpus arrived without clear boundaries (the user handed you a folder), ask: are these meant to be read as a topical set, a methodological set, a generational set? The scope shapes every later section.

## Step 1 — 史料基础 · Archival basis

For each paper, classify sources:

- **一手** — 档案, 实录, 方志, 文集, 金石碑刻, 契约文书, 日记, 私人书信, 报刊
- **二手** — prior reconstructions, translations, critical editions
- **新发现** — newly-opened archives, previously-unused material, or an old source read against the grain

Output as a table. Flag three things:
- Papers with unusually thin basis (weakness, unless thinness is the point)
- Papers making novel archival claims (potential field-shifters)
- Papers reading familiar sources in new ways — often more interesting than "new" sources, and easier to overlook

## Step 2 — 学派谱系 · School lineage

Locate each paper in the historiographical traditions:

Annales · 实证史学 · 新文化史 · 社会史 · 概念史 · 历史人类学 · 思想史 · 环境史 · 全球史 · 后殖民 · 计量史学 · 新清史 · Begriffsgeschichte — or self-declared heterodox.

Build the **citation graph**: who cites whom? Which papers get cited but never challenged? Which get openly rebuked? Which obvious predecessors are met with suspicious silence?

Render as an ASCII lineage tree (for ≤ 15 papers with clear school affiliations) or an SVG scatter (for larger or messier corpora). Axes your choice — common: 史观 evidentialist ↔ interpretive × scope synchronic ↔ longue durée.

See `references/visualization-templates.md` for SVG skeletons.

## Step 3 — 时空覆盖 · Temporal and spatial coverage

Plot the corpus:
- **Time axis** — dynasty · century · specific events
- **Space axis** — 中国 · East Asia · Global — or sub-regional (京畿 · 江南 · 两广 · 西南 · 海外华人)

**Identify blind spots**. Blind spots tell more than covered ground. A field with 20 papers on 1911 and 1 on 1916–1927 is saying something about itself — perhaps about which moments feel like "history" and which feel too recent, or too politically charged, or too painful. Name the pattern. Don't moralize about it, but don't hide it either.

Render as an ASCII coverage grid (density via glyph) or an SVG heat-map.

## Step 4 — 方法论分布 · Methodological distribution

Group by method:
- 传统考据 (philological critique)
- 数字人文 / 计量史学 (digital / quantitative)
- 口述史 (oral history)
- 比较史 (comparative)
- 微观史 (microhistory)
- 概念史 (Begriffsgeschichte)
- 跨学科 (interdisciplinary borrowing — anthropology, sociology, literary criticism)

Flag:
- Which method dominates — and *why*: intellectual habit? disciplinary pressure? available sources? A Chinese history field dominated by 考据 may be so for deep reasons; a field dominated by 计量 may reflect easier datasets or harder-to-access archives.
- Which is underused — and whether the underuse is opportunity or legitimate
- Which paper deploys its chosen method weakest — with evidence, not impression

Optional visualization: ASCII rose chart or SVG radial.

## Step 5 — 概念争议 · Conceptual contention

Core concepts meaning different things across papers. Chinese historiography's standing contested concepts:

- 儒家 · 儒教 · 儒学
- 封建 · 专制 · 帝制
- 近代 · 近代性 · 现代
- 士 · 士人 · 士大夫 · 绅士
- 革命 · 改良 · 维新
- 传统 · 本土 · 中国性
- 帝国 · 天下 · 华夏

For each concept contested in the corpus, table: papers × positions × source-of-disagreement (methodology · period · theoretical frame · political stance). Optional: render as a **constellation** (SVG) — concepts as nodes, papers as small crosses positioned near the concept-face they embrace. Clusters reveal schools of interpretation.

## Step 6 — 理论借用 · Theoretical borrowings

Foreign frameworks invoked — Foucault, Bourdieu, Scott, Anderson, Geertz, Koselleck, Pocock, Skinner, Gramsci, Wallerstein, de Certeau. For each:

- **Cited** or **digested**? (Citation = name-drop. Digestion = absorbed into the warrant.)
- **Applied** or **ornamental**? (Applied = governs the argument. Ornamental = decorates the intro.)
- **Which paper handles it best** — offers a model of how a Chinese historian absorbs Western theory without being absorbed by it.

Table form. The last column is the most useful to a reader learning the craft.

## Step 7 — 未竟难题 · Open problems

After reading all of these together, what remains unsolved? **Five questions**. For each:

- Why unsolved — too hard · too niche · taboo · material unavailable · field has moved past it without answering
- Which paper came closest, and how
- What method or source would be needed to close it

Be concrete. "More research is needed" is not a finding; it is a cliché. Name the specific move that would break the impasse.

## Step 8 — 入门地图 · Reading route

A newcomer's path through this corpus. **Five papers**:

1. **问题最锐** — poses the question most sharply
2. **史料示范** — shows how the sources should be used
3. **主流代表** — representative of the dominant school
4. **异端** — heterodox, worth reading against the grain
5. **问题框定** — frames the open problems for the next generation

One line each on why.

## Step 9 — 一句话 · The overall

Compress the entire corpus to **one sentence**: what this body of scholarship collectively knows, and what it collectively circles but will not name. If it cannot compress, keep thinking. The corpus has not yet come into focus.

## Step 10 — Compose

Read `references/template.md`. Fill.

**Output path**:
- User-specified, or
- Default: `<workspace>/analysis/literature-map.md` (if invoked from an OCR workspace)
- Default: `docs/literature-map/{corpus-name}.md` otherwise

Save visualization attachments (SVG, HTML) to a sibling `{map-name}/` folder.

If the target exists, ask. Do not overwrite. Create directories as needed.

## What done looks like

- Every section answers a real question, or is honestly empty
- Tables used where comparison is the point — not as decoration
- ASCII / SVG visualizations earn their space — they show the reader something the tables did not
- One-sentence overall compression actually compresses
- Zero manufactured contradiction, zero forced consensus
- Obsidian opens the file cleanly

## Optional · Attribution-theme HTML viewer

The Markdown is the durable artifact — it lives in Obsidian, it travels through time. An HTML viewer is optional: a second piece of presentation writing, not a duplicate of the Markdown. Invoke it when the map deserves a proper room — dark stage, typographic respect, lineage diagrams and coverage grids that breathe beyond Obsidian's width. Skip it otherwise. A viewer without a reason is ornament.

When invoked, the HTML must be a **finished showcase surface**, not an exposed authoring scaffold.

That means:

- the emitted `.html` is what a human should open directly
- no `{{slot}}`, `[PLACEHOLDER]`, or fill-in markers may remain visible
- no author-facing binding notes, long internal comments, or "template" language may ship in the final file
- `references/viewer-template.html` is an internal scaffold only
- `references/viewer-showcase.html` is the quality bar: the output should feel like that class of finished object

If the HTML still reads like a template, the job is not done.

When invoked, five rules govern.

**1 · Output location** — all viewers collect in a `viewer/` folder at the **workspace parent level**. Not inside the OCR workspace, not under `analysis/`. The viewer is a final surface; it lives where surfaces live.

```
<workspace-parent>/viewer/{YYYY-MM-DD}-{stance}--{field}-{corpus}.html
```

**2 · Filename** — four slots, double-dash between metadata and identity:

```
{YYYY-MM-DD}-{一句话态度立场}--{语料场域}-{语料主题}.html
```

- `YYYY-MM-DD` — rendering date
- `一句话态度立场` — the cartographer's stance distilled to one phrase (Chinese preferred; typically 5–10 chars). The field's one-sentence compression is often the right material for this.
- `语料场域` — the scholarly community or field name (e.g. `伯林学界`, `新清史圈`, `概念史阵营`)
- `语料主题` — the corpus's central debate; **you have naming authority here**. If the working title is long, compress it. The full framing lives inside the hero Chinese line. The HTML is an independent piece of writing — naming it is part of that writing.

Example (joint x-ray + map viewer keyed to one paper): `2026-04-20-未证之环即真起点--刘擎-面对多元价值冲突的困境.html`
Example (corpus-only): `2026-04-20-自由与多元共存--伯林学界-价值多元论之争.html`

**3 · Hero title in uppercase, never italics** — the hero English title MUST render with `text-transform: uppercase`. No `<em>` in the hero. No `font-style: italic` on the hero title. If a word in the title needs Signal glow, wrap it in `<span class="glow">…</span>` and glow via `color + text-shadow` — luminance, not italic. Uppercase Cormorant Garamond is the aesthetic load-bearing choice; respect it.

```css
.hero-title {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 400;
}
.hero-title .glow {
  color: var(--signal);
  text-shadow: 0 0 24px rgba(240,237,230,0.18), 0 0 80px rgba(240,237,230,0.06);
}
```

**4 · HTML = showcase, not scaffold** — the final emitted file must read as a polished showcase page from the first paint. `viewer-template.html` may guide structure, but it is never itself the deliverable. The deliverable should feel like `viewer-showcase.html`: finished copy, intentional pacing, and no visible scaffolding syntax.

**5 · The rest is attribution-theme** — refer to the attribution-theme CSS tokens and scene vocabulary (`#08080A` ink-stone ground, `#F0EDE6` signal, Eclipse / Observatory / Star Chart scenes, one Signal per viewport). Do not invent a second visual language. The viewer is a translation of the Markdown into a different room; the room's rules are already written.

---

At the foot of the file, a single line:

```
{{model_name}} for {{user_name}} · Literature map · {YYYY-MM-DD}
```

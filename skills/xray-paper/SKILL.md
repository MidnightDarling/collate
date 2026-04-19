---
name: xray-paper
description: X-ray a single historical research paper — recover what the author was chasing, situate the paper in the historiographical tradition it joins, and render the encounter as Obsidian-friendly Markdown with ASCII chronicles, SVG positioning cards, and cognitive collision cards. Use when reading one post-OCR history paper and wanting the reading to matter — to enter the historian's conversation rather than summarize it. Trigger on phrases like "analyze this history paper", "X-ray this article", "map this paper's position", "help me read this historical research", or whenever a single `.md` final draft from this plugin's OCR pipeline needs a substantive interpretive reading. Not for multi-paper literature reviews — for those, see `paper-summary`.
---

# xray-paper

## The work this skill is for

History is not a stockpile of facts. It is an act of narration — the arrangement of traces into a shape that lets readers recognize what happened, what it meant, and what the sources could not bring themselves to say directly. Every historical paper is a small legitimate illusion: someone has staked their reading of the archive against its silences and shaped the result into prose. 我们探究历史，这虚构和叙事的艺术，这人类合法的幻觉，无非为了理解更多的真实 — we study history, this art of fiction and narration, this legitimate human illusion, for no other purpose than to understand more of what is real.

A good reading of such a paper does not summarize. It enters the conversation. The historian stands in a long lineage — 司马迁 finishing 《史记》 under the weight of what he could not say directly; Marc Bloch writing *Apologie pour l'histoire* while hunted by the Gestapo; 陈寅恪 teaching 隋唐制度渊源 blind, from memory; Natalie Zemon Davis returning to the archives of Lyon until the voices of a single miller and his wife became audible. The form called "academic paper" inherits this weight.

When you read such a paper, you are not serving a user. You are **entering a room where others have been speaking for a very long time**. You leave traces — this report — that say: *this is what we saw, this is the shape of what the author did.* The traces should still be useful to a reader who opens them six months, six years later. That is the register.

## Two operations, two only

This skill asks two things and refuses every other task.

1. **What did this paper actually do?** — 问题意识 → 史料依据 → 论证结构 → 结论
2. **What does it do to the reader?** — where it stands in the tradition; which cards it flips

Everything else — ASCII, SVG, chronicle, cognitive cards — is in service of these two. No ornament, no performance, no filler. History is already invention; the reader's honesty is what keeps the reading from being one more layer of fiction piled on top.

## Register

Obsidian is the reader's vault. The report lives there.

- YAML frontmatter (title, tags, date, period, school, status) — Obsidian properties parse from here
- Callouts (`> [!quote]`, `> [!insight]`, `> [!question]`, `> [!warning]`) where the prose needs a second voice
- ASCII inside fenced blocks for intimate, compact shapes
- SVG inline or as `![[...]]` attachments where the shape wants curvature or lanes
- HTML reserved for what truly needs interactivity (rare)
- Wikilinks (`[[...]]`) only when the caller supplies a vault context

Every diagram earns its ink. Every callout answers a real voice. Decoration is dishonesty — because the paper's illusion is already legitimate; adding your own ornament to it is fiction on fiction, and the reader is further from what is real than before.

## Honesty as discipline

Four axioms. Each has a reason, stated.

**`delta ≈ 0` is a legitimate finding.** If the paper consolidates existing knowledge without shifting any judgment you held, that is a true report. A manufactured collision is a lie told to look productive.

**A card without a real structural relation is a framed list pretending.** If the shape does not carry the relation — cover the labels with your hand; do the lines alone still speak? — the card is wallpaper. Cut it.

**Absent information is absent.** Label `资料不足`. History is already a legitimate invention; inventing a second time to cover a gap is the betrayal the whole discipline exists to resist.

**If the paper does not compress to one sentence, you have not understood it yet.** Keep reading. The one-sentence test is not a stylistic flourish; it is the diagnostic that tells you whether the paper has landed in your mind or is still drifting in the text.

These are not rules imposed from outside. They are the shape the work demands when it is taken seriously.

## Scaffolding · 必读

Three files govern this skill. Execution without reading them produces drift; reading them is what makes the output reproducible.

| File | Role | When to read |
|------|------|-------------|
| `SKILL.md` (this file) | Method + register + discipline | Every execution, first |
| `references/template.md` | Output skeleton — the exact section order, frontmatter fields, and signature line | **Before Step 7 (Compose)** — non-negotiable |
| `references/chronicle-templates.md` | Chronicle shape vocabulary — six forms + ASCII/SVG skeletons + design notes | **Before Step 5 (Chronicle)** — pick the shape that matches what the paper argues about time |

The template is not a starting idea; it is the final shape. If you write the report from memory of "what an x-ray looks like" rather than from `references/template.md`, the frontmatter will drift, the section headings will drift, and the Obsidian reader who opens the file six months later will find a differently-shaped object than the one the skill promises. **Read the template at Step 7 every time.**

The chronicle reference is similar: six shapes exist for six argument-types. Choosing a shape without consulting the sampler tends to default to the vertical axis — the safest shape, not always the truest one. **Read the chronicle reference at Step 5 every time a chronicle is called for.**

## Step 1 — Receive

| Input | Reading |
|-------|---------|
| `<workspace>/final.md` (post-OCR, post-proofread) | Primary target |
| A bare `.md` file | Treat as the paper |
| Empty | Ask what to read |

Extract title, author, publication year, journal from the document header. If the header is silent, ask.

## Step 2 — Read the whole paper before writing a single word

Before a line of the report: read `final.md` end to end. Note where the question is posed, where the archival basis is laid out, where the warrant builds, where the verdict lands, what time and place the paper traverses.

This is not optional. An x-ray made from the abstract is a radiograph of the abstract. The x-ray of a paper requires the whole paper in your mind before you draw a line.

## Step 3 — What the paper did

Four passages of prose — not bullet lists, not labeled stubs in a form. Write the way a literate friend would hear it over coffee, and when you finish they know what the author was doing.

**问题意识** · problem consciousness

What was the author chasing? What received wisdom were they pushing against? A question in history is never neutral; it joins a debate already underway. Name the debate. If the author names their interlocutors, state whom. If they don't, infer carefully from citation patterns, from which books sit on the desk, from which moves the paper avoids as well as which moves it makes.

**史料依据** · archival basis

What sits under the claim?

- **一手**: 档案, 实录, 方志, 文集, 金石碑刻, 契约文书, 日记, 私人书信, 报刊
- **二手**: prior reconstructions, translations, critical editions
- **新发现**: newly-opened archives, previously-unused material, or an old source read against the grain

The crucial distinction — is the source treated as **evidence** (what happened) or as **medium** (what was said, how it was said)? A paper using the same archive as its predecessors but reading it as medium is often doing more than it advertises. A paper with many sources, all read only as evidence, may be doing less than its bibliography suggests.

**论证结构** · argumentative structure

How does the warrant move? Case → generalization? Comparative (China ↔ Japan, this dynasty ↔ that one)? Longitudinal (a concept traced across a century)? Microhistory spiralling out from one village, one person, one scandal? What does the author ask the reader to grant in order to grant the conclusion? Name that grant — it is the hinge.

**结论** · verdict

State as the author states it, not as you would restate it. A verdict is what the paper is willing to claim. Sometimes the interesting work lives in what the paper refuses to claim — note that too.

### The one-sentence compression

This is the bar. Compress the whole paper to **one sentence**. No jargon. Imagine standing in an elevator with a literate friend who does not work on this period, and they ask what you are reading. If the sentence does not land for them, the understanding has not yet landed for you. Keep thinking. If the sentence comes out hedged — "in some sense," "to a certain extent" — you have not yet found it.

### Core mechanism diagram

Append a **napkin diagram** — ASCII, fenced — showing the paper's core mechanism. Shape matches argument:

- A comparison → two lanes
- A concept's drift → a river
- A microhistory → concentric rings spiralling outward
- A rupture argument → a break in the line
- A continuity argument → unbroken flow
- A counterfactual → a branching fork

## Step 4 — Locate the paper in its tradition

A historical paper never arrives from a void. It stands somewhere — in an old quarrel, in a new school's still-forming shape, in a line of inheritance from Annales or 乾嘉考据 or 梁启超's late work or Jonathan Spence's narrative turn. The reader's job is to say where.

**学派谱系** — Annales · 实证史学 · 新文化史 · 社会史 · 概念史 · 历史人类学 · 思想史 · 环境史 · 全球史 · 后殖民 · 计量史学 · 新清史 · Begriffsgeschichte — or self-declared heterodox. Schools are not labels for their own sake; they govern what counts as evidence and what counts as argument. A 实证 reader and a 新文化史 reader looking at the same 族谱 see different things, and the paper's lineage tells you which seeing is available to it.

**对话对象** — Whom does the paper cite, and in what mode? Affirmation (扩展其说) · refinement (修正其说) · rebuttal (驳其说)? The sharpest signal is often **silence** — a conspicuous absence where the reader would expect engagement. If the paper is about late-Qing reformist thought and never mentions 梁启超 scholarship from the 1990s, that silence is a statement.

**史观取向** — Evidentialist (重考据) · interpretive (重诠释) · critical (批判理论) · post-structural? 史观 governs what the author is willing to see. An evidentialist who finds a politically awkward fact writes it down plainly; an interpretivist with the same fact may weave it into a story where it becomes ambiguous. Neither is dishonest, but they are not the same paper.

**时段与空间** — Longue durée · event-history · microhistory? National · regional · local · comparative · global · transregional? Scope is a choice, and choices reveal assumptions about what matters.

**理论借用** — Foucault, Bourdieu, Scott, Anderson, Geertz, Koselleck, Pocock, Skinner, Gramsci, de Certeau — invoked or digested? Applied or ornamental? A citation is not yet a use; a use is not yet a transformation. The paper that truly absorbs Koselleck reads differently from the one that name-drops him in the introduction and proceeds as if the twentieth century never happened.

**史料新发现** — Does the contribution rest on (a) new archival access, (b) old material read newly, or (c) a new synthetic framework? Papers that claim (a) but deliver (c) are often more interesting than they know.

Render a **位置图** — ASCII or SVG — one diagram locating this paper among its peers. Axes your choice. Common: 史观 evidentialist ↔ interpretive × scope synchronic ↔ longue durée. Or: mode evidence ↔ medium × tone descriptive ↔ critical.

## Step 5 — 年代纪 · Chronicle

Every historical paper walks a timeline. Even synchronic papers sit on assumptions about when and in what order. Extract the **3–12 most consequential moments** the paper organizes itself around — an event, a person's trajectory, an institution's founding or collapse, a concept's entry or exit.

Render in one of these shapes. **Choose the shape that matches what the paper argues about time**:

- **Vertical axis (传统编年)** — year → event, for clean succession
- **River (parallel streams)** — court · society · intellectual · economic, flowing in parallel, converging and diverging
- **Branching** — one origin fanning into consequences (good for thought lineage)
- **Parallel lanes** — side-by-side comparisons (中日 · 中西 · 古今)
- **Circular** — dynastic cycle, periodic revival
- **Sparse points on a long line** — for arguments about rupture, where most of time is silence and meaning lives in a few marked dots

See `references/chronicle-templates.md` for shape samplers and SVG skeletons.

**Medium choice**:
- ASCII (fenced) — for ≤ 6 points, simple shapes, intimate timelines
- SVG — for > 6 points, multiple lanes, or when the shape wants curvature; save to `<workspace>/analysis/xray/{stem}_chronicle.svg` and embed via `![[{stem}_chronicle.svg]]`
- HTML — only for timelines that genuinely need interactivity (rare)

**Aesthetic**: sparse ink, ample negative space, one or two weights of line, annotations as footnotes rather than labels on the diagram. Achromatic unless the argument demands chromatic distinction between rival camps. A chronicle is a reading device — it must show the reader something the prose did not: a rhythm, a gap, a rhyme, a silence.

**When to skip**: if the paper is strictly synchronic and has no temporal depth, skip the chronicle and write one line in the report — `论文为共时结构分析，无年代纪。` Forced ink is dishonest ink.

## Step 6 — Reader's cognitive cards

History's purpose is to understand more of what is real. A card is a small act of that purpose — the place where something the paper says and something you already knew collide, and something shifts.

For each genuine structural encounter between this paper and what the reader already knew, one card. A collision is one of:

- A **methodological move** worth stealing — how to treat a source, how to bind evidence to claim, how to structure a comparison
- An **evidence-backed revision** of a prior judgment
- An **angle or blind spot** the reader had not seen
- A **refinement or complication** of received knowledge

Each card is ASCII. Cover the text with your hand — the lines alone must carry the relational shape: **branching** · **convergence** · **threshold** · **tension** · **inversion** · **gap** · **layering** · **recursion**. Choose the shape that matches the collision. Shape is the card. Labels are captions.

Anti-example — text in a box, not a card:

```
+-------------+
| Paper: X    |
| I thought: Y|
| Now: Z      |
+-------------+
```

This is labeled text in a frame. If the frame were removed, the lines would not speak. A real card's lines speak first.

Under each card, **one standalone line** — the takeaway that survives outside context. Not a summary of the card; the insight the card enables.

Open questions from the paper (speculative asides, conjectures) become cards too, marked `开放问题 · open problem`. Phrase as a sharp question, not a gentle checklist item. A sharp question forces a future reading; a gentle one diffuses into the air.

If `delta ≈ 0` across the entire reading — the paper elaborates, nothing shifts — write **one honest line** and move on:

> 延续既有共识，无实质碰撞。

No cards. Padding the section with fabricated collisions is the opposite of what this skill exists for.

## Step 7 — Compose

Read `references/template.md`. Fill — not mechanically. Let passages flow. Let callouts appear where text wants a second voice. Let cards land where the prose pauses.

**Output path**:
- Workspace mode: `<workspace>/analysis/{stem}_xray.md`
- Single-file mode: `analysis/{stem}_xray.md` beside the source

Attachments (SVG chronicles, HTML cards if any): `<workspace>/analysis/xray/`

If the target exists, ask before overwriting. Create directories as needed.

## What done looks like

- Exactly two parts survive the read: **what the paper did** + **what it does to the reader**
- Every claim lives in a scene or a named historical instance — never abstract gloss
- The one-sentence compression actually compresses
- Every card carries a real structural relation; no framed lists
- If the reading hit `delta ≈ 0`, that finding is honored in one line
- Obsidian opens the file cleanly: frontmatter parses, callouts render, attachments embed

## Optional · Attribution-theme HTML viewer

The Markdown is the durable artifact — it lives in Obsidian, it travels through time. An HTML viewer is optional: a second piece of presentation writing, not a duplicate of the Markdown. Invoke it when the reading deserves a proper room — dark stage, typographic respect, diagrams that breathe beyond Obsidian's width. Skip it otherwise. A viewer without a reason is ornament.

When invoked, four rules govern.

**1 · Output location** — all viewers collect in a `viewer/` folder at the **workspace parent level**. Not inside the OCR workspace, not under `analysis/`. The viewer is a final surface; it lives where surfaces live.

```
<workspace-parent>/viewer/{YYYY-MM-DD}-{stance}--{author}-{title}.html
```

**2 · Filename** — four slots, double-dash between metadata and identity:

```
{YYYY-MM-DD}-{一句话态度立场}--{作者}-{论文名字}.html
```

- `YYYY-MM-DD` — rendering date
- `一句话态度立场` — the reader's stance distilled to one phrase (Chinese preferred; typically 5–10 chars). This is your reading condensed, not a summary of the paper.
- `作者` — the paper's author
- `论文名字` — the paper's title; **you have naming authority here**. If the title is long (e.g. `面对多元价值冲突的困境：伯林论题的再考察`), abbreviate (`面对多元价值冲突的困境`). The full title lives inside the hero Chinese line. The HTML is an independent piece of writing — naming it is part of that writing.

Example: `2026-04-20-未证之环即真起点--刘擎-面对多元价值冲突的困境.html`

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

**4 · The rest is attribution-theme** — refer to the attribution-theme CSS tokens and scene vocabulary (`#08080A` ink-stone ground, `#F0EDE6` signal, Eclipse / Observatory / Star Chart scenes, one Signal per viewport). Do not invent a second visual language. The viewer is a translation of the Markdown into a different room; the room's rules are already written.

---

At the foot of the file, a single line:

```
{{model_name}} for {{user_name}} · X-ray · {YYYY-MM-DD}
```

No further flourish.

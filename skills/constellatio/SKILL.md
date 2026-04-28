---
name: constellatio
description: Use when a historical phenomenon has irreconcilable era-readings; the lens diagnoses what each reading needs from the past and identifies the structural property of the object that makes it absorptive across time.
argument-hint: "[phenomenon | workspace-or-markdown-path]"
allowed-tools: Read, WebSearch, Write
---

# constellatio

## The work this lens is for

There are historical things you keep returning to and never quite resolve.

李鸿章 sits between three biographies that cannot all be true at once. 王安石
变法 oscillates across a thousand years of judgment, sliding between salvation
and catastrophe whenever the present needs the past to answer differently.
陈寅恪 fascinates without quite letting you say why. 曹操 from 正史 / 演义 /
翻案 is three different men. 鸦片战争 reads as 民族屈辱 from one side and
现代化起点 from the other, and you cannot quite stop believing both.

`constellatio` is the lens for those phenomena. It does not pick a winning
reading. It does two specific intellectual moves:

1. it diagnoses what each era's reading **needs from the past** in order to
   underwrite that era's own present
2. it identifies the **structural property of the object** that lets every era
   project onto it without resistance — the reason no era can settle it

It is the lateral cousin of `real-thesis`. `real-thesis` digs vertically into
one paper's buried claim. `constellatio` works laterally across many readings
of one phenomenon to surface what the readings reveal about their own readers
and what the object itself is doing that lets them all stick.

## Four cognitive moves

These are angles of attention. Hold them; do not run them as a recipe.

**锁定不可压缩面.** What in the phenomenon cannot be removed from any honest
account, regardless of who is reading. These are the items every reading must
carry. They are not "the truth" of the phenomenon — they are its irreducible
furniture. Without this floor, the rest of the lens has nothing to push
against.

**读法即诊断.** Each era-reading is a symptom of the era that produced it. Ask
not "is this reading correct" but "what did this era need to find here". A
reading is evidence about its reader before it is evidence about its subject.
What a reading must emphasize, what it must avert its eyes from, what
assumption it must protect — these are the era's pressures showing through.

**追踪变迁追踪的是什么.** When the readings change across centuries, ask
honestly what the variation tracks. It almost never tracks new findings about
the phenomenon itself. Usually it tracks the reading communities' own shifting
crises of legitimacy — what they need history to confirm in order to live with
their own present. Naming this clearly is the central decoding move of the
lens.

**辨识屏幕属性.** The deepest move. A phenomenon that absorbs every era's
projection without resisting must contain some structural ambiguity that
allows the projection to land. The object is, in this sense, a *screen*.
Identify the property that makes it so — usually an internal contradiction
that genuinely exists inside the object (启蒙 + 救亡 同时在场;
开明改革 + 帝国困局 同时在场). This screen-property is not the era's
construction; it is what the era is reaching for. Without naming it, the lens
collapses into mere reception history.

## Input

Target: `$ARGUMENTS`

- a phenomenon name (`李鸿章`, `王安石变法`, `鸦片战争`) → constellate from
  public material
- a workspace directory → read `<ws>/final.md` and treat it as one of the
  readings to be diagnosed against others
- a `.md` file → same as workspace mode
- empty → ask which phenomenon, and which readings the user already cannot
  let go of

If readings are not yet identified, surface 3–5 mutually incompatible ones
before continuing. Fewer than three usually means the phenomenon does not
yet warrant this lens. More than seven usually means the field is being
padded.

## Method

Five passes. Not steps; angles.

1. **Lock the irreducible.** State plainly what cannot be removed from any
   honest account of the phenomenon — the events, persons, decisions, texts,
   actions every reading must include. Do not interpret yet.
2. **Read each reading as its era's diagnostic act.** For each rival reading,
   name the era it speaks from, what that era was wrestling with on its own
   terms, and what this reading therefore needed the phenomenon to be. Do not
   evaluate the reading's accuracy yet. Diagnose its function.
3. **Locate the screen-property.** Identify the structural ambiguity inside
   the phenomenon itself that lets every era project onto it. Phrase it
   substantively: which two things does the object genuinely contain at once
   such that any era can foreground whichever one fits its own pressure.
4. **Name what the variation tracks.** Across the readings, the variation is
   tracking *something*. Almost never the phenomenon. Usually the readers'
   shifting relationship to their own legitimacy crisis. State it directly.
5. **Write the honest one-sentence shape.** If the lens has produced an
   honest finding, it can be stated in one sentence: the phenomenon is X
   because it contains Y, which lets each era make it carry Z. If it cannot
   honestly be reduced, say so. "Cannot reduce" is sometimes the correct
   conclusion.

## Output

- workspace mode → `<workspace>/analysis/{stem}_constellatio.md`
- single-file mode → `analysis/{stem}_constellatio.md`
- pure phenomenon mode → ask for a target directory if none is obvious

The deliverable is **prose**. Six sections:

1. **Phenomenon** — the name at the centre, no embellishment
2. **不可压缩面** — what every reading must include
3. **每代的读法即诊断** — for each era-reading: what that era needed the
   phenomenon to be, and why
4. **变迁追踪的是什么** — the diagnosis of what the across-time variation
   actually tracks
5. **屏幕属性** — the structural property of the phenomenon that makes it
   absorptive
6. **当下读法的诚实** — the synthesis the present is reaching for, named
   honestly as itself another era-reading rather than the verdict

## Optional · sibling visualization

When a phenomenon's readings are visually comparable — same items, different
selections of which to emphasize, which to dim, which to omit — a chart
sibling can stand alongside the prose. The chart is *never* the analysis; it
displays the readings so the eye can compare what the prose has already
diagnosed.

If you choose to deliver a chart, see `references/visual-handoff.md`. The
chart and the prose are equal-rank deliverables. Prose alone is a complete
output.

`references/example-may-fourth.md` is the canonical worked example of the
prose deliverable. `references/example-may-fourth.html` is the same case as
chart sibling. Read both to feel the relationship between them.

## Honesty

- If only two readings exist and they merely contradict, this is not yet a
  case for this lens. Do not pretend otherwise.
- If the screen-property cannot be honestly named, say so. Do not invent a
  contradiction the object does not actually contain.
- A reading not yet formulated by anyone is not a reading. Do not invent
  positions to round out the field.
- "Cannot resolve" is sometimes the honest conclusion. Do not collapse a
  legitimate aporia into a tidy synthesis.
- The current era reaches for its own synthesis as readily as past eras did.
  Name the synthesis when you reach it, do not enthrone it.

## Vocabulary discipline

Inside the prose deliverable, every chart-side noun (Polaris, fixed star,
gravity well, constellation, Stellae fixae, Terra Incognita) must be
replaceable by the substantive concept it stands for without loss of meaning.
If you cannot replace it without loss, the sentence has not yet been written
— the chart vocabulary was carrying meaning the prose has not yet earned.

Chart-side labels in the optional HTML sibling are exempt from this rule.
There the labels stand on top of figures that literally show the thing.

## Guardrails

- Never overwrite the source.
- The screen-property is what the readings reveal about the object, not what
  the operator imposes on it.
- Do not steal the centre by writing a new reading and calling it the truth.
- One phenomenon per invocation. The lens is precise; do not blur it.

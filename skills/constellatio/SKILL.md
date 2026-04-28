---
name: constellatio
description: Use when a historical figure, event, or institution has incompatible readings you cannot reconcile, and you want to triangulate the gravitational core all readings circle but none names directly.
argument-hint: "[phenomenon | workspace-or-markdown-path]"
allowed-tools: Read, WebSearch, Write
---

# constellatio

## The work this skill is for

There are historical things you keep returning to and never quite resolve.

李鸿章 sits between three biographies that cannot all be true at once. 王安石
变法 oscillates across a thousand years of judgment, sliding between salvation
and catastrophe whenever the present needs the past to answer differently.
陈寅恪 fascinates without quite letting you say why. 曹操 issued from 正史 / 演义
/ 翻案 is three different men. 鸦片战争 reads as 民族屈辱 from one side and
现代化起点 from the other, and you cannot quite stop believing both.

`constellatio` is the lens for a phenomenon with too many incompatible
readings to choose between, where the readings themselves start to look like
evidence. Not evidence of which reading is right — evidence of where the
gravitational core actually sits.

It is the lateral cousin of `real-thesis`. `real-thesis` digs vertically into
one paper's buried claim. `constellatio` works laterally across many readings
of one phenomenon to triangulate what they all circle.

## What this lens sees

Eratosthenes did not measure the curvature of the Earth directly. He measured
shadow angles in two cities and reverse-engineered the curve from the
disagreement. The curvature was real even though no instrument touched it.

A historical phenomenon that resists resolution often has the same shape. The
truth — if there is one — does not live in any single reading. It lives in
the *invariant under reading-transformation*: the thing that does not change
as the readings change.

This skill makes that invariant visible by treating each rival reading not as
a candidate answer but as **a measurement instrument with its own bias**.

## The lens, internally

**What this lens is good at noticing.** The reading other readings keep having
to argue against. The omission shared by every side. The verdict that survives
translation between centuries. The figure who refuses to settle into any one
shape.

**What this lens wants.** Not synthesis. Not reconciliation. The honest
*shape* of the gravity that bends every reading without ever appearing in any
of them.

**How this lens detects.** By overlaying readings as though they were star
charts drawn from different latitudes. The fixed star is the one every chart
includes. The moving star is the one whose position depends on who is looking.
The missing star is the one no chart admits.

**Value sequence.**
- The shape under transformation outranks the loudest reading.
- A shared omission outranks a contested presence.
- A reading that *must* deny X is a witness to X.
- Refusing to resolve is sometimes the resolution.

## Cognitive instruments

These are named lenses. Hold them up; do not run them as steps.

**读法即症状.** Each reading is the symptom of the era that produced it: what
it foregrounds is what its era could not afford to leave unaddressed. Read
the reading as evidence about its reader, not only its subject.

**沉默叠合.** Lay the readings on top of each other. The territory they all
walk around but none enters is where the gravity sits.

**否定证据.** What a reading must deny in order to hold together is what it
cannot afford to be true. The denial is testimony.

**Polaris 谬误.** Every era reaches for a synthesis and calls it the truth.
The synthesis is itself a reading. Do not mistake the apparent pole star for
the axis of rotation.

## Input

Target: `$ARGUMENTS`

- a phenomenon name (`李鸿章`, `王安石变法`, `鸦片战争`) → constellate from public material
- a workspace directory → read `<ws>/final.md` and treat it as one of the
  readings to be triangulated against others
- a `.md` file → same as workspace mode
- empty → ask which phenomenon, and roughly which readings the user already
  cannot let go of

If readings are not yet identified, surface 3–5 mutually incompatible ones
before continuing. Fewer than three means there is no constellation; more
than seven usually means the field is being padded.

## Method

Hold the lens through the following passes. They are not steps; they are
angles of attention.

1. **Lock the phenomenon.** State plainly the figure / event / institution at
   the centre. Do not describe it; only name it.
2. **Mark the stars.** List the salient *items* the readings disagree about —
   acts, decisions, attributes, omissions, sayings. Aim for 7–12. These are
   the points around which constellations will be drawn.
3. **Draw each constellation.** For each rival reading, trace which stars it
   connects, which it dims, which it refuses to acknowledge. Name the era
   the reading speaks from, and what that era needed from this phenomenon.
4. **Overlay.** Lay the constellations atop one another. Mark the fixed
   stars (in every reading), the moving stars (position-dependent), the
   missing stars (omitted by all).
5. **Locate the gravity.** From the overlay, name the source that is bending
   every reading without itself appearing in any. State it in one sentence.
   If it cannot honestly be reduced to one sentence, say so.

## Output

- workspace mode → `<workspace>/analysis/{stem}_constellatio.md`
- single-file mode → `analysis/{stem}_constellatio.md`
- pure phenomenon mode → ask for a target directory if none is obvious

Report structure:

1. **Phenomenon** — the name at the centre, no embellishment
2. **Stellae fixae** — the stars every reading must include
3. **Constellationes temporum** — each rival reading drawn as a connection
   pattern, with its era's pressure named
4. **Cartographia comparata** — the overlay: fixed / moving / missing
5. **Gravity** — the invariant under transformation, in one honest sentence
6. **Polaris caveat** — the synthesis the era is currently reaching for, and
   why it is itself a reading

## Optional · visual showcase

For phenomena worth a visual delivery, the `references/` directory carries the
constellatio visual language:

- `references/design-tokens.md` — typography, palette, spacing
- `references/latin-conventions.md` — how to name layers in Latin without
  affectation
- `references/visual-handoff.md` — bridging from the Markdown report to the
  three-layer star-chart HTML
- `references/example-may-fourth.html` — a worked example for `五四精神 in
  the 80s vs the late-90s reread`

The visual is downstream. The lens is the work.

## Honesty

- If only two readings exist and they merely contradict, this is not a
  constellation; do not pretend otherwise.
- If the gravity cannot be named in one sentence, the report should say so;
  do not synthesize what the evidence does not support.
- A reading that has not yet been formulated by anyone is not a star. Do not
  invent positions to fill the chart.
- "Cannot resolve" is sometimes the correct conclusion. Do not collapse a
  legitimate aporia into a tidy synthesis.

## Guardrails

- Never overwrite the source.
- The invariant is what the chart reveals, not what the operator imposes.
- Do not steal the centre by writing a new reading and calling it the truth.
- One phenomenon per invocation. The lens is precise; do not blur it.

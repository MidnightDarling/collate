# constellatio · visual handoff

This document is the bridge between the prose deliverable
(`<workspace>/analysis/{stem}_constellatio.md`) and its sibling visual
representation (`<workspace>/analysis/{stem}_constellatio.html`).

The chart and the prose are **siblings**, not parent-and-child. The prose
carries the lens's analytical work — diagnosis of each era's reading,
identification of the screen-property, naming what the variation tracks.
The chart shows the readings as visual constellations so the eye can
compare what the prose has already analyzed. Visualization is optional
and never required.

## When a chart adds something the prose cannot

Deliver a chart sibling when:

- The phenomenon has 3+ rival readings whose disagreement is visually
  comparable: same items, different selections of which to emphasize, dim,
  or omit.
- The visual layering itself reveals something — three eras' selections
  overlaid show patterns of shared silence or shared emphasis that prose
  has to circle around to describe.
- The reader has time to sit with the chart. A constellation does not work
  as a thumbnail or slide-deck embed.

Skip the chart when:

- Only two readings exist and they merely contradict (the prose alone is
  the work; there is no third reading for the eye to triangulate).
- The lens's finding is "cannot reduce" — a chart of an aporia just looks
  tidy and lies for you.
- The chart would lend false definiteness to a hypothesis the prose
  rightly hedges.

The prose alone is a complete deliverable. The chart on its own is not.

## The three figures

The chart has three figures. They display, they do not analyze. The
canonical worked example is `references/example-may-fourth.html`; its
prose sibling is `references/example-may-fourth.md`.

| Figure | Purpose |
|--------|---------|
| **FIG I — single chart** | Plot the items every reading must include. One field, all marks at full luminosity. The substrate. |
| **FIG II — duo (or n-tuple) panes** | One pane per rival reading; same coordinates, different connections, different brightness. Warm gold for affirmation panes, cool silver for critique panes. |
| **FIG III — overlay** | All connection lines faintly atop one another; marks dimmed; the cross-era recurring concerns drawn as the only filled halos on the page. |

Below FIG III sits a small grid of caption articles, one per recurring
concern surfaced by the overlay. These captions are chart legend, not
prose analysis — they describe what the figure shows.

| Prose section | HTML region |
|---------------|-------------|
| Phenomenon | `<header class="hero">` |
| 不可压缩面 | `<section class="chart-wrap">` (FIG I) |
| 每代的读法即诊断 | `<section class="duo-wrap">` (FIG II) |
| 屏幕属性 / 变迁追踪的是什么 | `<section class="overlay-wrap">` (FIG III) + `.grav-grid` captions below |

The chart side does not have a region for the *diagnostic* prose moves
(reading-as-symptom, screen-property, what-variation-tracks). Those moves
live exclusively in the prose sibling, where they belong.

## How many cross-era halos to render

A constellatio chart usually surfaces **2–3 named recurring concerns**, not
a single plumb mark. A rich phenomenon's recurrences are rarely one thing.
For May Fourth: *Janus* (two-faced structure) + *Angustia Occidentis*
(the perennial East-West anxiety) + *Necessitas Praesentis* (each era's
reach for the past as legitimacy for its present). Each is honest as a
separate halo; collapsing them into one would lie.

If the prose genuinely surfaces only one recurring concern, render one
halo. Never invent a second to balance the composition.

## Implementation notes

- **SVG for marks, lines, halos.** HTML/CSS for narration and section
  headers. No D3, no Canvas, no chart library — the chart is small enough
  to be hand-laid, and hand-laying enforces editorial care about every
  mark's position.
- **Coordinates are fixed across the document.** A given mark is at the
  same `(x, y)` in FIG I, FIG II, and FIG III. That consistency is what
  makes the three-figure progression legible. If you reposition a mark to
  "make this layer look better", you have broken the chart.
- **Gradient defs reuse.** Define `<radialGradient>` for `star-warm`,
  `cool-star`, `dim-star`, `dim-star-c`, `nebula`, `grav-glow`,
  `revocatio-glow` once per figure. The naming convention preserves
  semantic meaning across charts.
- **Connection lines.** 0.5–1.4px strokes. Solid for the warm gold set,
  dashed (`stroke-dasharray="2 4"` or `"2 5"`) for the cool silver set.
  Pattern + color together carry the signal — never color alone.
- **Each pane's omitted zone.** Each pane in FIG II should mark the zone
  the era refuses to engage. Diagonal-stripe `<pattern>` overlay at low
  opacity, captioned in Cinzel UPPER 11px in the era's tinted-soft variant.
- **Layer transitions.** A 60–84px vertical gap between figures is enough.
  Do not over-animate. This is a chart of judgment, not a hero section.

## From prose to chart — workflow

1. **Start from the canonical example.** `cp skills/constellatio/
   references/example-may-fourth.html <new-location>.html` is the safest
   starting point. The HTML scaffolding, SVG defs, and CSS already encode
   every discipline this document specifies.
2. **Replace the phenomenon name** in `<header class="hero">` (`.title`,
   `.subtitle`, `.coords-prose`, `.stats`).
3. **Mark the irreducible items** in FIG I. Position by what they are, not
   by what they say. Aim for 7–12 marks. Keep coordinates sensible so the
   eye can group related items naturally.
4. **Replace each pane** in FIG II. One pane per reading. Set the
   appropriate `.warm` or `.cool` class. Update the era label, the
   connection set, and the omitted-zone caption per pane. Each pane's
   `.pane-stance` is single-sentence chart caption — never a paragraph
   of analysis. Analysis lives in the prose sibling.
5. **Render FIG III overlay** with the recurring-concern halos identified
   in the prose. Use the readings' actual marks as faint background;
   place each halo at the center of mass of the cluster of marks whose
   recurrence it captures.
6. **Replace the `.grav-grid` captions** below FIG III with one
   `<article>` per recurring concern. Roman numeral, Latin name, Chinese
   gloss, one short caption sentence. These are chart legend, not prose
   analysis — keep them short.
7. **Test.** Render at 1280px (laptop) and 768px (tablet). The chart
   should be legible at both. The `@media (max-width: 980px)` block
   collapses the duo and the grav-grid to single columns.

## What the chart is and is not

- **Not a poster.** The chart is a quiet instrument, not a campaign image.
  It does not need a tagline. It does not need decoration.
- **Not a substitute for the prose.** The prose sibling carries the lens's
  diagnostic work. The chart is delivered with the prose, never instead
  of it. The chart shows readings as constellations; the thinking lives
  in the prose.
- **Not the lens applied.** Applying the lens is a thinking act, performed
  in the prose. The chart is a visualization of the readings the prose
  has already diagnosed. If you find yourself "applying the lens" inside
  the chart's caption space, you have leaked thinking work into label
  space — push it back to the prose.

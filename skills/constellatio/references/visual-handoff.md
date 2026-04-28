# constellatio · visual handoff

This is the bridge from the Markdown report to the three-figure star-chart
HTML. It is for use when a constellation merits a visual delivery — typically
because the gravity is genuinely structural, and the chart will say something
the prose cannot.

## When to deliver visually

Deliver visually when:

- The phenomenon has 3+ rival readings worth charting (or 2 rival readings
  whose disagreement is patterned enough to triangulate gravity).
- The gravity is structural (an absent third position, a shared denial,
  an axis of rotation under transformation) rather than rhetorical (which
  side is louder, which side has more recent backing).
- The reader has time to sit with the chart. A constellation does not
  work as a thumbnail or a slide-deck embed.

Do not deliver visually when:

- Only two readings exist and they merely contradict (no constellation
  exists; the prose report is the work).
- The report's core finding is "cannot resolve" without further structure.
  A chart of an aporia just looks tidy and lies for you.
- The visual would lend false definiteness to a hypothesis the prose
  rightly hedges.

## The three figures

The Markdown report's sections map to three figures, in order. The
canonical worked example is `references/example-may-fourth.html`.

| Markdown section | Figure | Purpose |
|------------------|--------|---------|
| `Stellae fixae` | **FIG I — single chart** | Plot the stars every reading must include. One field, all stars at full luminosity. The substrate. |
| `Constellationes temporum` | **FIG II — duo (or n-tuple) panes** | One pane per rival reading; same star coordinates, different connections, different brightness. Warm gold for affirmation panes, cool silver for critique panes. |
| `Cartographia comparata` | **FIG III — overlay** | All constellation lines faintly atop one another; stars dimmed; gravity wells (named, plural) drawn as the only filled halos on the page. |

Below the three figures sits a **Reading section** (the five-step prose
unfolding), and below that the **Polaris caveat** band — a closing prose
band that warns against treating the *current* era's reach for synthesis
as an answer.

| Markdown section | HTML element |
|------------------|--------------|
| `Phenomenon` | `<header class="hero">` |
| `Stellae fixae` | `<section class="chart-wrap">` (FIG I) |
| `Constellationes temporum` | `<section class="duo-wrap">` (FIG II) |
| `Cartographia comparata` | `<section class="overlay-wrap">` (FIG III) |
| `Gravity` | gravity-well halos in FIG III + `.grav-grid` articles below |
| `Polaris caveat` | `<section class="caveat-band">` |

## The plurality of gravity

A constellatio chart usually surfaces **2–3 named gravity wells**, not a
single plumb mark. A rich phenomenon's invariance is rarely one thing.
For May Fourth: *Janus* (the two-faced structure) + *Angustia Occidentis*
(the perennial East-West anxiety) + *Necessitas Praesentis* (the present's
need to anchor itself in the past). Each is honest as a separate gravity
source; collapsing them into one would lie.

If the analysis genuinely surfaces only one gravity, render one well.
Never invent a second to balance the composition. Asymmetry is honest.

## Implementation notes

- **SVG for stars, lines, gravity wells.** HTML/CSS for narration and
  section headers. No D3, no Canvas, no chart library — the chart is
  small enough to be hand-laid, and hand-laying enforces editorial care
  about every star's position.
- **Star coordinates are fixed across the document.** A given star is at
  the same `(x, y)` in FIG I, FIG II, and FIG III. That consistency is
  what makes the three-figure progression legible. If you reposition a
  star to "make this layer look better", you have broken the chart.
- **Gradient defs reuse.** Define `<radialGradient>` for `star-warm`,
  `cool-star`, `dim-star`, `dim-star-c`, `nebula`, `grav-glow`,
  `revocatio-glow` once per figure. The naming convention preserves
  semantic meaning across charts.
- **Connection lines.** 0.5–1.4px strokes. Solid for the warm gold set,
  dashed (`stroke-dasharray="2 4"` or `"2 5"`) for the cool silver set.
  Pattern + color together carry the signal — never color alone.
- **Terra Incognita.** Each pane in FIG II should mark the zone its era
  refuses to chart. Diagonal-stripe `<pattern>` overlay at low opacity,
  captioned in Cinzel UPPER 11px in the era's tinted-soft variant.
- **Layer transitions.** A 60–84px vertical gap between figures is enough.
  Do not over-animate. This is a chart of judgment, not a hero section.

## From Markdown to HTML — workflow

1. **Copy the canonical example.** `cp skills/constellatio/references/
   example-may-fourth.html <new-location>.html` is the safest starting
   point. The HTML scaffolding, SVG defs, and CSS already encode every
   discipline this document specifies.
2. **Replace the phenomenon name** in `<header class="hero">` (`.title`,
   `.subtitle`, `.coords-prose`, `.stats`).
3. **Re-mark the stars** in FIG I. Position by *what they are*, not
   *what they say*. Aim for 7–12 fixed stars. Keep coordinates sensible
   so the eye can group related stars naturally.
4. **Replace each pane** in FIG II. One pane per reading. Set the
   appropriate `.warm` or `.cool` class. Update Polaris Aetatis,
   Constellatio narration, and Terra Incognita per pane.
5. **Update FIG III overlay** with the inferred gravity wells. Use the
   reading's actual stars as faint background; place each gravity well
   at the center of mass of the cluster of stars whose pull it captures.
6. **Replace the .grav-grid** articles below FIG III with one `<article>`
   per gravity well. Roman numeral, Latin name, Chinese gloss, prose.
7. **Rewrite the Reading section** as the five-step methodology applied
   to the current phenomenon. Keep the discipline: the five steps are
   non-negotiable; the content varies.
8. **Rewrite the Polaris caveat band.** Identify the *current era's*
   reach for synthesis on this phenomenon. Name it. Show that it is
   itself a Constellatio Aetatis, not a verdict.
9. **Test.** Render at 1280px (laptop) and 768px (tablet). The chart
   should be legible at both. The `@media (max-width: 980px)` block
   collapses the duo, the grav-grid, and the reading-grid to single
   columns.

## What the visual is not

- **Not a poster.** The chart is a quiet instrument, not a campaign
  image. It does not need a tagline. It does not need decoration.
- **Not a substitute for the Markdown report.** The prose carries
  nuance the chart cannot. The visual is delivered *with* the report,
  never instead of it.
- **Not a final answer.** Like the lens itself, the chart shows the
  *shape* of the gravity, not the resolution of the dispute. The
  Polaris caveat band exists to enforce this — it is the chart's way
  of refusing to become an oracle.

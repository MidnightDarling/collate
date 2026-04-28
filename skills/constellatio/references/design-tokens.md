# constellatio · design tokens

These tokens define the visual register of the skill's optional showcase
output. They are downstream — the lens is the work, the visual is downstream
— but when a constellation merits a visual delivery, these are the defaults,
and `references/example-may-fourth.html` is built on them.

## Aesthetic stance

Deep-sky, not book-page.

A constellation lives at night. The page is a sky, not a sheet of paper.
Stars sit on a near-black field. Connection lines are thin pale strokes;
gravity wells are warm gold haloes; reading-eras tint warm or cool. Cream
ink reads as starlight on dark ground rather than ink on paper.

This is intentional. The kaozheng / chunqiu / real-thesis skills work on
prose and use a paper register. constellatio works on *judgments laid
across time*, and the night-sky register encodes the lateral, archival,
multi-era shape of that work.

## Typographic stack

| Role | Family | Weights | Usage |
|------|--------|---------|-------|
| Hero | Cinzel | 400, 500, 600, 700 | All-caps Latin titles, layer names, gravity-well names |
| Body Latin/English | Bodoni Moda | 400, 500, 600, italic 400/500 | English narration, era labels, technical sub-labels |
| Body Chinese | Noto Serif SC | 300, 400, 500 | Chinese narration, primary reading text, star annotations |
| Mono / meta | IBM Plex Mono | 300, 400 | Coordinate labels, FIG sequence markers, footer |

Cinzel carries the engraved-into-stone register fixed stars and gravity
wells need. Bodoni Moda italic carries the encyclopedia-entry register —
neutral authority with a slight chill. Noto Serif SC holds Chinese
material at parity with Latin; Chinese must not subordinate to a smaller
"annotation" weight. IBM Plex Mono carries the survey / cartographic
register for meta lines.

```html
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700&family=Bodoni+Moda:ital,opsz,wght@0,6..96,400;0,6..96,500;0,6..96,600;1,6..96,400;1,6..96,500;1,6..96,600&family=IBM+Plex+Mono:wght@300;400&family=Noto+Serif+SC:wght@300;400;500&display=swap" rel="stylesheet">
```

## Palette

The palette encodes a single semantic axis: **affirmation ↔ critique**.
Era-readings that affirm the phenomenon (建国之父, 救亡先驱, 启蒙之光)
lean warm gold. Era-readings that critique (汉奸, 改革罪人, 文化保守)
lean cool silver. Fixed stars stay neutral cream. Gravity wells take a
warmer cream-gold halo because they are *invariant*, not era-bound.

```css
:root {
  /* sky ground */
  --bg-deep: #050812;
  --bg-mid:  #0A1228;
  --bg-glow: #1A2547;

  /* cream ink (starlight) */
  --ink-1: #F4EDE0;  /* primary text on dark sky */
  --ink-2: #C9C2B4;  /* body prose */
  --ink-3: #807A6E;  /* meta labels, captions */
  --ink-4: #4A4636;  /* dimmed / Terra Incognita */

  /* affirmation register (warm gold) */
  --gold:      #E8C685;
  --gold-soft: #C9A56A;

  /* critique register (cool silver) */
  --silver:      #B8C8E8;
  --silver-soft: #8FA3C9;

  /* line work */
  --line-1: rgba(244,237,224,0.06);  /* faint frame */
  --line-2: rgba(244,237,224,0.14);  /* primary frame */
}
```

No additional accent. The whole point is that warm and cool sit *on the
same chart* so the eye can register their disagreement.

## Spacing & rhythm

```css
:root {
  --letter-cinzel: 0.18em;   /* hero caps + layer titles */
  --letter-mono:   0.34em;   /* meta labels (FIG · I, etc.) */
  --letter-bodoni: 0.02em;
  --letter-noto:   0;
}
```

- Outer container: `max-width: 1480px; padding: 84px 6vw 60px;`
- Section spacing: `padding: 0 6vw 80px;` between major figures.
- Generous letter-spacing on Cinzel hero (0.05em) and on layer-name
  Cinzel (0.18em–0.22em). The chart breathes; never crowd the field.

## Star-chart geometry

A constellation is drawn on a coordinate field, not a free canvas.

- The phenomenon is represented as **point + label**, never decorated
  with iconography. A star is a soft radial gradient (`star-warm` or
  `cool-star`) plus a 2–3.4px solid cream core. Label sits 12px to the
  right (or left, anchor="end") with Bodoni Moda italic on top, Noto
  Serif SC below.
- Star coordinates are *fixed across the document*. A given star is at
  the same `(x, y)` in every figure. That consistency is what makes the
  three-figure progression legible.
- **Star brightness encodes era-attention**, not absolute importance.
  Bright (radius 11–14, opacity 0.7–0.85) = the era is connecting to
  this star. Dim (radius 6, opacity 0.6, fill `dim-star`) = the era is
  refusing to connect. Same coordinate, different luminosity.
- **Connection lines.** 0.5–1.4px strokes. Solid for warm gold sets.
  Dashed (`stroke-dasharray="2 4"` or `"2 5"`) for cool silver sets.
  Pattern + color together carry the signal; never color alone.
- **Terra Incognita** (zones each era refuses to chart) drawn as
  diagonal-stripe `<pattern>` overlays at 40–80% opacity, captioned with
  Cinzel UPPER 11px in `--silver-soft` or `--gold-soft`.
- **Gravity wells** are the only *filled radial halos* on any chart, and
  they appear only on the Cartographia Comparata layer. Each gravity
  well = three stacked radial gradients (outer 80–92px halo at 50%
  opacity, mid 44–46px at 85%, core 6px solid cream). Names set in
  Cinzel UPPER 20–22px above; Latin gloss + Chinese gloss below.

## Typographic hierarchy in chart context

| Element | Family | Size | Letter-spacing | Case |
|---------|--------|------|----------------|------|
| Phenomenon hero | Cinzel 500 | clamp(50px,8.4vw,116px) | 0.05em | UPPER (mixed-case glow accent) |
| Subtitle | Bodoni Moda italic 400 | clamp(20px,2.4vw,32px) | n/a | Sentence |
| Layer label (FIG · I etc.) | IBM Plex Mono 300 | 10px | 0.34em | UPPER |
| Layer name (Stellae Fixae) | Bodoni Moda italic 500 | 22px | 0.02em | Title |
| Pane name (Illuminatio) | Bodoni Moda italic 500 | 32px | 0.02em | Title |
| Pane meta (MCMLXXX) | IBM Plex Mono 300 | 10px | 0.34em | UPPER |
| Star Latin label | Bodoni Moda italic 500 | 11–15px | 0 | Title |
| Star Chinese label | Noto Serif SC 400 | 9–10px | 0 | n/a |
| Gravity-well name | Cinzel 500 | 20–22px | 0.22em | UPPER |
| Gravity-well Latin gloss | Bodoni Moda italic 500 | 11.5px | 0.02em | Sentence |
| Body prose Chinese | Noto Serif SC 400 | 13–14.5px | 0 | n/a |

The hierarchy reflects the visual reading order: layer-frame, then
era-frame, then individual marks.

## What this aesthetic is not

- Not an infographic. There is no "data viz" affordance — no axes, no
  legends, no tooltips. The reader is meant to *read* the chart, not
  hover over it.
- Not symmetric. Asymmetry is honest in the chart because the readings
  genuinely cluster off-center; do not pull marks toward the middle for
  visual balance.
- Not warm-toned. The ground is near-black (#050812) and the cream ink
  reads as starlight. Warm gold and cool silver appear *only* as
  semantic encoding, never as mood.
- Not animated. A constellation is a still image. Era-by-era layer
  toggling is acceptable for an interactive viewer; transitions and
  hover effects are not.
- Not minimalist. Three figures with full SVG line work, multiple named
  recurring-concern halos, and per-pane omitted-zone markers — the chart
  earns its space by being thoroughly drawn, not by withholding marks.

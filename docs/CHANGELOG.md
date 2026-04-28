# Changelog

## 2026-04-29

### Constellatio sibling architecture

The `constellatio` skill is decoupled into two equal-rank deliverables: a
prose analysis and an optional chart sibling. The previous version let
chart vocabulary (Polaris, fixed star, gravity well, constellation) leak
into the cognitive method itself, which downstream agents would read as a
prompt and reproduce as meta-narration of their own chart-construction
process. The lens now teaches one mode of attention; the chart shows what
the prose has already diagnosed.

#### Changed

- `skills/constellatio/SKILL.md` rewritten as a thinking lens whose
  vocabulary is intellectual-history substantive, not star-chart costume.
  Four cognitive moves named in substantive terms (锁定不可压缩面,
  读法即诊断, 追踪变迁追踪的是什么, 辨识屏幕属性).
- `skills/constellatio/references/example-may-fourth.html` slimmed to
  chart-only; the embedded five-step prose unfolding and Polaris caveat
  band are removed.
- `skills/constellatio/references/visual-handoff.md` repositioned: chart
  and prose are sibling deliverables, not parent-child. Workflow steps
  that instructed the chart to perform analysis are removed.
- `skills/constellatio/references/design-tokens.md` strips
  cognitive-method claims from the visual rationale.
- README captions describe what the skill does (diagnose, identify), not
  what the chart shows.

#### Added

- `skills/constellatio/references/example-may-fourth.md` — canonical
  prose deliverable for the May Fourth case, parallel to the chart
  sibling.
- 屏幕属性 (screen-property) — the structural-ambiguity move that
  separates this lens from generic 接受史 / comparative reading.

#### Notes

- Pre-decouple HTML preserved locally outside the repository (does not
  ship to users).
- This release does not touch the OCR pipeline or any other skill.

## 2026-04-20

### Interface convergence: skill-first surface

This release collapses the duplicated command/skill surface into a cleaner
shape: skills are now the canonical capability layer, while standalone
commands remain only where they genuinely orchestrate or inspect.

#### Added

- Four formal reading-layer skills promoted from command-only lenses:
  `skills/chunqiu/SKILL.md`
  `skills/kaozheng/SKILL.md`
  `skills/prometheus/SKILL.md`
  `skills/real-thesis/SKILL.md`

#### Changed

- `commands/` now keeps only two standalone command shims:
  `ocr.md` and `status.md`
- Pipeline-stage surfaces such as `setup`, `prep-scan`, `ocr-run`,
  `proofread`, `diff-review`, `to-docx`, `mp-format`, and
  `visual-preview` are now documented as direct skill surfaces rather than
  same-name command wrappers
- Reading lenses are now canonical skills rather than command-only prompts
- Repository docs now state the governing rule explicitly:
  if a command ever contains capability absent from the skill, that
  capability belongs back in the skill

#### Removed

- Same-name command wrappers for:
  `setup`, `prep-scan`, `visual-preview`, `ocr-run`, `proofread`,
  `diff-review`, `to-docx`, `mp-format`
- Command-only lens files for:
  `chunqiu`, `kaozheng`, `prometheus`, `real-thesis`

### Viewer upgrade: finished ATTRIBUTION showcases

This release upgrades the reading-layer HTML references from exposed scaffolds
into finished showcase surfaces.

#### Added

- A completed `xray-paper` showcase:
  `skills/xray-paper/references/viewer-showcase.html`
- A completed `paper-summary` showcase:
  `skills/paper-summary/references/viewer-showcase.html`
- A first public changelog for repository-visible release notes

#### Changed

- `xray-paper` and `paper-summary` now treat HTML output as a showcase-grade
  deliverable rather than a visible authoring template
- Viewer contracts now require a visual-first reading surface:
  readers should see argument structure, position, route, and tension before
  they finish the prose
- The x-ray showcase now preserves the orbital ATTRIBUTION hero while adding
  stronger structural diagrams
- The map showcase now reads as an observatory / field sketch rather than a
  mirrored x-ray page
- Viewer templates were simplified into internal scaffolds rather than
  pseudo-finished pages with fill-in language

#### Content

- The showcase content is now grounded in Liu Qing's essay
  `超越全球化与民族主义的对立`
- The reading voice is more explicit in judgement:
  strongest move, thinnest move, and reader response are stated directly

#### Quality bar

- No visible `{{slot}}` placeholder syntax in showcase HTML
- No fill-in-template language or author-facing binding notes in showcase HTML
- One finished HTML page should be directly openable by a human without further
  editing

#### Notes

- `viewer-template.html` remains available as an internal writing scaffold
- `viewer-showcase.html` is the standard that final HTML should resemble

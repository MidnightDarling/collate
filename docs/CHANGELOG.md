# Changelog

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

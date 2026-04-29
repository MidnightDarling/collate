# Changelog

## 2026-04-29 · Hermes agents native support

### Changed

- Hermes agents promoted from "未实现" to "原生支持" in INTEGRATIONS.md matrix, both READMEs, and compatibility tables.
- `docs/INTEGRATIONS.md` section 10 (Hermes agents): rewritten from architecture reference to verified integration — documents `AGENTS.md` auto-discovery, `delegate_task` subagent dispatch, and `.cursor/rules/*.mdc` co-loading.
- Compatibility matrix now lists five supported runtimes (was four): Claude Code, Codex, Gemini CLI, Cursor, Hermes agents.
- README description updated: "native siblings for Codex, Gemini CLI, Cursor, and Hermes agents" (was "Codex, Gemini CLI, and Cursor").

### Notes

- No new file created. Hermes auto-discovers the existing `AGENTS.md` at project root — that IS the native integration.
- Creating `.hermes.md` was deliberately avoided: Hermes loads only the first context file it finds (`.hermes.md` → `AGENTS.md` → `CLAUDE.md`), so a `.hermes.md` would replace `AGENTS.md` loading and create a maintenance fork.

---

## 2026-04-29 · Gemini CLI & Cursor native support

### Added

- `GEMINI.md` — project context file auto-loaded by Gemini CLI every session.
- `gemini-extension.json` — Gemini CLI extension manifest (`gemini extensions install`).
- `.cursor/rules/collate.mdc` — Cursor project rule (`alwaysApply: true`), auto-loaded on project open.
- `docs/INTEGRATIONS.md` section 6: full Gemini CLI wiring (install, env vars, subagent dispatch, context management).

### Changed

- Compatibility matrix: Gemini CLI and Cursor promoted from "Untested" to "Supported" in both READMEs and INTEGRATIONS.md.
- `docs/INTEGRATIONS.md` section 4 (Cursor): updated to reference shipped `.cursor/rules/collate.mdc` instead of manual `.cursorrules`.
- `docs/INTEGRATIONS.md`: removed old section 8 (outdated Gemini CLI roadmap); renumbered sections 7–14.
- README description updated: "native siblings for Codex, Gemini CLI, and Cursor" (was "only Claude Code and Codex verified").
- README tree updated to show `GEMINI.md`, `gemini-extension.json`, and `.cursor/rules/`.

---

## 2026-04-29 · v0.2.0

### Version bump & runtime honesty

#### Changed

- Version 0.1.0 → 0.2.0 across all plugin manifests
  (`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, `docs/ARCHITECTURE.md`,
  `docs/TROUBLESHOOTING.md`).
- Model identity corrected: "Claude Opus 4.7" → "Claude Opus 4.6"
  throughout the repository (README, CONTRIBUTORS, manifests, references,
  commands, INTEGRATIONS, ARCHITECTURE, TROUBLESHOOTING).
- Runtime compatibility claims made honest: only Claude Code and Codex CLI
  have native plugin manifests. Removed unimplemented runtimes (OpenCode,
  Hermes, OpenClaw, Kimi, MiniMax) from README compatibility matrix;
  Cursor and Gemini CLI marked as untested.
- INTEGRATIONS.md runtime matrix updated with explicit status column
  (原生支持 / 未测试 / 未实现 / 路线图 / 概念架构).
- Marketplace description stripped of unverified runtime claims.
- Skill counts updated: 14 → 15 skills, 6 → 7 reading skills
  (constellatio added to reading layer).

### Constellatio honest repositioning

The `constellatio` skill is repositioned as a reception-history analysis
format with one genuinely novel contribution (screen-property
identification), not a "thinking lens" with four claimed cognitive moves.
The previous SKILL.md overclaimed: the first two steps (list irreducible
facts, treat each era's reading as diagnostic) are standard reception
history, not novel methods. Only the third step — identifying the
structural crack inside the object that lets every era's projection
stick — is the skill's distinctive contribution.

Three reference files (`visual-handoff.md`, `design-tokens.md`,
`latin-conventions.md`) are merged into a single `viewer-spec.md`.

#### Changed

- `skills/constellatio/SKILL.md` rewritten with honest three-step
  framing. Steps 1-2 are explicitly marked as standard reception-history
  work; step 3 (屏幕属性) is the skill's only novel contribution.
  Description changed from "thinking lens" to "接受史分析".
- README captions changed from "diagnose" framing to "reception-history
  analysis" — honest about what the skill actually does.

#### Added

- `skills/constellatio/references/viewer-spec.md` — single reference
  merging aesthetic stance, design tokens, and Latin conventions.

#### Removed

- `skills/constellatio/references/visual-handoff.md` — merged into
  `viewer-spec.md`.
- `skills/constellatio/references/design-tokens.md` — merged into
  `viewer-spec.md`.
- `skills/constellatio/references/latin-conventions.md` — merged into
  `viewer-spec.md`.

### Constellatio sibling architecture

The `constellatio` skill is decoupled into two equal-rank deliverables: a
prose analysis and an optional chart sibling. The previous version let
chart vocabulary (Polaris, fixed star, gravity well, constellation) leak
into the cognitive method itself, which downstream agents would read as a
prompt and reproduce as meta-narration of their own chart-construction
process.

#### Changed

- `skills/constellatio/references/example-may-fourth.html` slimmed to
  chart-only; the embedded five-step prose unfolding and Polaris caveat
  band are removed.
- Chart and prose positioned as sibling deliverables, not parent-child.

#### Added

- `skills/constellatio/references/example-may-fourth.md` — canonical
  prose deliverable for the May Fourth case, parallel to the chart
  sibling.
- 屏幕属性 (screen-property) — the structural-ambiguity move that
  separates this skill from generic 接受史 / comparative reading.

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

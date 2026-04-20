---
name: prometheus
description: Use when a historical paper or final draft contains a concept, institution, or proper noun that needs a sharply defined public-facing gloss and an ATTRIBUTION-style SVG card.
argument-hint: "[concept | workspace-path | markdown-path]"
allowed-tools: Read, WebSearch, WebFetch, Write
---

# prometheus

## The work this skill is for

`prometheus` steals the fire of definition.

It takes one concept from a historical text and renders it into a compact,
public-facing card: genus, differentia, plain-language gloss, institutional
and temporal grounding, and one conceptual spark bright enough to hold in the
mind.

The card is not a poster full of effects. It is a definition made visible.

## Input

Target: `$ARGUMENTS`

- concept name (for example `三司`, `均田`, `经世`, `清议`) → define it directly
- workspace directory → read `<ws>/final.md`, extract 3–5 definition-worthy terms, ask which one to render
- `.md` file → same as workspace mode
- empty → ask for a concept or source file

## Definition recipe

For the chosen concept, derive:

1. **Genus and differentia** — what kind of thing it is, and what distinguishes it
2. **Plain gloss** — what it means in ordinary language
3. **Formal signature** — a minimal structured definition
4. **Essential distinction** — what nearby concepts it must not be confused with
5. **Temporal context** — dynasty, institution, or discourse that grounds it
6. **Philosophical core** — why the concept matters beyond the glossary level

## Rendering contract

Render in ATTRIBUTION-style achromatic discipline:

- one concept = one signal
- no chromatic colour
- title-led composition, quiet grid, wide margin
- body text should remain spare and legible

Output path:

- workspace mode → `<workspace>/analysis/prometheus/{concept}.svg`
- single-file mode → `analysis/prometheus/{concept}.svg`
- pure concept mode → ask for a target directory if none is obvious

If the file exists, ask before overwriting.

## Guardrails

- Do not steal five flames at once: render one concept per invocation.
- Do not turn the card into a miniature essay.
- The card should clarify, not merely decorate.

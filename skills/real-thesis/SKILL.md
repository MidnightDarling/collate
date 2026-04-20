---
name: real-thesis
description: Use when a historical paper appears to orbit a deeper claim than the one it states directly, and you need to excavate the thesis it repeatedly approaches but does not quite write.
argument-hint: "[workspace-or-markdown-path]"
allowed-tools: Read, Write
---

# real-thesis

## The work this skill is for

Many papers are written around a safer surface topic. The explicit claim is the
outer layer; the real pressure lives deeper in the structure — what returns,
what gets omitted, where the densest citations accumulate, where the conclusion
lands with disproportionate force.

This skill excavates that buried centre.

## What to look for

When the surface argument unfolds, pay attention to:

- where the author returns repeatedly
- what is `略而不论` or passed over in silence
- where the conclusion lands and what it cannot let go
- where citations grow abnormally dense
- where footnotes work harder than the body

The aim is not psychoanalysis for its own sake. The aim is to identify the
thesis that, if spoken plainly, might reorganize the abstract, the structure,
or even the title.

## Input

Target: `$ARGUMENTS`

- workspace directory → read `<ws>/final.md`
- `.md` file → read it directly
- empty → ask what to read

## Output

- workspace mode → `<workspace>/analysis/{stem}_real-thesis.md`
- single-file mode → `analysis/{stem}_real-thesis.md`

Report layers:

1. **Surface topic** — what the paper openly claims
2. **Floating concerns** — what it repeatedly approaches but does not settle
3. **Candidate real theses** — one to three, each anchored in evidence: returns, elisions, citations, footnotes
4. **A question the author dare not ask themselves** — left open, not answered for them

## Guardrails

- Never overwrite the source.
- Do not upgrade a mood into a thesis without evidence.
- If the paper is actually direct and nothing deeper is hiding, say so.
- Precision matters more than theatrical boldness.

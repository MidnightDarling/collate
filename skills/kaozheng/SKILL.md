---
name: kaozheng
description: Use when a historical paper or final draft needs evidential scrutiny: warrants, citations, source rank, truncation risk, or argument structure must be audited rather than stylistically interpreted.
argument-hint: "[workspace-or-markdown-path]"
allowed-tools: Read, WebSearch, Write
---

# kaozheng

## The work this skill is for

This is not typo-catching. That is `proofread`.

`kaozheng` reads in the Qian-Jia evidential tradition: not asking whether the
paper sounds plausible, but whether its **evidentiary bridge bears weight**.
The source may be real and the bridge still false. A citation may be accurate
and still be pressed into service beyond what it can support.

## What it audits

For a post-OCR, post-proofread paper, test:

- whether the claim is actually supported by the data cited
- whether quotations are complete enough to preserve original sense
- whether cited authorities are first-rank, second-rank, or hearsay
- whether the warrant is visible and defensible
- whether the paper leans on a solitary witness (`孤证不立`)

## Input

Target: `$ARGUMENTS`

- workspace directory → read `<ws>/final.md`
- `.md` file → read it directly
- empty → ask what to read

If only `raw.md` exists, note that the text has not yet been proofread and mark
the report accordingly.

## Method

Read the argument in layers:

1. Extract the paper's main claims.
2. Pair each claim with its offered evidence.
3. Identify the warrant that connects the two.
4. Audit quotations and citation framing:
   - what is quoted
   - what is omitted
   - what rank the source holds
   - whether a footnote quietly carries more force than the body text
5. Flag cardinal errors first; breadth comes second.

The framework is a scale, not a blade. Do not deform the paper merely to force
it into Toulmin language.

## Output

- workspace mode → `<workspace>/analysis/{stem}_kaozheng.md`
- single-file mode → `analysis/{stem}_kaozheng.md`

Report structure:

1. **Argument skeleton** — claim / data / warrant / backing / qualifier / rebuttal
2. **Citation audit table** — original fragment → suspected source → verifiable? → truncated?
3. **Cardinal errors** — one to three, ranked by severity, with repair suggestions
4. **Suspicious but unverified** — handed off for further checking

## Guardrails

- Never modify the source text.
- Do not confuse disagreement with disproof.
- One decisive structural error outweighs twenty decorative observations.
- If verification is impossible from available material, mark it as unverified rather than pretending certainty.

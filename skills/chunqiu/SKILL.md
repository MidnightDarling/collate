---
name: chunqiu
description: Use when reading a single historical paper or final draft and you need to surface taboo, judgment, rhetorical silence, repetition, or the contemporary reality the author approaches indirectly.
argument-hint: "[workspace-or-markdown-path]"
allowed-tools: Read, WebSearch, Write
---

# chunqiu

## The work this skill is for

The historian rarely says it directly. A title can be safe while a verb is not.
A citation can be dutiful while a silence is not. This skill reads for **judgment
embedded in diction**: the words chosen among near-synonyms, the repetitions that
betray unease, the omission that does not quite manage to disappear.

It does not proofread and it does not fact-check. It reads the paper as an
act of positioning.

## What it asks

Use this skill to answer four questions:

1. Which word choices carry verdicts?
2. Where does the prose pause, repeat, or refuse to land?
3. How is antiquity being used as a mirror for the present?
4. What one sentence does the author most want to say without writing?

## Input

Target: `$ARGUMENTS`

- workspace directory → read `<ws>/final.md`
- `.md` file → read it directly
- empty → ask what to read

## Method

Read for the following force lines:

- Where the prose pauses, the pen fears.
- What repeats must repeat for a reason.
- The harder something is scrubbed clean, the blacker the original stain.
- Seemingly unrelated digressions are often leakage.
- What follows `然而` / `虽然` / `however` / `granted` is often what the author actually thinks.
- Passive voice and omitted subjects often hide accountability.

Pay special attention to verdict-bearing distinctions:

- rank-marked death verbs (`卒` / `薨` / `崩`)
- punitive verbs (`诛` / `弑` / `戮`)
- adjectives that moralize without declaring themselves
- conspicuous absences where the argument ought to name someone or something directly

Do not flatten the reading into ideology-hunting. The task is not to accuse; it
is to hear the pressure in the prose.

## Output

- workspace mode → `<workspace>/analysis/{stem}_chunqiu.md`
- single-file mode → `analysis/{stem}_chunqiu.md`

Report structure:

1. **Diction verdicts** — key verbs and nouns, with the implied judgment they carry
2. **Repetition and pause** — recurring phrases, abrupt transitions, elisions
3. **Mirror of antiquity** — where historical material is borrowed to gesture at a present concern
4. **One unsaid sentence** — the line the paper circles but never writes

## Guardrails

- Never overwrite the source.
- Do not turn suggestive silence into false certainty.
- If the text is too flat to justify this reading, say so plainly.
- Negative space matters: the point is to preserve the shape of the unsaid, not to vandalize it.

# `.codex-plugin` for `collate`

This repository ships as a native Codex plugin.

## What it includes

- `skills/` from the repository root as the single source of truth
- repository-level `AGENTS.md` guidance for in-repo work
- a repo marketplace at `.agents/plugins/marketplace.json` so Codex can surface the plugin cleanly

## Why the plugin lives at repo root

`collate` is the package. There is no second copy under `plugins/collate/`.

That keeps:

- the public repository installable as-is
- skills and docs shared across Claude Code and Codex
- release metadata in one place instead of split across wrapper folders

## Install surface

For Codex plugin surfaces, use the repo marketplace in `.agents/plugins/marketplace.json`.
For direct repo work in Codex CLI, `AGENTS.md` still auto-loads when you run Codex from this repository.

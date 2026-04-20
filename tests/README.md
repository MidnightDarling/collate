# tests

Regression smoke tests locking the four bundle contracts from the 2026-04-20
publish-blocker fix (codex-gleaming-rossum).

Each test exercises exactly one contract. They are standalone Python scripts
with no dependencies beyond stdlib and the project's own `scripts/` modules.
Each prints `PASS <name>` on success or raises on failure.

## Contracts

| Test | Bundle | Contract locked |
|------|--------|-----------------|
| [smoke_truthful_status.py](smoke_truthful_status.py) | 1 | `workspace_readme.py` reflects `_pipeline_status.json`; refuses to display "完成 ✓" when status=error |
| [smoke_fallback_chain.py](smoke_fallback_chain.py) | 2 | `try_ocr` selects `text-layer` when `run-mineru` fails and `MINERU_API_KEY` is unset; records the full attempt log in status |
| [smoke_page_grounded.py](smoke_page_grounded.py) | 3 | `SKILL.md` / `AGENTS.md` require `page_images_dir` in the subagent payload; `make_preview.py` is declared audit-only, not canonical |
| [smoke_fidelity_gate.py](smoke_fidelity_gate.py) | 4 | Export refused (exit 11) when a text-layer workspace lacks `structure_approved` frontmatter; passes when both markers (`_structure_approved` + `proofread_method: "page-grounded"`) are present |

## Why these exist

Every test was written because Codex's 2026-04-20 audit found the contract
missing or silently broken. See
[docs/audit/20260420_pipeline_fidelity_audit_report.md](../docs/audit/20260420_pipeline_fidelity_audit_report.md)
for the original findings. Each test must fail on the pre-fix tree and pass
on the post-fix tree — that is the definition of "locked".

## Running

```bash
bash tests/run_all.sh         # run everything (exit code = failing count)
python3 tests/smoke_<x>.py    # run one
```

No pytest, no fixtures framework. Keeps the test harness visible to
anyone auditing the tree later.

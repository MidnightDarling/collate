# tests

Regression smoke tests locking the prerequisite guardrails from the
2026-04-20 publish-blocker fix (codex-gleaming-rossum).

Passing these tests is necessary, but it is not release evidence on its own.
Release still requires a fresh-agent real-PDF one-command pass through the
public user path: `/collate:ocr <pdf>`.

Each test exercises exactly one contract. They are standalone Python scripts
with no dependencies beyond stdlib and the project's own `scripts/` modules.
Each prints `PASS <name>` on success or raises on failure.

## Contracts

| Test | Bundle | Contract locked |
|------|--------|-----------------|
| [smoke_truthful_status.py](smoke_truthful_status.py) | 1 | `workspace_readme.py` reflects `_pipeline_status.json`; refuses to display "完成 ✓" when status=error |
| [smoke_fallback_chain.py](smoke_fallback_chain.py) | 2 | `try_ocr` selects `text-layer` when `run-mineru` fails and `MINERU_API_KEY` is unset; records the full attempt log in status |
| [smoke_page_grounded.py](smoke_page_grounded.py) | 3 | `SKILL.md` / `AGENTS.md` require `page_images_dir` in the subagent payload; `make_preview.py` is declared audit-only, not canonical |
| [smoke_fidelity_gate.py](smoke_fidelity_gate.py) | 4 | Export refused (exit 11) when a text-layer workspace lacks `structure_approved` attestation; passes when the review is mechanically page-grounded and `apply_review.py` emits `_structure_approved` |
| [smoke_real_user_contract.py](smoke_real_user_contract.py) | reset-task-2 | `build_page_review_packets.py` and `verify_page_grounded_review.py` make page-grounded proofread mechanically executable rather than doc-only |

## Why these exist

Every test was written because a 2026-04-20 delivery review found the
contract missing or silently broken. Each test must fail on the pre-fix tree
and pass on the post-fix tree — that is the definition of "locked".

## Running

```bash
bash tests/run_all.sh         # run everything (exit code = failing count)
python3 tests/smoke_<x>.py    # run one
```

No pytest, no fixtures framework. Keeps the test harness visible to
anyone auditing the tree later.

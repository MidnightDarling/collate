---
description: Verify Python deps, poppler, and OCR engine credentials
allowed-tools: Bash(python3:*), Bash(which:*), Read
---

Self-check the environment. Diagnose only — do not auto-`pip install` or `brew install`.

### 1. Python version

Run `python3 --version`. Requires >= 3.9.

### 2. Required Python packages

For each module, run `python3 -c "import <mod>"` and report pass/fail:

- `cv2` (opencv-python)
- `PIL` (pillow)
- `pdf2image`
- `requests`
- `dotenv` (python-dotenv)
- `markdown`
- `bs4` (beautifulsoup4)
- `PyPDF2`
- `docx` (python-docx)
- `opencc` (opencc-python-reimplemented)
- `mineru` (mineru[pipeline] — default local OCR engine)

### 3. System dependencies

`which pdftoppm` confirms poppler. If missing:

- macOS: `brew install poppler`
- Debian / Ubuntu: `apt install poppler-utils`

### 4. OCR engine credentials

Based on the current `OCR_ENGINE` environment variable (default `mineru`):

| `OCR_ENGINE` | Required keys |
|--------------|---------------|
| `mineru` (local CLI) | none |
| `mineru-cloud` | `MINERU_API_KEY` |
| `baidu` | `BAIDU_OCR_API_KEY` + `BAIDU_OCR_SECRET_KEY` |

Keys live in `~/.env`. Do not create project-level `.env` files.

### Report

List passes ✓, missing ✗, and exactly one fix suggestion per missing item. Do not apply fixes.

---
description: 检查 Python 依赖、poppler、OCR 引擎凭据
allowed-tools: Bash(python3:*), Bash(which:*), Read
---

对这个仓库做环境自检。不要擅自 `pip install` / `brew install`，只做诊断。

### 1. Python 版本

跑 `python3 --version`，需要 >= 3.9。

### 2. 必需 Python 包

挨个 `python3 -c "import <mod>"` 验证（缺哪个报哪个）：

- `cv2`（opencv-python）
- `PIL`（pillow）
- `pdf2image`
- `requests`
- `dotenv`（python-dotenv）
- `markdown`
- `bs4`（beautifulsoup4）
- `PyPDF2`
- `docx`（python-docx）
- `opencc`（opencc-python-reimplemented）
- `mineru`（mineru[pipeline]，本地 OCR 默认引擎）

### 3. 系统依赖

`which pdftoppm` 确认 poppler 到位。缺失时提示：

- macOS：`brew install poppler`
- Debian/Ubuntu：`apt install poppler-utils`

### 4. OCR 引擎凭据

按当前 `OCR_ENGINE` 环境变量判断（默认 `mineru`）：

| OCR_ENGINE | 需要的密钥 |
|------------|------------|
| `mineru`（本地 CLI） | 无 |
| `mineru-cloud` | `MINERU_API_KEY` |
| `baidu` | `BAIDU_OCR_API_KEY` + `BAIDU_OCR_SECRET_KEY` |

密钥统一走 `~/.env`，不要在项目里创建 `.env`。

### 汇报

列出：通过项 ✓、缺失项 ✗、每个缺失项的一条修复命令建议。不要直接执行修复。

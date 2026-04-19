---
description: Export final.md to WeChat MP HTML (inline CSS, OpenCC t2s, footnotes at end)
argument-hint: <workspace-path>
allowed-tools: Bash(python3:*), Read
---

Export the workspace's `final.md` to WeChat Official Account HTML plus a xiumi-compatible markdown sidecar.

Workspace: `$ARGUMENTS`

### Preflight

`<workspace>/final.md` must exist. If missing, stop — the WeChat version must be built from the audited `final.md`, never from `raw.md`.

### Execute

```
python3 skills/mp-format/scripts/md_to_wechat.py \
  --input <workspace>/final.md \
  --also-markdown
```

The script:

- Inlines all CSS into tag `style` attributes (WeChat strips external stylesheets).
- Applies OpenCC t2s (traditional → simplified) to body text, **but preserves the original form inside `> blockquote` sections** (citations are not converted).
- Collects footnotes at the end of the article.
- Generates byline and source bar.
- Emits a xiumi-compatible markdown sidecar for the xiumi editor.

### Report

- HTML absolute path: `<workspace>/output/<stem>_wechat.html`
- Markdown sidecar absolute path
- Footnote count
- Note: if styles break when pasted into WeChat admin, verify the user copied only `<body>` content.

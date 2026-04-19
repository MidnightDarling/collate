---
description: final.md → 微信公众号 HTML（内联 CSS、OpenCC t2s、脚注归尾）
argument-hint: <workspace-path>
allowed-tools: Bash(python3:*), Read
---

把工作区的 `final.md` 输出为公众号发文用的 HTML + xiumi 兼容 markdown sidecar。

工作区：`$ARGUMENTS`

### 前置检查

`<workspace>/final.md` 必须存在。缺了就停手——公众号版本必须走审计过的 final，不走 raw。

### 执行

```
python3 skills/mp-format/scripts/md_to_wechat.py \
  --input <workspace>/final.md \
  --also-markdown
```

脚本会：

- 把所有 CSS 内联进标签（公众号会剥离 `<style>`）
- 对正文做 OpenCC t2s 繁→简，但 **保留 `> blockquote` 内的原文形态**（引文不做转换）
- 脚注统一收束到文末
- 生成署名 / 来源栏
- 另写一份 xiumi 兼容 markdown（便于进秀米编辑器）

### 汇报

- HTML 绝对路径：`<workspace>/output/<stem>_wechat.html`
- Markdown sidecar 绝对路径
- 脚注数量
- 提示：若公众号后台粘贴后样式异常，先核实是否复制了 `<body>` 之外的内容

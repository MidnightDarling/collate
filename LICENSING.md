# Licensing Notes

This repository uses two licensing tracks:

- Code and mechanically parsed artefacts are licensed under the Apache License 2.0. See [LICENSE](LICENSE).
- Human-readable reference and editorial materials are licensed under Creative Commons Attribution 4.0 International (CC BY 4.0). Canonical legal code: <https://creativecommons.org/licenses/by/4.0/legalcode>. Human-readable deed: <https://creativecommons.org/licenses/by/4.0/>.

This file explains scope and attribution expectations. It does not replace the binding legal text of Apache-2.0 or CC BY 4.0.

## Scope Matrix

### Apache-2.0

Apache-2.0 applies to files that are imported, executed, or mechanically parsed, including:

- Source code under `skills/*/scripts/**`, `scripts/**`, and other executable paths
- Configuration files such as `*.json`, `*.yaml`, `*.yml`, and `plugin.json`
- `SKILL.md` files and shell snippets embedded in them
- Templates under `skills/*/assets/**` that are consumed by code

### CC BY 4.0

CC BY 4.0 applies to human-readable reference and editorial material, including:

- `docs/**`
- `skills/*/references/**`
- `README.md`, `README.zh.md`, `AGENTS.md`, and `CONTRIBUTORS.md`
- Authored artwork such as `assets/**/*.png` and `assets/**/*.jpg`
- Markdown prose elsewhere, except `SKILL.md`

## Ambiguity Rule

If a file is imported, executed, or mechanically parsed by code, treat it as Apache-2.0 unless the file itself states otherwise.

If a file is intended to be read by humans as reference material or editorial prose, treat it as CC BY 4.0 unless the file itself states otherwise.

File-level SPDX headers override these defaults.

## Attribution Guidance For CC BY 4.0 Material

When reusing reference material from this repository, please include attribution substantially equivalent to:

> "{title of the reused material}" from collate  
> copyright 2026 Alice and contributors,  
> licensed under CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>)  
> changes: {describe modifications, or "unchanged"}

For scholarly citation styles, adapt the format to the venue's rules.

## Not Covered By CC BY 4.0

The following are outside the CC BY 4.0 scope above and remain governed by their own terms:

- Source code and configuration covered by Apache-2.0
- Third-party dependencies invoked at runtime
- User-supplied input documents processed by this repository
- Outputs produced from user data, which belong to the user subject to any rights in the source material

## Contact

Questions about scope or attribution may be raised via [GitHub Issues](https://github.com/MidnightDarling/collate/issues).

#!/usr/bin/env bash
# collate — one-command installer
#
# What it does:
#   1. Clones (or updates) the repo at $COLLATE_HOME (default: ~/.local/share/collate)
#   2. Installs Python dependencies via `pip install --user -r requirements.txt`
#   3. Auto-detects installed agent runtimes and wires collate into each one
#   4. Prints per-runtime next-step instructions
#
# Usage (remote one-liner):
#   curl -fsSL https://raw.githubusercontent.com/MidnightDarling/collate/main/scripts/install.sh | bash
#
# Usage (with flags):
#   curl -fsSL https://raw.githubusercontent.com/MidnightDarling/collate/main/scripts/install.sh \
#     | bash -s -- --target ~/tools/collate --no-deps
#
# Usage (in-repo):
#   ./scripts/install.sh [--target PATH] [--no-deps] [--no-runtimes] [--help]
#
# Flags:
#   --target PATH     Install location (default: $HOME/.local/share/collate)
#   --no-deps         Skip `pip install`; assume deps are already present
#   --no-runtimes     Skip agent-runtime wiring; only clone + install deps
#   --dry-run         Print what would happen; make no changes
#   --help            Show this message and exit

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_URL="https://github.com/MidnightDarling/collate.git"
DEFAULT_TARGET="${HOME}/.local/share/collate"

# ANSI colors (fall back to no-op if NO_COLOR is set or stdout is not a tty)
if [[ -z "${NO_COLOR:-}" && -t 1 ]]; then
    C_RESET=$'\033[0m'
    C_BOLD=$'\033[1m'
    C_DIM=$'\033[2m'
    C_RED=$'\033[31m'
    C_GREEN=$'\033[32m'
    C_YELLOW=$'\033[33m'
    C_BLUE=$'\033[34m'
    C_CYAN=$'\033[36m'
else
    C_RESET=""; C_BOLD=""; C_DIM=""; C_RED=""; C_GREEN=""; C_YELLOW=""; C_BLUE=""; C_CYAN=""
fi

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
log_info()  { printf '%s[info]%s %s\n' "${C_BLUE}" "${C_RESET}" "$*"; }
log_ok()    { printf '%s[ ok ]%s %s\n' "${C_GREEN}" "${C_RESET}" "$*"; }
log_warn()  { printf '%s[warn]%s %s\n' "${C_YELLOW}" "${C_RESET}" "$*" >&2; }
log_error() { printf '%s[err ]%s %s\n' "${C_RED}" "${C_RESET}" "$*" >&2; }
log_step()  { printf '\n%s==>%s %s%s%s\n' "${C_CYAN}" "${C_RESET}" "${C_BOLD}" "$*" "${C_RESET}"; }
log_hint()  { printf '      %s%s%s\n' "${C_DIM}" "$*" "${C_RESET}"; }

die() { log_error "$*"; exit 1; }

# ---------------------------------------------------------------------------
# Arg parsing
# ---------------------------------------------------------------------------
TARGET="${COLLATE_HOME:-$DEFAULT_TARGET}"
INSTALL_DEPS=1
WIRE_RUNTIMES=1
DRY_RUN=0

show_help() {
    # Inlined so `curl ... | bash -s -- --help` works (stdin is already consumed).
    cat <<'HELP'
collate — one-command installer

What it does:
  1. Clones (or updates) the repo at $COLLATE_HOME (default: ~/.local/share/collate)
  2. Installs Python dependencies via `pip install --user -r requirements.txt`
  3. Auto-detects installed agent runtimes and wires collate into each one
  4. Prints per-runtime next-step instructions

Usage (remote one-liner):
  curl -fsSL https://raw.githubusercontent.com/MidnightDarling/collate/main/scripts/install.sh | bash

Usage (with flags):
  curl -fsSL https://raw.githubusercontent.com/MidnightDarling/collate/main/scripts/install.sh \
    | bash -s -- --target ~/tools/collate --no-deps

Usage (in-repo):
  ./scripts/install.sh [--target PATH] [--no-deps] [--no-runtimes] [--dry-run] [--help]

Flags:
  --target PATH     Install location (default: $HOME/.local/share/collate)
  --no-deps         Skip `pip install`; assume deps are already present
  --no-runtimes     Skip agent-runtime wiring; only clone + install deps
  --dry-run         Print what would happen; make no changes
  --help            Show this message and exit
HELP
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target)       TARGET="${2:-}"; shift 2 ;;
        --target=*)     TARGET="${1#*=}"; shift ;;
        --no-deps)      INSTALL_DEPS=0; shift ;;
        --no-runtimes)  WIRE_RUNTIMES=0; shift ;;
        --dry-run)      DRY_RUN=1; shift ;;
        -h|--help)      show_help; exit 0 ;;
        *) die "Unknown flag: $1 (use --help)" ;;
    esac
done

[[ -z "$TARGET" ]] && die "--target cannot be empty"

# Resolve to absolute path, preserving ~ expansion
TARGET="${TARGET/#\~/$HOME}"
case "$TARGET" in
    /*) ;;  # already absolute
    *)  TARGET="$PWD/$TARGET" ;;
esac

# ---------------------------------------------------------------------------
# Dry-run helper
# ---------------------------------------------------------------------------
run() {
    if [[ $DRY_RUN -eq 1 ]]; then
        printf '%s[dry]%s %s\n' "${C_DIM}" "${C_RESET}" "$*"
    else
        eval "$@"
    fi
}

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
cat <<EOF

${C_BOLD}点校 · collate${C_RESET}   one-command installer
${C_DIM}target:${C_RESET} ${TARGET}
${C_DIM}deps:${C_RESET}   $( [[ $INSTALL_DEPS -eq 1 ]] && echo "install via pip --user" || echo "SKIPPED (--no-deps)" )
${C_DIM}wire:${C_RESET}   $( [[ $WIRE_RUNTIMES -eq 1 ]] && echo "auto-detect agent runtimes" || echo "SKIPPED (--no-runtimes)" )
$( [[ $DRY_RUN -eq 1 ]] && echo "${C_YELLOW}[dry-run mode]${C_RESET}" )

EOF

# ---------------------------------------------------------------------------
# Step 1: preflight
# ---------------------------------------------------------------------------
log_step "Preflight checks"

command -v git >/dev/null 2>&1 \
    || die "git not found. Install git first: https://git-scm.com/downloads"
log_ok "git: $(git --version | head -1)"

if command -v python3 >/dev/null 2>&1; then
    PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
    if (( PY_MAJOR < 3 || (PY_MAJOR == 3 && PY_MINOR < 9) )); then
        die "python3 >= 3.9 required, found ${PY_VERSION}"
    fi
    log_ok "python3: ${PY_VERSION}"
else
    die "python3 not found. macOS: \`brew install python@3.11\`; Debian: \`apt install python3\`"
fi

if ! python3 -m pip --version >/dev/null 2>&1; then
    die "pip not available for python3. Install pip: \`python3 -m ensurepip --upgrade\`"
fi
log_ok "pip: $(python3 -m pip --version | head -1)"

# poppler (pdftoppm is the canonical binary from poppler-utils)
if command -v pdftoppm >/dev/null 2>&1; then
    log_ok "poppler: $(command -v pdftoppm)"
else
    log_warn "poppler (pdftoppm) not found."
    if [[ "$(uname -s)" == "Darwin" ]]; then
        log_hint "install with: brew install poppler"
    else
        log_hint "install with: sudo apt install poppler-utils  (or your distro's equivalent)"
    fi
fi

# ---------------------------------------------------------------------------
# Step 2: clone or reuse
# ---------------------------------------------------------------------------
log_step "Repository"

# Detect if we're already inside a collate checkout
SCRIPT_PARENT=""
if [[ -n "${BASH_SOURCE:-}" && -f "${BASH_SOURCE[0]:-}" ]]; then
    SCRIPT_PARENT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

if [[ -n "$SCRIPT_PARENT" && -f "$SCRIPT_PARENT/.claude-plugin/plugin.json" ]]; then
    log_info "running from in-repo; using ${SCRIPT_PARENT} as COLLATE_HOME"
    TARGET="$SCRIPT_PARENT"
elif [[ -d "$TARGET/.git" ]]; then
    log_info "existing checkout at ${TARGET}; pulling"
    run "git -C \"$TARGET\" pull --ff-only"
    log_ok "repo updated"
else
    log_info "cloning ${REPO_URL} → ${TARGET}"
    run "mkdir -p \"$(dirname "$TARGET")\""
    run "git clone --depth 1 \"$REPO_URL\" \"$TARGET\""
    log_ok "repo cloned"
fi

# ---------------------------------------------------------------------------
# Step 3: Python deps
# ---------------------------------------------------------------------------
if [[ $INSTALL_DEPS -eq 1 ]]; then
    log_step "Python dependencies"
    log_info "running: pip install --user -U -r requirements.txt"
    log_hint "this pulls ~1 GB of torch + mineru models meta; takes ~5 minutes"

    if [[ $DRY_RUN -eq 0 ]]; then
        # Try --user first; if pip rejects (e.g. inside a venv), retry without
        if ! python3 -m pip install --user -U -r "$TARGET/requirements.txt" 2>/dev/null; then
            log_warn "--user rejected (likely inside a venv); retrying without --user"
            python3 -m pip install -U -r "$TARGET/requirements.txt"
        fi
    else
        printf '%s[dry]%s pip install --user -U -r %s/requirements.txt\n' \
            "${C_DIM}" "${C_RESET}" "$TARGET"
    fi
    log_ok "Python deps installed"
fi

# ---------------------------------------------------------------------------
# Step 4: Agent runtime wiring
# ---------------------------------------------------------------------------
declare -a WIRED_RUNTIMES=()
declare -a MANUAL_RUNTIMES=()

wire_claude_code() {
    local plugins_dir="$HOME/.claude/plugins"
    local target_link="$plugins_dir/collate"

    if [[ ! -d "$HOME/.claude" ]]; then
        return 1  # Claude Code not installed
    fi

    run "mkdir -p \"$plugins_dir\""

    if [[ -L "$target_link" ]]; then
        local current
        current=$(readlink "$target_link")
        if [[ "$current" == "$TARGET" ]]; then
            log_ok "claude-code: already wired → $target_link"
            WIRED_RUNTIMES+=("claude-code")
            return 0
        fi
        log_warn "claude-code: existing symlink points elsewhere ($current); leaving alone"
        MANUAL_RUNTIMES+=("claude-code")
        return 0
    fi

    if [[ -e "$target_link" ]]; then
        log_warn "claude-code: $target_link exists and is not a symlink; leaving alone"
        MANUAL_RUNTIMES+=("claude-code")
        return 0
    fi

    run "ln -s \"$TARGET\" \"$target_link\""
    log_ok "claude-code: symlinked $target_link → $TARGET"
    WIRED_RUNTIMES+=("claude-code")
}

wire_hermes() {
    if ! command -v hermes >/dev/null 2>&1; then
        return 1
    fi

    local hermes_skills="$HOME/.hermes/skills"
    run "mkdir -p \"$hermes_skills\""

    # In dry-run mode the $TARGET checkout may not exist yet; report intent only.
    if [[ $DRY_RUN -eq 1 && ! -d "$TARGET/skills" ]]; then
        log_ok "hermes: would symlink skills/* → ${hermes_skills}/collate-* (skills/ not yet cloned)"
        WIRED_RUNTIMES+=("hermes")
        return 0
    fi

    local wired=0 skipped=0
    for skill_dir in "$TARGET/skills/"*/; do
        [[ -d "$skill_dir" ]] || continue
        local skill_name
        skill_name="$(basename "$skill_dir")"
        local link_name="$hermes_skills/collate-${skill_name}"

        if [[ -L "$link_name" ]]; then
            skipped=$((skipped + 1))
            continue
        fi
        if [[ -e "$link_name" ]]; then
            log_warn "hermes: $link_name exists and is not a symlink; skipping"
            continue
        fi
        run "ln -s \"$skill_dir\" \"$link_name\""
        wired=$((wired + 1))
    done

    if (( wired > 0 )); then
        log_ok "hermes: wired ${wired} skills into ${hermes_skills}/collate-*"
    elif (( skipped > 0 )); then
        log_ok "hermes: all ${skipped} skills already wired"
    else
        log_warn "hermes: no skills/ directory found at ${TARGET}"
    fi
    WIRED_RUNTIMES+=("hermes")
}

wire_opencode() {
    if ! command -v opencode >/dev/null 2>&1; then
        return 1
    fi
    # OpenCode auto-loads AGENTS.md on `cd $TARGET && opencode` — nothing to do
    log_ok "opencode: detected (zero-config, AGENTS.md auto-loads)"
    WIRED_RUNTIMES+=("opencode")
}

wire_codex() {
    if ! command -v codex >/dev/null 2>&1; then
        return 1
    fi
    log_ok "codex-cli: detected (zero-config, AGENTS.md auto-discovered from Git root)"
    WIRED_RUNTIMES+=("codex-cli")
}

wire_gemini() {
    if ! command -v gemini >/dev/null 2>&1; then
        return 1
    fi
    log_ok "gemini-cli: detected (load AGENTS.md as session context; extension on roadmap)"
    MANUAL_RUNTIMES+=("gemini-cli")
}

wire_cursor() {
    # Cursor doesn't install a binary on PATH; detect via macOS .app or ~/.cursor
    if [[ "$(uname -s)" == "Darwin" && -d "/Applications/Cursor.app" ]] \
        || [[ -d "$HOME/.cursor" ]]; then
        log_ok "cursor: detected (per-project rule file required; see next-steps)"
        MANUAL_RUNTIMES+=("cursor")
        return 0
    fi
    return 1
}

if [[ $WIRE_RUNTIMES -eq 1 ]]; then
    log_step "Agent runtime auto-detection"

    wire_claude_code || log_hint "claude-code: not detected (no ~/.claude)"
    wire_opencode    || log_hint "opencode: not detected (no \`opencode\` on PATH)"
    wire_hermes      || log_hint "hermes: not detected (no \`hermes\` on PATH)"
    wire_codex       || log_hint "codex-cli: not detected (no \`codex\` on PATH)"
    wire_cursor      || log_hint "cursor: not detected"
    wire_gemini      || log_hint "gemini-cli: not detected (no \`gemini\` on PATH)"

    if (( ${#WIRED_RUNTIMES[@]} == 0 && ${#MANUAL_RUNTIMES[@]} == 0 )); then
        log_warn "no agent runtimes detected; install one and re-run, or use the mechanical pipeline directly"
    fi
fi

# ---------------------------------------------------------------------------
# Step 5: Next-step instructions
# ---------------------------------------------------------------------------
log_step "Next steps"

cat <<EOF
${C_BOLD}1. Set up OCR credentials${C_RESET}

   Put one of the following in ${C_CYAN}~/.env${C_RESET} (the default is local MinerU, no key needed):

     OCR_ENGINE=mineru              ${C_DIM}# local CLI, default${C_RESET}
     # OCR_ENGINE=mineru-cloud
     # MINERU_API_KEY=sk-...
     # OCR_ENGINE=baidu
     # BAIDU_OCR_API_KEY=...
     # BAIDU_OCR_SECRET_KEY=...

${C_BOLD}2. Run the pipeline${C_RESET}

   ${C_CYAN}\$${C_RESET} python3 ${TARGET}/scripts/run_full_pipeline.py --pdf /abs/path/to/paper.pdf

${C_BOLD}3. Or hand the job to an agent${C_RESET}
EOF

if [[ " ${WIRED_RUNTIMES[*]} " == *" claude-code "* ]]; then
    cat <<EOF

   ${C_GREEN}Claude Code${C_RESET} (wired):
     Inside Claude Code, run:  ${C_CYAN}/plugin install ${TARGET}${C_RESET}
     Then:                     ${C_CYAN}/collate:setup${C_RESET}
EOF
fi

if [[ " ${WIRED_RUNTIMES[*]} " == *" opencode "* ]]; then
    cat <<EOF

   ${C_GREEN}OpenCode${C_RESET} (wired):
     ${C_CYAN}cd ${TARGET} && opencode${C_RESET}     ${C_DIM}# AGENTS.md auto-loads${C_RESET}
EOF
fi

if [[ " ${WIRED_RUNTIMES[*]} " == *" hermes "* ]]; then
    cat <<EOF

   ${C_GREEN}Hermes${C_RESET} (wired):
     ${C_CYAN}cd ${TARGET} && hermes${C_RESET}       ${C_DIM}# AGENTS.md + skills auto-load${C_RESET}
EOF
fi

if [[ " ${WIRED_RUNTIMES[*]} " == *" codex-cli "* ]]; then
    cat <<EOF

   ${C_GREEN}Codex CLI${C_RESET} (wired):
     ${C_CYAN}cd ${TARGET} && codex${C_RESET}        ${C_DIM}# AGENTS.md auto-discovered from Git root${C_RESET}
EOF
fi

if [[ " ${MANUAL_RUNTIMES[*]} " == *" cursor "* ]]; then
    cat <<EOF

   ${C_YELLOW}Cursor${C_RESET} (manual):
     In any project that will use collate, create ${C_CYAN}.cursor/rules/collate.mdc${C_RESET}:

       ---
       description: collate agent contract
       alwaysApply: true
       ---

       See ${TARGET}/AGENTS.md for the full agent contract.
       Scripts live under ${TARGET}/skills/*/scripts/*.py.
EOF
fi

if [[ " ${MANUAL_RUNTIMES[*]} " == *" gemini-cli "* ]]; then
    cat <<EOF

   ${C_YELLOW}Gemini CLI${C_RESET} (manual):
     ${C_CYAN}cd ${TARGET} && gemini${C_RESET}
     In the first turn paste the contents of ${TARGET}/AGENTS.md as session context.
     (A native \`gemini-extension.json\` wrapper is on the roadmap.)
EOF
fi

cat <<EOF

${C_BOLD}Docs${C_RESET}

   README:         ${TARGET}/README.md  (中文: README.zh.md)
   Agent contract: ${TARGET}/AGENTS.md
   Per-runtime:    ${TARGET}/docs/INTEGRATIONS.md
   Troubleshoot:   ${TARGET}/docs/TROUBLESHOOTING.md

${C_BOLD}Uninstall${C_RESET}

   rm -rf ${TARGET}
   rm -f  ~/.claude/plugins/collate             ${C_DIM}# if wired${C_RESET}
   rm -f  ~/.hermes/skills/collate-*            ${C_DIM}# if wired${C_RESET}

${C_GREEN}Install complete.${C_RESET}

EOF

#!/usr/bin/env bash
#
# SessionStart hook: provision client and server dependencies.
#
# Fresh Claude Code (web/remote) containers clone the repo but never install
# dependencies. Because client/node_modules is gitignored, the local `jest`
# binary is missing and the pre-commit test hook fails with "jest: not found".
# This script installs deps once, up front, mirroring the commands CI uses.
#
# Notes:
# - No `set -e`: a failed install (e.g. offline container) must NOT abort the
#   session. We always exit 0 and let the pre-commit hook surface a clear
#   message if deps are still missing.
# - Output is kept brief because SessionStart stdout is added to the context.

set -u

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

log() { echo "[session-setup] $*" >&2; }

# Install client dependencies (matches .github/workflows/nodejs-client.yml).
if [ -d "$PROJECT_DIR/client" ]; then
  if command -v npm >/dev/null 2>&1; then
    if [ -d "$PROJECT_DIR/client/node_modules/.bin" ]; then
      log "client deps already present, skipping npm ci"
    else
      log "installing client deps (npm ci --legacy-peer-deps)..."
      if (cd "$PROJECT_DIR/client" && npm ci --legacy-peer-deps >&2); then
        log "client deps installed"
      else
        log "WARNING: npm ci failed (offline or network policy?); client tests may not run"
      fi
    fi
  else
    log "WARNING: npm not found; skipping client deps"
  fi
fi

# Install server dependencies (matches .github/workflows/python-app.yml).
if [ -d "$PROJECT_DIR/server" ]; then
  if command -v uv >/dev/null 2>&1; then
    log "syncing server deps (uv sync)..."
    if (cd "$PROJECT_DIR/server" && uv sync >&2); then
      log "server deps synced"
    else
      log "WARNING: uv sync failed (offline or network policy?); server tests may not run"
    fi
  else
    log "WARNING: uv not found; skipping server deps"
  fi
fi

exit 0

# Claude Code Hooks

This directory contains hooks for Claude Code that automate quality checks during development.

## Session Setup Hook

The `session-setup.sh` hook runs automatically on `SessionStart` to install
project dependencies, so a fresh container is ready to run tests before the
first commit.

### Why it exists

Fresh Claude Code (web/remote) containers clone the repo but never install
dependencies. Because `client/node_modules/` is gitignored, the client's local
`jest` binary is missing, and the pre-commit test hook fails with
`jest: not found` — blocking commits even for server-only changes.

### What it does

1. **Client deps**: runs `npm ci --legacy-peer-deps` in `client/` (matches CI), skipping if already installed
2. **Server deps**: runs `uv sync` in `server/` (matches CI)
3. **Never blocks the session**: if an install fails (e.g. offline / restricted network policy) it logs a warning and exits 0; the pre-commit hook then surfaces a clear, actionable message

### Configuration

Registered as a `SessionStart` hook in `.claude/settings.json` with a 600s
timeout (a cold `npm ci` can take a few minutes).

---

## Pre-Commit Lint Hook

The `pre-commit-lint.py` hook runs `make lint-fix` before commits to auto-fix linting issues.

### What it does

1. **Intercepts git commits**: Monitors all Bash commands and detects git commit attempts
2. **Runs linting**: Executes `make lint-fix` in the server directory (ruff check --fix + ruff format)
3. **Auto-fixes issues**: Automatically formats and fixes linting issues where possible
4. **Blocks if unfixable**: Prevents commits only if there are issues that can't be auto-fixed

### Timeout

- 60 seconds (runs before test hook)

---

## Pre-Commit Test Hook

The `pre-commit-test.py` hook ensures all tests pass before allowing commits.

### What it does

1. **Intercepts git commits**: Monitors all Bash commands and detects git commit attempts
2. **Runs all tests**: Executes both frontend (Jest) and backend (pytest) test suites
3. **Blocks bad commits**: Prevents commits if any tests fail
4. **Provides feedback**: Shows test results to Claude and the user

### Test suites run

- **Client tests**: `npm test` in the `client/` directory
- **Server tests**: `pytest -v` in the `server/` directory

### Configuration

Both hooks are configured in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/pre-commit-lint.py",
            "timeout": 60
          },
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/pre-commit-test.py",
            "timeout": 180
          }
        ]
      }
    ]
  }
}
```

### Behavior

- **Tests pass**: Commit proceeds normally
- **Tests fail**: Commit is blocked with detailed error messages shown to Claude
- **Timeout**: 180 seconds (3 minutes) to accommodate both test suites

### Manual testing

You can test the hook manually:

```bash
# Run the hook with sample input
echo '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "git commit -m \"test\""
  }
}' | CLAUDE_PROJECT_DIR=/home/user/budget.rip ./.claude/hooks/pre-commit-test.py
```

### Bypassing the hook

If you need to commit without running tests (not recommended):

1. Use `/hooks` command in Claude Code to temporarily disable the hook
2. Make your commit
3. Re-enable the hook afterwards

## How hooks work

Claude Code hooks are automated scripts that run at specific points in Claude's workflow. This project uses a `PreToolUse` hook that runs before any Bash command executes.

For more information, see the [Claude Code hooks documentation](https://docs.claude.com/en/docs/claude-code/hooks).

# Claude Code Hooks

This directory contains hooks for Claude Code that automate quality checks during development.

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

The hook is configured in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
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

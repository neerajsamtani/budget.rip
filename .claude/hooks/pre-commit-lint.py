#!/usr/bin/env python3
"""
Pre-commit hook for Claude Code that runs linting before allowing commits.

This hook:
1. Intercepts git commit commands
2. Runs linting checks (ruff check and ruff format) on server code
3. Blocks commits if linting fails
4. Provides feedback to Claude about linting results
"""

import json
import sys
import subprocess
import os
import re


def is_git_commit_command(command: str) -> bool:
    """Check if the command is a git commit."""
    # Match various git commit patterns
    patterns = [
        r'^git\s+commit',
        r'&&\s*git\s+commit',
        r';\s*git\s+commit',
    ]
    return any(re.search(pattern, command) for pattern in patterns)


def run_server_linting(project_dir: str) -> tuple[bool, str]:
    """Run linting checks for the server using Make."""
    server_dir = os.path.join(project_dir, 'server')

    if not os.path.exists(server_dir):
        return True, "No server directory found, skipping linting"

    try:
        # Use make lint-fix which auto-fixes linting issues and then checks
        result = subprocess.run(
            ['make', 'lint-fix'],
            cwd=server_dir,
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )

        if result.returncode == 0:
            return True, "Linting passed (auto-fixed issues if any)"
        else:
            # Return the output so Claude can see what needs to be fixed
            output = result.stdout + "\n" + result.stderr
            # Limit output to last 1000 chars to avoid prompt length issues
            if len(output) > 1000:
                output = "..." + output[-1000:]
            return False, f"Linting failed:\n{output}"
    except subprocess.TimeoutExpired:
        return False, "Linting timed out after 1 minute"
    except Exception as e:
        return False, f"Error running linting: {str(e)}"


def main():
    # Load input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    # Only process Bash tool calls
    if tool_name != "Bash":
        sys.exit(0)

    # Check if this is a git commit command
    if not is_git_commit_command(command):
        sys.exit(0)

    # Get project directory
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not project_dir:
        print("Error: CLAUDE_PROJECT_DIR not set", file=sys.stderr)
        sys.exit(1)

    print("Pre-commit hook: Running linting checks before commit...", file=sys.stderr)

    # Run linting
    lint_passed, lint_message = run_server_linting(project_dir)
    print(f"\n{lint_message}", file=sys.stderr)

    # Check results
    if not lint_passed:
        print("\n" + "="*60, file=sys.stderr)
        print("COMMIT BLOCKED: Linting failed!", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print("\nPlease fix the linting issues before committing.", file=sys.stderr)
        print("You can run linting manually:", file=sys.stderr)
        print("  Server: cd server && make lint-fix", file=sys.stderr)

        # Exit code 2 blocks the tool call and shows stderr to Claude
        sys.exit(2)

    print("\n" + "="*60, file=sys.stderr)
    print("Linting passed! Proceeding with commit.", file=sys.stderr)
    print("="*60 + "\n", file=sys.stderr)

    # Exit code 0 allows the commit to proceed
    sys.exit(0)


if __name__ == "__main__":
    main()

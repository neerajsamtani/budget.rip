#!/usr/bin/env python3
"""
Pre-commit hook for Claude Code that runs tests before allowing commits.

This hook:
1. Intercepts git commit commands
2. Runs both client (Jest) and server (pytest) test suites
3. Blocks commits if tests fail
4. Provides feedback to Claude about test results
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

def run_client_tests(project_dir: str) -> tuple[bool, str]:
    """Run Jest tests for the client."""
    client_dir = os.path.join(project_dir, 'client')

    if not os.path.exists(client_dir):
        return True, "No client directory found, skipping client tests"

    try:
        result = subprocess.run(
            ['npm', 'test'],
            cwd=client_dir,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        if result.returncode == 0:
            return True, "Client tests passed"
        else:
            return False, f"Client tests failed:\n{result.stdout}\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Client tests timed out after 2 minutes"
    except Exception as e:
        return False, f"Error running client tests: {str(e)}"

def run_server_tests(project_dir: str) -> tuple[bool, str]:
    """Run pytest tests for the server."""
    server_dir = os.path.join(project_dir, 'server')

    if not os.path.exists(server_dir):
        return True, "No server directory found, skipping server tests"

    try:
        result = subprocess.run(
            ['pytest', '-v'],
            cwd=server_dir,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        if result.returncode == 0:
            return True, "Server tests passed"
        else:
            return False, f"Server tests failed:\n{result.stdout}\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Server tests timed out after 2 minutes"
    except Exception as e:
        return False, f"Error running server tests: {str(e)}"

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

    print("Pre-commit hook: Running tests before commit...", file=sys.stderr)

    # Run client tests
    client_passed, client_message = run_client_tests(project_dir)
    print(f"\n{client_message}", file=sys.stderr)

    # Run server tests
    server_passed, server_message = run_server_tests(project_dir)
    print(f"\n{server_message}", file=sys.stderr)

    # Check results
    if not client_passed or not server_passed:
        print("\n" + "="*60, file=sys.stderr)
        print("COMMIT BLOCKED: Tests failed!", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print("\nPlease fix the failing tests before committing.", file=sys.stderr)
        print("You can run tests manually:", file=sys.stderr)
        print("  Client: cd client && npm test", file=sys.stderr)
        print("  Server: cd server && pytest -v", file=sys.stderr)

        # Exit code 2 blocks the tool call and shows stderr to Claude
        sys.exit(2)

    print("\n" + "="*60, file=sys.stderr)
    print("All tests passed! Proceeding with commit.", file=sys.stderr)
    print("="*60 + "\n", file=sys.stderr)

    # Exit code 0 allows the commit to proceed
    sys.exit(0)

if __name__ == "__main__":
    main()

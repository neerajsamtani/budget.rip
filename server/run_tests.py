#!/usr/bin/env python3
"""
Test runner script that handles database setup and teardown.

Usage:
    python run_tests.py                    # Run tests with auto cleanup
    python run_tests.py --keep-alive       # Keep databases running after tests
    python run_tests.py --stop-only        # Stop databases without running tests
    python run_tests.py --help             # Show help

This script will:
1. Check if Docker is available
2. Start MongoDB and PostgreSQL test databases via Docker Compose
3. Wait for databases to be healthy
4. Run database migrations
5. Execute pytest
6. Stop databases (unless --keep-alive is specified)
"""

import argparse
import os
import subprocess
import sys
import time


def run_command(cmd, capture_output=False, check=True, env=None):
    """Run a shell command and return the result."""
    try:
        if capture_output:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=check,
                env=env
            )
            return result
        else:
            subprocess.run(cmd, shell=True, check=check, env=env)
            return None
    except subprocess.CalledProcessError as e:
        if capture_output:
            print(f"Error running command: {cmd}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
        raise


def check_docker():
    """Check if Docker is installed and running."""
    print("Checking Docker availability...")
    try:
        result = run_command("docker --version", capture_output=True)
        print(f"  {result.stdout.strip()}")

        result = run_command("docker compose version", capture_output=True)
        print(f"  {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print("\n❌ Docker is not available!")
        print("\nTo run tests, you need Docker installed:")
        print("  - macOS: Install Docker Desktop from https://docker.com")
        print("  - Linux: Install docker and docker-compose")
        print("  - Windows: Install Docker Desktop from https://docker.com")
        return False


def start_databases():
    """Start test databases using Docker Compose."""
    print("\nStarting test databases...")
    run_command("docker compose -f docker-compose.test.yml up -d")

    print("\nWaiting for databases to be healthy...")
    max_wait = 30
    waited = 0

    while waited < max_wait:
        result = run_command(
            "docker compose -f docker-compose.test.yml ps --format json",
            capture_output=True
        )

        # Check if all services are healthy
        # The output is JSON, we can check for "healthy" status
        if '"Health":"healthy"' in result.stdout or 'running' in result.stdout.lower():
            # Give it a couple more seconds to be fully ready
            time.sleep(2)
            print("  ✓ Databases are ready!")
            return True

        time.sleep(2)
        waited += 2
        print(f"  Waiting... ({waited}/{max_wait}s)")

    print("  ⚠ Timeout waiting for databases, but continuing anyway...")
    return True


def stop_databases():
    """Stop test databases."""
    print("\nStopping test databases...")
    run_command("docker compose -f docker-compose.test.yml down -v")
    print("  ✓ Databases stopped")


def run_migrations():
    """Run database migrations."""
    print("\nRunning database migrations...")

    # Set up environment for migrations
    env = os.environ.copy()
    env['DATABASE_URL'] = 'postgresql://postgres:test_password@localhost:5432/budgit_test'

    try:
        run_command("alembic upgrade head", env=env)
        print("  ✓ Migrations completed")
        return True
    except subprocess.CalledProcessError as e:
        print("  ⚠ Migration failed, but continuing...")
        return False


def run_tests():
    """Run pytest."""
    print("\nRunning tests...")
    print("=" * 70)

    # Set up environment for tests
    env = os.environ.copy()
    env['TEST_MONGO_URI'] = 'mongodb://localhost:27017/budgit_test'
    env['DATABASE_URL'] = 'postgresql://postgres:test_password@localhost:5432/budgit_test'

    try:
        # Run pytest with environment variables
        subprocess.run("pytest", shell=True, check=True, env=env)
        print("=" * 70)
        print("✓ All tests passed!")
        return True
    except subprocess.CalledProcessError:
        print("=" * 70)
        print("❌ Some tests failed")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run backend tests with automatic database setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py              # Run tests with auto cleanup
  python run_tests.py --keep-alive # Keep databases running after tests
  python run_tests.py --stop-only  # Stop databases without running tests
        """
    )
    parser.add_argument(
        "--keep-alive",
        action="store_true",
        help="Keep databases running after tests (useful for debugging)"
    )
    parser.add_argument(
        "--stop-only",
        action="store_true",
        help="Only stop databases, don't run tests"
    )

    args = parser.parse_args()

    # Change to server directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("=" * 70)
    print("Budget.rip Test Runner")
    print("=" * 70)

    # Check Docker availability
    if not check_docker():
        sys.exit(1)

    # If stop-only, just stop and exit
    if args.stop_only:
        stop_databases()
        sys.exit(0)

    # Start databases
    try:
        start_databases()
    except Exception as e:
        print(f"\n❌ Failed to start databases: {e}")
        sys.exit(1)

    # Run migrations
    run_migrations()

    # Run tests
    tests_passed = run_tests()

    # Cleanup (unless keep-alive is specified)
    if not args.keep_alive:
        stop_databases()
        print("\n💡 Tip: Use --keep-alive to keep databases running for debugging")
    else:
        print("\n💡 Databases are still running. Use 'python run_tests.py --stop-only' to stop them.")

    # Exit with appropriate code
    sys.exit(0 if tests_passed else 1)


if __name__ == "__main__":
    main()

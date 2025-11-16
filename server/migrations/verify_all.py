#!/usr/bin/env python3
"""
Run all migration verification scripts in sequence.

Usage:
    python migrations/verify_all.py               # Default: thorough
    python migrations/verify_all.py --quick       # Quick (spot checks)

Exit codes:
    0: All passed
    1: One or more failed
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from constants import DATABASE_URL, MONGO_URI


def run_script(script_name, args=None):
    """Run verification script and return True if passed"""
    script_path = Path(__file__).parent / script_name
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    print(f"\n{'=' * 70}")
    print(f"Running: {script_name}")
    print('=' * 70)

    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run all verification scripts")
    parser.add_argument("--quick", action="store_true", help="Quick mode (spot checks)")
    args = parser.parse_args()

    print('=' * 70)
    print('DATABASE VERIFICATION')
    print('=' * 70)
    print(f"Mode: {'QUICK' if args.quick else 'THOROUGH'}")
    print(f"MongoDB: {MONGO_URI}")
    print(f"PostgreSQL: {DATABASE_URL}")

    # Determine args for each phase
    phase3_args = ["--quick"] if args.quick else ["--thorough"]
    phase4_args = [] if args.quick else ["--thorough"]

    # Run all verifications
    results = {
        "Phase 2: Reference Data": run_script("phase2_verify.py"),
        "Phase 3: Transactions & Line Items": run_script("phase3_verify.py", phase3_args),
        "Phase 4: Events & Relationships": run_script("phase4_verify.py", phase4_args),
        "Phase 5.5: Bank Accounts & Users": run_script("phase5_5_verify.py"),
    }

    # Print summary
    print(f"\n{'=' * 70}")
    print('SUMMARY')
    print('=' * 70)

    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")

    all_passed = all(results.values())
    print('=' * 70)

    if all_passed:
        print("\n✅ All verifications passed - databases are in sync")
    else:
        print("\n❌ Some verifications failed - review output above")
        print("Tip: Run phase3_reconcile.py to fix sync issues")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

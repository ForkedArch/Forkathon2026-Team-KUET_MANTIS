#!/usr/bin/env python3
"""
KUET CampusShare — 4-Tier E2E Test Suite Runner
Runs requirement-driven opaque-box tests across all 4 tiers:
- Tier 1: Feature Coverage (>=5 tests per core feature)
- Tier 2: Boundary & Corner Cases (>=5 tests per feature area)
- Tier 3: Cross-Feature Combinations (Pairwise integration flows)
- Tier 4: Real-World Application Scenarios (Multi-student campus workflows)

Exit Code:
- 0: All tests passed successfully
- 1: One or more tests failed
"""

import sys
import os
import time
import unittest
import argparse
from pathlib import Path

# Add project root and backend directory to path
repo_root = Path(__file__).resolve().parent.parent
backend_dir = repo_root / "backend"
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from tests.test_tier1_features import TestTier1Features
from tests.test_tier2_boundaries import TestTier2Boundaries
from tests.test_tier3_combinations import TestTier3Combinations
from tests.test_tier4_scenarios import TestTier4Scenarios

TIER_SUITES = {
    "1": ("Tier 1: Feature Coverage", TestTier1Features),
    "2": ("Tier 2: Boundary & Corner Cases", TestTier2Boundaries),
    "3": ("Tier 3: Cross-Feature Combinations", TestTier3Combinations),
    "4": ("Tier 4: Real-World Scenarios", TestTier4Scenarios),
}


def run_suite(suite_name: str, test_case_class, verbosity: int = 1):
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(test_case_class)
    runner = unittest.TextTestRunner(verbosity=verbosity)
    start_time = time.time()
    result = runner.run(suite)
    duration = time.time() - start_time
    return result, duration


def main():
    parser = argparse.ArgumentParser(description="KUET CampusShare E2E Test Suite Runner")
    parser.add_argument(
        "--tier",
        choices=["1", "2", "3", "4", "all"],
        default="all",
        help="Specify which tier to execute (1, 2, 3, 4, or all). Default: all",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable detailed verbose output for each test case",
    )
    args = parser.parse_args()

    verbosity = 2 if args.verbose else 1

    print("=" * 78)
    print("🎓 KUET CampusShare — 4-Tier Opaque-Box E2E Test Suite")
    print("   Platform: FastAPI + SQLAlchemy + SQLite (StaticPool In-Memory)")
    print("   Target: KUET Student-Exclusive Sharing Economy Platform")
    print("=" * 78)

    tiers_to_run = (
        ["1", "2", "3", "4"] if args.tier == "all" else [args.tier]
    )

    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_errors = 0
    total_duration = 0.0

    tier_results = []

    for tier_key in tiers_to_run:
        name, test_class = TIER_SUITES[tier_key]
        print(f"\n▶ Executing {name} ...")
        res, dur = run_suite(name, test_class, verbosity=verbosity)
        count = res.testsRun
        fails = len(res.failures)
        errs = len(res.errors)
        passed = count - (fails + errs)

        total_tests += count
        total_passed += passed
        total_failed += fails
        total_errors += errs
        total_duration += dur

        status_str = "PASS" if (fails == 0 and errs == 0) else "FAIL"
        tier_results.append((name, count, passed, fails + errs, dur, status_str))

    print("\n" + "=" * 78)
    print("📊 4-TIER E2E TEST EXECUTION SUMMARY")
    print("=" * 78)
    print(f"{'Tier Name':<42} {'Count':<8} {'Pass':<8} {'Fail':<8} {'Time (s)':<10} {'Status'}")
    print("-" * 78)
    for name, count, passed, fail_err, dur, status in tier_results:
        print(f"{name:<42} {count:<8} {passed:<8} {fail_err:<8} {dur:<10.2f} {status}")
    print("-" * 78)
    print(
        f"{'TOTALS':<42} {total_tests:<8} {total_passed:<8} {total_failed + total_errors:<8} {total_duration:<10.2f} "
        f"{'PASS' if (total_failed == 0 and total_errors == 0) else 'FAIL'}"
    )
    print("=" * 78)

    if total_failed == 0 and total_errors == 0:
        print(f"\n🎉 SUCCESS: All {total_tests} tests across {len(tiers_to_run)} tiers PASSED cleanly!")
        sys.exit(0)
    else:
        print(f"\n❌ FAILURE: {total_failed + total_errors} test(s) failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()

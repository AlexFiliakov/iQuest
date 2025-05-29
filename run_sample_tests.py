#!/usr/bin/env python3
"""Run a sample of new tests to verify they work."""

import subprocess
import sys

# Sample of tests to run
test_files = [
    "tests/unit/test_calendar_heatmap.py::TestCalendarHeatmapComponent::test_initialization",
    "tests/unit/test_anomaly_detection_comprehensive.py::TestAnomalyModels::test_anomaly_type_enum",
    "tests/unit/test_goal_management_comprehensive.py::TestGoalModels::test_goal_type_enum", 
    "tests/unit/test_health_score_comprehensive.py::TestHealthScoreModels::test_score_category_enum",
    "tests/unit/test_correlation_analyzer_comprehensive.py::TestCorrelationModels::test_correlation_type_enum"
]

def run_test(test_path):
    """Run a single test."""
    print(f"\nRunning: {test_path}")
    print("-" * 60)
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-xvs", test_path],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ PASSED")
        return True
    else:
        print("❌ FAILED")
        print(result.stdout)
        print(result.stderr)
        return False

def main():
    """Run sample tests."""
    print("Running sample tests to verify functionality...")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test in test_files:
        if run_test(test):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n✅ All sample tests passed! Ready to run full test suite.")
        return 0
    else:
        print("\n❌ Some tests failed. Need to fix imports/dependencies.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
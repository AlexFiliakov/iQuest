#!/usr/bin/env python3
"""
Script to fix remaining test import errors for Windows users.
Run this in your Windows environment to complete the test fixes.
"""

import os
import sys
import subprocess


def check_and_install_dependencies():
    """Check and install missing dependencies."""
    print("Checking Python dependencies...")
    
    required_packages = [
        'PyQt6',
        'pytest-benchmark',
        'faker',
        'memory-profiler',
        'networkx'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nInstalling missing packages: {', '.join(missing_packages)}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
        print("✓ All dependencies installed")
    else:
        print("\n✓ All dependencies are already installed")


def test_imports():
    """Test that key imports work."""
    print("\nTesting key imports...")
    
    test_cases = [
        ("Analytics components", [
            "from src.analytics.daily_metrics_calculator import DailyMetricsCalculator",
            "from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator",
            "from src.analytics.monthly_metrics_calculator import MonthlyMetricsCalculator",
            "from src.statistics_calculator import StatisticsCalculator"
        ]),
        ("Data components", [
            "from src.data_loader import DataLoader",
            "from src.database import DatabaseManager",
            "from src.data_filter_engine import DataFilterEngine"
        ]),
        ("Test utilities", [
            "from tests.test_data_generator import HealthDataGenerator",
            "import pytest_benchmark",
            "import faker"
        ])
    ]
    
    all_passed = True
    
    for category, imports in test_cases:
        print(f"\n{category}:")
        for import_stmt in imports:
            try:
                exec(import_stmt)
                print(f"  ✓ {import_stmt}")
            except Exception as e:
                print(f"  ✗ {import_stmt}: {e}")
                all_passed = False
    
    return all_passed


def run_test_collection():
    """Run pytest collection to verify tests can be collected."""
    print("\nRunning test collection...")
    
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', '--collect-only', '-q'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        # Count collected tests
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if 'collected' in line:
                print(f"✓ {line}")
                break
    else:
        print("✗ Test collection failed")
        print("Error output:")
        print(result.stderr)
    
    return result.returncode == 0


def main():
    """Main function."""
    print("=== Apple Health Analytics Test Suite Fixer ===\n")
    
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    print(f"Working directory: {project_dir}\n")
    
    # Step 1: Check dependencies
    check_and_install_dependencies()
    
    # Step 2: Test imports
    print("\n" + "="*50)
    imports_ok = test_imports()
    
    # Step 3: Run test collection
    print("\n" + "="*50)
    collection_ok = run_test_collection()
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY:")
    if imports_ok and collection_ok:
        print("✓ All tests are ready to run!")
        print("\nYou can now run the full test suite with:")
        print("  python -m pytest")
        print("\nOr run specific test categories:")
        print("  python -m pytest tests/unit/")
        print("  python -m pytest tests/test_data_generator_basic.py")
        print("  python -m pytest -m 'not visual'  # Skip visual tests")
    else:
        print("✗ Some issues remain. Please check the error messages above.")
        print("\nCommon fixes:")
        print("1. Make sure you're in the correct Python environment")
        print("2. Try: pip install --upgrade -r requirements.txt")
        print("3. For PyQt6 issues on Windows, you may need:")
        print("   pip uninstall PyQt6")
        print("   pip install PyQt6==6.5.0")


if __name__ == "__main__":
    main()
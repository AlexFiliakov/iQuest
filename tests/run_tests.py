#!/usr/bin/env python3
"""
Test runner script for the analytics test suite.
Provides convenient commands for running different types of tests.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description=""):
    """Run a command and handle output."""
    print(f"\n{'='*60}")
    print(f"Running: {description or command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True)
        print(f"✅ {description or 'Command'} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description or 'Command'} failed with exit code {e.returncode}")
        return False


def run_unit_tests(coverage=True, fail_under=90):
    """Run unit tests with optional coverage."""
    cmd = "pytest tests/unit tests/test_comprehensive_unit_coverage.py -v"
    
    if coverage:
        cmd += f" --cov=src --cov-report=term --cov-report=html --cov-fail-under={fail_under}"
    
    return run_command(cmd, "Unit Tests with Coverage")


def run_integration_tests():
    """Run integration tests."""
    cmd = "pytest tests/integration -v"
    return run_command(cmd, "Integration Tests")


def run_performance_tests(save_baseline=False):
    """Run performance benchmark tests."""
    cmd = "pytest tests/test_performance_benchmarks.py --benchmark-only --benchmark-sort=mean"
    
    if save_baseline:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        cmd += f" --benchmark-save=baseline_{timestamp}"
    
    return run_command(cmd, "Performance Benchmarks")


def run_visual_tests():
    """Run visual regression tests."""
    # Ensure baseline directory exists
    Path("tests/visual/baselines").mkdir(parents=True, exist_ok=True)
    
    cmd = "pytest tests/test_visual_regression.py -m visual -v"
    return run_command(cmd, "Visual Regression Tests")


def run_chaos_tests():
    """Run chaos testing scenarios."""
    cmd = "pytest tests/test_chaos_scenarios.py -m chaos -v --timeout=30"
    return run_command(cmd, "Chaos Tests")


def run_all_tests():
    """Run the complete test suite."""
    print("🚀 Running Complete Analytics Test Suite")
    
    results = []
    
    # Unit tests (must pass)
    results.append(run_unit_tests())
    
    # Integration tests
    results.append(run_integration_tests())
    
    # Performance tests
    results.append(run_performance_tests())
    
    # Visual tests (may be skipped if no display)
    try:
        results.append(run_visual_tests())
    except Exception as e:
        print(f"⚠️  Visual tests skipped: {e}")
        results.append(True)  # Don't fail entire suite
    
    # Chaos tests
    results.append(run_chaos_tests())
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUITE SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if all(results):
        print("🎉 All tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False


def generate_test_data():
    """Generate test data samples for manual testing."""
    print("Generating test data samples...")
    
    try:
        from tests.generators.test_data_generator import TestDataGenerator
        import pandas as pd
        
        generator = TestDataGenerator(seed=42)
        
        # Create output directory
        output_dir = Path("test_data_samples")
        output_dir.mkdir(exist_ok=True)
        
        # Generate various datasets
        datasets = {
            "normal_year": generator.generate_synthetic_data(365),
            "stress_test": generator.generate_performance_data('large'),
            "edge_cases": generator.generate_edge_cases()
        }
        
        # Save normal datasets
        for name, data in datasets.items():
            if name != "edge_cases":
                data.to_csv(output_dir / f"{name}.csv", index=False)
                print(f"✅ Generated {name}.csv ({len(data)} records)")
        
        # Save edge cases
        for case_name, case_data in datasets["edge_cases"].items():
            case_data.to_csv(output_dir / f"edge_case_{case_name}.csv", index=False)
            print(f"✅ Generated edge_case_{case_name}.csv ({len(case_data)} records)")
        
        print(f"📁 Test data saved to {output_dir}/")
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate test data: {e}")
        return False


def check_test_environment():
    """Check if test environment is properly configured."""
    print("Checking test environment...")
    
    required_packages = [
        'pytest', 'pytest-benchmark', 'pytest-timeout', 'pytest-mock',
        'pytest-xdist', 'pytest-html', 'pillow', 'faker', 'memory-profiler'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} (missing)")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("\n🎯 Test environment is ready!")
    return True


def main():
    """Main command line interface."""
    parser = argparse.ArgumentParser(description="Analytics Test Suite Runner")
    parser.add_argument(
        'command',
        choices=['unit', 'integration', 'performance', 'visual', 'chaos', 'all', 'check', 'data'],
        help='Type of tests to run'
    )
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='Skip coverage reporting for unit tests'
    )
    parser.add_argument(
        '--coverage-threshold',
        type=int,
        default=90,
        help='Coverage threshold percentage (default: 90)'
    )
    parser.add_argument(
        '--save-baseline',
        action='store_true',
        help='Save performance baseline for future comparisons'
    )
    
    args = parser.parse_args()
    
    if args.command == 'check':
        success = check_test_environment()
    elif args.command == 'data':
        success = generate_test_data()
    elif args.command == 'unit':
        success = run_unit_tests(
            coverage=not args.no_coverage,
            fail_under=args.coverage_threshold
        )
    elif args.command == 'integration':
        success = run_integration_tests()
    elif args.command == 'performance':
        success = run_performance_tests(save_baseline=args.save_baseline)
    elif args.command == 'visual':
        success = run_visual_tests()
    elif args.command == 'chaos':
        success = run_chaos_tests()
    elif args.command == 'all':
        success = run_all_tests()
    else:
        parser.print_help()
        return 1
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())